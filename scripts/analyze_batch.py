#import vari
from pyspark.sql import SparkSession
from pyspark.sql.window import Window
from pyspark.sql.functions import col, concat_ws, when, pandas_udf, udf, length, lower, regexp_replace, rank
from pyspark.ml.linalg import Vectors, VectorUDT
from pyspark.sql.types import ArrayType, FloatType
from pyspark.ml.clustering import KMeans # Keep KMeans, remove BisectingKMeans
from pyspark.ml.evaluation import ClusteringEvaluator
from pyspark.ml.feature import PCA, StandardScaler # Keep PCA, StandardScaler
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import sys
import traceback
import re 

# --- CONFIGURAZIONE ---
DATA_INIZIO = "2020-01-01"
HDFS_INPUT_PATH = "hdfs:///user/hadoop/news/News_Category_Dataset_v3.json"  # Percorso HDFS per il dataset
LOCAL_OUTPUT_DIR = "file:///home/hadoop/TrendSpotter-Cluster/data/output/" # Percorso locale per i risultati CSV
HDFS_MODEL_DIR = "hdfs:///user/hadoop/models" # Percorso HDFS per i modelli

# Modello Embedding e Parametri Ottimali
SENTENCE_MODEL_NAME = 'all-mpnet-base-v2' # Modello Sentence Transformer da usare
K_CLUSTERS = 5 # Valore K ottimale trovato
MAX_ITERATIONS = 200 # Parametro KMeans ottimizzato

# Pipeline di Preprocessing Feature
USE_TEXT_PREPROCESSING = True # Mantieni pulizia testo
MIN_TEXT_LENGTH = 0 # Mantieni filtro lunghezza (o metti 0 se non serve)
USE_SCALER = True # StandardScaler (z-score)
USE_PCA = True # PCA (riduzione dimensionale)
PCA_COMPONENTS = 40 # Numero di componenti PCA da mantenere
PREDICTION_COL = "prediction" # Nome della colonna di previsione KMeans

# --- CONFIGURAZIONE FINE ---

# Crea la sessione Spark
def get_spark():
    # Usiamo configurazioni che supportano il carico
    return SparkSession.builder \
        .appName(f"TrendSpotter Analyze News") \
        .master("yarn") \
        .config("spark.executor.memory", "6g") \
        .config("spark.driver.memory", "6g") \
        .config("spark.sql.execution.arrow.pyspark.enabled", "true") \
        .getOrCreate()

spark = get_spark()
spark.sparkContext.setLogLevel("WARN")

# Funzione di pulizia testo
def clean_text(text):
    if not text: return ""
    text = text.lower()
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    text = re.sub(r'\s\d+\s', ' ', text)
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text
clean_text_udf = udf(clean_text)

# ---------------- Funzione UDF per generare embedding---------------
@pandas_udf(ArrayType(FloatType()))
def generate_embeddings_udf(texts: pd.Series) -> pd.Series:
    global sentence_model
    if 'sentence_model' not in globals():
        print(f"[*] Caricamento modello sentence transformer: {SENTENCE_MODEL_NAME}...")
        try:
            sentence_model = SentenceTransformer(SENTENCE_MODEL_NAME)
            print("[*] Modello caricato.")
        except Exception as e:
            print(f"[ERRORE] Caricamento modello fallito: {e}")
            raise e
    embeddings_np = sentence_model.encode(texts.to_list(), show_progress_bar=False, convert_to_numpy=True)
    return pd.Series([e.astype(np.float32).tolist() for e in embeddings_np])

# Funzione UDF per convertire Array in VectorUDT
to_vector_udf = udf(lambda x: Vectors.dense(x) if x is not None else None, VectorUDT()) 

# ------------------------------------------------------------------------------------------

# Carica, Seleziona, Filtra per Data
print(f"\n[*] Lettura dataset da: {HDFS_INPUT_PATH}")
try:
    df_raw = spark.read.json(HDFS_INPUT_PATH)
except Exception as e:
    print(f"\n[ERRORE] Lettura dataset fallita: {e}"); spark.stop(); sys.exit(1)

print("[*] Selezione colonne iniziali...")
df = df_raw.select("headline", "short_description", "category", "date") \
           .na.drop(subset=["headline", "short_description", "category", "date"])

print(f"[*] Filtraggio dati per date >= {DATA_INIZIO}...")
df = df.filter(col("date") >= DATA_INIZIO)
count_after_filter = df.count()
print(f"[*] Record dopo filtro data: {count_after_filter}")
if count_after_filter == 0: print("[ATTENZIONE] Nessun record trovato..."); spark.stop(); sys.exit(1)

# Raggruppamento Manuale Categorie (Sostituisce 'category')
print("[*] Raggruppamento categorie...")
df = df.withColumn(
    "category_temp_grouped",
    when(col("category").isin("ARTS", "ARTS & CULTURE", "CULTURE & ARTS"), "ARTS_CULTURE")
    .when(col("category").isin("BUSINESS", "MONEY"), "BUSINESS_FINANCE")
    .when(col("category") == "CRIME", "CRIME")
    .when(col("category").isin("EDUCATION", "COLLEGE"), "EDUCATION")
    .when(col("category").isin("ENTERTAINMENT", "COMEDY", "MEDIA"), "ENTERTAINMENT_MEDIA")
    .when(col("category").isin("ENVIRONMENT", "GREEN"), "ENVIRONMENT")
    .when(col("category").isin("TASTE", "FOOD & DRINK"), "FOOD_DRINK")
    .when(col("category").isin("HEALTHY LIVING", "WELLNESS"), "HEALTH_WELLNESS")
    .when(col("category").isin("PARENTING", "PARENTS", "DIVORCE", "WEDDINGS"), "PARENTING_FAMILY")
    .when(col("category") == "POLITICS", "POLITICS")
    .when(col("category") == "RELIGION", "RELIGION")
    .when(col("category") == "SCIENCE", "SCIENCE")
    .when(col("category") == "SPORTS", "SPORTS")
    .when(col("category").isin("STYLE", "STYLE & BEAUTY", "HOME & LIVING"), "STYLE_BEAUTY_HOME")
    .when(col("category") == "TECH", "TECH")
    .when(col("category") == "TRAVEL", "TRAVEL")
    .when(col("category") == "U.S. NEWS", "US_NEWS")
    .when(col("category").isin("BLACK VOICES", "LATINO VOICES", "QUEER VOICES"), "VOICES")
    .when(col("category") == "WOMEN", "WOMEN")
    .when(col("category").isin("THE WORLDPOST", "WORLDPOST", "WORLD NEWS"), "WORLD_NEWS")
    .when(col("category").isin("GOOD NEWS", "WEIRD NEWS"), "GOOD_WEIRD_NEWS")
    .when(col("category").isin("FIFTY", "IMPACT"), "OTHER")
    .otherwise(col("category"))  # Mantieni le categorie non raggruppate
)
df = df.drop("category").withColumnRenamed("category_temp_grouped", "category")
print("[*] Conteggio categorie dopo raggruppamento:")
df.groupBy("category").count().orderBy(col("count").desc()).show(n=30, truncate=False)

# Prepara e Pulisci Testo
print("[*] Preparazione testo (headline + short_description)...")
df = df.withColumn("text", concat_ws(" ", col("headline"), col("short_description"))) \
       .filter(col("text").isNotNull() & (col("text") != ""))
if USE_TEXT_PREPROCESSING:
    print("[*] Applicazione pulizia testo avanzata...")
    df = df.withColumn("text", clean_text_udf(col("text")))
    df = df.filter(length(col("text")) >= MIN_TEXT_LENGTH)
    count_after_preprocessing = df.count()
    print(f"[*] Record dopo pulizia testo e filtro lunghezza: {count_after_preprocessing}")
    if count_after_preprocessing == 0: print("[ATTENZIONE] Nessun record rimasto dopo pulizia testo..."); spark.stop(); sys.exit(1)

# Genera Embeddings
print(f"[*] Generazione Sentence Embeddings con '{SENTENCE_MODEL_NAME}'...")
try:
    df_with_embeddings_arr = df.withColumn("embedding_array", generate_embeddings_udf(col("text")))
    df_with_embeddings = df_with_embeddings_arr.withColumn("embedding_vec", to_vector_udf(col("embedding_array")))
    df_with_embeddings.cache()
    num_embedded = df_with_embeddings.count()
    print(f"[*] Embedding generati per {num_embedded} record.")
    df_with_embeddings.select("embedding_vec").printSchema() 
except Exception as udf_err:
    print(f"\n[ERRORE] Generazione embedding fallita: {udf_err}"); traceback.print_exc(); spark.stop(); sys.exit(1)

# 6. Preprocessing Feature (Scaling + PCA)
processed_df = df_with_embeddings
feature_col_for_kmeans = "embedding_vec" # Inizia con gli embedding UDT

# Applica Scaler 
if USE_SCALER:
    print("[*] Standardizzazione embedding (z-score)...")
    scaler = StandardScaler(inputCol="embedding_vec", outputCol="scaled_features", withStd=True, withMean=True)
    scaler_model = scaler.fit(processed_df)
    processed_df = scaler_model.transform(processed_df)
    feature_col_for_kmeans = "scaled_features" # Usa le feature scalate per il passo successivo
    # --- SALVATAGGIO MODELLO SCALER ---
    scaler_model_path = f"{HDFS_MODEL_DIR}/scaler_model_{SENTENCE_MODEL_NAME.replace('-', '_')}" 
    print(f"[*] Salvataggio modello Scaler in: {scaler_model_path}") 
    try:
        scaler_model.write().overwrite().save(scaler_model_path)
        print(f"✅ Modello Scaler salvato.")
    except Exception as save_err:
        print(f"[ERRORE] Fallito salvataggio modello Scaler: {save_err}")

# Applica PCA 
if USE_PCA:
    print(f"[*] Applicazione PCA (k={PCA_COMPONENTS}) su '{feature_col_for_kmeans}'...")
    pca = PCA(k=PCA_COMPONENTS, inputCol=feature_col_for_kmeans, outputCol="pca_features")
    pca_model = pca.fit(processed_df)
    processed_df = pca_model.transform(processed_df)
    feature_col_for_kmeans = "pca_features" # Usa le feature PCA per KMeans
    # --- SALVATAGGIO MODELLO PCA ---
    pca_model_path = f"{HDFS_MODEL_DIR}/pca_model_{SENTENCE_MODEL_NAME.replace('-', '_')}_k{PCA_COMPONENTS}"
    print(f"[*] Salvataggio modello PCA in: {pca_model_path}")
    try:
        pca_model.write().overwrite().save(pca_model_path)
        print(f"✅ Modello PCA salvato.")
        # Stampa varianza spiegata
        explained_variance = np.sum(pca_model.explainedVariance)
        print(f"[*] Varianza totale spiegata da {PCA_COMPONENTS} componenti PCA: {explained_variance:.4f}")
    except Exception as save_err:
        print(f"[ERRORE] Fallito salvataggio modello PCA: {save_err}")

print(f"[*] Colonna features finale per KMeans: '{feature_col_for_kmeans}'")
processed_df.select(feature_col_for_kmeans).printSchema() # Verifica tipo finale


# KMeans Clustering 
print(f"[*] Esecuzione KMeans clustering finale (K={K_CLUSTERS}) su '{feature_col_for_kmeans}'...")
kmeans = KMeans(k=K_CLUSTERS, seed=42, featuresCol=feature_col_for_kmeans, predictionCol="prediction", maxIter=MAX_ITERATIONS, initMode="k-means||", initSteps=10, tol=1e-5)
model = None
clustered = None
if processed_df.count() > 0:
    try:
        model = kmeans.fit(processed_df)
        clustered = model.transform(processed_df)
        print("[*] Clustering KMeans completato.")

        # Valutazione Finale
        print("[*] Valutazione clustering finale (Silhouette)...")
        if clustered.count() > kmeans.getK():
            try:
                evaluator = ClusteringEvaluator(featuresCol=feature_col_for_kmeans, predictionCol="prediction")
                score = evaluator.evaluate(clustered)
                print(f"\n✅ Silhouette Score Finale: {score:.4f}\n")
            except Exception as eval_err:
                print(f"\n[ATTENZIONE] Calcolo Silhouette fallito: {eval_err}\n")
        else:
            print("\n[INFO] Silhouette Score non calcolato (pochi dati).\n")

    except Exception as kmeans_err:
        print(f"\n[ERRORE] KMeans fit/transform fallito: {kmeans_err}\n"); traceback.print_exc()
        clustered = None
else:
    print("[INFO] Clustering saltato (nessun dato processato).")

# Salva Risultati CSV Finali 
if clustered is not None:
    print(f"[*] Salvataggio risultati CSV finali in: {LOCAL_OUTPUT_DIR}")
    try:
        # A. Titoli con cluster e categoria raggruppata
        clustered.select("headline", "category", "prediction") \
                 .write.mode("overwrite").option("header", True) \
                 .csv(LOCAL_OUTPUT_DIR + "topics_with_cluster")
       # B. Relazione cluster-categoria raggruppata
        cluster_category_agg = clustered.groupBy("prediction", "category").count() 
        cluster_category_agg.write.mode("overwrite").option("header", True).csv(LOCAL_OUTPUT_DIR + "topics_vs_category")
        print(f"\n[*] Composizione TOP 3 Categorie per Ciascun Cluster (K={K_CLUSTERS}):")
        windowSpec = Window.partitionBy(PREDICTION_COL).orderBy(col("count").desc())
        top_n_categories_per_cluster = cluster_category_agg.withColumn("rank", rank().over(windowSpec)) \
                                                          .filter(col("rank") <= 3) \
                                                          .orderBy(PREDICTION_COL, "rank")
        top_n_categories_per_cluster.show(n=(K_CLUSTERS * 3) + K_CLUSTERS, truncate=False)
        print(f"✅ Risultati CSV finali salvati in: {LOCAL_OUTPUT_DIR}")
    except Exception as csv_err:
        print(f"\n[ERRORE] Salvataggio CSV fallito: {csv_err}"); traceback.print_exc()
else:
    print("[INFO] Salvataggio CSV saltato (nessun dato clusterizzato).")
# Salva Modello KMeans e Modelli di Preprocessing
final_model_name = f"kmeans_embedding_{SENTENCE_MODEL_NAME.replace('-', '_')}_k{K_CLUSTERS}"
if USE_SCALER: final_model_name += "_scaled"
if USE_PCA: final_model_name += f"_pca{PCA_COMPONENTS}"

kmeans_model_path = f"{HDFS_MODEL_DIR}/{final_model_name}"

if model is not None:
     print(f"[*] Salvataggio modello KMeans finale in: {kmeans_model_path}")
     try:
        model.write().overwrite().save(kmeans_model_path)
        print(f"✅ Modello KMeans finale salvato in HDFS.")
     except Exception as save_err:
        print(f"[ERRORE] Fallito salvataggio modello KMeans: {save_err}"); traceback.print_exc()
else:
    print("[INFO] Salvataggio modello KMeans saltato.")

# Liberare cache
if 'df_with_embeddings' in locals() and df_with_embeddings.is_cached:
    df_with_embeddings.unpersist()
if 'processed_df' in locals() and hasattr(processed_df, 'is_cached') and processed_df.is_cached:
    processed_df.unpersist()

print("\n[*] Arresto sessione Spark...")
spark.stop()
print("\n🏁 Script analyze_batch.py finale completato.")
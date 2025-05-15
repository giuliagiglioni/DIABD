#import vari
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, current_timestamp, window, udf, expr, when, pandas_udf, lower, regexp_replace, length, concat_ws
from pyspark.sql.types import StructType, StructField, StringType, ArrayType, FloatType, TimestampType
from pyspark.ml.linalg import Vectors, VectorUDT
from pyspark.ml.feature import StandardScalerModel, PCAModel # Importa classi modello
from pyspark.ml.clustering import KMeansModel # Importa classe modello KMeans
from sentence_transformers import SentenceTransformer
import pandas as pd
import numpy as np
import re
import os
import sys
import traceback

# --- CONFIGURAZIONE FINALE (ALLINEATA AL BATCH OTTIMIZZATO) ---
KAFKA_BOOTSTRAP_SERVERS = "master:9092" # Usa hostname risolvibile nel cluster
KAFKA_TOPIC = "test"
HDFS_MODEL_DIR = "hdfs:///user/hadoop/models" # Dove sono salvati i modelli

# Neo4j Configuration (Neo4j gira su 'master')
NEO4J_URI = "bolt://master:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "progetto24" # ATTENZIONE: Gestire meglio in produzione!

# Parametri pipeline (DEVONO CORRISPONDERE A QUELLI USATI PER ADDDESTRARE I MODELLI SALVATI)
SENTENCE_MODEL_NAME = 'all-mpnet-base-v2'
K_CLUSTERS = 5
PCA_COMPONENTS = 40
USE_TEXT_PREPROCESSING = True # Imposta come nel batch finale
MIN_TEXT_LENGTH = 0 # Imposta come nel batch finale (0 => non filtra)
USE_SCALER = True # Imposta come nel batch finale
USE_PCA = True # Imposta come nel batch finale

# Nomi colonne pipeline (DEVONO CORRISPONDERE)
EMBEDDING_ARRAY_COL = "embedding_array"
EMBEDDING_VEC_COL = "embedding_vec"
SCALED_FEATURE_COL = "scaled_features"
PCA_FEATURE_COL = "pca_features"
FINAL_FEATURE_COL = PCA_FEATURE_COL if USE_PCA else (SCALED_FEATURE_COL if USE_SCALER else EMBEDDING_VEC_COL)
PREDICTION_COL = "prediction"

# Windowing per analisi trend
WINDOW_DURATION = "2 minutes" # Larghezza finestra
SLIDE_DURATION = "2 minutes" # Intervallo di aggiornamento
TIMESTAMP_COL = "processing_timestamp" # Timestamp aggiunto da Spark
WATERMARK_DELAY_TRENDS = "1 minute"   # Ritardo per il watermark
CONSOLE_TRIGGER_INTERVAL = "30 seconds" # Frequenza di check/stampa della console

# Costruisci percorsi modelli HDFS (con K=5)
scaler_model_path = f"{HDFS_MODEL_DIR}/scaler_model_{SENTENCE_MODEL_NAME.replace('-', '_')}"
pca_model_path = f"{HDFS_MODEL_DIR}/pca_model_{SENTENCE_MODEL_NAME.replace('-', '_')}_k{PCA_COMPONENTS}"
kmeans_model_name = f"kmeans_embedding_{SENTENCE_MODEL_NAME.replace('-', '_')}_k{K_CLUSTERS}" # Usa K=13
if USE_SCALER: kmeans_model_name += "_scaled"
if USE_PCA: kmeans_model_name += f"_pca{PCA_COMPONENTS}"
kmeans_model_path = f"{HDFS_MODEL_DIR}/{kmeans_model_name}"

HDFS_NAMENODE_URI = "hdfs://master:9000" # Definisci l'URI base del NameNode
# --- Definisci percorsi Checkpoint UNICI per ogni query ---
HDFS_CHECKPOINT_PATH_BASE = f"{HDFS_NAMENODE_URI}/user/hadoop/spark_checkpoints/k{K_CLUSTERS}" # Base per K corrente
HDFS_CHECKPOINT_PATH_NEO4J = f"{HDFS_CHECKPOINT_PATH_BASE}/neo4j_writer"
HDFS_CHECKPOINT_PATH_CONSOLE = f"{HDFS_CHECKPOINT_PATH_BASE}/console_trends"

# --- Definisci pacchetto Connector (verifica versione!) ---
NEO4J_CONNECTOR_PACKAGE = "org.neo4j.spark:neo4j-connector-apache-spark_2.12:5.2.0" # Versione esempio per Spark 3.5

# 1. Crea la sessione Spark Streaming (con config Neo4j e Pacchetto)
print("[*] Creazione sessione Spark per lo streaming...")
try:
    spark = SparkSession.builder \
        .appName(f"Streaming News K={K_CLUSTERS} -> Neo4j") \
        .master("yarn") \
        .config("spark.executor.memory", "4g") \
        .config("spark.driver.memory", "4g") \
        .config("spark.sql.execution.arrow.pyspark.enabled", "true") \
        .config("spark.jars.packages", NEO4J_CONNECTOR_PACKAGE) \
        .config("spark.neo4j.bolt.url", NEO4J_URI) \
        .config("spark.neo4j.authentication.basic.username", NEO4J_USER) \
        .config("spark.neo4j.authentication.basic.password", NEO4J_PASSWORD) \
        .getOrCreate()
except Exception as e:
    print(f"\n[ERRORE] Creazione Sessione Spark fallita.")
    print(f"Possibile causa: Problemi con il pacchetto connector '{NEO4J_CONNECTOR_PACKAGE}'. Verifica la versione e la connessione internet, o se è già specificato in spark-submit.")
    print(f"Errore: {e}"); traceback.print_exc(); sys.exit(1)

spark.sparkContext.setLogLevel("WARN")

# 2. Carica i modelli di Preprocessing e Clustering da HDFS
print(f"[*] Caricamento modelli da HDFS...")
try:
    scaler_model = StandardScalerModel.load(scaler_model_path) if USE_SCALER else None
    pca_model = PCAModel.load(pca_model_path) if USE_PCA else None
    # Carica il modello KMeans specifico K=13
    print(f"[*] Caricamento KMeans da: {kmeans_model_path}")
    kmeans_model = KMeansModel.load(kmeans_model_path)
    kmeans_model.setFeaturesCol(FINAL_FEATURE_COL) # Imposta colonna corretta
    kmeans_model.setPredictionCol(PREDICTION_COL)
    print("✅ Modelli caricati con successo.")
except Exception as e:
    print(f"\n[ERRORE] Impossibile caricare modelli da HDFS: {e}"); traceback.print_exc(); spark.stop(); sys.exit(1)

# 3. Definisci UDF (identiche al batch finale)
os.environ['HF_HOME'] = '/home/hadoop/.cache/huggingface' # Imposta cache
def clean_text(text): # Funzione Python standard
    if not text: return ""
    text = text.lower(); text = re.sub(r'https?://\S+|www\.\S+', '', text); text = re.sub(r'\s\d+\s', ' ', text); text = re.sub(r'[^\w\s]', ' ', text); text = re.sub(r'\s+', ' ', text).strip()
    return text
clean_text_udf = udf(clean_text, StringType())

@pandas_udf(ArrayType(FloatType()))
def generate_embeddings_udf(texts: pd.Series) -> pd.Series:
    global sentence_model
    if 'sentence_model' not in globals():
        print(f"[*] (UDF Stream) Caricamento modello: {SENTENCE_MODEL_NAME}...")
        try: sentence_model = SentenceTransformer(SENTENCE_MODEL_NAME); print("[*] (UDF Stream) Modello caricato.")
        except Exception as e: print(f"[ERRORE] (UDF Stream) Caricamento fallito: {e}"); raise e
    embeddings_np = sentence_model.encode(texts.to_list(), show_progress_bar=False, convert_to_numpy=True)
    return pd.Series([e.astype(np.float32).tolist() for e in embeddings_np])

to_vector_udf = udf(lambda x: Vectors.dense(x) if x is not None else None, VectorUDT())

# 4. Definisci Schema JSON da Kafka
schema = StructType([
    StructField("headline", StringType(), True),
    StructField("category", StringType(), True),
    StructField("short_description", StringType(), True)
])

# 5. Leggi lo stream da Kafka
print(f"[*] Lettura stream Kafka dal topic '{KAFKA_TOPIC}'...")
kafka_stream_df = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS) \
    .option("subscribe", KAFKA_TOPIC) \
    .option("startingOffsets", "latest") \
    .option("failOnDataLoss", "false") \
    .load()

# 6. Pipeline di Trasformazione dello Stream (definita una volta)
print("[*] Definizione trasformazioni stream...")

# Parsa JSON e aggiungi timestamp di processamento
base_stream = kafka_stream_df \
    .selectExpr("CAST(value AS STRING) as json", "timestamp as kafka_timestamp") \
    .select(from_json(col("json"), schema).alias("data"), "kafka_timestamp") \
    .select("data.*", "kafka_timestamp") \
    .withColumn(TIMESTAMP_COL, current_timestamp()) \
    .na.drop(subset=["headline", "category"])

# Applica raggruppamento categorie
category_grouped_stream = base_stream.withColumn(
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
    .otherwise(col("category")) # Mantiene nuove categorie
).drop("category").withColumnRenamed("category_temp_grouped", "category")

# Applica pulizia testo
text_prepared_stream = category_grouped_stream.withColumn(
    "text_for_embedding", # Nome temporaneo per chiarezza
    concat_ws(" ", col("headline"), col("short_description")) # <-- CONCATENA QUI
).filter(col("text_for_embedding").isNotNull() & (col("text_for_embedding") != "") & (length(col("text_for_embedding")) > 1))
if USE_TEXT_PREPROCESSING:
    text_cleaned_stream = text_prepared_stream.withColumn("text", clean_text_udf(col("text_for_embedding"))) \
                                             .filter(length(col("text")) >= MIN_TEXT_LENGTH)

# Applica pipeline ML: Embedding -> Vector -> Scaler -> PCA -> KMeans
embedded_stream = text_cleaned_stream.withColumn(EMBEDDING_ARRAY_COL, generate_embeddings_udf(col("text")))
vector_stream = embedded_stream.withColumn(EMBEDDING_VEC_COL, to_vector_udf(col(EMBEDDING_ARRAY_COL)))
scaled_stream = scaler_model.transform(vector_stream) if scaler_model else vector_stream
pca_stream = pca_model.transform(scaled_stream) if pca_model else scaled_stream
clustered_stream = kmeans_model.transform(pca_stream) # Aggiunge colonna 'prediction'

# 7. Definisci la Query di Scrittura su Neo4j (Sink 1)
print("[*] Configurazione scrittura stream su Neo4j...")
output_neo4j_df = clustered_stream.select(
    col("headline").alias("topic"),
    col("category").alias("category"), # Categoria raggruppata o nuova
    col("short_description").alias("description"),
    col(PREDICTION_COL).cast(StringType()).alias("cluster") # ID Cluster come String
)

cypher_query = """
MERGE (t:Topic {name: event.topic})
  SET t.description = event.description, // <-- AGGIUNGI SET DESCRIPTION
      t.last_seen = timestamp()
MERGE (c:Category {name: event.category}) SET c.name = event.category
MERGE (cl:Cluster {id: event.cluster}) SET cl.id = event.cluster
MERGE (t)-[:BELONGS_TO]->(c)
MERGE (cl)-[:CONTAINS]->(t)
"""

neo4j_stream_writer = output_neo4j_df.writeStream \
    .format("org.neo4j.spark.DataSource") \
    .option("checkpointLocation", HDFS_CHECKPOINT_PATH_NEO4J) \
    .option("url", NEO4J_URI) \
    .option("authentication.type", "basic") \
    .option("authentication.basic.username", NEO4J_USER) \
    .option("authentication.basic.password", NEO4J_PASSWORD) \
    .option("query", cypher_query) \
    .option("save.mode", "Append") \
    .trigger(processingTime='2 minutes')

# 8. Definisci la Query di Analisi Trend su Console (Sink 2)
print("[*] Configurazione analisi trend su finestra temporale...")
windowed_counts = clustered_stream \
    .withWatermark(TIMESTAMP_COL, WATERMARK_DELAY_TRENDS) \
    .groupBy(
        window(col(TIMESTAMP_COL), WINDOW_DURATION, SLIDE_DURATION),
        col(PREDICTION_COL).alias("ClusterID")
    ).count()

trend_stream_writer = windowed_counts.writeStream \
    .outputMode("update") \
    .format("console") \
    .option("truncate", "false") \
    .option("checkpointLocation", HDFS_CHECKPOINT_PATH_CONSOLE) \
    .trigger(processingTime=CONSOLE_TRIGGER_INTERVAL) # Stampa ogni minuto

# --- Avvio delle query ---
try:
    print("[*] Avvio scrittura stream su Neo4j...")
    query_neo4j = neo4j_stream_writer.start()

    print("[*] Avvio analisi trend su console...")
    query_trends = trend_stream_writer.start()

    print(f"\n\n📡 Streaming Attivo!")
    print(f"   Aggiornamenti Neo4j -> {NEO4J_URI} ") # Usa la variabile dell'intervallo
    print(f"   Analisi Trend (K={K_CLUSTERS}) ") # Usa la variabile dell'intervallo
    print("\n" + "="*70)
    print("   INTERPRETAZIONE OUTPUT TRENDS SULLA CONSOLE (TUMBLING WINDOWS):")
    print("   - Verrà stampata una tabella solo quando una finestra temporale (es. 10 min) si chiude e ha dati.")
    print("   - Ogni tabella mostra i conteggi PER QUEL BLOCCO DI TEMPO SPECIFICO.")
    print(f"   - I 'ClusterID' (da 0 a {K_CLUSTERS-1}) sono ORDINATI per 'count' DECRESCENTE.")
    print("   - Il ClusterID IN CIMA ALLA LISTA è il TEMA PIU' FREQUENTE in quel blocco di tempo.")
    print("   - Per capire COSA rappresenta quel ClusterID, esamina i suoi contenuti (titoli) nel grafo Neo4j usando la query Cypher appropriata.")
    print("="*70 + "\n")
    print("\n   Attendere l'elaborazione dei batch dopo l'invio di notizie dal producer.")
    print("   Premi CTRL+C per terminare.")
    spark.streams.awaitAnyTermination() # Attende che una delle query venga terminata

except KeyboardInterrupt:
    print("\n[*] Ricevuto CTRL+C. Arresto in corso...")
except Exception as e:
    print(f"\n❌ Errore stream:") ; traceback.print_exc(); sys.exit(1)

finally:
    print("\n[*] Arresto delle query e della sessione Spark...")
    stopped_neo4j = False
    stopped_trends = False
    try:
        if 'query_neo4j' in locals() and query_neo4j.isActive:
            print("[*] Stopping Neo4j query...")
            query_neo4j.stop()
            stopped_neo4j = True
        if 'query_trends' in locals() and query_trends.isActive:
            print("[*] Stopping trends query...")
            query_trends.stop()
            stopped_trends = True
        # Attendi un po' per permettere lo stop pulito
        if stopped_neo4j: query_neo4j.awaitTermination(timeout=60)
        if stopped_trends: query_trends.awaitTermination(timeout=60)

        spark.stop()
        print("[*] Sessione Spark arrestata.")
    except Exception as stop_err:
        print(f"[WARN] Errore durante lo stop: {stop_err}")
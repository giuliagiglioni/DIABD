# 🧠 TrendSpotter: Analisi e Raccomandazione di Trend Emergenti da Flussi di Dati

## 🚀 Introduzione

**TrendSpotter** è un sistema distribuito progettato per l'identificazione e la raccomandazione di **trend emergenti** in tempo reale. Simula scenari di monitoraggio simili a Twitter Trends, Google News o aggregatori di flussi RSS, sfruttando tecnologie Big Data per offrire una soluzione completa: ingestione di dati in streaming, analisi testuale avanzata, clustering per l'identificazione di topic e visualizzazione semantica tramite grafo.

### 🎯 Obiettivi Principali

1.  **Identificare e Monitorare Trend:** Individuare i **temi** (argomenti) più **frequenti e rilevanti** nei dati recenti (identificati tramite clustering semantico) e **monitorarne l'attività** nel tempo tramite analisi aggregata del flusso streaming.
2.  **Abilitare Raccomandazioni:** Costruire una struttura dati (grafo) che permetta di generare raccomandazioni personalizzate basate sugli interessi degli utenti (simulati) e sulle correlazioni tra argomenti (topic/cluster) e categorie (potenzialità dimostrata tramite query Cypher di esempio).
3.  **Visualizzare Relazioni:** Offrire una rappresentazione visiva chiara dei legami tra argomenti (topic), categorie editoriali (raggruppate), cluster tematici (scoperti automaticamente) e utenti.

## 🧰 Stack Tecnologico

| Tecnologia        | Scopo                                                                         |
| :---------------- | :---------------------------------------------------------------------------- |
| **Apache Kafka** | Ingestione e buffering di flussi di notizie simulate in tempo reale (`news` topic). |
| **Apache Spark 3.5.0** | Elaborazione distribuita (batch/streaming), generazione Sentence Embeddings (`sentence-transformers`), preprocessing feature (Scaling, PCA), clustering (KMeans K=13), analisi di trend su finestre temporali. |
| **Apache Hadoop 3.2.4** | Archiviazione distribuita (HDFS per dataset originale, modelli Scaler/PCA/KMeans, checkpoints), gestione risorse cluster (YARN). |
| **Neo4j 4.4 (Community)** | Modellazione, persistenza (su VM `master`) e visualizzazione del grafo della conoscenza. |
| **Python/PySpark**| Linguaggio principale per lo sviluppo, incluse librerie NLP, ML, Kafka e Neo4j. |
| **Sentence Transformers** | Libreria Python per generare embedding semantici di alta qualità (`all-mpnet-base-v2`). |
| **Neo4j Spark Connector (v5.2.0)** | Libreria Spark per leggere/scrivere dati direttamente da Spark Streaming a Neo4j. |
| **Java 11 (OpenJDK)** | Ambiente di esecuzione per Hadoop, Spark e Neo4j 4.4 sul cluster. |


## 📦 Dataset Utilizzato

* **Dataset Iniziale:** `News_Category_Dataset_v3.json` (caricato su `hdfs:///user/hadoop/news/`). Colonne usate: `headline`, `short_description`, `category`, `date`.
* **Dati di Streaming (Simulati):** Messaggi JSON con `headline` e `category` originale inviati al topic Kafka `news` da `kafka/producer.py` (o versione che legge da file).

## 🧪 Preprocessing Dati Applicato (in Batch e Stream)

1.  **Filtraggio Temporale:** Conservati solo record con `date >= "2020-01-01"` per focalizzarsi sui dati recenti (~5500 record).
2.  **Raggruppamento Categorie:** Le 42 categorie originali sono state mappate manualmente a **22 categorie semantiche** più coerenti (es. `ARTS_CULTURE`, `BUSINESS_FINANCE`, `PARENTING_FAMILY`, `VOICES`, `GOOD_WEIRD_NEWS`, `OTHER`, ecc.). La colonna `category` finale contiene questi nomi raggruppati (le categorie nuove/sconosciute nello stream vengono mantenute con il loro nome originale).
3.  **Pulizia Testo:** Applicata pulizia standard (lowercase, rimozione URL/numeri/punteggiatura) al testo (`headline` + `short_description` nel batch, solo `headline` nello stream) prima della generazione degli embedding. Filtrati testi con `MIN_TEXT_LENGTH=0` (nessun filtro lunghezza attivo nella versione finale).

## ✨ Pipeline ML Avanzata e Clustering (in Batch e Stream)

Per ottenere cluster tematici significativi, è stata implementata la seguente pipeline:
1.  **Sentence Embeddings:** Il testo viene convertito in vettori densi (768d) usando **`all-mpnet-base-v2`** (`sentence-transformers` via Pandas UDF).
2.  **Conversione a VectorUDT:** Gli array di embedding vengono convertiti nel formato `VectorUDT` di Spark ML.
3.  **Feature Scaling:** Applicato **`StandardScaler`** ai vettori embedding per standardizzarli (addestrato nel batch, applicato nello stream).
4.  **Dimensionality Reduction (PCA):** Applicata **PCA** per ridurre le feature a **40 componenti**, mantenendo la maggior parte della varianza (~75-80% osservato) ma riducendo il rumore e la complessità computazionale per KMeans.
5.  **Clustering (KMeans):** Applicato **KMeans** alle feature finali (post-PCA). Il numero ottimale di cluster identificato sperimentalmente è **K=13**, ottenendo un **Silhouette Score di ~0.135** nel batch. Questo punteggio indica una struttura di cluster moderatamente definita e semanticamente più coerente rispetto all'approccio TF-IDF base.
6.  **Salvataggio/Caricamento Modelli:** I modelli `StandardScaler`, `PCA`, e `KMeans` (K=13) addestrati sul batch (`analyze_batch.py`) vengono salvati su HDFS e caricati dallo `streaming_job.py` per garantire coerenza nell'elaborazione in tempo reale.

## 📈 Identificazione Trend

L'identificazione dei trend si basa sull'analisi dei **13 cluster significativi** ottenuti:
* **Trend Dominanti (Batch):** Identificati tramite la **frequenza** (numero di notizie) per ciascun cluster nei dati batch (`topics_vs_category.csv` o query Neo4j).
* **Trend Emergenti (Streaming):** Monitorati tramite **Spark Streaming con finestre temporali**. Lo script `streaming_job.py` calcola e **stampa sulla console** la frequenza di ciascun cluster (ID 0-12) per finestre temporali definite (es. ogni 5 min sull'ultima ora). Un aumento significativo di questi conteggi per un cluster indica un trend emergente. L'analisi qualitativa dei topic nel cluster (tramite Neo4j) ne rivela il significato.

## 🕸️ Grafo Neo4j e Raccomandazioni

* **Aggiornamento Grafo:**
    * **Batch:** `graph_builder.py` (eseguito su `master`) popola Neo4j inizialmente leggendo l'output CSV del job batch (`topics_with_cluster`).
    * **Streaming:** `streaming_job.py`, usando il **Neo4j Spark Connector**, scrive i risultati di ogni micro-batch (headline, category processata, cluster ID) **direttamente su Neo4j** (in esecuzione su `master`) tramite query `MERGE`, mantenendo il grafo aggiornato in (near) real-time.
* **Esplorazione:** Neo4j Browser (`http://master:7474` accessibile dall'host Windows) permette di visualizzare i legami tra `:Topic`, `:Category` (raggruppate), `:Cluster` (0-12), `:User`.
* **Raccomandazioni:** La struttura del grafo abilita raccomandazioni content-based e collaborative (dimostrabili via Cypher).

## 📁 Struttura del Progetto (Finale)
TrendSpotter-Cluster/    (in /home/hadoop/ sulla VM master)
│
├── kafka/
│   ├── producer.py
│   └── sample_news.jsonl  (Opzionale: file per producer)
│
├── spark_jobs/
│   ├── analyze_batch.py     # Script batch finale K=13, salva modelli Scaler/PCA/KMeans
│   └── streaming_job.py     # Script stream finale: carica modelli, scrive su Neo4j, monitora trend
│
├── neo4j/
│   └── scripts/
│       └── graph_builder.py   # Per caricamento batch iniziale da CSV locale su master
│       # update_graph.py NON più necessario
│
├── models/ (SU HDFS!)       # Percorso: hdfs:///user/hadoop/models/
│   ├── scaler_model_.../
│   ├── pca_model_.../
│   └── kmeans_embedding_..._k13_scaled_pca40/
│
├── data/                    # Dati locali sulla VM master
│   └── output/              # Output CSV batch K=13
│       ├── topics_with_cluster/
│       └── topics_vs_category/
│
├── scripts/                 # Script di utilità o setup
│   └── list_categories.py
│
└── README.md                # Questo file
## 🚀 Come Eseguire il Progetto (Ordine Finale)

1.  **Setup Completo:** Verificare che Hadoop(HDFS/YARN), Spark 3.5, Kafka, Neo4j 4.4 (su `master`), Java 11 siano installati, configurati e attivi sulle VM. Verificare librerie Python (`pandas`, `pyarrow`, `torch`, `sentence-transformers`, `neo4j`, `kafka-python`). Caricare `News_Category_Dataset_v3.json` su HDFS.
2.  **Esecuzione Analisi Batch (Finale)** (da `master`):
    ```bash
    cd ~/TrendSpotter-Cluster
    # Assicurati che PYSPARK_PYTHON sia impostato correttamente se necessario
    # export PYSPARK_PYTHON=/usr/bin/python3.8 # O Python 3.x corretto
    spark-submit --master yarn spark_jobs/analyze_batch.py
    ```
    *(Salva modelli su HDFS e CSV K=13 localmente in `data/output/`)*
3.  **Costruzione Grafo Iniziale** (da `master`):
    ```bash
    cd ~/TrendSpotter-Cluster/neo4j/scripts
    # Verifica che il path in graph_builder.py sia corretto (es. "../../data/output/topics_with_cluster/part-*.csv")
    # Verifica che l'URI Neo4j sia "bolt://master:7687"
    python graph_builder.py
    ```
4.  **Avvio Job di Streaming** (da `master`):
    ```bash
    cd ~/TrendSpotter-Cluster
    # Assicurati che NEO4J_CONNECTOR_VERSION sia corretta (Es. 5.2.0 per Spark 3.5)
    NEO4J_CONNECTOR_VERSION="5.2.0"
    spark-submit   --master yarn   --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,
    org.neo4j:neo4j-connector-apache-spark_2.12:5.3.6_for_spark_3 streaming_job_final.py 
    ```
    *(Lascia in esecuzione. Monitora la console per i trend, Neo4j Browser per gli aggiornamenti del grafo)*
5.  **Avvio Producer Kafka** (da `master`, nuovo terminale):
    ```bash
    cd ~/TrendSpotter-Cluster/kafka
    python producer.py # O la versione che legge da file
    ```

## 📊 Query Neo4j Utili

*(Inserire qui le 8 query Cypher di esempio fornite in precedenza per esplorazione e raccomandazioni)*
```cypher
// Query 1: Statistiche Generali...
// Query 2: Cluster Più Frequenti...
// Query 3: Categorie Più Frequenti...
// Query 4: Esplora Contenuto Cluster (es. ID '3')...
// Query 5: Composizione Categorie in un Cluster (es. ID '3')...
// Query 6: Raccomandazione Basata su Cluster per 'Alessia'...
// Query 7: Raccomandazione Basata su Categoria per 'Alessia'...
// Query 8: Utenti Interessati a Topic nel Cluster (es. ID '3')...

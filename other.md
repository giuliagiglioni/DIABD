# 🧠 TrendSpotter: Analisi e Raccomandazione di Trend Emergenti da Flussi di Dati

## 🚀 Introduzione

**TrendSpotter** è un sistema distribuito per l'identificazione e la raccomandazione di **trend emergenti** in tempo reale, pensato per scenari simili a Twitter Trends, Google News, o flussi RSS. Il sistema sfrutta il meglio delle tecnologie Big Data per offrire una soluzione completa: raccolta dati in streaming, analisi testuale, clustering intelligente e visualizzazione semantica.

### 🎯 Obiettivi

1. Individuare e monitorare gli argomenti più discussi e rilevanti nel tempo.
2. Simulare utenti e generare raccomandazioni basate su interessi e contenuti simili.
3. Visualizzare i legami tra argomenti, categorie e utenti in un grafo informativo.

## 🧰 Tecnologie Utilizzate

| Tecnologia    | Scopo                                                                 |
|---------------|-----------------------------------------------------------------------|
| **Apache Kafka** | Simulazione dello stream di notizie e messaggi real-time             |
| **Apache Spark** | Analisi testuale in batch e streaming (TF-IDF, KMeans, clustering)  |
| **Apache Hadoop**| Archiviazione e gestione distribuita (HDFS + YARN)                 |
| **Neo4j**        | Visualizzazione e modellazione delle relazioni tra topic e utenti   |
| **Python + PySpark** | Scripting e machine learning distribuito                        |

## 📦 Dataset

- Dataset iniziale: **News Category Dataset** (Kaggle)
  - `headline`: titolo della notizia
  - `short_description`: breve descrizione
  - `category`: categoria assegnata

Durante lo streaming, Kafka simula nuovi articoli con:
```json
{
  "headline": "AI breakthrough transforms medical diagnosis",
  "category": "TECH"
}
```

## 🏗️ Architettura Distribuita

Costruita su un cluster Hadoop (3 VM):

- 🧠 **Master Node**: NameNode, ResourceManager, Kafka, Spark Master
- ⚙️ **2 Worker Node**: DataNode, NodeManager, Spark Worker

```
Kafka → Spark Streaming → HDFS/Neo4j
         ↑
   User/News Generator
```

## 📁 Struttura del Progetto

```
TrendSpotter-Cluster/
│
├── kafka/
│   └── producer.py
│
├── spark_jobs/
│   ├── analyze_batch.py
│   └── streaming_job.py
│
├── neo4j/
│   └── scripts/
│       ├── graph_builder.py
│       └── update_graph.py
│
├── models/                 ← modelli TF, IDF, KMeans
├── data/
│   └── output/             ← risultati batch/streaming
├── scripts/
│   └── cluster_setup/      ← script installazione su VM
└── README.md
```

## 🔁 Flusso Operativo

1. `analyze_batch.py` (su master):
   - Pulisce il dataset, calcola TF-IDF, clusterizza
   - Salva modelli e CSV in `/data/output/`
2. `graph_builder.py` (su macchina con Neo4j Desktop):
   - Costruisce il grafo iniziale con Topic, Cluster, Category
3. `producer.py` (su master):
   - Invia notizie simulate a Kafka
4. `streaming_job.py` (su master):
   - Riceve notizie live da Kafka, assegna cluster usando modelli preaddestrati, salva CSV su HDFS
5. `update_graph.py` (su macchina con Neo4j Desktop):
   - Aggiorna il grafo con i nuovi topic ricevuti via Kafka

## ⚙️ File di Configurazione Importanti

### Hadoop `core-site.xml`
```xml
<configuration>
  <property>
    <name>fs.defaultFS</name>
    <value>hdfs://master:9000</value>
  </property>
</configuration>
```

### Hadoop `hdfs-site.xml`
```xml
<configuration>
  <property>
    <name>dfs.replication</name>
    <value>2</value>
  </property>
</configuration>
```

### Hadoop `yarn-site.xml`
```xml
<configuration>
  <property>
    <name>yarn.nodemanager.aux-services</name>
    <value>mapreduce_shuffle</value>
  </property>
</configuration>
```

### Spark `spark-env.sh`
```bash
export SPARK_MASTER_HOST=master
export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
export HADOOP_CONF_DIR=/home/hadoop/hadoop/etc/hadoop
```

### Kafka (su master)
```bash
# Esempio avvio
bin/zookeeper-server-start.sh config/zookeeper.properties
bin/kafka-server-start.sh config/server.properties
```

### Neo4j `.env` o configurazione credenziali
```
uri = "bolt://localhost:7687"
user = "neo4j"
password = "progetto24"
```

## 📊 Visualizzazione in Neo4j

- Dopo `graph_builder.py`, visualizza su Neo4j Desktop
- Filtro nodi: `Topic`, `Category`, `Cluster`, `User`
- Relazioni:
  - `(:Topic)-[:BELONGS_TO]->(:Category)`
  - `(:Cluster)-[:CONTAINS]->(:Topic)`
  - `(:User)-[:INTERESTED_IN]->(:Topic)`

## 💬 Comandi di Esecuzione (ordine corretto)

1. **HDFS e YARN** (da `master`):
```bash
start-dfs.sh
start-yarn.sh
```

2. **Kafka** (da `master`):
```bash
zookeeper-server-start.sh config/zookeeper.properties
kafka-server-start.sh config/server.properties
```

3. **Analisi Batch** (su `master`):
```bash
spark-submit --master yarn spark_jobs/analyze_batch.py
```

4. **Costruzione Grafo** (su host Windows con cartella condivisa):
```bash
python neo4j/scripts/graph_builder.py
```

5. **Streaming Kafka (su master)**:
```bash
spark-submit \
  --master yarn \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 \
  spark_jobs/streaming_job.py
```

6. **Producer Kafka**:
```bash
python kafka/producer.py
```

7. **Aggiornamento Grafo** (Neo4j host):
```bash
python neo4j/scripts/update_graph.py
```

## 📋 Requisiti Minimi

- 🖥️ 3 VM Ubuntu 20.04, 8GB RAM ciascuna
- Java 8, Python 3.10+
- Hadoop 3.2.4, Spark 3.5.0, Kafka 3.6.0
- Neo4j Desktop o Server 5.x

## ✅ Conclusione

TrendSpotter è un progetto **maturo, distribuito e interattivo**, che dimostra la potenza del data processing moderno. Il flusso end-to-end consente di:
- Ingerire dati real-time
- Estrarre pattern e argomenti rilevanti
- Simulare utenti e interessi
- Visualizzare conoscenza in un grafo interattivo

Un esempio concreto di come Big Data e AI possano supportare sistemi informativi intelligenti e dinamici.

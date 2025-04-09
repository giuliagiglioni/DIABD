# TrendSpotter: Analisi e Raccomandazione di Trend Emergenti da Flussi di Dati

## Introduzione

Il progetto **TrendSpotter** si propone di identificare e raccomandare **trend emergenti** a partire da flussi di dati in tempo reale, simulando un sistema di monitoraggio in stile Twitter, Google Trends o portali news. Utilizzando tecnologie distribuite come **Apache Spark**, **Kafka**, **Hadoop** e **Neo4j**, il sistema analizza contenuti testuali prodotti da utenti, estrae le informazioni più rilevanti e costruisce un grafo di argomenti, utenti e categorie.

L'obiettivo finale è duplice:
1. Individuare gli argomenti più influenti o frequenti in un determinato periodo;
2. Raccomandare contenuti o interessi personalizzati, in base alla rete di correlazioni tra utenti e topic.

## Tecnologie Utilizzate

- **Apache Kafka**: per la simulazione di uno stream continuo di messaggi testuali (es. tweet, notizie);
- **Apache Spark** (Streaming e MLlib): per l'elaborazione distribuita in real-time e l'analisi dei dati testuali;
- **Apache Hadoop** (HDFS + YARN): per l'archiviazione distribuita dei dataset e dei dati elaborati;
- **Neo4j**: per la visualizzazione e gestione delle relazioni tra utenti, argomenti e categorie;
- **Python** (PySpark): linguaggio principale per lo sviluppo degli script Spark e Kafka.

## Dataset

Il dataset è composto da **frasi testuali simulate** che rappresentano titoli di notizie, tweet, post social o commenti. Ogni evento contiene:
- `user_id`: identificativo dell'utente;
- `timestamp`: data e ora dell'interazione;
- `text`: contenuto testuale da analizzare.

Esempio:
```json
{
  "user_id": 42,
  "timestamp": "2025-04-09T10:12:00",
  "text": "AI is revolutionizing healthcare in 2025"
}
```

Le fonti possono includere:
- Dataset Kaggle (es. News Category, Sentiment140);
- Feed RSS convertiti in formato JSON;
- Generazione casuale controllata con parole chiave.

## Architettura del Sistema

Il sistema è costruito su un cluster Hadoop con tre VM Ubuntu:
- **1 nodo master**: gestisce HDFS (NameNode) e YARN (Resource Manager);
- **2 nodi worker**: eseguono i task Spark e Hadoop (DataNode + NodeManager).

Il flusso dati è il seguente:
1. Kafka produce eventi in tempo reale.
2. Spark Streaming consuma i dati dal topic e applica pulizia, TF-IDF e clustering.
3. I topic identificati vengono salvati su HDFS e Neo4j.
4. In Neo4j si costruisce un grafo tra utenti, argomenti, e categorie.
5. Si calcola PageRank e centralità dei topic per ottenere i più influenti.

## Componenti Principali

- `kafka/producer.py`: simula eventi testuali da utenti
- `spark_jobs/streaming_job.py`: riceve eventi e li elabora in real-time
- `spark_jobs/analyze_batch.py`: job offline per TF-IDF e clustering
- `neo4j/scripts/graph_builder.py`: costruisce il grafo degli argomenti
- `scripts/cluster_setup/`: setup Hadoop, Spark, Neo4j su VM
- `data/`: contiene dataset statici iniziali e risultati

## Output Attesi

- File HDFS con i topic più frequenti e clusterizzati
- Grafo visivo in Neo4j con:
  - `(:User)-[:INTERESTED_IN]->(:Topic)`
  - `(:Topic)-[:RELATED_TO]->(:Topic)`
  - `(:Topic)-[:BELONGS_TO]->(:Category)`
- Raccomandazioni generate in base alla similarità tra utenti e topic

## Requisiti

- Ubuntu 20.04 su VirtualBox (3 VM, 4 core, 8GB ciascuna)
- Java 8
- Hadoop 3.2.4
- Spark 3.5+
- Kafka 3.6+
- Neo4j Desktop o Server
- Python 3.10+

## Estensioni Possibili

- Dashboard Streamlit per mostrare i trend in tempo reale
- Integrazione con un Vector DB (es. Qdrant) per similarità semantica
- Integrazione con modelli LLM (Retrieval-Augmented Generation) per spiegazioni automatiche dei trend

## Conclusioni

TrendSpotter è un sistema completo che combina streaming, big data e grafi per affrontare un problema moderno: la comprensione e la raccomandazione di contenuti emergenti. Il progetto permette di toccare con mano molte tecnologie centrali del corso, mantenendo una struttura scalabile, flessibile e facilmente estendibile.


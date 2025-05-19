# TrendSpotter: Analysis and Recommendation Enablement from Emerging Trends in Data Streams

## Table of Contents

* [🚀 Introduction](#-introduction)
* [🧰 Technology Stack](#-technology-stack)
* [📦 Dataset Used](#-dataset-used)
* [📁 Project Structure](#-project-structure)
* [🛠️ Architecture Setup and Installation](#️-architecture-setup-and-installation)
* [🧪 Data Preprocessing (Batch and Stream)](#-data-preprocessing-batch-and-stream)
* [✨ Advanced ML Pipeline and Clustering (Batch and Stream)](#-advanced-ml-pipeline-and-clustering-batch-and-stream)
* [📈 Trend Identification and Monitoring](#-trend-identification-and-monitoring)
* [🕸️ Neo4j Graph and Recommendation Enablement](#️-neo4j-graph-and-recommendation-enablement)
* [🚀 How to Run the Project](#-how-to-run-the-project)
* [📊 Neo4j Queries Used](#-neo4j-queries-used)
* [✅ Conclusions](#-conclusions)

---

🇮🇹 This README is available in Italian [here](README.md)

---

## 🚀 Introduction

**TrendSpotter** is a distributed system designed for the real-time identification of **emerging trends** and for building a data structure that **enables personalized recommendations**. Inspired by dynamic platforms such as Twitter Trends and Google News, the system orchestrates a powerful Big Data stack: from continuous data stream ingestion (simulated via Kafka), to advanced semantic text analysis (with Sentence Embeddings), to intelligent clustering (optimized KMeans) for topic discovery, and finally to graph construction in Neo4j.

This project goes beyond basic data processing by creating a relational data structure that supports recommendation systems, demonstrating how the synergy of Kafka, Spark, Hadoop, and Neo4j can bring intelligent and dynamic information systems to life.

### 🎯 Main Goals

1. **Identify and Monitor Trends:** The system identifies the most **frequent and relevant topics** within recent news data (filtered from 2020 onward) using advanced semantic clustering (K=5). These themes are **monitored over time** through a streaming flow analysis based on **non-overlapping tumbling windows**, with aggregated results printed in console using `outputMode("update")` for clear sequential interpretation.

2. **Enable Personalized Recommendations (via Graph):** A rich **Neo4j graph structure** was built to model relationships between users (simulated), news/topics (`headline` and `short_description`), their assigned cluster, and editorial categories. This structure **enables various types of personalized recommendations**, demonstrated via example Cypher queries (without implementing collaborative ML algorithms like ALS in Spark).

3. **Visualize Complex Relationships:** A **clear and interactive visual representation** (via Neo4j Browser) shows links between topics, categories, clusters, and simulated users, enabling intuitive data exploration.

---

## 🧰 Technology Stack

| Technology                | Main Purpose                                                                                                  | Version          |
|--------------------------|----------------------------------------------------------------------------------------------------------------|------------------|
| **Apache Kafka**         | Ingestion and buffering of real-time simulated news streams                                                   | 3.6.0            |
| **Apache Spark**         | Distributed batch and streaming processing; sentence embeddings; preprocessing (Scaler, PCA); clustering     | 3.5.0            |
| **Apache Hadoop**        | Distributed storage (HDFS); resource management (YARN)                                                        | 3.2.4            |
| **Neo4j Community Edition** | Knowledge graph modeling and visualization (on `master` VM)                                                 | 4.4.x            |
| **Python & PySpark**     | Main programming language and API interface                                                                  | Python 3.8+      |
| **Sentence Transformers**| High-quality semantic embeddings generation                                                                   | Latest stable    |
| **Neo4j Spark Connector**| Streaming integration with Neo4j from Spark                                                                   | 5.2.0+           |
| **Java (OpenJDK)**       | Runtime environment for Hadoop, Spark, and Neo4j                                                              | Java 11          |

---

## 📦 Dataset Used

* **Main Dataset:** [News Category Dataset](https://www.kaggle.com/datasets/rmisra/news-category-dataset)
    * `headline`: News title
    * `short_description`: Short text
    * `category`: Original category
    * `date`: Publication date (YYYY-MM-DD)

* **Streaming Data (Simulated):** Kafka producer sends JSON messages like:
    ```json
    {"headline": "News Title 1", "category": "CATEGORY_NAME_1", "short_description": "Short description..."}
    {"headline": "News Title 2", "category": "CATEGORY_NAME_2", "short_description": "Another description..."}   
    ```

## 📁 Project Structure
```
TrendSpotter-Cluster/
│
├── kafka/
│ ├── producer.py
│ └── sample_news.jsonl
│
├── scripts/
│ ├── analyze_batch.py
│ ├── streaming_job.py
│ └── graph_builder.py
│
├── models/ (on HDFS)
│ ├── scaler_model/
│ ├── pca_model/
│ └── kmeans_model/
│
├── data/
│ └── output/
│ ├── topics_with_cluster/
│ └── topics_vs_category/
│
├── setup/
│ ├── setup_hadoop.sh
│ ├── setup_spark.sh
│ └── setup_kafka.sh
```


---

## 🛠️ Architecture Setup and Installation

The system is deployed on a 3-node VM cluster (Ubuntu 20.04):

- **master**: NameNode, ResourceManager, Kafka Broker, Neo4j, Spark driver
- **worker1**/**worker2**: DataNode, NodeManager, Spark workers

All installation details, network setup, SSH config, and setup scripts are explained in the original [README.md](README.md).

---

## 🧪 Data Preprocessing (Batch and Stream)

Key preprocessing steps include:

1. **Date Filtering:** Only records from 2020 onwards are considered (about 5500 entries).
2. **Category Grouping:** 42 original categories are manually grouped into 22 meaningful categories (e.g., `BUSINESS_FINANCE`, `GOOD_WEIRD_NEWS`, `OTHER`).
3. **Text Cleaning:** Headlines and descriptions are lowercased, URLs/numbers/punctuation cleaned. No min-length filter.

---

## ✨ Advanced ML Pipeline and Clustering (Batch and Stream)

1. **Sentence Embeddings:** 768-dim embeddings from `all-mpnet-base-v2` model.
2. **Conversion to VectorUDT:** Required for Spark ML compatibility.
3. **Feature Scaling:** Standardization via Z-score.
4. **Dimensionality Reduction:** PCA to 40 components.
5. **Clustering:** KMeans with K=5, based on empirical tuning (Silhouette ≈ 0.13).
6. **Model Persistence:** Models trained in batch are saved to HDFS and reused in stream jobs.

---

## 📈 Trend Identification and Monitoring

- **Batch:** Trends identified by cluster size and category composition.
- **Streaming:** Tumbling windows via Spark Streaming print per-window topic counts by cluster ID, enabling trend detection over time.

---

## 🕸️ Neo4j Graph and Recommendation Enablement

- **Batch (graph_builder.py):** Loads CSVs into Neo4j.
- **Streaming (streaming_job.py):** Updates Neo4j live via connector.
- **Cypher Queries:** Used for personalized recommendations, trend exploration, and graph statistics.

---

## 🚀 How to Run the Project

See section [🚀 Come Eseguire il Progetto](README.md#-come-eseguire-il-progetto) in the Italian README for full instructions, including:

- Starting HDFS, YARN, Kafka, Neo4j
- Running batch and streaming jobs
- Kafka producer usage
- Viewing results in Neo4j and console

---

## 📊 Neo4j Queries Used

Includes:
- Graph stats
- Top clusters and categories
- User-based recommendations (cluster/category)
- Cluster composition
- Neo4j Cypher examples

Full list in [README.md](README.md#-query-neo4j-utilizzate)

---

## ✅ Conclusions

TrendSpotter demonstrates a full Big Data pipeline for textual trend analysis using Kafka, Spark, Hadoop, and Neo4j. It integrates advanced NLP (Sentence Embeddings) and ML (Scaler, PCA, KMeans) to discover meaningful topic clusters. Trends are monitored both in batch and via Spark Streaming, while a graph-based structure enables exploration and personalized recommendations via Cypher. This project is a strong example of real-world Big Data architecture and analysis.



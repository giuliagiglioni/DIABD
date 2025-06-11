# TrendSpotter: Analisi e Abilitazione di Raccomandazioni da Trend Emergenti su Flussi di Dati
## Indice

* [🚀 Introduzione](#-introduzione)
* [🧰 Stack Tecnologico](#-stack-tecnologico)
* [📦 Dataset Utilizzato](#-dataset-utilizzato)
* [📁 Struttura del Progetto](#-struttura-del-progetto)
* [🛠️ Setup Architettura e Installazione](#️-setup-architettura-e-installazione)
* [🧪 Preprocessing Dati (in Batch e Stream)](#-preprocessing-dati-in-batch-e-stream)
* [✨ Pipeline ML Avanzata e Clustering (Batch e Stream)](#-pipeline-ml-avanzata-e-clustering-batch-e-stream)
* [📈 Identificazione e Monitoraggio dei Trend](#-identificazione-e-monitoraggio-dei-trend)
* [🕸️ Grafo Neo4j e Abilitazione Raccomandazioni](#️-grafo-neo4j-e-abilitazione-raccomandazioni)
* [🌐 Overview del Sistema](#-overview-del-sistema)
* [🚀 Come Eseguire il Progetto](#-come-eseguire-il-progetto)
* [📊 Query Neo4j Utilizzate](#-query-neo4j-utilizzate)
* [✅ Conclusioni](#-conclusioni)


🇮🇹 Questo progetto è descritto in italiano.  
🌍 [Read this README in English](README.en.md)

## 🚀 Introduzione

**TrendSpotter** è un sistema distribuito progettato per l'identificazione di **trend emergenti** in tempo reale e per costruire una base dati che **abilita la generazione di raccomandazioni**. Prendendo ispirazione da piattaforme dinamiche come Twitter Trends e Google News, il sistema orchestra un potente insieme di tecnologie Big Data: dall'ingestione di flussi di dati continui (simulati tramite Kafka), all'analisi testuale semantica avanzata (con Sentence Embeddings), al clustering intelligente per la scoperta di topic, fino alla costruzione di un grafo in Neo4j.

Questo progetto non si limita a processare dati, ma mira a creare una struttura dati relazionale che può servire come fondamenta per sistemi di raccomandazioni, dimostrando come l'integrazione di Kafka, Spark, Hadoop e Neo4j possa dare vita a sistemi informativi dinamici e intelligenti.

### 🎯 Obiettivi Principali

1.  **Identificare e Monitorare Trend:** Il sistema individua i **topics** (argomenti) più **frequenti e rilevanti** all'interno dei dati di notizie recenti (filtrati dal 2020 in poi). Questo viene realizzato tramite un clustering semantico avanzato (configurato per **K=5** cluster). L'attività di questi topics viene poi **monitorata nel tempo** grazie all'analisi del flusso streaming con **finestre temporali non sovrapposte (tumbling windows)**, i cui risultati aggregati (conteggi per cluster) vengono visualizzati sulla console con `outputMode("update")` per una chiara interpretazione sequenziale.
2.  **Abilitare Raccomandazioni Personalizzate (tramite Grafo):** È stata costruita una ricca **struttura a grafo in Neo4j** che modella le relazioni tra utenti (simulati), notizie/topic (con `headline` e `short_description`), i 5 cluster tematici a cui appartengono e le loro categorie editoriali (raggruppate). Questa struttura **abilita la generazione di diverse tipologie di raccomandazioni personalizzate**, la cui potenzialità è **dimostrata tramite query Cypher esemplificative**, senza l'implementazione di algoritmi di Machine Learning specifici per la raccomandazione (come ALS) all'interno di Spark.
3.  **Visualizzare Complesse Relazioni:** Viene offerta una **rappresentazione visiva chiara ed interattiva** (tramite Neo4j Browser) delle relazioni tra topic, categorie, cluster e utenti simulati, permettendo un'esplorazione intuitiva dei dati.

## 🧰 Stack Tecnologico

| Tecnologia                 | Scopo Principale nel Progetto                                                                                                | Versione (Indicativa) |
| :------------------------- | :--------------------------------------------------------------------------------------------------------------------------- | :-------------------- |
| **Apache Kafka** | Ingestione e buffering di flussi di notizie simulate in tempo reale.                  | 3.6.0                 |
| **Apache Spark** | Elaborazione distribuita batch e streaming; generazione Sentence Embeddings (`all-mpnet-base-v2`); preprocessing feature (Scaler, PCA); clustering (KMeans); analisi trend su finestre tumbling. | 3.5.0                 |
| **Apache Hadoop** | Archiviazione distribuita (HDFS per dataset, modelli ML, checkpoints); gestione risorse cluster (YARN).                          | 3.2.4                 |
| **Neo4j Community Edition**| Modellazione, persistenza (su VM `master`) e visualizzazione del grafo della conoscenza.                                       | 4.4.x                 |
| **Python & PySpark** | Linguaggio principale per scripting, sviluppo UDF, interazione con Kafka e Neo4j.                                           | Python 3.8+           |
| **Sentence Transformers** | Libreria Python per generare embedding semantici di alta qualità dal testo.                                                 | Ultima stabile        |
| **Neo4j Spark Connector** | Libreria Spark per scrivere dati da Spark Streaming direttamente a Neo4j.                                                   | 5.2.0 (o compatibile) |
| **Java (OpenJDK)** | Ambiente di esecuzione per Hadoop, Spark e Neo4j 4.4 sul cluster.                                                            | 11                    |

## 📦 Dataset Utilizzato

* **Dataset Iniziale:** [News Category Dataset](https://www.kaggle.com/datasets/rmisra/news-category-dataset) - Contiene notizie dal 2012 al 2022. Le colonne principali utilizzate sono:
    * `headline`: Titolo della notizia.
    * `short_description`: Breve descrizione.
    * `category`: Categoria originale.
    * `date`: Data di pubblicazione (formato `YYYY-MM-DD`).
* **Dati di Streaming (Simulati):** Il producer Kafka invia messaggi JSON con `headline`, `category` e `short_description`.
    ```json
   {"headline": "Titolo Notizia 1", "category": "NOME_CATEGORIA_1", "short_description": "Descrizione breve..."}
   {"headline": "Titolo Notizia 2", "category": "NOME_CATEGORIA_2", "short_description": "Altra descrizione..."}   
    ```
## 📁 Struttura del Progetto
```
TrendSpotter-Cluster/    (in /home/hadoop/ sulla VM master)
│
├── kafka/
│   ├── producer.py          # Invia notizie a Kafka
│   └── sample_news.jsonl  # Esempio di file per il producer
│
├── scripts/
│   ├── analyze_batch.py     # Job Batch: Preprocessing, Embedding, Scaler, PCA, Training KMeans K=5, Salva Modelli/CSV
│   └── streaming_job.py     # Job Streaming: Legge Kafka, Carica Modelli, Applica Pipeline, Scrive su Neo4j, Monitora Trend
|   └── graph_builder.py     # Costruzione del grafo
│
├── models/ (SU HDFS!)         # Percorso: hdfs:///user/hadoop/models/
│   ├── scaler_model_all_mpnet_base_v2/
│   ├── pca_model_all_mpnet_base_v2_k40/
│   └── kmeans_embedding_all_mpnet_base_v2_k5_scaled_pca40/ 
│
├── data/                      # Dati locali sulla VM master
│   └── output/                
│       ├── topics_with_cluster/ 
│       └── topics_vs_category/  
│
├── setup/                   # Script di setup
│   └── setup_hadoop.sh 
|   └── setup_spark.sh
|   └── setup_kafka.sh         
```

## 🛠️ Setup Architettura e Installazione

Il sistema è implementato su un cluster simulato di 3 Virtual Machine (VM) su Ubuntu 20.04.

* 🧠 **master** (`192.168.56.10`): NameNode HDFS, ResourceManager YARN, Broker Kafka, Server Neo4j 4.4, nodo driver Spark.
* ⚙️ **worker1** (`192.168.56.11`): DataNode HDFS, NodeManager YARN, nodo worker Spark.
* ⚙️ **worker2** (`192.168.56.12`): DataNode HDFS, NodeManager YARN, nodo worker Spark.

L'installazione dei componenti principali è facilitata da script di setup.

### 1. Prerequisiti Comuni alle VM

* Ubuntu 20.04 Desktop/Server.
* Minimo 4 core CPU, 8 GB RAM, 40-60 GB Disco (più spazio consigliato per il master).
* **Java 11 (`openjdk-11-jdk`)** installato e impostato come default.
* Python 3.8+ (`python3`, `python3-pip`).
* SSH Server (`openssh-server`), `net-tools`, `rsync`.
* Creazione di un utente `hadoop` su tutte le VM, con privilegi `sudo` e configurazione di SSH senza password tra tutti i nodi (incluso `localhost` su ciascuno) per l'utente `hadoop`.

### 2. Configurazione Rete e Host

* Configurare due schede di rete per ogni VM (NAT per internet, Rete Interna `cluster-net` per comunicazione cluster).
* Assegnare IP statici sulla rete interna (vedi file `/etc/netplan/...` sotto).
* Configurare `/etc/hosts` su **tutte** le VM per la risoluzione dei nomi:
    ```
    127.0.0.1 localhost
    192.168.56.10 master
    192.168.56.11 worker1
    192.168.56.12 worker2
    ```
* **Esempio Netplan (`/etc/netplan/01-netcfg.yaml` su master):**
    ```yaml
    network:
      version: 2
      ethernets:
        enp0s3: # Adattare al nome della scheda NAT
          dhcp4: true
        enp0s8: # Adattare al nome della scheda Rete Interna
          dhcp4: no
          addresses: [192.168.56.10/24]
    ```
    *(Adattare l'IP per worker1 e worker2 e rieseguire `sudo netplan apply`)*

### 3. Utente `hadoop` e SSH senza Password

* Creare un utente `hadoop` su tutte le VM, aggiungerlo al gruppo `sudo`.
    ```bash
    sudo adduser hadoop
    sudo usermod -aG sudo hadoop
    su - hadoop # Lavorare come utente hadoop
    ```
* Configurare SSH senza password per l'utente `hadoop` tra tutti i nodi (incluso `localhost`).
    ```bash
    # Su ogni nodo come utente hadoop
    ssh-keygen -t rsa -P '' -f ~/.ssh/id_rsa
    cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys
    chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys
    ```
### 4. Script di Setup

L'installazione e la configurazione di base di Hadoop, Spark e Kafka sono gestite tramite i seguenti script (tutti eseguiti come utente `hadoop`) :

* `setup_hadoop.sh`
    * **Dove eseguire:** Solo sul nodo `master`.
    * **Quando:** Dopo la configurazione base della VM master.
    * **Scopo:** Installa Hadoop in `~/hadoop`, crea directory per NameNode/DataNode, imposta variabili ambiente (`JAVA_HOME` per Java 11, `HADOOP_HOME`, `PATH`) in `~/.bashrc`, e pre-configura i file XML essenziali.
    * **File di Configurazione Hadoop Chiave:**
        Si trovano in `$HADOOP_HOME/etc/hadoop/`.
        * **`hadoop-env.sh`**: Assicurarsi che `JAVA_HOME` punti a Java 11:
            ```bash
            export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64 
            ```
        * **`core-site.xml`**:
            ```xml
            <configuration>
              <property>
                <name>fs.defaultFS</name>
                <value>hdfs://master:9000</value>
              </property>
            </configuration>
            ```
        * **`hdfs-site.xml`**:
            ```xml
            <configuration>
              <property>
                <name>dfs.namenode.name.dir</name>
                <value>file:/home/hadoop/hadoop_data/hdfs/namenode</value> 
              </property>
              <property>
                <name>dfs.datanode.data.dir</name>
                <value>file:/home/hadoop/hadoop_data/hdfs/datanode</value> 
              </property>
              <property>
                <name>dfs.replication</name>
                <value>2</value> 
              </property>
            </configuration>
            ```
        * **`mapred-site.xml`**:
            ```xml
            <configuration>
              <property>
                <name>mapreduce.framework.name</name>
                <value>yarn</value>
              </property>
              <property>
                  <name>mapreduce.application.classpath</name>
                  <value>$HADOOP_MAPRED_HOME/share/hadoop/mapreduce/*:$HADOOP_MAPRED_HOME/share/hadoop/mapreduce/lib/*</value>
              </property>
            </configuration>
            ```
        * **`yarn-site.xml`**:
            ```xml
            <configuration>
              <property>
                <name>yarn.nodemanager.aux-services</name>
                <value>mapreduce_shuffle</value>
              </property>
              <property>
                <name>yarn.resourcemanager.hostname</name>
                <value>master</value> 
              </property>
              <property>
                  <name>yarn.application.classpath</name>
                  <value>$HADOOP_CONF_DIR,$HADOOP_COMMON_HOME/share/hadoop/common/*,$HADOOP_COMMON_HOME/share/hadoop/common/lib/*,$HADOOP_HDFS_HOME/share/hadoop/hdfs/*,$HADOOP_HDFS_HOME/share/hadoop/hdfs/lib/*,$HADOOP_MAPRED_HOME/share/hadoop/mapreduce/*,$HADOOP_MAPRED_HOME/share/hadoop/mapreduce/lib/*,$HADOOP_YARN_HOME/share/hadoop/yarn/*,$HADOOP_YARN_HOME/share/hadoop/yarn/lib/*</value>
              </property>
            </configuration>
            ```
        * **`workers`** (o `slaves`):
            ```
            master
            worker1
            worker2
            ```
    * **Azioni (Manuali) Post-Script `setup_hadoop.sh`:**
        1.  Copiare la cartella Hadoop configurata (`~/hadoop`) dal `master` ai `worker`:
            ```bash
            scp -r ~/hadoop hadoop@worker1:/home/hadoop/
            scp -r ~/hadoop hadoop@worker2:/home/hadoop/
            ```
        2.  Assicurarsi che `~/.bashrc` sui worker rifletta le variabili d'ambiente Hadoop e ricaricarlo (`source ~/.bashrc`).
        3.  Creare le directory per DataNode sui worker (es. `mkdir -p /home/hadoop/hadoop_data/hdfs/datanode`).
        4.  Formattare HDFS (SOLO LA PRIMA VOLTA!) dal `master`: `hdfs namenode -format`.
        5.  Avviare HDFS e YARN dal `master`: `start-dfs.sh && start-yarn.sh`.
        6.   Verificare con `jps` su ogni nodo e accedendo alle UI Web (HDFS: `http://master:9870`, YARN: `http://master:8088`).

### 5. Installazione Apache Spark 

* `setup_spark.sh`
    * **Dove eseguire:** Su **tutti e 3 i nodi** (`master`, `worker1`, `worker2`).
    * **Quando:** Dopo `setup_hadoop.sh` e la copia/configurazione di Hadoop sui worker.
    * **Scopo:** Installa Apache Spark (es. 3.5.0), configura `spark-env.sh` e il file `workers`, imposta variabili ambiente (`SPARK_HOME`, `PATH`).
    * **File di Configurazione Spark Chiave (impostati/verificati da `setup_spark.sh` e modifiche manuali):**
        Si trovano in `$SPARK_HOME/conf/`.
        * **`spark-env.sh`**:
            ```bash
            export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64 # Java 11
            export HADOOP_CONF_DIR=/home/hadoop/hadoop/etc/hadoop
            export SPARK_MASTER_HOST=master # Utile per Spark Standalone
            ```
        * **`workers`** (o `slaves`): Questo file è più rilevante per Spark in modalità Standalone. Quando si usa YARN, YARN gestisce i worker. Tuttavia, per coerenza:
            ```
            master
            worker1
            worker2
            ```
    * **Azioni Post-Script:** Ricaricare `source ~/.bashrc` su tutti i nodi.

### 6. Installazione Apache Kafka
* `setup_kafka.sh`
    * **Dove eseguire:** Solo sul nodo `master`.
    * **Quando:** Dopo aver configurato Spark.
    * **Scopo:** Scarica/installa Kafka (es. 3.6.0) e ZooKeeper (incluso), imposta variabili ambiente (`KAFKA_HOME`, `PATH`).
    * **Azioni Post-Script (per Avviare Kafka e Creare Topic):**
        1.  Ricaricare `~/.bashrc` sul master.
        2.  Avviare ZooKeeper: `bin/zookeeper-server-start.sh -daemon config/zookeeper.properties` (dalla dir Kafka).
        3.  Avviare il Broker Kafka: `bin/kafka-server-start.sh -daemon config/server.properties`.
        4.  Creare il topic (es. `news_final_test`): `bin/kafka-topics.sh --create --topic NOME_TOPIC --bootstrap-server master:9092 --partitions 1 --replication-factor 1`.
        
   *(Nota: `replication-factor 1` è adatto solo per un setup con un singolo broker)*

### 7. Installazione Neo4j (su VM Master)
* Aggiungere repository APT Neo4j, installare `neo4j=1:4.4.x -y`.
* Configurare `/etc/neo4j/neo4j.conf`:
    * `dbms.connector.bolt.listen_address=0.0.0.0:7687`
    * `dbms.connector.http.listen_address=0.0.0.0:7474`
    * Impostare limiti di memoria (es. heap `1g`, pagecache `1g`).
    * `dbms.security.auth_enabled=true`.
* Avviare/abilitare servizio: `sudo systemctl start neo4j && sudo systemctl enable neo4j`.
* Impostare password utente `neo4j` a `progetto24` tramite `cypher-shell`.
* Verificare accesso a Neo4j Browser da host Windows: `http://master_ip:7474`.

### 8. Librerie Python Necessarie (Installazione su TUTTI i Nodi per Spark)
Affinché Spark possa eseguire correttamente gli script con tutte le dipendenze (specialmente per le UDF Pandas con `sentence-transformers` e `torch`), è **fondamentale** che le seguenti librerie Python siano installate nell'ambiente Python (es. Python 3.8) utilizzato da Spark **su tutti i nodi del cluster (master, worker1, worker2)**:
```bash
# Eseguire su MASTER, WORKER1, e WORKER2 come utente 'hadoop'
pip install --user pandas pyarrow sentence-transformers torch neo4j kafka-python numpy
```
### 9. Preparazione Codice Progetto e Dati

* Posizionare la cartella del progetto `TrendSpotter-Cluster` nella home dell'utente `hadoop` sul `master`.
* Scaricare il dataset (`News_Category_Dataset_v3.json`) e caricarlo su HDFS nel percorso atteso dagli script (es. `hdfs dfs -put News_Category_Dataset_v3.json /user/hadoop/news/`).
* Installare le librerie Python necessarie (`pip install pyspark neo4j kafka-python pandas` - `pyspark` spesso non serve installarlo a mano se si usa `spark-submit` che lo include) nell'ambiente Python usato da Spark e dagli script locali.

## 🌐 Overview del Sistema
![Architettura del Sistema](img/schema.jpg)

## 🧪 Preprocessing Dati (in Batch e Stream)

Per migliorare la qualità e la rilevanza dell'analisi, sono stati implementati i seguenti passi di preprocessing:

1.  **Filtraggio Temporale:** Vengono conservati e analizzati unicamente i record con data `date >= "2020-01-01"`. Questa scelta focalizza l'analisi sui dati più recenti (circa 5500 record nel test), cruciali per l'identificazione di trend attuali, ottimizzando al contempo le performance.
2.  **Raggruppamento Semantico delle Categorie:** Le 42 categorie originali del dataset sono state consolidate manualmente in **22 categorie finali** più significative e meno frammentate (es. `ARTS_CULTURE`, `BUSINESS_FINANCE`, `PARENTING_FAMILY`, `VOICES`, `GOOD_WEIRD_NEWS`, `OTHER`). La colonna `category` nel DataFrame processato (e quindi nel grafo) contiene questi nomi raggruppati. Le categorie completamente nuove incontrate nello stream vengono mantenute con il loro nome originale.
3.  **Pulizia Avanzata del Testo:** Prima della generazione degli embedding, il testo combinato di `headline` e `short_description` (nel batch) e nello stream, viene sottoposto a pulizia: conversione in lowercase, rimozione di URL, numeri isolati e punteggiatura eccessiva, e normalizzazione degli spazi. È stato impostato `MIN_TEXT_LENGTH = 0` (nessun filtro sulla lunghezza minima del testo).

## ✨ Pipeline ML Avanzata e Clustering (Batch e Stream)

Per superare i limiti di approcci più semplici, è stata implementata una pipeline ML sofisticata:

1.  **Sentence Embeddings:** Il testo preparato viene trasformato in **vettori densi di embedding semantico** (768 dimensioni) utilizzando il potente modello pre-addestrato **`all-mpnet-base-v2`** (dalla libreria `sentence-transformers`), integrato in Spark tramite una Pandas UDF.
2.  **Conversione a VectorUDT:** Gli array di embedding vengono convertiti nel formato `VectorUDT` nativo di Spark ML.
3.  **Feature Scaling (StandardScaler):** Ai vettori embedding viene applicata la standardizzazione (Z-score) per normalizzare le feature, migliorando la performance degli algoritmi basati sulla distanza. Il modello `StandardScalerModel` addestrato nel batch viene salvato e riutilizzato nello stream.
4.  **Riduzione Dimensionalità (PCA):** Viene applicata la Principal Component Analysis (PCA) per ridurre la dimensionalità dei vettori standardizzati a **40 componenti principali**. Questo passo riduce il rumore, la complessità computazionale e può migliorare la separazione dei cluster. Il modello `PCAModel` addestrato nel batch viene salvato e riutilizzato nello stream.
5.  **Clustering (KMeans):** L'algoritmo KMeans viene applicato alle feature finali (output della PCA). È stato scelto **K=5** come numero di cluster, basandosi su sperimentazioni che hanno indicato una modesta ma positiva qualità di clustering (Metrica utilizzata: Silhouette Score di **~0.13** nel batch). Il modello `KMeansModel` addestrato nel batch viene salvato e riutilizzato nello stream.
6.  **Salvataggio e Caricamento Modelli:** Tutti i modelli della pipeline (Scaler, PCA, KMeans) addestrati da `analyze_batch.py` vengono salvati su HDFS. Lo script `streaming_job.py` carica questi stessi modelli per garantire coerenza assoluta nell'elaborazione dei dati in tempo reale.

## 📈 Identificazione e Monitoraggio dei Trend

L'identificazione dei trend si basa sull'analisi dei **5 cluster tematici** scoperti:

* **Trend Dominanti (Batch):** Identificati nel job batch analizzando la numerosità dei cluster (quanti topic per cluster) e la loro composizione rispetto alle categorie raggruppate.
* **Trend Emergenti (Streaming):** Monitorati tramite **Spark Streaming con finestre temporali non sovrapposte (tumbling windows)** e `outputMode("update")`. `streaming_job.py` calcola e **stampa sulla console** la frequenza di ciascun `ClusterID` (0-4) per blocchi di tempo disgiunti (es. ogni 2 minuti per i 2 minuti precedenti). Un aumento di questi conteggi segnala un trend. L'analisi qualitativa in Neo4j ne rivela il significato. Inoltre, durante lo streaming viene stampata una tabella contenente le nuove categorie inviduate durante l'arrivo di nuove notizie.

## 🕸️ Grafo Neo4j e Abilitazione Raccomandazioni

* **Costruzione/Aggiornamento:**
    * **Batch:** `graph_builder.py` popola Neo4j da CSV locali del batch.
    * **Streaming:** `streaming_job.py` (con Neo4j Spark Connector) aggiorna Neo4j direttamente.
* **Esplorazione:** Neo4j Browser (`http://master:7474`).
* **Abilitazione Raccomandazioni:** La struttura del grafo permette logiche di raccomandazione (dimostrate via Cypher).

## 🚀 Come Eseguire il Progetto
**Passo 0: Prerequisiti**
* Assicurarsi che il Setup completo (Hadoop, YARN, Spark, Kafka, Neo4j sulla VM `master`, Java 11, librerie Python necessarie installate su tutti i nodi come descritto nella sezione "Setup Architettura e Installazione") sia stato completato.
* Il dataset JSON originale deve essere su HDFS.

1.    **Avvio Servizi Hadoop (HDFS & YARN)**
(Eseguire dal nodo `master`, come utente `hadoop`)
  ```bash
   start-dfs.sh
   start-yarn.sh
   jps
  ```
*(Nota: Check su Worker1 e Worker2 (sempre come utente `hadoop`) con jps. Bisogna vedere: DataNode, NodeManager)*

2.    **Avvio Servizi Kafka (ZooKeeper & Broker)**
(Eseguire su altri due terminali distinti. Sempre da nodo `master`, come utente `hadoop` )
```bash
   cd ~/kafka
   bin/zookeeper-server-start.sh -daemon config/zookeeper.properties #Esegui prima
   bin/kafka-server-start.sh -daemon config/server.properties #Aspetta e poi esegui questo
   bin/kafka-topics.sh --list --bootstrap-server master:9092 #verifica esistenza topic
   jps
```
 Verifica UI Web: HDFS (http://master:9870), YARN (http://master:8088)

*(Nota: Check su Master con jps. Bisogna vedere: QuorumPeerMain (ZooKeeper) e Kafka. Se topic non ancora creato guardare [Setup Architettura e Installazione](#️-setup-architettura-e-installazione))*

3.    **Avvio Neo4j**
(Eseguire dal nodo `master`, come utente `hadoop`)
```bash
  sudo systemctl start neo4j
  sudo systemctl status neo4j
```
*(Nota:Lo stato dovrebbe essere 'active (running)'. Premi 'q' per uscire dallo status)*

**Passo 1: Esecuzione Analisi Batch** (da `master`):
  ```bash
      cd ~/TrendSpotter-Cluster
      export PYTHON_EXEC_PATH=$(which python3.8)
      export USER_SITE_PACKAGES_PATH=$(python3.8 -m site --user-site)
      export HF_CACHE_PATH="/home/hadoop/.cache/huggingface"
      mkdir -p ${HF_CACHE_PATH}
      spark-submit --master yarn \
        --name "TrendSpotter_Batch_K5_UserEnv" \
        --conf spark.pyspark.driver.python=${PYTHON_EXEC_PATH} \
        --conf spark.pyspark.python=${PYTHON_EXEC_PATH} \
        --conf spark.executorEnv.PYTHONPATH=${USER_SITE_PACKAGES_PATH} \
        --conf spark.driverEnv.PYTHONPATH=${USER_SITE_PACKAGES_PATH} \
        --conf spark.executorEnv.HF_HOME=${HF_CACHE_PATH} \
        scripts/analyze_batch.py
  ```

**Passo 2: Costruzione Grafo Iniziale** (da `master`):
  ```bash
       cd ~/TrendSpotter-Cluster/scripts
       python3 graph_builder.py
  ```
  *(Nota: Una volta completato, andare su (http://master:7474) per visualizzare grafo)*
      
**Passo 3: Avvio Job di Streaming** (da `master`):    
  ```bash
      cd ~/TrendSpotter-Cluster
      export KAFKA_SPARK_PKG="org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0" 
      export NEO4J_SPARK_PKG="org.neo4j:neo4j-connector-apache-spark_2.12:5.3.7_for_spark_3"

     spark-submit --master yarn \
      --name "TrendSpotter_Streaming_K5_UserEnv" \
      --conf spark.pyspark.driver.python=${PYTHON_EXEC_PATH} \
      --conf spark.pyspark.python=${PYTHON_EXEC_PATH} \
      --conf spark.executorEnv.PYTHONPATH=${USER_SITE_PACKAGES_PATH} \
      --conf spark.driverEnv.PYTHONPATH=${USER_SITE_PACKAGES_PATH} \
      --conf spark.executorEnv.HF_HOME=${HF_CACHE_PATH} \
      --packages ${KAFKA_SPARK_PKG},${NEO4J_SPARK_PKG} \
      scripts/streaming_job.py
  ```
   *(Nota: Monitora console per trend e Neo4j Browser per aggiornamenti. Inoltre nel caso in cui si ha necessità di riavviare i servizi dfs e yarn, prima di eseguire streaming_job fare di nuovo export delle variabili d'ambiente)*
   
### 📊 Guida all'Output della Console (Streaming Attivo)

Quando lo script `streaming_job.py` è in esecuzione, sulla console del terminale appariranno due tipi di output informativi in tempo reale. Questi sono generati da due query di streaming separate che girano in parallelo, permettendo di monitorare diversi aspetti dell'analisi simultaneamente.

---

#### 📈 1. Analisi dei Trend (su Finestre Temporali)

Questo output appare periodicamente e mostra l'attività aggregata dei temi (cluster) scoperti da Spark. Serve per capire quali argomenti sono più discussi in un dato intervallo di tempo.

> #### **Come Interpretare la Tabella dei Trend (Finestre Non Sovrapposte)**
>
> * **Quando Appare:** Verrà stampata una tabella solo quando una finestra temporale (es. i nostri **2 minuti**, come impostato nello script) si "chiude" e i suoi conteggi aggregati sono finalizzati.
> * **Cosa Mostra:** Ogni tabella si riferisce **esclusivamente** a quel specifico blocco temporale.
> * **Contenuto:** La tabella elenca i `ClusterID` (da 0 a 4, se K=5) attivi in quella finestra e il loro `count` (numero di notizie).
> * **Come Trovare il Trend:** Poiché con `outputMode("update")` l'ordinamento per conteggio non è garantito, per identificare il tema più frequente in quel blocco, dovrai **scorrere visivamente** le poche righe (massimo 5 in questo caso) e trovare il `ClusterID` con il `count` più alto.
> * **Capire il Trend:** Per capire **COSA** rappresenta quel ClusterID (es. 'Cluster 2'), è necessario esaminare i suoi contenuti (titoli) nel grafo Neo4j.

    
    **Guida all'Output della Console (Streaming Attivo):**
    Quando lo script `streaming_job.py` è in esecuzione, sulla console del terminale appariranno due tipi di output informativi in tempo reale, generati da due query di streaming separate che girano in parallelo.
    ###Analisi dei Trend (su Finestre Temporali)
    Questo output appare periodicamente e mostra l'attività aggregata dei topics scoperti da Spark.
    ```
    ======================================================================
       INTERPRETAZIONE OUTPUT TRENDS SULLA CONSOLE:
       - Lo stream stamperà una tabella sulla console solo quando una finestra temporale
         (es. **2 minuti**) si "chiude" e i suoi conteggi aggregati sono finalizzati.
       - Ogni tabella mostrata si riferisce ESCLUSIVAMENTE a quel specifico blocco temporale.
       - La tabella elencherà i 'ClusterID' attivi in quella finestra
         e il loro 'count' (numero di notizie).
       - NOTA: Le righe non sono garantite essere ordinate per 'count'.
       - Per identificare il TEMA PIU' FREQUENTE in quel blocco, trovare il ClusterID con il 'count' più alto.
       - Per capire COSA rappresenta quel ClusterID, esaminare i suoi contenuti 
         nel grafo Neo4j usando la query Cypher appropriata.
    ======================================================================
    ```
    ###Allerta per Nuove Categorie Rilevate
    Questo output appare **solo se e quando** il producer Kafka invia una notizia con una categoria che **non** è presente nella lista delle 22 categorie raggruppate conosciute.
     
    ======================================================================
    INTERPRETAZIONE TABELLA NUOVE CATEGORIE:
    - Questa tabella appare solo quando viene rilevata una categoria sconosciuta.
    - Utilizza outputMode("append"), quindi ogni nuova categoria viene stampata una sola volta, nel momento in cui viene scoperta.
    - Serve come un sistema di allerta in tempo reale per la comparsa di nuovi temi editoriali non previsti dalla mappatura iniziale. 
    ======================================================================
    
  **Passo 4: Avvio Producer Kafka** (da `master`, nuovo terminale):    
  ```bash
    cd ~/kafka
    python3 producer.py
  ```
Una volta che `producer.py` invia nuove notizie:
1.  **Elaborazione Streaming:** Lo script `streaming_job.py` (già in esecuzione) rileva questi nuovi messaggi da Kafka. Ogni notizia viene processata attraverso la pipeline ML completa.
2.  **Aggiornamento Grafo Neo4j:** I risultati (topic, categoria raggruppata/nuova, ID cluster) vengono inviati **direttamente a Neo4j** (`bolt://master:7687`) tramite il connettore Spark. Il grafo si aggiorna quasi in tempo reale, con un ritardo legato all'intervallo di trigger e al tempo di elaborazione del micro-batch (impostato, ad esempio, per tentare un aggiornamento ogni 2-5 minuti per la demo). Puoi verificare i nuovi dati interrogando Neo4j Browser.
3.  **Monitoraggio Trend su Console:** Parallelamente, sulla console dove è in esecuzione `streaming_job.py`, la tabella dei trend (conteggio notizie per `ClusterID` su finestre temporali non sovrapposte) verrà aggiornata quando una nuova finestra temporale si "chiude" e ha dati da mostrare (basato sull'impostazione `outputMode("update")` e da un trigger di 5-10 minuti per la demo).

*Nota: La visualizzazione degli aggiornamenti non è istantanea a causa dei tempi di elaborazione e degli intervalli di trigger configurati per lo stream.*

## 📊 Query Neo4j Utilizzate

```cypher
// Query 1: Statistiche Generali del Grafo
MATCH (n) RETURN labels(n) AS TipoNodo, count(*) AS Conteggio
UNION ALL
MATCH ()-[r]->() RETURN "Relazioni Totali" AS TipoNodo, count(r) AS Conteggio;

// Query 2: Cluster/Temi Più Frequenti (K=0-4, basato su dimensione cluster)
MATCH (c:Cluster)-[:CONTAINS]->(t:Topic)
RETURN c.id AS ClusterID, count(t) AS NumeroNotizie
ORDER BY NumeroNotizie DESC
LIMIT 5;

// Query 3: Categorie Raggruppate Più Frequenti
MATCH (cat:Category)<-[:BELONGS_TO]-(t:Topic)
RETURN cat.name AS CategoriaRaggruppata, count(t) AS NumeroNotizie
ORDER BY NumeroNotizie DESC
LIMIT 10;

// Query 4: Esplora Contenuto di un Cluster Specifico (sostituisci 'ID_CLUSTER' con 0,1,2,3 o 4)
MATCH (c:Cluster {id: 'ID_CLUSTER'})-[:CONTAINS]->(t:Topic)
RETURN t.name AS TitoloEsempio
LIMIT 15;

// Query 5: Composizione Categorie in un Cluster (sostituisci 'ID_CLUSTER')
MATCH (c:Cluster {id: 'ID_CLUSTER'})-[:CONTAINS]->(t:Topic)-[:BELONGS_TO]->(cat:Category)
RETURN cat.name AS CategoriaRaggruppata, count(t) AS ConteggioNotizie
ORDER BY ConteggioNotizie DESC;

// Query 6: Raccomandazione Basata su Cluster per 'Giulia'
MATCH (u:User {name:'Giulia'})-[:INTERESTED_IN]->(liked_topic:Topic)
MATCH (liked_topic)<-[:CONTAINS]-(c:Cluster)-[:CONTAINS]->(rec_topic:Topic)
WHERE NOT (u)-[:INTERESTED_IN]->(rec_topic)
RETURN DISTINCT rec_topic.name AS Raccomandazione, c.id AS DalCluster
LIMIT 10;

// Query 7: Raccomandazione Basata su Categoria Raggruppata per 'Daniele'
MATCH (u:User {name:'Daniele'})-[:INTERESTED_IN]->(liked_topic:Topic)
MATCH (liked_topic)-[:BELONGS_TO]->(cat:Category)
MATCH (rec_topic:Topic)-[:BELONGS_TO]->(cat)
WHERE NOT (u)-[:INTERESTED_IN]->(rec_topic)
RETURN DISTINCT rec_topic.name AS Raccomandazione, cat.name AS DallaCategoria
LIMIT 10;

// Query 8: Utenti Interessati a Topic nel Cluster (sostituisci 'ID_CLUSTER')
MATCH (c:Cluster {id: 'ID_CLUSTER'})-[:CONTAINS]->(t:Topic)<-[:INTERESTED_IN]-(u:User)
RETURN DISTINCT u.name AS UtenteInteressato, t.name AS TopicDiInteresse, c.id AS ClusterID;
```
## ✅ Conclusioni
TrendSpotter è un progetto che mostra come costruire una pipeline Big Data completa per analizzare trend a partire da flussi di testo. Utilizzando tecnologie come Kafka, Spark, Hadoop e Neo4j, siamo riusciti a combinare tecniche di NLP e Machine Learning (come sentence embedding, PCA e KMeans) per raggruppare le notizie in cluster tematici coerenti.
L’identificazione dei trend avviene sia tramite l’analisi della frequenza dei cluster in batch, sia osservando l’evoluzione nel tempo tramite Spark Streaming con finestre temporali.
Il grafo costruito in Neo4j, aggiornato quasi in tempo reale, permette di visualizzare le relazioni tra topic, categorie e utenti e rende possibile la "generazione" e la visualizzazione di raccomandazioni.



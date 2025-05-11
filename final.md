# 🧠 TrendSpotter: Analisi e Abilitazione di Raccomandazioni da Trend Emergenti su Flussi di Dati

## 🚀 Introduzione

**TrendSpotter** è un sistema distribuito progettato per l'identificazione di **trend emergenti** in tempo reale e per costruire una base dati che **abilita la generazione di raccomandazioni**. Prendendo ispirazione da piattaforme dinamiche come Twitter Trends e Google News, il sistema orchestra un potente insieme di tecnologie Big Data per offrire una soluzione end-to-end: dall'ingestione di flussi di dati continui (simulati tramite Kafka), all'analisi testuale semantica avanzata (con Sentence Embeddings), al clustering intelligente (KMeans ottimizzato) per la scoperta di topic, fino alla costruzione di un grafo della conoscenza in Neo4j.

Questo progetto non si limita a processare dati, ma mira a trasformarli in insight azionabili e a creare una struttura dati relazionale che può servire come fondamenta per sistemi di suggerimento, dimostrando come l'integrazione sinergica di Kafka, Spark, Hadoop e Neo4j possa dare vita a sistemi informativi dinamici e intelligenti.

### 🎯 Obiettivi Principali Raggiunti

1.  **Identificare e Monitorare Trend:** Il sistema individua i **temi** (argomenti) più **frequenti e rilevanti** all'interno dei dati di notizie recenti (filtrati dal 2020 in poi). Questo viene realizzato tramite un clustering semantico avanzato (configurato per **K=5** cluster). L'attività di questi temi viene poi **monitorata nel tempo** grazie all'analisi del flusso streaming con **finestre temporali non sovrapposte (tumbling windows)**, i cui risultati aggregati (conteggi per cluster) vengono visualizzati sulla console con `outputMode("update")` per una chiara interpretazione sequenziale.
2.  **Abilitare Raccomandazioni Personalizzate (tramite Grafo):** È stata costruita una ricca **struttura a grafo in Neo4j** che modella le relazioni tra utenti (simulati), notizie/topic (con `headline` e `short_description`), i 5 cluster tematici a cui appartengono e le loro categorie editoriali (raggruppate). Questa struttura **abilita la generazione di diverse tipologie di raccomandazioni personalizzate**, la cui potenzialità è **dimostrata tramite query Cypher esemplificative**, senza l'implementazione di algoritmi di Machine Learning specifici per la raccomandazione (come ALS) all'interno di Spark.
3.  **Visualizzare Complesse Relazioni:** Viene offerta una **rappresentazione visiva chiara ed interattiva** (tramite Neo4j Browser) dei legami tra argomenti (singole notizie), le categorie editoriali raggruppate, i 5 cluster tematici scoperti automaticamente e gli utenti simulati, permettendo un'esplorazione intuitiva dei dati.

## 🧰 Stack Tecnologico

| Tecnologia                 | Scopo Principale nel Progetto                                                                                                | Versione (Indicativa) |
| :------------------------- | :--------------------------------------------------------------------------------------------------------------------------- | :-------------------- |
| **Apache Kafka** | Ingestione e buffering di flussi di notizie simulate in tempo reale (topic configurabile, es. `news_final_test`).                  | 3.6.0                 |
| **Apache Spark** | Elaborazione distribuita batch e streaming; generazione Sentence Embeddings (`all-mpnet-base-v2`); preprocessing feature (Scaler, PCA); clustering (KMeans K=5); analisi trend su finestre tumbling. | 3.5.0                 |
| **Apache Hadoop** | Archiviazione distribuita (HDFS per dataset, modelli ML, checkpoints); gestione risorse cluster (YARN).                          | 3.2.4                 |
| **Neo4j Community Edition**| Modellazione, persistenza (su VM `master`) e visualizzazione del grafo della conoscenza.                                       | 4.4.x                 |
| **Python & PySpark** | Linguaggio principale per scripting, sviluppo UDF, interazione con Kafka e Neo4j.                                           | Python 3.8+           |
| **Sentence Transformers** | Libreria Python per generare embedding semantici di alta qualità dal testo.                                                 | Ultima stabile        |
| **Neo4j Spark Connector** | Libreria Spark per scrivere dati da Spark Streaming direttamente a Neo4j.                                                   | 5.2.0 (o compatibile) |
| **Java (OpenJDK)** | Ambiente di esecuzione per Hadoop, Spark e Neo4j 4.4 sul cluster.                                                            | 11                    |

## 📦 Dataset Utilizzato

* **Dataset Iniziale:** `News_Category_Dataset_v3.json`, caricato su HDFS (es. `hdfs:///user/hadoop/news/`). Si utilizzano le colonne: `headline`, `short_description`, `category`, `date`.
* **Dati di Streaming (Simulati):** Messaggi JSON inviati da `kafka/producer.py` (o versione che legge da file) al topic Kafka configurato, contenenti `headline`, `short_description` e `category` (originale).

## 🛠️ Setup Architettura e Installazione

Il sistema è implementato su un cluster simulato di 3 Virtual Machine (VM) Ubuntu 20.04.

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
          # Gateway e DNS non necessari sulla rete interna se si usa NAT per internet
          # nameservers:
          #   addresses: [8.8.8.8, 1.1.1.1]
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
    # Copiare id_rsa.pub di master su authorized_keys dei worker e viceversa se necessario
    # Verificare con ssh worker1, ssh worker2, ssh master, ssh localhost
    ```
### 4. Script di Setup (da eseguire come utente `hadoop`)

L'installazione e la configurazione di base di Hadoop, Spark e Kafka sono gestite tramite i seguenti script:

* **A. `setup_hadoop.sh`**
    * **Dove eseguire:** Solo sul nodo `master`.
    * **Quando:** Dopo la configurazione base della VM master.
    * **Scopo:** Installa Hadoop (es. 3.2.4) in `~/hadoop`, crea directory per NameNode/DataNode, imposta variabili ambiente (`JAVA_HOME` per Java 11, `HADOOP_HOME`, `PATH`) in `~/.bashrc`, e pre-configura i file XML essenziali.
    * **File di Configurazione Hadoop Chiave (impostati/verificati da `setup_hadoop.sh` e modifiche manuali):**
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
    * **Azioni Post-Script `setup_hadoop.sh` (Manuali):**
        1.  Copiare la cartella Hadoop configurata (`~/hadoop`) dal `master` ai `worker`:
            ```bash
            scp -r ~/hadoop hadoop@worker1:/home/hadoop/
            scp -r ~/hadoop hadoop@worker2:/home/hadoop/
            ```
        2.  Assicurarsi che `~/.bashrc` sui worker rifletta le variabili d'ambiente Hadoop e ricaricarlo (`source ~/.bashrc`).
        3.  Creare le directory per DataNode sui worker (es. `mkdir -p /home/hadoop/hadoop_data/hdfs/datanode`).
        4.  Formattare HDFS (SOLO LA PRIMA VOLTA!) dal `master`: `hdfs namenode -format`.
        5.  Avviare HDFS e YARN dal `master`: `start-dfs.sh && start-yarn.sh`.
* Verificare con `jps` su ogni nodo e accedendo alle UI Web (HDFS: `http://master:9870`, YARN: `http://master:8088`).

### 5. Installazione Apache Spark 

* Scaricare una distribuzione Spark compatibile con Hadoop e pre-compilata per Hadoop (es. Spark 3.5.0 for Hadoop 3.2 and later) sul `master`.
* Estrarre l'archivio (es. in `/home/hadoop/spark`).
* Configurare le variabili d'ambiente Spark (`SPARK_HOME`, aggiungere `$SPARK_HOME/bin` al `PATH`) in `~/.bashrc` su **tutti** i nodi. `source ~/.bashrc`.
* Configurare Spark per usare YARN e trovare Hadoop:
    * Copiare `spark-env.sh.template` in `spark-env.sh` in `$SPARK_HOME/conf/`.
    * Modificare `spark-env.sh` aggiungendo almeno:
        ```bash
        export SPARK_MASTER_HOST=master # Se si usa Spark Standalone Master (opzionale con YARN)
        export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64 # O percorso corretto
        export HADOOP_CONF_DIR=/home/hadoop/hadoop/etc/hadoop # Fondamentale per trovare YARN/HDFS
        # Potrebbe essere utile impostare SPARK_DIST_CLASSPATH se ci sono problemi a trovare classi Hadoop
        # export SPARK_DIST_CLASSPATH=$(hadoop classpath)
        ```
* Copiare la cartella Spark configurata (`/home/hadoop/spark`) dal `master` ai `worker` usando `scp`.
* Verificare l'installazione eseguendo `spark-shell --master yarn` o `pyspark --master yarn` dal master.

### 6. Installazione Apache Kafka (su Master)

* Scaricare Kafka (es. 3.6.0) sul nodo `master`.
* Estrarre l'archivio (es. in `/home/hadoop/kafka`).
* Kafka richiede ZooKeeper. Kafka include uno script per avviare uno ZooKeeper semplice per test, altrimenti installare ZooKeeper separatamente per ambienti più robusti.
* **Avvio (esempio con ZK integrato):**
    * Avviare ZooKeeper in background:
        ```bash
        # Dalla directory di Kafka sul master
        bin/zookeeper-server-start.sh -daemon config/zookeeper.properties
        ```
    * Avviare il Broker Kafka in background:
        ```bash
        bin/kafka-server-start.sh -daemon config/server.properties
        ```
    * Creare il topic `news` se non esiste già:
        ```bash
        bin/kafka-topics.sh --create --topic news --bootstrap-server master:9092 --partitions 1 --replication-factor 1
        ```
        *(Nota: `replication-factor 1` è adatto solo per un setup con un singolo broker)*

### 7. Installazione Neo4j (su Host Windows)

* Installare Neo4j (Server o Desktop) sulla macchina da cui si intende visualizzare il grafo e lanciare gli script `graph_builder.py` e `update_graph.py` (tipicamente la macchina **host Windows** o una VM separata, non necessariamente parte del cluster Hadoop/Spark).
* Avviare il database Neo4j.
* Impostare (o prendere nota de) la password per l'utente `neo4j`. Assicurarsi che corrisponda a quella usata negli script Python (`password = "progetto24"`).
* Verificare che Neo4j sia accessibile sulla porta Bolt (default `7687`) dall'ambiente dove girano gli script Python.

### 8. Setup Cartella Condivisa:
* Configurare la cartella condivisa (es. `trendspotter_shared`) nelle impostazioni della VM (VirtualBox/VMware).
* Installare le Guest Additions/VMware Tools nella VM Ubuntu.
* Assicurarsi che la cartella sia montata (es. in `/media/sf_shared`) e che l'utente `hadoop` abbia i permessi di scrittura (potrebbe essere necessario aggiungerlo al gruppo `vboxsf` o simile: `sudo usermod -aG vboxsf hadoop` e riavviare/riloggare).

### 9. Preparazione Codice Progetto e Dati

* Posizionare la cartella del progetto `TrendSpotter-Cluster` nella home dell'utente `hadoop` sul `master`.
* Scaricare il dataset (`News_Category_Dataset_v3.json` o nome corretto) e caricarlo su HDFS nel percorso atteso dagli script (es. `hdfs dfs -put News_Category_Dataset_v3.json /user/hadoop/news/`).
* Installare le librerie Python necessarie (`pip install pyspark neo4j kafka-python pandas` - `pyspark` spesso non serve installarlo a mano se si usa `spark-submit` che lo include) nell'ambiente Python usato da Spark e dagli script locali.

## 🧪 Preprocessing dei Dati (Applicato in Batch e Stream)

Per migliorare la qualità e la rilevanza dell'analisi, sono stati implementati i seguenti passi di preprocessing:

1.  **Filtraggio Temporale:** Vengono conservati e analizzati unicamente i record con data `date >= "2020-01-01"`. Questa scelta focalizza l'analisi sui dati più recenti (circa 5500 record nel test), cruciali per l'identificazione di trend attuali, ottimizzando al contempo le performance.
2.  **Raggruppamento Semantico delle Categorie:** Le 42 categorie originali del dataset sono state consolidate manualmente in **22 categorie finali** più significative e meno frammentate (es. `ARTS_CULTURE`, `BUSINESS_FINANCE`, `PARENTING_FAMILY`, `VOICES`, `GOOD_WEIRD_NEWS`, `OTHER`). La colonna `category` nel DataFrame processato (e quindi nel grafo) contiene questi nomi raggruppati. Le categorie completamente nuove incontrate nello stream vengono mantenute con il loro nome originale.
3.  **Pulizia Avanzata del Testo:** Prima della generazione degli embedding, il testo combinato di `headline` e `short_description` (nel batch) o la sola `headline` (nello stream, come da configurazione attuale) viene sottoposto a pulizia: conversione in lowercase, rimozione di URL, numeri isolati e punteggiatura eccessiva, e normalizzazione degli spazi. È stato impostato `MIN_TEXT_LENGTH = 0` (nessun filtro sulla lunghezza minima del testo).

## ✨ Pipeline ML Avanzata e Clustering (Batch e Stream)

Per superare i limiti di approcci più semplici, è stata implementata una pipeline ML sofisticata:

1.  **Sentence Embeddings:** Il testo preparato viene trasformato in **vettori densi di embedding semantico** (768 dimensioni) utilizzando il potente modello pre-addestrato **`all-mpnet-base-v2`** (dalla libreria `sentence-transformers`), integrato in Spark tramite una Pandas UDF.
2.  **Conversione a VectorUDT:** Gli array di embedding vengono convertiti nel formato `VectorUDT` nativo di Spark ML.
3.  **Feature Scaling (StandardScaler):** Ai vettori embedding viene applicata la standardizzazione (Z-score) per normalizzare le feature, migliorando la performance degli algoritmi basati sulla distanza. Il modello `StandardScalerModel` addestrato nel batch viene salvato e riutilizzato nello stream.
4.  **Riduzione Dimensionalità (PCA):** Viene applicata la Principal Component Analysis (PCA) per ridurre la dimensionalità dei vettori standardizzati a **40 componenti principali**. Questo passo riduce il rumore, la complessità computazionale e può migliorare la separazione dei cluster. Il modello `PCAModel` addestrato nel batch viene salvato e riutilizzato nello stream.
5.  **Clustering (KMeans):** L'algoritmo KMeans viene applicato alle feature finali (output della PCA). È stato scelto **K=5** come numero di cluster, basandosi su sperimentazioni che hanno indicato una modesta ma positiva qualità di clustering (Silhouette Score di **~0.13** nel batch, un netto miglioramento rispetto a TF-IDF). Il modello `KMeansModel` (K=5) addestrato nel batch viene salvato e riutilizzato nello stream.
6.  **Salvataggio e Caricamento Modelli:** Tutti i modelli della pipeline (Scaler, PCA, KMeans K=5) addestrati da `analyze_batch.py` vengono salvati su HDFS. Lo script `streaming_job.py` carica questi stessi modelli per garantire coerenza assoluta nell'elaborazione dei dati in tempo reale.

## 📈 Identificazione e Monitoraggio dei Trend

L'identificazione dei trend si basa sull'analisi dei **5 cluster tematici** scoperti:

* **Trend Dominanti (Batch):** Identificati nel job batch analizzando la numerosità dei cluster (quanti topic per cluster) e la loro composizione rispetto alle categorie raggruppate (output CSV `topics_vs_category`).
* **Trend Emergenti (Streaming):** Monitorati in (near) real-time dallo `streaming_job.py`. Lo script calcola e **stampa sulla console** la frequenza (numero di notizie) per ciascuno dei 5 `ClusterID` all'interno di **finestre temporali scorrevoli** (es. 10 minuti di durata, aggiornate ogni 5 minuti). Un aumento significativo di questi conteggi per un `ClusterID` specifico, o la sua persistente alta frequenza, segnala un trend. L'analisi qualitativa dei topic (titoli) all'interno di un cluster "caldo", esplorabile tramite Neo4j, ne rivela il significato semantico.

    **Guida all'Output dei Trend sulla Console:**
    ```
    ======================================================================
       INTERPRETAZIONE OUTPUT TRENDS SULLA CONSOLE:
       - Verranno stampate periodicamente tabelle 'window | ClusterID | count'.
       - Ogni 'window' rappresenta un intervallo di tempo definito.
       - All'interno di ogni 'window', i 'ClusterID' (da 0 a 4) sono ORDINATI per 'count' DECRESCENTE.
       - Il ClusterID che appare PER PRIMO per la finestra temporale più recente è il TEMA PIU' FREQUENTE.
       - Osservare come i 'count' cambiano nel tempo indica trend emergenti.
       - Per capire COSA rappresenta un ClusterID, esaminare i suoi contenuti nel grafo Neo4j.
    ======================================================================
    ```

## 🕸️ Grafo Neo4j e Abilitazione Raccomandazioni

* **Costruzione e Aggiornamento Grafo:**
    * **Caricamento Batch Iniziale:** Lo script `neo4j/scripts/graph_builder.py` (eseguito sulla VM `master`) legge l'output CSV del job `analyze_batch.py` (dalla cartella locale `data/output/topics_with_cluster`) e popola inizialmente il database Neo4j (in esecuzione su `bolt://master:7687`).
    * **Aggiornamento Streaming Real-Time:** Lo script `streaming_job.py`, grazie al **Neo4j Spark Connector**, scrive i risultati (headline, categoria processata, ID cluster) di ogni micro-batch **direttamente e automaticamente su Neo4j** tramite query `MERGE`. Questo mantiene il grafo costantemente aggiornato con le ultime notizie analizzate. Lo script `update_graph.py` non è più necessario.
* **Esplorazione e Visualizzazione:** Neo4j Browser (accessibile da `http://master:7474` dall'host Windows) permette di navigare ed esplorare visivamente i nodi `:Topic`, `:Category` (con nomi raggruppati), `:Cluster` (ID da 0 a 4), e `:User` (simulati), insieme alle loro relazioni `:BELONGS_TO`, `:CONTAINS`, `:INTERESTED_IN`.
* **Abilitazione Raccomandazioni:** La struttura relazionale del grafo è la base per implementare diversi tipi di logiche di raccomandazione, la cui potenzialità è dimostrata tramite query Cypher (vedi sezione Query Neo4j Utili).

## 📁 Struttura del Progetto
```
TrendSpotter-Cluster/    (in /home/hadoop/ sulla VM master)
│
├── kafka/
│   ├── producer.py          # Invia notizie a Kafka
│   └── sample_news.jsonl  # Esempio di file per il producer
│
├── spark_jobs/
│   ├── analyze_batch.py     # Job Batch: Preprocessing, Embedding, Scaler, PCA, Training KMeans K=5, Salva Modelli/CSV
│   └── streaming_job.py     # Job Streaming: Legge Kafka, Carica Modelli, Applica Pipeline, Scrive su Neo4j, Monitora Trend
│
├── neo4j/
│   └── scripts/
│       └── graph_builder.py   # Per caricamento batch iniziale da CSV (eseguito su master)
│
├── models/ (SU HDFS!)         # Percorso: hdfs:///user/hadoop/models/
│   ├── scaler_model_all_mpnet_base_v2/
│   ├── pca_model_all_mpnet_base_v2_k40/
│   └── kmeans_embedding_all_mpnet_base_v2_k5_scaled_pca40/ # Modello per K=5
│
├── data/                      # Dati locali sulla VM master
│   └── output/                # Output CSV del job batch (con K=5)
│       ├── topics_with_cluster/ # Colonne: headline, category (raggruppata), prediction (0-4)
│       └── topics_vs_category/  # Colonne: prediction (0-4), category (raggruppata), count
│
├── utils/ # Moduli Python condivisi (se si sceglie di usarli per refactoring)
│   └── category_mapper.py # (Attualmente la logica è duplicata negli script Spark)
│
├── scripts/                   # Script di utilità o setup
│   └── list_categories.py   # Per listare le categorie originali
│
└── README.md                  # Questo file
## 🚀 Come Eseguire il Progetto (Ordine Finale Consigliato)
```
1.  **Setup Completo:** Verificare che Hadoop (HDFS/YARN), Spark 3.5, Kafka, Neo4j 4.4 (su `master`), Java 11 siano installati, configurati e attivi. Librerie Python (`pandas`, `pyarrow`, `torch`, `sentence-transformers`, `neo4j`, `kafka-python`) installate negli ambienti Python corretti. Dataset JSON originale su HDFS.
2.  **Esecuzione Analisi Batch (Finale)** (da `master`):
    ```bash
    cd ~/TrendSpotter-Cluster
    # export PYSPARK_PYTHON=/usr/bin/python3.8 # Se necessario
    spark-submit --master yarn spark_jobs/analyze_batch.py
    ```
    *(Crea/Sovrascrive modelli Scaler, PCA, KMeans K=5 su HDFS e CSV locali in `data/output/`)*
3.  **Costruzione Grafo Iniziale** (da `master`):
    ```bash
    cd ~/TrendSpotter-Cluster/neo4j/scripts
    # Assicurati che graph_builder.py legga da "../../data/output/topics_with_cluster/part-*.csv"
    # e che l'URI Neo4j sia "bolt://master:7687"
    python graph_builder.py
    ```
4.  **Avvio Job di Streaming** (da `master`):
    ```bash
    cd ~/TrendSpotter-Cluster
    # Versione Connettore Neo4j per Spark 3.5 e Scala 2.12/2.13
    NEO4J_CONNECTOR_VERSION="5.2.0" # Verifica la migliore per la tua build Spark
    # export PYSPARK_PYTHON=/usr/bin/python3.8 # Se necessario
    spark-submit --master yarn   --conf spark.pyspark.python=/usr/bin/python3.8   --conf spark.executorEnv.PYTHONPATH=/home/hadoop/.local/lib/python3.8/site-packages   --conf spark.driverEnv.PYTHONPATH=/home/hadoop/.local/lib/python3.8/site-packages   --conf spark.executorEnv.HF_HOME=/home/hadoop/.cache/huggingface --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.neo4j:neo4j-connector-apache-spark_2.12:5.3.6_for_spark_3 streaming_job_final.py 

    ```
    *(Lascia in esecuzione. Monitora la console per i trend e Neo4j Browser per gli aggiornamenti del grafo)*
5.  **Avvio Producer Kafka** (da `master`, in un nuovo terminale):
    ```bash
    cd ~/TrendSpotter-Cluster/kafka
    python producer.py # (O la versione che legge da sample_news.jsonl)
    ```

## 📊 Query Neo4j Utili per Dimostrazione

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

// Query 6: Raccomandazione Basata su Cluster per 'Alessia'
MATCH (u:User {name:'Alessia'})-[:INTERESTED_IN]->(liked_topic:Topic)
MATCH (liked_topic)<-[:CONTAINS]-(c:Cluster)-[:CONTAINS]->(rec_topic:Topic)
WHERE NOT (u)-[:INTERESTED_IN]->(rec_topic)
RETURN DISTINCT rec_topic.name AS Raccomandazione, c.id AS DalCluster
LIMIT 10;

// Query 7: Raccomandazione Basata su Categoria Raggruppata per 'Alessia'
MATCH (u:User {name:'Alessia'})-[:INTERESTED_IN]->(liked_topic:Topic)
MATCH (liked_topic)-[:BELONGS_TO]->(cat:Category)
MATCH (rec_topic:Topic)-[:BELONGS_TO]->(cat)
WHERE NOT (u)-[:INTERESTED_IN]->(rec_topic)
RETURN DISTINCT rec_topic.name AS Raccomandazione, cat.name AS DallaCategoria
LIMIT 10;

// Query 8: Utenti Interessati a Topic nel Cluster (sostituisci 'ID_CLUSTER')
MATCH (c:Cluster {id: 'ID_CLUSTER'})-[:CONTAINS]->(t:Topic)<-[:INTERESTED_IN]-(u:User)
RETURN DISTINCT u.name AS UtenteInteressato, t.name AS TopicDiInteresse, c.id AS ClusterID;

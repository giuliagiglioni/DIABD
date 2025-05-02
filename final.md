# 🧠 TrendSpotter: Analisi e Raccomandazione di Trend Emergenti da Flussi di Dati

## 🚀 Introduzione

**TrendSpotter** è un sistema distribuito progettato per l'identificazione e la raccomandazione di **trend emergenti** in tempo reale. Simula scenari di monitoraggio simili a Twitter Trends, Google News o aggregatori di flussi RSS, sfruttando tecnologie Big Data per offrire una soluzione completa: ingestione di dati in streaming, analisi testuale, clustering per l'identificazione di topic e visualizzazione semantica tramite grafo.

### 🎯 Obiettivi Principali

1.  **Identificare e Monitorare Trend:** Individuare gli argomenti più discussi e rilevanti all'interno di un flusso di notizie recenti.
2.  **Abilitare Raccomandazioni:** Costruire una struttura dati (grafo) che permetta di generare raccomandazioni personalizzate basate sugli interessi degli utenti (simulati) e sulle correlazioni tra argomenti e categorie.
3.  **Visualizzare Relazioni:** Offrire una rappresentazione visiva chiara dei legami tra argomenti (topic), categorie editoriali e cluster tematici scoperti automaticamente.

## 🧰 Stack Tecnologico

| Tecnologia        | Scopo                                                                      |
| :---------------- | :------------------------------------------------------------------------- |
| **Apache Kafka** | Ingestione e buffering di flussi di notizie simulate in tempo reale.         |
| **Apache Spark** | Elaborazione distribuita (batch e streaming), analisi testuale (TF-IDF), clustering (KMeans - Spark MLlib). |
| **Apache Hadoop** | Archiviazione distribuita (HDFS per dataset e modelli ML), gestione risorse cluster (YARN). |
| **Neo4j** | Modellazione, persistenza e visualizzazione del grafo della conoscenza (topic, categorie, cluster, utenti, relazioni). |
| **Python/PySpark**| Linguaggio principale per lo sviluppo degli script Spark, Kafka e Neo4j. |

## 📦 Dataset Utilizzato

* **Dataset Iniziale:** [News Category Dataset (Versione ridotta/modificata)](https://www.kaggle.com/datasets/rmisra/news-category-dataset) - Contiene notizie dal 2012 al 2022. Le colonne principali utilizzate sono:
    * `headline`: Titolo della notizia.
    * `short_description`: Breve descrizione.
    * `category`: Categoria editoriale originale.
    * `date`: Data di pubblicazione (formato `YYYY-MM-DD`).
* **Dati di Streaming (Simulati):** Il producer Kafka invia messaggi JSON con `headline` e `category`.
    ```json
    { "headline": "Nuova notizia su AI", "category": "TECH" }
    ```

## 🛠️ Setup Architettura e Installazione

Il sistema è stato implementato su un cluster simulato composto da 3 Virtual Machine (VM) Ubuntu 20.04 ospitate su un unico host fisico (Windows), configurate come segue:

* 🧠 **master** (`192.168.56.10`): NameNode HDFS, ResourceManager YARN, Broker Kafka, nodo driver Spark.
* ⚙️ **worker1** (`192.168.56.11`): DataNode HDFS, NodeManager YARN, nodo worker Spark.
* ⚙️ **worker2** (`192.168.56.12`): DataNode HDFS, NodeManager YARN, nodo worker Spark.

Il database a grafo **Neo4j viene eseguito direttamente sulla macchina host Windows**, separato dal cluster VM.

### 🔄 Trasferimento Dati VM <-> Host Windows

Per permettere agli script Python eseguiti sull'host Windows (per Neo4j) di accedere ai file CSV generati all'interno delle VM (dal job Spark Batch) o scaricati da HDFS (output dello streaming), è stata utilizzata una **cartella condivisa**.
* **Nome Host (Esempio):** `trendspotter_shared` (creata su Windows)
* **Punto di Mount nelle VM:** `/media/sf_shared` (configurato tramite le impostazioni di VirtualBox/VMware e le Guest Additions/Tools)
    I file vengono copiati in questa cartella condivisa dai nodi del cluster per essere poi letti dagli script Neo4j sull'host.

### 1. Prerequisiti VM (per ogni nodo)

* Ubuntu 20.04 Desktop/Server
* Minimo 4 core CPU, 8 GB RAM, 40 GB Disco
* Java 8 (`openjdk-8-jdk`)
* Python 3.10+ (`python3`, `python3-pip`)
* Librerie Python comuni (es. `neo4j`, `kafka-python`) - installabili via `pip`.
* SSH Server (`openssh-server`)
* Utilità: `net-tools`, `rsync`

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

### 4. Installazione Hadoop (HDFS+YARN)

* Scaricare una distribuzione Hadoop stabile (es. 3.2.4) sul nodo `master`.
* Estrarre l'archivio (es. in `/home/hadoop/hadoop`).
* Configurare le variabili d'ambiente Hadoop (`HADOOP_HOME`, aggiungere `$HADOOP_HOME/bin` e `$HADOOP_HOME/sbin` al `PATH`) in `~/.bashrc` su **tutti** i nodi. Non dimenticare `source ~/.bashrc`.
* **Configurare i file XML** in `$HADOOP_HOME/etc/hadoop/` come segue:
    * **`hadoop-env.sh`**: Impostare `export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64` (o il percorso corretto).
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
            <value>file:/home/hadoop/hadoop_data/hdfs/namenode</value> </property>
          <property>
            <name>dfs.datanode.data.dir</name>
            <value>file:/home/hadoop/hadoop_data/hdfs/datanode</value> </property>
          <property>
            <name>dfs.replication</name>
            <value>2</value> </property>
        </configuration>
        ```
    * **`mapred-site.xml`** (potrebbe essere necessario rinominare `mapred-site.xml.template`):
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
            <value>master</value> </property>
           <property>
               <name>yarn.application.classpath</name>
               <value>$HADOOP_CONF_DIR,$HADOOP_COMMON_HOME/share/hadoop/common/*,$HADOOP_COMMON_HOME/share/hadoop/common/lib/*,$HADOOP_HDFS_HOME/share/hadoop/hdfs/*,$HADOOP_HDFS_HOME/share/hadoop/hdfs/lib/*,$HADOOP_MAPRED_HOME/share/hadoop/mapreduce/*,$HADOOP_MAPRED_HOME/share/hadoop/mapreduce/lib/*,$HADOOP_YARN_HOME/share/hadoop/yarn/*,$HADOOP_YARN_HOME/share/hadoop/yarn/lib/*</value>
           </property>
        </configuration>
        ```
    * **`workers`** (o `slaves` nelle versioni precedenti): Elencare gli hostname dei nodi worker (e opzionalmente master se deve fare anche da datanode):
        ```
        master
        worker1
        worker2
        ```
* Creare le directory specificate in `hdfs-site.xml` su tutti i nodi rilevanti (es. `mkdir -p /home/hadoop/hadoop_data/hdfs/namenode` su master, `mkdir -p /home/hadoop/hadoop_data/hdfs/datanode` su master, worker1, worker2).
* Copiare la cartella Hadoop configurata (`/home/hadoop/hadoop`) dal `master` ai `worker` usando `scp`.
* **Formattare HDFS (SOLO LA PRIMA VOLTA!)** dal `master`: `hdfs namenode -format`
* Avviare HDFS e YARN dal `master`: `start-dfs.sh && start-yarn.sh`.
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

## 🧪 Preprocessing Dati Applicato

Prima dell'analisi, il dataset viene processato come segue nello script `analyze_batch.py`:

1.  **Filtraggio Temporale:** Vengono mantenuti solo i record con data `date >= "2020-01-01"` per focalizzarsi sui dati recenti e migliorare la rilevanza dei trend identificati, oltre a ottimizzare le performance.
2.  **Raggruppamento Categorie:** Le 42 categorie originali vengono mappate manualmente a 22 categorie semantiche più coerenti (es. `ARTS_CULTURE`, `BUSINESS_FINANCE`, `PARENTING_FAMILY`, `OTHER`, ecc.) per ridurre la frammentazione, migliorare l'interpretabilità dei cluster e semplificare il grafo. La colonna `category` viene sovrascritta con i nomi delle categorie raggruppate.

## ⚙️ Analisi e Clustering

* **Estrazione Feature:** Il testo combinato di `headline` e `short_description` viene pulito (lowercase, rimozione non-alfanumerici), tokenizzato e processato con `StopWordsRemover`. Successivamente, viene applicato **HashingTF** (con 5000 feature) seguito da **IDF** per generare vettori TF-IDF che rappresentano numericamente il contenuto testuale.
* **Clustering:** Viene utilizzato l'algoritmo **KMeans** (da Spark MLlib) per raggruppare gli articoli in `K` cluster (es. K=6 o altro valore sperimentato) basandosi sulla similarità dei loro vettori TF-IDF. Ogni articolo viene assegnato a un cluster (colonna `prediction`).
* **Valutazione Clustering:** Viene calcolato il **Silhouette Score**. Valori bassi (vicini a 0 o negativi) sono stati osservati, indicando cluster poco separati. Questo è attribuito ai limiti noti di TF-IDF nel catturare la semantica complessa del testo e all'alta dimensionalità/sparsità dei dati, un risultato comune in questo tipo di analisi. Si sottolinea che, nonostante la metrica, i cluster possono fornire insight qualitativi.
* **Salvataggio Modelli:** I modelli HashingTF, IDF e KMeans addestrati vengono salvati su HDFS per essere riutilizzati dal job di streaming.

## 📁 Struttura del Progetto (Riepilogo)
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

## 🚀 Come Eseguire il Progetto 


*(Nota: La cartella `models/` si trova su HDFS nel percorso specificato, non localmente)*

Assicurarsi che tutti i servizi HDFS, YARN, Kafka (Broker+ZK) e Neo4j siano attivi, i dati/script siano nelle posizioni corrette e la cartella condivisa sia montata e accessibile.

1.  **Avvio Servizi Hadoop** (solo se non già attivi, da `master` come utente `hadoop`):
    ```bash
    start-dfs.sh
    start-yarn.sh
    jps # Verifica processi attivi su master e worker
    #Per fermare fare (su Master):
    stop-dfs.sh && stop-yarn.sh
    ```
2.  **Avvio Servizi Kafka** (solo se non già attivi, da `master` come utente `hadoop` nella dir di Kafka):
    ```bash
    bin/zookeeper-server-start.sh -daemon config/zookeeper.properties
    bin/kafka-server-start.sh -daemon config/server.properties
    # Check su esistenza del topic
    bin/kafka-topics.sh --list --bootstrap-server master:9092 (se non resituisce "news" crearlo con comando di sopra)
    # Per terminare servizi fare:
    bin/kafka-server-stop.sh (PRIMA)
    bin/zookeeper-server-stop.sh (DOPO)
    ```
3.  **Esecuzione Analisi Batch** (da `master` come utente `hadoop` nella dir del progetto):
    ```bash
    cd ~/TrendSpotter-Cluster 
    spark-submit --master yarn sscripts/analyze_batch.py
    ```
    *(Questo passo crea i modelli ML su HDFS e i CSV locali in `data/output/`)*

4.  **Copia Risultati Batch per Neo4j:** Copia la cartella `TrendSpotter-Cluster/data/output/topics_with_cluster` dalla VM `master` alla macchina Windows dove gira Neo4j Desktop (es. tramite cartella condivisa montata in `/media/sf_shared`):
    ```bash
    # Esegui sulla VM master
    cp -r ~/TrendSpotter-Cluster/data/output/topics_with_cluster /media/sf_shared/
    ```

5.  **Costruzione Grafo Iniziale** (sull'**host Windows**, nella directory del progetto condivisa):
    ```powershell
    # Esempio da PowerShell, navigare nella dir giusta, in questo caso
    cd C:\trendspotter_shared
    python .\neo4j\scripts\graph_builder.py
    ```
    *(Assicurati che graph_builder.py punti al percorso corretto dei CSV, es. `../data/output/topics_with_cluster/sample_1000.csv` o simile)*

6.  **Avvio Job di Streaming** (da `master` come utente `hadoop` nella dir del progetto):
    ```bash
    cd ~/TrendSpotter-Cluster 
    spark-submit \
      --master yarn \
      --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 \
      scripts/streaming_job.py
    ```
    *(Lascia questo job in esecuzione in un terminale)*

7.  **Avvio Producer Kafka (Simulazione)** (da `master` in un **nuovo** terminale, come utente `hadoop` nella dir del progetto):
    ```bash
    cd ~/kafka 
    python kafka/producer.py
    ```
    *(Inviera notizie allo stream processato dal job al passo 6)*

8.  **(Su VM AMster Dopo un po') Copia Risultati Streaming per Neo4j:**
    * Lo streaming job scrive su HDFS (es. `hdfs://master:9000/user/hadoop/trendspotter/output/live_topics_XXXXXX`).
    * Copia queste cartelle da HDFS alla macchina Windows dove gira Neo4j (prima su FS locale della VM, poi sulla cartella condivisa):
        ```bash
        # Sulla VM master (sostituisci XXXXXX)
        hdfs dfs -get hdfs://master:9000/user/hadoop/trendspotter/output/live_topics_XXXXXX ~/temp_stream_output
        cp -r ~/temp_stream_output/live_topics_XXXXXX /media/sf_shared/
        rm -rf ~/temp_stream_output # Pulisci temp
        ```

9.  **Aggiornamento Grafo** (sull'**host Windows**): Esegui lo script posizionandoti nella directory condivisa.
    ```powershell
    # Esempio da PowerShell, navigare nella dir giusta, in questo caso
    cd C:\trendspotter_shared
    python .\neo4j\scripts\update_graph.py
    ```
    *(Assicurati che update_graph.py punti alle cartelle copiate al passo 8)*

## 📊 Grafo Neo4j ed Esplorazione

* Accedi a Neo4j Browser (`http://localhost:7474`).
* Il grafo conterrà nodi `:Topic`, `:Category` (con nomi raggruppati), `:Cluster`, `:User`.
* Le relazioni principali sono `:BELONGS_TO`, `:CONTAINS`, `:INTERESTED_IN`.
* **Query di Esempio per Esplorazione:**
    * `MATCH (n) RETURN labels(n) AS Tipo, count(*) AS Conteggio` (Conta nodi per tipo)
    * `MATCH (c:Cluster {id:'0'})-[:CONTAINS]->(t:Topic) RETURN t.name LIMIT 20` (Topic nel Cluster 0)
    * `MATCH (cat:Category {name:'POLITICS'})<-[:BELONGS_TO]-(t:Topic) RETURN t.name LIMIT 20` (Topic di Politica)
* **Query di Esempio per Raccomandazioni (Dimostrative):**
    * *Basate su Cluster:*
        ```cypher
        MATCH (u:User {name:'Alessia'})-[:INTERESTED_IN]->(:Topic)<-[:CONTAINS]-(c:Cluster)-[:CONTAINS]->(rec:Topic)
        WHERE NOT (u)-[:INTERESTED_IN]->(rec)
        RETURN DISTINCT rec.name, c.id LIMIT 10
        ```
    * *Basate su Categoria:*
        ```cypher
        MATCH (u:User {name:'Alessia'})-[:INTERESTED_IN]->(:Topic)-[:BELONGS_TO]->(cat:Category)
        MATCH (rec:Topic)-[:BELONGS_TO]->(cat)
        WHERE NOT (u)-[:INTERESTED_IN]->(rec)
        RETURN DISTINCT rec.name, cat.name LIMIT 10
        ```

## ✅ Conclusione

TrendSpotter dimostra con successo l'integrazione di Kafka, Spark, Hadoop e Neo4j per costruire una pipeline di analisi di flussi testuali. Il sistema è in grado di ingerire dati, processarli applicando tecniche di preprocessing (filtraggio temporale, raggruppamento semantico di categorie) e machine learning (clustering TF-IDF/KMeans per topic discovery), e di persistere e visualizzare le relazioni scoperte in un grafo della conoscenza. Sebbene la metrica quantitativa del clustering (Silhouette Score) evidenzi i limiti dell'approccio TF-IDF/KMeans su dati testuali complessi, la pipeline complessiva è funzionante e la struttura del grafo generato abilita efficacemente gli obiettivi di analisi dei trend e di raccomandazione personalizzata. Il progetto costituisce una solida base che potrebbe essere ulteriormente potenziata esplorando tecniche NLP più avanzate per la rappresentazione del testo.

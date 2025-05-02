# Setup completo cluster Hadoop (3 VM Ubuntu 20.04)

## ✅ 1. Installazione Ubuntu VM (per tutte e 3 le macchine)
- Scaricare Ubuntu 20.04 Desktop ISO
- Creare 3 VM: master, worker1, worker2
- Configurazione minima: 4 core, 8 GB RAM, 40 GB disco

### Rete VirtualBox:
- Scheda 1: NAT (per internet)
- Scheda 2: Rete interna (nome: cluster-net)

### File `/etc/netplan/01-netcfg.yaml` (es. master):
```yaml
network:
  version: 2
  ethernets:
    enp0s3:
      dhcp4: true
    enp0s8:
      dhcp4: no
      addresses: [192.168.56.10/24]
      nameservers:
        addresses: [8.8.8.8, 1.1.1.1]
```
> Cambiare IP per worker1 (192.168.56.11), worker2 (192.168.56.12)

Eseguire:
```bash
sudo netplan apply
```

### `/etc/hosts` su tutte le VM:
```
127.0.0.1 localhost
192.168.56.10 master
192.168.56.11 worker1
192.168.56.12 worker2
```

## ✅ 2. Configurazione utente e pacchetti (su ogni VM)
```bash
sudo adduser hadoop
sudo usermod -aG sudo hadoop
su - hadoop

sudo apt update && sudo apt install -y openjdk-8-jdk ssh python3-pip net-tools rsync
```

## ✅ 3. Setup SSH senza password (su ogni VM)
```bash
ssh-keygen -t rsa
cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys
chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys
```

Verifica:
```bash
ssh localhost
```

## ✅ 4. Setup Hadoop su master

### Crea file `setup_hadoop.sh` e incolla script preparato
> Avvia con:
```bash
chmod +x setup_hadoop.sh
./setup_hadoop.sh
```

### Dopo `source ~/.bashrc`, verifica:
```bash
hadoop version
```

## ✅ 5. Configura file Hadoop

### `core-site.xml`
```xml
<configuration>
  <property>
    <name>fs.defaultFS</name>
    <value>hdfs://master:9000</value>
  </property>
</configuration>
```

### `hdfs-site.xml`
```xml
<configuration>
  <property>
    <name>dfs.namenode.name.dir</name>
    <value>file:/home/hadoop/hadoop/data/namenode</value>
  </property>
  <property>
    <name>dfs.datanode.data.dir</name>
    <value>file:/home/hadoop/hadoop/data/datanode</value>
  </property>
  <property>
    <name>dfs.replication</name>
    <value>2</value>
  </property>
</configuration>
```

### `mapred-site.xml`
```xml
<configuration>
  <property>
    <name>mapreduce.framework.name</name>
    <value>yarn</value>
  </property>
</configuration>
```

### `yarn-site.xml`
```xml
<configuration>
    <!-- Servizi di base necessari per lo shuffle dei dati -->
    <property>
        <name>yarn.nodemanager.aux-services</name>
        <value>mapreduce_shuffle</value>
    </property>
    
    <!-- Configurazione del ResourceManager - punta al nodo master -->
    <property>
        <name>yarn.resourcemanager.hostname</name>
        <value>master</value>
    </property>
</configuration>
```

### `hadoop-env.sh`
Modifica:
```bash
export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
```

## ✅ 6. Format e avvio cluster su master
```bash
hdfs namenode -format
start-dfs.sh
start-yarn.sh
```

Verifica:
```bash
jps
```
Output atteso (master):
- NameNode
- DataNode
- ResourceManager
- NodeManager
- SecondaryNameNode

## ✅ 7. Configura file `slaves` o `workers`
```bash
nano ~/hadoop/etc/hadoop/workers
```
Contenuto:
```
master
worker1
worker2
```

## ✅ 8. Prepara i worker (se cloni le VM):
- Cambia hostname con `hostnamectl`
- Cambia IP in netplan
- Riavvia e controlla `ip a`

## ✅ 9. Copia la cartella Hadoop dal master ai worker:
```bash
scp -r ~/hadoop hadoop@worker1:/home/hadoop/
scp -r ~/hadoop hadoop@worker2:/home/hadoop/
```

Su ciascun worker:
```bash
source ~/.bashrc
hadoop version
```

## ✅ 10. Avvia cluster distribuito
Da `master`:
```bash
start-dfs.sh
start-yarn.sh
```

### Verifica con `jps` su ogni nodo:
- master → NameNode, ResourceManager, SecondaryNameNode
- worker1/2 → DataNode, NodeManager

### Interfacce web:
- HDFS → http://localhost:9870
- YARN → http://localhost:8088

---

💡 Pronto per installare Spark e Kafka, ora che il cluster Hadoop funziona!


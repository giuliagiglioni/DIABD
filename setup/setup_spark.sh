#!/bin/bash

# === setup_spark.sh ===

# 1. Impostazioni iniziali
SPARK_VERSION="3.5.0"
HADOOP_VERSION="3"
SPARK_ARCHIVE="spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}.tgz"
SPARK_URL="https://archive.apache.org/dist/spark/spark-${SPARK_VERSION}/${SPARK_ARCHIVE}"
INSTALL_DIR="$HOME/spark"

# 2. Scarica Spark solo se il file è assente o incompleto
cd $HOME
VALID_DOWNLOAD=false

if [ -f "$SPARK_ARCHIVE" ]; then
    echo "🔍 Verifica integrità archivio Spark..."
    FILESIZE=$(stat -c%s "$SPARK_ARCHIVE")
    if [ $FILESIZE -lt 100000000 ]; then
        echo "⚠️  Archivio Spark incompleto. Lo riscarico."
        rm -f "$SPARK_ARCHIVE"
    else
        echo "✅ Archivio Spark esistente e sembra valido"
        VALID_DOWNLOAD=true
    fi
fi

if [ "$VALID_DOWNLOAD" = false ]; then
    echo "⬇️  Scaricamento Spark $SPARK_VERSION ..."
    wget "$SPARK_URL" -O "$SPARK_ARCHIVE"
    if [ $? -ne 0 ]; then
        echo "❌ Errore durante il download di Spark. Interrotto."
        exit 1
    fi
fi

# 3. Estrai Spark
if [ -d "$INSTALL_DIR" ]; then
    echo "✅ Directory Spark già esistente"
else
    tar -xzf "$SPARK_ARCHIVE"
    if [ $? -ne 0 ]; then
        echo "❌ Estrazione fallita. L'archivio Spark potrebbe essere corrotto."
        rm -f "$SPARK_ARCHIVE"
        exit 1
    fi
    mv "spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}" "$INSTALL_DIR"
    echo "✅ Spark estratto in $INSTALL_DIR"
fi

# 4. Configurazione variabili d'ambiente
if ! grep -q "SPARK_HOME" ~/.bashrc; then
    echo "" >> ~/.bashrc
    echo "# Spark environment" >> ~/.bashrc
    echo "export SPARK_HOME=\$HOME/spark" >> ~/.bashrc
    echo "export PATH=\$PATH:\$SPARK_HOME/bin:\$SPARK_HOME/sbin" >> ~/.bashrc
    echo "✅ Variabili SPARK aggiunte a ~/.bashrc"
else
    echo "✅ Variabili SPARK già presenti in ~/.bashrc"
fi

# 5. Configura spark-env.sh
if [ -f "$INSTALL_DIR/conf/spark-env.sh.template" ]; then
    cp "$INSTALL_DIR/conf/spark-env.sh.template" "$INSTALL_DIR/conf/spark-env.sh"
    echo "export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64" >> "$INSTALL_DIR/conf/spark-env.sh"
    echo "export HADOOP_CONF_DIR=\$HOME/hadoop/etc/hadoop" >> "$INSTALL_DIR/conf/spark-env.sh"
    echo "export SPARK_WORKER_MEMORY=2g" >> "$INSTALL_DIR/conf/spark-env.sh"
    echo "export SPARK_MASTER_HOST=master" >> "$INSTALL_DIR/conf/spark-env.sh"
    echo "✅ spark-env.sh configurato"
else
    echo "❌ spark-env.sh.template non trovato. Verifica che l'estrazione sia andata a buon fine."
fi

# 6. Configurazione slaves/workers
if [ -d "$INSTALL_DIR/conf" ]; then
    echo -e "worker1\nworker2" > "$INSTALL_DIR/conf/workers"
    echo "✅ worker1 e worker2 aggiunti come worker"
else
    echo "❌ Directory conf mancante. Controlla l'installazione."
fi

# 7. Fine
source ~/.bashrc

exit 0

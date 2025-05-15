#!/usr/bin/env bash

# Script di installazione Hadoop 3.2.4 su Ubuntu 20.04
# ESEGUILO SOLO SULLA VM MASTER
# I WORKER dovranno ricevere la cartella hadoop già pronta via scp.

HADOOP_VERSION=3.2.4
HADOOP_TARBALL="hadoop-$HADOOP_VERSION.tar.gz"
DOWNLOAD_URL="https://downloads.apache.org/hadoop/common/hadoop-$HADOOP_VERSION/$HADOOP_TARBALL"
INSTALL_DIR="$HOME/hadoop"

cd "$HOME" || exit 1

# 1. Scarica Hadoop se non presente
if [ ! -f "$HADOOP_TARBALL" ]; then
    echo "⬇️  Scaricamento Hadoop $HADOOP_VERSION..."
    wget -q "$DOWNLOAD_URL" -O "$HADOOP_TARBALL"
    if [ $? -ne 0 ]; then
        echo "❌ Errore nel download. Verifica la connessione o l'URL."
        exit 1
    fi
    echo "✅ Scaricato: $HADOOP_TARBALL"
else
    echo "✅ Hadoop già scaricato."
fi

# 2. Estrai Hadoop
if [ ! -d "$INSTALL_DIR" ]; then
    echo "📦 Estrazione Hadoop..."
    tar -xzf "$HADOOP_TARBALL"
    mv "hadoop-$HADOOP_VERSION" "$INSTALL_DIR"
    echo "✅ Estratto in: $INSTALL_DIR"
else
    echo "✅ Directory Hadoop già presente: $INSTALL_DIR"
fi

# 3. Configura variabili ambiente in ~/.bashrc
if ! grep -q "HADOOP_HOME" ~/.bashrc; then
    JAVA_PATH="$(command -v java)"
    if [ -n "$JAVA_PATH" ]; then
        JAVA_HOME_DIR="$(dirname "$(dirname "$(readlink -f "$JAVA_PATH")")")"
    else
        JAVA_HOME_DIR="/usr/lib/jvm/java-8-openjdk-amd64"
    fi
    echo "" >> ~/.bashrc
    echo "# Hadoop env" >> ~/.bashrc
    echo "export JAVA_HOME=$JAVA_HOME_DIR" >> ~/.bashrc
    echo "export HADOOP_HOME=$INSTALL_DIR" >> ~/.bashrc
    echo "export PATH=\$PATH:\$HADOOP_HOME/bin:\$HADOOP_HOME/sbin" >> ~/.bashrc
    echo "✅ Variabili d'ambiente aggiunte a ~/.bashrc"
else
    echo "✅ Variabili già presenti in ~/.bashrc"
fi

# 4. Crea SOLO sul master le cartelle del namenode e datanode
if [ "$1" == "master" ]; then
    echo "🗂️  Preparazione HDFS per il master..."
    mkdir -p "$INSTALL_DIR/data/namenode"
    mkdir -p "$INSTALL_DIR/data/datanode"
    echo "✅ Cartelle namenode e datanode create su master"
else
    echo "⚠️  Skip creazione HDFS su questa macchina (non è il master)"
fi

# 5. Applica ~/.bashrc ora
source ~/.bashrc

# 6. Verifica Hadoop
HADOOP_VERSION_OUTPUT=$("$INSTALL_DIR/bin/hadoop" version 2>/dev/null | head -n1)
if echo "$HADOOP_VERSION_OUTPUT" | grep -q "$HADOOP_VERSION"; then
    echo "🎉 Hadoop installato correttamente: $HADOOP_VERSION_OUTPUT"
else
    echo "❌ Errore: Hadoop non installato correttamente"
fi

#!/bin/bash

# === setup_kafka.sh ===
# Script per installare e configurare Apache Kafka (con Zookeeper) su Ubuntu 20.04
# Va eseguito su una macchina con accesso a internet (di solito il master)
# Funziona solo come utente "hadoop" o altro utente non root

KAFKA_VERSION="3.6.0"
SCALA_VERSION="2.13"
KAFKA_ARCHIVE="kafka_${SCALA_VERSION}-${KAFKA_VERSION}.tgz"
KAFKA_URL="https://downloads.apache.org/kafka/${KAFKA_VERSION}/${KAFKA_ARCHIVE}"
INSTALL_DIR="$HOME/kafka"

# 1. Scarica Kafka
cd "$HOME"
if [ -f "$KAFKA_ARCHIVE" ]; then
    echo "✅ Archivio Kafka già presente."
else
    echo "⬇️  Scaricamento Kafka..."
    wget "$KAFKA_URL" -O "$KAFKA_ARCHIVE"
    if [ $? -ne 0 ]; then
        echo "❌ Errore nel download di Kafka. Interrotto."
        exit 1
    fi
fi

# 2. Estrai Kafka
if [ -d "$INSTALL_DIR" ]; then
    echo "✅ Directory Kafka già esistente."
else
    tar -xzf "$KAFKA_ARCHIVE"
    mv "kafka_${SCALA_VERSION}-${KAFKA_VERSION}" "$INSTALL_DIR"
    echo "✅ Kafka estratto in $INSTALL_DIR"
fi

# 3. Aggiungi variabili d'ambiente (se non presenti)
if ! grep -q "KAFKA_HOME" ~/.bashrc; then
    echo "" >> ~/.bashrc
    echo "# Kafka environment" >> ~/.bashrc
    echo "export KAFKA_HOME=\$HOME/kafka" >> ~/.bashrc
    echo "export PATH=\$PATH:\$KAFKA_HOME/bin" >> ~/.bashrc
    echo "✅ Variabili KAFKA aggiunte a ~/.bashrc"
fi

source ~/.bashrc

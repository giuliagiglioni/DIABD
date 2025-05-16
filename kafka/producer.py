# === kafka/producer.py ===
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable
import json
import time
import sys
import random 

# --- Configurazioni ---
KAFKA_BROKER = 'master:9092' # Indirizzo del broker Kafka
KAFKA_TOPIC = 'test'
INPUT_FILE = 'sample_news.jsonl' # File di input JSONL
SLEEP_TIME = 3 # Tempo di attesa tra gli invii di news

producer = None
try:
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BROKER,
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        api_version_auto_timeout_ms=10000 # Timeout per la connessione
    )
    print(f"\n✅ Producer connesso a {KAFKA_BROKER}")

    print(f"🚀 Inizio invio notizie da '{INPUT_FILE}' al topic '{KAFKA_TOPIC}'...")
    line_count = 0
    # Apertura e lettura file
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip() # Elimina spazi bianchi
            if not line: # Salta righe vuote
                continue

            try:
                article = json.loads(line)
                if 'headline' in article and 'category' in article:
                    line_count += 1
                    print(f"📤 Invio notizia {line_count}: {article['headline']} ({article['category']})")
                    producer.send(KAFKA_TOPIC, article)
                    producer.flush() 
                    # Pausa
                    print(f"  (pausa {SLEEP_TIME}s)")
                    time.sleep(SLEEP_TIME)
                else:
                    print(f"⚠️ Riga saltata (mancano chiavi): {line}")
            except json.JSONDecodeError:
                print(f"⚠️ Riga saltata (JSON non valido): {line}")
            except Exception as send_error:
                print(f"  ❌ Errore durante l'invio: {send_error}")

    print(f"\n✅ Fine lettura file. Inviate {line_count} notizie.")

except FileNotFoundError:
    print(f"\n❌ ERRORE CRITICO: File '{INPUT_FILE}' non trovato.")
    print("  Assicurati che il file esista nella stessa directory dello script.")
    sys.exit(1)
except NoBrokersAvailable:
    print(f"\n❌ ERRORE CRITICO: Impossibile connettersi ai broker Kafka a '{KAFKA_BROKER}'.")
    print("  Verifica che Kafka sia in esecuzione e raggiungibile.")
    sys.exit(1)
except Exception as e:
    print(f"\n❌ ERRORE nel producer: {e}")
    sys.exit(1)
finally:
    if producer:
        print("\n🚪 Chiusura connessione producer...")
        producer.close()
        print("✅ Connessione producer chiusa.")
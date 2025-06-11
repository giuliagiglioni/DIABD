
from neo4j import GraphDatabase
import csv
import glob

# 1. Connessione a Neo4j
uri = "bolt://master:7687"
user = "neo4j"
password = "progetto24"
driver = GraphDatabase.driver(uri, auth=(user, password))

# 2. Funzione per creare nodi Topic, Category e relazioni
def create_graph(tx, topic, cluster, category):
    tx.run("""
        MERGE (t:Topic {name: $topic})
        MERGE (c:Category {name: $category})
        MERGE (t)-[:BELONGS_TO]->(c)
        MERGE (cl:Cluster {id: $cluster})
        MERGE (cl)-[:CONTAINS]->(t)
    """, topic=topic, cluster=str(cluster), category=category)

# 3. Simula 2 utenti con interessi (per demo)
def add_users(tx):
    tx.run("""
        // Creazione di due utenti fittizi
      MERGE (daniele:User {name: 'Daniele'})
      MERGE (giulia:User {name: 'Giulia'})

      // Connetti Daniele a tutti i Topic della categoria POLITICS
      WITH daniele
      MATCH (politics_topic:Topic)-[:BELONGS_TO]->(c:Category {name: 'POLITICS'})
      MERGE (daniele)-[:INTERESTED_IN]->(politics_topic)

      // Connetti Giulia a tutti i Topic della categoria 
      WITH giulia
      MATCH (arts_topic:Topic)-[:BELONGS_TO]->(c2:Category {name: 'ENTERTAINMENT_MEDIA'})
      MERGE (giulia)-[:INTERESTED_IN]->(arts_topic)
    """)

# 4. Caricamento nodi e relazioni
with driver.session() as session:
    print("\n🔄 Importazione nodi e relazioni in corso...")

    files = glob.glob("../data/output/topics_with_cluster/part-*.csv")
    if not files:
        print("❌ Nessun file CSV trovato in 'topics_with_cluster/'")
    else:
        with open(files[0], encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                session.execute_write(create_graph, row['headline'], row['prediction'], row['category'])

        session.execute_write(add_users)
        print("\n✅ Grafo costruito in Neo4j con successo!")
        

import os
from neo4j import GraphDatabase
from dotenv import load_dotenv
load_dotenv()


def test_connection():
    driver = GraphDatabase.driver(
        os.getenv("NEO4J_URI"),
        auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
    )

    try:
        driver.verify_connectivity()
        print("✅ Erfolgreich mit Neo4j verbunden!\n")

        driver.execute_query("MATCH (n) DETACH DELETE n")


    except Exception as e:
        print(f"❌ Fehler bei der Verbindung: {e}")

    finally:
        driver.close()
        print("\nVerbindung geschlossen.")


if __name__ == "__main__":
    test_connection()
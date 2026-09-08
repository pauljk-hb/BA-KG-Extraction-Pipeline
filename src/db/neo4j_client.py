from neo4j import GraphDatabase
from src.config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
from src.models.schemas import CSVExponat, LLMGraphExtraction

class Neo4jClient:
    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    def close(self):
        self.driver.close()

    def init_constraints(self):
        labels = ["Person", "Firma", "Ort", "Material"]
        with self.driver.session() as session:
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (e:Exponat) REQUIRE e.werks_nr IS UNIQUE;")
            for label in labels:
                session.run(f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{label}) REQUIRE n.name IS UNIQUE;")
        print("✅ Constraints initialisiert.")

    def merge_exponate(self, exponate: list[CSVExponat]):
        query = """
        UNWIND $batch AS row
        // GEÄNDERT: Matching über werks_nr
        MERGE (e:Exponat {werks_nr: row.werks_nr})
        ON CREATE SET e.titel = row.titel
        """
        batch = [e.model_dump() for e in exponate]
        with self.driver.session() as session:
            session.run(query, batch=batch)

    def get_existing_vocabulary(self) -> dict:
        """Holt alle bisher in Neo4j existierenden Namen sortiert nach Typ (ohne Schema-Warnung)."""
        query = """
        MATCH (n)
        WHERE n:Person OR n:Firma OR n:Ort OR n:Material OR n:Exponat
        WITH labels(n)[0] AS typ,
             CASE 
                 WHEN n:Exponat THEN coalesce(n.titel, n.werks_nr)
                 ELSE n.name
             END AS bezeichnung
        WHERE bezeichnung IS NOT NULL AND trim(bezeichnung) <> ""
        RETURN typ, collect(DISTINCT bezeichnung) AS namen
        """
        with self.driver.session() as session:
            result = session.run(query)
            return {row["typ"]: row["namen"] for row in result}

    def merge_llm_kanten(self, extraction: LLMGraphExtraction):
        query = """
        UNWIND $kanten AS k
        MERGE (h:Entitaet {name: k.head.name}) ON CREATE SET h.typ = k.head.label
        MERGE (t:Entitaet {name: k.tail.name}) ON CREATE SET t.typ = k.tail.label
        MERGE (h)-[r:BEZIEHUNG {typ: k.relation_type}]->(t)
        """
        kanten_dict = [k.model_dump() for k in extraction.kanten]
        with self.driver.session() as session:
            session.run(query, kanten=kanten_dict)
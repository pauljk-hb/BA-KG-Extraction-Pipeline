from neo4j import GraphDatabase
from src.config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
from src.models.schemas import Exponat, LLMGraphExtraction


class Neo4jClient:
    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    def close(self):
        self.driver.close()

    def init_constraints(self):
        """Setzt Eindeutigkeits-Regeln (verhindert Duplikate)."""
        queries = [
            "CREATE CONSTRAINT IF NOT EXISTS FOR (e:Exponat) REQUIRE e.inventarnummer IS UNIQUE;",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (d:Dokument) REQUIRE d.signatur IS UNIQUE;"
        ]
        with self.driver.session() as session:
            for q in queries:
                session.run(q)
        print("✅ Constraints initialisiert.")

    def merge_exponate(self, exponate: list[Exponat]):
        """Schreibt Exponate deterministisch in die DB."""
        query = """
        UNWIND $batch AS row
        MERGE (e:Exponat {inventarnummer: row.inventarnummer})
        ON CREATE SET 
            e.titel = row.titel,
            e.bezeichnung = row.bezeichnung,
            e.roher_text = row.roher_text,
            e.llm_processed = false
        """
        batch = [e.model_dump() for e in exponate]
        with self.driver.session() as session:
            session.run(query, batch=batch)
        print(f"✅ {len(batch)} Exponate mit MERGE verarbeitet.")

    def get_unprocessed_texts(self) -> list[dict]:
        """Holt Texte, die das LLM noch nicht gesehen hat."""
        query = """
        MATCH (n)
        WHERE (n:Exponat OR n:Dokument) 
          AND n.llm_processed = false 
          AND (n.roher_text IS NOT NULL OR n.volltext IS NOT NULL)
        RETURN labels(n)[0] AS typ, 
               COALESCE(n.inventarnummer, n.signatur) AS id, 
               COALESCE(n.roher_text, n.volltext) AS text
        """
        with self.driver.session() as session:
            result = session.run(query)
            return [{"typ": r["typ"], "id": r["id"], "text": r["text"]} for r in result]

    def merge_llm_kanten(self, extraction: LLMGraphExtraction):
        """Speichert die vom LLM gefundenen Kanten ohne Duplikate."""
        query = """
        UNWIND $kanten AS kante

        // 1. Ursprungsknoten finden (Exponat oder Dokument)
        MATCH (quelle) WHERE quelle.inventarnummer = kante.quelle_id OR quelle.signatur = kante.quelle_id

        // 2. Extrahierte Entität finden oder anlegen
        MERGE (ziel:Entitaet {name: kante.ziel_entitaet.name})
        ON CREATE SET ziel.typ = kante.ziel_entitaet.label

        // 3. Kante verknüpfen (Generisch ohne APOC Plugin)
        MERGE (quelle)-[r:BEZUG_ZU {relation_type: kante.relation_type}]->(ziel)
        """
        kanten_dict = [k.model_dump() for k in extraction.kanten]
        with self.driver.session() as session:
            session.run(query, kanten=kanten_dict)

    def mark_as_processed(self, node_id: str):
        """Setzt das Verarbeitet-Flag auf true."""
        query = """
        MATCH (n) WHERE n.inventarnummer = $id OR n.signatur = $id
        SET n.llm_processed = true
        """
        with self.driver.session() as session:
            session.run(query, id=node_id)
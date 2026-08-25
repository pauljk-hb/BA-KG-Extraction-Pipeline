# src/main.py
import os
from src.db.neo4j_client import Neo4jClient
from src.extractors.csv_parser import parse_csv
from src.llm.groq_client import extract_graph_from_text


def run_pipeline():
    # Stelle sicher, dass Pfade stimmen
    base_dir = os.path.dirname(os.path.dirname(__file__))
    csv_path = os.path.join(base_dir, "data", "raw", "export.csv")

    db = Neo4jClient()

    print("\n--- STUFE 1: Deterministischer Import ---")
    db.init_constraints()

    # Lade strukturierte Exponate
    if os.path.exists(csv_path):
        exponate = parse_csv(csv_path)
        db.merge_exponate(exponate)
    else:
        print(f"⚠️ CSV nicht gefunden: {csv_path}")

    print("\n--- STUFE 2: LLM-Anreicherung (Idempotent) ---")

    # Hole nur Dokumente/Exponate mit unbearbeitetem Text
    unprocessed = db.get_unprocessed_texts()
    print(f"Gefundene Texte zur Analyse: {len(unprocessed)}")

    for item in unprocessed:
        # Überspringe leere Texte
        if not item["text"].strip():
            db.mark_as_processed(item["id"])
            continue

        print(f"➤ Analysiere Text für ID: {item['id']}...")

        try:
            # LLM Extraktion
            llm_result = extract_graph_from_text(text=item["text"], quelle_id=item["id"])

            # Kanten in DB schreiben
            if llm_result.kanten:
                db.merge_llm_kanten(llm_result)
                print(f"  └─ {len(llm_result.kanten)} Kanten extrahiert und gemerged.")

            # Als verarbeitet markieren
            db.mark_as_processed(item["id"])

        except Exception as e:
            print(f"❌ Fehler bei {item['id']}: {e}")

    db.close()
    print("\n✅ Pipeline-Durchlauf beendet!")


if __name__ == "__main__":
    run_pipeline()
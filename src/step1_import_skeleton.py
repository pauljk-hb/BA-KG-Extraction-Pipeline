from pathlib import Path
from src.db.neo4j_client import Neo4jClient
from src.extractors.csv_parser import parse_csv


def run_import():
    base_dir = Path(__file__).resolve().parent.parent
    csv_path = base_dir / "data" / "raw" / "export (1).csv"
    db = Neo4jClient()

    print("\n--- TEIL 1: Leitplanken (Skelett) aus CSV bauen ---")
    db.init_constraints()

    exponate = parse_csv(str(csv_path)) if csv_path.exists() else []

    if exponate:
        db.merge_exponate(exponate)
        print(f"✅ {len(exponate)} Exponate als Leitplanken in Neo4j angelegt.")
    else:
        print(f"⚠️ Keine Exponate in {csv_path.name} gefunden.")

    db.close()
    print("\n✅ Klassischer Import abgeschlossen!")


if __name__ == "__main__":
    run_import()
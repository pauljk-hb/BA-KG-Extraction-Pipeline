from pathlib import Path
from src.db.neo4j_client import Neo4jClient
from src.extractors.csv_parser import parse_csv
from src.extractors.pdf_parser import parse_pdfs
from src.llm.groq_client import extract_domain_graph


def get_processed_files_log(log_path: Path) -> set:
    if log_path.exists():
        with open(log_path, "r", encoding="utf-8") as f:
            return set(f.read().splitlines())
    return set()


def mark_file_processed(log_path: Path, file_id: str):
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"{file_id}\n")


def run_extraction():
    base_dir = Path(__file__).resolve().parent.parent
    csv_path = base_dir / "data" / "raw" / "export (1).csv"
    pdf_dir = base_dir / "data" / "raw"
    processed_log = base_dir / "data" / "logs" / "processed_texts.txt"

    # --- TEST LIMIT: Stell das auf 4 für deine ersten Tests ---
    MAX_DOCS_TO_PROCESS = 4

    db = Neo4jClient()
    processed_ids = get_processed_files_log(processed_log)

    print("\n--- TEIL 2: Vokabular für die KI abrufen ---")
    known_vocabulary = db.get_existing_vocabulary()
    print("📚 Bekanntes Vokabular geladen.")

    print("\n--- TEIL 3: Rohtexte an die KI füttern ---")
    alle_exponate = parse_csv(str(csv_path)) if csv_path.exists() else []
    dokumente = parse_pdfs(pdf_dir)

    processed_count = 0

    # 1. CSV Texte verarbeiten
    for e in alle_exponate:
        if processed_count >= MAX_DOCS_TO_PROCESS:
            break

        text_id = f"csv_desc_{e.werks_nr}"
        if e.roher_text.strip() and text_id not in processed_ids:
            print(f"\n➤ Analysiere CSV-Text (Werks-Nr: {e.werks_nr})...")
            try:
                llm_result = extract_domain_graph(e.roher_text, known_vocabulary)
                if llm_result and llm_result.kanten:
                    db.merge_llm_kanten(llm_result)
                    print(f"  └─ ✅ {len(llm_result.kanten)} Kanten in Neo4j gespeichert.")
                mark_file_processed(processed_log, text_id)
                processed_count += 1
            except Exception as ex:
                print(f"❌ Fehler bei {text_id}: {ex}")

    # 2. PDF Texte verarbeiten
    for d in dokumente:
        if processed_count >= MAX_DOCS_TO_PROCESS:
            break

        text_id = f"pdf_{d.signatur}"
        if d.volltext.strip() and text_id not in processed_ids:
            print(f"\n➤ Analysiere Brief: {d.signatur}...")
            try:
                llm_result = extract_domain_graph(d.volltext, known_vocabulary)
                if llm_result and llm_result.kanten:
                    db.merge_llm_kanten(llm_result)
                    print(f"  └─ ✅ {len(llm_result.kanten)} Kanten in Neo4j gespeichert.")
                mark_file_processed(processed_log, text_id)
                processed_count += 1
            except Exception as ex:
                print(f"❌ Fehler bei {text_id}: {ex}")

    db.close()
    print("\n✅ KI-Extraktion beendet!")


if __name__ == "__main__":
    run_extraction()
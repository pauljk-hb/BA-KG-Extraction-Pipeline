from pathlib import Path
from pypdf import PdfReader
from src.models.schemas import Dokument


def parse_pdfs(directory_path: Path | str) -> list[Dokument]:
    dokumente = []
    pdf_dir = Path(directory_path).resolve()

    if not pdf_dir.exists():
        print(f"⚠️ PDF-Pfad existiert nicht: {pdf_dir}")
        return dokumente

    pdf_files = list(pdf_dir.glob("*.pdf"))
    print(f"Gefundene PDF-Dateien auf Platte: {[f.name for f in pdf_files]}")

    for pdf_file in pdf_files:
        try:
            reader = PdfReader(str(pdf_file))
            volltext = "\n".join([page.extract_text() or "" for page in reader.pages])
            print(f"📄 {pdf_file.name}: {len(volltext.strip())} Zeichen extrahiert.")

            dokumente.append(Dokument(
                signatur=pdf_file.stem,
                dateipfad=str(pdf_file),
                volltext=volltext.strip()
            ))
        except Exception as e:
            print(f"❌ Fehler beim Lesen von {pdf_file.name}: {e}")

    return dokumente
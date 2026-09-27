import json
import time
from pathlib import Path
from groq import Groq
from src.config import GROQ_API_KEY
from src.models.schemas import LLMGraphExtraction
from src.utils.logger import ExperimentLogger

client = Groq(api_key=GROQ_API_KEY)
logger = ExperimentLogger()
MODEL_NAME = "openai/gpt-oss-120b"
CACHE_FILE = Path("data/logs/entity_cache.json")
PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"


def _load_prompt(filename: str) -> str:
    """Liest die Prompt-Datei aus dem prompts-Ordner ein."""
    file_path = PROMPTS_DIR / filename
    if not file_path.exists():
        raise FileNotFoundError(f"Prompt-Datei fehlt: {file_path}")
    return file_path.read_text(encoding="utf-8")


def _load_cache() -> dict:
    if CACHE_FILE.exists():
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_cache(cache_data: dict):
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache_data, f, ensure_ascii=False, indent=2)


def classify_entities(namen: set[str]) -> dict:
    cache = _load_cache()
    unbekannt = [n for n in namen if n not in cache]

    if unbekannt:
        print(f"🧠 LLM: Klassifiziere {len(unbekannt)} neue Akteure...")

        # Prompt aus Datei laden
        system_prompt = _load_prompt("classification.md")

        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(unbekannt, ensure_ascii=False)}
            ],
            model=MODEL_NAME,
            response_format={"type": "json_object"},
            temperature=0.0
        )
        try:
            neue_daten = json.loads(response.choices[0].message.content)
            cache.update(neue_daten)
            _save_cache(cache)
        except json.JSONDecodeError:
            print("❌ Fehler beim Parsen der LLM-Klassifizierung.")

    return {name: cache.get(name, "Firma") for name in namen}


def extract_domain_graph(text: str, known_vocabulary: dict = None) -> LLMGraphExtraction:
    vocab_context = f"\nBekannte Entitäten:\n{json.dumps(known_vocabulary, ensure_ascii=False)}" if known_vocabulary else ""

    # Prompt aus Datei laden und den Platzhalter durch das Vokabular ersetzen
    raw_prompt = _load_prompt("extraction.md")
    system_prompt = raw_prompt.replace("[VOCAB_CONTEXT]", vocab_context)

    start_time = time.time()
    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Extrahiere Relationen:\n\n{text}"}
        ],
        model=MODEL_NAME,
        response_format={"type": "json_object"},
        temperature=0.0
    )

    raw_json = response.choices[0].message.content
    parsed = LLMGraphExtraction.model_validate_json(raw_json)

    logger.log_run(
        model_name=MODEL_NAME, system_prompt=system_prompt,
        user_input=text, raw_response=raw_json, parsed_result=parsed,
        execution_time_sec=round(time.time() - start_time, 3)
    )
    return parsed
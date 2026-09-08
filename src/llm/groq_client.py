import json
import time
from groq import Groq
from src.config import GROQ_API_KEY
from src.models.schemas import LLMGraphExtraction
from src.utils.logger import ExperimentLogger

client = Groq(api_key=GROQ_API_KEY)
logger = ExperimentLogger(log_dir="data/logs")


def extract_domain_graph(text: str, known_vocabulary: dict = None) -> LLMGraphExtraction:
    vocab_context = ""
    if known_vocabulary:
        vocab_context = f"\nBekannte Entitäten in der Datenbank:\n{json.dumps(known_vocabulary, ensure_ascii=False)}\nNutze bevorzugt diese exakten Bezeichnungen, um Duplikate zu vermeiden."

    system_prompt = (
        "Du bist ein Experte für Wissensgraphen in einem Museumsarchiv. "
        "Extrahiere Beziehungen zwischen Personen, Firmen, Orten, Materialien und Exponaten als Tripel. "
        "Erlaubte Labels: 'Person', 'Firma', 'Ort', 'Material', 'Exponat'. "
        "Das Prädikat MUSS in UPPER_SNAKE_CASE sein (z. B. ENTWARF, HERGESTELLT_IN, ARBEITETE_FUER).\n\n"
        f"{vocab_context}\n\n"
        "Antworte ausschließlich im folgenden JSON-Format:\n"
        "{\n"
        '  "kanten": [\n'
        "    {\n"
        '      "subjekt": {"name": "Weinkanne", "label": "Exponat"},\n'
        '      "praedikat": "AUSGESTELLT_IN",\n'
        '      "objekt": {"name": "Berlin", "label": "Ort"}\n'
        "    }\n"
        "  ]\n"
        "}"
    )

    start_time = time.time()
    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Extrahiere alle Relationen aus folgendem Text:\n\n{text}"}
        ],
        model="openai/gpt-oss-120b",
        response_format={"type": "json_object"},
        temperature=0.0
    )

    execution_time = round(time.time() - start_time, 3)
    raw_json = response.choices[0].message.content
    parsed_result = LLMGraphExtraction.model_validate_json(raw_json)

    logger.log_run(
        model_name="llama-3.1-70b-versatile", system_prompt=system_prompt,
        user_input=text, raw_response=raw_json, parsed_result=parsed_result,
        temperature=0.0, execution_time_sec=execution_time,
        tags=["domain_extraction", "personen_firmen_orte"]
    )

    return parsed_result
# src/llm/groq_client.py
import time
from groq import Groq
from src.config import GROQ_API_KEY
from src.models.schemas import LLMGraphExtraction
from src.utils.logger import ExperimentLogger

# Clients initialisieren
client = Groq(api_key=GROQ_API_KEY)
logger = ExperimentLogger(log_dir="data/logs")


def extract_graph_from_text(text: str, quelle_id: str) -> LLMGraphExtraction:
    model_name = "llama-3.3-70b-versatile"
    temperature = 0.0

    system_prompt = (
        "You are an expert knowledge graph extractor for a museum archive. "
        "Extract relations from the text. "
        "You MUST return a JSON object with a single key 'kanten', containing a list of relations. "
        f"For every relation you extract, set the 'quelle_id' strictly to '{quelle_id}'. "
        "Formats: relation_type must be UPPER_SNAKE_CASE. Entities should be concise names."
    )
    user_prompt = f"Extract relations from:\n\n{text}"

    # Zeitmessung starten
    start_time = time.time()

    # API-Aufruf
    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        model=model_name,
        response_format={"type": "json_object"},
        temperature=temperature
    )

    # Ausführungszeit berechnen
    execution_time = round(time.time() - start_time, 3)

    # JSON parsen und validieren
    raw_json = response.choices[0].message.content
    parsed_result = LLMGraphExtraction.model_validate_json(raw_json)

    logger.log_run(
        model_name=model_name,
        system_prompt=system_prompt,
        user_input=user_prompt,
        raw_response=raw_json,
        parsed_result=parsed_result,
        temperature=temperature,
        execution_time_sec=execution_time,
        tags=["pipeline_extraction", "csv_freitext"]
    )

    return parsed_result
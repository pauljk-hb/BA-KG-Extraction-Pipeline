import os
from groq import Groq
from dotenv import load_dotenv
from neo4j import GraphDatabase
from pydantic import BaseModel, Field
load_dotenv()
from typing import LiteralString
from logger import ExperimentLogger

logger = ExperimentLogger(log_dir="data/logs")

class ExtractionItem(BaseModel):
    head: str = Field(description="Name der Quell-Entität")
    head_type: str = Field(description="Typ der Quell-Entität")
    relation: str = Field(description="Name der Beziehung (SNAKE_CASE oder UPPERCASE)")
    tail: str = Field(description="Name der Ziel-Entität")
    tail_type: str = Field(description="Typ der Ziel-Entität")


class KnowledgeGraphExtraction(BaseModel):
    relationships: list[ExtractionItem]

sample_text = (
        "Im Jahr 1924 entwarf Wilhelm Wagenfeld die berühmte Bauhaus-Leuchte in Weimar. "
        "Später zog der Designer nach Bremen, wo er über viele Jahre hinweg mit der AGIFA "
        "zusammenarbeitete und für diese neuartige Glaskollektionen gestaltete."
    )

system_prompt = (
    "You are a top-tier algorithm designed to extract information in structured formats for building knowledge graphs."
    "Your task is to identify the requested entities and relations with the user prompt from a given text."
    "Generate the output in JSON format, containing a list of JSON objects. "
    "Each object should contain the following keys: 'head', 'head_type', 'relation', 'tail' and 'tail_type'. "
    
    "Here is one example: Consider the following text: 'Adam has been a software engineer at Microsoft since 2009'. "
    "Example output structure:\n"
        "{\n"
        '  "relationships": [\n'
        '    {"head": "Adam", "head_type": "Person", "relation": "WORKS_FOR", "tail": "Microsoft", "tail_type": "Company"}\n'
        "  ]\n"
        "}"
)

model_name = "llama-3.1-8b-instant"
temperature = 0.1

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
chat_completion = client.chat.completions.create(
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Extract knowledge graph relationships from the following text:\n\n{sample_text}"}

    ],
    model=model_name,
    response_format={"type": "json_object"},
    temperature=temperature
)

raw_json = chat_completion.choices[0].message.content
extracted_relationships = KnowledgeGraphExtraction.model_validate_json(raw_json)

logger.log_run(
        model_name=model_name,
        system_prompt=system_prompt,
        user_input=sample_text,
        raw_response=raw_json,
        parsed_result=extracted_relationships,
        temperature=temperature,
        tags=["test_run", "wagenfeld_sample"],
    )

cypher_query: LiteralString  = """
    UNWIND $relationships AS rel

    // Quell-Knoten (Head) erstellen/suchen
    MERGE (h:Entity {name: rel.head})
    ON CREATE SET h.type = rel.head_type

    // Ziel-Knoten (Tail) erstellen/suchen
    MERGE (t:Entity {name: rel.tail})
    ON CREATE SET t.type = rel.tail_type

    // Gerichtete Kante (Relation) dynamisch zwischen Head und Tail erzeugen
    WITH h, t, rel
    CALL apoc.create.relationship(h, rel.relation, {}, t) YIELD rel AS r
    RETURN count(r)
    """

"""
driver = GraphDatabase.driver(
        os.getenv("NEO4J_URI"),
        auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
    )

try:
    driver.verify_connectivity()
    data_dict = extracted_relationships.model_dump()

    summary = driver.execute_query(
        cypher_query,
        relationships=data_dict["relationships"]
    )

    print(f"Import erfolgreich! Knoten/Kanten in Neo4j verarbeitet.")
    print(f"   In DB geänderte Elemente: {summary.counters}")

except Exception as e:
    print(f"Fehler bei der Verbindung: {e}")

finally:
    driver.close()
"""
print("--- Extrahierte Kanten (Knowledge Graph) ---")
print(chat_completion.choices[0].message.content)
print("------------------------")
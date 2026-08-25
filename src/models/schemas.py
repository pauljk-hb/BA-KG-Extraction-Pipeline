from pydantic import BaseModel, Field
from typing import List, Optional

# --- Deterministische Basis-Modelle (Aus CSV & Dateisystem) ---

class Exponat(BaseModel):
    inventarnummer: str
    titel: str
    bezeichnung: str
    roher_text: str = Field(default="", description="Unstrukturierte Bemerkungen für das LLM")
    llm_processed: bool = False

class Dokument(BaseModel):
    signatur: str
    dateipfad: str
    volltext: str = Field(default="", description="OCR-extrahierter Text des Briefes/PDFs")
    llm_processed: bool = False

# --- LLM-Extraktions-Modelle (Für Groq/Llama) ---

class LLMEntity(BaseModel):
    name: str = Field(description="Name der Entität, z.B. 'Wilhelm Wagenfeld' oder 'AGIFA'")
    label: str = Field(description="Typ, z.B. 'Person', 'Institution', 'Ort', 'Material'")

class LLMRelation(BaseModel):
    quelle_id: str = Field(description="Die Inventarnummer oder Signatur, aus der die Info stammt")
    relation_type: str = Field(description="SNAKE_CASE Kanten-Name, z.B. 'KORRESPONDIERTE_MIT'")
    ziel_entitaet: LLMEntity

class LLMGraphExtraction(BaseModel):
    kanten: List[LLMRelation]
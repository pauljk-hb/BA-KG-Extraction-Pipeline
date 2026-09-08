from typing import List, Literal
from pydantic import BaseModel, Field

# --- RAM-Modelle für Raw-Daten ---

class Exponat(BaseModel):
    werks_nr: str
    titel: str
    roher_text: str = Field(default="", description="Rohtext. Geht NICHT in die DB.")

class Dokument(BaseModel):
    signatur: str
    dateipfad: str
    volltext: str = Field(default="", description="Rohtext. Geht NICHT in die DB.")

# --- KI-Modelle für den Domänengraphen ---

EntityType = Literal["Person", "Firma", "Ort", "Exponat", "Material"]

class LLMEntity(BaseModel):
    name: str = Field(description="Exakter Name der Entität (z.B. 'Wilhelm Wagenfeld', 'WMF')")
    label: EntityType = Field(description="Typ der Entität")

class LLMRelation(BaseModel):
    head: LLMEntity = Field(description="Ausgangsentität des Tripels")
    relation_type: str = Field(description="Semantische Beziehung in UPPER_SNAKE_CASE")
    tail: LLMEntity = Field(description="Zielentität des Tripels")

class LLMGraphExtraction(BaseModel):
    kanten: List[LLMRelation]
import pandas as pd
from src.models.schemas import Exponat


def parse_csv(filepath: str) -> list[Exponat]:
    df = pd.read_csv(filepath, sep=",", dtype=str, encoding="utf-8").fillna("")
    exponate = []

    for _, row in df.iterrows():
        werks_nr = row.get("Werkverzeichnisnummer", "").strip()
        if not werks_nr:
            continue  # Ohne Werksnummer kein Eintrag im Graph

        exponate.append(Exponat(
            werks_nr=werks_nr,
            titel=(row.get("Titel") or row.get("Objekt.Titel") or "").strip(),
            roher_text=row.get("Bemerkungen", "").strip()
        ))
    return exponate
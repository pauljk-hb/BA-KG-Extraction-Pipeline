import pandas as pd
from src.models.schemas import Exponat


def parse_csv(filepath: str) -> list[Exponat]:
    # Passt sich an Semikolon-getrennte Exporte an
    df = pd.read_csv(filepath, sep=",", dtype=str).fillna("")

    exponate = []
    for _, row in df.iterrows():
        inv_nr = row.get("Objekt.Inventarnummer") or row.get("Andere_Nummer")
        if not inv_nr:
            continue

        exponate.append(Exponat(
            inventarnummer=inv_nr.strip(),
            titel=(row.get("Titel") or row.get("Objekt.Titel") or "").strip(),
            bezeichnung=(row.get("Objektbezeichnung") or "").strip(),
            roher_text=row.get("Bemerkungen", "").strip()
        ))
    return exponate
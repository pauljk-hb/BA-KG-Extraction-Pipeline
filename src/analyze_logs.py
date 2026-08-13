import pandas as pd
from pathlib import Path

# 1. JSONL-Datei laden
log_file = Path("data/logs/all_experiments.jsonl")

if not log_file.exists():
    print("Keine Log-Datei gefunden!")
    exit()

# Pandas liest JSONL zeilenweise nativ ein
df = pd.read_json(log_file, lines=True)

# 2. Verschachtelte JSON-Objekte (Nested JSON) in flache Spalten umwandeln
# Damit werden metadata, prompts, metrics zu eigenen Tabellenspalten
metadata_df = pd.json_normalize(df["metadata"])
metrics_df = pd.json_normalize(df["output"].apply(lambda x: x.get("metrics", {})))

# Tabellen zusammenfügen
full_df = pd.concat([df[["experiment_id", "timestamp"]], metadata_df, metrics_df], axis=1)

# Timestamp in echtes Datetime-Objekt umwandeln (für Zeitreihen)
full_df["timestamp"] = pd.to_datetime(full_df["timestamp"])

print("--- Übersicht deiner Experimente ---")
print(full_df)

print("\n--- Statistische Auswertung ---")
print(f"Gesamtzahl Versuche: {len(full_df)}")
print(f"Durchschnittliche Laufzeit: {full_df['execution_time_sec'].mean():.2f} Sekunden")
print(f"Durchschnittlich extrahierte Kanten: {full_df['extracted_edges_count'].mean():.1f}")
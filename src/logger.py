import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from pydantic import BaseModel


class ExperimentLogger:
    """Helper-Klasse zur Dokumentation von Prompt-Szenarien und LLM-Outputs."""

    def __init__(self, log_dir: str = "data/logs"):
        """Initialisiert das Log-Verzeichnis relativ zum Projekt.

        :param log_dir: Pfad zum Ordner, in dem die Logs gespeichert werden.
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.summary_file = self.log_dir / "all_experiments.jsonl"

    def log_run(
        self,
        model_name: str,
        system_prompt: str,
        user_input: str,
        raw_response: str,
        parsed_result: Optional[Any] = None,
        temperature: float = 0.1,
        execution_time_sec: Optional[float] = None,
        tags: Optional[list[str]] = None,
    ) -> Path:
        """Speichert einen einzelnen Versuch als strukturierte JSON-Datei.

        :param model_name: Name des genutzten LLM (z.B. 'llama-3.3-70b-versatile')
        :param system_prompt: Der verwendete System-Prompt
        :param user_input: Der analysierte Eingabetext
        :param raw_response: Der unstrukturierte Raw-Output des LLM
        :param parsed_result: Das geparste Ergebnis (Pydantic-Modell oder dict)
        :param temperature: Verwendete LLM-Temperatur
        :param execution_time_sec: Laufzeit der Inferenz in Sekunden
        :param tags: Beliebige Tags zur Filterung (z.B. ['test', 'wagenfeld_briefe'])
        :return: Pfad zur erstellten JSON-Datei
        """
        now = datetime.now()
        timestamp_str = now.strftime("%Y%m%d_%H%M%S_%f")[:19]
        date = now.strftime("%d.%m.%Y-%H:%M")

        # Falls ein Pydantic-Modell übergeben wurde, in dict umwandeln
        if isinstance(parsed_result, BaseModel):
            parsed_data = parsed_result.model_dump()
        else:
            parsed_data = parsed_result

        # Extrahiere Metriken für schnelle Analysen (z.B. wie viele Kanten gefunden wurden)
        edges_count = None
        if isinstance(parsed_data, dict) and "relationships" in parsed_data:
            edges_count = len(parsed_data["relationships"])

        log_payload = {
            "experiment_id": f"exp_{timestamp_str}",
            "timestamp": now.isoformat(),
            "timestamp_human": now.strftime("%d.%m.%Y - %H:%M"),
            "metadata": {
                "model_name": model_name,
                "temperature": temperature,
                "execution_time_sec": execution_time_sec,
                "tags": tags or [],
            },
            "prompts": {
                "system_prompt": system_prompt,
                "user_input": user_input,
            },
            "output": {
                "raw_response": raw_response,
                "parsed_result": parsed_data,
                "metrics": {
                    "extracted_edges_count": edges_count,
                },
            },
        }

        # 1. Als Einzeldatei (Einzelauswertung) speichern
        single_log_file = self.log_dir / f"exp_{timestamp_str}.json"
        with open(single_log_file, "w", encoding="utf-8") as f:
            json.dump(log_payload, f, ensure_ascii=False, indent=2)

        # 2. In die zentrale JSONL-Datei anhängen (für spätere Batch-Analysen)
        with open(self.summary_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_payload, ensure_ascii=False) + "\n")

        print(f"📝 Experiment protokoliert: {single_log_file.name}")
        return single_log_file
from __future__ import annotations

import csv
import json
import shutil
from dataclasses import asdict
from datetime import datetime
from uuid import uuid4

from .config import CSV_PATH, SENT_DIR, SESSIONS_DIR
from .models import MeasurementRecord, MeasurementSession


class PersistenceMixin:
    def start_new_session(self) -> None:
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S_") + uuid4().hex[:6]
        self.session = MeasurementSession(session_id=session_id, operador=self.operator_id)
        self.status_text = ""

    def reset_operator_only(self) -> None:
        self.session = None
        self.input_value = ""
        self.circuit_inputs = {"A": "", "B": ""}
        self.selected_index = 0
        self.status_text = ""

    def save_session(self) -> None:
        if self.session is None:
            return
        self.session.atualizado_em = datetime.now().isoformat(timespec="seconds")
        path = SESSIONS_DIR / f"{self.session.session_id}.json"
        with path.open("w", encoding="utf-8") as f:
            json.dump(asdict(self.session), f, ensure_ascii=False, indent=2)

    def append_measurement_csv(self, record: MeasurementRecord) -> None:
        CSV_PATH.parent.mkdir(exist_ok=True)
        exists = CSV_PATH.exists()
        with CSV_PATH.open("a", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(asdict(record).keys()), delimiter=";")
            if not exists:
                writer.writeheader()
            writer.writerow(asdict(record))

    def simulate_send_pending_sessions(self) -> int:
        sent_count = 0
        for path in SESSIONS_DIR.glob("*.json"):
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("enviado_em"):
                continue
            data["estado"] = "enviado"
            data["enviado_em"] = datetime.now().isoformat(timespec="seconds")
            with path.open("w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            shutil.copy2(path, SENT_DIR / path.name)
            sent_count += 1
        return sent_count

    def pending_sessions_count(self) -> int:
        count = 0
        for path in SESSIONS_DIR.glob("*.json"):
            try:
                with path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                if not data.get("enviado_em"):
                    count += 1
            except json.JSONDecodeError:
                continue
        return count

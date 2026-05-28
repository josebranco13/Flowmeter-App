from __future__ import annotations

import csv
import json
import shutil
from dataclasses import asdict
from datetime import datetime
from typing import Any
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
        self.side_options = []
        self.current_side = ""
        self.current_circuit = 0
        self.samples = []
        self.measurement_running = False
        self.last_measurement_record = None
        self.selected_result_index = 0
        self.circuit_active_field = 0
        self.operator_list_open = False
        self.selected_menu_option = ""
        self.selected_mold_side_index = 0
        self.mold_side_dropdown_open = False
        self.selected_index = 0
        self.status_text = ""

    def logout(self) -> None:
        self.reset_operator_only()
        self.operator_id = ""
        self.pin = ""
        self.login_active_field = 0
        self.operator_selected_index = 0

    def refresh_operator_options(self) -> None:
        operators = {str(operator).strip() for operator in self.operator_options}
        operators.discard("")

        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        for path in SESSIONS_DIR.glob("*.json"):
            try:
                with path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
            except (OSError, json.JSONDecodeError):
                continue

            operator = str(data.get("operador", "")).strip()
            if operator:
                operators.add(operator)

        self.operator_options = sorted(operators, key=self.operator_sort_key)
        if not self.operator_options:
            self.operator_selected_index = 0
            return

        if self.operator_list_open:
            self.operator_selected_index = min(
                self.operator_selected_index,
                len(self.operator_options) - 1,
            )
            return

        if self.operator_id in self.operator_options:
            self.operator_selected_index = self.operator_options.index(self.operator_id)
        else:
            self.operator_selected_index = min(
                self.operator_selected_index,
                len(self.operator_options) - 1,
            )

    @staticmethod
    def operator_sort_key(operator: str) -> tuple[int, int | str, str]:
        if operator.isdigit():
            return (0, int(operator), operator)
        return (1, operator.casefold(), operator)

    def save_session(self) -> None:
        if self.session is None:
            return
        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        self.session.atualizado_em = datetime.now().isoformat(timespec="seconds")
        path = SESSIONS_DIR / f"{self.session.session_id}.json"
        with path.open("w", encoding="utf-8") as f:
            json.dump(asdict(self.session), f, ensure_ascii=False, indent=2)

    def append_measurement_csv(self, record: MeasurementRecord) -> None:
        CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
        exists = CSV_PATH.exists()
        with CSV_PATH.open("a", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(asdict(record).keys()), delimiter=";")
            if not exists:
                writer.writeheader()
            writer.writerow(asdict(record))

    def simulate_send_pending_sessions(self) -> int:
        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        SENT_DIR.mkdir(parents=True, exist_ok=True)
        sent_count = 0
        for path in SESSIONS_DIR.glob("*.json"):
            try:
                with path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
            except (OSError, json.JSONDecodeError):
                continue
            if not isinstance(data, dict):
                continue
            if data.get("enviado_em"):
                continue
            data["estado"] = "enviado"
            data["enviado_em"] = datetime.now().isoformat(timespec="seconds")
            with path.open("w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            shutil.copy2(path, SENT_DIR / path.name)
            sent_count += 1
        return sent_count

    def load_pending_sessions(self) -> list[dict[str, Any]]:
        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        sessions: list[dict[str, Any]] = []
        for path in SESSIONS_DIR.glob("*.json"):
            try:
                with path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
            except (OSError, json.JSONDecodeError):
                continue

            if not isinstance(data, dict):
                continue

            if data.get("enviado_em"):
                continue

            data["_file_name"] = path.name
            sessions.append(data)

        return sorted(
            sessions,
            key=lambda item: str(
                item.get("atualizado_em") or item.get("criado_em") or item.get("session_id") or ""
            ),
            reverse=True,
        )

    def pending_sessions_count(self) -> int:
        return len(self.load_pending_sessions())

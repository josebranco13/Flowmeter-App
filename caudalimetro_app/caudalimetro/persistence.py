from __future__ import annotations

import csv
import json
import shutil
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from .config import (
    CSV_PATH,
    OPERATOR_OPTIONS,
    OPERATOR_PASSWORDS,
    OPERATORS_PATH,
    SENT_DIR,
    SESSIONS_DIR,
)
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
        self.measurement_reviewing_saved_result = False
        self.last_measurement_record = None
        self.selected_result_index = 0
        self.result_editing = False
        self.circuit_active_field = 0
        self.operator_list_open = False
        self.admin_operator_input = ""
        self.admin_new_operator_name = ""
        self.admin_new_operator_pin = ""
        self.admin_add_active_field = 0
        self.selected_admin_operator_index = 0
        self.pending_admin_operator_removal = ""
        self.admin_operator_labels = []
        self.admin_visible_indices = []
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
        self.load_operator_options()
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

    def normalize_operator_name(self, value: str) -> str:
        return value.strip().upper()

    def load_operator_passwords(self) -> None:
        self.operator_passwords = {
            self.normalize_operator_name(operator): str(pin).zfill(4)
            for operator, pin in OPERATOR_PASSWORDS.items()
        }

    def operator_expected_pin(self, operator: str) -> str | None:
        return self.operator_passwords.get(self.normalize_operator_name(operator))

    def operator_pin_matches(self, operator: str, pin: str) -> bool:
        expected_pin = self.operator_expected_pin(operator)
        if expected_pin is None:
            return False
        return pin == expected_pin

    def sorted_operator_options(self, operators: list[str]) -> list[str]:
        normalized = {
            self.normalize_operator_name(operator)
            for operator in operators
            if self.normalize_operator_name(operator)
        }
        normalized.add("ADMIN")
        return sorted(normalized, key=self.operator_sort_key)

    def load_operator_options(self) -> None:
        self.load_operator_passwords()
        operators = OPERATOR_OPTIONS.copy()
        if OPERATORS_PATH.exists():
            try:
                with OPERATORS_PATH.open("r", encoding="utf-8") as f:
                    data = json.load(f)
            except (OSError, json.JSONDecodeError):
                data = []

            if isinstance(data, list):
                operators = [str(operator) for operator in data]
            elif isinstance(data, dict):
                stored_operators = data.get("operators")
                if isinstance(stored_operators, list):
                    operators = [str(operator) for operator in stored_operators]

                stored_passwords = data.get("passwords")
                if isinstance(stored_passwords, dict):
                    for operator, pin in stored_passwords.items():
                        name = self.normalize_operator_name(str(operator))
                        if name:
                            self.operator_passwords[name] = str(pin).zfill(4)

        self.operator_options = self.sorted_operator_options(operators)
        self.save_operator_options()

    def save_operator_options(self) -> None:
        OPERATORS_PATH.parent.mkdir(parents=True, exist_ok=True)
        passwords = {
            operator: self.operator_passwords[operator]
            for operator in self.operator_options
            if operator in self.operator_passwords
        }
        data = {
            "operators": self.operator_options,
            "passwords": passwords,
        }
        with OPERATORS_PATH.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def managed_operator_options(self) -> list[str]:
        return [operator for operator in self.operator_options if operator != "ADMIN"]

    def add_operator(self, operator: str, pin: str) -> tuple[bool, str]:
        name = self.normalize_operator_name(operator)
        if not name:
            return False, "Indique o nome do operador."
        pin = pin.strip()
        if not pin.isdigit() or len(pin) != 4:
            return False, "Indique um PIN com 4 digitos."
        if name == "ADMIN":
            return False, "ADMIN já existe."
        if name in self.operator_options:
            if name not in self.operator_passwords:
                self.operator_passwords[name] = pin
                self.save_operator_options()
                return True, f"PIN do operador {name} configurado."
            return False, f"Operador {name} já existe."

        self.operator_passwords[name] = pin
        self.operator_options = self.sorted_operator_options([*self.operator_options, name])
        self.save_operator_options()
        return True, f"Operador {name} criado."

    def remove_operator(self, operator: str) -> tuple[bool, str]:
        name = self.normalize_operator_name(operator)
        if name == "ADMIN":
            return False, "ADMIN não pode ser removido."
        if name not in self.operator_options:
            return False, "Operador não encontrado."

        self.operator_options = [item for item in self.operator_options if item != name]
        self.operator_passwords.pop(name, None)
        self.save_operator_options()
        return True, f"Operador {name} removido."

    @staticmethod
    def operator_sort_key(operator: str) -> tuple[int, str, str]:
        return (0 if operator == "ADMIN" else 1, operator.casefold(), operator)

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

    def pending_session_file(self, file_name: str) -> Path | None:
        if file_name != Path(file_name).name:
            return None
        path = SESSIONS_DIR / file_name
        if path.suffix.lower() != ".json":
            return None
        return path

    def load_pending_session_file(
        self, file_name: str
    ) -> tuple[Path, dict[str, Any]] | None:
        path = self.pending_session_file(file_name)
        if path is None or not path.exists():
            return None
        try:
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            return None
        if not isinstance(data, dict) or data.get("enviado_em"):
            return None
        return path, data

    def delete_pending_session(self, file_name: str) -> bool:
        loaded = self.load_pending_session_file(file_name)
        if loaded is None:
            return False

        path, _ = loaded
        try:
            path.unlink()
        except OSError:
            return False
        return True

    def simulate_send_pending_session(self, file_name: str) -> bool:
        loaded = self.load_pending_session_file(file_name)
        if loaded is None:
            return False

        path, data = loaded
        SENT_DIR.mkdir(parents=True, exist_ok=True)
        sent_at = datetime.now().isoformat(timespec="seconds")
        data["estado"] = "enviado"
        data["atualizado_em"] = sent_at
        data["enviado_em"] = sent_at
        try:
            with path.open("w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            shutil.copy2(path, SENT_DIR / path.name)
        except OSError:
            return False
        return True

    def delete_pending_measurement(self, file_name: str, measurement_index: int) -> bool:
        loaded = self.load_pending_session_file(file_name)
        if loaded is None:
            return False

        path, data = loaded
        measurements = data.get("medicoes")
        if not isinstance(measurements, list):
            return False
        if measurement_index < 0 or measurement_index >= len(measurements):
            return False

        measurements.pop(measurement_index)
        data["atualizado_em"] = datetime.now().isoformat(timespec="seconds")
        if measurements:
            try:
                with path.open("w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            except OSError:
                return False
        else:
            try:
                path.unlink()
            except OSError:
                return False
        return True

    def simulate_send_pending_measurement(
        self, file_name: str, measurement_index: int
    ) -> bool:
        loaded = self.load_pending_session_file(file_name)
        if loaded is None:
            return False

        path, data = loaded
        measurements = data.get("medicoes")
        if not isinstance(measurements, list):
            return False
        if measurement_index < 0 or measurement_index >= len(measurements):
            return False

        SENT_DIR.mkdir(parents=True, exist_ok=True)
        sent_at = datetime.now().isoformat(timespec="seconds")
        if len(measurements) == 1:
            data["estado"] = "enviado"
            data["atualizado_em"] = sent_at
            data["enviado_em"] = sent_at
            try:
                with path.open("w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                shutil.copy2(path, SENT_DIR / path.name)
            except OSError:
                return False
            return True

        selected_measurement = measurements[measurement_index]
        sent_data = data.copy()
        sent_data["estado"] = "enviado"
        sent_data["atualizado_em"] = sent_at
        sent_data["enviado_em"] = sent_at
        sent_data["medicoes"] = [selected_measurement]
        sent_name = (
            f"{path.stem}_medicao_{measurement_index + 1}_"
            f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:6]}.json"
        )
        try:
            with (SENT_DIR / sent_name).open("w", encoding="utf-8") as f:
                json.dump(sent_data, f, ensure_ascii=False, indent=2)

            measurements.pop(measurement_index)
            data["atualizado_em"] = sent_at
            with path.open("w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except OSError:
            return False
        return True

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

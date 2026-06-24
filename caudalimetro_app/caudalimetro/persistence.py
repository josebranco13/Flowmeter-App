from __future__ import annotations

import csv
import json
import shutil
from copy import deepcopy
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from .database import (
    authenticate_user,
    change_user_password,
    create_user,
    delete_user,
    get_usernames,
)
from .config import (
    CSV_PATH,
    DIAMETER_LABELS,
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
        self.circuit_inputs = {"count": "", "start": ""}
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
        self.admin_reset_operator_name = ""
        self.admin_reset_operator_pin = ""
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

    def operator_pin_matches(self, operator: str, pin: str) -> bool:
        return authenticate_user(operator, pin)

    def sorted_operator_options(self, operators: list[str]) -> list[str]:
        normalized = {
            self.normalize_operator_name(operator)
            for operator in operators
            if self.normalize_operator_name(operator)
        }
        normalized.add("ADMIN")
        return sorted(normalized, key=self.operator_sort_key)

    def load_operator_options(self) -> None:
        self.operator_options = get_usernames()

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
        
        success, message = create_user(name, pin)

        if success:
            self.load_operator_options()
        
        return success, message

    def remove_operator(self, operator: str) -> tuple[bool, str]:
        name = self.normalize_operator_name(operator)
        
        success, message = delete_user(name)

        if success:
            self.load_operator_options()

        return success, message

    def reset_operator_password(self, operator: str, pin: str) -> tuple[bool, str]:
        name = self.normalize_operator_name(operator)
        if not name:
            return False, "Selecione um operador."
        pin = pin.strip()
        if not pin.isdigit() or len(pin) != 4:
            return False, "Indique um PIN com 4 digitos."
        if name == "ADMIN":
            return False, "Password do ADMIN nao pode ser alterada aqui."

        success, message = change_user_password(name, pin)
        if success:
            self.load_operator_options()
        return success, message

    @staticmethod
    def operator_sort_key(operator: str) -> tuple[int, str, str]:
        return (0 if operator == "ADMIN" else 1, operator.casefold(), operator)

    @staticmethod
    def export_diameter_value(value: Any) -> Any:
        if isinstance(value, bool) or value in (None, ""):
            return value
        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            return value
        if not numeric_value.is_integer():
            return value
        diameter = int(numeric_value)
        return DIAMETER_LABELS.get(diameter, f"{diameter} mm")

    def session_data_for_export(self, data: dict[str, Any]) -> dict[str, Any]:
        exported = deepcopy(data)
        if "diametro_mm" in exported:
            exported["diametro_mm"] = self.export_diameter_value(
                exported.get("diametro_mm")
            )

        measurements = exported.get("medicoes")
        if isinstance(measurements, list):
            duplicate_measurement_fields = (
                "session_id",
                "operador",
                "molde",
                "diametro_mm",
                "pressao_entrada_bar",
                "lado",
            )
            for measurement in measurements:
                if isinstance(measurement, dict):
                    for field in duplicate_measurement_fields:
                        measurement.pop(field, None)
        return exported

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
        exported_data = self.session_data_for_export(data)
        try:
            with path.open("w", encoding="utf-8") as f:
                json.dump(exported_data, f, ensure_ascii=False, indent=2)
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
            exported_data = self.session_data_for_export(data)
            try:
                with path.open("w", encoding="utf-8") as f:
                    json.dump(exported_data, f, ensure_ascii=False, indent=2)
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
        sent_data = self.session_data_for_export(sent_data)
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
            exported_data = self.session_data_for_export(data)
            with path.open("w", encoding="utf-8") as f:
                json.dump(exported_data, f, ensure_ascii=False, indent=2)
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

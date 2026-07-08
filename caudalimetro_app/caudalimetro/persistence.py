from __future__ import annotations

import csv
import json
import os
import re
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
    PDF_EXPORTS_DIR,
    SENT_DIR,
    SESSIONS_DIR,
)
from .models import MeasurementRecord, MeasurementSession
from .email_sender import EMAIL_SENT_FIELD, send_automatic_exports_if_configured
from .pdf_exporter import generate_flow_report


COMPLETED_SESSION_STATE = "concluida"
LEGACY_COMPLETED_SESSION_STATES = {"confirmada_operador"}


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
        self.send_review_checked_group_keys = set()
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
        text = str(value).strip().replace('"', "")
        compact = text.replace(" ", "")
        valid_labels = set(DIAMETER_LABELS.values())
        if compact in valid_labels:
            return compact
        try:
            numeric_text = compact
            if numeric_text.casefold().endswith("mm"):
                numeric_text = numeric_text[:-2]
            numeric_value = float(numeric_text.replace(",", "."))
        except (TypeError, ValueError):
            return value
        if not numeric_value.is_integer():
            return value
        diameter = int(numeric_value)
        legacy_labels = {
            8: "3/8",
        }
        return DIAMETER_LABELS.get(diameter) or legacy_labels.get(diameter, value)

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
        self.session.atualizado_em = datetime.now().isoformat(timespec="seconds")
        path = SESSIONS_DIR / f"{self.session.session_id}.json"

        if not self.is_completed_session_state(self.session.estado):
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass
            return

        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(asdict(self.session), f, ensure_ascii=False, indent=2)

    @staticmethod
    def is_completed_session_state(estado: Any) -> bool:
        return str(estado or "").strip().casefold() == COMPLETED_SESSION_STATE

    @staticmethod
    def is_legacy_completed_session_state(estado: Any) -> bool:
        return str(estado or "").strip().casefold() in LEGACY_COMPLETED_SESSION_STATES

    @staticmethod
    def remove_session_file(path: Path) -> None:
        try:
            path.unlink()
        except OSError:
            pass

    def normalize_sessions_dir(self) -> None:
        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        for path in SESSIONS_DIR.glob("*.json"):
            try:
                with path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
            except (OSError, json.JSONDecodeError):
                self.remove_session_file(path)
                continue

            if not isinstance(data, dict):
                self.remove_session_file(path)
                continue

            estado = data.get("estado")
            if self.is_completed_session_state(estado) and not data.get("enviado_em"):
                continue

            if (
                self.is_legacy_completed_session_state(estado)
                and not data.get("enviado_em")
            ):
                data["estado"] = COMPLETED_SESSION_STATE
                data["atualizado_em"] = datetime.now().isoformat(timespec="seconds")
                try:
                    with path.open("w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                except OSError:
                    pass
                continue

            self.remove_session_file(path)

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
        if (
            not isinstance(data, dict)
            or data.get("enviado_em")
            or not self.is_completed_session_state(data.get("estado"))
        ):
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

    def send_pending_session(self, file_name: str) -> bool:
        loaded = self.load_pending_session_file(file_name)
        if loaded is None:
            self.last_send_error = "Não foi possível abrir a medição."
            return False

        path, data = loaded
        measurements = data.get("medicoes")
        if not isinstance(measurements, list) or not measurements:
            self.last_send_error = "A sessão não contém medições válidas."
            return False

        sent_at = datetime.now().isoformat(timespec="seconds")
        sent_data = deepcopy(data)
        sent_data["estado"] = "enviado"
        sent_data["atualizado_em"] = sent_at
        sent_data["enviado_em"] = sent_at
        exported_data = self.session_data_for_export(sent_data)

        self.last_send_error = ""
        SENT_DIR.mkdir(parents=True, exist_ok=True)
        try:
            with (SENT_DIR / path.name).open("w", encoding="utf-8") as file:
                json.dump(
                    exported_data,
                    file,
                    ensure_ascii=False,
                    indent=2,
                )

            path.unlink()
        except OSError:
            self.last_send_error = (
                "Não foi possível guardar o ficheiro em enviados ou apagar a sessão."
            )
            return False

        return True

    def simulate_send_pending_session(self, file_name: str) -> bool:
        return self.send_pending_session(file_name)

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

    def send_pending_measurement(
        self,
        file_name: str,
        measurement_index: int,
    ) -> bool:
        loaded = self.load_pending_session_file(file_name)
        if loaded is None:
            self.last_send_error = "Não foi possível abrir a medição."
            return False

        _, data = loaded
        measurements = data.get("medicoes")
        if not isinstance(measurements, list):
            self.last_send_error = "A sessão não contém medições válidas."
            return False

        if measurement_index < 0 or measurement_index >= len(measurements):
            self.last_send_error = "A medição selecionada não existe."
            return False

        return self.send_pending_session(file_name)

    def simulate_send_pending_measurement(
        self,
        file_name: str,
        measurement_index: int,
    ) -> bool:
        return self.send_pending_measurement(file_name, measurement_index)

    def simulate_send_pending_sessions(self) -> int:
        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        sent_count = 0
        for path in SESSIONS_DIR.glob("*.json"):
            loaded = self.load_pending_session_file(path.name)
            if loaded is None:
                continue
            _, data = loaded
            measurements = data.get("medicoes")
            if not isinstance(measurements, list) or not measurements:
                continue

            if self.send_pending_session(path.name):
                sent_count += len(measurements)
                continue
            return sent_count
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

            if not self.is_completed_session_state(data.get("estado")):
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

    def load_exported_sessions(self) -> list[dict[str, Any]]:
        SENT_DIR.mkdir(parents=True, exist_ok=True)
        sessions: list[dict[str, Any]] = []
        for path in SENT_DIR.glob("*.json"):
            try:
                with path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
            except (OSError, json.JSONDecodeError):
                continue

            if not isinstance(data, dict):
                continue

            data["_file_name"] = path.name
            sessions.append(data)

        return sorted(
            sessions,
            key=lambda item: str(
                item.get("enviado_em")
                or item.get("atualizado_em")
                or item.get("criado_em")
                or item.get("session_id")
                or ""
            ),
            reverse=True,
        )


    @staticmethod
    def safe_pdf_file_component(value: Any) -> str:
        text = str(value or "").strip()
        text = re.sub(r"[^A-Za-z0-9._-]+", "_", text)
        text = text.strip("._-")
        return text or "molde"

    @staticmethod
    def measurement_export_identity(measurement: dict[str, Any]) -> tuple[str, str, str, str]:
        return (
            str(measurement.get("session_id") or measurement.get("_source_file") or ""),
            str(measurement.get("lado") or "").casefold(),
            str(measurement.get("circuito") or ""),
            str(measurement.get("medido_em") or ""),
        )

    def measurement_payloads_for_rows(
        self, rows: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        payloads: list[dict[str, Any]] = []
        loaded_by_file: dict[str, dict[str, Any]] = {}
        seen_refs: set[tuple[str, int]] = set()
        inherited_fields = (
            "session_id",
            "operador",
            "molde",
            "diametro_mm",
            "pressao_entrada_bar",
        )

        for row in rows:
            file_name = str(row.get("_file_name") or "")
            try:
                measurement_index = int(row.get("_measurement_index"))
            except (TypeError, ValueError):
                continue
            ref = (file_name, measurement_index)
            if not file_name or ref in seen_refs:
                continue
            seen_refs.add(ref)

            session = loaded_by_file.get(file_name)
            if session is None:
                loaded = self.load_pending_session_file(file_name)
                if loaded is None:
                    continue
                _, session = loaded
                loaded_by_file[file_name] = session

            measurements = session.get("medicoes")
            if not isinstance(measurements, list):
                continue
            if measurement_index < 0 or measurement_index >= len(measurements):
                continue
            source = measurements[measurement_index]
            if not isinstance(source, dict):
                continue

            payload = deepcopy(source)

            for field in inherited_fields:
                session_value = session.get(field)

                if session_value not in (None, ""):
                    payload[field] = session_value
                elif payload.get(field) in (None, ""):
                    payload[field] = session_value
                    
            if payload.get("lado") in (None, ""):
                payload["lado"] = session.get("lado_molde")
            payload["_source_file"] = file_name
            payloads.append(payload)

        return payloads

    @staticmethod
    def recompute_session_side_totals(data: dict[str, Any]) -> None:
        measurements = data.get("medicoes")
        if not isinstance(measurements, list):
            data["circuitos_por_lado"] = {}
            data["circuitos_inicio_por_lado"] = {}
            return

        counts: dict[str, int] = {}
        starts: dict[str, int] = {}
        for measurement in measurements:
            if not isinstance(measurement, dict):
                continue
            side = str(measurement.get("lado") or "").strip()
            if not side:
                continue
            counts[side] = counts.get(side, 0) + 1
            try:
                circuit = int(measurement.get("circuito"))
            except (TypeError, ValueError):
                continue
            starts[side] = min(starts.get(side, circuit), circuit)

        data["circuitos_por_lado"] = counts
        data["circuitos_inicio_por_lado"] = starts
        if counts:
            data["lado_molde"] = next(iter(counts))

    def unique_sent_json_path(self, preferred_name: str, exported_at: str) -> Path:
        preferred = SENT_DIR / Path(preferred_name).name
        if not preferred.exists():
            return preferred
        timestamp = exported_at.replace("-", "").replace(":", "").replace("T", "_")
        base = preferred.stem
        candidate = SENT_DIR / f"{base}__pdf_{timestamp}{preferred.suffix}"
        counter = 2
        while candidate.exists():
            candidate = SENT_DIR / f"{base}__pdf_{timestamp}_{counter}{preferred.suffix}"
            counter += 1
        return candidate

    def archive_pdf_export_rows(
        self,
        rows: list[dict[str, Any]],
        *,
        pdf_file_name: str,
        exported_at: str,
    ) -> int:
        refs_by_file: dict[str, set[int]] = {}
        for row in rows:
            file_name = str(row.get("_file_name") or "")
            try:
                index = int(row.get("_measurement_index"))
            except (TypeError, ValueError):
                continue
            refs_by_file.setdefault(file_name, set()).add(index)

        plans: list[tuple[Path, Path, dict[str, Any] | None, dict[str, Any]]] = []
        for file_name, selected_indices in refs_by_file.items():
            loaded = self.load_pending_session_file(file_name)
            if loaded is None:
                raise OSError(f"Não foi possível abrir {file_name}.")
            source_path, data = loaded
            measurements = data.get("medicoes")
            if not isinstance(measurements, list):
                raise OSError(f"A sessão {file_name} não contém medições válidas.")

            selected = [
                deepcopy(measurement)
                for index, measurement in enumerate(measurements)
                if index in selected_indices and isinstance(measurement, dict)
            ]
            remaining = [
                deepcopy(measurement)
                for index, measurement in enumerate(measurements)
                if index not in selected_indices
            ]
            if not selected:
                continue

            exported_data = deepcopy(data)
            exported_data["medicoes"] = selected
            exported_data["estado"] = "exportado_pdf"
            exported_data["atualizado_em"] = exported_at
            exported_data["enviado_em"] = exported_at
            exported_data["pdf_ficheiro"] = pdf_file_name
            exported_data = self.session_data_for_export(exported_data)
            sent_path = self.unique_sent_json_path(source_path.name, exported_at)

            pending_data: dict[str, Any] | None = None
            if remaining:
                pending_data = deepcopy(data)
                pending_data["medicoes"] = remaining
                pending_data["atualizado_em"] = exported_at
                self.recompute_session_side_totals(pending_data)

            plans.append((source_path, sent_path, pending_data, exported_data))

        if not plans:
            return 0

        SENT_DIR.mkdir(parents=True, exist_ok=True)
        temp_files: list[Path] = []
        try:
            prepared: list[tuple[Path, Path, Path, Path | None, dict[str, Any] | None]] = []
            for source_path, sent_path, pending_data, exported_data in plans:
                sent_temp = sent_path.with_name(f".{sent_path.name}.{uuid4().hex}.tmp")
                with sent_temp.open("w", encoding="utf-8") as file:
                    json.dump(exported_data, file, ensure_ascii=False, indent=2)
                temp_files.append(sent_temp)

                pending_temp: Path | None = None
                if pending_data is not None:
                    pending_temp = source_path.with_name(
                        f".{source_path.name}.{uuid4().hex}.tmp"
                    )
                    with pending_temp.open("w", encoding="utf-8") as file:
                        json.dump(pending_data, file, ensure_ascii=False, indent=2)
                    temp_files.append(pending_temp)
                prepared.append(
                    (source_path, sent_path, sent_temp, pending_temp, pending_data)
                )

            for source_path, sent_path, sent_temp, pending_temp, pending_data in prepared:
                os.replace(sent_temp, sent_path)
                temp_files.remove(sent_temp)
                if pending_data is None:
                    source_path.unlink()
                elif pending_temp is not None:
                    os.replace(pending_temp, source_path)
                    temp_files.remove(pending_temp)
        finally:
            for temp_path in temp_files:
                try:
                    temp_path.unlink()
                except OSError:
                    pass

        return sum(len(indices) for indices in refs_by_file.values())

    def exported_sides_for_mold(self, mold: str) -> set[str]:
        PDF_EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

        target_mold = str(mold or "").strip().casefold()
        sides: set[str] = set()

        if not target_mold:
            return sides

        for manifest_path in PDF_EXPORTS_DIR.glob("Registo_Caudais_*.json"):
            try:
                with manifest_path.open("r", encoding="utf-8") as file:
                    manifest = json.load(file)
            except (OSError, json.JSONDecodeError):
                continue

            if not isinstance(manifest, dict):
                continue

            manifest_mold = str(manifest.get("molde") or "").strip().casefold()
            if manifest_mold != target_mold:
                continue

            measurements = manifest.get("medicoes")
            if not isinstance(measurements, list):
                continue

            for measurement in measurements:
                if not isinstance(measurement, dict):
                    continue

                side = str(measurement.get("lado") or "").strip()
                if side:
                    sides.add(side.casefold())

        return sides

    def auto_export_completed_sessions_on_boot(self) -> None:
        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

        grouped_by_mold: dict[str, dict[str, Any]] = {}

        for path in SESSIONS_DIR.glob("*.json"):
            loaded = self.load_pending_session_file(path.name)
            if loaded is None:
                continue

            _, session = loaded

            estado = str(session.get("estado") or "").strip().casefold()
            if estado not in {"concluida", "concluido", "concluído"}:
                continue

            measurements = session.get("medicoes")
            if not isinstance(measurements, list) or not measurements:
                continue

            mold = str(session.get("molde") or "").strip()
            if not mold:
                continue

            mold_key = mold.casefold()

            group = grouped_by_mold.setdefault(
                mold_key,
                {
                    "molde": mold,
                    "rows": [],
                    "pending_sides": set(),
                },
            )

            for measurement_index, measurement in enumerate(measurements):
                if not isinstance(measurement, dict):
                    continue

                side = str(
                    measurement.get("lado")
                    or session.get("lado_molde")
                    or ""
                ).strip()

                if not side:
                    continue

                side_key = side.casefold()

                group["pending_sides"].add(side_key)
                group["rows"].append(
                    {
                        "_file_name": path.name,
                        "_measurement_index": measurement_index,
                        "_side_key": side_key,
                    }
                )

        exported_molds = 0
        exported_measurements = 0
        errors: list[str] = []

        for group in grouped_by_mold.values():
            mold = str(group["molde"])
            rows = list(group["rows"])
            pending_sides = set(group["pending_sides"])
            existing_sides = self.exported_sides_for_mold(mold)

            if not rows or not pending_sides:
                continue

            has_multiple_pending_sides = len(pending_sides) >= 2
            adds_new_side_to_existing_pdf = bool(existing_sides) and bool(
                pending_sides - existing_sides
            )

            if not has_multiple_pending_sides and not adds_new_side_to_existing_pdf:
                continue

            if existing_sides:
                rows_to_export = [
                    row
                    for row in rows
                    if row.get("_side_key") not in existing_sides
                ]
            else:
                rows_to_export = rows

            if not rows_to_export:
                continue

            success, message, _record = self.export_pending_measurement_rows_to_pdf(
                rows_to_export
            )

            if success:
                exported_molds += 1
                exported_measurements += len(rows_to_export)
            else:
                errors.append(message)

        if exported_molds:
            self.status_text = (
                f"Exportação automática concluída: "
                f"{exported_molds} molde(s), "
                f"{exported_measurements} medição(ões)."
            )
        elif errors:
            self.status_text = "Erro na exportação automática: " + errors[0]

        if getattr(self, "screen", "") == "LOGIN":
            self.show_login()

    def export_pending_measurement_rows_to_pdf(
        self, rows: list[dict[str, Any]]
    ) -> tuple[bool, str, dict[str, Any] | None]:
        if not rows:
            return False, "Selecione pelo menos uma medição.", None

        payloads = self.measurement_payloads_for_rows(rows)
        if not payloads:
            return False, "Não foi possível ler as medições selecionadas.", None

        mold_values = {
            str(item.get("molde") or "").strip()
            for item in payloads
            if str(item.get("molde") or "").strip()
        }
        normalized_molds = {value.casefold() for value in mold_values}
        if len(normalized_molds) != 1:
            return (
                False,
                "A exportação só é permitida para um único molde. "
                "Selecione um lado ou vários lados do mesmo molde.",
                None,
            )
        mold = sorted(mold_values, key=str.casefold)[0]

        PDF_EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
        safe_mold = self.safe_pdf_file_component(mold)
        pdf_path = PDF_EXPORTS_DIR / f"Registo_Caudais_{safe_mold}.pdf"
        manifest_path = PDF_EXPORTS_DIR / f"Registo_Caudais_{safe_mold}.json"
        exported_at = datetime.now().isoformat(timespec="seconds")

        manifest: dict[str, Any] = {}
        if manifest_path.exists():
            try:
                with manifest_path.open("r", encoding="utf-8") as file:
                    loaded_manifest = json.load(file)
                if isinstance(loaded_manifest, dict):
                    manifest = loaded_manifest
            except (OSError, json.JSONDecodeError):
                manifest = {}

        previous_measurements = manifest.get("medicoes")
        if not isinstance(previous_measurements, list):
            previous_measurements = []

        merged_by_identity: dict[tuple[str, str, str, str], dict[str, Any]] = {}
        for measurement in [*previous_measurements, *payloads]:
            if not isinstance(measurement, dict):
                continue
            merged_by_identity[self.measurement_export_identity(measurement)] = deepcopy(
                measurement
            )
        merged_measurements = sorted(
            merged_by_identity.values(),
            key=lambda item: (
                str(item.get("lado") or "").casefold(),
                int(item.get("circuito") or 0),
                str(item.get("medido_em") or ""),
            ),
        )

        measurements_for_json = deepcopy(merged_measurements)

        for measurement in measurements_for_json:
            if not isinstance(measurement, dict):
                continue

            if "diametro_mm" in measurement:
                measurement["diametro_mm"] = self.export_diameter_value(
                    measurement.get("diametro_mm")
                )

        operators = sorted(
            {
                str(item.get("operador") or "").strip()
                for item in merged_measurements
                if str(item.get("operador") or "").strip()
            },
            key=str.casefold,
        )
        new_manifest = {
            "molde": mold,
            "ficheiro": pdf_path.name,
            "criado_em": manifest.get("criado_em") or exported_at,
            "atualizado_em": exported_at,
            "operadores": operators,
            "medicoes": measurements_for_json,
        }

        temp_pdf = pdf_path.with_name(f".{pdf_path.name}.{uuid4().hex}.tmp.pdf")
        temp_manifest = manifest_path.with_name(
            f".{manifest_path.name}.{uuid4().hex}.tmp"
        )
        try:
            generate_flow_report(
                temp_pdf,
                mold=mold,
                measurements=merged_measurements,
                exported_at=exported_at,
            )
            with temp_manifest.open("w", encoding="utf-8") as file:
                json.dump(new_manifest, file, ensure_ascii=False, indent=2)

            archived_count = self.archive_pdf_export_rows(
                rows,
                pdf_file_name=pdf_path.name,
                exported_at=exported_at,
            )
            if archived_count <= 0:
                raise OSError("Nenhuma medição foi arquivada.")

            os.replace(temp_pdf, pdf_path)
            os.replace(temp_manifest, manifest_path)

            # Envio automático opcional.
            # Só inicia se estiver ativo em data/email_config.json e se existirem
            # pares PDF/JSON exportados na pasta data/pdf_exportados.
            send_automatic_exports_if_configured(
                pdf_path=pdf_path,
                json_path=manifest_path,
                molde=mold,
            )
        except (OSError, ValueError) as exc:
            for temp_path in (temp_pdf, temp_manifest):
                try:
                    temp_path.unlink()
                except OSError:
                    pass
            return False, f"Não foi possível exportar o PDF: {exc}", None

        record = {
            "data": exported_at.replace("T", " ")[:16],
            "operador": ", ".join(operators) or "-",
            "molde": mold,
            "ficheiro": pdf_path.name,
            "tamanho_bytes": pdf_path.stat().st_size,
            "medicoes": len(merged_measurements),
        }
        return True, f"PDF exportado: {pdf_path.name}", record

    def load_exported_pdf_records(self) -> list[dict[str, Any]]:
        PDF_EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
        records: list[dict[str, Any]] = []
        for manifest_path in PDF_EXPORTS_DIR.glob("Registo_Caudais_*.json"):
            try:
                with manifest_path.open("r", encoding="utf-8") as file:
                    manifest = json.load(file)
            except (OSError, json.JSONDecodeError):
                continue
            if not isinstance(manifest, dict):
                continue
            if manifest.get(EMAIL_SENT_FIELD):
                continue

            pdf_name = str(manifest.get("ficheiro") or "")
            pdf_path = PDF_EXPORTS_DIR / Path(pdf_name).name
            if not pdf_name or not pdf_path.exists():
                continue
            operators = manifest.get("operadores")
            if not isinstance(operators, list):
                operators = []
            measurements = manifest.get("medicoes")
            records.append(
                {
                    "data": str(
                        manifest.get("atualizado_em")
                        or manifest.get("criado_em")
                        or "-"
                    ).replace("T", " ")[:16],
                    "operador": ", ".join(str(item) for item in operators) or "-",
                    "molde": str(manifest.get("molde") or "-"),
                    "ficheiro": pdf_path.name,
                    "json_ficheiro": manifest_path.name,
                    "tamanho_bytes": pdf_path.stat().st_size,
                    "medicoes": len(measurements) if isinstance(measurements, list) else 0,
                }
            )

        return sorted(records, key=lambda item: item["data"], reverse=True)

    def exported_pdf_record_paths(
        self,
        record: dict[str, Any],
    ) -> tuple[Path, Path] | None:
        pdf_name = Path(str(record.get("ficheiro") or "")).name
        if not pdf_name or Path(pdf_name).suffix.lower() != ".pdf":
            return None

        json_name = Path(str(record.get("json_ficheiro") or "")).name
        if not json_name:
            json_name = f"{Path(pdf_name).stem}.json"
        if Path(json_name).suffix.lower() != ".json":
            return None

        return PDF_EXPORTS_DIR / pdf_name, PDF_EXPORTS_DIR / json_name

    def exported_pdf_record_attachments(
        self,
        record: dict[str, Any],
    ) -> tuple[list[Path], str]:
        paths = self.exported_pdf_record_paths(record)
        if paths is None:
            return [], "Registo invalido."

        pdf_path, manifest_path = paths
        missing = [path.name for path in (pdf_path, manifest_path) if not path.exists()]
        if missing:
            return [], f"Ficheiro em falta: {', '.join(missing)}"

        return [pdf_path, manifest_path], ""

    def delete_exported_pdf_record(self, record: dict[str, Any]) -> tuple[bool, str]:
        paths = self.exported_pdf_record_paths(record)
        if paths is None:
            return False, "Registo invalido."

        pdf_path, manifest_path = paths
        removed: list[str] = []
        errors: list[str] = []
        for path in (pdf_path, manifest_path):
            if not path.exists():
                continue
            try:
                path.unlink()
            except OSError as exc:
                errors.append(f"{path.name}: {exc}")
            else:
                removed.append(path.name)

        if errors:
            return False, "Nao foi possivel apagar: " + "; ".join(errors)
        if not removed:
            return False, "Os ficheiros ja nao existem."
        return True, "Apagado: " + ", ".join(removed)

    @staticmethod
    def format_file_size(size_bytes: Any) -> str:
        try:
            size = float(size_bytes)
        except (TypeError, ValueError):
            return "-"
        units = ("B", "KB", "MB", "GB")
        unit = units[0]
        for unit in units:
            if size < 1024 or unit == units[-1]:
                break
            size /= 1024
        return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} B"

    def pending_sessions_count(self) -> int:
        return len(self.load_pending_sessions())

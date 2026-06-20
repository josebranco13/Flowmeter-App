from __future__ import annotations

import math
import random
from dataclasses import asdict
from datetime import datetime
from statistics import mean

from .models import MeasurementRecord


class MeasurementMixin:
    def measured_count_for_side(self, side: str) -> int:
        if self.session is None:
            return 0
        return sum(1 for item in self.session.medicoes if item["lado"] == side)

    def measurements_for_side(self, side: str) -> list[dict[str, object]]:
        if self.session is None:
            return []
        return [item for item in self.session.medicoes if item["lado"] == side]

    def expected_count_for_side(self, side: str) -> int:
        if self.session is None or not side:
            return 0
        return int(self.session.circuitos_por_lado.get(side, 0))

    def expected_count_for_current_side(self) -> int:
        if self.session is None:
            return 0
        return self.expected_count_for_side(self.session.lado_molde)

    def side_measurement_complete(self, side: str) -> bool:
        expected = self.expected_count_for_side(side)
        return expected > 0 and self.measured_count_for_side(side) >= expected

    def measurement_record_for_circuit(
        self,
        side: str,
        circuit: int,
    ) -> dict[str, object] | None:
        if self.session is None or not side or not circuit:
            return None

        for item in self.session.medicoes:
            try:
                item_circuit = int(item.get("circuito", 0))
            except (TypeError, ValueError):
                continue
            if item.get("lado") == side and item_circuit == circuit:
                return item
        return None

    def build_side_options(self) -> list[str]:
        if self.session is None:
            return []
        options = []
        for side in self.mold_side_options:
            expected = self.session.circuitos_por_lado.get(side, 0)
            measured = self.measured_count_for_side(side)
            if expected > measured:
                options.append(side)
        if self.session.medicoes:
            options.append("Concluir sessão")
        return options

    def start_measurement(self, selected_side_option: str) -> None:
        assert self.session is not None
        side = selected_side_option.replace("Lado ", "")
        self.current_side = side
        if self.side_measurement_complete(side):
            self.current_circuit = self.expected_count_for_side(side)
            self.show_circuit_results()
            return
        self.current_circuit = self.measured_count_for_side(side) + 1
        self.samples = []
        self.measurement_running = False
        self.status_text = ""
        self.show_circuit_start()

    def prepare_next_circuit_measurement(self) -> None:
        assert self.session is not None
        self.current_side = self.session.lado_molde or self.current_side
        if self.side_measurement_complete(self.current_side):
            self.current_circuit = self.expected_count_for_side(self.current_side)
            self.samples = []
            self.measurement_running = False
            self.status_text = ""
            self.show_circuit_results()
            return
        self.current_circuit = self.measured_count_for_side(self.current_side) + 1
        self.samples = []
        self.measurement_running = False
        self.status_text = ""
        self.show_circuit_start()

    def start_current_flow_measurement(self) -> None:
        if self.session is None:
            return
        if not self.current_side:
            self.current_side = self.session.lado_molde
        if not self.current_circuit:
            self.current_circuit = self.measured_count_for_side(self.current_side) + 1

        expected = self.expected_count_for_side(self.current_side)
        if expected and self.current_circuit > expected:
            measured = self.measured_count_for_side(self.current_side)
            if measured >= expected:
                self.current_circuit = expected
                self.show_circuit_results()
                return
            self.current_circuit = measured + 1

        existing_record = self.measurement_record_for_circuit(
            self.current_side,
            self.current_circuit,
        )
        if existing_record is not None:
            self.last_measurement_record = existing_record
            if self.side_measurement_complete(self.current_side):
                self.show_circuit_results()
            else:
                self.prepare_next_circuit_measurement()
            return

        if self.side_measurement_complete(self.current_side):
            self.current_circuit = expected
            self.show_circuit_results()
            return

        self.samples = []
        self.measurement_running = True
        self.status_text = ""
        self.show_measurement()

    def stop_current_measurement(self) -> None:
        self.measurement_running = False

    def restart_current_measurement(self) -> None:
        self.samples = []
        self.measurement_running = True
        self.show_measurement()

    def simulated_flow_sample(self) -> float:
        assert self.session is not None
        # Simulação simples. Quando houver sensor real, substituir este método
        # por leitura de impulsos/GPIO ou comunicação com microcontrolador.
        diameter_factor = (self.session.diametro_mm / 10) ** 2
        pressure_factor = math.sqrt(max(self.session.pressao_entrada_bar, 0.1))
        base_flow = 3.5 * diameter_factor * pressure_factor
        noise = random.gauss(0, base_flow * 0.06)
        drift = random.uniform(-0.15, 0.15)
        return round(max(0.0, base_flow + noise + drift), 2)

    def update_measurement_values(self) -> None:
        if self.screen != "MEASURE" or not self.measurement_running:
            return

        sample = self.simulated_flow_sample()
        self.samples.append(sample)

        current = sample
        minimum = min(self.samples)
        average = mean(self.samples)
        maximum = max(self.samples)

        values = {
            "current": self.format_flow_display(current),
            "min": self.format_flow_display(minimum),
            "avg": self.format_flow_display(average),
            "max": self.format_flow_display(maximum),
            "samples": str(len(self.samples)),
        }
        for key, value in values.items():
            label = self.measure_labels.get(key)
            if label is not None:
                label.configure(text=value)

        if self.measurement_running:
            self.after(1000, self.update_measurement_values)

    def finish_current_measurement(self) -> None:
        if self.session is None:
            return
        self.measurement_running = False
        if not self.current_side:
            self.current_side = self.session.lado_molde
        if not self.current_circuit:
            self.current_circuit = self.measured_count_for_side(self.current_side) + 1

        expected = self.expected_count_for_side(self.current_side)
        if expected and self.current_circuit > expected:
            measured = self.measured_count_for_side(self.current_side)
            if measured >= expected:
                self.current_circuit = expected
                self.samples = []
                self.status_text = "Todos os circuitos pedidos ja foram medidos."
                self.show_circuit_results()
                return
            self.current_circuit = measured + 1

        if not self.samples:
            self.samples.append(self.simulated_flow_sample())

        record = MeasurementRecord(
            session_id=self.session.session_id,
            operador=self.session.operador,
            molde=self.session.molde,
            diametro_mm=self.session.diametro_mm,
            pressao_entrada_bar=self.session.pressao_entrada_bar,
            lado=self.current_side,
            circuito=self.current_circuit,
            caudal_min_l_min=round(min(self.samples), 2),
            caudal_medio_l_min=round(mean(self.samples), 2),
            caudal_max_l_min=round(max(self.samples), 2),
            amostras=len(self.samples),
            medido_em=datetime.now().isoformat(timespec="seconds"),
        )
        record_data = asdict(record)
        existing_index = None
        for index, item in enumerate(self.session.medicoes):
            try:
                item_circuit = int(item.get("circuito", 0))
            except (TypeError, ValueError):
                continue
            if item.get("lado") == self.current_side and item_circuit == self.current_circuit:
                existing_index = index
                break

        if existing_index is None:
            self.session.medicoes.append(record_data)
        else:
            self.session.medicoes[existing_index] = record_data
        self.last_measurement_record = record_data
        self.append_measurement_csv(record)
        self.save_session()

        self.samples = []
        self.status_text = ""
        self.selected_index = 0
        self.show_measurement_result()

    def highlight_current_measurement(self) -> None:
        if self.session is None or self.last_measurement_record is None:
            return

        for item in self.session.medicoes:
            if (
                item.get("lado") == self.current_side
                and item.get("circuito") == self.current_circuit
            ):
                item["destacado"] = not bool(item.get("destacado"))
                self.last_measurement_record = item
                break

        self.selected_index = 1
        self.save_session()
        self.show_measurement_result()

    def advance_after_measurement_result(self) -> None:
        if self.session is None:
            return

        measured = self.measured_count_for_side(self.current_side)
        expected = self.expected_count_for_side(self.current_side)
        if measured < expected:
            self.prepare_next_circuit_measurement()
            return

        self.selected_result_index = 0
        self.result_editing = False
        self.input_value = ""
        self.show_circuit_results()

    def selected_result_record(self) -> dict[str, object] | None:
        if self.session is None or not self.current_side:
            return None

        records = sorted(self.measurements_for_side(self.current_side), key=lambda item: item["circuito"])
        if not records:
            return None

        self.selected_result_index = min(self.selected_result_index, len(records) - 1)
        return records[self.selected_result_index]

    def result_edit_display_value(self) -> str:
        return self.input_value.replace(".", ",")

    def refresh_result_edit_display(self) -> None:
        if not self.update_field_value("selected_result_value", self.result_edit_display_value()):
            self.show_circuit_results()

    def edit_selected_result(self) -> None:
        if self.selected_result_record() is None:
            return

        self.result_editing = True
        self.input_value = ""
        self.status_text = ""
        self.show_circuit_results()
        self.focus_set()

    def save_selected_result_edit(self) -> bool:
        if not self.result_editing:
            return True

        text = self.input_value.strip().replace(",", ".")
        try:
            value = float(text)
        except ValueError:
            self.status_text = "Indique um valor de caudal valido."
            self.show_circuit_results()
            self.focus_set()
            return False

        if value < 0:
            self.status_text = "O caudal nao pode ser negativo."
            self.show_circuit_results()
            self.focus_set()
            return False

        record = self.selected_result_record()
        if record is None:
            return False

        value = round(value, 2)
        record["caudal_medio_l_min"] = value
        if (
            self.last_measurement_record is not None
            and self.last_measurement_record.get("lado") == record.get("lado")
            and self.last_measurement_record.get("circuito") == record.get("circuito")
        ):
            self.last_measurement_record = record

        self.result_editing = False
        self.input_value = ""
        self.status_text = ""
        self.save_session()
        self.show_circuit_results()
        return True

    def remeasure_current_circuit(self) -> None:
        if self.session is None or not self.current_side or not self.current_circuit:
            return
        self.session.medicoes = [
            item
            for item in self.session.medicoes
            if not (item["lado"] == self.current_side and item["circuito"] == self.current_circuit)
        ]
        self.save_session()
        self.start_current_flow_measurement()

    def remeasure_selected_result(self) -> None:
        if self.session is None or not self.current_side:
            return
        self.result_editing = False
        self.input_value = ""
        records = sorted(self.measurements_for_side(self.current_side), key=lambda item: item["circuito"])
        if not records:
            return
        self.selected_result_index = min(self.selected_result_index, len(records) - 1)
        circuit = int(records[self.selected_result_index]["circuito"])
        self.session.medicoes = [
            item
            for item in self.session.medicoes
            if not (item["lado"] == self.current_side and item["circuito"] == circuit)
        ]
        self.current_circuit = circuit
        self.save_session()
        self.start_current_flow_measurement()

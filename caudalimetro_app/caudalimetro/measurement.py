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

    def build_side_options(self) -> list[str]:
        if self.session is None:
            return []
        options = []
        for side in ("A", "B"):
            expected = self.session.circuitos_por_lado.get(side, 0)
            measured = self.measured_count_for_side(side)
            if expected > measured:
                options.append(f"Lado {side}")
        if self.session.medicoes:
            options.append("Concluir sessão")
        return options

    def start_measurement(self, selected_side_option: str) -> None:
        assert self.session is not None
        side = selected_side_option.replace("Lado ", "")
        self.current_side = side
        self.current_circuit = self.measured_count_for_side(side) + 1
        self.samples = []
        self.status_text = ""
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
        if self.screen != "MEASURE":
            return

        sample = self.simulated_flow_sample()
        self.samples.append(sample)

        current = sample
        minimum = min(self.samples)
        average = mean(self.samples)
        maximum = max(self.samples)

        values = {
            "current": f"{current:.2f} L/min",
            "min": f"{minimum:.2f} L/min",
            "avg": f"{average:.2f} L/min",
            "max": f"{maximum:.2f} L/min",
            "samples": str(len(self.samples)),
        }
        for key, value in values.items():
            label = self.measure_labels.get(key)
            if label is not None:
                label.configure(text=value)

        self.after(1000, self.update_measurement_values)

    def finish_current_measurement(self) -> None:
        if self.session is None:
            return
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
        self.session.medicoes.append(asdict(record))
        self.append_measurement_csv(record)
        self.save_session()

        self.status_text = (
            f"Lado {self.current_side}, circuito {self.current_circuit} guardado."
        )
        self.samples = []

        expected_side_total = self.session.circuitos_por_lado.get(self.current_side, 0)
        if self.measured_count_for_side(self.current_side) < expected_side_total:
            self.start_measurement(f"Lado {self.current_side}")
            return

        if self.build_side_options() == ["Concluir sessão"]:
            self.selected_index = 0
            self.show_summary()
        else:
            self.show_side_selection()

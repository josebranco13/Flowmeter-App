from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from time import monotonic_ns

try:
    from gpiozero import DigitalInputDevice
except ImportError:
    DigitalInputDevice = None


class FlowSensorError(RuntimeError):
    """Erro relacionado com a inicialização ou utilização do sensor."""


@dataclass(frozen=True, slots=True)
class FlowReading:

    flow_l_min: float
    instantaneous_flow_l_min: float
    total_litres: float
    total_pulses: int
    last_pulse_age_seconds: float
    is_flowing: bool


class YFS201Sensor:

    def __init__(
        self,
        gpio_pin: int = 17,
        pulses_per_litre: float = 450.0,
        zero_flow_timeout: float = 0.5,
        smoothing_factor: float = 0.30,
        minimum_pulse_interval: float = 0.002,
        active_high: bool = True,
    ) -> None:
    
        if DigitalInputDevice is None:
            raise FlowSensorError(
                "A biblioteca gpiozero não está instalada. "
                "No Raspberry Pi, executa: "
                "sudo apt install python3-gpiozero"
            )

        if gpio_pin < 0:
            raise ValueError("O número do GPIO não pode ser negativo.")

        if pulses_per_litre <= 0:
            raise ValueError(
                "O número de impulsos por litro deve ser superior a zero."
            )

        if zero_flow_timeout <= 0:
            raise ValueError(
                "O tempo para considerar caudal zero deve ser superior a zero."
            )

        if not 0 < smoothing_factor <= 1:
            raise ValueError(
                "O fator de suavização deve estar entre 0 e 1."
            )

        if minimum_pulse_interval < 0:
            raise ValueError(
                "O intervalo mínimo entre impulsos não pode ser negativo."
            )

        self.gpio_pin = gpio_pin
        self.pulses_per_litre = pulses_per_litre
        self.zero_flow_timeout = zero_flow_timeout
        self.smoothing_factor = smoothing_factor
        self.minimum_pulse_interval = minimum_pulse_interval
        self.active_high = active_high

        self._lock = Lock()

        self._last_pulse_time_ns: int | None = None
        self._total_pulses = 0

        self._instantaneous_flow_l_min = 0.0
        self._filtered_flow_l_min = 0.0

        self._has_valid_flow_reading = False
        self._closed = False

        try:
            self._input = DigitalInputDevice(
                pin=self.gpio_pin,
                pull_up=None,
                active_state=self.active_high,
                bounce_time=None,
            )
        except Exception as exc:
            raise FlowSensorError(
                f"Não foi possível configurar o GPIO {self.gpio_pin}: {exc}"
            ) from exc

        self._input.when_activated = self._pulse_received

    def _pulse_received(self) -> None:

        current_time_ns = monotonic_ns()

        with self._lock:
            if self._closed:
                return

            if self._last_pulse_time_ns is None:
                self._total_pulses = 1
                self._last_pulse_time_ns = current_time_ns
                return

            pulse_period_ns = current_time_ns - self._last_pulse_time_ns
            pulse_period_seconds = pulse_period_ns / 1_000_000_000

            # Rejeitar transições demasiado rápidas que provavelmente
            # resultam de ruído elétrico.
            if pulse_period_seconds < self.minimum_pulse_interval:
                return

            self._last_pulse_time_ns = current_time_ns
            self._total_pulses += 1

            instantaneous_flow = (
                60.0
                / (
                    self.pulses_per_litre
                    * pulse_period_seconds
                )
            )

            self._instantaneous_flow_l_min = instantaneous_flow

            if not self._has_valid_flow_reading:
                self._filtered_flow_l_min = instantaneous_flow
                self._has_valid_flow_reading = True
            else:
                alpha = self.smoothing_factor

                self._filtered_flow_l_min = (
                    alpha * instantaneous_flow
                    + (1.0 - alpha) * self._filtered_flow_l_min
                )

    def get_reading(self) -> FlowReading:

        current_time_ns = monotonic_ns()

        with self._lock:
            last_pulse_time_ns = self._last_pulse_time_ns
            total_pulses = self._total_pulses
            instantaneous_flow = self._instantaneous_flow_l_min
            filtered_flow = self._filtered_flow_l_min
            has_valid_reading = self._has_valid_flow_reading

        if last_pulse_time_ns is None:
            return FlowReading(
                flow_l_min=0.0,
                instantaneous_flow_l_min=0.0,
                total_litres=0.0,
                total_pulses=0,
                last_pulse_age_seconds=float("inf"),
                is_flowing=False,
            )

        last_pulse_age_seconds = (
            current_time_ns - last_pulse_time_ns
        ) / 1_000_000_000

        is_flowing = (
            has_valid_reading
            and last_pulse_age_seconds < self.zero_flow_timeout
        )

        if not is_flowing:
            instantaneous_flow = 0.0
            filtered_flow = 0.0

        total_litres = total_pulses / self.pulses_per_litre

        return FlowReading(
            flow_l_min=round(filtered_flow, 3),
            instantaneous_flow_l_min=round(
                instantaneous_flow,
                3,
            ),
            total_litres=round(total_litres, 6),
            total_pulses=total_pulses,
            last_pulse_age_seconds=last_pulse_age_seconds,
            is_flowing=is_flowing,
        )

    def get_flow_l_min(self) -> float:

        return self.get_reading().flow_l_min

    def get_instantaneous_flow_l_min(self) -> float:

        return self.get_reading().instantaneous_flow_l_min

    def get_total_litres(self) -> float:

        return self.get_reading().total_litres

    def reset(self) -> None:

        with self._lock:
            self._last_pulse_time_ns = None
            self._total_pulses = 0
            self._instantaneous_flow_l_min = 0.0
            self._filtered_flow_l_min = 0.0
            self._has_valid_flow_reading = False

    def close(self) -> None:

        with self._lock:
            if self._closed:
                return

            self._closed = True

        self._input.when_activated = None
        self._input.close()

    def __enter__(self) -> YFS201Sensor:
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()
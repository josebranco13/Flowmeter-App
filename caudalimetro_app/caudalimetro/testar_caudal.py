from __future__ import annotations

import time
from threading import Lock

try:
    import RPi.GPIO as GPIO
except (ImportError, RuntimeError):
    GPIO = None

# --- Configuration ---
FLOW_SENSOR_PIN = 21
# Calibration factor for YF-S201 (Pulse frequency (Hz) / 7.5 = Q (L/min))
CALIBRATION_FACTOR = 7.5 

# Global variable to keep track of pulses
pulse_count = 0


class FlowMeterError(RuntimeError):
    """Raised when the flow meter cannot be used."""


class RPiGPIOFlowMeter:
    """Pulse counter for a YF-S201 style flow meter using RPi.GPIO."""

    def __init__(
        self,
        gpio_pin: int = FLOW_SENSOR_PIN,
        calibration_factor: float = CALIBRATION_FACTOR,
    ) -> None:
        if GPIO is None:
            raise FlowMeterError(
                "A biblioteca RPi.GPIO nao esta disponivel. "
                "Instala-a no Raspberry Pi antes de medir caudal."
            )
        if gpio_pin < 0:
            raise ValueError("O numero do GPIO nao pode ser negativo.")
        if calibration_factor <= 0:
            raise ValueError("O fator de calibracao deve ser superior a zero.")

        self.gpio_pin = gpio_pin
        self.calibration_factor = calibration_factor
        self._lock = Lock()
        self._pulse_count = 0
        self._last_read_count = 0
        self._last_read_time = time.monotonic()
        self._closed = False

        try:
            GPIO.setwarnings(False)
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.gpio_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.add_event_detect(
                self.gpio_pin,
                GPIO.FALLING,
                callback=self._count_pulse,
            )
        except Exception as exc:
            self.close()
            raise FlowMeterError(
                f"Nao foi possivel configurar o GPIO {self.gpio_pin}: {exc}"
            ) from exc

    def _count_pulse(self, _channel: int) -> None:
        with self._lock:
            if not self._closed:
                self._pulse_count += 1

    def reset(self) -> None:
        with self._lock:
            self._last_read_count = self._pulse_count
            self._last_read_time = time.monotonic()

    def read_pulse_sample(self) -> tuple[int, float]:
        current_time = time.monotonic()
        with self._lock:
            elapsed_seconds = current_time - self._last_read_time
            pulses = self._pulse_count - self._last_read_count
            self._last_read_count = self._pulse_count
            self._last_read_time = current_time

        return pulses, elapsed_seconds

    def read_flow_l_min(self) -> float:
        pulses, elapsed_seconds = self.read_pulse_sample()
        if elapsed_seconds <= 0:
            return 0.0

        pulse_frequency_hz = pulses / elapsed_seconds
        return pulse_frequency_hz / self.calibration_factor

    def close(self) -> None:
        if GPIO is None:
            return

        with self._lock:
            if self._closed:
                return
            self._closed = True

        try:
            GPIO.remove_event_detect(self.gpio_pin)
        except Exception:
            pass

        try:
            GPIO.cleanup(self.gpio_pin)
        except Exception:
            pass

    def __enter__(self) -> "RPiGPIOFlowMeter":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

def count_pulse(channel):
    """Callback function that increments the pulse counter."""
    global pulse_count
    pulse_count += 1

def setup():
    """Initializes the GPIO pins and interrupts."""
    if GPIO is None:
        raise FlowMeterError(
            "A biblioteca RPi.GPIO nao esta disponivel. "
            "Instala-a no Raspberry Pi antes de medir caudal."
        )
    GPIO.setmode(GPIO.BCM)
    # Set up the pin as an input with an internal pull-up resistor
    GPIO.setup(FLOW_SENSOR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    
    # Attach a hardware interrupt to the pin. 
    # It triggers the count_pulse function every time the signal falls from high to low.
    GPIO.add_event_detect(FLOW_SENSOR_PIN, GPIO.FALLING, callback=count_pulse)

def main():
    print("Starting Flow Sensor reading... Press Ctrl+C to exit.")

    try:
        with RPiGPIOFlowMeter() as flow_meter:
            while True:
                time.sleep(1.0)
                current_count, elapsed_seconds = flow_meter.read_pulse_sample()
                if elapsed_seconds <= 0:
                    flow_rate_l_min = 0.0
                else:
                    flow_rate_l_min = (
                        current_count / elapsed_seconds
                    ) / CALIBRATION_FACTOR
                print(
                    f"Flow Rate: {flow_rate_l_min:.2f} L/min | "
                    f"Pulses in last sec: {current_count}"
                )
    except KeyboardInterrupt:
        print("\nProgram interrupted by user. Cleaning up...")
    except FlowMeterError as exc:
        print(f"Erro: {exc}")

if __name__ == '__main__':
    main()

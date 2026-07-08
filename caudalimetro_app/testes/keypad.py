from __future__ import annotations

from collections.abc import Callable, Sequence
from threading import Event, Thread
import time

try:
    import RPi.GPIO as GPIO
except (ImportError, RuntimeError) as exc:
    GPIO = None
    GPIO_IMPORT_ERROR = exc
else:
    GPIO_IMPORT_ERROR = None


ROW_PINS = [25, 24, 22, 27]
COL_PINS = [18, 15, 14]

KEYPAD = [
    ["1", "2", "3"],
    ["4", "5", "6"],
    ["7", "8", "9"],
    ["*", "0", "#"],
]

KeyCallback = Callable[[str], None]


def _ensure_gpio_available() -> None:
    if GPIO is None:
        raise RuntimeError(
            "A biblioteca RPi.GPIO nao esta disponivel. "
            "Instale-a no Raspberry Pi para usar o numpad."
        ) from GPIO_IMPORT_ERROR


def setup(
    row_pins: Sequence[int] = ROW_PINS,
    col_pins: Sequence[int] = COL_PINS,
) -> None:
    _ensure_gpio_available()
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    for row_pin in row_pins:
        GPIO.setup(row_pin, GPIO.OUT)
        GPIO.output(row_pin, GPIO.HIGH)

    for col_pin in col_pins:
        GPIO.setup(col_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)


def read_keypad(
    row_pins: Sequence[int] = ROW_PINS,
    col_pins: Sequence[int] = COL_PINS,
    keypad: Sequence[Sequence[str]] = KEYPAD,
) -> str | None:
    _ensure_gpio_available()

    for row_index, row_pin in enumerate(row_pins):
        GPIO.output(row_pin, GPIO.LOW)

        try:
            for col_index, col_pin in enumerate(col_pins):
                if GPIO.input(col_pin) == GPIO.LOW:
                    pressed_key = keypad[row_index][col_index]
                    while GPIO.input(col_pin) == GPIO.LOW:
                        time.sleep(0.01)
                    return pressed_key
        finally:
            GPIO.output(row_pin, GPIO.HIGH)

    return None


class MatrixKeypad:
    def __init__(
        self,
        on_key: KeyCallback,
        *,
        row_pins: Sequence[int] = ROW_PINS,
        col_pins: Sequence[int] = COL_PINS,
        keypad: Sequence[Sequence[str]] = KEYPAD,
        poll_interval: float = 0.05,
    ) -> None:
        _ensure_gpio_available()
        self.on_key = on_key
        self.row_pins = list(row_pins)
        self.col_pins = list(col_pins)
        self.keypad = [list(row) for row in keypad]
        self.poll_interval = poll_interval
        self._stop_event = Event()
        self._thread: Thread | None = None

    def start(self) -> None:
        if self._thread is not None:
            return

        setup(self.row_pins, self.col_pins)
        self._thread = Thread(target=self._poll_loop, daemon=True)
        self._thread.start()

    def _poll_loop(self) -> None:
        while not self._stop_event.is_set():
            key = self._read_once()
            if key is not None:
                self.on_key(key)
            self._stop_event.wait(self.poll_interval)

    def _read_once(self) -> str | None:
        for row_index, row_pin in enumerate(self.row_pins):
            GPIO.output(row_pin, GPIO.LOW)

            try:
                for col_index, col_pin in enumerate(self.col_pins):
                    if GPIO.input(col_pin) == GPIO.LOW:
                        pressed_key = self.keypad[row_index][col_index]
                        while (
                            GPIO.input(col_pin) == GPIO.LOW
                            and not self._stop_event.is_set()
                        ):
                            time.sleep(0.01)
                        return pressed_key
            finally:
                GPIO.output(row_pin, GPIO.HIGH)

        return None

    def close(self) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=1.0)
            self._thread = None

        try:
            GPIO.cleanup([*self.row_pins, *self.col_pins])
        except Exception:
            pass


def main() -> None:
    setup()
    print("Keypad initialized successfully.")
    print("Press any key (Press Ctrl+C to exit)...")

    try:
        while True:
            key = read_keypad()
            if key:
                print(f"Key Pressed: {key}")
            time.sleep(0.05)
    except KeyboardInterrupt:
        print("\nProgram interrupted. Exiting...")
    finally:
        GPIO.cleanup([*ROW_PINS, *COL_PINS])


if __name__ == "__main__":
    main()

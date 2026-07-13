from __future__ import annotations

from collections.abc import Callable, Mapping
from signal import pause

try:
    from gpiozero import Button
except (ImportError, RuntimeError) as exc:
    Button = None
    GPIOZERO_IMPORT_ERROR = exc
else:
    GPIOZERO_IMPORT_ERROR = None


BUTTON_CONFIG = {
    "Voltar": 12,
    "Cima": 20,
    "Baixo": 16,
    "Vermelho": 5,
    "Verde": 1,
    "Azul": 7,
}

ButtonCallback = Callable[[str], None]
ButtonCallbacks = ButtonCallback | Mapping[str, ButtonCallback]


class PhysicalButtonPanel:
    def __init__(
        self,
        on_pressed: ButtonCallbacks | None = None,
        on_released: ButtonCallbacks | None = None,
        *,
        button_config: Mapping[str, int] = BUTTON_CONFIG,
        bounce_time: float = 0.05,
    ) -> None:
        if Button is None:
            raise RuntimeError(
                "A biblioteca gpiozero nao esta disponivel. "
                "Instale-a no Raspberry Pi para usar os botoes fisicos."
            ) from GPIOZERO_IMPORT_ERROR

        self._on_pressed = on_pressed
        self._on_released = on_released
        self.buttons: dict[str, Button] = {}

        for name, pin in button_config.items():
            btn = Button(pin, bounce_time=bounce_time)
            btn.when_pressed = self._make_dispatcher(self._on_pressed, name)
            btn.when_released = self._make_dispatcher(self._on_released, name)
            self.buttons[name] = btn

    def _make_dispatcher(
        self,
        callbacks: ButtonCallbacks | None,
        button_name: str,
    ) -> Callable[..., None]:
        def dispatch_button_name(*_args: object) -> None:
            self._dispatch(callbacks, button_name)

        return dispatch_button_name

    @staticmethod
    def _dispatch(callbacks: ButtonCallbacks | None, button_name: str) -> None:
        if callbacks is None:
            return

        if callable(callbacks):
            callbacks(button_name)
            return

        callback = callbacks.get(button_name)
        if callback is not None:
            callback(button_name)

    def close(self) -> None:
        for btn in self.buttons.values():
            btn.when_pressed = None
            btn.when_released = None
            btn.close()
        self.buttons.clear()


def button_pressed(button_name: str) -> None:
    print(f"[{button_name}] was pressed!")


def button_released(button_name: str) -> None:
    print(f"[{button_name}] was released!")


def main() -> None:
    panel = PhysicalButtonPanel(button_pressed, button_released)
    print("Program is running. Press any of the buttons (Press Ctrl+C to exit)...")

    try:
        pause()
    finally:
        panel.close()


if __name__ == "__main__":
    main()

from __future__ import annotations

import tkinter as tk

from .config import (
    APP_BG,
    APP_HEIGHT,
    APP_WIDTH,
    DATA_DIR,
    DIAMETER_OPTIONS,
    MENU_OPTIONS,
    SENT_DIR,
    SESSIONS_DIR,
)
from .keyboard import KeyboardMixin
from .measurement import MeasurementMixin
from .models import MeasurementSession
from .persistence import PersistenceMixin
from .screens import ScreensMixin
from .ui_components import UiComponentsMixin


class CaudalimetroApp(
    KeyboardMixin,
    PersistenceMixin,
    MeasurementMixin,
    UiComponentsMixin,
    ScreensMixin,
    tk.Tk,
):
    def __init__(self) -> None:
        super().__init__()
        self.title("Caudalímetro Industrial")
        self.geometry(f"{APP_WIDTH}x{APP_HEIGHT}")
        self.minsize(APP_WIDTH, APP_HEIGHT)
        self.configure(bg=APP_BG)

        DATA_DIR.mkdir(exist_ok=True)
        SESSIONS_DIR.mkdir(exist_ok=True)
        SENT_DIR.mkdir(exist_ok=True)

        self.screen = ""
        self.operator_id = ""
        self.pin = ""
        self.active_field = 0
        self.selected_index = 0
        self.input_value = ""
        self.login_active_field = 0
        self.circuit_active_field = 0
        self.circuit_inputs = {"A": "", "B": ""}
        self.diameter_options = DIAMETER_OPTIONS.copy()
        self.menu_options = MENU_OPTIONS.copy()
        self.side_options: list[str] = []
        self.session: MeasurementSession | None = None
        self.current_side = ""
        self.current_circuit = 0
        self.samples: list[float] = []
        self.measure_labels: dict[str, tk.Label] = {}
        self.status_text = ""

        self.bind("<Key>", self.on_key)
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.show_login()

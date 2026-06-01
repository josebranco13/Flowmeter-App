from __future__ import annotations

import tkinter as tk

from .config import (
    APP_BG,
    APP_HEIGHT,
    APP_WIDTH,
    DATA_DIR,
    DIAMETER_OPTIONS,
    MENU_OPTIONS,
    OPERATOR_OPTIONS,
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
        self.maximize_window()

        DATA_DIR.mkdir(parents=True, exist_ok=True)
        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        SENT_DIR.mkdir(parents=True, exist_ok=True)

        self.screen = ""
        self.operator_id = ""
        self.pin = ""
        self.active_field = 0
        self.selected_index = 0
        self.operator_options = OPERATOR_OPTIONS.copy()
        self.operator_list_open = False
        self.operator_selected_index = 0
        self.operator_visible_indices: list[int] = []
        self.input_value = ""
        self.login_active_field = 0
        self.circuit_active_field = 0
        self.circuit_inputs = {"A": "", "B": ""}
        self.diameter_options = DIAMETER_OPTIONS.copy()
        self.menu_options = MENU_OPTIONS.copy()
        self.selected_menu_option = ""
        self.mold_side_options = [
            "Fixed plate",
            "Moving Plate",
            "Middle Plate",
            "Jiggle",
            "Cam Slide",
        ]
        self.selected_mold_side_index = 0
        self.mold_side_dropdown_open = False
        self.side_options: list[str] = []
        self.session: MeasurementSession | None = None
        self.current_side = ""
        self.current_circuit = 0
        self.samples: list[float] = []
        self.measurement_running = False
        self.last_measurement_record: dict[str, object] | None = None
        self.selected_result_index = 0
        self.result_editing = False
        self.option_labels: list[tk.Label] = []
        self.diameter_labels: list[tk.Label] = []
        self.field_value_labels: dict[str, tk.Label] = {}
        self.measure_labels: dict[str, tk.Label] = {}
        self.status_text = ""

        self.bind("<Key>", self.on_key)
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.show_login()

    def maximize_window(self) -> None:
        try:
            self.state("zoomed")
        except tk.TclError:
            self.attributes("-zoomed", True)

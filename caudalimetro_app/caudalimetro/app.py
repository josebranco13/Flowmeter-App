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
    OPERATOR_PASSWORDS,
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
        self.option_add("*Button.takeFocus", 0)
        self.maximize_window()

        DATA_DIR.mkdir(parents=True, exist_ok=True)
        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        SENT_DIR.mkdir(parents=True, exist_ok=True)

        self.screen = ""
        self.operator_id = ""
        self.pin = ""
        self.active_field = 0
        self.selected_index = 0
        self.send_review_first_row = 0
        self.operator_options = OPERATOR_OPTIONS.copy()
        self.operator_passwords = OPERATOR_PASSWORDS.copy()
        self.operator_list_open = False
        self.operator_selected_index = 0
        self.operator_visible_indices: list[int] = []
        self.admin_operator_input = ""
        self.admin_new_operator_name = ""
        self.admin_new_operator_pin = ""
        self.admin_add_active_field = 0
        self.selected_admin_operator_index = 0
        self.pending_admin_operator_removal = ""
        self.admin_operator_labels: list[tk.Label] = []
        self.admin_visible_indices: list[int] = []
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

        self.bind_all("<KeyPress>", self.on_key)
        self.bind_all("<ButtonRelease-1>", self.restore_keyboard_focus, add="+")
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.show_login()
        self.after_idle(self.restore_keyboard_focus)

    def maximize_window(self) -> None:
        try:
            self.state("zoomed")
        except tk.TclError:
            self.attributes("-zoomed", True)

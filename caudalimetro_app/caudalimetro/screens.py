from __future__ import annotations

import tkinter as tk
from typing import Any

from .config import BLUE, GREEN, GREY, PANEL_BG, PANEL_FG, RED, WHITE


class ScreensMixin:
    def show_login(self) -> None:
        self.screen = "LOGIN"
        self.refresh_operator_options()
        self.clear()
        self.option_labels = []
        self.diameter_labels = []
        self.field_value_labels = {}

        root = tk.Frame(self, bg=WHITE)
        root.pack(fill="both", expand=True)

        content = tk.Frame(root, bg=WHITE)
        content.pack(fill="both", expand=True)
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(0, weight=1)
        content.grid_rowconfigure(3, weight=2)

        form = tk.Frame(content, bg=WHITE)
        form.grid(row=1, column=0)

        self.field_value_labels["operator_id"] = self.login_field_row(
            form,
            0,
            "Nº operador",
            self.operator_id,
            show_arrow=True,
        )
        self.field_value_labels["pin"] = self.login_field_row(
            form,
            1,
            "PIN",
            "●" * len(self.pin),
            show_arrow=False,
        )

        if self.operator_list_open:
            visible_options = self.visible_operator_options()
            self.operator_visible_indices = [index for index, _ in visible_options]
            dropdown = tk.Frame(form, bg=WHITE)
            dropdown.grid(row=2, column=1, sticky="ew", pady=(8, 0))
            for index, operator in visible_options:
                label = tk.Label(dropdown, text=f"Operador {operator}", pady=8, padx=10, anchor="w")
                self.style_option_label(label, index == self.operator_selected_index)
                label.pack(fill="x", pady=1)
                self.option_labels.append(label)
        else:
            self.operator_visible_indices = []

        if self.status_text:
            tk.Label(
                content,
                text=self.status_text,
                bg=WHITE,
                fg=RED,
                font=("Arial", 12, "bold"),
            ).grid(row=2, column=0, pady=14)

        self.build_login_footer(root)

    def login_field_row(
        self,
        parent: tk.Widget,
        row: int,
        label_text: str,
        value: str,
        show_arrow: bool,
    ) -> tk.Label:
        tk.Label(
            parent,
            text=label_text,
            bg=WHITE,
            fg=PANEL_FG,
            font=("Arial", 22, "bold"),
            anchor="e",
            width=11,
        ).grid(row=row, column=0, sticky="e", padx=(0, 16), pady=6)

        field = tk.Frame(parent, bg=GREY, width=310, height=54)
        field.grid(row=row, column=1, sticky="w", pady=6)
        field.pack_propagate(False)

        value_label = tk.Label(
            field,
            text=value or " ",
            bg=GREY,
            fg=PANEL_FG,
            font=("Arial", 20, "bold"),
            anchor="w",
            padx=10,
        )
        value_label.pack(side="left", fill="both", expand=True)

        if show_arrow:
            tk.Label(
                field,
                text="▼",
                bg=GREY,
                fg=PANEL_FG,
                font=("Arial", 22, "bold"),
                width=2,
            ).pack(side="right", fill="y")

        return value_label

    def build_login_footer(self, parent: tk.Widget) -> None:
        footer = tk.Frame(parent, bg=WHITE)
        footer.pack(side="bottom", fill="x")

        buttons = [
            ("Apagar tudo", "#303030", WHITE, self.clear_login_values),
            ("Apagar", RED, PANEL_FG, self.delete_one),
            ("Selecionar", GREEN, PANEL_FG, self.select),
            ("Confirmar", BLUE, PANEL_FG, self.confirm),
        ]
        for text, bg, fg, command in buttons:
            tk.Button(
                footer,
                text=text,
                command=command,
                bg=bg,
                fg=fg,
                activebackground=bg,
                activeforeground=fg,
                relief="flat",
                bd=0,
                borderwidth=0,
                highlightthickness=0,
                font=("Arial", 14),
                pady=16,
            ).pack(side="left", expand=True, fill="both")

    def clear_login_values(self) -> None:
        self.operator_id = ""
        self.pin = ""
        self.operator_list_open = False
        self.login_active_field = 0
        self.status_text = ""
        self.show_login()

    def visible_operator_options(self) -> list[tuple[int, str]]:
        max_visible = 4
        if len(self.operator_options) <= max_visible:
            return list(enumerate(self.operator_options))

        start = self.operator_selected_index - 1
        start = max(0, min(start, len(self.operator_options) - max_visible))
        end = start + max_visible
        return list(enumerate(self.operator_options[start:end], start=start))

    def show_menu(self) -> None:
        self.screen = "MENU"
        self.selected_index = min(self.selected_index, len(self.menu_options) - 1)
        panel = self.build_base("Menu principal", "2/8")
        tk.Label(
            panel,
            text=f"Operador: {self.operator_id}",
            bg=PANEL_BG,
            fg="#555555",
            font=("Arial", 12),
        ).pack(pady=(26, 12))
        for i, option in enumerate(self.menu_options):
            self.option_row(panel, option, i == self.selected_index)

    def show_mold(self) -> None:
        self.screen = "MOLD"
        self.clear()
        self.option_labels = []
        self.diameter_labels = []
        self.field_value_labels = {}

        root = tk.Frame(self, bg=WHITE)
        root.pack(fill="both", expand=True)

        content = tk.Frame(root, bg=WHITE)
        content.pack(fill="both", expand=True)
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(0, weight=1)
        content.grid_rowconfigure(2, weight=2)

        row = tk.Frame(content, bg=WHITE)
        row.grid(row=1, column=0, sticky="w", padx=8)

        tk.Label(
            row,
            text="Nº do molde:",
            bg=WHITE,
            fg=PANEL_FG,
            font=("Arial", 14, "bold"),
        ).pack(side="left")
        tk.Label(
            row,
            text="AHA",
            bg=WHITE,
            fg=PANEL_FG,
            font=("Arial", 14),
            padx=5,
        ).pack(side="left")

        field = tk.Frame(row, bg=GREY, width=182, height=32)
        field.pack(side="left", padx=(6, 0))
        field.pack_propagate(False)
        value_label = tk.Label(
            field,
            text=self.input_value or " ",
            bg=GREY,
            fg=PANEL_FG,
            font=("Arial", 14),
            anchor="w",
            padx=8,
        )
        value_label.pack(fill="both", expand=True)
        self.field_value_labels["input_value"] = value_label

        if self.status_text:
            tk.Label(
                content,
                text=self.status_text,
                bg=WHITE,
                fg=RED,
                font=("Arial", 12, "bold"),
            ).grid(row=2, column=0, sticky="n", pady=12)

        self.build_mold_footer(root)
        selected_option = tk.Label(
            root,
            text=self.selected_menu_option or "Medir caudal",
            bg="#f0b57a",
            fg="#8a5a25",
            font=("Arial", 15),
            padx=4,
            pady=3,
        )
        selected_option.place(relx=1.0, x=-1, y=1, anchor="ne")
        selected_option.lift()

    def build_mold_footer(self, parent: tk.Widget) -> None:
        footer = tk.Frame(parent, bg=WHITE)
        footer.pack(side="bottom", fill="x")

        buttons = [
            ("Voltar atrás", "#303030", WHITE, self.go_back),
            ("Apagar", RED, PANEL_FG, self.delete_one),
            ("Seguinte", GREEN, PANEL_FG, self.confirm),
            ("Confirmar", BLUE, PANEL_FG, self.confirm),
        ]
        for text, bg, fg, command in buttons:
            tk.Button(
                footer,
                text=text,
                command=command,
                bg=bg,
                fg=fg,
                activebackground=bg,
                activeforeground=fg,
                relief="flat",
                bd=0,
                borderwidth=0,
                highlightthickness=0,
                font=("Arial", 12),
                pady=16,
            ).pack(side="left", expand=True, fill="both")

    def show_mold_side(self) -> None:
        self.screen = "MOLD_SIDE"
        if self.selected_index not in (0, 1):
            self.selected_index = 0
        self.clear()
        self.option_labels = []
        self.diameter_labels = []
        self.field_value_labels = {}

        root = tk.Frame(self, bg=WHITE)
        root.pack(fill="both", expand=True)

        content = tk.Frame(root, bg=WHITE)
        content.pack(fill="both", expand=True)
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(0, weight=1)
        content.grid_rowconfigure(2, weight=2)

        form = tk.Frame(content, bg=WHITE)
        form.grid(row=1, column=0)

        tk.Label(
            form,
            text="Lado do Molde:",
            bg=WHITE,
            fg=PANEL_FG,
            font=("Arial", 15, "bold"),
        ).grid(row=0, column=0, sticky="e", padx=(0, 8), pady=5)

        side_value = self.session.lado_molde if self.session else ""
        side_active = self.selected_index == 0
        side_field = tk.Frame(
            form,
            bg=GREY,
            width=230,
            height=36,
            highlightbackground="#087cff" if side_active else WHITE,
            highlightcolor="#087cff" if side_active else WHITE,
            highlightthickness=3,
        )
        side_field.grid(row=0, column=1, sticky="w", pady=5)
        side_field.pack_propagate(False)
        tk.Label(
            side_field,
            text=side_value or " ",
            bg=GREY,
            fg=PANEL_FG,
            font=("Arial", 14),
            anchor="w",
            padx=8,
        ).pack(side="left", fill="both", expand=True)
        tk.Label(
            side_field,
            text="▼",
            bg=GREY,
            fg=PANEL_FG,
            font=("Arial", 21, "bold"),
            width=2,
        ).pack(side="right", fill="y")

        if self.mold_side_dropdown_open:
            dropdown = tk.Frame(form, bg=WHITE)
            dropdown.grid(row=1, column=1, sticky="ew", pady=(2, 6))
            for index, option in enumerate(self.mold_side_options):
                label = tk.Label(dropdown, text=option, pady=7, padx=8, anchor="w")
                self.style_option_label(label, index == self.selected_mold_side_index)
                label.pack(fill="x", pady=1)
                self.option_labels.append(label)

        tk.Label(
            form,
            text="Operador:",
            bg=WHITE,
            fg=PANEL_FG,
            font=("Arial", 15, "bold"),
        ).grid(row=2, column=0, sticky="e", padx=(0, 8), pady=(14, 5))
        tk.Label(
            form,
            text=self.operator_display_text(),
            bg=GREY,
            fg=PANEL_FG,
            font=("Arial", 14),
            anchor="w",
            width=20,
            padx=6,
            pady=4,
        ).grid(row=2, column=1, sticky="w", pady=(14, 5))

        operator_active = self.selected_index == 1
        operator_action = tk.Frame(
            form,
            bg="#087cff" if operator_active else WHITE,
            padx=3,
            pady=3,
        )
        operator_action.grid(row=3, column=0, columnspan=2, pady=(12, 0))
        tk.Button(
            operator_action,
            text="Trocar\nOperador",
            command=self.change_operator_from_mold_side,
            bg="#1f1f1f",
            fg=WHITE,
            activebackground="#1f1f1f",
            activeforeground=WHITE,
            relief="flat",
            bd=0,
            borderwidth=0,
            highlightthickness=0,
            font=("Arial", 13),
            width=14,
            pady=8,
        ).pack()

        if self.status_text:
            tk.Label(
                content,
                text=self.status_text,
                bg=WHITE,
                fg=RED,
                font=("Arial", 12, "bold"),
            ).grid(row=2, column=0, sticky="n", pady=12)

        self.build_mold_side_footer(root)
        mold_badge = tk.Label(
            root,
            text=(self.session.molde if self.session else ""),
            bg="#f0b57a",
            fg="#8a5a25",
            font=("Arial", 15),
            padx=14,
            pady=3,
        )
        mold_badge.place(relx=1.0, x=-1, y=1, anchor="ne")
        mold_badge.lift()

    def build_mold_side_footer(self, parent: tk.Widget) -> None:
        footer = tk.Frame(parent, bg=WHITE)
        footer.pack(side="bottom", fill="x")

        buttons = [
            ("Voltar atrás", "#303030", WHITE, self.go_back),
            ("Apagar", RED, PANEL_FG, self.clear_mold_side_selection),
            ("Selecionar", GREEN, PANEL_FG, self.select),
            ("Confirmar", BLUE, PANEL_FG, self.confirm),
        ]
        for text, bg, fg, command in buttons:
            tk.Button(
                footer,
                text=text,
                command=command,
                bg=bg,
                fg=fg,
                activebackground=bg,
                activeforeground=fg,
                relief="flat",
                bd=0,
                borderwidth=0,
                highlightthickness=0,
                font=("Arial", 12),
                pady=16,
            ).pack(side="left", expand=True, fill="both")

    def build_simple_footer(
        self,
        parent: tk.Widget,
        buttons: list[tuple[str, str, str, object]],
        font_size: int = 12,
    ) -> None:
        footer = tk.Frame(parent, bg=WHITE)
        footer.pack(side="bottom", fill="x")
        for text, bg, fg, command in buttons:
            tk.Button(
                footer,
                text=text,
                command=command,
                bg=bg,
                fg=fg,
                activebackground=bg,
                activeforeground=fg,
                relief="flat",
                bd=0,
                borderwidth=0,
                highlightthickness=0,
                font=("Arial", font_size),
                pady=16,
            ).pack(side="left", expand=True, fill="both")

    def clear_mold_side_selection(self) -> None:
        if self.session is not None:
            self.session.lado_molde = ""
        self.mold_side_dropdown_open = False
        self.selected_mold_side_index = 0
        self.selected_index = 0
        self.status_text = ""
        self.show_mold_side()

    def change_operator_from_mold_side(self) -> None:
        self.logout()
        self.show_login()

    def operator_display_text(self) -> str:
        return self.operator_id or "-"

    def place_orange_badge(
        self,
        parent: tk.Widget,
        text: str,
        font_size: int = 15,
        padx: int = 14,
    ) -> tk.Label:
        badge = tk.Label(
            parent,
            text=text,
            bg="#f0b57a",
            fg="#8a5a25",
            font=("Arial", font_size),
            padx=padx,
            pady=3,
        )
        badge.place(relx=1.0, x=-1, y=1, anchor="ne")
        badge.lift()
        return badge

    def diameter_badge_text(self) -> str:
        if self.session is None or not self.session.diametro_mm:
            return ""
        inch_labels = {
            6: '1/4"',
            8: '5/16"',
            10: '3/8"',
            12: '1/2"',
            14: '9/16"',
            16: '5/8"',
            20: '3/4"',
            25: '1"',
        }
        return inch_labels.get(self.session.diametro_mm, f"{self.session.diametro_mm} mm")

    def circuit_count_badge_text(self) -> str:
        count = self.expected_count_for_current_side()
        return f"{count}circuitos" if count else ""

    def measurement_badge_text(self) -> str:
        lines = [self.diameter_badge_text()]
        if self.session is not None and self.session.lado_molde:
            lines.append(self.session.lado_molde)
        count_text = self.circuit_count_badge_text()
        if count_text:
            lines.append(count_text)
        return "\n".join(line for line in lines if line)

    @staticmethod
    def format_flow_display(value: Any) -> str:
        try:
            return f"{float(value):.1f}".replace(".", ",")
        except (TypeError, ValueError):
            return "-"

    @staticmethod
    def format_mold_code(value: str) -> str:
        text = value.strip().upper()
        if not text:
            return ""
        if text.startswith("AHA"):
            return text
        return f"AHA{text}"

    @staticmethod
    def mold_input_from_code(value: str) -> str:
        text = value.strip().upper()
        if text.startswith("AHA"):
            return text[3:]
        return text

    def show_diameter(self) -> None:
        self.screen = "DIAMETER"
        panel = self.build_base("Diâmetro do circuito", "4/8")
        tk.Label(
            panel,
            text="Selecione o diâmetro",
            bg=PANEL_BG,
            fg=PANEL_FG,
            font=("Arial", 18, "bold"),
        ).pack(pady=(24, 12))

        grid = tk.Frame(panel, bg=PANEL_BG)
        grid.pack(pady=4)
        self.diameter_labels = []
        for i, diameter in enumerate(self.diameter_options):
            active = i == self.selected_index
            label = tk.Label(
                grid,
                text=f"{diameter} mm",
                width=10,
                pady=14,
            )
            self.style_diameter_label(label, active)
            label.grid(row=i % 2, column=i // 2, padx=7, pady=7)
            self.diameter_labels.append(label)

        tk.Label(
            panel,
            text="Use ↑/↓ para alterar a opção e confirme.",
            bg=PANEL_BG,
            fg="#555555",
            font=("Arial", 11),
        ).pack(pady=12)

        if self.session is not None and self.session.lado_molde:
            self.place_orange_badge(self, self.session.lado_molde)

    def show_pressure(self) -> None:
        self.screen = "PRESSURE"
        self.clear()
        self.option_labels = []
        self.diameter_labels = []
        self.field_value_labels = {}

        root = tk.Frame(self, bg=WHITE)
        root.pack(fill="both", expand=True)

        content = tk.Frame(root, bg=WHITE)
        content.pack(fill="both", expand=True)
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(0, weight=1)
        content.grid_rowconfigure(2, weight=2)

        row = tk.Frame(content, bg=WHITE)
        row.grid(row=1, column=0, sticky="w", padx=8)

        tk.Label(
            row,
            text="Pressão à entrada:",
            bg=WHITE,
            fg=PANEL_FG,
            font=("Arial", 14, "bold"),
        ).pack(side="left")
        field = tk.Frame(row, bg=GREY, width=90, height=32)
        field.pack(side="left", padx=(6, 4))
        field.pack_propagate(False)
        value_label = tk.Label(
            field,
            text=self.input_value or " ",
            bg=GREY,
            fg=PANEL_FG,
            font=("Arial", 14),
            anchor="w",
            padx=8,
        )
        value_label.pack(fill="both", expand=True)
        self.field_value_labels["input_value"] = value_label
        tk.Label(
            row,
            text="bar",
            bg=WHITE,
            fg=PANEL_FG,
            font=("Arial", 14),
        ).pack(side="left")

        if self.status_text:
            tk.Label(
                content,
                text=self.status_text,
                bg=WHITE,
                fg=RED,
                font=("Arial", 12, "bold"),
            ).grid(row=2, column=0, sticky="n", pady=12)

        self.build_simple_footer(
            root,
            [
                ("Voltar atrás", "#303030", WHITE, self.go_back),
                ("Apagar", RED, PANEL_FG, self.delete_one),
                ("Selecionar", GREEN, PANEL_FG, self.confirm),
                ("Confirmar", BLUE, PANEL_FG, self.confirm),
            ],
        )
        self.place_orange_badge(root, self.circuit_count_badge_text(), font_size=13, padx=10)

    def show_circuits(self) -> None:
        self.screen = "CIRCUITS"
        self.clear()
        self.option_labels = []
        self.diameter_labels = []
        self.field_value_labels = {}

        root = tk.Frame(self, bg=WHITE)
        root.pack(fill="both", expand=True)

        content = tk.Frame(root, bg=WHITE)
        content.pack(fill="both", expand=True)
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(0, weight=1)
        content.grid_rowconfigure(2, weight=2)

        row = tk.Frame(content, bg=WHITE)
        row.grid(row=1, column=0, sticky="w", padx=32)

        tk.Label(
            row,
            text="Quantidade de circuitos :",
            bg=WHITE,
            fg=PANEL_FG,
            font=("Arial", 12, "bold"),
        ).pack(side="left")
        field = tk.Frame(row, bg=GREY, width=70, height=26)
        field.pack(side="left", padx=(6, 0))
        field.pack_propagate(False)
        value_label = tk.Label(
            field,
            text=self.input_value or " ",
            bg=GREY,
            fg=PANEL_FG,
            font=("Arial", 12),
            anchor="center",
        )
        value_label.pack(fill="both", expand=True)
        self.field_value_labels["input_value"] = value_label

        if self.status_text:
            tk.Label(
                content,
                text=self.status_text,
                bg=WHITE,
                fg=RED,
                font=("Arial", 12, "bold"),
            ).grid(row=2, column=0, sticky="n", pady=12)

        self.build_simple_footer(
            root,
            [
                ("Voltar atrás", "#303030", WHITE, self.go_back),
                ("Apagar", RED, PANEL_FG, self.delete_one),
                ("Selecionar", GREEN, PANEL_FG, self.confirm),
                ("Confirmar", BLUE, PANEL_FG, self.confirm),
            ],
        )
        self.place_orange_badge(root, self.diameter_badge_text(), font_size=12, padx=24)

    def show_side_selection(self) -> None:
        self.screen = "SIDE"
        self.side_options = self.build_side_options()
        if not self.side_options:
            self.selected_index = 0
            self.show_summary()
            return
        self.selected_index = min(self.selected_index, len(self.side_options) - 1)
        panel = self.build_base("Escolha do lado", "7/8")
        assert self.session is not None
        tk.Label(
            panel,
            text="Selecione o lado a medir",
            bg=PANEL_BG,
            fg=PANEL_FG,
            font=("Arial", 18, "bold"),
        ).pack(pady=(24, 8))
        tk.Label(
            panel,
            text=(
                f"Molde {self.session.molde} | Ø {self.session.diametro_mm} mm | "
                f"{self.session.pressao_entrada_bar:.2f} bar"
            ),
            bg=PANEL_BG,
            fg="#555555",
            font=("Arial", 12),
        ).pack(pady=(0, 16))
        for i, option in enumerate(self.side_options):
            if option.startswith("Lado"):
                side = option[-1]
                measured = self.measured_count_for_side(side)
                expected = self.session.circuitos_por_lado[side]
                text = f"{option}  ({measured}/{expected} medidos)"
            else:
                text = option
            self.option_row(panel, text, i == self.selected_index)

    def show_measurement(self) -> None:
        self.screen = "MEASURE"
        self.clear()
        self.option_labels = []
        self.diameter_labels = []
        self.field_value_labels = {}
        self.measure_labels = {}

        root = tk.Frame(self, bg=WHITE)
        root.pack(fill="both", expand=True)

        content = tk.Frame(root, bg=WHITE)
        content.pack(fill="both", expand=True)
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(0, weight=1)
        content.grid_rowconfigure(2, weight=2)

        form = tk.Frame(content, bg=WHITE)
        form.grid(row=1, column=0, sticky="w", padx=4)

        assert self.session is not None
        tk.Label(
            form,
            text="Caudal atual:",
            bg=WHITE,
            fg=PANEL_FG,
            font=("Arial", 12),
        ).grid(row=0, column=0, sticky="w", pady=(0, 24))
        current = self.measure_value_box(form, 0, 1, 84, "")
        self.measure_labels["current"] = current

        labels = [("Min:", "min"), ("Med:", "avg"), ("Max:", "max")]
        for index, (text, key) in enumerate(labels):
            col = index * 2
            tk.Label(
                form,
                text=text,
                bg=WHITE,
                fg=PANEL_FG,
                font=("Arial", 12),
            ).grid(row=1, column=col, sticky="w", padx=(0, 2))
            self.measure_labels[key] = self.measure_value_box(form, 1, col + 1, 54, "")

        self.build_simple_footer(
            root,
            [
                ("Voltar atrás", "#303030", WHITE, self.go_back),
                ("Recomeçar", RED, PANEL_FG, self.restart_current_measurement),
                ("Parar", GREEN, PANEL_FG, self.stop_current_measurement),
                ("Concluir", BLUE, PANEL_FG, self.confirm),
            ],
            font_size=10,
        )
        self.place_orange_badge(root, f"circuito {self.current_circuit}", font_size=12, padx=18)

        self.after(250, self.update_measurement_values)

    def measure_value_box(
        self,
        parent: tk.Widget,
        row: int,
        column: int,
        width: int,
        value: str,
    ) -> tk.Label:
        box = tk.Frame(parent, bg=GREY, width=width, height=24)
        box.grid(row=row, column=column, sticky="w", padx=(0, 12), pady=(0, 24))
        box.pack_propagate(False)
        label = tk.Label(
            box,
            text=value or " ",
            bg=GREY,
            fg=PANEL_FG,
            font=("Arial", 12),
            anchor="center",
        )
        label.pack(fill="both", expand=True)
        return label

    def show_circuit_start(self) -> None:
        self.screen = "CIRCUIT_START"
        self.clear()
        self.option_labels = []
        self.diameter_labels = []
        self.field_value_labels = {}

        root = tk.Frame(self, bg=WHITE)
        root.pack(fill="both", expand=True)

        content = tk.Frame(root, bg=WHITE)
        content.pack(fill="both", expand=True)
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(2, weight=1)

        form = tk.Frame(content, bg=WHITE)
        form.grid(row=0, column=0, sticky="w", padx=4, pady=(8, 0))
        tk.Label(
            form,
            text="Medir circuitos",
            bg=WHITE,
            fg=PANEL_FG,
            font=("Arial", 12),
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))
        tk.Label(
            form,
            text="circuito nº",
            bg=WHITE,
            fg=PANEL_FG,
            font=("Arial", 11),
        ).grid(row=1, column=0, sticky="w")
        field = tk.Frame(form, bg=GREY, width=84, height=24)
        field.grid(row=1, column=1, sticky="w", padx=(8, 0))
        field.pack_propagate(False)
        tk.Label(
            field,
            text=str(self.current_circuit),
            bg=GREY,
            fg="#777777",
            font=("Arial", 11),
        ).pack(fill="both", expand=True)
        tk.Button(
            form,
            text="Medir Caudal",
            command=self.start_current_flow_measurement,
            bg="#1f1f1f",
            fg=WHITE,
            activebackground="#1f1f1f",
            activeforeground=WHITE,
            relief="flat",
            bd=0,
            borderwidth=0,
            highlightthickness=0,
            font=("Arial", 9),
            padx=16,
            pady=5,
        ).grid(row=2, column=0, columnspan=2, pady=(10, 0))

        self.build_simple_footer(
            root,
            [
                ("Voltar atrás", "#303030", WHITE, self.go_back),
                ("------", RED, PANEL_FG, self.no_action),
                ("Selecionar", GREEN, PANEL_FG, self.start_current_flow_measurement),
                ("Seguinte", BLUE, PANEL_FG, self.start_current_flow_measurement),
            ],
            font_size=10,
        )
        self.place_orange_badge(root, self.measurement_badge_text(), font_size=10, padx=18)

    def show_measurement_result(self) -> None:
        self.screen = "MEASUREMENT_RESULT"
        self.clear()
        self.option_labels = []
        self.diameter_labels = []
        self.field_value_labels = {}

        root = tk.Frame(self, bg=WHITE)
        root.pack(fill="both", expand=True)

        content = tk.Frame(root, bg=WHITE)
        content.pack(fill="both", expand=True)
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(1, weight=1)

        form = tk.Frame(content, bg=WHITE)
        form.grid(row=0, column=0, sticky="w", padx=6, pady=(8, 0))
        tk.Label(
            form,
            text="Medir circuitos",
            bg=WHITE,
            fg=PANEL_FG,
            font=("Arial", 18),
        ).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 8))
        tk.Label(
            form,
            text="circuito nº",
            bg=WHITE,
            fg=PANEL_FG,
            font=("Arial", 13),
        ).grid(row=1, column=0, sticky="e", pady=3)
        self.result_box(form, 1, 1, 120, str(self.current_circuit), font_size=16)

        flow_value = ""
        flow_highlighted = False
        if self.last_measurement_record:
            flow_value = self.format_flow_display(
                self.last_measurement_record.get("caudal_medio_l_min")
            )
            flow_highlighted = bool(self.last_measurement_record.get("destacado"))
        flow_active = self.selected_index == 0
        flow_bg = RED if flow_highlighted else GREY
        tk.Label(
            form,
            text="caudal:",
            bg=WHITE,
            fg=PANEL_FG,
            font=("Arial", 15),
        ).grid(row=2, column=0, sticky="e", pady=3)
        box = tk.Frame(
            form,
            bg=flow_bg,
            width=120,
            height=30,
            highlightbackground="#087cff" if flow_active else WHITE,
            highlightcolor="#087cff" if flow_active else WHITE,
            highlightthickness=2,
        )
        box.grid(row=2, column=1, sticky="w", padx=(8, 4), pady=3)
        box.pack_propagate(False)
        tk.Label(
            box,
            text=flow_value,
            bg=flow_bg,
            fg="#777777",
            font=("Arial", 15),
        ).pack(fill="both", expand=True)
        tk.Label(
            form,
            text="L/min",
            bg=WHITE,
            fg=PANEL_FG,
            font=("Arial", 15),
        ).grid(row=2, column=2, sticky="w", pady=3)

        highlight_active = self.selected_index == 1
        highlight_action = tk.Frame(
            form,
            bg="#087cff" if highlight_active else WHITE,
            padx=3,
            pady=3,
        )
        highlight_action.grid(row=3, column=0, columnspan=3, pady=(12, 0))
        tk.Button(
            highlight_action,
            text="Destacar",
            command=self.highlight_current_measurement,
            bg="#ff1010",
            fg=PANEL_FG,
            activebackground="#ff1010",
            activeforeground=PANEL_FG,
            relief="flat",
            bd=0,
            borderwidth=0,
            highlightthickness=0,
            font=("Arial", 11),
            padx=30,
            pady=8,
        ).pack()

        next_text = (
            "Proximo\nCircuito"
            if self.measured_count_for_side(self.current_side) < self.expected_count_for_current_side()
            else "Seguinte"
        )
        footer_area = tk.Frame(root, bg=WHITE)
        footer_area.pack(side="bottom", fill="x")
        tk.Label(
            footer_area,
            text="Limpar circuito anterior",
            bg=WHITE,
            fg=RED,
            font=("Arial", 13, "bold"),
        ).pack(fill="x", pady=(0, 4))
        self.build_simple_footer(
            footer_area,
            [
                ("Voltar atrás", "#303030", WHITE, self.go_back),
                ("Medir\nNovamente", RED, PANEL_FG, self.remeasure_current_circuit),
                ("Selecionar", GREEN, PANEL_FG, self.select),
                (next_text, BLUE, PANEL_FG, self.advance_after_measurement_result),
            ],
            font_size=10,
        )
        self.place_orange_badge(root, self.measurement_badge_text(), font_size=14, padx=18)

    def result_box(
        self,
        parent: tk.Widget,
        row: int,
        column: int,
        width: int,
        text: str,
        font_size: int = 13,
        bg: str = GREY,
        highlight_bg: str | None = None,
        highlight_thickness: int = 0,
    ) -> tk.Label:
        highlight_bg = highlight_bg or bg
        box = tk.Frame(
            parent,
            bg=bg,
            width=width,
            height=34,
            highlightbackground=highlight_bg,
            highlightcolor=highlight_bg,
            highlightthickness=highlight_thickness,
        )
        box.grid(row=row, column=column, sticky="w", padx=(8, 4), pady=3)
        box.pack_propagate(False)
        label = tk.Label(
            box,
            text=text,
            bg=bg,
            fg=PANEL_FG,
            font=("Arial", font_size),
            anchor="center",
        )
        label.pack(fill="both", expand=True)
        return label

    def show_circuit_results(self) -> None:
        self.screen = "CIRCUIT_RESULTS"
        self.clear()
        self.option_labels = []
        self.diameter_labels = []
        self.field_value_labels = {}

        root = tk.Frame(self, bg=WHITE)
        root.pack(fill="both", expand=True)

        content = tk.Frame(root, bg=WHITE)
        content.pack(fill="both", expand=True)
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(1, weight=1)

        side = self.current_side or (self.session.lado_molde if self.session else "")
        tk.Label(
            content,
            text=f"Circuitos do {side}",
            bg=WHITE,
            fg=PANEL_FG,
            font=("Arial", 22),
        ).grid(row=0, column=0, sticky="w", padx=4, pady=(0, 4))

        records = sorted(self.measurements_for_side(side), key=lambda item: item["circuito"])
        rows = tk.Frame(content, bg=WHITE)
        rows.grid(row=1, column=0, sticky="nw", padx=96)
        for index, item in enumerate(records[:6]):
            circuit = item.get("circuito", index + 1)
            editing = self.result_editing and index == self.selected_result_index
            value = (
                self.result_edit_display_value()
                if editing
                else self.format_flow_display(item.get("caudal_medio_l_min"))
            )
            tk.Label(
                rows,
                text=f"circuito {circuit}",
                bg=WHITE,
                fg=PANEL_FG,
                font=("Arial", 20),
            ).grid(row=index, column=0, sticky="e", pady=3)
            highlighted = bool(item.get("destacado"))
            selected = index == self.selected_result_index
            bg = RED if highlighted else GREY
            value_label = self.result_box(
                rows,
                index,
                1,
                184,
                value,
                font_size=18,
                bg=bg,
                highlight_bg="#087cff" if selected else bg,
                highlight_thickness=2 if selected else 0,
            )
            if selected:
                self.field_value_labels["selected_result_value"] = value_label
            tk.Label(
                rows,
                text="L/min",
                bg=WHITE,
                fg=PANEL_FG,
                font=("Arial", 20),
            ).grid(row=index, column=2, sticky="w", pady=3)

        if len(records) > 6:
            scroll = tk.Frame(content, bg="#d7d7d7", width=26, height=220)
            scroll.place(relx=0.965, rely=0.36, anchor="ne")
            scroll.pack_propagate(False)
            tk.Frame(scroll, bg="#555555", width=10, height=150).pack(pady=10)

        if self.status_text:
            tk.Label(
                content,
                text=self.status_text,
                bg=WHITE,
                fg=RED,
                font=("Arial", 13, "bold"),
            ).grid(row=2, column=0, sticky="w", padx=96, pady=(12, 0))

        self.build_simple_footer(
            root,
            [
                ("Voltar atrás", "#303030", WHITE, self.go_back),
                ("Medir\nNovamente", RED, PANEL_FG, self.remeasure_selected_result),
                (
                    "Guardar" if self.result_editing else "Editar",
                    GREEN,
                    PANEL_FG,
                    self.save_selected_result_edit if self.result_editing else self.edit_selected_result,
                ),
                ("Confirmar", BLUE, PANEL_FG, self.confirm),
            ],
            font_size=14,
        )

    def show_side_complete(self) -> None:
        self.screen = "SIDE_COMPLETE"
        self.clear()
        self.option_labels = []
        self.diameter_labels = []
        self.field_value_labels = {}

        root = tk.Frame(self, bg=WHITE)
        root.pack(fill="both", expand=True)

        content = tk.Frame(root, bg=WHITE)
        content.pack(fill="both", expand=True)

        info = tk.Frame(content, bg=WHITE)
        info.pack(anchor="nw", padx=20, pady=48)
        assert self.session is not None
        rows = [
            f"Molde {self.session.molde}",
            self.current_side or self.session.lado_molde,
        ]
        for row_index, text in enumerate(rows):
            tk.Label(
                info,
                text=text,
                bg=WHITE,
                fg=PANEL_FG,
                font=("Arial", 22),
                anchor="w",
            ).grid(row=row_index, column=0, columnspan=2, sticky="w")

        tk.Label(
            info,
            text="Nº de circuitos medidos",
            bg=WHITE,
            fg=PANEL_FG,
            font=("Arial", 22),
        ).grid(row=2, column=0, sticky="w")
        self.result_box(
            info,
            2,
            1,
            68,
            str(self.measured_count_for_side(self.current_side)),
            font_size=20,
        )
        tk.Label(
            info,
            text="Operador:",
            bg=WHITE,
            fg=PANEL_FG,
            font=("Arial", 22),
        ).grid(row=3, column=0, sticky="w")
        tk.Label(
            info,
            text=self.operator_display_text(),
            bg=GREY,
            fg=PANEL_FG,
            font=("Arial", 22),
            padx=4,
        ).grid(row=3, column=1, sticky="w")

        self.build_simple_footer(
            root,
            [
                ("Voltar atrás", "#303030", WHITE, self.go_back),
                ("Apagar", RED, PANEL_FG, self.no_action),
                ("Guardar\nDados", GREEN, PANEL_FG, self.save_session_and_return_to_login),
                ("Confirmar", BLUE, PANEL_FG, self.save_session_and_return_to_login),
            ],
            font_size=15,
        )

    def save_session_and_return_to_login(self) -> None:
        if self.session is not None:
            self.session.estado = "concluida"
            self.save_session()
        self.logout()
        self.show_login()

    def measure_next_side(self) -> None:
        if self.session is not None:
            self.session.lado_molde = ""
        self.current_side = ""
        self.current_circuit = 0
        self.input_value = ""
        self.selected_index = 0
        self.selected_mold_side_index = 0
        self.mold_side_dropdown_open = False
        self.status_text = ""
        self.show_mold_side()

    def no_action(self) -> None:
        return

    def show_summary(self) -> None:
        self.screen = "SUMMARY"
        if self.session is not None:
            self.session.estado = "concluida"
            self.save_session()
        panel = self.build_base("Resumo da sessão", "Concluído")
        tk.Label(
            panel,
            text="Medições guardadas",
            bg=PANEL_BG,
            fg=PANEL_FG,
            font=("Arial", 18, "bold"),
        ).pack(pady=(18, 6))

        total = len(self.session.medicoes) if self.session else 0
        tk.Label(
            panel,
            text=f"Total de circuitos medidos: {total}",
            bg=PANEL_BG,
            fg="#555555",
            font=("Arial", 12),
        ).pack(pady=(0, 10))

        if self.session and self.session.medicoes:
            table = tk.Frame(panel, bg=PANEL_BG)
            table.pack(fill="x", padx=35, pady=(0, 8))
            headers = ["Lado", "Circ.", "Min", "Médio", "Máx"]
            for col, header in enumerate(headers):
                tk.Label(
                    table,
                    text=header,
                    bg="#374151",
                    fg=WHITE,
                    font=("Arial", 10, "bold"),
                    width=10,
                    pady=4,
                ).grid(row=0, column=col, padx=1)
            for row, item in enumerate(self.session.medicoes[-5:], start=1):
                values = [
                    item["lado"],
                    item["circuito"],
                    item["caudal_min_l_min"],
                    item["caudal_medio_l_min"],
                    item["caudal_max_l_min"],
                ]
                for col, value in enumerate(values):
                    tk.Label(
                        table,
                        text=str(value),
                        bg=WHITE,
                        fg=PANEL_FG,
                        font=("Arial", 10),
                        width=10,
                        pady=4,
                    ).grid(row=row, column=col, padx=1, pady=1)

        options = ["Nova operação", "Enviar dados", "Terminar sessão"]
        for i, option in enumerate(options):
            self.option_row(panel, option, i == self.selected_index)

    def show_send_data(self) -> None:
        self.screen = "SEND"
        panel = self.build_base("Envio de dados", "Sincronização")
        pending = self.pending_sessions_count()
        tk.Label(
            panel,
            text="Enviar medições guardadas",
            bg=PANEL_BG,
            fg=PANEL_FG,
            font=("Arial", 18, "bold"),
        ).pack(pady=(42, 16))
        tk.Label(
            panel,
            text=f"Sessões pendentes: {pending}",
            bg=PANEL_BG,
            fg=BLUE if pending else GREEN,
            font=("Arial", 18, "bold"),
        ).pack(pady=(0, 20))

        options = self.get_send_options()
        self.selected_index = min(self.selected_index, len(options) - 1)
        for i, option in enumerate(options):
            self.option_row(panel, option, i == self.selected_index)

        tk.Label(
            panel,
            text="Nesta versão o envio é simulado e copiado para data/enviados/.",
            bg=PANEL_BG,
            fg="#555555",
            font=("Arial", 11),
        ).pack(pady=12)

    def get_send_options(self) -> list[str]:
        return ["Verificar medições", "Enviar agora", "Voltar ao menu"]

    def show_send_review(self) -> None:
        self.screen = "SEND_REVIEW"
        panel = self.build_base("Verificar medições", "Pré-envio")
        sessions = self.load_pending_sessions()
        rows = self.pending_measurement_rows(sessions)

        tk.Label(
            panel,
            text="Medições pendentes",
            bg=PANEL_BG,
            fg=PANEL_FG,
            font=("Arial", 18, "bold"),
        ).pack(pady=(18, 6))
        tk.Label(
            panel,
            text=f"Sessões: {len(sessions)} | Medições: {len(rows)}",
            bg=PANEL_BG,
            fg=BLUE if sessions else GREEN,
            font=("Arial", 14, "bold"),
        ).pack(pady=(0, 12))

        if rows:
            max_rows = 10 if self.winfo_height() >= 700 else 5
            visible_rows = rows[:max_rows]
            table = tk.Frame(panel, bg=PANEL_BG)
            table.pack(fill="x", padx=24, pady=(0, 6))
            headers = [
                ("Data", 14),
                ("Molde", 12),
                ("Lado", 5),
                ("Circ.", 5),
                ("Min", 8),
                ("Médio", 8),
                ("Máx", 8),
            ]
            for col, (header, width) in enumerate(headers):
                tk.Label(
                    table,
                    text=header,
                    bg="#374151",
                    fg=WHITE,
                    font=("Arial", 10, "bold"),
                    width=width,
                    pady=4,
                ).grid(row=0, column=col, padx=1, sticky="ew")

            for row_index, item in enumerate(visible_rows, start=1):
                values = [
                    item["data"],
                    item["molde"],
                    item["lado"],
                    item["circuito"],
                    item["min"],
                    item["medio"],
                    item["max"],
                ]
                for col, value in enumerate(values):
                    tk.Label(
                        table,
                        text=value,
                        bg=WHITE,
                        fg=PANEL_FG,
                        font=("Arial", 10),
                        width=headers[col][1],
                        pady=4,
                    ).grid(row=row_index, column=col, padx=1, pady=1, sticky="ew")

            if len(rows) > max_rows:
                tk.Label(
                    panel,
                    text=f"A mostrar {max_rows} de {len(rows)} medições.",
                    bg=PANEL_BG,
                    fg="#555555",
                    font=("Arial", 10),
                ).pack(pady=(0, 4))
        else:
            message = "Não existem medições pendentes para verificar."
            if sessions:
                message = "As sessões pendentes ainda não têm medições guardadas."
            tk.Label(
                panel,
                text=message,
                bg=PANEL_BG,
                fg="#555555",
                font=("Arial", 13),
            ).pack(pady=22)

        tk.Label(
            panel,
            text="Reveja os valores antes de confirmar o envio.",
            bg=PANEL_BG,
            fg="#555555",
            font=("Arial", 11),
        ).pack(pady=(8, 0))

    def pending_measurement_rows(self, sessions: list[dict[str, Any]]) -> list[dict[str, str]]:
        rows: list[dict[str, str]] = []
        for session in sessions:
            measurements = session.get("medicoes") or []
            if not isinstance(measurements, list):
                continue

            session_date = self.format_session_date(session)
            mold = self.short_table_text(session.get("molde") or "-", 12)
            for measurement in measurements:
                if not isinstance(measurement, dict):
                    continue

                rows.append(
                    {
                        "data": session_date,
                        "molde": mold,
                        "lado": self.short_table_text(measurement.get("lado") or "-", 5),
                        "circuito": self.short_table_text(
                            measurement.get("circuito") or "-", 5
                        ),
                        "min": self.format_measurement_value(
                            measurement.get("caudal_min_l_min")
                        ),
                        "medio": self.format_measurement_value(
                            measurement.get("caudal_medio_l_min")
                        ),
                        "max": self.format_measurement_value(
                            measurement.get("caudal_max_l_min")
                        ),
                    }
                )
        return rows

    @staticmethod
    def format_session_date(session: dict[str, Any]) -> str:
        value = str(
            session.get("criado_em")
            or session.get("atualizado_em")
            or session.get("session_id")
            or "-"
        )
        return value.replace("T", " ")[:16]

    @staticmethod
    def format_measurement_value(value: Any) -> str:
        if value in (None, ""):
            return "-"
        try:
            return f"{float(value):.2f}"
        except (TypeError, ValueError):
            return str(value)

    @staticmethod
    def short_table_text(value: Any, limit: int) -> str:
        text = str(value)
        if len(text) <= limit:
            return text
        if limit <= 3:
            return text[:limit]
        return f"{text[: limit - 3]}..."

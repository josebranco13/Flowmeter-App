from __future__ import annotations

import tkinter as tk

from .config import (
    APP_BG,
    BLACK,
    BLUE,
    DARK_PANEL,
    GREEN,
    GREY,
    PANEL_BG,
    PANEL_FG,
    RED,
    WHITE,
    YELLOW,
)


class UiComponentsMixin:
    def clear(self) -> None:
        for child in self.winfo_children():
            child.destroy()

    def build_base(self, title: str, step: str) -> tk.Frame:
        self.clear()
        self.option_labels = []
        self.diameter_labels = []
        self.field_value_labels = {}
        root = tk.Frame(self, bg=APP_BG)
        root.pack(fill="both", expand=True)

        if title or step:
            header = tk.Frame(root, bg=APP_BG)
            header.pack(fill="x", padx=22, pady=(16, 8))
            if title:
                tk.Label(
                    header,
                    text=title,
                    bg=APP_BG,
                    fg=WHITE,
                    font=("Arial", 22, "bold"),
                ).pack(side="left")
            if step:
                tk.Label(
                    header,
                    text=step,
                    bg=APP_BG,
                    fg="#cfd6df",
                    font=("Arial", 11),
                ).pack(side="right")

        body = tk.Frame(root, bg=APP_BG)
        body.pack(fill="both", expand=True, padx=22, pady=6)

        panel = tk.Frame(body, bg=PANEL_BG, bd=0, highlightthickness=0)
        panel.pack(side="left", fill="both", expand=True)

        if self.status_text:
            tk.Label(
                root,
                text=self.status_text,
                bg=APP_BG,
                fg=YELLOW,
                font=("Arial", 12, "bold"),
            ).pack(fill="x", padx=22, pady=(0, 4))

        self.build_footer(root)
        return panel

    def build_keypad_help(self, parent: tk.Widget) -> tk.Frame:
        frame = tk.Frame(parent, bg=DARK_PANEL, width=180, height=310)
        frame.pack_propagate(False)
        tk.Label(
            frame,
            text="Comandos",
            bg=DARK_PANEL,
            fg=WHITE,
            font=("Arial", 13, "bold"),
        ).pack(pady=(12, 8))

        rows = [
            ("↑ / ↓", "navegar"),
            ("0-9", "introduzir"),
            ("←", "voltar"),
            ("⌫", "apagar"),
            ("DEL / *", "limpar"),
            ("ENTER / #", "confirmar"),
        ]
        for key, desc in rows:
            line = tk.Frame(frame, bg=DARK_PANEL)
            line.pack(fill="x", padx=14, pady=4)
            tk.Label(
                line,
                text=key,
                width=9,
                bg="#3b82f6",
                fg=WHITE,
                font=("Arial", 11, "bold"),
                padx=6,
                pady=4,
            ).pack(side="left")
            tk.Label(
                line,
                text=desc,
                bg=DARK_PANEL,
                fg="#dce3ec",
                font=("Arial", 10),
            ).pack(side="left", padx=8)
        return frame

    def build_footer(self, parent: tk.Widget) -> None:
        footer = tk.Frame(parent, bg=APP_BG)
        footer.pack(fill="x", padx=22, pady=(4, 14))

        buttons = [
            ("Voltar", BLACK, self.go_back),
            ("Apagar", RED, self.delete_one),
            ("Selecionar", GREEN, self.select),
            ("Confirmar", BLUE, self.confirm),
        ]
        for text, color, command in buttons:
            tk.Button(
                footer,
                text=text,
                command=command,
                bg=color,
                fg=WHITE,
                activebackground=color,
                activeforeground=WHITE,
                relief="flat",
                font=("Arial", 11, "bold"),
                padx=18,
                pady=10,
            ).pack(side="left", expand=True, fill="x", padx=3)

    def field_row(self, parent: tk.Widget, label: str, value: str, active: bool) -> tk.Label:
        row = tk.Frame(parent, bg=PANEL_BG)
        row.pack(fill="x", padx=60, pady=10)
        tk.Label(row, text=label, bg=PANEL_BG, fg=PANEL_FG, font=("Arial", 14)).pack(
            side="left"
        )
        value_label = tk.Label(
            row,
            text=value or " ",
            bg="#bcd8ff" if active else GREY,
            fg=PANEL_FG,
            font=("Arial", 16, "bold"),
            anchor="w",
            width=18,
            padx=8,
        )
        value_label.pack(side="right")
        return value_label

    def update_field_value(self, key: str, value: str) -> bool:
        label = self.field_value_labels.get(key)
        if label is None:
            return False

        try:
            label.configure(text=value or " ")
        except tk.TclError:
            return False
        return True

    def style_option_label(self, label: tk.Label, active: bool) -> None:
        label.configure(
            bg=BLUE if active else GREY,
            fg=WHITE if active else PANEL_FG,
            font=("Arial", 17, "bold"),
        )

    def style_diameter_label(self, label: tk.Label, active: bool) -> None:
        label.configure(
            bg=BLUE if active else GREY,
            fg=WHITE if active else PANEL_FG,
            font=("Arial", 16, "bold"),
        )

    def update_option_selection(self) -> bool:
        if not self.option_labels:
            return False

        try:
            for index, label in enumerate(self.option_labels):
                self.style_option_label(label, index == self.selected_index)
        except tk.TclError:
            return False
        return True

    def update_diameter_selection(self) -> bool:
        if len(self.diameter_labels) != len(self.diameter_options):
            return False

        try:
            for index, label in enumerate(self.diameter_labels):
                self.style_diameter_label(label, index == self.selected_index)
        except tk.TclError:
            return False
        return True

    def update_operator_selection(self) -> bool:
        if len(self.option_labels) != len(self.operator_visible_indices):
            return False

        try:
            for label, index in zip(self.option_labels, self.operator_visible_indices):
                self.style_option_label(label, index == self.operator_selected_index)
        except tk.TclError:
            return False
        return True

    def update_operator_options(self, visible_options: list[tuple[int, str]]) -> bool:
        if len(self.option_labels) != len(visible_options):
            return False

        try:
            self.operator_visible_indices = []
            for label, (index, operator) in zip(self.option_labels, visible_options):
                self.operator_visible_indices.append(index)
                label.configure(text=f"Operador {operator}")
                self.style_option_label(label, index == self.operator_selected_index)
        except tk.TclError:
            return False
        return True

    def option_row(self, parent: tk.Widget, text: str, active: bool) -> tk.Label:
        label = tk.Label(
            parent,
            text=text,
            pady=12,
            padx=10,
            anchor="w",
        )
        self.style_option_label(label, active)
        label.pack(fill="x", padx=60, pady=6)
        self.option_labels.append(label)
        return label

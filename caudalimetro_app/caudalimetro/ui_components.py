from __future__ import annotations

import tkinter as tk

from .config import (
    BLUE,
    DARK_PANEL,
    GREEN,
    GREY,
    PANEL_BG,
    PANEL_FG,
    RED,
    WHITE,
)


class UiComponentsMixin:
    def clear(self) -> None:
        for child in self.winfo_children():
            child.destroy()
        self.after_idle(self.restore_keyboard_focus)

    def build_base(
        self,
        title: str,
        step: str,
        confirm_text: str = "Confirmar",
        back_text: str = "Voltar",
        back_command=None,
        delete_text: str | None = "Apagar",
        delete_command=None,
        select_text: str | None = "Selecionar",
        select_command=None,
        confirm_command=None,
        center_title: bool = False,
    ) -> tk.Frame:
        self.clear()
        self.option_labels = []
        self.diameter_labels = []
        self.field_value_labels = {}
        root = tk.Frame(self, bg=WHITE)
        root.pack(fill="both", expand=True)

        if title or step:
            header = tk.Frame(root, bg=WHITE)
            header.pack(fill="x", padx=22, pady=(16, 8))
            if title:
                title_label = tk.Label(
                    header,
                    text=title,
                    bg=WHITE,
                    fg=PANEL_FG,
                    font=("Arial", 22, "bold"),
                )
                if center_title:
                    title_label.pack(anchor="center")
                else:
                    title_label.pack(side="left")
            if step:
                tk.Label(
                    header,
                    text=step,
                    bg=WHITE,
                    fg="#777777",
                    font=("Arial", 11),
                ).pack(side="right")

        self.build_footer(
            root,
            confirm_text=confirm_text,
            back_text=back_text,
            back_command=back_command,
            delete_text=delete_text,
            delete_command=delete_command,
            select_text=select_text,
            select_command=select_command,
            confirm_command=confirm_command,
        )

        if self.status_text:
            tk.Label(
                root,
                text=self.status_text,
                bg=WHITE,
                fg="#c48b00",
                font=("Arial", 12, "bold"),
            ).pack(side="bottom", fill="x", pady=(0, 4))

        body = tk.Frame(root, bg=WHITE)
        body.pack(fill="both", expand=True)

        panel = tk.Frame(body, bg=PANEL_BG, bd=0, highlightthickness=0)
        panel.pack(side="left", fill="both", expand=True)
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

    def build_footer(
        self,
        parent: tk.Widget,
        confirm_text: str = "Confirmar",
        back_text: str = "Voltar",
        back_command=None,
        delete_text: str | None = "Apagar",
        delete_command=None,
        select_text: str | None = "Selecionar",
        select_command=None,
        confirm_command=None,
    ) -> None:
        footer = tk.Frame(parent, bg=WHITE)
        footer.pack(side="bottom", fill="x")

        back_command = back_command or self.go_back
        delete_command = delete_command or self.delete_one
        select_command = select_command or self.select
        confirm_command = confirm_command or self.confirm
        buttons = [
            (back_text, "#303030", WHITE, back_command),
        ]
        if delete_text is not None:
            buttons.append((delete_text, RED, PANEL_FG, delete_command))
        if select_text is not None:
            buttons.append((select_text, GREEN, PANEL_FG, select_command))
        buttons.append((confirm_text, BLUE, PANEL_FG, confirm_command))
        for text, color, fg, command in buttons:
            tk.Button(
                footer,
                takefocus=0,
                text=text,
                command=command,
                bg=color,
                fg=fg,
                activebackground=color,
                activeforeground=fg,
                relief="flat",
                bd=0,
                borderwidth=0,
                highlightthickness=0,
                font=("Arial", 12),
                pady=16,
            ).pack(side="left", expand=True, fill="both")

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
        font_size = getattr(label, "option_font_size", 17)
        font_weight = getattr(label, "option_font_weight", "bold")
        label.configure(
            bg=BLUE if active else GREY,
            fg=WHITE if active else PANEL_FG,
            font=("Arial", font_size, font_weight),
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
                label.configure(text=operator)
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

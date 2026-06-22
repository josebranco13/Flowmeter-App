from __future__ import annotations

import tkinter as tk
from typing import Any

from .config import APP_BG, BLUE, GREEN, GREY, PANEL_BG, PANEL_FG, RED, WHITE


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
        content.grid_rowconfigure(1, weight=1)

        tk.Label(
            content,
            text="Medição de Caudais de Circuitos de Moldes",
            bg=WHITE,
            fg=PANEL_FG,
            font=("Arial", 18, "bold"),
        ).grid(row=0, column=0, sticky="n", pady=(20, 30))

        form = tk.Frame(content, bg=WHITE)
        form.grid(row=1, column=0)

        op_container = tk.Frame(form, bg=WHITE)
        op_container.pack()
        self.field_value_labels["operator_id"] = self.login_field_row(
            op_container,
            0,
            "Operador",
            self.operator_id,
            show_arrow=True,
            command=None,
            active=self.login_active_field == 0,
        )

        if self.operator_list_open:
            visible_options = self.visible_operator_options()
            self.operator_visible_indices = [index for index, _ in visible_options]
            dropdown = tk.Frame(form, bg=WHITE)
            dropdown.pack(pady=(2, 8))
            for index, operator in visible_options:
                label = tk.Label(dropdown, text=operator, pady=8, padx=10, anchor="w")
                self.style_option_label(label, index == self.operator_selected_index)
                label.pack(fill="x", pady=1)
                self.option_labels.append(label)
        else:
            self.operator_visible_indices = []

        pin_container = tk.Frame(form, bg=WHITE)
        pin_container.pack()
        self.field_value_labels["pin"] = self.login_field_row(
            pin_container,
            1,
            "PIN",
            "●" * len(self.pin),
            show_arrow=False,
            active=self.login_active_field == 1,
        )

        if self.status_text:
            tk.Label(
                content,
                text=self.status_text,
                bg=WHITE,
                fg=RED,
                font=("Arial", 12, "bold"),
            ).grid(row=2, column=0, pady=14, sticky="n")

        action_area = tk.Frame(root, bg=WHITE)
        action_area.pack(side="bottom", fill="x")

        credits_active = self.login_active_field == 2
        credits_container = tk.Frame(
            action_area,
            width=310,
            height=48,
            highlightbackground="#087cff" if credits_active else WHITE,
            highlightcolor="#087cff",
            highlightthickness=3 if credits_active else 0,
        )
        credits_container.pack(pady=(0, 5))
        credits_container.pack_propagate(False)

        tk.Button(
            credits_container,
            takefocus=0,
            text="Créditos",
            bg="#303030",
            fg=WHITE,
            font=("Arial", 14),
        ).pack(fill="both", expand=True)

        self.build_login_footer(action_area)

    def login_field_row(
        self,
        parent: tk.Widget,
        row: int,
        label_text: str,
        value: str,
        show_arrow: bool,
        command=None,
        active: bool = False,
    ) -> tk.Label:
        tk.Label(
            parent,
            text=label_text,
            bg=WHITE,
            fg=PANEL_FG,
            font=("Arial", 18, "bold"),
            width=8,
            anchor="e",
        ).pack(side="left", padx=(0, 10))

        field = tk.Frame(
            parent,
            bg=GREY,
            width=310,
            height=54,
            highlightbackground="#087cff" if active else WHITE,
            highlightcolor="#087cff" if active else WHITE,
            highlightthickness=3 if active else 0,
        )
        field.pack(side="left", pady=8)
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
            arrow_label = tk.Label(
                field,
                text="▼",
                bg=GREY,
                fg=PANEL_FG,
                font=("Arial", 22, "bold"),
                width=2,
            )
            arrow_label.pack(side="right", fill="y")

        return value_label

    def show_credits(self) -> None:
        self.screen = "CREDITS"
        self.clear()

        root = tk.Frame(self, bg=WHITE)
        root.pack(fill="both", expand=True)

        content = tk.Frame(root, bg=WHITE)
        content.pack(fill="both", expand=True)

        tk.Label(
            content,
            text="Créditos",
            bg=WHITE,
            fg=PANEL_FG,
            font=("Arial", 18, "bold"),
        ).pack(side="top", pady=20)

        tk.Label(
            content,
            text=(
                "Projeto desenvolvido por:\n\n"
                "José Branco\n"
                "Rodrigo Lourenço\n\n\n"
                "Orientadores:\n\n"
                "Prof. Filipe Neves\n"
                "Prof. Paulo Costa\n"
                "Prof. João Galvão\n\n\n"
                "Colaboração técnica:\n\n"
                "Eng. João Godinho"
            ),
            bg=WHITE,
            fg=PANEL_FG,
            font=("Arial", 16),
            justify="center",
        ).pack(side="top", pady=(10, 0))

        self.build_login_footer(root)

    def build_login_footer(self, parent: tk.Widget) -> None:
        footer = tk.Frame(parent, bg=WHITE)
        footer.pack(side="bottom", fill="x")

        buttons = [
            ("Apagar tudo", "#303030", WHITE, self.delete_all),
            ("Apagar", RED, PANEL_FG, self.delete_one),
            ("Selecionar", GREEN, PANEL_FG, self.select),
            ("Confirmar", BLUE, PANEL_FG, self.confirm),
        ]
        for text, bg, fg, command in buttons:
            tk.Button(
                footer,
                takefocus=0,
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

    def clear_login_values(self) -> None:
        self.operator_id = ""
        self.pin = ""
        self.operator_list_open = False
        self.operator_visible_indices = []
        self.login_active_field = 0
        self.operator_selected_index = 0
        self.status_text = ""
        self.update_field_value("operator_id", "")
        self.update_field_value("pin", "")
        self.show_login()

    def visible_operator_options(self) -> list[tuple[int, str]]:
        max_visible = 4
        if len(self.operator_options) <= max_visible:
            return list(enumerate(self.operator_options))

        start = self.operator_selected_index - 1
        start = max(0, min(start, len(self.operator_options) - max_visible))
        end = start + max_visible
        return list(enumerate(self.operator_options[start:end], start=start))

    def visible_admin_operator_options(self) -> list[tuple[int, str]]:
        operators = self.managed_operator_options()
        max_visible = self.admin_operator_visible_count()
        if len(operators) <= max_visible:
            return list(enumerate(operators))

        start = self.selected_admin_operator_index - (max_visible // 2)
        start = max(0, min(start, len(operators) - max_visible))
        end = start + max_visible
        return list(enumerate(operators[start:end], start=start))

    def admin_operator_visible_count(self) -> int:
        height = max(self.winfo_height(), self.winfo_screenheight(), 480)
        if height >= 900:
            return 12
        if height >= 700:
            return 10
        return 8

    def show_admin_menu(self) -> None:
        self.screen = "ADMIN_MENU"
        self.selected_index = min(self.selected_index, 1)
        panel = self.build_base(
            "Admin",
            "",
            back_text="Logout",
            back_command=self.logout_to_login,
            center_title=True,
        )
        panel.configure(bg=WHITE)

        menu_content = tk.Frame(panel, bg=WHITE)
        menu_content.pack(expand=True, anchor="center")

        for i, option in enumerate(("Operadores", "Enviar dados")):
            label = tk.Label(
                menu_content,
                text=option,
                pady=18,
                padx=36,
                width=34,
                anchor="center",
            )
            label.option_font_size = 20
            self.style_option_label(label, i == self.selected_index)
            label.pack(fill="x", pady=8)
            self.option_labels.append(label)

    def show_admin_operators(self) -> None:
        self.screen = "ADMIN_OPERATORS"
        self.refresh_operator_options()
        admin_status_text = self.status_text
        operators = self.managed_operator_options()
        if operators:
            self.selected_admin_operator_index = min(
                self.selected_admin_operator_index,
                len(operators) - 1,
            )
        else:
            self.selected_admin_operator_index = 0

        self.status_text = ""
        panel = self.build_base(
            "Operadores",
            "",
            back_text="Voltar",
            back_command=self.show_admin_menu,
            delete_text="Remover",
            delete_command=self.remove_selected_admin_operator,
            select_text="Adicionar Operador",
            select_command=self.show_admin_add_operator,
            confirm_text="Sair",
            confirm_command=self.logout_to_login,
            center_title=True,
        )
        panel.configure(bg=WHITE)
        self.status_text = admin_status_text

        if admin_status_text:
            tk.Label(
                panel,
                text=admin_status_text,
                bg=WHITE,
                fg="#c48b00",
                font=("Arial", 12, "bold"),
            ).pack(fill="x", padx=60, pady=(18, 6))

        visible_options = self.visible_admin_operator_options()
        self.admin_operator_labels = []
        self.admin_visible_indices = [index for index, _ in visible_options]
        self.admin_operator_scrollbar = None
        if visible_options:
            list_area = tk.Frame(panel, bg=WHITE)
            list_area.pack(fill="x", padx=60, pady=(18 if not admin_status_text else 4, 0))
            operator_list = tk.Frame(list_area, bg=WHITE)
            operator_list.pack(side="left", fill="x", expand=True)
            for index, operator in visible_options:
                label = tk.Label(
                    operator_list,
                    text=operator,
                    pady=4,
                    padx=10,
                    anchor="w",
                )
                self.style_option_label(label, index == self.selected_admin_operator_index)
                label.pack(fill="x", pady=1)
                self.admin_operator_labels.append(label)

            if len(operators) > len(visible_options):
                self.admin_operator_scrollbar = tk.Frame(
                    list_area,
                    bg="#d7d7d7",
                    width=22,
                )
                self.admin_operator_scrollbar.pack(side="right", fill="y", padx=(8, 0))
                self.admin_operator_scrollbar.pack_propagate(False)
                self.update_admin_operator_scrollbar(operators, visible_options)
        else:
            tk.Label(
                panel,
                text="Sem operadores criados.",
                bg=WHITE,
                fg="#555555",
                font=("Arial", 12),
            ).pack(fill="x", padx=60, pady=12)

    def update_admin_operator_selection(self) -> bool:
        visible_options = self.visible_admin_operator_options()
        if len(self.admin_operator_labels) != len(visible_options):
            return False

        try:
            self.admin_visible_indices = []
            for label, (index, operator) in zip(self.admin_operator_labels, visible_options):
                self.admin_visible_indices.append(index)
                label.configure(text=operator)
                self.style_option_label(label, index == self.selected_admin_operator_index)
            self.update_admin_operator_scrollbar(
                self.managed_operator_options(),
                visible_options,
            )
        except tk.TclError:
            return False

        return True

    def update_admin_operator_scrollbar(
        self,
        operators: list[str],
        visible_options: list[tuple[int, str]],
    ) -> None:
        scrollbar = getattr(self, "admin_operator_scrollbar", None)
        if scrollbar is None or not visible_options or not operators:
            return

        for child in scrollbar.winfo_children():
            child.destroy()

        visible_fraction = max(0.12, min(1.0, len(visible_options) / len(operators)))
        max_start = max(len(operators) - len(visible_options), 1)
        first_visible_index = visible_options[0][0]
        thumb_top = (first_visible_index / max_start) * (1.0 - visible_fraction)
        tk.Frame(scrollbar, bg="#555555").place(
            relx=0.5,
            rely=thumb_top,
            anchor="n",
            relwidth=0.5,
            relheight=visible_fraction,
        )

    def show_admin_add_operator(self) -> None:
        self.screen = "ADMIN_ADD_OPERATOR"
        add_status_text = self.status_text
        self.status_text = ""
        panel = self.build_base(
            "Adicionar operador",
            "Admin",
            back_text="Voltar",
            back_command=self.cancel_admin_add_operator,
            delete_text="Apagar",
            delete_command=self.delete_one,
            select_text="Guardar",
            select_command=self.save_admin_operator,
            confirm_text="Sair",
            confirm_command=self.cancel_admin_add_operator,
        )
        self.status_text = add_status_text

        form = tk.Frame(panel, bg=PANEL_BG)
        form.pack(expand=True)
        self.admin_add_field_row(
            form,
            0,
            "Operador:",
            self.admin_new_operator_name,
            self.admin_add_active_field == 0,
            "admin_new_operator_name",
        )
        self.admin_add_field_row(
            form,
            1,
            "PIN:",
            "●" * len(self.admin_new_operator_pin),
            self.admin_add_active_field == 1,
            "admin_new_operator_pin",
        )

        if add_status_text:
            tk.Label(
                panel,
                text=add_status_text,
                bg=PANEL_BG,
                fg="#c48b00",
                font=("Arial", 12, "bold"),
            ).pack(fill="x", padx=60, pady=(0, 18))

    def admin_add_field_row(
        self,
        parent: tk.Widget,
        row: int,
        label_text: str,
        value: str,
        active: bool,
        key: str,
    ) -> None:
        tk.Label(
            parent,
            text=label_text,
            bg=PANEL_BG,
            fg=PANEL_FG,
            font=("Arial", 18, "bold"),
            width=10,
            anchor="e",
        ).grid(row=row, column=0, sticky="e", padx=(0, 12), pady=8)
        field = tk.Frame(
            parent,
            bg=GREY,
            width=300,
            height=42,
            highlightbackground="#087cff" if active else PANEL_BG,
            highlightcolor="#087cff" if active else PANEL_BG,
            highlightthickness=3,
        )
        field.grid(row=row, column=1, sticky="w", pady=8)
        field.pack_propagate(False)
        label = tk.Label(
            field,
            text=value or " ",
            bg=GREY,
            fg=PANEL_FG,
            font=("Arial", 16, "bold"),
            anchor="w",
            padx=8,
        )
        label.pack(fill="both", expand=True)
        self.field_value_labels[key] = label

    def refresh_admin_add_field(self) -> None:
        key = (
            "admin_new_operator_name"
            if self.admin_add_active_field == 0
            else "admin_new_operator_pin"
        )
        value = (
            self.admin_new_operator_name
            if self.admin_add_active_field == 0
            else "●" * len(self.admin_new_operator_pin)
        )
        if not self.update_field_value(key, value):
            self.show_admin_add_operator()

    def cancel_admin_add_operator(self) -> None:
        self.admin_new_operator_name = ""
        self.admin_new_operator_pin = ""
        self.admin_add_active_field = 0
        self.status_text = ""
        self.show_admin_operators()

    def refresh_admin_operator_input(self) -> None:
        if not self.update_field_value("admin_operator_input", self.admin_operator_input):
            self.show_admin_operators()

    def save_admin_operator(self) -> None:
        success, message = self.add_operator(
            self.admin_new_operator_name,
            self.admin_new_operator_pin,
        )
        self.status_text = message
        if success:
            new_operator = self.normalize_operator_name(self.admin_new_operator_name)
            self.admin_new_operator_name = ""
            self.admin_new_operator_pin = ""
            self.admin_add_active_field = 0
            operators = self.managed_operator_options()
            if new_operator in operators:
                self.selected_admin_operator_index = operators.index(new_operator)
            self.show_admin_operators()
        else:
            self.show_admin_add_operator()

    def remove_selected_admin_operator(self) -> None:
        operators = self.managed_operator_options()
        if not operators:
            self.status_text = "Não existem operadores para remover."
            self.show_admin_operators()
            return

        self.selected_admin_operator_index = min(
            self.selected_admin_operator_index,
            len(operators) - 1,
        )
        operator = operators[self.selected_admin_operator_index]
        self.pending_admin_operator_removal = operator
        self.status_text = ""
        self.show_admin_remove_confirmation()

    def show_admin_remove_confirmation(self) -> None:
        self.screen = "ADMIN_REMOVE_CONFIRM"
        self.clear()
        self.option_labels = []
        self.diameter_labels = []
        self.field_value_labels = {}

        operator = self.pending_admin_operator_removal or "-"

        root = tk.Frame(self, bg=APP_BG)
        root.pack(fill="both", expand=True)

        header = tk.Frame(root, bg=APP_BG)
        header.pack(fill="x", padx=22, pady=(16, 8))
        tk.Label(
            header,
            text="Remover operador",
            bg=APP_BG,
            fg=WHITE,
            font=("Arial", 22, "bold"),
        ).pack(side="left")
        tk.Label(
            header,
            text="Admin",
            bg=APP_BG,
            fg="#cfd6df",
            font=("Arial", 11),
        ).pack(side="right")

        body = tk.Frame(root, bg=APP_BG)
        body.pack(fill="both", expand=True, padx=22, pady=6)

        panel = tk.Frame(body, bg=PANEL_BG, bd=0, highlightthickness=0)
        panel.pack(fill="both", expand=True)

        content = tk.Frame(panel, bg=PANEL_BG)
        content.pack(expand=True)
        tk.Label(
            content,
            text="Pretende remover este operador?",
            bg=PANEL_BG,
            fg=PANEL_FG,
            font=("Arial", 20, "bold"),
        ).pack(pady=(0, 16))
        tk.Label(
            content,
            text=operator,
            bg=PANEL_BG,
            fg=BLUE,
            font=("Arial", 28, "bold"),
        ).pack()

        footer = tk.Frame(root, bg=APP_BG)
        footer.pack(fill="x", padx=22, pady=(4, 14))
        for text, bg, command in [
            ("Não", RED, self.cancel_admin_operator_removal),
            ("Sim", GREEN, self.confirm_admin_operator_removal),
        ]:
            tk.Button(
                footer,
                takefocus=0,
                text=text,
                bg=bg,
                fg=WHITE,
                activebackground=bg,
                activeforeground=WHITE,
                relief="flat",
                font=("Arial", 13, "bold"),
                padx=18,
                pady=14,
            ).pack(side="left", expand=True, fill="x", padx=3)

    def cancel_admin_operator_removal(self) -> None:
        self.pending_admin_operator_removal = ""
        self.status_text = ""
        self.show_admin_operators()

    def confirm_admin_operator_removal(self) -> None:
        operator = self.pending_admin_operator_removal
        if not operator:
            self.status_text = "Nenhum operador selecionado."
            self.show_admin_operators()
            return

        _, self.status_text = self.remove_operator(operator)
        self.pending_admin_operator_removal = ""
        remaining = self.managed_operator_options()
        if remaining:
            self.selected_admin_operator_index = min(
                self.selected_admin_operator_index,
                len(remaining) - 1,
            )
        else:
            self.selected_admin_operator_index = 0
        self.show_admin_operators()

    def show_menu(self) -> None:
        self.screen = "MENU"
        self.selected_index = min(self.selected_index, len(self.menu_options) - 1)
        panel = self.build_base(
            "Menu principal",
            "",
            back_text="Logout",
            back_command=self.logout_to_login,
            center_title=True,
        )
        panel.configure(bg=WHITE)
        menu_content = tk.Frame(panel, bg=WHITE)
        menu_content.pack(expand=True)

        tk.Label(
            menu_content,
            text=f"Operador: {self.operator_id}",
            bg=WHITE,
            fg="#555555",
            font=("Arial", 12),
        ).pack(pady=(0, 12))
        for i, option in enumerate(self.menu_options):
            label = tk.Label(
                menu_content,
                text=option,
                pady=8,
                padx=10,
                anchor="center",
                width=34,
            )
            label.option_font_size = 14
            self.style_option_label(label, i == self.selected_index)
            label.pack(pady=5)
            self.option_labels.append(label)

    def logout_to_login(self) -> None:
        self.logout()
        self.show_login()

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
        content.grid_rowconfigure(2, weight=1)

        row = tk.Frame(content, bg=WHITE)
        row.grid(row=1, column=0)

        tk.Label(
            row,
            text="Nº do molde:",
            bg=WHITE,
            fg=PANEL_FG,
            font=("Arial", 22, "bold"),
        ).pack(side="left")
        tk.Label(
            row,
            text="AHA",
            bg=WHITE,
            fg=PANEL_FG,
            font=("Arial", 22),
            padx=10,
        ).pack(side="left")

        field = tk.Frame(row, bg=GREY, width=300, height=54)
        field.pack(side="left", padx=(12, 0))
        field.pack_propagate(False)
        value_label = tk.Label(
            field,
            text=self.input_value or " ",
            bg=GREY,
            fg=PANEL_FG,
            font=("Arial", 22),
            anchor="w",
            padx=12,
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
                takefocus=0,
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
        content.grid_rowconfigure(2, weight=1)

        form = tk.Frame(content, bg=WHITE)
        form.grid(row=1, column=0)

        tk.Label(
            form,
            text="Lado do Molde:",
            bg=WHITE,
            fg=PANEL_FG,
            font=("Arial", 18, "bold"),
        ).grid(row=0, column=0, sticky="e", padx=(0, 12), pady=8)

        side_value = self.session.lado_molde if self.session else ""
        side_active = self.selected_index == 0
        side_field = tk.Frame(
            form,
            bg=GREY,
            width=330,
            height=56,
            highlightbackground="#087cff" if side_active else WHITE,
            highlightcolor="#087cff" if side_active else WHITE,
            highlightthickness=3,
        )
        side_field.grid(row=0, column=1, sticky="w", pady=8)
        side_field.pack_propagate(False)
        tk.Label(
            side_field,
            text=side_value or " ",
            bg=GREY,
            fg=PANEL_FG,
            font=("Arial", 17),
            anchor="w",
            padx=12,
        ).pack(side="left", fill="both", expand=True)
        tk.Label(
            side_field,
            text="▼",
            bg=GREY,
            fg=PANEL_FG,
            font=("Arial", 26, "bold"),
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
            font=("Arial", 18, "bold"),
        ).grid(row=2, column=0, sticky="e", padx=(0, 12), pady=(18, 8))
        operator_box = tk.Frame(
            form,
            bg=GREY,
            width=330,
            height=56,
        )
        operator_box.grid(row=2, column=1, sticky="w", pady=(18, 8))
        operator_box.pack_propagate(False)
        tk.Label(
            operator_box,
            text=self.operator_display_text(),
            bg=GREY,
            fg=PANEL_FG,
            font=("Arial", 17),
            anchor="w",
            padx=12,
        ).pack(fill="both", expand=True)

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
            takefocus=0,
            text="Trocar\nOperador",
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
                takefocus=0,
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
                takefocus=0,
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
        return self.diameter_display_text(self.session.diametro_mm)

    @staticmethod
    def diameter_display_text(diameter: int) -> str:
        inch_labels = {
            3: "1/8",
            6: "1/4",
            10: "3/8",
            12: "1/2",
            20: "3/4",
        }
        return inch_labels.get(diameter, f"{diameter} mm")

    def circuit_count_badge_text(self) -> str:
        count = self.expected_count_for_current_side()
        return f"{count} circuitos" if count else ""

    def pressure_badge_text(self) -> str:
        if self.session is None or not self.session.pressao_entrada_bar:
            return ""
        value = f"{float(self.session.pressao_entrada_bar):g}".replace(".", ",")
        return f"{value} bar"

    def setup_badge_text(
        self,
        include_circuit_count: bool = False,
        include_pressure: bool = False,
    ) -> str:
        lines = [self.diameter_badge_text()]
        if self.session is not None:
            if self.session.lado_molde:
                lines.append(self.session.lado_molde)
            if self.session.molde:
                lines.append(f"Molde {self.session.molde}")
        if include_circuit_count:
            lines.append(self.circuit_count_badge_text())
        if include_pressure:
            lines.append(self.pressure_badge_text())
        return "\n".join(line for line in lines if line)

    def diameter_context_badge_text(self) -> str:
        if self.session is None:
            return ""

        lines = []
        if self.session.lado_molde:
            lines.append(self.session.lado_molde)
        if self.session.molde:
            lines.append(f"Molde {self.session.molde}")
        return "\n".join(lines)

    def circuit_progress_title(self) -> str:
        total = (
            self.expected_count_for_side(self.current_side)
            if self.current_side
            else self.expected_count_for_current_side()
        )
        if self.current_circuit and total:
            return f"Medição de circuitos ({self.circuit_progress_index()}/{total})"
        return "Medição de circuitos"

    def measurement_badge_text(self) -> str:
        return self.setup_badge_text(include_circuit_count=True, include_pressure=True)

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
        if self.diameter_options:
            self.selected_index = min(self.selected_index, len(self.diameter_options) - 1)
        panel = self.build_base("", "")
        panel.configure(bg=WHITE)
        content = tk.Frame(panel, bg=WHITE)
        content.pack(expand=True)
        tk.Label(
            content,
            text="Selecione o diâmetro do circuito",
            bg=WHITE,
            fg=PANEL_FG,
            font=("Arial", 18, "bold"),
        ).pack(pady=(0, 22))

        grid = tk.Frame(content, bg=WHITE)
        grid.pack()
        top_row = tk.Frame(grid, bg=WHITE)
        top_row.pack()
        bottom_row = tk.Frame(grid, bg=WHITE)
        bottom_row.pack(pady=(8, 0))
        self.diameter_labels = []
        for i, diameter in enumerate(self.diameter_options):
            active = i == self.selected_index
            row_frame = top_row if i < 3 else bottom_row
            label = tk.Label(
                row_frame,
                text=self.diameter_display_text(diameter),
                width=10,
                pady=14,
            )
            self.style_diameter_label(label, active)
            label.pack(side="left", padx=7, pady=7)
            self.diameter_labels.append(label)

        tk.Label(
            content,
            text="Use ↑/↓ para alterar a opção e confirme.",
            bg=WHITE,
            fg="#555555",
            font=("Arial", 11),
        ).pack(pady=(18, 0))

        badge_text = self.diameter_context_badge_text()
        if badge_text:
            self.place_orange_badge(self, badge_text, font_size=13, padx=12)

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
        content.grid_rowconfigure(2, weight=1)

        row = tk.Frame(content, bg=WHITE)
        row.grid(row=1, column=0)

        tk.Label(
            row,
            text="Pressão à entrada:",
            bg=WHITE,
            fg=PANEL_FG,
            font=("Arial", 22, "bold"),
        ).pack(side="left")
        field = tk.Frame(row, bg=GREY, width=150, height=54)
        field.pack(side="left", padx=(14, 10))
        field.pack_propagate(False)
        value_label = tk.Label(
            field,
            text=self.input_value or " ",
            bg=GREY,
            fg=PANEL_FG,
            font=("Arial", 22),
            anchor="w",
            padx=12,
        )
        value_label.pack(fill="both", expand=True)
        self.field_value_labels["input_value"] = value_label
        tk.Label(
            row,
            text="bar",
            bg=WHITE,
            fg=PANEL_FG,
            font=("Arial", 22),
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
        self.place_orange_badge(
            root,
            self.setup_badge_text(include_circuit_count=True),
            font_size=11,
            padx=14,
        )

    def show_circuits(self) -> None:
        self.screen = "CIRCUITS"
        self.clear()
        self.option_labels = []
        self.diameter_labels = []
        self.field_value_labels = {}
        self.circuit_inputs.setdefault("count", "")
        self.circuit_inputs.setdefault("start", "")

        root = tk.Frame(self, bg=WHITE)
        root.pack(fill="both", expand=True)

        content = tk.Frame(root, bg=WHITE)
        content.pack(fill="both", expand=True)
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(0, weight=1)
        content.grid_rowconfigure(2, weight=1)

        form = tk.Frame(content, bg=WHITE)
        form.grid(row=1, column=0)

        side = self.session.lado_molde if self.session else ""
        start_required = self.circuit_start_required_for_side(side)
        if not start_required:
            self.circuit_active_field = 0
            self.circuit_inputs["start"] = "1"
        if self.input_value and not self.circuit_inputs["count"]:
            self.circuit_inputs["count"] = self.input_value

        self.circuit_input_row(
            form,
            0,
            "Quantidade de circuitos :",
            self.circuit_inputs["count"],
            "circuit_count",
            self.circuit_active_field == 0,
        )
        if start_required:
            self.circuit_input_row(
                form,
                1,
                "Circuito inicial :",
                self.circuit_inputs["start"],
                "circuit_start",
                self.circuit_active_field == 1,
            )

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
                ("Selecionar", GREEN, PANEL_FG, self.select),
                ("Confirmar", BLUE, PANEL_FG, self.confirm),
            ],
        )
        self.place_orange_badge(root, self.setup_badge_text(), font_size=12, padx=18)

    def circuit_input_row(
        self,
        parent: tk.Widget,
        row_index: int,
        label_text: str,
        value: str,
        field_key: str,
        active: bool,
    ) -> None:
        tk.Label(
            parent,
            text=label_text,
            bg=WHITE,
            fg=PANEL_FG,
            font=("Arial", 22, "bold"),
        ).grid(row=row_index, column=0, sticky="e", padx=(0, 14), pady=8)
        field = tk.Frame(
            parent,
            bg=GREY,
            width=140,
            height=54,
            highlightbackground="#087cff" if active else WHITE,
            highlightcolor="#087cff" if active else WHITE,
            highlightthickness=3 if active else 0,
        )
        field.grid(row=row_index, column=1, sticky="w", pady=8)
        field.pack_propagate(False)
        value_label = tk.Label(
            field,
            text=value or " ",
            bg=GREY,
            fg=PANEL_FG,
            font=("Arial", 22),
            anchor="center",
        )
        value_label.pack(fill="both", expand=True)
        self.field_value_labels[field_key] = value_label
        if field_key == "circuit_count":
            self.field_value_labels["input_value"] = value_label

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
                f"Molde {self.session.molde} | Ø {self.diameter_badge_text()} | "
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
        content.grid_rowconfigure(2, weight=1)

        form = tk.Frame(content, bg=WHITE)
        form.grid(row=1, column=0)

        assert self.session is not None
        tk.Label(
            form,
            text=f"Circuito {self.current_circuit}",
            bg=WHITE,
            fg=PANEL_FG,
            font=("Arial", 24, "bold"),
        ).grid(row=0, column=0, columnspan=6, pady=(0, 26))
        tk.Label(
            form,
            text="Caudal atual:",
            bg=WHITE,
            fg=PANEL_FG,
            font=("Arial", 20),
        ).grid(row=1, column=0, sticky="e", padx=(0, 12), pady=(0, 30))
        current = self.measure_value_box(form, 1, 1, 150, "")
        self.measure_labels["current"] = current

        labels = [("Min:", "min"), ("Med:", "avg"), ("Max:", "max")]
        for index, (text, key) in enumerate(labels):
            col = index * 2
            tk.Label(
                form,
                text=text,
                bg=WHITE,
                fg=PANEL_FG,
                font=("Arial", 20),
            ).grid(row=2, column=col, sticky="e", padx=(0, 10))
            self.measure_labels[key] = self.measure_value_box(form, 2, col + 1, 96, "")

        for key, value in self.current_measurement_display_values().items():
            label = self.measure_labels.get(key)
            if label is not None:
                label.configure(text=value)

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
        self.place_orange_badge(
            root,
            self.measurement_badge_text(),
            font_size=10,
            padx=18,
        )

        self.after(250, self.update_measurement_values)

    def measure_value_box(
        self,
        parent: tk.Widget,
        row: int,
        column: int,
        width: int,
        value: str,
    ) -> tk.Label:
        height = 42 if width >= 90 else 24
        font_size = 20 if width >= 90 else 12
        box = tk.Frame(parent, bg=GREY, width=width, height=height)
        box.grid(row=row, column=column, sticky="w", padx=(0, 28), pady=(0, 30))
        box.pack_propagate(False)
        label = tk.Label(
            box,
            text=value or " ",
            bg=GREY,
            fg=PANEL_FG,
            font=("Arial", font_size),
            anchor="center",
        )
        label.pack(fill="both", expand=True)
        return label

    def show_circuit_start(self) -> None:
        if self.session is not None and self.current_side:
            total = self.expected_count_for_side(self.current_side)
            last_circuit = self.last_circuit_for_side(self.current_side)
            if total and self.current_circuit > last_circuit:
                measured = self.measured_count_for_side(self.current_side)
                if measured >= total:
                    self.current_circuit = last_circuit
                    self.show_circuit_results()
                    return
                self.current_circuit = self.next_circuit_for_side(self.current_side)

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
        content.grid_rowconfigure(0, weight=1)
        content.grid_rowconfigure(2, weight=1)

        form = tk.Frame(content, bg=WHITE)
        form.grid(row=1, column=0)
        tk.Label(
            form,
            text=self.circuit_progress_title(),
            bg=WHITE,
            fg=PANEL_FG,
            font=("Arial", 24, "bold"),
        ).grid(row=0, column=0, columnspan=2, pady=(0, 24))
        tk.Label(
            form,
            text="circuito nº",
            bg=WHITE,
            fg=PANEL_FG,
            font=("Arial", 22),
        ).grid(row=1, column=0, sticky="e", padx=(0, 14))
        field = tk.Frame(form, bg=GREY, width=160, height=54)
        field.grid(row=1, column=1, sticky="w")
        field.pack_propagate(False)
        tk.Label(
            field,
            text=str(self.current_circuit),
            bg=GREY,
            fg="#777777",
            font=("Arial", 22),
        ).pack(fill="both", expand=True)
        tk.Button(
            form,
            takefocus=0,
            text="Medir Caudal",
            bg="#1f1f1f",
            fg=WHITE,
            activebackground="#1f1f1f",
            activeforeground=WHITE,
            relief="flat",
            bd=0,
            borderwidth=0,
            highlightthickness=0,
            font=("Arial", 18),
            padx=34,
            pady=12,
        ).grid(row=2, column=0, columnspan=2, pady=(26, 0))

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
        content.grid_rowconfigure(0, weight=1)
        content.grid_rowconfigure(1, weight=1)

        form = tk.Frame(content, bg=WHITE)
        form.grid(row=0, column=0)
        tk.Label(
            form,
            text=self.circuit_progress_title(),
            bg=WHITE,
            fg=PANEL_FG,
            font=("Arial", 24, "bold"),
        ).grid(row=0, column=0, columnspan=3, pady=(0, 24))
        tk.Label(
            form,
            text="Circuito nº",
            bg=WHITE,
            fg=PANEL_FG,
            font=("Arial", 22),
        ).grid(row=1, column=0, sticky="e", padx=(0, 14), pady=8)
        self.result_box(form, 1, 1, 180, str(self.current_circuit), font_size=22)

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
            font=("Arial", 22, "bold"),
        ).grid(row=2, column=0, sticky="e", padx=(0, 14), pady=8)
        box = tk.Frame(
            form,
            bg=flow_bg,
            width=180,
            height=54,
            highlightbackground="#087cff" if flow_active else WHITE,
            highlightcolor="#087cff" if flow_active else WHITE,
            highlightthickness=2,
        )
        box.grid(row=2, column=1, sticky="w", pady=8)
        box.pack_propagate(False)
        tk.Label(
            box,
            text=flow_value,
            bg=flow_bg,
            fg="#777777",
            font=("Arial", 22),
        ).pack(fill="both", expand=True)
        tk.Label(
            form,
            text="litros/min",
            bg=WHITE,
            fg=PANEL_FG,
            font=("Arial", 22, "bold"),
        ).grid(row=2, column=2, sticky="w", padx=(14, 0), pady=8)

        highlight_active = self.selected_index == 1
        highlight_action = tk.Frame(
            form,
            bg="#087cff" if highlight_active else WHITE,
            padx=3,
            pady=3,
        )
        highlight_action.grid(row=3, column=0, columnspan=3, pady=(24, 0))
        tk.Button(
            highlight_action,
            takefocus=0,
            text="Destacar",
            bg="#ff1010",
            fg=PANEL_FG,
            activebackground="#ff1010",
            activeforeground=PANEL_FG,
            relief="flat",
            bd=0,
            borderwidth=0,
            highlightthickness=0,
            font=("Arial", 18),
            padx=44,
            pady=12,
        ).pack()

        measured = self.measured_count_for_side(self.current_side)
        expected = self.expected_count_for_side(self.current_side)
        next_text = "Proximo\nCircuito" if measured < expected else "Seguinte"
        footer_area = tk.Frame(root, bg=WHITE)
        footer_area.pack(side="bottom", fill="x")
        tk.Label(
            footer_area,
            text="Limpar circuito",
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
            height=54 if font_size >= 20 else 34,
            highlightbackground=highlight_bg,
            highlightcolor=highlight_bg,
            highlightthickness=highlight_thickness,
        )
        box.grid(
            row=row,
            column=column,
            sticky="w",
            padx=(0, 4),
            pady=8 if font_size >= 20 else 3,
        )
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
        content.grid_rowconfigure(0, weight=1)
        content.grid_rowconfigure(1, weight=1)
        content.grid_rowconfigure(2, weight=1)

        side = self.current_side or (self.session.lado_molde if self.session else "")
        results_content = tk.Frame(content, bg=WHITE)
        results_content.grid(row=1, column=0)
        tk.Label(
            results_content,
            text=f"Circuitos do {side}",
            bg=WHITE,
            fg=PANEL_FG,
            font=("Arial", 28, "bold"),
        ).pack(pady=(0, 26))

        records = sorted(self.measurements_for_side(side), key=lambda item: item["circuito"])
        rows = tk.Frame(results_content, bg=WHITE)
        rows.pack()
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
                text=f"Circuito {circuit}",
                bg=WHITE,
                fg=PANEL_FG,
                font=("Arial", 24),
            ).grid(row=index, column=0, sticky="e", padx=(0, 14), pady=6)
            highlighted = bool(item.get("destacado"))
            selected = index == self.selected_result_index
            bg = RED if highlighted else GREY
            value_label = self.result_box(
                rows,
                index,
                1,
                220,
                value,
                font_size=24,
                bg=bg,
                highlight_bg="#087cff" if selected else bg,
                highlight_thickness=2 if selected else 0,
            )
            if selected:
                self.field_value_labels["selected_result_value"] = value_label
            tk.Label(
                rows,
                text="litros/min",
                bg=WHITE,
                fg=PANEL_FG,
                font=("Arial", 24),
            ).grid(row=index, column=2, sticky="w", padx=(14, 0), pady=6)

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
            ).grid(row=2, column=0, pady=(12, 0))

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
                ("Apagar", RED, PANEL_FG, self.restart_current_side_measurements),
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

    def restart_current_side_measurements(self) -> None:
        if self.session is None:
            return

        side = self.current_side or self.session.lado_molde
        if not side:
            return

        self.session.medicoes = [
            item for item in self.session.medicoes if item.get("lado") != side
        ]
        self.session.lado_molde = side
        self.current_side = side
        self.current_circuit = self.circuit_start_for_side(side)
        self.samples = []
        self.measurement_running = False
        self.last_measurement_record = None
        self.selected_index = 0
        self.selected_result_index = 0
        self.result_editing = False
        self.input_value = ""
        self.status_text = ""
        self.save_session()
        self.show_circuit_start()

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

    def show_send_review(self) -> None:
        self.screen = "SEND_REVIEW"
        panel = self.build_base(
            "",
            "",
            select_text="Enviar selecionado",
            confirm_text="Enviar",
        )
        panel.configure(bg=WHITE)
        sessions = self.load_pending_sessions()
        rows = self.pending_measurement_rows(sessions)
        session_count = self.pending_review_session_count(rows)
        operator_count = len({row["_operator_key"] for row in rows})
        count_text = (
            f"Operadores: {operator_count} | Medições: {len(rows)}"
            if self.operator_id == "ADMIN"
            else f"Sessões: {session_count} | Medições: {len(rows)}"
        )

        tk.Label(
            panel,
            text="Medições pendentes",
            bg=WHITE,
            fg=PANEL_FG,
            font=("Arial", 18, "bold"),
        ).pack(pady=(18, 6))
        tk.Label(
            panel,
            text=count_text,
            bg=WHITE,
            fg=BLUE if rows else GREEN,
            font=("Arial", 14, "bold"),
        ).pack(pady=(0, 12))

        if rows:
            self.selected_index = min(self.selected_index, session_count - 1)
            max_rows = self.send_review_visible_row_count()
            max_start = max(len(rows) - max_rows, 0)
            first_visible_row = max(
                0,
                min(getattr(self, "send_review_first_row", 0), max_start),
            )
            self.send_review_first_row = first_visible_row
            visible_rows = rows[first_visible_row : first_visible_row + max_rows]
            if visible_rows and all(
                row["_session_index"] != self.selected_index for row in visible_rows
            ):
                self.selected_index = int(visible_rows[0]["_session_index"])
            table_area = tk.Frame(panel, bg=WHITE)
            table_area.pack(fill="x", padx=24, pady=(0, 0))
            table = tk.Frame(table_area, bg=WHITE)
            table.pack(side="left", fill="x", expand=True)
            if self.operator_id == "ADMIN":
                headers = [
                    ("Data", 14),
                    ("Operador", 12),
                    ("Molde", 10),
                    ("Lado", 12),
                    ("Circ.", 5),
                    ("Min", 8),
                    ("Médio", 8),
                    ("Máx", 8),
                ]
            else:
                headers = [
                    ("Data", 14),
                    ("Operador", 12),
                    ("Molde", 10),
                    ("Lado", 12),
                    ("Circ.", 5),
                    ("Médio", 10),
                ]
            for col, (header, width) in enumerate(headers):
                table.grid_columnconfigure(col, weight=width)
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
                is_selected = item["_session_index"] == self.selected_index
                if self.operator_id == "ADMIN":
                    values = [
                        item["data"],
                        item["operador"],
                        item["molde"],
                        item["lado"],
                        item["circuito"],
                        item["min"],
                        item["medio"],
                        item["max"],
                    ]
                else:
                    values = [
                        item["data"],
                        item["operador"],
                        item["molde"],
                        item["lado"],
                        item["circuito"],
                        item["medio"],
                    ]
                for col, value in enumerate(values):
                    tk.Label(
                        table,
                        text=value,
                        bg=BLUE if is_selected else WHITE,
                        fg=WHITE if is_selected else PANEL_FG,
                        font=("Arial", 10, "bold" if is_selected else "normal"),
                        width=headers[col][1],
                        pady=4,
                    ).grid(row=row_index, column=col, padx=1, pady=1, sticky="ew")

            if len(rows) > max_rows:
                scrollbar = tk.Frame(table_area, bg="#d7d7d7", width=22)
                scrollbar.pack(side="right", fill="y", padx=(8, 0))
                scrollbar.pack_propagate(False)

                visible_fraction = max(0.12, min(1.0, len(visible_rows) / len(rows)))
                max_start = max(len(rows) - len(visible_rows), 1)
                thumb_top = (first_visible_row / max_start) * (1.0 - visible_fraction)
                tk.Frame(scrollbar, bg="#555555").place(
                    relx=0.5,
                    rely=thumb_top,
                    anchor="n",
                    relwidth=0.5,
                    relheight=visible_fraction,
                )
        else:
            message = "Não existem medições pendentes para verificar."
            if sessions and self.operator_id != "ADMIN":
                message = "Não existem medições pendentes deste operador."
            elif sessions:
                message = "As sessões pendentes ainda não têm medições guardadas."
            tk.Label(
                panel,
                text=message,
                bg=WHITE,
                fg="#555555",
                font=("Arial", 13),
            ).pack(pady=22)

    def pending_review_session_count(self, rows: list[dict[str, Any]]) -> int:
        if not rows:
            return 0
        return max(int(row["_session_index"]) for row in rows) + 1

    def send_review_visible_row_count(self) -> int:
        height = max(self.winfo_height(), self.winfo_screenheight(), 480)
        if height >= 900:
            return 16
        if height >= 700:
            return 11
        return 8

    def selected_pending_session_rows(self) -> list[dict[str, Any]]:
        rows = self.pending_measurement_rows(self.load_pending_sessions())
        if not rows:
            self.selected_index = 0
            return []

        session_count = self.pending_review_session_count(rows)
        self.selected_index = min(self.selected_index, session_count - 1)
        return [row for row in rows if row["_session_index"] == self.selected_index]

    def should_show_pending_measurement(
        self, measurement: dict[str, Any], session_operator: str
    ) -> bool:
        if self.operator_id == "ADMIN":
            return True
        operator = measurement.get("operador") or session_operator
        return (
            self.normalize_operator_name(str(operator))
            == self.normalize_operator_name(self.operator_id)
        )

    def delete_selected_pending_session(self) -> None:
        selected_rows = self.selected_pending_session_rows()
        if not selected_rows:
            self.status_text = "Não existe uma medição selecionada para apagar."
            self.show_send_review()
            return

        deleted_count = self.delete_pending_measurement_rows(selected_rows)
        if deleted_count:
            self.status_text = f"Medições apagadas: {deleted_count}."
            remaining_rows = self.pending_measurement_rows(self.load_pending_sessions())
            if remaining_rows:
                session_count = self.pending_review_session_count(remaining_rows)
                self.selected_index = min(self.selected_index, session_count - 1)
            else:
                self.selected_index = 0
            self.send_review_first_row = 0
        else:
            self.status_text = "Não foi possível apagar a medição selecionada."
        self.show_send_review()

    def send_selected_pending_session(self) -> None:
        selected_rows = self.selected_pending_session_rows()
        if not selected_rows:
            self.status_text = "Não existe uma medição selecionada para enviar."
            self.show_send_review()
            return

        sent_count = self.send_pending_measurement_rows(selected_rows)
        if sent_count:
            self.status_text = f"Medições enviadas: {sent_count}."
            remaining_rows = self.pending_measurement_rows(self.load_pending_sessions())
            if remaining_rows:
                session_count = self.pending_review_session_count(remaining_rows)
                self.selected_index = min(self.selected_index, session_count - 1)
            else:
                self.selected_index = 0
            self.send_review_first_row = 0
        else:
            self.status_text = "Não foi possível enviar a medição selecionada."
        self.show_send_review()

    def send_pending_measurements_for_current_operator(self) -> int:
        return self.send_pending_measurement_rows(
            self.pending_measurement_rows(self.load_pending_sessions())
        )

    def send_pending_measurement_rows(self, rows: list[dict[str, Any]]) -> int:
        sent_count = 0
        row_refs = sorted(
            (
                (str(row["_file_name"]), int(row["_measurement_index"]))
                for row in rows
            ),
            key=lambda item: (item[0], item[1]),
            reverse=True,
        )
        for file_name, measurement_index in row_refs:
            if self.simulate_send_pending_measurement(file_name, measurement_index):
                sent_count += 1
        return sent_count

    def delete_pending_measurement_rows(self, rows: list[dict[str, Any]]) -> int:
        deleted_count = 0
        row_refs = sorted(
            (
                (str(row["_file_name"]), int(row["_measurement_index"]))
                for row in rows
            ),
            key=lambda item: (item[0], item[1]),
            reverse=True,
        )
        for file_name, measurement_index in row_refs:
            if self.delete_pending_measurement(file_name, measurement_index):
                deleted_count += 1
        return deleted_count

    def pending_measurement_rows(self, sessions: list[dict[str, Any]]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        session_index = 0
        for session in sessions:
            measurements = session.get("medicoes") or []
            if not isinstance(measurements, list):
                continue

            file_name = str(
                session.get("_file_name") or f"{session.get('session_id')}.json"
            )
            session_date = self.format_session_date(session)
            session_operator = session.get("operador") or "-"
            mold = self.short_table_text(session.get("molde") or "-", 10)
            session_rows: list[dict[str, Any]] = []
            for measurement_index, measurement in enumerate(measurements):
                if not isinstance(measurement, dict):
                    continue

                operator = measurement.get("operador") or session_operator
                if not self.should_show_pending_measurement(measurement, session_operator):
                    continue

                session_rows.append(
                    {
                        "_file_name": file_name,
                        "_measurement_index": measurement_index,
                        "_session_index": session_index,
                        "_operator_key": self.normalize_operator_name(str(operator)),
                        "data": session_date,
                        "operador": self.short_table_text(operator, 12),
                        "molde": mold,
                        "lado": self.short_table_text(measurement.get("lado") or "-", 12),
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
            if session_rows:
                rows.extend(session_rows)
                session_index += 1
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

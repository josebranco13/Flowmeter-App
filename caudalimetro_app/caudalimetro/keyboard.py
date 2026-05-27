from __future__ import annotations

import tkinter as tk


class KeyboardMixin:
    def on_key(self, event: tk.Event) -> None:
        key = event.keysym
        char = event.char

        if key == "Escape":
            self.destroy()
            return

        if key == "Left":
            self.go_back()
            return

        if key in ("Return", "KP_Enter") or char == "#":
            self.confirm()
            return

        if key == "space":
            self.select()
            return

        if key == "BackSpace":
            self.delete_one()
            return

        if key == "Delete" or char == "*":
            self.delete_all()
            return

        if key == "Up":
            self.move(-1)
            return

        if key == "Down":
            self.move(1)
            return

        if char and char.isdigit():
            self.add_char(char)
            return

        if char in (".", ","):
            self.add_char(".")
            return

    def move(self, delta: int) -> None:
        if self.screen == "LOGIN":
            if self.operator_list_open:
                self.refresh_operator_options()
                if self.operator_options:
                    self.operator_selected_index = (
                        self.operator_selected_index + delta
                    ) % len(self.operator_options)
                visible_options = self.visible_operator_options()
                if self.update_operator_options(visible_options):
                    return

                self.show_login()
                return

            self.login_active_field = (self.login_active_field + delta) % 2
            self.operator_list_open = False
            self.show_login()
        elif self.screen == "MENU":
            self.selected_index = (self.selected_index + delta) % len(self.menu_options)
            if not self.update_option_selection():
                self.show_menu()
        elif self.screen == "DIAMETER":
            self.move_diameter_selection(delta)
            if not self.update_diameter_selection():
                self.show_diameter()
        elif self.screen == "CIRCUITS":
            self.circuit_active_field = (self.circuit_active_field + delta) % 2
            self.show_circuits()
        elif self.screen == "SIDE":
            if self.side_options:
                self.selected_index = (self.selected_index + delta) % len(self.side_options)
                if not self.update_option_selection():
                    self.show_side_selection()
        elif self.screen == "SUMMARY":
            self.selected_index = (self.selected_index + delta) % 3
            if not self.update_option_selection():
                self.show_summary()
        elif self.screen == "SEND":
            self.selected_index = (self.selected_index + delta) % 2
            if not self.update_option_selection():
                self.show_send_data()

    def move_diameter_selection(self, delta: int) -> None:
        if not self.diameter_options:
            return

        columns = 4
        option_count = len(self.diameter_options)
        index = self.selected_index
        column = index % columns

        if delta > 0:
            below = index + columns
            if below < option_count:
                self.selected_index = below
                return

            next_column = (column + 1) % columns
            self.selected_index = self.first_index_in_column(next_column, columns)
            return

        above = index - columns
        if above >= 0:
            self.selected_index = above
            return

        previous_column = (column - 1) % columns
        self.selected_index = self.last_index_in_column(previous_column, columns)

    def first_index_in_column(self, column: int, columns: int) -> int:
        option_count = len(self.diameter_options)
        while column >= option_count:
            column = (column + 1) % columns
        return column

    def last_index_in_column(self, column: int, columns: int) -> int:
        option_count = len(self.diameter_options)
        while column >= option_count:
            column = (column - 1) % columns

        index = column
        while index + columns < option_count:
            index += columns
        return index

    def update_input_value_field(self) -> bool:
        if self.screen == "PRESSURE":
            value = f"{self.input_value} bar" if self.input_value else ""
        else:
            value = self.input_value
        return self.update_field_value("input_value", value)

    def add_char(self, char: str) -> None:
        if self.screen == "LOGIN":
            if self.login_active_field == 0:
                was_list_open = self.operator_list_open
                self.operator_list_open = False
                self.operator_id = (self.operator_id + char)[:12]
                if was_list_open or not self.update_field_value("operator_id", self.operator_id):
                    self.show_login()
            else:
                self.pin = (self.pin + char)[:8]
                if not self.update_field_value("pin", "●" * len(self.pin)):
                    self.show_login()
        elif self.screen == "MOLD":
            self.input_value = (self.input_value + char)[:20]
            if not self.update_input_value_field():
                self.show_mold()
        elif self.screen == "PRESSURE":
            if char == "." and "." in self.input_value:
                return
            self.input_value = (self.input_value + char)[:8]
            if not self.update_input_value_field():
                self.show_pressure()
        elif self.screen == "CIRCUITS":
            side = "A" if self.circuit_active_field == 0 else "B"
            self.circuit_inputs[side] = (self.circuit_inputs[side] + char)[:2]
            if not self.update_field_value(f"circuit_{side}", self.circuit_inputs[side]):
                self.show_circuits()

    def delete_one(self) -> None:
        if self.screen == "LOGIN":
            if self.login_active_field == 0:
                was_list_open = self.operator_list_open
                self.operator_list_open = False
                self.operator_id = self.operator_id[:-1]
                if was_list_open or not self.update_field_value("operator_id", self.operator_id):
                    self.show_login()
            else:
                self.pin = self.pin[:-1]
                if not self.update_field_value("pin", "●" * len(self.pin)):
                    self.show_login()
        elif self.screen in ("MOLD", "PRESSURE"):
            self.input_value = self.input_value[:-1]
            self.refresh_current_screen()
        elif self.screen == "CIRCUITS":
            side = "A" if self.circuit_active_field == 0 else "B"
            self.circuit_inputs[side] = self.circuit_inputs[side][:-1]
            if not self.update_field_value(f"circuit_{side}", self.circuit_inputs[side]):
                self.show_circuits()

    def delete_all(self) -> None:
        if self.screen == "LOGIN":
            if self.login_active_field == 0:
                was_list_open = self.operator_list_open
                self.operator_list_open = False
                self.operator_id = ""
                if was_list_open or not self.update_field_value("operator_id", self.operator_id):
                    self.show_login()
            else:
                self.pin = ""
                if not self.update_field_value("pin", ""):
                    self.show_login()
        elif self.screen in ("MOLD", "PRESSURE"):
            self.input_value = ""
            self.refresh_current_screen()
        elif self.screen == "CIRCUITS":
            side = "A" if self.circuit_active_field == 0 else "B"
            self.circuit_inputs[side] = ""
            if not self.update_field_value(f"circuit_{side}", ""):
                self.show_circuits()

    def select(self) -> None:
        if self.screen == "LOGIN":
            self.select_login_operator()
            return

        self.confirm()

    def select_login_operator(self) -> None:
        if self.login_active_field != 0:
            self.confirm()
            return

        self.refresh_operator_options()
        if not self.operator_options:
            self.operator_list_open = False
            self.status_text = "Não existem operadores configurados."
            self.show_login()
            return

        if self.operator_list_open:
            self.operator_id = self.operator_options[self.operator_selected_index]
            self.operator_list_open = False
            self.login_active_field = 1
            self.status_text = ""
            self.show_login()
            return

        if self.operator_id in self.operator_options:
            self.operator_selected_index = self.operator_options.index(self.operator_id)
        else:
            self.operator_selected_index = 0
        self.operator_list_open = True
        self.status_text = ""
        self.show_login()

    def confirm(self) -> None:
        if self.screen == "LOGIN":
            self.operator_list_open = False
            if not self.operator_id or not self.pin:
                self.status_text = "Preencha o nº de operador e o PIN."
                self.show_login()
                return
            self.status_text = ""
            self.show_menu()

        elif self.screen == "MENU":
            option = self.menu_options[self.selected_index]
            if option == "Medir caudal":
                self.start_new_session()
                self.input_value = ""
                self.show_mold()
            else:
                self.selected_index = 0
                self.show_send_data()

        elif self.screen == "MOLD":
            if not self.input_value:
                self.status_text = "Indique o molde."
                self.show_mold()
                return
            assert self.session is not None
            self.session.molde = self.input_value
            self.input_value = ""
            self.status_text = ""
            self.selected_index = 0
            self.show_diameter()

        elif self.screen == "DIAMETER":
            assert self.session is not None
            self.session.diametro_mm = self.diameter_options[self.selected_index]
            self.input_value = ""
            self.show_pressure()

        elif self.screen == "PRESSURE":
            try:
                pressure = float(self.input_value)
            except ValueError:
                pressure = 0.0
            if pressure <= 0:
                self.status_text = "A pressão deve ser superior a 0 bar."
                self.show_pressure()
                return
            assert self.session is not None
            self.session.pressao_entrada_bar = pressure
            self.status_text = ""
            self.circuit_inputs = {"A": "", "B": ""}
            self.circuit_active_field = 0
            self.show_circuits()

        elif self.screen == "CIRCUITS":
            a = int(self.circuit_inputs["A"] or "0")
            b = int(self.circuit_inputs["B"] or "0")
            if a + b <= 0:
                self.status_text = "Indique pelo menos 1 circuito."
                self.show_circuits()
                return
            assert self.session is not None
            self.session.circuitos_por_lado = {"A": a, "B": b}
            self.save_session()
            self.status_text = ""
            self.selected_index = 0
            self.show_side_selection()

        elif self.screen == "SIDE":
            if not self.side_options:
                self.show_summary()
                return
            selected = self.side_options[self.selected_index]
            if selected == "Concluir sessão":
                self.selected_index = 0
                self.show_summary()
                return
            self.start_measurement(selected)

        elif self.screen == "MEASURE":
            self.finish_current_measurement()

        elif self.screen == "SUMMARY":
            if self.selected_index == 0:
                self.reset_operator_only()
                self.show_menu()
            elif self.selected_index == 1:
                self.selected_index = 0
                self.show_send_data()
            else:
                self.logout()
                self.show_login()

        elif self.screen == "SEND":
            if self.selected_index == 0:
                count = self.simulate_send_pending_sessions()
                self.status_text = f"Envio concluído. Sessões enviadas: {count}."
                self.selected_index = 0
                self.show_send_data()
            else:
                self.selected_index = 0
                self.show_menu()

    def go_back(self) -> None:
        if self.screen == "LOGIN":
            if self.operator_list_open:
                self.operator_list_open = False
                self.show_login()
            return
        if self.screen == "MENU":
            self.show_login()
        elif self.screen == "MOLD":
            self.show_menu()
        elif self.screen == "DIAMETER":
            self.input_value = self.session.molde if self.session else ""
            self.show_mold()
        elif self.screen == "PRESSURE":
            self.show_diameter()
        elif self.screen == "CIRCUITS":
            self.input_value = str(self.session.pressao_entrada_bar) if self.session else ""
            self.show_pressure()
        elif self.screen == "SIDE":
            self.show_circuits()
        elif self.screen == "MEASURE":
            self.status_text = "Medição cancelada. Nenhum valor foi guardado."
            self.samples = []
            self.show_side_selection()
        elif self.screen in ("SUMMARY", "SEND"):
            self.show_menu()

    def refresh_current_screen(self) -> None:
        if self.screen in ("MOLD", "PRESSURE") and self.update_input_value_field():
            return

        if self.screen == "MOLD":
            self.show_mold()
        elif self.screen == "PRESSURE":
            self.show_pressure()

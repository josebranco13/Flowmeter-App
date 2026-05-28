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

        if self.screen == "MOLD" and char and char.isalnum():
            self.add_char(char.upper())
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
        elif self.screen == "MOLD_SIDE":
            if self.mold_side_options:
                self.mold_side_dropdown_open = True
                self.selected_mold_side_index = (
                    self.selected_mold_side_index + delta
                ) % len(self.mold_side_options)
                self.show_mold_side()
        elif self.screen == "CIRCUIT_RESULTS":
            records = self.measurements_for_side(self.current_side)
            if records:
                self.selected_result_index = (
                    self.selected_result_index + delta
                ) % len(records)
                self.show_circuit_results()
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
            self.selected_index = (self.selected_index + delta) % len(self.get_send_options())
            if not self.update_option_selection():
                self.show_send_data()

    def move_diameter_selection(self, delta: int) -> None:
        if not self.diameter_options:
            return

        self.selected_index = (self.selected_index + delta) % len(self.diameter_options)

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
            self.input_value = (self.input_value + char)[:3]
            if not self.update_field_value("input_value", self.input_value):
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
        elif self.screen == "MOLD_SIDE":
            self.clear_mold_side_selection()
        elif self.screen == "MEASURE":
            self.restart_current_measurement()
        elif self.screen == "MEASUREMENT_RESULT":
            self.remeasure_current_circuit()
        elif self.screen == "CIRCUIT_RESULTS":
            self.remeasure_selected_result()
        elif self.screen == "CIRCUITS":
            self.input_value = self.input_value[:-1]
            if not self.update_field_value("input_value", self.input_value):
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
        elif self.screen == "MOLD_SIDE":
            self.clear_mold_side_selection()
        elif self.screen == "MEASURE":
            self.restart_current_measurement()
        elif self.screen == "MEASUREMENT_RESULT":
            self.remeasure_current_circuit()
        elif self.screen == "CIRCUIT_RESULTS":
            self.remeasure_selected_result()
        elif self.screen == "CIRCUITS":
            self.input_value = ""
            if not self.update_field_value("input_value", ""):
                self.show_circuits()

    def select(self) -> None:
        if self.screen == "LOGIN":
            self.select_login_operator()
            return

        if self.screen == "MOLD_SIDE":
            self.select_mold_side()
            return

        if self.screen == "CIRCUIT_START":
            self.start_current_flow_measurement()
            return

        if self.screen == "MEASURE":
            self.stop_current_measurement()
            return

        if self.screen in ("MEASUREMENT_RESULT", "CIRCUIT_RESULTS"):
            return

        if self.screen == "SIDE_COMPLETE":
            self.save_session()
            return

        if self.screen == "SEND_REVIEW":
            return

        self.confirm()

    def select_mold_side(self) -> None:
        if not self.mold_side_dropdown_open:
            self.mold_side_dropdown_open = True
            self.show_mold_side()
            return

        assert self.session is not None
        self.session.lado_molde = self.mold_side_options[self.selected_mold_side_index]
        self.mold_side_dropdown_open = False
        self.status_text = ""
        self.show_mold_side()

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
            self.selected_menu_option = option
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
            self.session.molde = self.format_mold_code(self.input_value)
            self.session.lado_molde = ""
            self.input_value = ""
            self.status_text = ""
            self.selected_index = 0
            self.selected_mold_side_index = 0
            self.mold_side_dropdown_open = False
            self.show_mold_side()

        elif self.screen == "MOLD_SIDE":
            assert self.session is not None
            if not self.session.lado_molde:
                self.status_text = "Selecione o lado do molde."
                self.show_mold_side()
                return
            self.status_text = ""
            self.selected_index = 0
            self.show_diameter()

        elif self.screen == "DIAMETER":
            assert self.session is not None
            self.session.diametro_mm = self.diameter_options[self.selected_index]
            self.input_value = ""
            self.show_circuits()

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
            self.prepare_next_circuit_measurement()

        elif self.screen == "CIRCUITS":
            count = int(self.input_value or "0")
            if count <= 0:
                self.status_text = "Indique pelo menos 1 circuito."
                self.show_circuits()
                return
            assert self.session is not None
            self.session.circuitos_por_lado[self.session.lado_molde] = count
            self.save_session()
            self.status_text = ""
            self.input_value = ""
            self.show_pressure()

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

        elif self.screen == "CIRCUIT_START":
            self.start_current_flow_measurement()

        elif self.screen == "MEASUREMENT_RESULT":
            self.advance_after_measurement_result()

        elif self.screen == "CIRCUIT_RESULTS":
            self.show_side_complete()

        elif self.screen == "SIDE_COMPLETE":
            self.measure_next_side()

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
                self.status_text = ""
                self.selected_index = 0
                self.show_send_review()
            elif self.selected_index == 1:
                count = self.simulate_send_pending_sessions()
                self.status_text = f"Envio concluído. Sessões enviadas: {count}."
                self.selected_index = 0
                self.show_send_data()
            else:
                self.selected_index = 0
                self.show_menu()

        elif self.screen == "SEND_REVIEW":
            count = self.simulate_send_pending_sessions()
            self.status_text = f"Envio concluído. Sessões enviadas: {count}."
            self.selected_index = 0
            self.show_send_data()

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
        elif self.screen == "MOLD_SIDE":
            self.input_value = self.mold_input_from_code(self.session.molde) if self.session else ""
            self.mold_side_dropdown_open = False
            self.show_mold()
        elif self.screen == "DIAMETER":
            self.mold_side_dropdown_open = False
            self.show_mold_side()
        elif self.screen == "PRESSURE":
            if self.session is not None:
                self.input_value = str(
                    self.session.circuitos_por_lado.get(self.session.lado_molde, "")
                )
            self.show_circuits()
        elif self.screen == "CIRCUITS":
            self.input_value = ""
            self.show_diameter()
        elif self.screen == "SIDE":
            self.show_circuits()
        elif self.screen == "CIRCUIT_START":
            self.input_value = str(self.session.pressao_entrada_bar) if self.session else ""
            self.show_pressure()
        elif self.screen == "MEASURE":
            self.status_text = "Medição cancelada. Nenhum valor foi guardado."
            self.measurement_running = False
            self.samples = []
            self.show_circuit_start()
        elif self.screen == "MEASUREMENT_RESULT":
            self.show_circuit_start()
        elif self.screen == "CIRCUIT_RESULTS":
            self.show_measurement_result()
        elif self.screen == "SIDE_COMPLETE":
            self.show_circuit_results()
        elif self.screen == "SEND_REVIEW":
            self.selected_index = 0
            self.show_send_data()
        elif self.screen in ("SUMMARY", "SEND"):
            self.show_menu()

    def refresh_current_screen(self) -> None:
        if self.screen in ("MOLD", "PRESSURE") and self.update_input_value_field():
            return

        if self.screen == "MOLD":
            self.show_mold()
        elif self.screen == "PRESSURE":
            self.show_pressure()

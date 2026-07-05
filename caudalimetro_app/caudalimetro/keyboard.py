from __future__ import annotations

import tkinter as tk


class KeyboardMixin:
    def restore_keyboard_focus(self, _event: tk.Event | None = None) -> None:
        try:
            self.focus_set()
        except tk.TclError:
            return

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

        if self.screen == "LOGIN" and char:
            if (
                char.isdigit()
                and self.login_active_field == 1
                and self.operator_id
                and self.operator_id in self.operator_options
                and not self.operator_list_open
            ):
                self.add_char(char)
            return

        if self.screen == "ADMIN_ADD_OPERATOR" and char and char.isalnum():
            self.add_char(char.upper())
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
                status_was_visible = bool(self.status_text)
                self.status_text = ""
                self.refresh_operator_options()
                if self.operator_options:
                    self.operator_selected_index = (
                        self.operator_selected_index + delta
                    ) % len(self.operator_options)
                visible_options = self.visible_operator_options()
                if (
                    not status_was_visible
                    and self.update_operator_options(visible_options)
                ):
                    return

                self.show_login()
                return

            self.login_active_field = (self.login_active_field + delta) % 3
            self.operator_list_open = False
            self.show_login()
        elif self.screen == "MENU":
            self.selected_index = (self.selected_index + delta) % len(self.menu_options)
            if not self.update_option_selection():
                self.show_menu()
        elif self.screen == "ADMIN_MENU":
            self.selected_index = (self.selected_index + delta) % 2
            if not self.update_option_selection():
                self.show_admin_menu()
        elif self.screen == "DIAMETER":
            self.move_diameter_selection(delta)
            if not self.update_diameter_selection():
                self.show_diameter()
        elif self.screen == "CIRCUITS":
            if self.session and self.circuit_start_required_for_side(self.session.lado_molde):
                self.circuit_active_field = (self.circuit_active_field + delta) % 2
                self.show_circuits()
        elif self.screen == "MOLD_SIDE":
            if self.mold_side_dropdown_open and self.mold_side_options:
                self.mold_side_dropdown_open = True
                self.selected_mold_side_index = (
                    self.selected_mold_side_index + delta
                ) % len(self.mold_side_options)
            else:
                self.mold_side_dropdown_open = False
                self.selected_index = (self.selected_index + delta) % 2
            self.show_mold_side()
        elif self.screen == "MEASUREMENT_RESULT":
            self.selected_index = (self.selected_index + delta) % 2
            self.show_measurement_result()
        elif self.screen == "CIRCUIT_RESULTS":
            if self.result_editing:
                return
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
        elif self.screen == "SEND_REVIEW":
            if self.move_send_review_selection(delta):
                self.show_send_review()
        elif self.screen == "ADMIN_OPERATORS":
            operators = self.managed_operator_options()
            if operators:
                self.selected_admin_operator_index = (
                    self.selected_admin_operator_index + delta
                ) % len(operators)
                if not self.update_admin_operator_selection():
                    self.show_admin_operators()
        elif self.screen == "ADMIN_ADD_OPERATOR":
            self.admin_add_active_field = (self.admin_add_active_field + delta) % 2
            self.show_admin_add_operator()
        elif self.screen == "ADMIN_RESET_PASSWORD":
            return
        elif self.screen == "ADMIN_REMOVE_CONFIRM":
            return

    def move_diameter_selection(self, delta: int) -> None:
        if not self.diameter_options:
            return

        if len(self.diameter_options) == 5:
            vertical_order = [0, 3, 1, 4, 2]
            try:
                order_index = vertical_order.index(self.selected_index)
            except ValueError:
                order_index = 0

            step = 1 if delta > 0 else -1
            self.selected_index = vertical_order[
                (order_index + step) % len(vertical_order)
            ]
            return

        self.selected_index = (self.selected_index + delta) % len(self.diameter_options)

    def update_input_value_field(self) -> bool:
        return self.update_field_value("input_value", self.input_value)

    def active_circuit_input_key(self) -> str:
        if (
            self.session is not None
            and self.circuit_start_required_for_side(self.session.lado_molde)
            and self.circuit_active_field == 1
        ):
            return "start"
        return "count"

    def refresh_circuit_input_display(self) -> None:
        self.input_value = self.circuit_inputs.get("count", "")
        updated = self.update_field_value(
            "circuit_count",
            self.circuit_inputs.get("count", ""),
        )
        if self.session and self.circuit_start_required_for_side(self.session.lado_molde):
            updated = (
                self.update_field_value(
                    "circuit_start",
                    self.circuit_inputs.get("start", ""),
                )
                and updated
            )
        if not updated:
            self.show_circuits()

    def add_char(self, char: str) -> None:
        if self.screen == "LOGIN":
            if self.login_active_field == 0:
                return
            else:
                if (
                    not self.operator_id
                    or self.operator_id not in self.operator_options
                    or self.operator_list_open
                    or not char.isdigit()
                ):
                    return
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
            if not char.isdigit():
                return
            key = self.active_circuit_input_key()
            limit = 4 if key == "start" else 3
            self.circuit_inputs[key] = (self.circuit_inputs.get(key, "") + char)[:limit]
            self.refresh_circuit_input_display()
        elif self.screen == "CIRCUIT_RESULTS" and self.result_editing:
            if char == "." and "." in self.input_value:
                return
            self.input_value = (self.input_value + char)[:8]
            self.refresh_result_edit_display()
        elif self.screen == "ADMIN_ADD_OPERATOR":
            if self.admin_add_active_field == 0:
                self.admin_new_operator_name = (
                    self.admin_new_operator_name + char.upper()
                )[:20]
            elif char.isdigit():
                self.admin_new_operator_pin = (self.admin_new_operator_pin + char)[:4]
            self.refresh_admin_add_field()
        elif self.screen == "ADMIN_RESET_PASSWORD":
            if char.isdigit():
                self.admin_reset_operator_pin = (
                    self.admin_reset_operator_pin + char
                )[:4]
                self.refresh_admin_reset_field()

    def delete_one(self) -> None:
        if self.screen == "LOGIN":
            if self.operator_list_open:
                self.operator_list_open = False
                self.login_active_field = 1 if self.operator_id else 0
                self.show_login()
                return

            if self.login_active_field == 0:
                return
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
            if self.result_editing:
                self.input_value = self.input_value[:-1]
                self.refresh_result_edit_display()
            else:
                self.remeasure_selected_result()
        elif self.screen == "CIRCUITS":
            key = self.active_circuit_input_key()
            self.circuit_inputs[key] = self.circuit_inputs.get(key, "")[:-1]
            self.refresh_circuit_input_display()
        elif self.screen == "SIDE_COMPLETE":
            self.restart_current_side_measurements()
        elif self.screen == "SEND_REVIEW":
            if self.send_review_expanded_group_key is not None:
                self.delete_selected_pending_session()
            else:
                self.toggle_selected_pending_group()
        elif self.screen == "ADMIN_OPERATORS":
            self.remove_selected_admin_operator()
        elif self.screen == "ADMIN_ADD_OPERATOR":
            if self.admin_add_active_field == 0:
                self.admin_new_operator_name = self.admin_new_operator_name[:-1]
            else:
                self.admin_new_operator_pin = self.admin_new_operator_pin[:-1]
            self.refresh_admin_add_field()
        elif self.screen == "ADMIN_RESET_PASSWORD":
            self.admin_reset_operator_pin = self.admin_reset_operator_pin[:-1]
            self.refresh_admin_reset_field()
        elif self.screen == "ADMIN_REMOVE_CONFIRM":
            self.cancel_admin_operator_removal()

    def delete_all(self) -> None:
        if self.screen == "LOGIN":
            self.clear_login_values()
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
            if self.result_editing:
                self.input_value = ""
                self.refresh_result_edit_display()
            else:
                self.remeasure_selected_result()
        elif self.screen == "CIRCUITS":
            key = self.active_circuit_input_key()
            self.circuit_inputs[key] = ""
            self.refresh_circuit_input_display()
        elif self.screen == "SIDE_COMPLETE":
            self.restart_current_side_measurements()
        elif self.screen == "ADMIN_OPERATORS":
            self.remove_selected_admin_operator()
        elif self.screen == "ADMIN_ADD_OPERATOR":
            if self.admin_add_active_field == 0:
                self.admin_new_operator_name = ""
            else:
                self.admin_new_operator_pin = ""
            self.refresh_admin_add_field()
        elif self.screen == "ADMIN_RESET_PASSWORD":
            self.admin_reset_operator_pin = ""
            self.refresh_admin_reset_field()
        elif self.screen == "ADMIN_REMOVE_CONFIRM":
            self.cancel_admin_operator_removal()

    def select(self) -> None:
        if self.screen == "LOGIN":
            if self.login_active_field == 0:
                self.select_login_operator()
            elif self.login_active_field == 2:
                self.show_credits()
            return

        if self.screen == "MOLD_SIDE":
            if self.selected_index == 1 and not self.mold_side_dropdown_open:
                self.change_operator_from_mold_side()
                return
            self.select_mold_side()
            return

        if self.screen == "CIRCUITS":
            if (
                self.session is not None
                and self.circuit_start_required_for_side(self.session.lado_molde)
                and self.circuit_active_field == 0
            ):
                count = int(self.circuit_inputs.get("count") or self.input_value or "0")
                if count <= 0:
                    self.status_text = "Indique pelo menos 1 circuito."
                    self.show_circuits()
                    return
                self.status_text = ""
                self.circuit_active_field = 1
                self.show_circuits()
                return
            self.confirm()
            return

        if self.screen == "CIRCUIT_START":
            self.start_current_flow_measurement()
            return

        if self.screen == "MEASURE":
            self.stop_current_measurement()
            return

        if self.screen == "MEASUREMENT_RESULT":
            if self.selected_index == 1:
                self.highlight_current_measurement()
            return

        if self.screen == "CIRCUIT_RESULTS":
            if self.result_editing:
                self.save_selected_result_edit()
            else:
                self.edit_selected_result()
            return

        if self.screen == "SIDE_COMPLETE":
            self.save_session_and_return_to_login()
            return

        if self.screen == "SEND_REVIEW":
            if self.send_review_expanded_group_key is None:
                self.toggle_selected_pending_group_checkbox()
            return

        if self.screen == "ADMIN_OPERATORS":
            self.show_admin_add_operator()
            return

        if self.screen == "ADMIN_ADD_OPERATOR":
            self.save_admin_operator()
            return

        if self.screen == "ADMIN_RESET_PASSWORD":
            self.save_admin_reset_password()
            return

        if self.screen == "ADMIN_REMOVE_CONFIRM":
            self.confirm_admin_operator_removal()
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
        self.refresh_operator_options()
        if not self.operator_options:
            self.login_active_field = 0
            self.operator_list_open = False
            self.status_text = "Não existem operadores configurados."
            self.show_login()
            return

        if self.operator_list_open:
            selected_operator = self.operator_options[self.operator_selected_index]
            if selected_operator != self.operator_id:
                self.pin = ""
            self.operator_id = selected_operator
            self.operator_list_open = False
            self.login_active_field = 1
            self.status_text = ""
            self.show_login()
            return

        if self.operator_id in self.operator_options:
            self.operator_selected_index = self.operator_options.index(self.operator_id)
        else:
            self.operator_selected_index = 0
        self.login_active_field = 0
        self.operator_list_open = True
        self.status_text = ""
        self.show_login()

    def confirm(self) -> None:
        if self.screen == "LOGIN":
            if self.login_active_field == 2:
                self.show_credits()
                return

            self.operator_list_open = False
            self.operator_id = self.normalize_operator_name(self.operator_id)
            if not self.operator_id or not self.pin:
                self.status_text = "Preencha o operador e o PIN."
                self.show_login()
                return
            self.refresh_operator_options()
            if self.operator_id not in self.operator_options:
                self.status_text = "Selecione um operador válido."
                self.show_login()
                return
            if not self.operator_pin_matches(self.operator_id, self.pin):
                self.status_text = "PIN incorreto para este operador."
                self.pin = ""
                self.show_login()
                return
            self.status_text = ""
            if self.operator_id == "ADMIN":
                self.admin_operator_input = ""
                self.selected_admin_operator_index = 0
                self.selected_index = 0
                self.show_admin_menu()
            else:
                self.show_menu()

        elif self.screen == "MENU":
            option = self.menu_options[self.selected_index]
            self.selected_menu_option = option
            if option == "Medir caudal":
                self.start_new_session()
                self.input_value = ""
                self.show_mold()
            else:
                self.status_text = ""
                self.selected_index = 0
                self.send_review_first_row = 0
                self.send_review_expanded_group_key = None
                self.send_review_selected_measurement_ref = None
                self.checked_send_review_group_keys().clear()
                self.show_send_review()

        elif self.screen == "ADMIN_MENU":
            if self.selected_index == 0:
                self.selected_admin_operator_index = 0
                self.show_admin_operators()
            else:
                self.status_text = ""
                self.selected_index = 0
                self.send_review_first_row = 0
                self.send_review_expanded_group_key = None
                self.send_review_selected_measurement_ref = None
                self.checked_send_review_group_keys().clear()
                self.show_send_review()

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
            if self.selected_index == 1 and not self.mold_side_dropdown_open:
                self.change_operator_from_mold_side()
                return
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
            self.circuit_active_field = 0
            self.circuit_inputs = {"count": "", "start": ""}
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
            assert self.session is not None
            side = self.session.lado_molde
            count = int(self.circuit_inputs.get("count") or self.input_value or "0")
            if count <= 0:
                self.status_text = "Indique pelo menos 1 circuito."
                self.show_circuits()
                return
            if self.circuit_start_required_for_side(side):
                start = int(self.circuit_inputs.get("start") or "0")
                if start <= 0:
                    self.status_text = "Indique o numero do circuito inicial."
                    self.circuit_active_field = 1
                    self.show_circuits()
                    return
            else:
                start = 1

            self.session.circuitos_por_lado[side] = count
            self.session.circuitos_inicio_por_lado[side] = start
            self.save_session()
            self.status_text = ""
            self.input_value = ""
            self.circuit_active_field = 0
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
            if self.result_editing and not self.save_selected_result_edit():
                return
            self.show_side_complete()

        elif self.screen == "SIDE_COMPLETE":
            self.save_session_and_return_to_login()

        elif self.screen == "SUMMARY":
            if self.selected_index == 0:
                self.reset_operator_only()
                self.show_menu()
            elif self.selected_index == 1:
                self.status_text = ""
                self.selected_index = 0
                self.send_review_first_row = 0
                self.send_review_expanded_group_key = None
                self.send_review_selected_measurement_ref = None
                self.checked_send_review_group_keys().clear()
                self.show_send_review()
            else:
                self.logout()
                self.show_login()

        elif self.screen == "SEND_REVIEW":
            self.confirm_checked_pending_sessions()
            return

        elif self.screen == "ADMIN_OPERATORS":
            self.reset_selected_admin_operator_password()

        elif self.screen == "ADMIN_ADD_OPERATOR":
            self.cancel_admin_add_operator()

        elif self.screen == "ADMIN_RESET_PASSWORD":
            self.cancel_admin_reset_password()

        elif self.screen == "ADMIN_REMOVE_CONFIRM":
            return

    def go_back(self) -> None:
        if self.screen == "LOGIN":
            self.clear_login_values()
            return
        if self.screen == "MENU":
            self.logout_to_login()
            return
        if self.screen == "ADMIN_MENU":
            self.logout_to_login()
            return
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
                side = self.session.lado_molde
                self.circuit_inputs = {
                    "count": str(self.session.circuitos_por_lado.get(side, "")),
                    "start": str(self.session.circuitos_inicio_por_lado.get(side, 1)),
                }
                self.input_value = self.circuit_inputs["count"]
                self.circuit_active_field = 0
            self.show_circuits()
        elif self.screen == "CIRCUITS":
            self.input_value = ""
            self.circuit_inputs = {"count": "", "start": ""}
            self.circuit_active_field = 0
            self.show_diameter()
        elif self.screen == "SIDE":
            self.show_circuits()
        elif self.screen == "CIRCUIT_START":
            self.input_value = str(self.session.pressao_entrada_bar) if self.session else ""
            self.show_pressure()
        elif self.screen == "MEASURE":
            if self.measurement_reviewing_saved_result:
                self.measurement_reviewing_saved_result = False
                self.measurement_running = False
                self.show_circuit_start()
                return
            self.status_text = "Medição cancelada. Nenhum valor foi guardado."
            self.measurement_running = False
            self.samples = []
            self.show_circuit_start()
        elif self.screen == "MEASUREMENT_RESULT":
            self.measurement_reviewing_saved_result = True
            self.measurement_running = False
            self.show_measurement()
        elif self.screen == "CIRCUIT_RESULTS":
            if self.result_editing:
                self.result_editing = False
                self.input_value = ""
                self.status_text = ""
                self.show_circuit_results()
            else:
                self.show_measurement_result()
        elif self.screen == "SIDE_COMPLETE":
            self.show_circuit_results()
        elif self.screen == "SEND_REVIEW":
            self.status_text = ""
            if self.send_review_expanded_group_key is not None:
                self.send_review_expanded_group_key = None
                self.send_review_selected_measurement_ref = None
                self.send_review_first_row = 0
                self.show_send_review()
                return
            self.selected_index = 0
            self.send_review_first_row = 0
            self.send_review_expanded_group_key = None
            self.send_review_selected_measurement_ref = None
            self.checked_send_review_group_keys().clear()
            if self.operator_id == "ADMIN":
                self.show_admin_menu()
            else:
                self.show_menu()
        elif self.screen == "ADMIN_OPERATORS":
            self.selected_index = 0
            self.show_admin_menu()
        elif self.screen == "ADMIN_ADD_OPERATOR":
            self.cancel_admin_add_operator()
        elif self.screen == "ADMIN_RESET_PASSWORD":
            self.cancel_admin_reset_password()
        elif self.screen == "ADMIN_REMOVE_CONFIRM":
            self.cancel_admin_operator_removal()
        elif self.screen == "CREDITS":
            self.show_login()
        elif self.screen == "SUMMARY":
            self.show_menu()

    def refresh_current_screen(self) -> None:
        if self.screen in ("MOLD", "PRESSURE") and self.update_input_value_field():
            return

        if self.screen == "MOLD":
            self.show_mold()
        elif self.screen == "PRESSURE":
            self.show_pressure()

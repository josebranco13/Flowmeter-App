from __future__ import annotations

import tkinter as tk

from .config import BLUE, GREEN, GREY, PANEL_BG, PANEL_FG, WHITE


class ScreensMixin:
    def show_login(self) -> None:
        self.screen = "LOGIN"
        self.refresh_operator_options()
        panel = self.build_base("", "")
        tk.Label(
            panel,
            text="Identificação do operador",
            bg=PANEL_BG,
            fg=PANEL_FG,
            font=("Arial", 18, "bold"),
        ).pack(pady=(30, 16))
        self.field_value_labels["operator_id"] = self.field_row(
            panel,
            "Nº operador",
            self.operator_id,
            self.login_active_field == 0,
        )

        if self.operator_list_open:
            visible_options = self.visible_operator_options()
            self.operator_visible_indices = [index for index, _ in visible_options]
            for index, operator in visible_options:
                self.option_row(
                    panel,
                    f"Operador {operator}",
                    index == self.operator_selected_index,
                )
        else:
            self.operator_visible_indices = []
            self.field_value_labels["pin"] = self.field_row(
                panel,
                "PIN",
                "●" * len(self.pin),
                self.login_active_field == 1,
            )

        help_text = (
            "Use ↑/↓ para escolher e prima Selecionar."
            if self.operator_list_open
            else "No campo do operador, prima Selecionar para abrir a lista."
        )
        tk.Label(
            panel,
            text=help_text,
            bg=PANEL_BG,
            fg="#555555",
            font=("Arial", 11),
        ).pack(pady=16)

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
        panel = self.build_base("Identificação do molde", "3/8")
        tk.Label(
            panel,
            text="Indique o molde a medir",
            bg=PANEL_BG,
            fg=PANEL_FG,
            font=("Arial", 18, "bold"),
        ).pack(pady=(46, 24))
        self.field_value_labels["input_value"] = self.field_row(
            panel,
            "Molde",
            self.input_value,
            True,
        )
        tk.Label(
            panel,
            text="Pode introduzir números pelo teclado físico.",
            bg=PANEL_BG,
            fg="#555555",
            font=("Arial", 11),
        ).pack(pady=18)

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
            label.grid(row=i // 4, column=i % 4, padx=7, pady=7)
            self.diameter_labels.append(label)

        tk.Label(
            panel,
            text="Use ↑/↓ para alterar a opção e confirme.",
            bg=PANEL_BG,
            fg="#555555",
            font=("Arial", 11),
        ).pack(pady=12)

    def show_pressure(self) -> None:
        self.screen = "PRESSURE"
        panel = self.build_base("Pressão à entrada", "5/8")
        pressure_value = f"{self.input_value} bar" if self.input_value else ""
        tk.Label(
            panel,
            text="Indique a pressão de entrada",
            bg=PANEL_BG,
            fg=PANEL_FG,
            font=("Arial", 18, "bold"),
        ).pack(pady=(46, 24))
        self.field_value_labels["input_value"] = self.field_row(
            panel,
            "Pressão",
            pressure_value,
            True,
        )
        tk.Label(
            panel,
            text="Exemplo: 2.5 bar",
            bg=PANEL_BG,
            fg="#555555",
            font=("Arial", 11),
        ).pack(pady=18)

    def show_circuits(self) -> None:
        self.screen = "CIRCUITS"
        panel = self.build_base("Circuitos por lado", "6/8")
        tk.Label(
            panel,
            text="Quantos circuitos existem em cada lado?",
            bg=PANEL_BG,
            fg=PANEL_FG,
            font=("Arial", 18, "bold"),
        ).pack(pady=(38, 22))
        self.field_value_labels["circuit_A"] = self.field_row(
            panel,
            "Lado A",
            self.circuit_inputs["A"],
            self.circuit_active_field == 0,
        )
        self.field_value_labels["circuit_B"] = self.field_row(
            panel,
            "Lado B",
            self.circuit_inputs["B"],
            self.circuit_active_field == 1,
        )
        tk.Label(
            panel,
            text="Use ↑/↓ para alternar entre Lado A e Lado B.",
            bg=PANEL_BG,
            fg="#555555",
            font=("Arial", 11),
        ).pack(pady=18)

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
        panel = self.build_base("Medição de caudal", "8/8")
        assert self.session is not None
        tk.Label(
            panel,
            text=f"Lado {self.current_side} | Circuito {self.current_circuit}",
            bg=PANEL_BG,
            fg=PANEL_FG,
            font=("Arial", 20, "bold"),
        ).pack(pady=(20, 6))
        tk.Label(
            panel,
            text=(
                f"Molde {self.session.molde} | Ø {self.session.diametro_mm} mm | "
                f"{self.session.pressao_entrada_bar:.2f} bar"
            ),
            bg=PANEL_BG,
            fg="#555555",
            font=("Arial", 12),
        ).pack(pady=(0, 8))

        cards = tk.Frame(panel, bg=PANEL_BG)
        cards.pack(pady=10)
        self.measure_labels = {}
        items = [
            ("Caudal atual", "current"),
            ("Mínimo", "min"),
            ("Médio", "avg"),
            ("Máximo", "max"),
        ]
        for idx, (title, key) in enumerate(items):
            card = tk.Frame(cards, bg=WHITE, highlightthickness=1, highlightbackground="#c8c8c8")
            card.grid(row=idx // 2, column=idx % 2, padx=10, pady=8, sticky="nsew")
            tk.Label(
                card,
                text=title,
                bg=WHITE,
                fg="#555555",
                font=("Arial", 12),
                width=19,
            ).pack(pady=(10, 2))
            value_label = tk.Label(
                card,
                text="-- L/min",
                bg=WHITE,
                fg=BLUE if key == "current" else PANEL_FG,
                font=("Arial", 20, "bold"),
            )
            value_label.pack(pady=(0, 10))
            self.measure_labels[key] = value_label

        bottom = tk.Frame(panel, bg=PANEL_BG)
        bottom.pack(pady=(2, 0))
        tk.Label(bottom, text="Amostras:", bg=PANEL_BG, fg="#555555", font=("Arial", 11)).pack(
            side="left"
        )
        sample_label = tk.Label(bottom, text="0", bg=PANEL_BG, fg=PANEL_FG, font=("Arial", 11, "bold"))
        sample_label.pack(side="left", padx=4)
        self.measure_labels["samples"] = sample_label

        tk.Label(
            panel,
            text="Prima Confirmar para concluir e guardar este circuito.",
            bg=PANEL_BG,
            fg="#555555",
            font=("Arial", 11),
        ).pack(pady=6)

        self.after(250, self.update_measurement_values)

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

        options = ["Enviar agora", "Voltar ao menu"]
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

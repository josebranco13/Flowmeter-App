from __future__ import annotations

import os
import tkinter as tk
from typing import Any

#novo
from PIL import Image, ImageTk

from .config import (
    APP_HEIGHT,
    APP_WIDTH,
    BLUE,
    BLACK,
    DIAMETER_LABELS,
    GREEN,
    GREY,
    FOOTER_FONT_SIZE,
    PANEL_BG,
    PANEL_FG,
    RED,
    RESULTS_TABLE_FONT_SIZE,
    TABLE_FONT_SIZE,
    WHITE,
)
from .email_sender import (
    load_email_config,
    send_all_exports_email_async,
    send_selected_export_email_async,
)


class ScreensMixin:
    @staticmethod
    def admin_menu_options() -> tuple[str, ...]:
        return ("Operadores", "Exportar dados", "Registos Exportados")

    def show_splash(self) -> None:
        self.screen = "SPLASH"
        self.clear() 
        
        # The main background frame that fills the whole window
        splash_frame = tk.Frame(self, bg=WHITE)
        splash_frame.pack(fill="both", expand=True)
        
        # A container frame to keep the text and image grouped together.
        # packing it with expand=True (but no fill) centers it perfectly in the middle.
        content_container = tk.Frame(splash_frame, bg=WHITE)
        content_container.pack(expand=True) 

        # --- Add Text (Packed first so it sits on top) ---
        tk.Label(
            content_container,
            text="Carregando...", 
            bg=WHITE,
            fg=BLACK, 
            font=("Arial", 24, "bold")
        ).pack(side="top", pady=(0, 20)) # pady adds a 20px gap below the text

        # --- Add Image (Packed second so it sits below the text) ---
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            
            # 2. Join that folder path with your image name
            aha_path = os.path.join(current_dir, "aha.png")
            ipl_path = os.path.join(current_dir, "ipl.png")
            
            # 3. Open the image using the absolute path
            aha_image = Image.open(aha_path)
            ipl_image = Image.open(ipl_path)
            # We removed the image.resize() line so it uses its native resolution
            self.splash_img = ImageTk.PhotoImage(aha_image)
            self.splash_img2 = ImageTk.PhotoImage(ipl_image)
            tk.Label(content_container, image=self.splash_img, bg=WHITE).pack(side="left")
            tk.Label(content_container, image=self.splash_img2, bg=WHITE).pack(side="right")
        except Exception as e:
            print(f"Could not load image: {e}")

        # Start the fade-in animation
        self._fade_in_splash()

    def _fade_in_splash(self, alpha: float = 0.0) -> None:
        alpha += 0.05
        if alpha < 1.0:
            self.attributes("-alpha", alpha)
            self.after(30, self._fade_in_splash, alpha)
        else:
            self.attributes("-alpha", 1.0)
            # Wait for 1.5 seconds (1500 ms) before fading out
            self.after(1500, self._fade_out_splash)

    def _fade_out_splash(self, alpha: float = 1.0) -> None:
        alpha -= 0.05
        if alpha > 0.0:
            self.attributes("-alpha", alpha)
            self.after(30, self._fade_out_splash, alpha)
        else:
            self.attributes("-alpha", 0.0)
            # Once fully invisible, load the first real screen
            self.show_login()
            # Fade the main screen back in
            self._fade_in_main()

    def _fade_in_main(self, alpha: float = 0.0) -> None:
        alpha += 0.05
        if alpha < 1.0:
            self.attributes("-alpha", alpha)
            self.after(30, self._fade_in_main, alpha)
        else:
            self.attributes("-alpha", 1.0)

    def show_login(self) -> None:
        self.screen = "LOGIN"
        self.refresh_operator_options()
        self.clear()
        self.option_labels = []
        self.diameter_labels = []
        self.field_value_labels = {}

        root = tk.Frame(self, bg=WHITE)
        root.pack(fill="both", expand=True)
        root.grid_columnconfigure(0, weight=1)
        root.grid_rowconfigure(0, weight=1)

        content = tk.Frame(root, bg=WHITE)
        content.grid(row=0, column=0, sticky="nsew")
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
                font=("Arial", 14, "bold"),
                wraplength=APP_WIDTH - 120,
                justify="center",
            ).grid(row=2, column=0, pady=14, sticky="n")

        action_area = tk.Frame(root, bg=WHITE)
        action_area.grid(row=1, column=0, sticky="ew")

        if not self.operator_list_open:
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

        # 1. BUILD THE FOOTER FIRST
        self.build_login_footer(
            root,
            black_text="Voltar atrás",
            black_command=self.close_credits,
            red_text="-",
            red_command=self.no_action,
        )

        # 2. CREATE A CANVAS FOR SCROLLING
        canvas = tk.Canvas(root, bg=WHITE, bd=0, highlightthickness=0)
        self.credits_canvas = canvas
        canvas.pack(side="top", fill="both", expand=True)

        # 3. CREATE THE CONTENT FRAME INSIDE THE CANVAS
        content = tk.Frame(canvas, bg=WHITE)
        
        # FIX 1: Change anchor to "nw" (North-West) so (0,0) is the top-left corner
        canvas_window = canvas.create_window((0, 0), window=content, anchor="nw")

        def configure_canvas(event):
            canvas.itemconfig(canvas_window, width=event.width)
        
        def configure_content(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            
        canvas.bind("<Configure>", configure_canvas)
        content.bind("<Configure>", configure_content)

        # 4. ADD YOUR TEXT LABELS
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
                "Eng. João Godinho\n"
                "Eng. João Almeida\n"
                "Eng. Adriano Gomes"
            ),
            bg=WHITE,
            fg=PANEL_FG,
            font=("Arial", 16),
            justify="center",
        ).pack(side="top", pady=(10, 40)) 

    def scroll_credits(self, delta: int) -> bool:
        if self.screen != "CREDITS":
            return False

        canvas = getattr(self, "credits_canvas", None)
        if canvas is None:
            return False

        try:
            if not canvas.winfo_exists():
                return False
            canvas.yview_scroll(delta, "units")
        except tk.TclError:
            return False

        return True

    def close_credits(self) -> None:
        self.credits_canvas = None
        self.login_active_field = 0
        self.operator_list_open = False
        self.status_text = ""
        self.show_login()

    def build_login_footer(
        self,
        parent: tk.Widget,
        black_text: str = "Apagar tudo",
        black_command=None,
        red_text: str = "Apagar",
        red_command=None,
    ) -> None:
        footer = tk.Frame(parent, bg=WHITE)
        footer.pack(side="bottom", fill="x")

        black_command = black_command or self.delete_all
        red_command = red_command or self.delete_one
        buttons = [
            (black_text, "#303030", WHITE, black_command),
            (red_text, RED, PANEL_FG, red_command),
            ("Selecionar", GREEN, PANEL_FG, self.select),
            ("Confirmar", BLUE, PANEL_FG, self.confirm),
        ]
        button_wrap_length = APP_WIDTH // len(buttons) - 16
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
                font=("Arial", FOOTER_FONT_SIZE),
                wraplength=button_wrap_length,
                justify="center",
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
        height = self.winfo_height()
        if height <= 1:
            height = APP_HEIGHT

        if height >= 900:
            count = 12
        elif height >= 700:
            count = 8
        else:
            count = 6

        if self.status_text:
            count -= 1

        return max(4, count)

    def show_admin_menu(self) -> None:
        self.screen = "ADMIN_MENU"
        options = self.admin_menu_options()
        self.selected_index = min(self.selected_index, len(options) - 1)
        panel = self.build_base(
            "Admin",
            "",
            back_text="Logout",
            back_command=self.logout_to_login,
            delete_text=None,
            center_title=True,
        )
        panel.configure(bg=WHITE)

        menu_content = tk.Frame(panel, bg=WHITE)
        menu_content.pack(expand=True, anchor="center")

        for i, option in enumerate(options):
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

    def show_exported_records(self) -> None:
        self.screen = "EXPORTED_RECORDS"
        records = self.load_exported_pdf_records()
        total_measurements = sum(int(item.get("medicoes") or 0) for item in records)
        panel = self.build_base(
            "",
            "",
            back_text="Voltar",
            back_command=self.show_admin_menu,
            delete_text="Apagar",
            delete_command=self.delete_selected_exported_record,
            select_text="Enviar selecionado",
            select_command=self.email_selected_exported_record,
            confirm_text="Enviar todos",
            confirm_command=self.email_all_exported_records,
        )
        panel.configure(bg=WHITE)

        tk.Label(
            panel,
            text="Registos Exportados",
            bg=WHITE,
            fg=PANEL_FG,
            font=("Arial", 18, "bold"),
        ).pack(pady=(18, 6))
        tk.Label(
            panel,
            text=(
                f"Ficheiros: {len(records)} | Moldes: {len(records)} | "
                f"Medições: {total_measurements}"
            ),
            bg=WHITE,
            fg=BLUE if records else GREEN,
            font=("Arial", 14, "bold"),
        ).pack(pady=(0, 12))

        if not records:
            self.selected_exported_record_index = 0
            self.exported_records_first_row = 0
            tk.Label(
                panel,
                text="Não existem ficheiros PDF exportados.",
                bg=WHITE,
                fg="#555555",
                font=("Arial", 14),
            ).pack(pady=22)
            return

        self.selected_exported_record_index = max(
            0,
            min(
                getattr(self, "selected_exported_record_index", 0),
                len(records) - 1,
            ),
        )
        max_rows = self.exported_records_visible_row_count()
        first_visible_row = self.exported_records_first_row_for_selection(
            records,
            max_rows,
        )
        self.exported_records_first_row = first_visible_row
        visible_records = records[first_visible_row : first_visible_row + max_rows]

        table_area = tk.Frame(panel, bg=WHITE)
        table_area.pack(fill="x", padx=4, pady=(0, 0))
        table = tk.Frame(table_area, bg=WHITE)
        table.pack(side="left", fill="x", expand=True)
        self.bind_exported_records_scroll(table_area)
        self.bind_exported_records_scroll(table)
        headers = [
            ("Data", 15),
            ("Operador", 16),
            ("Molde", 11),
            ("Nome do ficheiro", 28),
            ("Tamanho", 10),
        ]
        for col, (header, width) in enumerate(headers):
            table.grid_columnconfigure(col, weight=width)
            header_label = tk.Label(
                table,
                text=header,
                bg="#374151",
                fg=WHITE,
                font=("Arial", TABLE_FONT_SIZE, "bold"),
                width=width,
                pady=4,
            )
            header_label.grid(row=0, column=col, padx=1, sticky="ew")
            self.bind_exported_records_scroll(header_label)

        for row_index, item in enumerate(visible_records, start=1):
            item_index = first_visible_row + row_index - 1
            is_selected = item_index == self.selected_exported_record_index
            bg = BLUE if is_selected else WHITE
            fg = WHITE if is_selected else PANEL_FG
            font_weight = "bold" if is_selected else "normal"
            values = [
                item["data"],
                self.short_table_text(item["operador"], 16),
                self.short_table_text(item["molde"], 11),
                self.short_table_text(item["ficheiro"], 28),
                self.format_file_size(item["tamanho_bytes"]),
            ]
            for col, value in enumerate(values):
                cell = tk.Label(
                    table,
                    text=value,
                    bg=bg,
                    fg=fg,
                    font=("Arial", TABLE_FONT_SIZE, font_weight),
                    width=headers[col][1],
                    pady=4,
                )
                cell.bind(
                    "<ButtonRelease-1>",
                    lambda _event, index=item_index: self.select_exported_record(index),
                )
                self.bind_exported_records_scroll(cell)
                cell.grid(row=row_index, column=col, padx=1, pady=1, sticky="ew")

        if len(records) > max_rows:
            scrollbar = tk.Frame(table_area, bg="#d7d7d7", width=22)
            scrollbar.pack(side="right", fill="y", padx=(8, 0))
            scrollbar.pack_propagate(False)
            self.bind_exported_records_scroll(scrollbar)

            visible_fraction = max(0.12, min(1.0, len(visible_records) / len(records)))
            max_start = max(len(records) - len(visible_records), 1)
            thumb_top = (first_visible_row / max_start) * (1.0 - visible_fraction)
            tk.Frame(scrollbar, bg="#555555").place(
                relx=0.5,
                rely=thumb_top,
                anchor="n",
                relwidth=0.5,
                relheight=visible_fraction,
            )

    def exported_records_visible_row_count(self) -> int:
        height = self.winfo_height()
        if height <= 1:
            height = APP_HEIGHT

        if height >= 900:
            return 14
        if height >= 700:
            return 10
        return 7

    @staticmethod
    def clamp_exported_records_first_row(
        records: list[dict[str, Any]],
        first_row: int,
        max_rows: int,
    ) -> int:
        max_start = max(len(records) - max_rows, 0)
        return max(0, min(first_row, max_start))

    def exported_records_first_row_for_selection(
        self,
        records: list[dict[str, Any]],
        max_rows: int,
    ) -> int:
        if not records:
            return 0

        selected_index = max(
            0,
            min(
                getattr(self, "selected_exported_record_index", 0),
                len(records) - 1,
            ),
        )
        first_row = self.clamp_exported_records_first_row(
            records,
            int(getattr(self, "exported_records_first_row", 0)),
            max_rows,
        )
        visible_last_row = first_row + max_rows - 1
        if selected_index < first_row:
            return self.clamp_exported_records_first_row(records, selected_index, max_rows)
        if selected_index > visible_last_row:
            return self.clamp_exported_records_first_row(
                records,
                selected_index - max_rows + 1,
                max_rows,
            )
        return first_row

    def bind_exported_records_scroll(self, widget: tk.Widget) -> None:
        widget.bind("<MouseWheel>", self.on_exported_records_mousewheel, add="+")
        widget.bind("<Button-4>", self.on_exported_records_mousewheel, add="+")
        widget.bind("<Button-5>", self.on_exported_records_mousewheel, add="+")

    def on_exported_records_mousewheel(self, event: tk.Event) -> str:
        if getattr(event, "num", None) == 4:
            delta = -1
        elif getattr(event, "num", None) == 5:
            delta = 1
        else:
            delta = -1 if getattr(event, "delta", 0) > 0 else 1

        if self.move_exported_record_selection(delta):
            self.show_exported_records()
        return "break"

    def move_exported_record_selection(self, delta: int) -> bool:
        records = self.load_exported_pdf_records()
        if not records:
            self.selected_exported_record_index = 0
            self.exported_records_first_row = 0
            return False

        self.selected_exported_record_index = (
            self.selected_exported_record_index + delta
        ) % len(records)
        max_rows = self.exported_records_visible_row_count()
        self.exported_records_first_row = self.exported_records_first_row_for_selection(
            records,
            max_rows,
        )
        return True

    def select_exported_record(self, index: int) -> None:
        records = self.load_exported_pdf_records()
        if not records:
            self.selected_exported_record_index = 0
            self.exported_records_first_row = 0
            self.show_exported_records()
            return

        self.selected_exported_record_index = max(0, min(index, len(records) - 1))
        max_rows = self.exported_records_visible_row_count()
        self.exported_records_first_row = self.exported_records_first_row_for_selection(
            records,
            max_rows,
        )
        self.show_exported_records()

    def selected_exported_record(self) -> dict[str, Any] | None:
        records = self.load_exported_pdf_records()
        if not records:
            self.selected_exported_record_index = 0
            self.exported_records_first_row = 0
            return None

        self.selected_exported_record_index = max(
            0,
            min(self.selected_exported_record_index, len(records) - 1),
        )
        return records[self.selected_exported_record_index]

    def delete_selected_exported_record(self) -> None:
        record = self.selected_exported_record()
        if record is None:
            self.status_text = "Nao existem ficheiros para apagar."
            self.show_exported_records()
            return

        success, message = self.delete_exported_pdf_record(record)
        self.status_text = message
        if success:
            remaining_records = self.load_exported_pdf_records()
            if remaining_records:
                self.selected_exported_record_index = min(
                    self.selected_exported_record_index,
                    len(remaining_records) - 1,
                )
            else:
                self.selected_exported_record_index = 0
                self.exported_records_first_row = 0
        self.show_exported_records()

    def _finish_email_send(self, success: bool, message: str) -> None:
        def update_status() -> None:
            self.email_send_in_progress = False
            self.status_text = message if success else f"Erro ao enviar email: {message}"
            if self.screen == "EXPORTED_RECORDS":
                self.show_exported_records()

        self.after(0, update_status)

    def email_selected_exported_record(self) -> None:
        if self.email_send_in_progress:
            self.status_text = "Já existe um envio de email em curso."
            self.show_exported_records()
            return

        record = self.selected_exported_record()
        if record is None:
            self.status_text = "Nao existem ficheiros para enviar."
            self.show_exported_records()
            return

        paths = self.exported_pdf_record_paths(record)
        if paths is None:
            self.status_text = "Registo invalido."
            self.show_exported_records()
            return

        attachments, error = self.exported_pdf_record_attachments(record)
        if error:
            self.status_text = error
            self.show_exported_records()
            return

        pdf_path, json_path = paths
        mold = str(record.get("molde") or "-")

        try:
            config = load_email_config()
        except Exception as exc:
            self.status_text = f"Configuração de email inválida: {exc}"
            self.show_exported_records()
            return

        self.email_send_in_progress = True
        self.status_text = "A enviar email..."
        self.show_exported_records()
        send_selected_export_email_async(
            config=config,
            pdf_path=pdf_path,
            json_path=json_path,
            molde=mold,
            on_result=self._finish_email_send,
        )

    def email_all_exported_records(self) -> None:
        if self.email_send_in_progress:
            self.status_text = "Já existe um envio de email em curso."
            self.show_exported_records()
            return

        records = self.load_exported_pdf_records()
        if not records:
            self.status_text = "Nao existem ficheiros para enviar."
            self.show_exported_records()
            return

        pairs = []
        for record in records:
            _attachments, error = self.exported_pdf_record_attachments(record)
            if error:
                self.status_text = error
                self.show_exported_records()
                return
            paths = self.exported_pdf_record_paths(record)
            if paths is None:
                self.status_text = "Registo invalido."
                self.show_exported_records()
                return
            pairs.append(paths)

        try:
            config = load_email_config()
        except Exception as exc:
            self.status_text = f"Configuração de email inválida: {exc}"
            self.show_exported_records()
            return

        self.email_send_in_progress = True
        self.status_text = "A enviar todos os ficheiros exportados..."
        self.show_exported_records()
        send_all_exports_email_async(
            config=config,
            pairs=pairs,
            on_result=self._finish_email_send,
        )

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
            confirm_text="Resetar Password",
            confirm_command=self.reset_selected_admin_operator_password,
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
                font=("Arial", 14, "bold"),
                wraplength=APP_WIDTH - 120,
                justify="center",
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
                font=("Arial", 14),
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
                font=("Arial", 14, "bold"),
                wraplength=APP_WIDTH - 120,
                justify="center",
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

    def reset_selected_admin_operator_password(self) -> None:
        operators = self.managed_operator_options()
        if not operators:
            self.status_text = "Nao existem operadores para resetar."
            self.show_admin_operators()
            return

        self.selected_admin_operator_index = min(
            self.selected_admin_operator_index,
            len(operators) - 1,
        )
        self.admin_reset_operator_name = operators[self.selected_admin_operator_index]
        self.admin_reset_operator_pin = ""
        self.status_text = ""
        self.show_admin_reset_password()

    def show_admin_reset_password(self) -> None:
        self.screen = "ADMIN_RESET_PASSWORD"
        reset_status_text = self.status_text
        self.status_text = ""
        panel = self.build_base(
            "Resetar password",
            "Admin",
            back_text="Voltar",
            back_command=self.cancel_admin_reset_password,
            delete_text="Apagar",
            delete_command=self.delete_one,
            select_text="Guardar",
            select_command=self.save_admin_reset_password,
            confirm_text="Sair",
            confirm_command=self.cancel_admin_reset_password,
        )
        self.status_text = reset_status_text

        form = tk.Frame(panel, bg=PANEL_BG)
        form.pack(expand=True)
        self.admin_add_field_row(
            form,
            0,
            "Operador:",
            self.admin_reset_operator_name,
            False,
            "admin_reset_operator_name",
        )
        self.admin_add_field_row(
            form,
            1,
            "PIN:",
            "●" * len(self.admin_reset_operator_pin),
            True,
            "admin_reset_operator_pin",
        )

        if reset_status_text:
            tk.Label(
                panel,
                text=reset_status_text,
                bg=PANEL_BG,
                fg="#c48b00",
                font=("Arial", 14, "bold"),
                wraplength=APP_WIDTH - 120,
                justify="center",
            ).pack(fill="x", padx=60, pady=(0, 18))

    def refresh_admin_reset_field(self) -> None:
        if not self.update_field_value(
            "admin_reset_operator_pin",
            "●" * len(self.admin_reset_operator_pin),
        ):
            self.show_admin_reset_password()

    def cancel_admin_reset_password(self) -> None:
        self.admin_reset_operator_name = ""
        self.admin_reset_operator_pin = ""
        self.status_text = ""
        self.show_admin_operators()

    def save_admin_reset_password(self) -> None:
        success, message = self.reset_operator_password(
            self.admin_reset_operator_name,
            self.admin_reset_operator_pin,
        )
        self.status_text = message
        if success:
            reset_operator = self.normalize_operator_name(self.admin_reset_operator_name)
            self.admin_reset_operator_name = ""
            self.admin_reset_operator_pin = ""
            operators = self.managed_operator_options()
            if reset_operator in operators:
                self.selected_admin_operator_index = operators.index(reset_operator)
            self.show_admin_operators()
        else:
            self.show_admin_reset_password()

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

        root = tk.Frame(self, bg=PANEL_BG)
        root.pack(fill="both", expand=True)

        body = tk.Frame(root, bg=PANEL_BG)
        body.pack(fill="both", expand=True)

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

        footer = tk.Frame(root, bg=PANEL_BG)
        footer.pack(fill="x")
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
                command=command,
                relief="flat",
                bd=0,
                borderwidth=0,
                highlightthickness=0,
                font=("Arial", FOOTER_FONT_SIZE, "bold"),
                padx=18,
                pady=14,
            ).pack(side="left", expand=True, fill="x")

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
        menu_content.pack(expand=True, anchor="center")

        tk.Label(
            menu_content,
            text=f"Operador: {self.operator_id}",
            bg=WHITE,
            fg="#555555",
            font=("Arial", 14),
        ).pack(pady=(0, 12))
        for i, option in enumerate(self.menu_options):
            label = tk.Label(
                menu_content,
                text=option,
                pady=18,
                padx=36,
                anchor="center",
                width=34,
            )
            label.option_font_size = 20
            self.style_option_label(label, i == self.selected_index)
            label.pack(fill="x", pady=8)
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

        self.build_mold_footer(root)

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
                font=("Arial", 14, "bold"),
                wraplength=APP_WIDTH - 120,
                justify="center",
            ).grid(row=2, column=0, sticky="n", pady=12)

        selected_option = tk.Label(
            root,
            text=self.selected_menu_option or "Medir caudal",
            bg="#f0b57a",
            fg="#8a5a25",
            font=("Arial", 15),
            padx=4,
            pady=3,
            wraplength=300,
            justify="right",
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
        button_wrap_length = APP_WIDTH // len(buttons) - 16
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
                font=("Arial", FOOTER_FONT_SIZE),
                wraplength=button_wrap_length,
                justify="center",
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

        self.build_mold_side_footer(root)

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
            font=("Arial", 14),
            width=14,
            pady=8,
        ).pack()

        if self.status_text:
            tk.Label(
                content,
                text=self.status_text,
                bg=WHITE,
                fg=RED,
                font=("Arial", 14, "bold"),
                wraplength=APP_WIDTH - 120,
                justify="center",
            ).grid(row=2, column=0, sticky="n", pady=12)

        mold_badge = tk.Label(
            root,
            text=(self.session.molde if self.session else ""),
            bg="#f0b57a",
            fg="#8a5a25",
            font=("Arial", 15),
            padx=14,
            pady=3,
            wraplength=300,
            justify="right",
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
        button_wrap_length = APP_WIDTH // len(buttons) - 16
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
                font=("Arial", FOOTER_FONT_SIZE),
                wraplength=button_wrap_length,
                justify="center",
                pady=16,
            ).pack(side="left", expand=True, fill="both")

    def build_simple_footer(
        self,
        parent: tk.Widget,
        buttons: list[tuple[str, str, str, object]],
        font_size: int = FOOTER_FONT_SIZE,
    ) -> None:
        existing_children = parent.winfo_children()
        footer = tk.Frame(parent, bg=WHITE)
        pack_options = {"side": "bottom", "fill": "x"}
        if existing_children:
            pack_options["before"] = existing_children[0]
        footer.pack(**pack_options)
        button_wrap_length = APP_WIDTH // len(buttons) - 16
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
                wraplength=button_wrap_length,
                justify="center",
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
            wraplength=300,
            justify="right",
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
        return DIAMETER_LABELS.get(diameter, f"{diameter} mm")

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
            font=("Arial", 14),
        ).pack(pady=(18, 0))

        badge_text = self.diameter_context_badge_text()
        if badge_text:
            self.place_orange_badge(self, badge_text, font_size=14, padx=12)

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
            text=self.input_value.replace(".", ",") or " ",
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

        feedback = tk.Frame(content, bg=WHITE)
        feedback.grid(row=2, column=0, sticky="n", pady=12)
        tk.Label(
            feedback,
            text=self.decimal_separator_help_text(),
            bg=WHITE,
            fg="#555555",
            font=("Arial", 14, "bold"),
            wraplength=APP_WIDTH - 120,
            justify="center",
        ).pack()

        if self.status_text:
            tk.Label(
                feedback,
                text=self.status_text,
                bg=WHITE,
                fg=RED,
                font=("Arial", 14, "bold"),
                wraplength=APP_WIDTH - 120,
                justify="center",
            ).pack(pady=(6, 0))

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
            font_size=14,
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
                "Nº do circuito inicial :",
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
                font=("Arial", 14, "bold"),
                wraplength=APP_WIDTH - 120,
                justify="center",
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
        self.place_orange_badge(root, self.setup_badge_text(), font_size=14, padx=18)

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
            font=("Arial", 14),
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

        footer_area = tk.Frame(root, bg=WHITE)
        footer_area.pack(side="bottom", fill="x")

        if not self.measurement_running and self.samples:
            tk.Label(
                footer_area,
                text="Medição parada.",
                bg=WHITE,
                fg=RED,
                font=("Arial", 14, "bold"),
            ).pack(fill="x", pady=(0, 4))

        if self.status_text:
            tk.Label(
                footer_area,
                text=self.status_text,
                bg=WHITE,
                fg=RED,
                font=("Arial", 14, "bold"),
                wraplength=APP_WIDTH - 40,
                justify="center",
            ).pack(fill="x", pady=(0, 4))

        self.build_simple_footer(
            footer_area,
            [
                ("Voltar atrás", "#303030", WHITE, self.go_back),
                ("Recomeçar", RED, PANEL_FG, self.restart_current_measurement),
                ("Parar", GREEN, PANEL_FG, self.stop_current_measurement),
                ("Concluir", BLUE, PANEL_FG, self.confirm),
            ],
            font_size=14,
        )
        self.place_orange_badge(
            root,
            self.measurement_badge_text(),
            font_size=14,
            padx=18,
        )

        if self.measurement_running:
            self.schedule_measurement_update()

    def measure_value_box(
        self,
        parent: tk.Widget,
        row: int,
        column: int,
        width: int,
        value: str,
    ) -> tk.Label:
        height = 42 if width >= 90 else 28
        font_size = 20 if width >= 90 else 14
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
            font_size=14,
        )
        self.place_orange_badge(root, self.measurement_badge_text(), font_size=14, padx=18)

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
            font=("Arial", 20, "bold"),
        ).pack(fill="x", pady=(0, 4))
        self.build_simple_footer(
            footer_area,
            [
                ("Voltar atrás", "#303030", WHITE, self.go_back),
                ("Medir\nNovamente", RED, PANEL_FG, self.remeasure_current_circuit),
                ("Selecionar", GREEN, PANEL_FG, self.select),
                (next_text, BLUE, PANEL_FG, self.advance_after_measurement_result),
            ],
            font_size=14,
        )
        self.place_orange_badge(root, self.measurement_badge_text(), font_size=14, padx=18)

    def result_box(
        self,
        parent: tk.Widget,
        row: int,
        column: int,
        width: int,
        text: str,
        font_size: int = 14,
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

    def circuit_results_visible_row_count(self) -> int:
        height = self.winfo_height()
        if height <= 1:
            height = APP_HEIGHT

        if height >= 900:
            count = 8
        elif height >= 700:
            count = 6
        else:
            count = 4

        if self.status_text:
            count -= 1

        return max(3, count)

    def show_circuit_results(self) -> None:
        self.screen = "CIRCUIT_RESULTS"
        self.clear()
        self.option_labels = []
        self.diameter_labels = []
        self.field_value_labels = {}

        root = tk.Frame(self, bg=WHITE)
        root.pack(fill="both", expand=True)

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
            font_size=15,
        )

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
        ).pack(pady=(0, 10 if self.result_editing else 26))

        if self.result_editing:
            tk.Label(
                results_content,
                text=self.decimal_separator_help_text(),
                bg=WHITE,
                fg="#555555",
                font=("Arial", 14, "bold"),
                wraplength=APP_WIDTH - 120,
                justify="center",
            ).pack(pady=(0, 10))

        records = sorted(self.measurements_for_side(side), key=lambda item: item["circuito"])
        if records:
            self.selected_result_index = max(
                0,
                min(self.selected_result_index, len(records) - 1),
            )

        table_area = tk.Frame(results_content, bg=WHITE)
        table_area.pack()
        rows = tk.Frame(table_area, bg=WHITE)
        rows.pack(side="left")

        max_visible = self.circuit_results_visible_row_count()
        if len(records) > max_visible:
            start = self.selected_result_index - (max_visible // 2)
            start = max(0, min(start, len(records) - max_visible))
            end = start + max_visible
        else:
            start = 0
            end = len(records)

        for row_index, item_index in enumerate(range(start, end)):
            item = records[item_index]
            circuit = item.get("circuito", item_index + 1)
            editing = self.result_editing and item_index == self.selected_result_index
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
                font=("Arial", RESULTS_TABLE_FONT_SIZE),
            ).grid(row=row_index, column=0, sticky="e", padx=(0, 14), pady=6)
            highlighted = bool(item.get("destacado"))
            selected = item_index == self.selected_result_index
            bg = RED if highlighted else GREY
            value_label = self.result_box(
                rows,
                row_index,
                1,
                220,
                value,
                font_size=RESULTS_TABLE_FONT_SIZE,
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
                font=("Arial", RESULTS_TABLE_FONT_SIZE),
            ).grid(row=row_index, column=2, sticky="w", padx=(14, 0), pady=6)

        visible_count = max(end - start, 1)
        if len(records) > visible_count:
            scroll = tk.Frame(table_area, bg="#d7d7d7", width=26)
            scroll.pack(side="left", fill="y", padx=(28, 0))
            scroll.pack_propagate(False)

            visible_fraction = max(0.12, min(1.0, visible_count / len(records)))
            max_start = max(len(records) - visible_count, 1)
            thumb_top = (start / max_start) * (1.0 - visible_fraction)
            tk.Frame(scroll, bg="#555555").place(
                relx=0.5,
                rely=thumb_top,
                anchor="n",
                relwidth=0.5,
                relheight=visible_fraction,
            )

        if self.status_text:
            tk.Label(
                content,
                text=self.status_text,
                bg=WHITE,
                fg=RED,
                font=("Arial", 14, "bold"),
                wraplength=APP_WIDTH - 120,
                justify="center",
            ).grid(row=2, column=0, pady=(12, 0))

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
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(0, weight=1)

        info = tk.Frame(content, bg=WHITE)
        info.grid(row=0, column=0)
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
                ("-", RED, PANEL_FG, lambda: None),
                ("Guardar\nDados", GREEN, PANEL_FG, self.save_session_and_return_to_login),
                ("Confirmar", BLUE, PANEL_FG, self.save_session_and_return_to_login),
            ],
            font_size=16,
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
            font=("Arial", 14),
        ).pack(pady=(0, 10))

        if self.session and self.session.medicoes:
            table = tk.Frame(panel, bg=PANEL_BG)
            table.pack(fill="x", padx=20, pady=(0, 8))
            headers = [
                ("Lado", 16),
                ("Circ.", 9),
                ("Min", 11),
                ("Médio", 11),
                ("Máx", 11),
            ]
            for col, (header, width) in enumerate(headers):
                table.grid_columnconfigure(col, weight=1)
                tk.Label(
                    table,
                    text=header,
                    bg="#374151",
                    fg=WHITE,
                    font=("Arial", TABLE_FONT_SIZE, "bold"),
                    width=width,
                    pady=4,
                ).grid(row=0, column=col, padx=1, sticky="ew")
            height = self.winfo_height()
            summary_row_count = 3 if height <= 1 or height < 700 else 5
            visible_measurements = self.session.medicoes[-summary_row_count:]
            for row, item in enumerate(visible_measurements, start=1):
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
                        font=("Arial", TABLE_FONT_SIZE),
                        width=headers[col][1],
                        pady=4,
                    ).grid(row=row, column=col, padx=1, pady=1, sticky="ew")

        options = ["Nova operação", "Confirmar dados", "Terminar sessão"]
        for i, option in enumerate(options):
            self.option_row(panel, option, i == self.selected_index)

    def show_send_review(self) -> None:
        self.screen = "SEND_REVIEW"
        sessions = self.load_pending_sessions()
        rows = self.pending_measurement_rows(sessions)
        groups = self.pending_measurement_groups(rows)
        self.prune_send_review_checked_groups(groups)
        if groups:
            self.normalize_pending_review_selection(groups)
        expanded_group_key = getattr(self, "send_review_expanded_group_key", None)
        selected_group = self.selected_pending_group(groups)
        is_selected_group_expanded = (
            selected_group is not None
            and selected_group.get("_group_key") == expanded_group_key
        )
        show_checkboxes = self.operator_id == "ADMIN"
        if not show_checkboxes:
            self.checked_send_review_group_keys().clear()
        can_select_group = show_checkboxes and not is_selected_group_expanded
        panel = self.build_base(
            "",
            "",
            delete_text=(
                "Apagar"
                if not show_checkboxes or is_selected_group_expanded
                else "Expandir"
            ),
            delete_command=(
                (
                    self.delete_selected_pending_session
                    if not show_checkboxes or is_selected_group_expanded
                    else self.toggle_selected_pending_group
                )
            ),
            select_text="Selecionar" if can_select_group else None,
            select_command=(
                self.toggle_selected_pending_group_checkbox if can_select_group else None
            ),
            confirm_text="Exportar PDF" if show_checkboxes else "Expandir",
            confirm_command=(
                self.confirm_checked_pending_sessions
                if show_checkboxes
                else (
                    (lambda: None)
                    if is_selected_group_expanded
                    else self.toggle_selected_pending_group
                )
            ),
        )
        panel.configure(bg=WHITE)
        session_count = self.pending_review_session_count(rows)
        operator_count = len({row["_operator_key"] for row in rows})
        count_text = (
            f"Operadores: {operator_count} | Grupos: {len(groups)} | Medições: {len(rows)}"
            if self.operator_id == "ADMIN"
            else f"Sessões: {session_count} | Grupos: {len(groups)} | Medições: {len(rows)}"
        )

        tk.Label(
            panel,
            text="Medições feitas",
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
        ).pack(pady=(0, 6 if self.status_text else 12))

        if self.status_text:
            status_lower = self.status_text.casefold()
            is_error = any(
                term in status_lower
                for term in ("não", "nao", "selecione", "permitida", "erro")
            )
            tk.Label(
                panel,
                text=self.status_text,
                bg=WHITE,
                fg=RED if is_error else GREEN,
                font=("Arial", 14, "bold"),
                wraplength=APP_WIDTH - 120,
                justify="center",
            ).pack(pady=(0, 6))

        if groups:
            display_rows = self.pending_review_display_rows(groups)
            is_expanded = (
                getattr(self, "send_review_expanded_group_key", None) is not None
            )
            if is_expanded:
                self.normalize_send_review_detail_selection(display_rows)
            max_rows = self.send_review_visible_row_count()
            max_start = max(len(display_rows) - max_rows, 0)
            first_visible_row = max(
                0,
                min(getattr(self, "send_review_first_row", 0), max_start),
            )
            self.send_review_first_row = first_visible_row
            first_visible_row = self.send_review_first_row_for_selection(
                display_rows, max_rows
            )
            self.send_review_first_row = first_visible_row
            visible_rows = display_rows[first_visible_row : first_visible_row + max_rows]
            table_area = tk.Frame(panel, bg=WHITE)
            table_area.pack(fill="x", padx=4, pady=(0, 0))
            table = tk.Frame(table_area, bg=WHITE)
            table.pack(side="left", fill="x", expand=True)
            self.send_review_checkbox_vars = []
            self.bind_send_review_scroll(table_area)
            self.bind_send_review_scroll(table)
            if not is_expanded:
                headers = [
                    ("Data", 16),
                    ("Operador", 14),
                    ("Molde", 12),
                    ("Lado", 14),
                    ("Nº circuitos", 12),
                ]
            elif self.operator_id == "ADMIN":
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
            first_data_column = 0
            if show_checkboxes:
                checkbox_column_width = 3
                table.grid_columnconfigure(0, weight=checkbox_column_width)
                checkbox_header = tk.Label(
                    table,
                    text="",
                    bg="#374151",
                    fg=WHITE,
                    font=("Arial", TABLE_FONT_SIZE, "bold"),
                    width=checkbox_column_width,
                    pady=4,
                )
                checkbox_header.grid(row=0, column=0, padx=1, sticky="ew")
                self.bind_send_review_scroll(checkbox_header)
                first_data_column = 1

            for col, (header, width) in enumerate(headers, start=first_data_column):
                table.grid_columnconfigure(col, weight=width)
                header_label = tk.Label(
                    table,
                    text=header,
                    bg="#374151",
                    fg=WHITE,
                    font=("Arial", TABLE_FONT_SIZE, "bold"),
                    width=width,
                    pady=4,
                )
                header_label.grid(row=0, column=col, padx=1, sticky="ew")
                self.bind_send_review_scroll(header_label)

            for row_index, item in enumerate(visible_rows, start=1):
                is_detail = item.get("_row_type") == "detail"
                is_selected = (
                    self.is_selected_send_review_detail_row(item)
                    if is_expanded
                    else item["_group_index"] == self.selected_index
                )
                if not is_expanded:
                    values = [
                        item["data"],
                        item["operador"],
                        item["molde"],
                        item["lado"],
                        item["circuito"],
                    ]
                elif self.operator_id == "ADMIN":
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
                bg = WHITE
                fg = PANEL_FG
                font_weight = "normal"
                if is_selected:
                    bg = BLUE
                    fg = WHITE
                    font_weight = "bold"
                elif is_detail:
                    bg = "#e8f4ff" if is_selected else "#f4f8fb"

                if show_checkboxes:
                    checkbox_var = tk.BooleanVar(
                        value=self.is_checked_send_review_row(item)
                    )
                    self.send_review_checkbox_vars.append(checkbox_var)
                    checkbox = tk.Checkbutton(
                        table,
                        variable=checkbox_var,
                        bg=bg,
                        activebackground=bg,
                        selectcolor=WHITE,
                        relief="flat",
                        bd=0,
                        borderwidth=0,
                        highlightthickness=0,
                        takefocus=0,
                        pady=0,
                    )
                    checkbox.bind("<Button-1>", lambda _event: "break")
                    checkbox.bind("<ButtonRelease-1>", lambda _event: "break")
                    self.bind_send_review_scroll(checkbox)
                    checkbox.grid(
                        row=row_index,
                        column=0,
                        padx=1,
                        pady=1,
                        sticky="nsew",
                    )

                for col, value in enumerate(values, start=first_data_column):
                    cell = tk.Label(
                        table,
                        text=value,
                        bg=bg,
                        fg=fg,
                        font=("Arial", TABLE_FONT_SIZE, font_weight),
                        width=headers[col - first_data_column][1],
                        pady=4,
                    )
                    cell.bind(
                        "<ButtonRelease-1>",
                        lambda _event, row=item: self.select_send_review_row(row),
                    )
                    self.bind_send_review_scroll(cell)
                    cell.grid(row=row_index, column=col, padx=1, pady=1, sticky="ew")

            if len(display_rows) > max_rows:
                scrollbar = tk.Frame(table_area, bg="#d7d7d7", width=22)
                scrollbar.pack(side="right", fill="y", padx=(8, 0))
                scrollbar.pack_propagate(False)
                self.bind_send_review_scroll(scrollbar)

                visible_fraction = max(0.12, min(1.0, len(visible_rows) / len(display_rows)))
                max_start = max(len(display_rows) - len(visible_rows), 1)
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
                font=("Arial", 14),
            ).pack(pady=22)

    def pending_review_session_count(self, rows: list[dict[str, Any]]) -> int:
        if not rows:
            return 0
        return max(int(row["_session_index"]) for row in rows) + 1

    def pending_measurement_groups(
        self, rows: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        groups: list[dict[str, Any]] = []
        group_by_key: dict[tuple[str, str, str, str], dict[str, Any]] = {}
        for row in rows:
            group_key = (
                str(row["_file_name"]),
                str(row["_operator_key"]),
                str(row["_mold_key"]),
                str(row["_side_key"]),
            )
            group = group_by_key.get(group_key)
            if group is None:
                group = {
                    "_group_index": len(groups),
                    "_group_key": group_key,
                    "_operator_key": row["_operator_key"],
                    "_rows": [],
                    "_row_type": "group",
                    "data": row["data"],
                    "operador": row["operador"],
                    "molde": row["molde"],
                    "lado": row["lado"],
                    "circuito": "",
                    "min": "-",
                    "medio": "-",
                    "max": "-",
                }
                group_by_key[group_key] = group
                groups.append(group)
            group["_rows"].append(row)

        for group in groups:
            group_rows = group["_rows"]
            group["circuito"] = str(len(group_rows))
            group["min"] = self.format_group_measurement_value(group_rows, "min")
            group["medio"] = self.format_group_measurement_value(group_rows, "medio")
            group["max"] = self.format_group_measurement_value(group_rows, "max")
        return groups

    def pending_review_display_rows(
        self, groups: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        expanded_group_key = getattr(self, "send_review_expanded_group_key", None)
        valid_group_keys = {group["_group_key"] for group in groups}
        if expanded_group_key not in valid_group_keys:
            self.send_review_expanded_group_key = None
            self.send_review_selected_measurement_ref = None
            return groups

        for group in groups:
            if group["_group_key"] != expanded_group_key:
                continue

            display_rows = []
            for row in group["_rows"]:
                detail_row = row.copy()
                detail_row["_row_type"] = "detail"
                detail_row["_group_index"] = group["_group_index"]
                detail_row["_group_key"] = group["_group_key"]
                display_rows.append(detail_row)
            return display_rows

        return groups

    @staticmethod
    def send_review_measurement_ref(row: dict[str, Any]) -> tuple[str, int]:
        return str(row["_file_name"]), int(row["_measurement_index"])

    def checked_send_review_group_keys(self) -> set[tuple[str, str, str, str]]:
        checked_group_keys = getattr(self, "send_review_checked_group_keys", None)
        if checked_group_keys is None:
            checked_group_keys = set()
            self.send_review_checked_group_keys = checked_group_keys
        return checked_group_keys

    def prune_send_review_checked_groups(self, groups: list[dict[str, Any]]) -> None:
        valid_group_keys = {group["_group_key"] for group in groups}
        checked_group_keys = self.checked_send_review_group_keys()
        checked_group_keys.intersection_update(valid_group_keys)

    def is_checked_send_review_row(self, row: dict[str, Any]) -> bool:
        return row.get("_group_key") in self.checked_send_review_group_keys()

    def normalize_send_review_detail_selection(
        self, rows: list[dict[str, Any]]
    ) -> tuple[str, int] | None:
        detail_refs = [
            self.send_review_measurement_ref(row)
            for row in rows
            if row.get("_row_type") == "detail"
        ]
        if not detail_refs:
            self.send_review_selected_measurement_ref = None
            return None

        current_ref = getattr(self, "send_review_selected_measurement_ref", None)
        if current_ref not in detail_refs:
            current_ref = detail_refs[0]
            self.send_review_selected_measurement_ref = current_ref
        return current_ref

    def is_selected_send_review_detail_row(self, row: dict[str, Any]) -> bool:
        if row.get("_row_type") != "detail":
            return False
        return (
            self.send_review_measurement_ref(row)
            == getattr(self, "send_review_selected_measurement_ref", None)
        )

    @staticmethod
    def pending_review_group_indices(groups: list[dict[str, Any]]) -> list[int]:
        return [int(group["_group_index"]) for group in groups]

    def normalize_pending_review_selection(
        self, groups: list[dict[str, Any]]
    ) -> list[int]:
        group_indices = self.pending_review_group_indices(groups)
        if not group_indices:
            self.selected_index = 0
            return []

        if self.selected_index not in group_indices:
            position = max(0, min(self.selected_index, len(group_indices) - 1))
            self.selected_index = group_indices[position]
        return group_indices

    @staticmethod
    def pending_review_group_bounds(
        display_rows: list[dict[str, Any]], group_index: int
    ) -> tuple[int, int] | None:
        first_row: int | None = None
        last_row: int | None = None
        for row_index, row in enumerate(display_rows):
            if int(row["_group_index"]) != group_index:
                continue
            if first_row is None:
                first_row = row_index
            last_row = row_index

        if first_row is None or last_row is None:
            return None
        return first_row, last_row

    @staticmethod
    def clamp_send_review_first_row(
        rows: list[dict[str, Any]], first_row: int, max_rows: int
    ) -> int:
        max_start = max(len(rows) - max_rows, 0)
        return max(0, min(first_row, max_start))

    def send_review_first_row_for_group(
        self, rows: list[dict[str, Any]], group_index: int, max_rows: int
    ) -> int:
        bounds = self.pending_review_group_bounds(rows, group_index)
        if bounds is None:
            return 0

        first_row, _ = bounds
        return self.clamp_send_review_first_row(rows, first_row, max_rows)

    def send_review_first_row_for_selection(
        self, rows: list[dict[str, Any]], max_rows: int
    ) -> int:
        first_visible_row = self.clamp_send_review_first_row(
            rows,
            int(getattr(self, "send_review_first_row", 0)),
            max_rows,
        )
        if getattr(self, "send_review_expanded_group_key", None) is not None:
            return first_visible_row

        bounds = self.pending_review_group_bounds(rows, self.selected_index)
        if bounds is None:
            return first_visible_row

        selected_first_row, selected_last_row = bounds
        visible_last_row = first_visible_row + max_rows - 1
        if selected_first_row < first_visible_row:
            return self.clamp_send_review_first_row(rows, selected_first_row, max_rows)

        if selected_last_row > visible_last_row:
            selected_row_count = selected_last_row - selected_first_row + 1
            if selected_row_count > max_rows:
                return self.clamp_send_review_first_row(
                    rows, selected_first_row, max_rows
                )
            return self.clamp_send_review_first_row(
                rows, selected_last_row - max_rows + 1, max_rows
            )

        return first_visible_row

    def move_send_review_selection(self, delta: int) -> bool:
        rows = self.pending_measurement_rows(self.load_pending_sessions())
        groups = self.pending_measurement_groups(rows)
        if not groups:
            self.selected_index = 0
            self.send_review_first_row = 0
            return False

        max_rows = self.send_review_visible_row_count()
        group_indices = self.normalize_pending_review_selection(groups)
        display_rows = self.pending_review_display_rows(groups)
        if getattr(self, "send_review_expanded_group_key", None) is not None:
            return self.move_send_review_detail_selection(
                delta, display_rows, max_rows
            )

        bounds = self.pending_review_group_bounds(display_rows, self.selected_index)
        if not group_indices or bounds is None:
            self.selected_index = 0
            self.send_review_first_row = 0
            return False

        self.send_review_first_row = self.send_review_first_row_for_selection(
            display_rows, max_rows
        )
        first_visible_row = self.send_review_first_row
        visible_last_row = first_visible_row + max_rows - 1
        selected_first_row, selected_last_row = bounds

        if delta > 0 and selected_last_row > visible_last_row:
            self.send_review_first_row = self.clamp_send_review_first_row(
                display_rows, first_visible_row + 1, max_rows
            )
            return True

        if delta < 0 and selected_first_row < first_visible_row:
            self.send_review_first_row = self.clamp_send_review_first_row(
                display_rows, first_visible_row - 1, max_rows
            )
            return True

        if getattr(self, "send_review_expanded_group_key", None) is not None:
            return True

        try:
            current_position = group_indices.index(self.selected_index)
        except ValueError:
            current_position = 0

        step = 1 if delta > 0 else -1
        self.selected_index = group_indices[
            (current_position + step) % len(group_indices)
        ]
        self.send_review_first_row = self.send_review_first_row_for_group(
            display_rows, self.selected_index, max_rows
        )
        return True

    def move_send_review_detail_selection(
        self, delta: int, rows: list[dict[str, Any]], max_rows: int
    ) -> bool:
        detail_rows = [
            (row_index, row)
            for row_index, row in enumerate(rows)
            if row.get("_row_type") == "detail"
        ]
        if not detail_rows:
            self.send_review_selected_measurement_ref = None
            self.send_review_first_row = 0
            return False

        current_ref = self.normalize_send_review_detail_selection(rows)
        refs = [self.send_review_measurement_ref(row) for _, row in detail_rows]
        try:
            current_position = refs.index(current_ref)
        except ValueError:
            current_position = 0

        step = 1 if delta > 0 else -1
        next_position = (current_position + step) % len(detail_rows)
        next_row_index, next_row = detail_rows[next_position]
        self.send_review_selected_measurement_ref = self.send_review_measurement_ref(
            next_row
        )

        first_row = self.clamp_send_review_first_row(
            rows,
            int(getattr(self, "send_review_first_row", 0)),
            max_rows,
        )
        visible_last_row = first_row + max_rows - 1
        if next_row_index < first_row:
            first_row = next_row_index
        elif next_row_index > visible_last_row:
            first_row = next_row_index - max_rows + 1

        self.send_review_first_row = self.clamp_send_review_first_row(
            rows, first_row, max_rows
        )
        return True

    def toggle_selected_pending_group_checkbox(self) -> None:
        rows = self.pending_measurement_rows(self.load_pending_sessions())
        groups = self.pending_measurement_groups(rows)
        self.prune_send_review_checked_groups(groups)
        group = self.selected_pending_group(groups)
        if group is None:
            self.status_text = "Nao existe uma medicao selecionada."
            self.show_send_review()
            return

        checked_group_keys = self.checked_send_review_group_keys()
        group_key = group["_group_key"]
        if group_key in checked_group_keys:
            checked_group_keys.remove(group_key)
        else:
            checked_group_keys.add(group_key)

        self.status_text = ""
        display_rows = self.pending_review_display_rows(groups)
        max_rows = self.send_review_visible_row_count()
        self.send_review_first_row = self.send_review_first_row_for_selection(
            display_rows, max_rows
        )
        self.show_send_review()

    def select_send_review_group(self, group_index: int) -> None:
        rows = self.pending_measurement_rows(self.load_pending_sessions())
        groups = self.pending_measurement_groups(rows)
        if not groups:
            self.selected_index = 0
            self.send_review_first_row = 0
            self.show_send_review()
            return

        group_indices = self.pending_review_group_indices(groups)
        if group_index in group_indices:
            self.selected_index = group_index
            selected_group = self.selected_pending_group(groups)
            if selected_group is not None:
                self.send_review_expanded_group_key = selected_group["_group_key"]
                self.send_review_selected_measurement_ref = None
        else:
            self.normalize_pending_review_selection(groups)

        display_rows = self.pending_review_display_rows(groups)
        self.normalize_send_review_detail_selection(display_rows)
        max_rows = self.send_review_visible_row_count()
        self.send_review_first_row = self.send_review_first_row_for_selection(
            display_rows, max_rows
        )
        self.show_send_review()

    def select_send_review_row(self, row: dict[str, Any]) -> None:
        if row.get("_row_type") != "detail":
            self.select_send_review_group(int(row["_group_index"]))
            return

        self.selected_index = int(row["_group_index"])
        self.send_review_selected_measurement_ref = self.send_review_measurement_ref(row)
        rows = self.pending_measurement_rows(self.load_pending_sessions())
        groups = self.pending_measurement_groups(rows)
        display_rows = self.pending_review_display_rows(groups)
        max_rows = self.send_review_visible_row_count()
        self.send_review_first_row = self.send_review_first_row_for_selection(
            display_rows, max_rows
        )
        self.show_send_review()

    def send_review_visible_row_count(self) -> int:
        height = max(self.winfo_height(), self.winfo_screenheight(), 480)
        if height >= 900:
            return 14
        if height >= 700:
            return 10
        return 7

    def bind_send_review_scroll(self, widget: tk.Widget) -> None:
        widget.bind("<MouseWheel>", self.on_send_review_mousewheel, add="+")
        widget.bind("<Button-4>", self.on_send_review_mousewheel, add="+")
        widget.bind("<Button-5>", self.on_send_review_mousewheel, add="+")

    def on_send_review_mousewheel(self, event: tk.Event) -> str:
        if getattr(event, "num", None) == 4:
            delta = -1
        elif getattr(event, "num", None) == 5:
            delta = 1
        else:
            delta = -1 if getattr(event, "delta", 0) > 0 else 1

        if self.scroll_send_review_rows(delta):
            self.show_send_review()
        return "break"

    def scroll_send_review_rows(self, delta: int) -> bool:
        rows = self.pending_measurement_rows(self.load_pending_sessions())
        groups = self.pending_measurement_groups(rows)
        if not groups:
            self.send_review_first_row = 0
            return False

        display_rows = self.pending_review_display_rows(groups)
        max_rows = self.send_review_visible_row_count()
        if len(display_rows) <= max_rows:
            self.send_review_first_row = 0
            return False

        first_row = int(getattr(self, "send_review_first_row", 0))
        next_first_row = self.clamp_send_review_first_row(
            display_rows,
            first_row + delta,
            max_rows,
        )
        if next_first_row == first_row:
            return False

        self.send_review_first_row = next_first_row
        return True

    def selected_pending_group(self, groups: list[dict[str, Any]]) -> dict[str, Any] | None:
        if not groups:
            return None
        self.normalize_pending_review_selection(groups)
        for group in groups:
            if int(group["_group_index"]) == self.selected_index:
                return group
        return None

    def checked_pending_session_rows(self) -> list[dict[str, Any]]:
        rows = self.pending_measurement_rows(self.load_pending_sessions())
        groups = self.pending_measurement_groups(rows)
        self.prune_send_review_checked_groups(groups)
        checked_group_keys = self.checked_send_review_group_keys()
        selected_rows: list[dict[str, Any]] = []
        for group in groups:
            if group["_group_key"] in checked_group_keys:
                selected_rows.extend(group["_rows"])
        return selected_rows

    def selected_pending_session_rows(self) -> list[dict[str, Any]]:
        rows = self.pending_measurement_rows(self.load_pending_sessions())
        groups = self.pending_measurement_groups(rows)
        group = self.selected_pending_group(groups)
        if group is None:
            self.selected_index = 0
            return []

        if getattr(self, "send_review_expanded_group_key", None) is not None:
            display_rows = self.pending_review_display_rows(groups)
            selected_ref = self.normalize_send_review_detail_selection(display_rows)
            if selected_ref is None:
                return []
            return [
                row
                for row in display_rows
                if row.get("_row_type") == "detail"
                and self.send_review_measurement_ref(row) == selected_ref
            ]

        return list(group["_rows"])

    def toggle_selected_pending_group(self) -> None:
        rows = self.pending_measurement_rows(self.load_pending_sessions())
        groups = self.pending_measurement_groups(rows)
        group = self.selected_pending_group(groups)
        if group is None:
            self.status_text = "Não existe uma medição selecionada para expandir."
            self.show_send_review()
            return

        group_key = group["_group_key"]
        if getattr(self, "send_review_expanded_group_key", None) == group_key:
            self.send_review_expanded_group_key = None
            self.send_review_selected_measurement_ref = None
        else:
            self.send_review_expanded_group_key = group_key
            self.send_review_selected_measurement_ref = None

        display_rows = self.pending_review_display_rows(groups)
        self.normalize_send_review_detail_selection(display_rows)
        max_rows = self.send_review_visible_row_count()
        self.send_review_first_row = self.send_review_first_row_for_selection(
            display_rows, max_rows
        )
        self.status_text = ""
        self.show_send_review()

    def restore_send_review_selection_after_change(
        self,
        groups: list[dict[str, Any]],
        expanded_group_key: tuple[str, str, str, str] | None,
    ) -> None:
        if not groups:
            self.selected_index = 0
            self.send_review_expanded_group_key = None
            self.send_review_selected_measurement_ref = None
            self.send_review_first_row = 0
            return

        if expanded_group_key is not None:
            for group in groups:
                if group["_group_key"] != expanded_group_key:
                    continue
                self.selected_index = int(group["_group_index"])
                self.send_review_expanded_group_key = expanded_group_key
                display_rows = self.pending_review_display_rows(groups)
                self.normalize_send_review_detail_selection(display_rows)
                max_rows = self.send_review_visible_row_count()
                self.send_review_first_row = self.send_review_first_row_for_selection(
                    display_rows, max_rows
                )
                return

        self.send_review_expanded_group_key = None
        self.send_review_selected_measurement_ref = None
        self.selected_index = min(self.selected_index, len(groups) - 1)
        self.normalize_pending_review_selection(groups)
        self.send_review_first_row = 0

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

        expanded_group_key = getattr(self, "send_review_expanded_group_key", None)
        deleted_count = self.delete_pending_measurement_rows(selected_rows)
        if deleted_count:
            self.status_text = f"Medições apagadas: {deleted_count}."
            remaining_rows = self.pending_measurement_rows(self.load_pending_sessions())
            remaining_groups = self.pending_measurement_groups(remaining_rows)
            self.restore_send_review_selection_after_change(
                remaining_groups, expanded_group_key
            )
        else:
            self.status_text = "Não foi possível apagar a medição selecionada."
        self.show_send_review()

    def confirm_checked_pending_sessions(self) -> None:
        selected_rows = self.checked_pending_session_rows()
        success, message, _record = self.export_pending_measurement_rows_to_pdf(
            selected_rows
        )
        self.status_text = message
        if success:
            self.selected_index = 0
            self.send_review_first_row = 0
            self.send_review_expanded_group_key = None
            self.send_review_selected_measurement_ref = None
            self.checked_send_review_group_keys().clear()
            remaining_rows = self.pending_measurement_rows(self.load_pending_sessions())
            remaining_groups = self.pending_measurement_groups(remaining_rows)
            self.restore_send_review_selection_after_change(remaining_groups, None)
        self.show_send_review()

    def confirm_current_operator_pending_sessions(self) -> None:
        self.last_send_error = ""
        count = self.send_pending_measurements_for_current_operator()
        if count:
            self.status_text = f"Envio concluido. Medicoes enviadas: {count}."
            if self.last_send_error:
                self.status_text += f" {self.last_send_error}"
        else:
            self.status_text = (
                self.last_send_error
                or "Nao foi possivel enviar medicoes."
            )
        self.selected_index = 0
        self.send_review_first_row = 0
        self.send_review_expanded_group_key = None
        self.send_review_selected_measurement_ref = None
        self.checked_send_review_group_keys().clear()
        self.show_send_review()

    def send_selected_pending_session(self) -> None:
        if getattr(self, "send_review_expanded_group_key", None) is not None:
            self.status_text = "Envio selecionado desativado no detalhe. Use Confirmar."
            self.show_send_review()
            return

        self.last_send_error = ""

        selected_rows = self.selected_pending_session_rows()
        if not selected_rows:
            self.status_text = "Não existe uma medição selecionada para enviar."
            self.show_send_review()
            return

        sent_count = self.send_pending_measurement_rows(selected_rows)
        if sent_count:
            self.status_text = f"Medições enviadas: {sent_count}."
            if self.last_send_error:
                self.status_text += f" {self.last_send_error}"
            remaining_rows = self.pending_measurement_rows(self.load_pending_sessions())
            remaining_groups = self.pending_measurement_groups(remaining_rows)
            self.restore_send_review_selection_after_change(
                remaining_groups, None
            )
        else:
            self.status_text = (
                self.last_send_error
                or "Não foi possível enviar a medição selecionada."
            )
        self.show_send_review()

    def send_pending_measurements_for_current_operator(self) -> int:
        return self.send_pending_measurement_rows(
            self.pending_measurement_rows(self.load_pending_sessions())
        )

    def send_pending_measurement_rows(self, rows: list[dict[str, Any]]) -> int:
        sent_count = 0
        file_measurement_counts: dict[str, int] = {}
        for row in rows:
            file_name = str(row["_file_name"])
            file_measurement_counts[file_name] = (
                file_measurement_counts.get(file_name, 0) + 1
            )

        for file_name in sorted(file_measurement_counts, reverse=True):
            if self.send_pending_session(file_name):
                sent_count += file_measurement_counts[file_name]
            else:
                break
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
            mold_value = session.get("molde") or "-"
            mold = self.short_table_text(mold_value, 10)
            session_rows: list[dict[str, Any]] = []
            for measurement_index, measurement in enumerate(measurements):
                if not isinstance(measurement, dict):
                    continue

                operator = measurement.get("operador") or session_operator
                if not self.should_show_pending_measurement(measurement, session_operator):
                    continue

                side_value = measurement.get("lado") or session.get("lado_molde") or "-"
                min_value = self.measurement_float_value(
                    measurement.get("caudal_min_l_min")
                )
                average_value = self.measurement_float_value(
                    measurement.get("caudal_medio_l_min")
                )
                max_value = self.measurement_float_value(
                    measurement.get("caudal_max_l_min")
                )
                session_rows.append(
                    {
                        "_file_name": file_name,
                        "_measurement_index": measurement_index,
                        "_session_index": session_index,
                        "_operator_key": self.normalize_operator_name(str(operator)),
                        "_mold_key": str(mold_value),
                        "_side_key": str(side_value),
                        "_min_value": min_value,
                        "_average_value": average_value,
                        "_max_value": max_value,
                        "_row_type": "detail",
                        "data": session_date,
                        "operador": self.short_table_text(operator, 12),
                        "molde": mold,
                        "lado": self.short_table_text(side_value, 12),
                        "circuito": self.short_table_text(
                            measurement.get("circuito") or "-", 5
                        ),
                        "min": self.format_measurement_value(min_value),
                        "medio": self.format_measurement_value(average_value),
                        "max": self.format_measurement_value(max_value),
                    }
                )
            if session_rows:
                rows.extend(session_rows)
                session_index += 1
        return rows

    @staticmethod
    def format_session_date(session: dict[str, Any]) -> str:
        value = str(
            session.get("enviado_em")
            or session.get("criado_em")
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
    def measurement_float_value(value: Any) -> float | None:
        if value in (None, ""):
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def format_group_measurement_value(
        self, rows: list[dict[str, Any]], field: str
    ) -> str:
        value_key = {
            "min": "_min_value",
            "medio": "_average_value",
            "max": "_max_value",
        }[field]
        values = [
            value
            for value in (row.get(value_key) for row in rows)
            if isinstance(value, (int, float))
        ]
        if not values:
            return "-"
        if field == "min":
            return self.format_measurement_value(min(values))
        if field == "max":
            return self.format_measurement_value(max(values))
        return self.format_measurement_value(sum(values) / len(values))

    @staticmethod
    def short_table_text(value: Any, limit: int) -> str:
        text = str(value)
        if len(text) <= limit:
            return text
        if limit <= 3:
            return text[:limit]
        return f"{text[: limit - 3]}..."

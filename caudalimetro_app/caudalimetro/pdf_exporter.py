from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

from .config import DIAMETER_LABELS

PAGE_WIDTH, PAGE_HEIGHT = A4
PALE_YELLOW = HexColor("#fffec7")
LIGHT_GREY = HexColor("#dedede")
BORDER_GREY = HexColor("#666666")

SIDE_ALIASES = {
    "fixed plate": "Fixed plate",
    "fixedplate": "Fixed plate",
    "moving plate": "Moving Plate",
    "movingplate": "Moving Plate",
    "middle plate": "Middle Plate",
    "middleplate": "Middle Plate",
    "jiggle": "Jiggle",
    "cam slide": "Cam Slide",
    "camslide": "Cam Slide",
}

SIDE_CAPACITIES = {
    "Fixed plate": 35,
    "Moving Plate": 35,
    "Middle Plate": 35,
    "Jiggle": 10,
    "Cam Slide": 10,
}

PDF_DIAMETER_LABELS: dict[int, str] = {
    3: "1/8",
    6: "1/4",

    # Valor legado existente em medições antigas
    8: "3/8",

    10: "3/8",
    12: "1/2",
    20: "3/4",
}

VALID_DIAMETER_LABELS = (
    "1/8",
    "1/4",
    "3/8",
    "1/2",
    "3/4",
)

def _format_diameter(value: Any) -> str | None:
    if isinstance(value, bool) or value in (None, ""):
        return None

    text = str(value).strip().replace('"', "")
    compact = text.replace(" ", "")

    if compact in VALID_DIAMETER_LABELS:
        return compact

    try:
        numeric = float(text.replace(",", "."))
    except (TypeError, ValueError):
        return None

    if not numeric.is_integer():
        return None

    return PDF_DIAMETER_LABELS.get(int(numeric))


def _diameter_summary(
    measurements: Iterable[dict[str, Any]],
) -> tuple[list[str], list[str]]:
    valid: set[str] = set()
    invalid: set[str] = set()

    order = {
        label: index
        for index, label in enumerate(VALID_DIAMETER_LABELS)
    }

    for measurement in measurements:
        raw = measurement.get("diametro_mm")

        if raw in (None, ""):
            continue

        formatted = _format_diameter(raw)

        if formatted is None:
            invalid.add(_safe_text(raw))
        else:
            valid.add(formatted)

    return (
        sorted(valid, key=lambda label: order.get(label, len(order))),
        sorted(invalid, key=str.casefold),
    )

def normalize_side(value: Any) -> str | None:
    key = " ".join(str(value or "").strip().split()).casefold()
    return SIDE_ALIASES.get(key)


def _safe_text(value: Any) -> str:
    return str(value if value not in (None, "") else "").strip()


def _format_number(value: Any, decimals: int = 2) -> str:
    if value in (None, ""):
        return ""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return _safe_text(value)
    text = f"{number:.{decimals}f}"
    return text.rstrip("0").rstrip(".")


def _fit_text(c: canvas.Canvas, text: str, max_width: float, font: str, max_size: float) -> float:
    size = max_size
    while size > 5 and stringWidth(text, font, size) > max_width:
        size -= 0.5
    return size


def _draw_centered(
    c: canvas.Canvas,
    text: Any,
    x: float,
    y: float,
    width: float,
    height: float,
    *,
    font: str = "Helvetica",
    size: float = 8,
) -> None:
    value = _safe_text(text)
    font_size = _fit_text(c, value, max(width - 5, 5), font, size)
    c.setFillColor(black)
    c.setFont(font, font_size)
    c.drawCentredString(x + width / 2, y + (height - font_size) / 2 + 1, value)


def _draw_cell(
    c: canvas.Canvas,
    x: float,
    y: float,
    width: float,
    height: float,
    *,
    fill=white,
    line_width: float = 0.7,
) -> None:
    c.setLineWidth(line_width)
    c.setStrokeColor(black)
    c.setFillColor(fill)
    c.rect(x, y, width, height, stroke=1, fill=1)


def _draw_header_fields(
    c: canvas.Canvas,
    *,
    mold: str,
    operators: list[str],
    exported_at: str,
    pressures: list[str],
    record_name: str,
) -> None:
    left = 55
    total_width = 470

    title_y = 758
    _draw_cell(c, left, title_y, total_width, 21, fill=white, line_width=1.2)
    _draw_centered(
        c,
        "TEST RUN PROTOCOL FOR WATER FLOW RATE",
        left,
        title_y,
        total_width,
        21,
        font="Helvetica-Bold",
        size=11,
    )

    row_h = 16
    y = title_y - row_h - 5
    widths = [82, 92, 67, 56, 100, 73]
    labels = ["Customer", "", "AHA", mold, "Document finished. Sign", ""]
    fills = [LIGHT_GREY, PALE_YELLOW, LIGHT_GREY, PALE_YELLOW, LIGHT_GREY, PALE_YELLOW]
    x = left
    for width, label, fill in zip(widths, labels, fills):
        _draw_cell(c, x, y, width, row_h, fill=fill)
        _draw_centered(
            c,
            label,
            x,
            y,
            width,
            row_h,
            font="Helvetica-Bold" if fill == LIGHT_GREY else "Helvetica",
            size=7.5,
        )
        x += width

    y -= row_h
    widths = [82, 92, 67, 56, 100, 73]
    operator_text = ", ".join(operators)
    date_text = exported_at.replace("T", " ")[:16]
    values = ["Doc issued by / Date:", f"{operator_text} - {date_text}", "Record", record_name, "Pression (bar)", ", ".join(pressures)]
    fills = [LIGHT_GREY, white, LIGHT_GREY, PALE_YELLOW, LIGHT_GREY, PALE_YELLOW]
    x = left
    for width, value, fill in zip(widths, values, fills):
        _draw_cell(c, x, y, width, row_h, fill=fill)
        _draw_centered(
            c,
            value,
            x,
            y,
            width,
            row_h,
            font="Helvetica-Bold" if fill == LIGHT_GREY else "Helvetica",
            size=6.6 if x == left else 7.2,
        )
        x += width


def _measurement_map(measurements: Iterable[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    latest_by_side_circuit: dict[tuple[str, int], dict[str, Any]] = {}
    for measurement in measurements:
        side = normalize_side(measurement.get("lado"))
        if side is None:
            continue
        try:
            circuit = int(measurement.get("circuito"))
        except (TypeError, ValueError):
            continue
        if circuit <= 0:
            continue
        key = (side, circuit)
        previous = latest_by_side_circuit.get(key)
        current_date = str(measurement.get("medido_em") or "")
        previous_date = str(previous.get("medido_em") or "") if previous else ""
        if previous is None or current_date >= previous_date:
            latest_by_side_circuit[key] = measurement

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for (side, _), measurement in latest_by_side_circuit.items():
        grouped[side].append(measurement)
    for values in grouped.values():
        values.sort(key=lambda item: int(item.get("circuito") or 0))
    return grouped


def _draw_flow_table(
    c: canvas.Canvas,
    *,
    x: float,
    top_y: float,
    width: float,
    title: str,
    measurements: list[dict[str, Any]],
    capacity: int,
    row_height: float,
) -> list[dict[str, Any]]:
    header_h = 31
    label_w = width * 0.50
    value_w = width - label_w
    header_bottom = top_y - header_h

    _draw_cell(c, x, header_bottom, label_w, header_h, fill=white, line_width=1.0)
    _draw_cell(c, x + label_w, header_bottom, value_w, header_h, fill=white, line_width=1.0)
    title_lines = title.split(" ") if title in {"Fixed plate", "Moving Plate", "Middle Plate"} else [title]
    if len(title_lines) == 2:
        c.setFillColor(black)
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(x + label_w / 2, header_bottom + 18, title_lines[0])
        c.drawCentredString(x + label_w / 2, header_bottom + 7, title_lines[1])
    else:
        _draw_centered(c, title, x, header_bottom, label_w, header_h, font="Helvetica-Bold", size=9)
    _draw_centered(c, "l/m", x + label_w, header_bottom, value_w, header_h, font="Helvetica-Bold", size=9)

    separator_h = 5
    separator_y = header_bottom - separator_h
    _draw_cell(c, x, separator_y, width, separator_h, fill=LIGHT_GREY, line_width=0.8)

    shown = measurements[:capacity]
    overflow = measurements[capacity:]
    by_row = {index: item for index, item in enumerate(shown)}
    y = separator_y
    for row_index in range(capacity):
        y -= row_height
        measurement = by_row.get(row_index)
        _draw_cell(c, x, y, label_w, row_height, fill=white)
        _draw_cell(c, x + label_w, y, value_w, row_height, fill=PALE_YELLOW)
        if measurement is not None:
            circuit = measurement.get("circuito")
            value = measurement.get("caudal_medio_l_min")
            c.setFillColor(black)
            c.setFont("Helvetica", 7.2)
            c.drawString(x + 3, y + (row_height - 7.2) / 2 + 1, f"circuit {circuit}")
            _draw_centered(c, _format_number(value), x + label_w, y, value_w, row_height, size=7.5)
        else:
            c.setFillColor(black)
            c.setFont("Helvetica", 7.2)
            c.drawString(x + 3, y + (row_height - 7.2) / 2 + 1, "circuit")
    return overflow


def _draw_main_page(
    c: canvas.Canvas,
    *,
    mold: str,
    measurements: list[dict[str, Any]],
    operators: list[str],
    exported_at: str,
    record_value: str,
    pdf_title:str,
) -> list[dict[str, Any]]:
    c.setTitle(pdf_title)
    c.setAuthor("Flowmeter-App")
    c.setStrokeColor(BORDER_GREY)
    c.setLineWidth(0.8)
    c.rect(49, 48, 478, 746, stroke=1, fill=0)
    c.setStrokeColor(black)

    pressures = sorted({_format_number(item.get("pressao_entrada_bar")) for item in measurements if item.get("pressao_entrada_bar") not in (None, "")})
    _draw_header_fields(
        c,
        mold=mold,
        operators=operators,
        exported_at=exported_at,
        pressures=pressures or [""],
        record_name=record_value,
    )

    grouped = _measurement_map(measurements)
    top_y = 708
    overflow: list[dict[str, Any]] = []
    overflow.extend(
        _draw_flow_table(
            c,
            x=55,
            top_y=top_y,
            width=106,
            title="Fixed plate",
            measurements=grouped.get("Fixed plate", []),
            capacity=35,
            row_height=15.7,
        )
    )
    overflow.extend(
        _draw_flow_table(
            c,
            x=170,
            top_y=top_y,
            width=106,
            title="Moving Plate",
            measurements=grouped.get("Moving Plate", []),
            capacity=35,
            row_height=15.7,
        )
    )
    overflow.extend(
        _draw_flow_table(
            c,
            x=285,
            top_y=top_y,
            width=106,
            title="Middle Plate",
            measurements=grouped.get("Middle Plate", []),
            capacity=35,
            row_height=15.7,
        )
    )
    overflow.extend(
        _draw_flow_table(
            c,
            x=400,
            top_y=top_y,
            width=125,
            title="Jiggle",
            measurements=grouped.get("Jiggle", []),
            capacity=10,
            row_height=17.0,
        )
    )
    overflow.extend(
        _draw_flow_table(
            c,
            x=400,
            top_y=438,
            width=125,
            title="Cam Slide",
            measurements=grouped.get("Cam Slide", []),
            capacity=10,
            row_height=17.0,
        )
    )
    return overflow


def _draw_remarks_page(
    c: canvas.Canvas,
    *,
    mold: str,
    measurements: list[dict[str, Any]],
    operators: list[str],
    exported_at: str,
    overflow: list[dict[str, Any]],
) -> None:
    c.setStrokeColor(BORDER_GREY)
    c.setLineWidth(0.8)
    c.rect(49, 765, 478, 36, stroke=1, fill=0)
    c.setStrokeColor(black)
    _draw_cell(c, 55, 771, 82, 18, fill=LIGHT_GREY, line_width=0.8)
    _draw_cell(c, 137, 771, 384, 18, fill=white, line_width=0.8)
    _draw_centered(c, "Remarks:", 55, 771, 82, 18, font="Helvetica-Bold", size=8.5)

    unique_pressures = sorted({_format_number(item.get("pressao_entrada_bar")) for item in measurements if item.get("pressao_entrada_bar") not in (None, "")})
    unique_diameters, _ = _diameter_summary(measurements)
    notes = [
        f"Molde: {mold}",
        f"Operadores: {', '.join(operators) or '-'}",
        f"Última atualização: {exported_at.replace('T', ' ')[:19]}",
        f"Medições incluídas: {len(measurements)}",
        f"Pressão(ões) de entrada: {', '.join(unique_pressures) or '-'} bar",
        f"Diâmetro(s): {', '.join(unique_diameters) or '-'}",
    ]
    if overflow:
        notes.append(
            "Existem medições acima da capacidade visual do modelo principal; "
            "essas medições são apresentadas na tabela de continuação abaixo."
        )

    c.setFillColor(black)
    text = c.beginText(62, 745)
    text.setFont("Helvetica", 9)
    text.setLeading(14)
    for note in notes:
        text.textLine(note)
    c.drawText(text)

    if overflow:
        y = 640
        c.setFillColor(black)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(62, y, "Continuação de medições")
        y -= 18
        headers = [("Lado", 120), ("Circuito", 70), ("Caudal médio (l/m)", 110), ("Operador", 100)]
        x = 62
        for title, width in headers:
            _draw_cell(c, x, y, width, 18, fill=LIGHT_GREY)
            _draw_centered(c, title, x, y, width, 18, font="Helvetica-Bold", size=7.5)
            x += width
        y -= 18
        for measurement in overflow:
            if y < 55:
                c.showPage()
                y = 770
            values = [
                normalize_side(measurement.get("lado")) or _safe_text(measurement.get("lado")),
                _safe_text(measurement.get("circuito")),
                _format_number(measurement.get("caudal_medio_l_min")),
                _safe_text(measurement.get("operador")),
            ]
            x = 62
            for value, (_, width) in zip(values, headers):
                _draw_cell(c, x, y, width, 18, fill=white)
                _draw_centered(c, value, x, y, width, 18, size=7.5)
                x += width
            y -= 18

def generate_flow_report(
    output_path: str | Path,
    *,
    mold: str,
    measurements: list[dict[str, Any]],
    exported_at: str | None = None,
) -> None:
    if not measurements:
        raise ValueError("Não existem medições para exportar.")

    unsupported_sides = sorted(
        {
            _safe_text(item.get("lado"))
            for item in measurements
            if normalize_side(item.get("lado")) is None
        }
    )

    if unsupported_sides:
        raise ValueError(
            "Lado(s) de molde não suportado(s): "
            + ", ".join(unsupported_sides)
        )

    # Validar e converter os diâmetros
    diameter_values, invalid_diameters = _diameter_summary(measurements)

    if invalid_diameters:
        raise ValueError(
            "Diâmetro(s) inválido(s): "
            + ", ".join(invalid_diameters)
            + ". Valores permitidos: "
            + ", ".join(VALID_DIAMETER_LABELS)
            + "."
        )

    if not diameter_values:
        raise ValueError(
            "As medições selecionadas não têm um diâmetro válido. "
            "Valores permitidos: "
            + ", ".join(VALID_DIAMETER_LABELS)
            + "."
        )

    # Valor que será apresentado no campo Record
    record_value = ", ".join(diameter_values)

    # Nome interno do documento PDF
    pdf_title = Path(output_path).stem

    exported_at = exported_at or datetime.now().isoformat(
        timespec="seconds"
    )

    operators = sorted(
        {
            _safe_text(item.get("operador"))
            for item in measurements
            if _safe_text(item.get("operador"))
        },
        key=str.casefold,
    )

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    c = canvas.Canvas(str(output), pagesize=A4)

    overflow = _draw_main_page(
        c,
        mold=mold,
        measurements=measurements,
        operators=operators,
        exported_at=exported_at,
        record_value=record_value,
        pdf_title=pdf_title,
    )

    c.showPage()

    _draw_remarks_page(
        c,
        mold=mold,
        measurements=measurements,
        operators=operators,
        exported_at=exported_at,
        overflow=overflow,
    )

    c.save()
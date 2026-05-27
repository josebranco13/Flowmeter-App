from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class MeasurementRecord:
    session_id: str
    operador: str
    molde: str
    diametro_mm: int
    pressao_entrada_bar: float
    lado: str
    circuito: int
    caudal_min_l_min: float
    caudal_medio_l_min: float
    caudal_max_l_min: float
    amostras: int
    medido_em: str


@dataclass
class MeasurementSession:
    session_id: str
    operador: str
    molde: str = ""
    diametro_mm: int = 0
    pressao_entrada_bar: float = 0.0
    circuitos_por_lado: dict[str, int] = field(default_factory=lambda: {"A": 0, "B": 0})
    estado: str = "em_medicao"
    criado_em: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    atualizado_em: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    enviado_em: str | None = None
    medicoes: list[dict[str, Any]] = field(default_factory=list)

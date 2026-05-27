from __future__ import annotations

from pathlib import Path


APP_WIDTH = 800
APP_HEIGHT = 480
APP_BG = "#2d3642"
PANEL_BG = "#f7f7f7"
PANEL_FG = "#111111"
DARK_PANEL = "#11151a"
BLUE = "#0788d8"
GREEN = "#37b85a"
RED = "#c91616"
YELLOW = "#f0b429"
GREY = "#d7d7d7"
BLACK = "#050505"
WHITE = "#ffffff"

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
SESSIONS_DIR = DATA_DIR / "sessoes"
SENT_DIR = DATA_DIR / "enviados"
CSV_PATH = DATA_DIR / "medicoes.csv"

DIAMETER_OPTIONS = [6, 8, 10, 12, 14, 16, 20, 25]
MENU_OPTIONS = ["Medir caudal", "Enviar dados"]
OPERATOR_OPTIONS = ["1001", "1002", "1003", "1004"]

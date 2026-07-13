from __future__ import annotations

from pathlib import Path


APP_WIDTH = 800
APP_HEIGHT = 480
MIN_UI_FONT_SIZE = 14
FOOTER_FONT_SIZE = 14
TABLE_FONT_SIZE = 13
RESULTS_TABLE_FONT_SIZE = 24
APP_BG = "#2d3642"
PANEL_BG = "#f7f7f7"
PANEL_FG = "#111111"
DARK_PANEL = "#11151a"
BLUE = "#0788d8"
GREEN = "#37b85a"
RED = "#e93939"
YELLOW = "#f0b429"
GREY = "#d7d7d7"
BLACK = "#050505"
WHITE = "#ffffff"

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
SESSIONS_DIR = DATA_DIR / "sessoes"
SENT_DIR = DATA_DIR / "enviados"
PDF_EXPORTS_DIR = DATA_DIR / "pdf_exportados"
MAIL_DRAFTS_DIR = DATA_DIR / "emails"
CSV_PATH = DATA_DIR / "medicoes.csv"

DIAMETER_OPTIONS = [3, 6, 10, 12, 20]
DIAMETER_LABELS = {
    3: "1/8",
    6: "1/4",
    10: "3/8",
    12: "1/2",
    20: "3/4",
}
MENU_OPTIONS = ["Medir caudal", "Medições feitas"]

FLOW_SENSOR_GPIO_PIN = 21
FLOW_SENSOR_CALIBRATION_FACTOR = 7.5
FLOW_SENSOR_UPDATE_MS = 1000

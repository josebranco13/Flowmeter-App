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
OPERATORS_PATH = DATA_DIR / "operadores.json"

DIAMETER_OPTIONS = [3, 6, 10, 12, 20]
MENU_OPTIONS = ["Medir caudal", "Enviar dados"]
OPERATOR_PASSWORDS = {
    "ADMIN": "7482",
    "AMADO": "1936",
    "ANGELOC": "6205",
    "BERNARDO": "8517",
    "CARLICIA": "3049",
    "DIOGOL": "9721",
    "JCSANTOS": "4658",
    "LUISMIGUEL": "2390",
    "MARCOPEREIRA": "5863",
    "MARTINHO": "7140",
    "MIGUEL": "0586",
    "PLOURENÇO": "3927",
    "RAFAELC": "8074",
    "RANA": "1469",
    "TONI": "6318",
}
OPERATOR_OPTIONS = list(OPERATOR_PASSWORDS.keys())

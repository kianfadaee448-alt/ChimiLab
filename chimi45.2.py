import json
import sys
import time
import re
import os
import math
import random
from collections import Counter
import sqlite3
import matplotlib
from molmass import Formula
import shutil
from datetime import datetime

matplotlib.use("Qt5Agg")

try:
    from PyQt5.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QLabel, QPushButton, QComboBox, QFrame, QGroupBox, QTextEdit,
        QTabWidget, QMessageBox, QDoubleSpinBox, QFormLayout, QTableWidget,
        QTableWidgetItem, QHeaderView, QSplitter, QLineEdit, QGridLayout,
        QListWidget, QSpinBox, QProgressBar, QScrollArea, QDialog, QToolTip, QFileDialog,
        QSizePolicy, QMenu, QInputDialog, QStackedLayout, QGraphicsDropShadowEffect,
        QScrollBar, QToolBar, QAction
    )
    from PyQt5.QtCore import Qt, QTimer, QRectF, QPropertyAnimation, pyqtProperty, QEasingCurve, QPointF, QSize, QRect
    from PyQt5.QtGui import QFont, QColor, QPainter, QPen, QLinearGradient, QPainterPath, QBrush, QRadialGradient, \
        QPixmap, QPdfWriter, QPageSize, QImage, QPainter as QPainterGui, QIcon
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
except ImportError as e:
    print(f"Error: {e}")
    sys.exit(0)

# تلاش برای وارد کردن کتابخانه های OpenGL (اگر نباشد برنامه کرش نمی کند)
HAS_OPENGL = False
try:
    from PyQt5.QtWidgets import QOpenGLWidget
    from OpenGL.GL import *
    from OpenGL.GLU import *
    HAS_OPENGL = True
except ImportError:
    pass

CUSTOM_REACTIONS = {}
CHEMILAB_DB = {}

FLASK_BREAK_TEMP = 500.0
HEAT_COOL_DELTA = 5.0
BROCHURE_FOLDER = "element_brochures"

SOLID_TYPE_KEYWORDS = (
    "Solid", "Metal", "Salt", "Powder", "Precipitate", "Alloy", "Mineral",
    "Element", "Oxide", "Ceramic", "Carbide", "Nitride", "Hydride", "Silicide",
    "Sulfide", "Refractory", "Semiconductor", "Magnet", "Halogen",
    "جامد", "فلز", "نمک", "رسوب", "پودر", "آلیاژ", "معدنی", "عنصر", "اکسید",
)
LIQUID_GAS_KEYWORDS = (
    "Liquid", "Gas", "Acid", "Base", "Solvent", "Alcohol", "Ether",
    "مایع", "گاز", "اسید", "باز", "حلال", "الکل",
)

BADGE_CATALOG = {
    "داغی ۲۰۰ درجه": ("🔥", "رسیدن به دمای ۲۰۰ درجه سانتی‌گراد"),
    "اولین واکنش": ("🧪", "کشف اولین واکنش شیمیایی"),
    "استاد فیلتر": ("⚗️", "استفاده از فیلتر جامدات"),
    "تیتراسیون حرفه‌ای": ("💧", "انجام تیتراسیون موفق"),
    "ایمنی آزمایشگاه": ("🛡️", "بدون شکستن ظرف در یک جلسه"),
}

# دیتابیس عناصر برای مدل اتمی بور (Z: [Name, Symbol, Category, State, Neutrons, [Compounds]])
ATOMIC_DB = {
    1: ("هیدروژن", "H", "نافلز", "گاز", 0, ["H₂O", "HCl", "CH₄", "NH₃"]),
    2: ("هلیوم", "He", "نافلز (گاز نجیب)", "گاز", 2, []),
    3: ("لیتیوم", "Li", "فلز قلیایی", "جامد", 4, ["Li₂CO₃", "Li₂O"]),
    4: ("بریلیوم", "Be", "فلز قلیایی خاکی", "جامد", 5, ["BeO", "BeCl₂"]),
    5: ("بور", "B", "شبه‌فلز", "جامد", 6, ["H₃BO₃", "B₄C"]),
    6: ("کربن", "C", "نافلز", "جامد", 6, ["CO₂", "CH₄", "CaCO₃"]),
    7: ("نیتروژن", "N", "نافلز", "گاز", 7, ["NH₃", "HNO₃", "NO₂"]),
    8: ("اکسیژن", "O", "نافلز", "گاز", 8, ["H₂O", "CO₂", "MgO", "Al₂O₃"]),
    9: ("فلوئور", "F", "نافلز (هالوژن)", "گاز", 10, ["HF", "CaF₂"]),
    10: ("نئون", "Ne", "نافلز (گاز نجیب)", "گاز", 10, []),
    11: ("سدیم", "Na", "فلز قلیایی", "جامد", 12, ["NaCl", "NaOH", "Na₂CO₃"]),
    12: ("منیزیم", "Mg", "فلز قلیایی خاکی", "جامد", 12, ["MgO", "MgSO₄", "MgCl₂"]),
    13: ("آلومینیوم", "Al", "فلز", "جامد", 14, ["Al₂O₃", "AlCl₃", "Al₂(SO₄)₃"]),
    14: ("سیلیسیم", "Si", "شبه‌فلز", "جامد", 14, ["SiO₂", "SiC"]),
    15: ("فسفر", "P", "نافلز", "جامد", 16, ["H₃PO₄", "PH₃", "P₂O₅"]),
    16: ("گوگرد", "S", "نافلز", "جامد", 16, ["H₂SO₄", "H₂S", "SO₂"]),
    17: ("کلر", "Cl", "نافلز (هالوژن)", "گاز", 18, ["NaCl", "HCl", "KCl"]),
    18: ("آرگون", "Ar", "نافلز (گاز نجیب)", "گاز", 22, []),
    19: ("پتاسیم", "K", "فلز قلیایی", "جامد", 20, ["KCl", "KNO₃", "KOH"]),
    20: ("کلسیم", "Ca", "فلز قلیایی خاکی", "جامد", 20, ["CaCO₃", "CaO", "CaSO₄"]),
    21: ("اسکاندیم", "Sc", "فلز واسطه", "جامد", 24, []),
    22: ("تیتانیوم", "Ti", "فلز واسطه", "جامد", 26, ["TiO₂"]),
    23: ("وانادیم", "V", "فلز واسطه", "جامد", 28, ["V₂O₅"]),
    24: ("کروم", "Cr", "فلز واسطه", "جامد", 28, ["K₂Cr₂O₇"]),
    25: ("منگنز", "Mn", "فلز واسطه", "جامد", 30, ["KMnO₄", "MnO₂"]),
    26: ("آهن", "Fe", "فلز واسطه", "جامد", 30, ["Fe₂O₃", "FeSO₄", "FeCl₃"]),
    27: ("کبالت", "Co", "فلز واسطه", "جامد", 32, ["CoCl₂"]),
    28: ("نیکل", "Ni", "فلز واسطه", "جامد", 30, ["NiSO₄"]),
    29: ("مس", "Cu", "فلز واسطه", "جامد", 34, ["CuSO₄", "CuO", "CuCl₂"]),
    30: ("روی", "Zn", "فلز واسطه", "جامد", 34, ["ZnO", "ZnSO₄", "ZnCl₂"]),
    31: ("گالیوم", "Ga", "فلز", "جامد", 38, ["GaAs"]),
    32: ("ژرمانیوم", "Ge", "شبه‌فلز", "جامد", 40, ["GeO₂"]),
    33: ("آرسنیک", "As", "شبه‌فلز", "جامد", 42, ["As₂O₃"]),
    34: ("سلنیوم", "Se", "نافلز", "جامد", 44, ["H₂Se"]),
    35: ("برم", "Br", "نافلز (هالوژن)", "مایع", 44, ["NaBr", "HBr"]),
    36: ("کریپتون", "Kr", "نافلز (گاز نجیب)", "گاز", 48, []),
    37: ("روبیدیوم", "Rb", "فلز قلیایی", "جامد", 48, []),
    38: ("استرانسیوم", "Sr", "فلز قلیایی خاکی", "جامد", 50, []),
    39: ("ایتریوم", "Y", "فلز واسطه", "جامد", 50, []),
    40: ("زیرکونیوم", "Zr", "فلز واسطه", "جامد", 51, []),
    41: ("نیوبیوم", "Nb", "فلز واسطه", "جامد", 52, []),
    42: ("مولیبدن", "Mo", "فلز واسطه", "جامد", 54, []),
    43: ("تکنسیم", "Tc", "فلز واسطه", "جامد", 55, []),
    44: ("روتنیم", "Ru", "فلز واسطه", "جامد", 57, []),
    45: ("رودیوم", "Rh", "فلز واسطه", "جامد", 58, []),
    46: ("پالادیوم", "Pd", "فلز واسطه", "جامد", 60, []),
    47: ("نقره", "Ag", "فلز واسطه", "جامد", 61, []),
    48: ("کادمیوم", "Cd", "فلز واسطه", "جامد", 64, []),
    49: ("ایندیوم", "In", "فلز واسطه ضعیف", "جامد", 66, []),
    50: ("قلع", "Sn", "فلز واسطه ضعیف", "جامد", 69, []),
    51: ("آنتیموان", "Sb", "شبه‌فلز", "جامد", 71, []),
    52: ("تلوریوم", "Te", "شبه‌فلز", "جامد", 76, []),
    53: ("ید", "I", "هالوژن", "جامد", 74, []),
    54: ("زنون", "Xe", "گاز نجیب", "گاز", 77, []),
    55: ("سزیم", "Cs", "فلز قلیایی", "جامد", 78, []),
    56: ("باریوم", "Ba", "فلز قلیایی خاکی", "جامد", 81, []),
    57: ("لانتان", "La", "لانتانید", "جامد", 82, []),
    58: ("سریوم", "Ce", "لانتانید", "جامد", 82, []),
    59: ("پرازئودیمیم", "Pr", "لانتانید", "جامد", 82, []),
    60: ("نئودیمیم", "Nd", "لانتانید", "جامد", 84, []),
    61: ("پرومتیم", "Pm", "لانتانید", "جامد", 84, []),
    62: ("ساماریم", "Sm", "لانتانید", "جامد", 88, []),
    63: ("اروپیم", "Eu", "لانتانید", "جامد", 89, []),
    64: ("گادولینیم", "Gd", "لانتانید", "جامد", 93, []),
    65: ("تربیم", "Tb", "لانتانید", "جامد", 94, []),
    66: ("دیسپروزیم", "Dy", "لانتانید", "جامد", 97, []),
    67: ("هولمیم", "Ho", "لانتانید", "جامد", 98, []),
    68: ("اربیم", "Er", "لانتانید", "جامد", 99, []),
    69: ("تولیم", "Tm", "لانتانید", "جامد", 100, []),
    70: ("ایتربیم", "Yb", "لانتانید", "جامد", 103, []),
    71: ("لوتتیم", "Lu", "لانتانید", "جامد", 104, []),
    72: ("هافنیم", "Hf", "فلز واسطه", "جامد", 106, []),
    73: ("تانتال", "Ta", "فلز واسطه", "جامد", 108, []),
    74: ("تنگستن", "W", "فلز واسطه", "جامد", 110, []),
    75: ("رنیوم", "Re", "فلز واسطه", "جامد", 111, []),
    76: ("اسمیم", "Os", "فلز واسطه", "جامد", 114, []),
    77: ("ایریدیم", "Ir", "فلز واسطه", "جامد", 115, []),
    78: ("پلاتین", "Pt", "فلز واسطه", "جامد", 117, []),
    79: ("طلا", "Au", "فلز واسطه", "جامد", 118, []),
    80: ("جیوه", "Hg", "فلز واسطه", "مایع", 121, []),
    81: ("تالیم", "Tl", "فلز واسطه ضعیف", "جامد", 123, []),
    82: ("سرب", "Pb", "فلز واسطه ضعیف", "جامد", 125, []),
    83: ("بیسموت", "Bi", "فلز واسطه ضعیف", "جامد", 126, []),
    84: ("پولونیم", "Po", "شبه‌فلز", "جامد", 125, []),
    85: ("استاتین", "At", "هالوژن", "جامد", 125, []),
    86: ("رادون", "Rn", "گاز نجیب", "گاز", 136, []),
    87: ("فرانسیم", "Fr", "فلز قلیایی", "جامد", 136, []),
    88: ("رادیوم", "Ra", "فلز قلیایی خاکی", "جامد", 138, []),
    89: ("اکتینیم", "Ac", "آکتینید", "جامد", 138, []),
    90: ("توریم", "Th", "آکتینید", "جامد", 142, []),
    91: ("پروتاکتینیم", "Pa", "آکتینید", "جامد", 140, []),
    92: ("اورانیوم", "U", "آکتینید", "جامد", 146, []),
    93: ("نپتونیوم", "Np", "آکتینید", "جامد", 144, []),
    94: ("پلوتونیوم", "Pu", "آکتینید", "جامد", 150, []),
    95: ("امریسیم", "Am", "آکتینید", "جامد", 148, []),
    96: ("کوریم", "Cm", "آکتینید", "جامد", 151, []),
    97: ("برکلیم", "Bk", "آکتینید", "جامد", 150, []),
    98: ("کالیفرنیم", "Cf", "آکتینید", "جامد", 153, []),
    99: ("اینشتینیم", "Es", "آکتینید", "جامد", 153, []),
    100: ("فرمیم", "Fm", "آکتینید", "جامد", 157, []),
    101: ("مندلیفیم", "Md", "آکتینید", "جامد", 157, []),
    102: ("نوبلیم", "No", "آکتینید", "جامد", 157, []),
    103: ("لورنسیم", "Lr", "آکتینید", "جامد", 159, []),
    104: ("رادرفوردیم", "Rf", "فلز واسطه", "جامد", 163, []),
    105: ("دوبنیم", "Db", "فلز واسطه", "جامد", 163, []),
    106: ("سیبورگیم", "Sg", "فلز واسطه", "جامد", 165, []),
    107: ("بوریم", "Bh", "فلز واسطه", "جامد", 165, []),
    108: ("هاسیم", "Hs", "فلز واسطه", "جامد", 169, []),
    109: ("مایتنریم", "Mt", "فلز واسطه", "جامد", 169, []),
    110: ("دارمشتادیم", "Ds", "فلز واسطه", "جامد", 171, []),
    111: ("رونتگنیم", "Rg", "فلز واسطه", "جامد", 171, []),
    112: ("کوپرنیسیم", "Cn", "فلز واسطه", "جامد", 173, []),
    113: ("نیهونیم", "Nh", "فلز واسطه ضعیف", "جامد", 173, []),
    114: ("فلروویم", "Fl", "فلز واسطه ضعیف", "جامد", 175, []),
    115: ("موسکوویم", "Mc", "فلز واسطه ضعیف", "جامد", 173, []),
    116: ("لیورموریم", "Lv", "فلز واسطه ضعیف", "جامد", 177, []),
    117: ("تنسین", "Ts", "هالوژن", "جامد", 177, []),
    118: ("اوگانسون", "Og", "گاز نجیب", "گاز", 176, [])
}

def get_save_path():
    return os.path.join(get_app_base_dir(), "lab_save.json")


def get_brochure_dir():
    path = os.path.join(get_app_base_dir(), BROCHURE_FOLDER)
    os.makedirs(path, exist_ok=True)
    return path


def get_brochure_path(symbol):
    """مسیر بروشور عنصر — نام فایل: نماد شیمیایی (مثلاً C.png یا H.jpg)"""
    folder = get_brochure_dir()
    for ext in (".png", ".jpg", ".jpeg", ".webp", ".bmp"):
        candidate = os.path.join(folder, f"{symbol}{ext}")
        if os.path.exists(candidate):
            return candidate
    return None


def normalize_chem_formula(formula):
    if not formula:
        return ""
    text = str(formula).strip()
    text = text.translate(str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789"))
    text = text.translate(str.maketrans("⁺⁻", "+-"))
    return text


def is_solid_chemical_type(ctype):
    if not ctype:
        return False
    ctype = str(ctype)
    if any(k in ctype for k in LIQUID_GAS_KEYWORDS):
        if not any(k in ctype for k in SOLID_TYPE_KEYWORDS):
            return False
    return any(k in ctype for k in SOLID_TYPE_KEYWORDS)


def get_app_base_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.abspath(".")


def get_db_path():
    base_dir = get_app_base_dir()
    local_db = os.path.join(base_dir, "db.db")
    if not os.path.exists(local_db) and hasattr(sys, '_MEIPASS'):
        bundled_db = os.path.join(sys._MEIPASS, "db.db")
        if os.path.exists(bundled_db):
            try:
                shutil.copy2(bundled_db, local_db)
            except:
                return bundled_db
    return local_db


def normalize_key(key):
    if not key: return ""
    key = re.sub(
        r'\s+(heat|light|conc|dilute|steam|aq|excess|limited|slow|cold|hot|dissolved|decay|solid|liquid|gas|catalyst).*',
        '', str(key), flags=re.IGNORECASE)
    key = re.sub(r'\((s|g|l|aq|solid|gas|liquid)\)', '', key, flags=re.IGNORECASE)
    return key.strip().lower()


def load_databases():
    db_path = get_db_path()
    if not os.path.exists(db_path):
        # دیتای پیشفرض در صورت نبود فایل
        CHEMILAB_DB["h2o"] = {"name": "آب", "type": "Liquid", "pH": 7.0, "molarity": 55.5, "heat": 0.0,
                              "color": "#aaddff", "formula": "H2O"}
        CHEMILAB_DB["hcl"] = {"name": "هیدروکلریک اسید", "type": "Strong Acid", "pH": 1.0, "molarity": 1.0, "heat": 0.0,
                              "color": "#ffffff", "formula": "HCl"}
        CHEMILAB_DB["naoh"] = {"name": "سدیم هیدروکسید", "type": "Strong Base", "pH": 13.0, "molarity": 1.0,
                               "heat": -44.5, "color": "#eeeeee", "formula": "NaOH"}
        CHEMILAB_DB["agcl"] = {"name": "نقره کلرید", "type": "Precipitate", "pH": 7.0, "molarity": 0.0, "heat": 0.0,
                               "color": "#ffffff", "formula": "AgCl"}
        CHEMILAB_DB["co2"] = {"name": "کربن دی اکسید", "type": "Gas", "pH": 5.5, "molarity": 0.0, "heat": 0.0,
                              "color": "#dddddd", "formula": "CO2"}
        CUSTOM_REACTIONS["خنثی سازی HCl"] = {"reactants": ["hcl", "naoh"], "products": ["h2o", "nacl"],
                                             "desc": "خنثی سازی", "xp": 50, "temp_min": -273}
        CUSTOM_REACTIONS["رسوب AgCl"] = {"reactants": ["agno3", "hcl"], "products": ["agcl", "hno3"],
                                         "desc": "رسوب‌گذاری", "xp": 40, "temp_min": -273}
        return

    try:
        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()

        def parse_db_list(val):
            if isinstance(val, list): return val
            if not val or str(val).strip() == "": return []
            val_str = str(val).strip()
            if val_str.startswith('[') and val_str.endswith(']'):
                try:
                    return json.loads(val_str.replace("'", '"'))
                except:
                    pass
            return [x.strip(" []\"'") for x in val_str.split(',')]

        cursor.execute("SELECT * FROM custom_reactions WHERE 1")
        for i in cursor.fetchall():
            fa_name = str(i[1])
            try:
                xp_val = int(i[5])
            except:
                xp_val = 0
            try:
                temp_min_val = float(i[6])
            except:
                temp_min_val = 0

            CUSTOM_REACTIONS[fa_name] = {
                "reactants": parse_db_list(i[2]), "products": parse_db_list(i[3]),
                "desc": str(i[4]), "xp": xp_val, "temp_min": temp_min_val,
            }

        cursor.execute("SELECT * FROM chemilab WHERE 1")
        for i in cursor.fetchall():
            fa_name = normalize_key(str(i[2]))
            try:
                ph_val = float(i[4])
            except:
                ph_val = 7.0
            try:
                mol_val = float(i[5])
            except:
                mol_val = 0.1
            try:
                heat_val = float(i[6])
            except:
                heat_val = 0.0

            CHEMILAB_DB[fa_name] = {
                "name": str(i[1]), "type": str(i[3]), "pH": ph_val,
                "molarity": mol_val, "heat": heat_val, "color": str(i[7]), "formula": str(i[8]),
            }
        connection.close()
    except:
        pass


load_databases()

FONT_NAME = "Tahoma"
APP_STYLE_DARK = """
QMainWindow { background-color: #0d0d14; }
QWidget { color: #cdd6f4; font-family: 'Tahoma', sans-serif; font-size: 13px; }
QGroupBox { border: 2px solid #313244; border-radius: 8px; margin-top: 15px; background-color: #161622; font-weight: bold; }
QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top center; padding: 0 10px; background-color: #0d0d14; color: #89b4fa; border-radius: 4px; }
QPushButton { background-color: #313244; border: 1px solid #45475a; border-radius: 6px; padding: 8px 16px; color: #cdd6f4; font-weight: bold; font-size: 14px; }
QPushButton:hover { background-color: #45475a; border: 1px solid #89b4fa; }
QPushButton:pressed { background-color: #11111b; border: 2px solid #fab387; padding-top: 10px; } 
QPushButton:checked { background-color: #a6e3a1; color: #11111b; border: 2px solid #94e2d5; }
QLineEdit { background-color: #1e1e2e; border: 1px solid #45475a; border-radius: 4px; padding: 5px; color: #a6e3a1; font-weight: bold; }
QComboBox, QDoubleSpinBox, QSpinBox { background-color: #1e1e2e; border: 1px solid #45475a; border-radius: 4px; padding: 5px; color: #cdd6f4; }
QListWidget { background-color: #11111b; border: 1px solid #313244; border-radius: 6px; color: #cdd6f4; font-size: 14px; }
QTableWidget { background-color: #11111b; gridline-color: #313244; color: #cdd6f4; border: 1px solid #313244; border-radius: 6px; }
QHeaderView::section { background-color: #1e1e2e; padding: 6px; border: 1px solid #313244; color: #f9e2af; font-weight: bold; }
QTextEdit { background-color: #11111b; border: 1px solid #313244; border-radius: 4px; color: #a6e3a1; }
QTabWidget::pane { border: 1px solid #313244; background: #161622; border-radius: 8px; }
QTabBar::tab { background: #313244; color: #cdd6f4; padding: 8px 12px; margin-right: 2px; border-top-left-radius: 6px; border-top-right-radius: 6px; }
QTabBar::tab:selected { background: #89b4fa; color: #1e1e2e; font-weight: bold; }
QProgressBar { border: 2px solid #45475a; border-radius: 5px; text-align: center; color: white; background-color: #1e1e2e; }
QProgressBar::chunk { background-color: #fab387; width: 20px; }
QScrollArea { border: none; background-color: transparent; }
QDialog { background-color: #161622; }
QLabel#theme_btn { color: #f9e2af; font-size: 16px; font-weight: bold; }
QToolBar { background-color: #161622; border: none; spacing: 10px; }
QToolBar QPushButton { background-color: #313244; border: 1px solid #45475a; border-radius: 6px; padding: 6px 12px; color: #cdd6f4; font-weight: bold; font-size: 13px; }
QToolBar QPushButton:hover { background-color: #45475a; border: 1px solid #89b4fa; }
"""

APP_STYLE_LIGHT = """
QMainWindow { background-color: #f0f0f5; }
QWidget { color: #2c2e3e; font-family: 'Tahoma', sans-serif; font-size: 13px; }
QGroupBox { border: 2px solid #b0b0c0; border-radius: 8px; margin-top: 15px; background-color: #ffffff; font-weight: bold; }
QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top center; padding: 0 10px; background-color: #f0f0f5; color: #1a5fb4; border-radius: 4px; }
QPushButton { background-color: #e0e0eb; border: 1px solid #b0b0c0; border-radius: 6px; padding: 8px 16px; color: #2c2e3e; font-weight: bold; font-size: 14px; }
QPushButton:hover { background-color: #d0d0e0; border: 1px solid #1a5fb4; }
QPushButton:pressed { background-color: #c0c0d0; border: 2px solid #e66100; padding-top: 10px; } 
QPushButton:checked { background-color: #2ec27e; color: #ffffff; border: 2px solid #26a269; }
QLineEdit { background-color: #ffffff; border: 1px solid #b0b0c0; border-radius: 4px; padding: 5px; color: #1a5fb4; font-weight: bold; }
QComboBox, QDoubleSpinBox, QSpinBox { background-color: #ffffff; border: 1px solid #b0b0c0; border-radius: 4px; padding: 5px; color: #2c2e3e; }
QListWidget { background-color: #ffffff; border: 1px solid #b0b0c0; border-radius: 6px; color: #2c2e3e; font-size: 14px; }
QTableWidget { background-color: #ffffff; gridline-color: #d0d0e0; color: #2c2e3e; border: 1px solid #b0b0c0; border-radius: 6px; }
QHeaderView::section { background-color: #e0e0eb; padding: 6px; border: 1px solid #b0b0c0; color: #e66100; font-weight: bold; }
QTextEdit { background-color: #ffffff; border: 1px solid #b0b0c0; border-radius: 4px; color: #1a5fb4; }
QTabWidget::pane { border: 1px solid #b0b0c0; background: #ffffff; border-radius: 8px; }
QTabBar::tab { background: #e0e0eb; color: #2c2e3e; padding: 8px 12px; margin-right: 2px; border-top-left-radius: 6px; border-top-right-radius: 6px; }
QTabBar::tab:selected { background: #1a5fb4; color: #ffffff; font-weight: bold; }
QProgressBar { border: 2px solid #b0b0c0; border-radius: 5px; text-align: center; color: black; background-color: #ffffff; }
QProgressBar::chunk { background-color: #e66100; width: 20px; }
QScrollArea { border: none; background-color: transparent; }
QDialog { background-color: #ffffff; }
QLabel#theme_btn { color: #1a5fb4; font-size: 16px; font-weight: bold; }
QToolBar { background-color: #f0f0f5; border: none; spacing: 10px; }
QToolBar QPushButton { background-color: #e0e0eb; border: 1px solid #b0b0c0; border-radius: 6px; padding: 6px 12px; color: #2c2e3e; font-weight: bold; font-size: 13px; }
QToolBar QPushButton:hover { background-color: #d0d0e0; border: 1px solid #1a5fb4; }
"""

TYPE_MAP = {
    "Strong Acid": "مایع (اسید قوی)", "Weak Acid": "مایع (اسید ضعیف)", "Strong Base": "مایع (باز قوی)",
    "Weak Base": "مایع (باز ضعیف)", "Acid": "مایع (اسید)", "Base": "مایع (باز)", "Superacid": "ابر اسید",
    "Superacid Base": "پایه ابر اسید", "Acidic Oxide": "اکسید اسیدی", "Gas": "گاز", "Liquid": "مایع",
    "Solid": "جامد", "Metal": "جامد (فلز)", "Oxide": "جامد (اکسید)", "Salt": "جامد (نمک)",
    "Element": "جامد (عنصر)", "Halogen": "هالوژن", "Ion": "یون", "Complex": "کمپلکس", "Precipitate": "جامد (رسوب)",
    "Alloy": "آلیاژ", "Mineral": "معدنی", "Organic Compound": "ترکیب آلی", "Organic": "ماده آلی",
    "Organometallic": "ترکیب آلی-فلزی", "Hydrocarbon": "هیدروکربن", "Alkane": "آلکان", "Alcohol": "مایع (الکل)",
    "Aldehyde": "آلدئید", "Ester": "استر", "Ether": "اتر", "Epoxide": "اپوکسید", "Sugar": "قند (کربوهیدرات)",
    "Carb": "کربوهیدرات", "Fatty Acid": "اسید چرب", "Amino Acid": "آمینو اسید", "Protein": "پروتئین",
    "Enzyme": "آنزیم", "Lipid": "لیپید (چربی)", "Alkaloid": "آلکالوئید", "Solvent": "مایع (حلال)",
    "Monomer": "مونومر", "Polymer": "پلیمر", "Catalyst": "کاتالیزور", "Chelating Agent": "عامل کلات‌کننده",
    "Fixative": "تثبیت‌کننده", "Lubricant": "روان‌کننده", "Abrasive": "سایینده", "Refrigerant": "مبرد (سرمازا)",
    "Battery Material": "ماده باتری", "Fuel": "سوخت", "Precursor": "پیش‌ماده", "Semiconductor": "نیمه‌هادی",
    "Superconductor": "ابررسانا", "Dopant": "ناخالصی (دوپ‌کننده)", "Dielectric": "دی‌الکتریک (عایق)",
    "Phosphor": "فسفر (ماده تابناک)", "Magnet": "آهنربا", "Photovoltaic": "فوتوولتائیک",
    "Nanomaterial": "نانومواد", "Conductor": "رسانا", "Oxidizer": "اکسیدکننده", "Explosive": "ماده منفجره",
    "Primary Explosive": "منفجره اولیه", "Radioactive": "رادیواکتیو", "Radioisotope": "رادیوایزوتوپ",
    "Pollutant": "آلاینده", "Forever Chemical": "مواد شیمیایی ماندگار (PFAS)", "Moderator": "کندکننده نوترون",
    "Superheavy": "عنصر فوق سنگین", "Medicine": "دارو", "Carbide": "کاربید", "Nitride": "نیترید",
    "Hydride": "هیدرید", "Silicide": "سیلیسید", "Sulfide": "سولفید", "Ceramic": "سرامیک",
    "Refractory": "دیرگداز", "Neurotoxin": "سم عصبی (نوروتوکسین)", "Molten Salt": "نمک مذاب",
    "Thermoelectric": "ترمو الکتریک", "Reagent": "واکنش‌گر (ری‌اجنت)", "Electrolyte": "الکترولیت",
    "Reducing Agent": "عامل کاهنده", "Toxin": "سم (توکسین)", "Sugar Alcohol": "قند الکلی",
    "Fiber Optic": "فیبر نوری", "Ozone Depleting": "تخریب‌کننده لایه ازون", "Choking Agent": "عامل خفه‌کننده",
    "Scintillator": "سوسوزن", "Radioactive Gas": "گاز رادیواکتیو", "Photocatalyst": "فوتوکاتالیزور",
    "Medical": "پزشکی", "Antimicrobial": "ضد میکروب", "Additive": "افزودنی", "Thermal Storage": "ذخیره‌ساز حرارتی",
    "Etchant": "خورنده", "Stable Isotope": "ایزوتوپ پایدار", "Flow Battery": "باتری جریانی",
    "Phenol": "فنول", "Optical": "نوری", "Shielding": "محافظ", "Herbicide": "علف‌کش",
    "Propellant": "پیش‌ران", "Greenhouse Gas": "گاز گلخانه‌ای", "Interhalogen": "بین‌هالوژنی",
    "Contrast Agent": "عامل تضاد", "Blister Agent": "عامل تاول‌زا", "Nerve Agent": "عامل اعصاب",
    "Insulator": "عایق",
}


def get_persian_type(eng_type):
    for k, v in TYPE_MAP.items():
        if k in eng_type:
            return v
    return eng_type


class ChemicalCalculator:
    SUBSCRIPTS = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")
    SUPERSCRIPTS = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")

    @staticmethod
    def to_subscript(text):
        if not text: return ""
        return text.translate(ChemicalCalculator.SUBSCRIPTS)

    @staticmethod
    def to_superscript(text):
        if not text: return ""
        return str(text).translate(ChemicalCalculator.SUPERSCRIPTS)

    @staticmethod
    def parse_formula(formula):
        if formula in ["Mix", "-", None]: return Counter()
        formula = normalize_chem_formula(formula)
        try:
            f = Formula(formula)
            composition = Counter()
            for el in f.composition.keys():
                composition[el] = int(round(f.composition[el]))
            return composition
        except Exception:
            elements = re.findall(r'([A-Z][a-z]*)(\d*)', formula)
            composition = Counter()
            for el, count in elements:
                composition[el] += int(count) if count else 1
            return composition

    @staticmethod
    def calculate_empirical_from_moles(atom_moles_counter):
        if not atom_moles_counter:
            return "ماده‌ای وجود ندارد"
        filtered_atoms = {k: v for k, v in atom_moles_counter.items() if v > 1e-6}
        if not filtered_atoms:
            return "-"
        # اگر فقط یک عنصر باشد، فرمول آن عنصر با تعداد نسبی
        if len(filtered_atoms) == 1:
            el, mol = next(iter(filtered_atoms.items()))
            # ساده‌سازی به کوچکترین عدد صحیح
            # برای تعداد مول، اگر عدد صحیح باشد یا نزدیک به عدد صحیح، استفاده می‌کنیم
            ratio = mol
            # سعی می‌کنیم به عدد صحیح نزدیک کنیم
            if abs(ratio - round(ratio)) < 0.01:
                count = int(round(ratio))
            else:
                # اگر نه، کسر را به صورت عدد اعشاری نشان می‌دهیم (اما معمولاً فرمول به صورت کسر نیست)
                count = ratio
            if count == 1:
                return el
            else:
                return f"{el}{count}"
        # محاسبه نسبت‌ها
        min_mole = min(filtered_atoms.values())
        if min_mole < 1e-9:
            return "ناچیز"
        ratios = {k: v / min_mole for k, v in filtered_atoms.items()}
        # پیدا کردن ضریب مناسب
        best_multiplier = 1
        best_error = float('inf')
        for m in range(1, 31):
            current_error = sum(abs(r * m - round(r * m)) for r in ratios.values())
            if current_error < best_error:
                best_error = current_error
                best_multiplier = m
            if current_error < 0.05:
                break
        # ترتیب عناصر: C, H, سپس بقیه به ترتیب الفبا
        sorted_elements = []
        keys = list(filtered_atoms.keys())
        if 'C' in keys:
            sorted_elements.append('C')
            keys.remove('C')
        if 'H' in keys:
            sorted_elements.append('H')
            keys.remove('H')
        keys.sort()
        sorted_elements.extend(keys)
        formula_str = ""
        for el in sorted_elements:
            final_count = int(round(ratios[el] * best_multiplier))
            if final_count > 0:
                display_str = "" if final_count == 1 else str(final_count)
                formula_str += f"{el}{display_str}"
        return ChemicalCalculator.to_subscript(formula_str)


# ----------------- کلاس‌ها و منطق مدل بور -----------------
def get_electron_shells(z):
    shells = [0] * 7
    orbitals = [
        (1, 2), (2, 2), (2, 6), (3, 2), (3, 6), (4, 2), (3, 10), (4, 6),
        (5, 2), (4, 10), (5, 6), (6, 2), (4, 14), (5, 10), (6, 6),
        (7, 2), (5, 14), (6, 10), (7, 6)
    ]
    rem = z
    for n, cap in orbitals:
        if rem <= 0:
            break
        fill = min(rem, cap)
        shells[n - 1] += fill
        rem -= fill
    return shells


class BohrCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 400)
        self.Z = 0
        self.shells = [0] * 7
        self.angle_offset = 0.0
        self.symbol = "?"
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.rotate_electrons)
        self.timer.start(30)

    def rotate_electrons(self):
        self.angle_offset += 0.015
        self.update()

    def update_atom(self, z, symbol):
        self.Z = max(0, min(118, z))
        self.symbol = symbol if self.Z > 0 else "?"
        self.shells = get_electron_shells(self.Z)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2

        n_rad = min(w, h) * 0.06
        grad_nucleus = QRadialGradient(cx - n_rad / 3, cy - n_rad / 3, n_rad * 1.5)
        grad_nucleus.setColorAt(0, QColor("#f9e2af"))
        grad_nucleus.setColorAt(1, QColor("#fab387").darker(150))
        painter.setBrush(QBrush(grad_nucleus))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(cx, cy), n_rad, n_rad)

        painter.setPen(QColor("#11111b"))
        font = painter.font()
        font.setPointSize(int(n_rad * 0.7))
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(QRectF(cx - n_rad, cy - n_rad, n_rad * 2, n_rad * 2), Qt.AlignCenter, self.symbol)

        base_radius = n_rad * 1.8
        active_shells = sum(1 for s in self.shells if s > 0)
        radius_step = (min(w, h) / 2 - base_radius - 10) / max(1, active_shells)

        shell_names = ['K', 'L', 'M', 'N', 'O', 'P', 'Q']
        for i in range(7):
            count = self.shells[i]
            if count == 0:
                continue
            r = base_radius + (i * radius_step)

            pen_shell = QPen(QColor("#45475a" if active_shells < 5 else "#6c7086"))
            pen_shell.setWidth(1)
            pen_shell.setStyle(Qt.DashLine)
            painter.setPen(pen_shell)
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(QPointF(cx, cy), r, r)

            painter.setPen(QColor("#89b4fa"))
            font_shell = painter.font()
            font_shell.setPointSize(8)
            painter.setFont(font_shell)
            painter.drawText(int(cx + r + 2), int(cy - 2), shell_names[i])

            step_angle = 2 * math.pi / count
            layer_angle = self.angle_offset * (1.5 - i * 0.1)

            for j in range(count):
                ang = layer_angle + j * step_angle
                ex = cx + r * math.cos(ang)
                ey = cy + r * math.sin(ang)

                painter.setBrush(QColor("#a6e3a1"))
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(QPointF(ex, ey), 4, 4)

        painter.setPen(QColor("#bac2de"))
        font_stat = painter.font()
        font_stat.setPointSize(9)
        painter.setFont(font_stat)
        stat_text = " | ".join([f"{shell_names[i]}:{self.shells[i]}" for i in range(7) if self.shells[i] > 0])
        painter.drawText(QRectF(10, h - 25, w, 25), Qt.AlignLeft | Qt.AlignVCenter, stat_text)


# --- 3D OpenGL Beaker Background ---
if HAS_OPENGL:
    class GLBeakerCanvas(QOpenGLWidget):
        """بشر شیشه‌ای سه‌بعدی با OpenGL"""
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setMinimumSize(450, 600)
            self.angle_x = 15.0
            self.angle_y = 25.0
            self.last_pos = None
            self.quadric = None
            self.stirrer_on = False
            self.stirrer_angle = 0.0
            self._stirrer_timer = QTimer(self)
            self._stirrer_timer.timeout.connect(self._tick_stirrer)
            self._stirrer_timer.start(30)

        def _tick_stirrer(self):
            if self.stirrer_on:
                self.stirrer_angle = (self.stirrer_angle + 12) % 360
                self.update()

        def initializeGL(self):
            glEnable(GL_DEPTH_TEST)
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            glEnable(GL_LIGHTING)
            glEnable(GL_LIGHT0)
            glEnable(GL_COLOR_MATERIAL)
            glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
            glLightfv(GL_LIGHT0, GL_POSITION, [2.0, 4.0, 6.0, 1.0])
            glLightfv(GL_LIGHT0, GL_AMBIENT, [0.35, 0.35, 0.4, 1.0])
            glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.85, 0.9, 1.0, 1.0])
            glClearColor(0.07, 0.07, 0.11, 1.0)
            self.quadric = gluNewQuadric()

        def resizeGL(self, w, h):
            glViewport(0, 0, max(1, w), max(1, h))
            glMatrixMode(GL_PROJECTION)
            glLoadIdentity()
            gluPerspective(38, w / max(h, 1), 0.1, 60.0)
            glMatrixMode(GL_MODELVIEW)

        def paintGL(self):
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glLoadIdentity()
            glTranslatef(0.0, -0.4, -7.0)
            glRotatef(self.angle_x, 1.0, 0.0, 0.0)
            glRotatef(self.angle_y, 0.0, 1.0, 0.0)

            # پایه بشر
            glColor4f(0.27, 0.27, 0.33, 1.0)
            glPushMatrix()
            glTranslatef(0, -2.6, 0)
            glRotatef(-90, 1, 0, 0)
            gluDisk(self.quadric, 0, 1.35, 32, 1)
            glPopMatrix()

            # بدنه بشر (استوانه شیشه‌ای)
            glDisable(GL_LIGHTING)
            glColor4f(0.75, 0.88, 1.0, 0.22)
            glBegin(GL_QUAD_STRIP)
            for i in range(37):
                ang = math.radians(i * 10)
                x = math.cos(ang) * 1.05
                z = math.sin(ang) * 1.05
                glVertex3f(x, -2.4, z)
                glVertex3f(x * 0.82, 1.8, z * 0.82)
            glEnd()

            # لبه و خطوط شیشه
            glLineWidth(2.0)
            glColor4f(0.9, 0.95, 1.0, 0.75)
            for y_top, radius in ((1.8, 0.82), (-2.4, 1.05)):
                glBegin(GL_LINE_LOOP)
                for i in range(36):
                    ang = math.radians(i * 10)
                    glVertex3f(math.cos(ang) * radius, y_top, math.sin(ang) * radius)
                glEnd()
            glEnable(GL_LIGHTING)

            # درپوش/لبه بالایی
            glColor4f(0.85, 0.92, 1.0, 0.35)
            glPushMatrix()
            glTranslatef(0, 1.85, 0)
            glRotatef(-90, 1, 0, 0)
            gluDisk(self.quadric, 0.75, 0.85, 32, 1)
            glPopMatrix()

            # نشانگر همزن مغناطیسی (میله در کف)
            if self.stirrer_on:
                glColor3f(0.85, 0.85, 0.9)
                glPushMatrix()
                glTranslatef(0, -2.35, 0)
                glRotatef(self.stirrer_angle, 0, 1, 0)
                glBegin(GL_QUADS)
                glVertex3f(-0.35, 0, -0.06)
                glVertex3f(0.35, 0, -0.06)
                glVertex3f(0.35, 0, 0.06)
                glVertex3f(-0.35, 0, 0.06)
                glEnd()
                glPopMatrix()

        def mousePressEvent(self, event):
            self.last_pos = event.pos()

        def mouseMoveEvent(self, event):
            if self.last_pos:
                dx = event.x() - self.last_pos.x()
                dy = event.y() - self.last_pos.y()
                self.angle_y += dx * 0.4
                self.angle_x = max(-10, min(45, self.angle_x + dy * 0.3))
                self.last_pos = event.pos()
                self.update()


# --- 3D OpenGL Bohr Model ---
if HAS_OPENGL:
    class GLBohrCanvas(QOpenGLWidget):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setMinimumSize(400, 400)
            self.Z = 0
            self.shells = [0] * 7
            self.angle_x = 20.0
            self.angle_y = 0.0
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.rotate_electrons)
            self.timer.start(30)
            self.last_pos = None

        def update_atom(self, z, symbol):
            self.Z = max(0, min(118, z))
            self.shells = get_electron_shells(self.Z)
            self.update()

        def rotate_electrons(self):
            self.angle_y += 1.0
            self.update()

        def initializeGL(self):
            glEnable(GL_DEPTH_TEST)
            glEnable(GL_LIGHTING)
            glEnable(GL_LIGHT0)
            glEnable(GL_COLOR_MATERIAL)
            glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
            glLightfv(GL_LIGHT0, GL_POSITION, [5.0, 5.0, 5.0, 1.0])
            glLightfv(GL_LIGHT0, GL_AMBIENT, [0.3, 0.3, 0.3, 1.0])
            glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.8, 0.8, 0.8, 1.0])
            glClearColor(0.05, 0.05, 0.08, 1.0)
            self.quadric = gluNewQuadric()

        def resizeGL(self, w, h):
            glViewport(0, 0, w, h)
            glMatrixMode(GL_PROJECTION)
            glLoadIdentity()
            gluPerspective(45, w / h, 0.1, 50.0)
            glMatrixMode(GL_MODELVIEW)

        def paintGL(self):
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glLoadIdentity()
            glTranslatef(0.0, 0.0, -10.0)
            glRotatef(self.angle_x, 1.0, 0.0, 0.0)
            glRotatef(self.angle_y * 0.2, 0.0, 1.0, 0.0)

            # Draw nucleus
            glColor3f(1.0, 0.7, 0.3)
            gluSphere(self.quadric, 0.5, 32, 32)

            # Draw shells and electrons
            active_shells = sum(1 for s in self.shells if s > 0)
            if active_shells == 0:
                return

            radius_step = 0.8
            for i in range(7):
                count = self.shells[i]
                if count == 0:
                    continue
                r = 0.8 + (i * radius_step)

                glDisable(GL_LIGHTING)
                glColor3f(0.3, 0.3, 0.4)
                glBegin(GL_LINE_LOOP)
                for a in range(0, 360, 5):
                    rad = math.radians(a)
                    glVertex3f(math.cos(rad) * r, 0, math.sin(rad) * r)
                glEnd()
                glEnable(GL_LIGHTING)

                step_angle = 360.0 / count
                layer_angle = self.angle_y * (1.5 - i * 0.1)

                for j in range(count):
                    ang = math.radians(layer_angle + j * step_angle)
                    ex = math.cos(ang) * r
                    ez = math.sin(ang) * r

                    glPushMatrix()
                    glTranslatef(ex, 0, ez)
                    glColor3f(0.5, 0.9, 0.5)
                    gluSphere(self.quadric, 0.1, 16, 16)
                    glPopMatrix()

        def mousePressEvent(self, event):
            self.last_pos = event.pos()

        def mouseMoveEvent(self, event):
            if self.last_pos:
                dx = event.x() - self.last_pos.x()
                dy = event.y() - self.last_pos.y()
                self.angle_x += dy * 0.5
                self.angle_y += dx * 0.5
                self.last_pos = event.pos()
                self.update()


class BohrModelWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.Z = 0
        self.setup_ui()
        self.update_info()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        left_panel = QFrame()
        left_panel.setStyleSheet("background-color: transparent; border: 2px solid #313244; border-radius: 10px;")
        v_left = QVBoxLayout(left_panel)

        title_lbl = QLabel("مدل اتمی بور و آرایش اوربیتالی (۱۱۸ عنصر)")
        title_lbl.setAlignment(Qt.AlignCenter)
        title_lbl.setStyleSheet("color: #89b4fa; font-size: 18px; font-weight: bold; margin: 5px; border:none;")
        v_left.addWidget(title_lbl)

        self._use_3d_bohr = HAS_OPENGL
        self.canvas_2d = BohrCanvas()
        if HAS_OPENGL:
            self.canvas_3d = GLBohrCanvas()
            self.canvas = self.canvas_3d
            self.lbl_bohr_mode = QLabel("💡 حالت سه‌بعدی — با ماوس بچرخانید.")
            self.lbl_bohr_mode.setStyleSheet("color: #a6e3a1; font-size: 11px; border:none;")
        else:
            self.canvas_3d = None
            self.canvas = self.canvas_2d
            self.lbl_bohr_mode = QLabel("⚠️ برای مدل سه‌بعدی کتابخانه PyOpenGL را نصب کنید.")
            self.lbl_bohr_mode.setStyleSheet("color: #f38ba8; font-size: 11px; border:none;")
        self.lbl_bohr_mode.setAlignment(Qt.AlignCenter)
        v_left.addWidget(self.lbl_bohr_mode)

        self.canvas_stack = QStackedLayout()
        stack_host = QWidget()
        stack_host.setLayout(self.canvas_stack)
        self.canvas_stack.addWidget(self.canvas_2d)
        if self.canvas_3d:
            self.canvas_stack.addWidget(self.canvas_3d)
            self.canvas_stack.setCurrentWidget(self.canvas_3d)
        else:
            self.canvas_stack.setCurrentWidget(self.canvas_2d)
        v_left.addWidget(stack_host, 1)

        self.btn_toggle_bohr_dim = QPushButton("🔄 تغییر حالت ۲بعدی / ۳بعدی")
        self.btn_toggle_bohr_dim.setStyleSheet(
            "background-color: #cba6f7; color: #1e1e2e; border:none; padding: 10px; font-weight: bold;")
        self.btn_toggle_bohr_dim.clicked.connect(self.toggle_bohr_dimension)
        if not HAS_OPENGL:
            self.btn_toggle_bohr_dim.setEnabled(False)
        v_left.addWidget(self.btn_toggle_bohr_dim)

        h_btn = QHBoxLayout()
        btn_add = QPushButton("➕ افزودن الکترون")
        btn_add.setStyleSheet("background-color: #a6e3a1; color: #1e1e2e; border:none; padding: 12px;")
        btn_add.clicked.connect(self.add_electron)

        btn_remove = QPushButton("➖ حذف آخرین")
        btn_remove.setStyleSheet("background-color: #f38ba8; color: #1e1e2e; border:none; padding: 12px;")
        btn_remove.clicked.connect(self.remove_electron)

        btn_reset = QPushButton("🌀 تخلیه مدارها")
        btn_reset.setStyleSheet("background-color: #89dceb; color: #1e1e2e; border:none; padding: 12px;")
        btn_reset.clicked.connect(self.reset_electrons)

        h_btn.addWidget(btn_add)
        h_btn.addWidget(btn_remove)
        h_btn.addWidget(btn_reset)

        btn_brochure = QPushButton("📥 دانلود بروشور عنصر")
        btn_brochure.setStyleSheet("background-color: #f9e2af; color: #1e1e2e; border:none; padding: 12px;")
        btn_brochure.clicked.connect(self.download_brochure)

        self.lbl_e_total = QLabel("📀 الکترون‌ها: 0")
        self.lbl_e_total.setStyleSheet("color: #f9e2af; font-size: 16px; font-weight:bold; border:none; padding: 5px;")
        self.lbl_e_total.setAlignment(Qt.AlignCenter)
        v_left.addLayout(h_btn)
        v_left.addWidget(btn_brochure)
        v_left.addWidget(self.lbl_e_total)

        right_panel = QScrollArea()
        right_panel.setWidgetResizable(True)
        right_panel.setStyleSheet("border: none; background-color: transparent;")
        right_content = QWidget()
        v_right = QVBoxLayout(right_content)

        self.gb_main = QGroupBox("🧪 اطلاعات عنصر")
        f_main = QFormLayout(self.gb_main)
        f_main.setLabelAlignment(Qt.AlignRight)

        self.lbl_name = QLabel("—")
        self.lbl_atomic_num = QLabel("0")
        self.lbl_protons = QLabel("0")
        self.lbl_neutrons = QLabel("0")
        self.lbl_group = QLabel("—")
        self.lbl_period = QLabel("—")
        self.lbl_category = QLabel("—")
        self.lbl_state = QLabel("—")
        self.lbl_valence = QLabel("0")

        lbl_style = "color: #cdd6f4; font-size: 15px; font-weight: bold;"
        for lbl in [self.lbl_name, self.lbl_atomic_num, self.lbl_protons, self.lbl_neutrons,
                    self.lbl_group, self.lbl_period, self.lbl_category, self.lbl_state, self.lbl_valence]:
            lbl.setStyleSheet(lbl_style)

        f_main.addRow("نام عنصر:", self.lbl_name)
        f_main.addRow("عدد اتمی (Z):", self.lbl_atomic_num)
        f_main.addRow("پروتون‌ها (p⁺):", self.lbl_protons)
        f_main.addRow("نوترون‌ها (n⁰):", self.lbl_neutrons)
        f_main.addRow("گروه:", self.lbl_group)
        f_main.addRow("دوره (تناوب):", self.lbl_period)
        f_main.addRow("دسته‌بندی:", self.lbl_category)
        f_main.addRow("حالت (۲۵°C):", self.lbl_state)
        f_main.addRow("الکترون ظرفیت:", self.lbl_valence)
        v_right.addWidget(self.gb_main)

        self.gb_orbital = QGroupBox("🔬 آرایش اوربیتالی")
        v_orb = QVBoxLayout(self.gb_orbital)
        self.lbl_orbital = QLabel("—")
        self.lbl_orbital.setStyleSheet(
            "color: #fab387; font-size: 16px; font-family: Consolas, monospace; letter-spacing: 1px;")
        self.lbl_orbital.setWordWrap(True)
        v_orb.addWidget(self.lbl_orbital)
        v_right.addWidget(self.gb_orbital)

        self.gb_compounds = QGroupBox("🔗 ترکیبات شناخته شده")
        v_comp = QVBoxLayout(self.gb_compounds)
        self.list_compounds = QListWidget()
        self.list_compounds.setStyleSheet(
            "background-color: #1e1e2e; border: 1px solid #45475a; border-radius: 6px; padding: 5px;")
        v_comp.addWidget(self.list_compounds)
        v_right.addWidget(self.gb_compounds)

        lbl_rule = QLabel("💡 قانون بور: گسترش یافته برای 118 عنصر بر اساس قانون مادلونگ.")
        lbl_rule.setStyleSheet(
            "color: #a6adc8; font-size: 12px; font-style: italic; background-color: #181825; padding: 10px; border-radius: 5px;")
        lbl_rule.setWordWrap(True)
        v_right.addWidget(lbl_rule)

        right_panel.setWidget(right_content)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([600, 400])
        layout.addWidget(splitter)

    def add_electron(self):
        if self.Z < 118:
            self.Z += 1
            self.update_info()

    def remove_electron(self):
        if self.Z > 0:
            self.Z -= 1
            self.update_info()

    def reset_electrons(self):
        self.Z = 0
        self.update_info()

    def toggle_bohr_dimension(self):
        if not HAS_OPENGL or self.canvas_3d is None:
            return
        self._use_3d_bohr = not self._use_3d_bohr
        if self._use_3d_bohr:
            self.canvas = self.canvas_3d
            self.canvas_stack.setCurrentWidget(self.canvas_3d)
            self.lbl_bohr_mode.setText("💡 حالت سه‌بعدی — با ماوس بچرخانید.")
            self.lbl_bohr_mode.setStyleSheet("color: #a6e3a1; font-size: 11px; border:none;")
        else:
            self.canvas = self.canvas_2d
            self.canvas_stack.setCurrentWidget(self.canvas_2d)
            self.lbl_bohr_mode.setText("📐 حالت دوبعدی")
            self.lbl_bohr_mode.setStyleSheet("color: #89b4fa; font-size: 11px; border:none;")
        self.update_info()

    def get_orbital_string(self, z):
        orbitalsOrder = [
            ("1s", 2), ("2s", 2), ("2p", 6), ("3s", 2), ("3p", 6),
            ("4s", 2), ("3d", 10), ("4p", 6), ("5s", 2), ("4d", 10), ("5p", 6),
            ("6s", 2), ("4f", 14), ("5d", 10), ("6p", 6),
            ("7s", 2), ("5f", 14), ("6d", 10), ("7p", 6)
        ]
        rem = z
        parts = []
        for orb, cap in orbitalsOrder:
            if rem <= 0:
                break
            fill = min(rem, cap)
            parts.append(f"{orb}{ChemicalCalculator.to_superscript(fill)}")
            rem -= fill
        return " ".join(parts) if parts else "—"

    def get_group_period_valence(self):
        shells = self.canvas.shells
        last_layer = -1
        for i in range(7):
            if shells[i] > 0:
                last_layer = i
        if last_layer == -1:
            return "—", "—", 0
        period = last_layer + 1
        valence = shells[last_layer]
        group = valence
        if valence == 0:
            group = "—"
        elif valence == 1:
            group = 1
        elif valence == 2:
            group = 2
        elif 3 <= valence <= 7:
            group = valence + 10
        elif valence >= 8:
            group = 18
        return str(group), str(period), valence

    def update_info(self):
        data = ATOMIC_DB.get(self.Z, ("—", "?", "—", "—", 0, []))
        self.canvas.update_atom(self.Z, data[1])
        # همگام‌سازی هر دو بوم در صورت وجود
        if hasattr(self, 'canvas_2d') and self.canvas_2d is not self.canvas:
            self.canvas_2d.update_atom(self.Z, data[1])
        if hasattr(self, 'canvas_3d') and self.canvas_3d and self.canvas_3d is not self.canvas:
            self.canvas_3d.update_atom(self.Z, data[1])

        self.lbl_e_total.setText(f"📀 مجموع الکترون‌ها: {self.Z}")
        self.lbl_name.setText(f"⚛️ {data[0]} ({data[1]})")
        self.lbl_atomic_num.setText(str(self.Z))
        self.lbl_protons.setText(str(self.Z))
        self.lbl_neutrons.setText(str(data[4]))

        self.lbl_category.setText(data[2])
        self.lbl_state.setText(data[3])

        grp, per, val = self.get_group_period_valence()
        self.lbl_group.setText(grp)
        self.lbl_period.setText(per)
        self.lbl_valence.setText(str(val))

        self.lbl_orbital.setText(self.get_orbital_string(self.Z))

        self.list_compounds.clear()
        if data[5]:
            for comp in data[5]:
                self.list_compounds.addItem(ChemicalCalculator.to_subscript(comp))
        else:
            self.list_compounds.addItem("—")

    def download_brochure(self):
        if self.Z <= 0:
            QMessageBox.warning(self, "بروشور", "ابتدا یک عنصر انتخاب کنید.")
            return
        data = ATOMIC_DB.get(self.Z, ("—", "?", "—", "—", 0, []))
        symbol = data[1]
        src = get_brochure_path(symbol)
        if not src:
            QMessageBox.information(
                self, "بروشور",
                f"برای عنصر {data[0]} ({symbol}) تصویری تعریف نشده است.\n\n"
                f"لطفاً تصویر را در پوشه «{BROCHURE_FOLDER}» با نام {symbol}.png قرار دهید.\n"
                f"مسیر: {get_brochure_dir()}"
            )
            return
        ext = os.path.splitext(src)[1]
        default_name = f"بروشور_{symbol}{ext}"
        dest, _ = QFileDialog.getSaveFileName(self, "ذخیره بروشور عنصر", default_name, f"Images (*{ext})")
        if dest:
            try:
                shutil.copy2(src, dest)
                QMessageBox.information(self, "موفق", f"بروشور {data[0]} ({symbol}) ذخیره شد.")
            except Exception as e:
                QMessageBox.critical(self, "خطا", f"خطا در کپی فایل:\n{e}")


# ----------------- کلاس‌های شبیه‌ساز آزمایشگاه -----------------
class LoginDialog(QDialog):
    def __init__(self, parent=None, current_name=""):
        super().__init__(parent)
        self.setWindowTitle("ورود / خروج حساب کاربری")
        self.setFixedSize(420, 280)
        self.setStyleSheet("""
            QDialog { background-color: #0f0f17; border: 2px solid #89b4fa; border-radius: 10px; }
            QLabel { color: #ffffff; font-size: 14px; font-weight: bold; }
            QLineEdit { padding: 8px; border-radius: 5px; border: 1px solid #45475a; background: #1e1e2e; color: #a6e3a1; font-size: 14px; }
            QPushButton#primary { background-color: #89b4fa; color: #11111b; padding: 10px; border-radius: 5px; font-weight: bold; font-size: 14px; }
            QPushButton#primary:hover { background-color: #b4befe; }
            QPushButton#logout { background-color: #45475a; color: #f38ba8; padding: 10px; border-radius: 5px; font-weight: bold; font-size: 13px; }
            QPushButton#logout:hover { background-color: #585b70; }
        """)
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(32, 32, 32, 32)
        title = QLabel("🧪 آزمایشگاه شیمی‌لَب V44 Pro")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #89dceb; margin-bottom: 6px;")
        layout.addWidget(title)
        lbl = QLabel("احراز هویت شیمیدان:")
        layout.addWidget(lbl)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("نام خود را وارد کنید...")
        if current_name and current_name != "دانشجو":
            self.name_input.setText(current_name)
        layout.addWidget(self.name_input)
        btn = QPushButton("✅ ورود به آزمایشگاه")
        btn.setObjectName("primary")
        btn.clicked.connect(self.check_input)
        layout.addWidget(btn)
        if current_name and current_name != "دانشجو":
            btn_out = QPushButton("🚪 خروج از حساب کاربری")
            btn_out.setObjectName("logout")
            btn_out.clicked.connect(self.do_logout)
            layout.addWidget(btn_out)
        self._logout_requested = False

    def do_logout(self):
        self._logout_requested = True
        self.name_input.clear()
        self.accept()

    def is_logout(self):
        return self._logout_requested

    def check_input(self):
        if self.name_input.text().strip():
            self._logout_requested = False
            self.accept()
        else:
            self.name_input.setPlaceholderText("⚠️ لطفاً نام معتبر وارد کنید!")
            self.name_input.setStyleSheet("border: 2px solid #f38ba8; background: #1e1e2e; color: #a6e3a1;")

    def get_name(self):
        return self.name_input.text().strip()


class LabEngine:
    def __init__(self):
        self.score = 0
        self.level = 1
        self.player_name = "دانشجو"
        self.discovered = set()
        self.badges = set()
        self.completed_missions = set()
        self.notes = ""
        self.visual_layers = []
        self.layer_id_counter = 0
        self.max_capacity = 1000.0
        self.speed_multiplier = 1.0
        self.is_broken = False
        self.titration_volume = 0.0

        self.flask_label = "بشر شماره ۱"
        self.auto_log = []
        self.stats = {
            "start_time_stamp": time.time(),
            "total_play_time": 0,
            "reactions_found": 0,
            "flask_breaks": 0,
            "filter_uses": 0,
            "successful_titrations": 0
        }

        self.missions = [
            {"id": "m1", "title": "اولین ترکیب", "desc": "دو ماده مختلف را مخلوط کنید.", "xp": 10},
            {"id": "m2", "title": "محیط بسیار اسیدی", "desc": "pH را به زیر 2 برسانید.", "xp": 20},
            {"id": "m3", "title": "محیط بسیار بازی", "desc": "pH را به بالای 12 برسانید.", "xp": 20},
            {"id": "m4", "title": "نقطه جوش", "desc": "دما را به بالای 100 درجه برسانید.", "xp": 30},
            {"id": "m5", "title": "خنثی سازی", "desc": "یک اسید و باز را خنثی کنید (pH بین 6.5 تا 7.5).", "xp": 50},
            {"id": "m6", "title": "انفجار کنترل شده", "desc": "دما را به حدی بالا ببرید که ظرف بشکند.", "xp": 10},
            {"id": "m7", "title": "استاد تیتراسیون", "desc": "بیش از ۵۰ میلی‌لیتر بورت انجام دهید.", "xp": 40},
        ]

        self.load_data()
        self.reset()
        self.add_to_log("آزمایشگاه راه‌اندازی شد.")

    def add_to_log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{ts}] {msg}"
        self.auto_log.append(log_entry)
        if len(self.auto_log) > 500:
            self.auto_log.pop(0)

    def reset(self):
        self.total_volume = 0.0
        self.moles_h = 0.0
        self.moles_oh = 0.0
        self.temp_c = 25.0
        self.contents = {}
        self.visual_layers = []
        self.is_broken = False
        self.titration_volume = 0.0
        self.last_update = time.time()
        self.add_to_log("ظرف آزمایش ریست شد.")

    def load_data(self):
        save_path = get_save_path()
        if os.path.exists(save_path):
            try:
                with open(save_path, "r", encoding="utf-8") as f:
                    d = json.load(f)
                    self.score = d.get("score", 0)
                    self.level = d.get("level", 1)
                    self.discovered = set(d.get("discovered", []))
                    self.player_name = d.get("player_name", "دانشجو")
                    self.notes = d.get("notes", "")
                    self.badges = set(d.get("badges", []))
                    self.completed_missions = set(d.get("completed_missions", []))
                    self.flask_label = d.get("flask_label", "بشر شماره ۱")
                    if "stats" in d:
                        self.stats.update(d["stats"])
            except:
                pass

    def save_data(self):
        save_path = get_save_path()
        try:
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump({
                    "score": self.score, "level": self.level,
                    "discovered": list(self.discovered), "player_name": self.player_name,
                    "notes": self.notes, "badges": list(self.badges),
                    "completed_missions": list(self.completed_missions),
                    "flask_label": self.flask_label,
                    "stats": self.stats
                }, f, ensure_ascii=False)
        except:
            pass

    def set_player_name(self, name):
        self.player_name = name
        self.save_data()

    def to_dict(self):
        return {
            "score": self.score, "level": self.level, "player_name": self.player_name,
            "discovered": list(self.discovered), "badges": list(self.badges),
            "completed_missions": list(self.completed_missions), "notes": self.notes,
            "total_volume": self.total_volume, "moles_h": self.moles_h, "moles_oh": self.moles_oh,
            "temp_c": self.temp_c, "contents": self.contents, "visual_layers": self.visual_layers,
            "is_broken": self.is_broken, "titration_volume": self.titration_volume,
            "flask_label": self.flask_label, "stats": self.stats
        }

    def from_dict(self, d):
        self.score = d.get("score", 0)
        self.level = d.get("level", 1)
        self.player_name = d.get("player_name", "دانشجو")
        self.discovered = set(d.get("discovered", []))
        self.badges = set(d.get("badges", []))
        self.completed_missions = set(d.get("completed_missions", []))
        self.notes = d.get("notes", "")
        self.total_volume = d.get("total_volume", 0.0)
        self.moles_h = d.get("moles_h", 0.0)
        self.moles_oh = d.get("moles_oh", 0.0)
        self.temp_c = d.get("temp_c", 25.0)
        self.contents = d.get("contents", {})
        self.visual_layers = d.get("visual_layers", [])
        self.is_broken = d.get("is_broken", False)
        self.titration_volume = d.get("titration_volume", 0.0)
        self.flask_label = d.get("flask_label", "بشر شماره ۱")
        if "stats" in d:
            self.stats.update(d["stats"])
        if self.visual_layers:
            self.layer_id_counter = max([l.get('id', 0) for l in self.visual_layers]) + 1
        self.save_data()
        self.add_to_log("وضعیت آزمایش از فایل بارگذاری شد.")

    def filter_solids(self):
        if self.is_broken:
            return []
        removed = []
        new_layers = []
        removed_moles = Counter()
        for layer in self.visual_layers:
            db_type = CHEMILAB_DB.get(layer['key'], {}).get('type', '')
            layer_type = layer.get('type', '')
            combined_type = f"{db_type} {layer_type}"
            is_solid = is_solid_chemical_type(combined_type)
            if is_solid or any(k in str(layer_type) for k in ["جامد", "فلز", "رسوب", "پودر", "آلیاژ", "نمک"]):
                removed.append(layer['name'])
                self.total_volume -= layer['amount']
                removed_moles[layer['key']] += layer.get('moles', 0.0)
            else:
                new_layers.append(layer)
        for key, moles in removed_moles.items():
            if key in self.contents:
                self.contents[key] -= moles
                if self.contents[key] <= 1e-12:
                    del self.contents[key]
        self.visual_layers = new_layers
        if self.total_volume < 0:
            self.total_volume = 0
        if removed:
            self.stats["filter_uses"] += 1
            self.add_to_log(f"مواد جامد فیلتر شدند: {','.join(removed)}")
        return removed

    def spill_cleanup(self):
        if self.total_volume > self.max_capacity:
            amount_to_remove = self.total_volume - self.max_capacity
            ratio = self.max_capacity / self.total_volume
            self.total_volume = self.max_capacity
            for l in self.visual_layers:
                l['amount'] *= ratio
                l['moles'] *= ratio
            for k in self.contents:
                self.contents[k] *= ratio
            self.moles_h *= ratio
            self.moles_oh *= ratio
            self.add_to_log(f"میز تمیز شد و {amount_to_remove:.1f} واحد ماده هدر رفت.")
            return True
        return False

    def add_chemical(self, key, amount, custom_molarity=None):
        warnings = []
        if self.is_broken:
            return "❌ ظرف شکسته است! ابتدا آن را بشویید.", False, warnings
        key = key.lower()
        if key not in CHEMILAB_DB:
            return "خطا: ماده یافت نشد", False, warnings

        data = CHEMILAB_DB[key]
        chem_type = data.get('type', '')

        # هشدارهای ایمنی
        if key == "h2o" and any("Acid" in CHEMILAB_DB.get(k, {}).get('type', '') for k in self.contents):
            warnings.append(
                "⚠️ خطر ایمنی: افزودن آب به اسید می‌تواند باعث پاشش خطرناک شود! (همیشه اسید به آب افزوده شود)")
        if "Strong Acid" in chem_type and any(
                "Strong Base" in CHEMILAB_DB.get(k, {}).get('type', '') for k in self.contents):
            warnings.append("⚠️ احتیاط: واکنش اسید قوی و باز قوی به شدت گرمازاست.")
        elif "Strong Base" in chem_type and any(
                "Strong Acid" in CHEMILAB_DB.get(k, {}).get('type', '') for k in self.contents):
            warnings.append("⚠️ احتیاط: واکنش اسید قوی و باز قوی به شدت گرمازاست.")

        ph_val = float(data.get("pH", 7.0))
        molarity = float(data.get("molarity", 0.1))
        if custom_molarity is not None:
            molarity = custom_molarity

        if any(x in chem_type for x in ["Solid", "Metal", "Salt", "Powder", "Precipitate"]):
            added_moles = (amount / 100.0) * molarity
            unit_display = "g"
        else:
            added_moles = molarity * (amount / 1000.0)
            unit_display = "mL"

        old_vol = self.total_volume
        self.total_volume += amount

        if self.total_volume > 0:
            self.temp_c = ((old_vol * self.temp_c) + (amount * 25.0)) / self.total_volume
            q_joules = added_moles * (-float(data.get("heat", 0.0))) * 1000
            mass_approx = self.total_volume
            if mass_approx > 0:
                dt_temp = q_joules / (mass_approx * 4.18)
                self.temp_c += dt_temp

        self.contents[key] = self.contents.get(key, 0) + added_moles
        self.layer_id_counter += 1
        self.visual_layers.append({
            'id': self.layer_id_counter, 'key': key, 'name': data['name'],
            'amount': amount, 'color': data['color'], 'type': get_persian_type(chem_type),
            'moles': added_moles,
            'formula': data.get('formula', '')
        })

        if ph_val < 7:
            self.moles_h += added_moles * (1 if ph_val < 2 else 0.1)
        elif ph_val > 7:
            self.moles_oh += added_moles * (1 if ph_val > 12 else 0.1)

        result_msg = f"افزوده شد: {data['name']} ({amount:.1f} {unit_display})"
        is_overflow = False

        if self.total_volume > self.max_capacity:
            is_overflow = True
            result_msg += " ⚠️ ظرف سرریز شد!"

        self.add_to_log(result_msg)
        return result_msg, is_overflow, warnings

    def remove_layer(self, layer_id):
        for i, layer in enumerate(self.visual_layers):
            if layer['id'] == layer_id:
                key = layer['key']
                moles = layer['moles']
                amount = layer['amount']
                if key in self.contents:
                    self.contents[key] -= moles
                    if self.contents[key] <= 0:
                        del self.contents[key]
                self.total_volume -= amount
                self.visual_layers.pop(i)
                self.add_to_log(f"ماده حذف شد: {layer['name']}")
                return True
        return False

    def change_temperature(self, delta):
        try:
            self.temp_c = float(self.temp_c) + float(delta)
            # محدوده منطقی دما برای جلوگیری از مقادیر غیرواقعی
            self.temp_c = max(-273.15, min(2000.0, self.temp_c))
            self.add_to_log(f"تغییر دما توسط کاربر (دلتا: {delta})")
        except Exception:
            self.temp_c = 25.0

    def update_physics(self):
        current_time = time.time()
        dt_real = current_time - self.last_update
        self.last_update = current_time
        dt = dt_real * self.speed_multiplier

        self.stats["total_play_time"] += dt_real

        if self.speed_multiplier == 0:
            return

        if self.is_broken:
            diff = self.temp_c - 25.0
            self.temp_c -= diff * 0.1 * dt
            return

        room_temp = 25.0
        cooling_rate = 0.05
        diff = self.temp_c - room_temp
        if abs(diff) > 0.1:
            self.temp_c -= diff * cooling_rate * dt

        if self.temp_c >= 100.0 and self.total_volume > 0:
            evap_rate = (self.temp_c - 100.0) * 0.5 * dt
            if evap_rate > 0:
                liquid_layers = [l for l in self.visual_layers if
                                 any(x in l['type'] for x in ["مایع", "آب", "محلول", "اسید", "باز"])]
                if liquid_layers:
                    evap_per_layer = evap_rate / len(liquid_layers)
                    for l in liquid_layers:
                        remove_amt = min(l['amount'], evap_per_layer)
                        l['amount'] -= remove_amt
                        self.total_volume -= remove_amt
                        if remove_amt > 0 and (l['amount'] + remove_amt) > 0:
                            ratio = l['amount'] / (l['amount'] + remove_amt)
                            l['moles'] *= ratio
                            if l['key'] in self.contents:
                                self.contents[l['key']] *= ratio
                    self.visual_layers = [l for l in self.visual_layers if l['amount'] > 0.1]

        if self.temp_c > FLASK_BREAK_TEMP and not self.is_broken:
            self.is_broken = True
            self.stats["flask_breaks"] += 1
            self.add_to_log("💥 ظرف به دلیل دمای بسیار بالا منفجر شد!")
            self.total_volume = 0
            self.visual_layers = []
            self.contents = {}
            self.moles_h = 0
            self.moles_oh = 0

    def check_reactions(self):
        if self.is_broken:
            return None
        present = set()
        for k, v in self.contents.items():
            if v > 1e-12:
                present.add(normalize_key(k))
                if k in CHEMILAB_DB:
                    present.add(normalize_key(CHEMILAB_DB[k].get("formula", "")))
                    present.add(normalize_key(CHEMILAB_DB[k].get("name", "")))

        found_old = None
        for name, rxn in CUSTOM_REACTIONS.items():
            needed = {normalize_key(r) for r in rxn["reactants"]}
            if len(needed) > 0 and needed.issubset(present):
                req_temp = rxn.get("temp_min", -273)
                if self.temp_c >= req_temp:
                    has_precipitate = any(
                        "Precipitate" in CHEMILAB_DB.get(p, {}).get('type', '') for p in rxn["products"])
                    has_gas = any("Gas" in CHEMILAB_DB.get(p, {}).get('type', '') for p in rxn["products"])

                    if name not in self.discovered:
                        self.discovered.add(name)
                        self.stats["reactions_found"] += 1
                        self.score += rxn["xp"]
                        if self.score >= self.level * 100:
                            self.level += 1
                        self.save_data()
                        self.temp_c += 15.0
                        self.add_to_log(f"واکنش جدید کشف شد: {name}")
                        return (name, rxn["xp"], "new", has_precipitate, has_gas)
                    else:
                        found_old = (name, 0, "old", has_precipitate, has_gas)
        return found_old

    def check_missions_and_badges(self):
        new_missions = []
        if len(self.contents) >= 2 and "m1" not in self.completed_missions:
            new_missions.append("m1")
        if self.get_ph() < 2 and "m2" not in self.completed_missions:
            new_missions.append("m2")
        if self.get_ph() > 12 and "m3" not in self.completed_missions:
            new_missions.append("m3")
        if self.temp_c > 100 and "m4" not in self.completed_missions:
            new_missions.append("m4")
        if 6.5 <= self.get_ph() <= 7.5 and self.total_volume > 100 and self.moles_h > 0.01 and "m5" not in self.completed_missions:
            new_missions.append("m5")
        if self.is_broken and "m6" not in self.completed_missions:
            new_missions.append("m6")
        if self.titration_volume >= 50 and "m7" not in self.completed_missions:
            new_missions.append("m7")

        for m_id in new_missions:
            self.completed_missions.add(m_id)
            mission = next((m for m in self.missions if m['id'] == m_id), None)
            if mission:
                self.score += mission['xp']
                if self.score >= self.level * 100:
                    self.level += 1
                self.save_data()
                self.add_to_log(f"ماموریت تکمیل شد: {mission['title']}")
                return mission

        # چک مدال ها
        if self.temp_c >= 200 and "داغی ۲۰۰ درجه" not in self.badges:
            self.badges.add("داغی ۲۰۰ درجه")
            self.save_data()
            self.add_to_log("مدال جدید: داغی ۲۰۰ درجه")
            return {"type": "badge", "title": "داغی ۲۰۰ درجه"}
        if len(self.discovered) >= 1 and "اولین واکنش" not in self.badges:
            self.badges.add("اولین واکنش")
            self.save_data()
            self.add_to_log("مدال جدید: اولین واکنش")
            return {"type": "badge", "title": "اولین واکنش"}

        return None

    def get_ph(self):
        if self.total_volume == 0 or self.is_broken:
            return 7.0
        vol_l = self.total_volume / 1000.0 if self.total_volume > 0 else 1
        h = self.moles_h / vol_l
        oh = self.moles_oh / vol_l
        if abs(h - oh) < 1e-9:
            return 7.0
        try:
            if h > oh:
                val = h - oh
                if val <= 0:
                    return 7.0
                ph = -math.log10(val + 1e-14)
            else:
                val = oh - h
                if val <= 0:
                    return 7.0
                ph = 14 + math.log10(val + 1e-14)
            return max(0.0, min(14.0, ph))
        except ValueError:
            return 7.0

    def get_mixture_empirical_formula(self):
        if self.is_broken:
            return "-"
        total_atoms = Counter()
        for key, moles in self.contents.items():
            if moles <= 1e-9:
                continue
            if key in CHEMILAB_DB:
                form = CHEMILAB_DB[key]["formula"]
                atoms_in_molecule = ChemicalCalculator.parse_formula(form)
                for atom, count in atoms_in_molecule.items():
                    total_atoms[atom] += count * moles
        filtered = {k: v for k, v in total_atoms.items() if v > 1e-6}
        if not filtered:
            return "-"
        return ChemicalCalculator.calculate_empirical_from_moles(filtered)


class AnimatedContainer(QWidget):
    def __init__(self, engine, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.setMinimumSize(450, 600)
        self.setMouseTracking(True)
        self._flash_opacity = 0.0

        self.anim_flash = QPropertyAnimation(self, b"flashOpacity")
        self.anim_flash.setDuration(600)
        self.anim_flash.setEasingCurve(QEasingCurve.OutQuad)

        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.process_animations)
        self.animation_timer.start(30)

        self.bubbles, self.particles, self.steam_particles, self.overflow_particles, self.shards = [], [], [], [], []
        self.plate_state = "off"
        self.plate_glow_alpha = 0
        self.plate_glow_dir = 5
        self.stirrer_on = False
        self.stirrer_angle = 0.0
        self.is_exploding = False
        self.frost_seed = random.randint(0, 99999)
        self.show_layer_labels = True

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    def show_context_menu(self, pos):
        menu = QMenu(self)
        menu.setStyleSheet("background-color: #1e1e2e; color: #cdd6f4; border: 1px solid #45475a;")
        rename_action = menu.addAction("🏷️ تغییر برچسب ظرف")
        spill_action = menu.addAction("🧽 تمیز کردن سرریز (در صورت وجود)")

        action = menu.exec_(self.mapToGlobal(pos))
        if action == rename_action:
            text, ok = QInputDialog.getText(self, "برچسب ظرف", "نام جدید برچسب را وارد کنید:",
                                            text=self.engine.flask_label)
            if ok and text:
                self.engine.flask_label = text
                self.engine.save_data()
                self.update()
        elif action == spill_action:
            if self.engine.spill_cleanup():
                self.overflow_particles.clear()
                self.update()

    def set_plate_state(self, state):
        self.plate_state = state
        if state != "off":
            QTimer.singleShot(4000, lambda: self.set_plate_state("off"))

    def set_stirrer(self, state):
        self.stirrer_on = state
        if not state:
            self.stirrer_angle = 0.0

    def trigger_explosion(self):
        self.is_exploding = True
        self.shards = []
        w, h = self.width(), self.height()
        cx, cy = w / 2, h - 100
        for _ in range(50):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(8, 20)
            self.shards.append({
                'x': cx, 'y': cy, 'vx': math.cos(angle) * speed, 'vy': math.sin(angle) * speed,
                'rot': random.uniform(0, 360), 'vrot': random.uniform(-30, 30), 'size': random.uniform(5, 25)
            })

    def process_animations(self):
        if self.engine.is_broken and not self.is_exploding:
            self.trigger_explosion()
        if not self.engine.is_broken:
            self.is_exploding = False

        dt_mult = max(0, self.engine.speed_multiplier)

        if self.plate_state != "off" and dt_mult > 0:
            self.plate_glow_alpha += self.plate_glow_dir * dt_mult
            if self.plate_glow_alpha >= 200:
                self.plate_glow_alpha, self.plate_glow_dir = 200, -8
            elif self.plate_glow_alpha <= 60:
                self.plate_glow_alpha, self.plate_glow_dir = 60, 8
        else:
            self.plate_glow_alpha = max(0, self.plate_glow_alpha - 10)

        if self.stirrer_on and dt_mult > 0:
            self.stirrer_angle += 15.0 * dt_mult
            if self.stirrer_angle >= 360:
                self.stirrer_angle -= 360

        total_amount = self.engine.total_volume
        h = self.height()
        margin_x, margin_y = 100, 30
        container_h = h - 2 * margin_y - 30

        if dt_mult > 0:
            for p in self.particles[:]:
                p['x'] += p['vx'] * dt_mult
                p['y'] -= p['vy'] * dt_mult
                p['life'] -= 1 * dt_mult
                if p['life'] <= 0:
                    self.particles.remove(p)

            for sp in self.steam_particles[:]:
                sp['y'] -= sp['vy'] * dt_mult
                sp['x'] += math.sin(sp['life'] * 0.1) * 2
                sp['life'] -= 1 * dt_mult
                if sp['life'] <= 0:
                    self.steam_particles.remove(sp)

            for op in self.overflow_particles[:]:
                op['y'] += op['vy'] * dt_mult
                op['life'] -= 1 * dt_mult
                if op['life'] <= 0:
                    self.overflow_particles.remove(op)

            for sh in self.shards[:]:
                sh['x'] += sh['vx'] * dt_mult
                sh['y'] += sh['vy'] * dt_mult
                sh['vy'] += 0.8 * dt_mult
                sh['rot'] += sh['vrot'] * dt_mult

            if self.engine.temp_c >= 100.0 and total_amount > 0 and not self.engine.is_broken:
                if random.random() < 0.4 * dt_mult:
                    self.steam_particles.append({
                        'x': random.uniform(margin_x, self.width() - margin_x),
                        'y': h - margin_y - 30 - (total_amount * (container_h / self.engine.max_capacity)),
                        'vy': random.uniform(1.0, 4.0), 'life': 100, 'size': random.uniform(10, 30)
                    })

            if total_amount > 0 and not self.engine.is_broken:
                is_heating = self.plate_state == "heat" or self.engine.temp_c > 80
                spawn_chance = (0.6 if is_heating else (0.3 if self.stirrer_on else 0.05)) * dt_mult
                if random.random() < spawn_chance:
                    self.bubbles.append({
                        'x': random.uniform(margin_x + 10, self.width() - margin_x - 10),
                        'y': h - margin_y - 30,
                        'speed': random.uniform(1.0, 4.0) if is_heating else random.uniform(0.5, 1.5),
                        'size': random.uniform(3, 8)
                    })

                liquid_top = h - margin_y - 30 - (total_amount * (container_h / self.engine.max_capacity))
                for b in self.bubbles:
                    b['y'] -= b['speed'] * dt_mult
                    if self.stirrer_on:
                        b['x'] += math.sin(self.stirrer_angle * math.pi / 180.0) * 3
                    else:
                        b['x'] += random.uniform(-0.5, 0.5)
                self.bubbles = [b for b in self.bubbles if b['y'] > liquid_top]
            else:
                self.bubbles.clear()

        self.update()

    @pyqtProperty(float)
    def flashOpacity(self):
        return self._flash_opacity

    @flashOpacity.setter
    def flashOpacity(self, value):
        self._flash_opacity = value
        self.update()

    def trigger_reaction_animation(self, has_pr, has_gas):
        self.anim_flash.setStartValue(1.0)
        self.anim_flash.setEndValue(0.0)
        self.anim_flash.start()
        h, margin_x, margin_y = self.height(), 100, 30
        base_y = h - margin_y - 30
        total_amount = self.engine.total_volume
        if total_amount > 0:
            scale = (h - 2 * margin_y - 30) / self.engine.max_capacity
            base_y -= (total_amount * scale)

        for _ in range(50):
            self.particles.append({
                'x': random.uniform(margin_x + 20, self.width() - margin_x - 20),
                'y': base_y, 'vx': random.uniform(-4.0, 4.0), 'vy': random.uniform(3.0, 8.0),
                'life': random.randint(20, 70),
                'color': random.choice([QColor(255, 200, 50), QColor(0, 255, 255), QColor(255, 100, 255)])
            })

    def trigger_overflow(self):
        w, margin_x, margin_y = self.width(), 100, 30
        for _ in range(15):
            self.overflow_particles.append(
                {'x': margin_x - random.uniform(0, 15), 'y': margin_y + random.uniform(0, 15),
                 'vy': random.uniform(3, 6), 'life': 80, 'size': random.uniform(4, 8)})
            self.overflow_particles.append(
                {'x': w - margin_x + random.uniform(0, 15), 'y': margin_y + random.uniform(0, 15),
                 'vy': random.uniform(3, 6), 'life': 80, 'size': random.uniform(4, 8)})

    def mouseMoveEvent(self, event):
        if self.engine.is_broken:
            QToolTip.hideText()
            return
        y_pos = event.y()
        w, h, margin_x, margin_y = self.width(), self.height(), 100, 30
        scale = (h - 2 * margin_y - 30) / self.engine.max_capacity
        current_y = h - margin_y - 30
        hovered_layer = None

        def layer_density(layer):
            t = layer['type']
            if any(x in t for x in ["جامد", "فلز", "رسوب", "پودر", "آلیاژ"]):
                return 10
            if "گاز" in t:
                return 0.1
            return 1.0

        for layer in sorted(self.engine.visual_layers, key=layer_density, reverse=True):
            top_y = current_y - (layer['amount'] * scale)
            if top_y <= y_pos <= current_y and margin_x <= event.x() <= w - margin_x:
                hovered_layer = layer
                break
            current_y = top_y

        if hovered_layer:
            f = hovered_layer.get('formula', '')
            if f:
                f_display = ChemicalCalculator.to_subscript(f)
            else:
                f_display = "?"
            QToolTip.showText(event.globalPos(),
                              f"{hovered_layer['name']}\nفرمول: {f_display}\nمقدار: {hovered_layer['amount']:.1f} mL/g\n{hovered_layer['type']}",
                              self)
        else:
            QToolTip.hideText()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h, margin_x, margin_y, plate_height = self.width(), self.height(), 100, 30, 25
        container_rect = QRectF(margin_x, margin_y, w - 2 * margin_x, h - 2 * margin_y - plate_height)
        scale = container_rect.height() / self.engine.max_capacity

        self.draw_thermometer(painter, container_rect)
        self.draw_ph_strip(painter, container_rect)

        if not self.engine.is_broken:
            painter.setPen(QPen(QColor(255, 255, 255, 20), 1))
            painter.setBrush(QColor(255, 255, 255, 5))
            painter.drawRect(container_rect)

            total_amount = self.engine.total_volume
            current_y = container_rect.bottom()

            def layer_density(layer):
                t = layer['type']
                return 10 if any(x in t for x in ["جامد", "فلز", "رسوب", "پودر", "آلیاژ"]) else (
                    0.1 if "گاز" in t else 1.0)

            if total_amount > 0:
                for layer in sorted(self.engine.visual_layers, key=layer_density, reverse=True):
                    layer_h = layer['amount'] * scale
                    if layer_h <= 0:
                        continue
                    if current_y - layer_h < container_rect.top():
                        layer_h = current_y - container_rect.top()
                    rect = QRectF(container_rect.left(), current_y - layer_h, container_rect.width(), layer_h)
                    painter.setPen(Qt.NoPen)
                    c = QColor(layer['color'])
                    grad = QLinearGradient(rect.topLeft(), rect.topRight())
                    grad.setColorAt(0, c.darker(150))
                    grad.setColorAt(0.5, c)
                    grad.setColorAt(1, c.darker(150))
                    painter.setBrush(grad)
                    painter.drawRect(rect)

                    if self.show_layer_labels and layer_h > 15:
                        painter.save()
                        painter.setPen(QPen(QColor(255, 255, 255, 200), 1))
                        font = painter.font()
                        font.setPointSize(9)
                        font.setBold(True)
                        painter.setFont(font)
                        label_text = f"{layer['name']}"
                        f = layer.get('formula', '')
                        if f:
                            label_text += f" ({ChemicalCalculator.to_subscript(f)})"
                        label_text += f" {layer['amount']:.1f}"
                        painter.drawText(rect.adjusted(5, 2, -5, -2), Qt.AlignLeft | Qt.AlignVCenter, label_text)
                        painter.restore()

                    current_y -= layer_h

            painter.setPen(Qt.NoPen)
            for b in self.bubbles:
                painter.setBrush(QColor(255, 255, 255, 120))
                painter.drawEllipse(QRectF(b['x'], b['y'], b['size'], b['size']))

            if total_amount > 0 and self.engine.visual_layers:
                painter.save()
                painter.translate(container_rect.center().x(), container_rect.bottom() - 5)
                if self.stirrer_on:
                    painter.rotate(self.stirrer_angle)
                painter.setBrush(QColor(220, 220, 220))
                painter.setPen(QPen(QColor(100, 100, 100), 1))
                painter.drawRoundedRect(QRectF(-15, -4, 30, 8), 4, 4)
                painter.restore()

            painter.setPen(QPen(QColor(200, 220, 255, 180), 3))
            painter.setBrush(Qt.NoBrush)
            path = QPainterPath()
            path.moveTo(container_rect.topLeft())
            path.lineTo(container_rect.bottomLeft())
            path.lineTo(container_rect.bottomRight())
            path.lineTo(container_rect.topRight())
            painter.drawPath(path)

            painter.save()
            font = painter.font()
            font.setPointSize(12)
            font.setBold(True)
            painter.setFont(font)
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(container_rect.adjusted(0, 10, 0, 0), Qt.AlignTop | Qt.AlignHCenter,
                             self.engine.flask_label)
            painter.restore()

            # افکت یخ زدگی بهبود یافته
            if self.engine.temp_c < 0:
                try:
                    frost_intensity = min(1.0, abs(float(self.engine.temp_c)) / 20.0)
                    frost_alpha = max(0, min(255, int(80 + 120 * frost_intensity)))
                    painter.setPen(QPen(QColor(180, 220, 255, frost_alpha), 1))
                    # استفاده از seed ثابت بر اساس دما برای جلوگیری از لرزش و خطا
                    rng = random.Random(int(abs(self.engine.temp_c) * 10) + self.frost_seed)
                    n_crystals = max(1, int(20 + 40 * frost_intensity))
                    for i in range(n_crystals):
                        cw = max(20.0, container_rect.width() - 20)
                        ch = max(20.0, container_rect.height() - 20)
                        x = container_rect.left() + 10 + rng.uniform(0, cw)
                        y = container_rect.top() + 10 + rng.uniform(0, ch)
                        size = rng.uniform(3, 8 + 10 * frost_intensity)
                        painter.save()
                        painter.translate(x, y)
                        for j in range(6):
                            angle = j * 60 + rng.uniform(-5, 5)
                            painter.drawLine(0, 0,
                                             size * math.cos(math.radians(angle)),
                                             size * math.sin(math.radians(angle)))
                        painter.restore()
                    painter.setPen(QPen(QColor(200, 240, 255, max(0, min(255, int(60 + 100 * frost_intensity)))), 3))
                    painter.drawArc(container_rect, 0, 180 * 16)
                except Exception:
                    pass

            painter.setPen(QPen(QColor(255, 255, 255, 150), 1))
            font = painter.font()
            font.setPointSize(9)
            painter.setFont(font)
            for val in range(0, int(self.engine.max_capacity) + 1, 100):
                if val == 0:
                    continue
                y_coord = container_rect.bottom() - ((val / self.engine.max_capacity) * container_rect.height())
                painter.drawLine(int(container_rect.left()), int(y_coord), int(container_rect.left() + 15),
                                 int(y_coord))
                painter.drawText(int(container_rect.left()) - 45, int(y_coord) + 5, f"{val}")
            painter.drawText(int(container_rect.left()) - 45, int(container_rect.top()) - 5, "mL/g")

        else:
            painter.setPen(QPen(QColor(200, 220, 255, 150), 3))
            painter.drawLine(container_rect.bottomLeft(), container_rect.bottomRight())
            for sh in self.shards:
                painter.save()
                painter.translate(sh['x'], sh['y'])
                painter.rotate(sh['rot'])
                painter.setBrush(QColor(200, 230, 255, 180))
                painter.setPen(Qt.NoPen)
                painter.drawPolygon(QPointF(-sh['size'] / 2, -sh['size'] / 2), QPointF(sh['size'] / 2, 0),
                                    QPointF(0, sh['size'] / 2))
                painter.restore()

        plate_rect = QRectF(container_rect.left() - 20, container_rect.bottom() + 2, container_rect.width() + 40,
                            plate_height)
        plate_grad = QLinearGradient(plate_rect.topLeft(), plate_rect.bottomLeft())
        plate_grad.setColorAt(0, QColor(40, 42, 54))
        plate_grad.setColorAt(1, QColor(20, 22, 30))
        painter.setPen(Qt.NoPen)
        painter.setBrush(plate_grad)
        painter.setPen(QPen(QColor(100, 100, 120), 1))
        painter.drawRoundedRect(plate_rect, 5, 5)

        if self.plate_glow_alpha > 0 and self.engine.speed_multiplier > 0:
            glow_color = QColor(255, 50, 50, int(self.plate_glow_alpha)) if self.plate_state == "heat" else QColor(50,
                                                                                                                   150,
                                                                                                                   255,
                                                                                                                   int(self.plate_glow_alpha))
            painter.setBrush(glow_color)
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(plate_rect.adjusted(2, 0, -2, -20), 3, 3)

        for p in self.particles:
            c = QColor(p['color'])
            c.setAlpha(max(0, min(255, int(255 * (p['life'] / 70.0)))))
            painter.setBrush(c)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(p['x'], p['y']), 3, 3)

        for sp in self.steam_particles:
            painter.setBrush(QColor(220, 220, 220, max(0, min(255, int(120 * (sp['life'] / 100.0))))))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(sp['x'], sp['y']), sp['size'], sp['size'])

        for op in self.overflow_particles:
            painter.setBrush(QColor(100, 150, 255, 200))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(op['x'], op['y']), op['size'], op['size'])

        if self._flash_opacity > 0.01:
            painter.setBrush(QColor(255, 255, 200, int(self._flash_opacity * 200)))
            painter.setPen(Qt.NoPen)
            painter.drawRect(self.rect())

    def draw_thermometer(self, painter, rect):
        tx, ty, th, tw = rect.right() + 30, rect.top(), rect.height(), 12
        painter.setPen(QPen(QColor(100, 100, 100), 2))
        painter.setBrush(QColor(30, 30, 40))
        painter.drawRoundedRect(QRectF(tx, ty, tw, th), 6, 6)
        painter.drawEllipse(QRectF(tx - 4, ty + th - 5, 20, 20))

        min_t, max_t = -50, 600
        temp = max(min_t, min(self.engine.temp_c, max_t))
        fill_h = th * ((temp - min_t) / (max_t - min_t))
        fill_color = QColor(255, 50, 50) if temp > 50 else (QColor(50, 150, 255) if temp < 0 else QColor(255, 100, 50))

        painter.setPen(Qt.NoPen)
        painter.setBrush(fill_color)
        painter.drawRoundedRect(QRectF(tx + 2, ty + th - fill_h, tw - 4, fill_h), 4, 4)
        painter.drawEllipse(QRectF(tx - 2, ty + th - 3, 16, 16))

        # خط چین دمای شکستن
        break_y = ty + th - (th * ((FLASK_BREAK_TEMP - min_t) / (max_t - min_t)))
        painter.setPen(QPen(QColor(255, 0, 0, 180), 1, Qt.DashLine))
        painter.drawLine(int(tx - 8), int(break_y), int(tx + tw + 8), int(break_y))
        painter.setPen(QPen(QColor(255, 0, 0, 200), 1))
        painter.drawText(int(tx + tw + 10), int(break_y) + 4, "شکست")

        # درجه‌بندی با اعداد
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        for i in range(0, max_t + 1, 50):
            y = ty + th - (th * ((i - min_t) / (max_t - min_t)))
            painter.drawLine(int(tx + tw), int(y), int(tx + tw + 5), int(y))
            if i % 100 == 0:
                painter.drawText(int(tx + tw + 8), int(y) + 3, f"{i}")

        painter.setPen(QColor(200, 200, 220))
        painter.drawText(int(tx - 5), int(ty - 10), "°C")

        # نمایش دمای فعلی به صورت عدد
        painter.setPen(QPen(QColor(255, 255, 255, 220), 1))
        font = painter.font()
        font.setPointSize(10)
        font.setBold(True)
        painter.setFont(font)
        temp_str = f"{self.engine.temp_c:.0f}°C"
        painter.drawText(int(tx - 8), int(ty + th + 20), temp_str)

        # هشدار نزدیک به شکستن
        if self.engine.temp_c > FLASK_BREAK_TEMP - 50 and not self.engine.is_broken:
            painter.setPen(QPen(QColor(255, 100, 0, 200), 2))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(QRectF(tx - 12, ty - 5, tw + 24, th + 10), 4, 4)
            painter.setPen(QPen(QColor(255, 200, 0, 220), 1))
            painter.drawText(int(tx - 10), int(ty - 12), "⚠️ خطر شکستن!")

    def draw_ph_strip(self, painter, rect):
        px, py, ph, pw = rect.left() - 40, rect.top(), rect.height(), 10
        grad = QLinearGradient(0, py, 0, py + ph)
        grad.setColorAt(0, QColor(128, 0, 128))
        grad.setColorAt(0.5, QColor(0, 255, 0))
        grad.setColorAt(1, QColor(255, 0, 0))
        painter.setPen(QPen(QColor(100, 100, 100), 1))
        painter.setBrush(grad)
        painter.drawRect(QRectF(px, py, pw, ph))

        arrow_y = py + ph - (ph * (self.engine.get_ph() / 14.0))
        painter.setBrush(QColor(255, 255, 255))
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        poly = QPainterPath()
        poly.moveTo(px - 2, arrow_y)
        poly.lineTo(px - 10, arrow_y - 5)
        poly.lineTo(px - 10, arrow_y + 5)
        poly.closeSubpath()
        painter.drawPath(poly)
        painter.setPen(QColor(200, 200, 220))
        painter.drawText(int(px - 15), int(py - 10), "pH")


class BadgeWidget(QWidget):
    """ویجت نمایش مدال با hover tooltip"""
    def __init__(self, badge_name, parent=None):
        super().__init__(parent)
        self.badge_name = badge_name
        icon, desc = BADGE_CATALOG.get(badge_name, ("🏅", "بدون توضیح"))
        self.icon = icon
        self.desc = desc
        self.setFixedSize(80, 80)
        self.setToolTip(f"{icon} {badge_name}\n{desc}")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect().adjusted(2, 2, -2, -2)

        grad = QRadialGradient(rect.center(), rect.width() / 2)
        grad.setColorAt(0, QColor(255, 215, 0, 100))
        grad.setColorAt(1, QColor(200, 160, 0, 50))
        painter.setBrush(grad)
        painter.setPen(QPen(QColor(255, 215, 0, 150), 2))
        painter.drawEllipse(rect)

        font = painter.font()
        font.setPointSize(28)
        painter.setFont(font)
        painter.setPen(QColor(255, 215, 0))
        painter.drawText(rect, Qt.AlignCenter, self.icon)

        font.setPointSize(8)
        painter.setFont(font)
        painter.setPen(QColor(200, 200, 220))
        short_name = self.badge_name[:6] + ".." if len(self.badge_name) > 6 else self.badge_name
        painter.drawText(QRectF(rect.x(), rect.bottom() - 18, rect.width(), 16), Qt.AlignCenter, short_name)


class ModernLabWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("آزمایشگاه شیمی پیشرفته - شیمی‌لَب (نسخه 44 Pro + اتم بور + PDF)")
        self.resize(1550, 950)
        self.is_dark_mode = True

        self.engine = LabEngine()
        self.check_login()

        self.data_time, self.data_ph, self.data_temp = [], [], []
        self.last_ph = 7.0

        self.setup_ui()
        self.update_player_stats()

        self.timer = QTimer()
        self.timer.timeout.connect(self.game_loop)
        QTimer.singleShot(500, self.start_simulation)

        self._last_warning_temp = 0

    def check_login(self):
        save_path = get_save_path()
        if self.engine.player_name == "دانشجو" or not os.path.exists(save_path):
            dlg = LoginDialog(self)
            if dlg.exec_() == QDialog.Accepted:
                self.engine.set_player_name(dlg.get_name())

    def start_simulation(self):
        self.timer.start(50)

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # نوار بالای برنامه برای شخصی‌سازی پنل‌ها
        top_bar = QFrame()
        top_bar.setStyleSheet("background-color: #161622; border-bottom: 2px solid #313244; padding: 4px;")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(10, 4, 10, 4)
        btn_customize = QPushButton("⚙️ شخصی‌سازی پنل‌ها")
        btn_customize.setStyleSheet(
            "background-color: #89b4fa; color: #1e1e2e; font-weight: bold; padding: 8px 16px; "
            "border-radius: 6px; font-size: 14px;")
        btn_customize.clicked.connect(self.open_customize_panel)
        top_layout.addWidget(btn_customize)
        top_layout.addStretch()
        self.lbl_top_status = QLabel("شیمی‌لَب V44 Pro")
        self.lbl_top_status.setStyleSheet("color: #89dceb; font-weight: bold; font-size: 14px;")
        top_layout.addWidget(self.lbl_top_status)
        layout.addWidget(top_bar)

        # پنل اصلی با سه بخش
        main_splitter = QSplitter(Qt.Horizontal)
        self.left_panel = self._create_left_panel()
        self.center_panel = self._create_center_panel()
        self.right_tabs = self._create_all_tabs()

        main_splitter.addWidget(self.left_panel)
        main_splitter.addWidget(self.center_panel)
        main_splitter.addWidget(self.right_tabs)
        main_splitter.setSizes([400, 450, 700])
        self.main_splitter = main_splitter

        layout.addWidget(main_splitter)

        # نوار ابزار پایین
        self._create_bottom_toolbar(layout)

    def open_customize_panel(self):
        """پنجره شخصی‌سازی: نمایش/مخفی کردن بخش‌های رابط"""
        dlg = QDialog(self)
        dlg.setWindowTitle("شخصی‌سازی پنل‌ها")
        dlg.setFixedSize(420, 380)
        dlg.setStyleSheet("background-color: #1e1e2e; color: #cdd6f4;")
        v = QVBoxLayout(dlg)
        v.addWidget(QLabel("بخش‌هایی که می‌خواهید دیده شوند را علامت بزنید:"))
        from PyQt5.QtWidgets import QCheckBox
        cb_left = QCheckBox("پنل چپ (مواد و ابزار)")
        cb_left.setChecked(self.left_panel.isVisible())
        cb_center = QCheckBox("ظرف واکنش (مرکز)")
        cb_center.setChecked(self.center_panel.isVisible())
        cb_right = QCheckBox("تب‌های راست (اطلاعات)")
        cb_right.setChecked(self.right_tabs.isVisible())
        cb_bottom = QCheckBox("نوار ابزار پایین")
        bottom_bar = None
        for i in range(self.centralWidget().layout().count()):
            item = self.centralWidget().layout().itemAt(i)
            if item and item.widget() and isinstance(item.widget(), QFrame):
                w = item.widget()
                if "border-top" in (w.styleSheet() or ""):
                    bottom_bar = w
                    break
        cb_bottom.setChecked(bottom_bar.isVisible() if bottom_bar else True)
        for cb in (cb_left, cb_center, cb_right, cb_bottom):
            cb.setStyleSheet("font-size: 14px; padding: 6px;")
            v.addWidget(cb)
        v.addStretch()
        btn_ok = QPushButton("اعمال")
        btn_ok.setStyleSheet("background-color: #a6e3a1; color: #1e1e2e; font-weight: bold; padding: 10px;")
        def apply():
            self.left_panel.setVisible(cb_left.isChecked())
            self.center_panel.setVisible(cb_center.isChecked())
            self.right_tabs.setVisible(cb_right.isChecked())
            if bottom_bar:
                bottom_bar.setVisible(cb_bottom.isChecked())
            dlg.accept()
        btn_ok.clicked.connect(apply)
        v.addWidget(btn_ok)
        dlg.exec_()


    def _create_left_panel(self):
        panel = QFrame()
        panel.setFixedWidth(400)
        vbox = QVBoxLayout(panel)

        # ---------- پروفایل ----------
        gb_player = QGroupBox("پروفایل شیمیدان")
        v_player = QVBoxLayout()
        h_top = QHBoxLayout()
        self.lbl_welcome = QLabel(f"👤 شیمیدان: {self.engine.player_name}")
        self.lbl_welcome.setStyleSheet("color: #a6e3a1; font-size: 18px; font-weight: bold;")
        btn_theme = QPushButton("🌓 تم")
        btn_theme.setFixedSize(100, 40)
        btn_theme.setStyleSheet("background-color: #45475a; color: #f9e2af; font-weight: bold; border-radius: 8px; font-size: 15px; padding: 6px 12px;")
        btn_theme.clicked.connect(self.toggle_theme)
        h_top.addWidget(self.lbl_welcome)
        h_top.addWidget(btn_theme)
        v_player.addLayout(h_top)

        h_save = QHBoxLayout()
        btn_save = QPushButton("💾 ذخیره")
        btn_save.clicked.connect(self.action_save_state_file)
        btn_load = QPushButton("📂 بارگذاری")
        btn_load.clicked.connect(self.action_load_state_file)
        h_save.addWidget(btn_save)
        h_save.addWidget(btn_load)
        v_player.addLayout(h_save)

        self.lbl_level = QLabel("سطح: 1")
        self.lbl_level.setStyleSheet("color: #fab387; font-size: 14px; font-weight: bold;")
        self.lbl_score = QLabel("امتیاز: 0")
        self.progress_xp = QProgressBar()
        self.progress_xp.setRange(0, 100)
        v_player.addWidget(self.lbl_level)
        v_player.addWidget(self.lbl_score)
        v_player.addWidget(QLabel("پیشرفت تا سطح بعدی:"))
        v_player.addWidget(self.progress_xp)
        gb_player.setLayout(v_player)
        vbox.addWidget(gb_player)

        # ---------- افزودن ماده ----------
        gb_chem = QGroupBox("افزودن ماده به بشر")
        frm = QFormLayout()
        h_search = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍 جستجو...")
        self.search_box.textChanged.connect(self.filter_chemicals)
        self.combo_filter = QComboBox()
        self.combo_filter.addItems(["همه", "اسید", "باز", "نمک", "گاز", "جامد", "مایع"])
        self.combo_filter.currentTextChanged.connect(lambda _: self.filter_chemicals(self.search_box.text()))
        h_search.addWidget(self.search_box)
        h_search.addWidget(self.combo_filter)

        self.combo_chem = QComboBox()
        self.populate_chemicals()
        self.combo_chem.currentIndexChanged.connect(self.update_chem_details)

        self.spin_vol = QDoubleSpinBox()
        self.spin_vol.setRange(0.1, 500)
        self.spin_vol.setValue(50)
        self.spin_vol.setSuffix(" mL/g")
        self.spin_molarity = QDoubleSpinBox()
        self.spin_molarity.setRange(0.01, 20.0)
        self.spin_molarity.setValue(0.1)
        self.spin_molarity.setSingleStep(0.1)

        h_vol = QHBoxLayout()
        h_vol.addWidget(QLabel("مقدار:"))
        h_vol.addWidget(self.spin_vol)
        h_vol.addWidget(QLabel("غلظت(M):"))
        h_vol.addWidget(self.spin_molarity)

        h_btn = QHBoxLayout()
        btn_add = QPushButton("➕ افزودن یکباره")
        btn_add.clicked.connect(self.action_add)
        btn_add.setStyleSheet("background-color: #a6e3a1; color: #1e1e2e;")
        self.btn_titrate = QPushButton("💧 بورت هوشمند")
        self.btn_titrate.setCheckable(True)
        self.btn_titrate.clicked.connect(self.action_toggle_titration)
        self.btn_titrate.setStyleSheet("background-color: #89b4fa; color: #1e1e2e;")
        h_btn.addWidget(btn_add)
        h_btn.addWidget(self.btn_titrate)

        self.spin_drop_rate = QDoubleSpinBox()
        self.spin_drop_rate.setRange(0.1, 10.0)
        self.spin_drop_rate.setValue(1.0)
        self.spin_drop_rate.setPrefix("سرعت قطره: ")

        frm.addRow(h_search)
        frm.addRow("ماده:", self.combo_chem)
        frm.addRow(h_vol)
        frm.addRow(self.spin_drop_rate)
        frm.addRow(h_btn)
        gb_chem.setLayout(frm)
        vbox.addWidget(gb_chem)

        # ---------- ابزارها (فقط سرعت و ابزارهای اصلی) ----------
        gb_tools = QGroupBox("ابزارهای آزمایشگاه")
        v_tools = QVBoxLayout()

        # کنترل سرعت
        gb_speed = QGroupBox("⏱️ کنترل سرعت زمان")
        h_time = QHBoxLayout()
        btn_pause = QPushButton("⏸️ توقف")
        btn_pause.clicked.connect(lambda: self.set_speed(0))
        btn_normal = QPushButton("▶️ عادی")
        btn_normal.clicked.connect(lambda: self.set_speed(1))
        btn_fast = QPushButton("⏩ تند (x5)")
        btn_fast.clicked.connect(lambda: self.set_speed(5))
        h_time.addWidget(btn_pause)
        h_time.addWidget(btn_normal)
        h_time.addWidget(btn_fast)
        gb_speed.setLayout(h_time)
        v_tools.addWidget(gb_speed)

        # دما و فیلتر و همزن (که در نوار پایین هم هستند، اما برای دسترسی سریع)
        h_temp = QHBoxLayout()
        btn_heat = QPushButton("🔥 حرارت (+5°)")
        btn_heat.clicked.connect(self.action_heat)
        btn_heat.setStyleSheet("background-color: #f38ba8; color: #1e1e2e;")
        btn_cool = QPushButton("🧊 خنک‌کننده (-5°)")
        btn_cool.clicked.connect(self.action_cool)
        btn_cool.setStyleSheet("background-color: #89b4fa; color: #1e1e2e;")
        h_temp.addWidget(btn_cool)
        h_temp.addWidget(btn_heat)
        v_tools.addLayout(h_temp)

        gb_tools.setLayout(v_tools)
        vbox.addWidget(gb_tools)

        # ---------- مشخصات ماده ----------
        self.gb_details = self._create_details_group()
        vbox.addWidget(self.gb_details)

        # ---------- لاگ ----------
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        vbox.addWidget(QLabel("📜 سیستم گزارش زنده:"))
        vbox.addWidget(self.txt_log)

        btn_toggle = QPushButton("👁️ نمایش / مخفی‌کردن پنل اطلاعات")
        btn_toggle.setStyleSheet("background-color: #313244; color: #ffffff; font-weight: bold;")
        btn_toggle.clicked.connect(self.toggle_tabs)
        vbox.addWidget(btn_toggle)

        return panel

    def _create_bottom_toolbar(self, parent_layout):
        """نوار ابزار پایین با دکمه‌های پرکاربرد"""
        toolbar = QFrame()
        toolbar.setStyleSheet("background-color: #161622; border-top: 2px solid #313244; padding: 5px;")
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(10)

        btn_filter = QPushButton("⚗️ فیلتر جامدات")
        btn_filter.clicked.connect(self.action_filter)
        btn_filter.setStyleSheet("background-color: #f9e2af; color: #1e1e2e;")
        layout.addWidget(btn_filter)

        self.btn_stirrer = QPushButton("🌪️ همزن مغناطیسی")
        self.btn_stirrer.setCheckable(True)
        self.btn_stirrer.clicked.connect(self.action_toggle_stirrer)
        self.btn_stirrer.setStyleSheet("background-color: #cba6f7; color: #1e1e2e;")
        layout.addWidget(self.btn_stirrer)

        btn_photo = QPushButton("📸 عکس از ظرف")
        btn_photo.clicked.connect(self.action_screenshot)
        layout.addWidget(btn_photo)

        btn_wash = QPushButton("🚿 تعویض ظرف")
        btn_wash.clicked.connect(self.action_wash)
        btn_wash.setStyleSheet("background-color: #89dceb; color: #1e1e2e;")
        layout.addWidget(btn_wash)

        layout.addStretch()

        # نمایش 3D بشر
        if HAS_OPENGL:
            btn_3d = QPushButton("🖥️ بشر سه‌بعدی (جایگزین)")
            btn_3d.clicked.connect(self.toggle_beaker_view)
            btn_3d.setStyleSheet("background-color: #a6e3a1; color: #1e1e2e;")
            layout.addWidget(btn_3d)

        parent_layout.addWidget(toolbar)

    def show_3d_beaker(self):
        """نمایش بشر سه‌بعدی در یک دیالوگ"""
        if not HAS_OPENGL:
            QMessageBox.information(self, "اطلاع", "کتابخانه OpenGL نصب نیست.")
            return
        dlg = QDialog(self)
        dlg.setWindowTitle("بشر سه‌بعدی")
        dlg.setFixedSize(600, 700)
        dlg.setStyleSheet("background-color: #0d0d14;")
        layout = QVBoxLayout(dlg)
        gl_beaker = GLBeakerCanvas()
        layout.addWidget(gl_beaker)
        lbl = QLabel("💡 با ماوس بچرخانید")
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet("color: #a6e3a1; font-size: 14px;")
        layout.addWidget(lbl)
        btn_close = QPushButton("بستن")
        btn_close.clicked.connect(dlg.accept)
        btn_close.setStyleSheet("background-color: #313244; color: #cdd6f4; padding: 8px; border-radius: 6px;")
        layout.addWidget(btn_close)
        dlg.exec_()

    def _create_center_panel(self):
        panel = QFrame()
        panel.setStyleSheet("background-color: #11111b; border-radius: 10px; border: 2px solid #313244;")
        v_vis = QVBoxLayout(panel)
        h_title = QHBoxLayout()
        title = QLabel("ظرف واکنش هوشمند (1000 mL)")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; color: #89dceb; font-weight: bold; padding: 10px;")
        h_title.addWidget(title, 1)
        self.btn_toggle_beaker_view = QPushButton("🖥️ ۲بعدی / ۳بعدی")
        self.btn_toggle_beaker_view.setStyleSheet(
            "background-color: #a6e3a1; color: #1e1e2e; font-weight: bold; padding: 6px 12px; border-radius: 6px;")
        self.btn_toggle_beaker_view.clicked.connect(self.toggle_beaker_view)
        if not HAS_OPENGL:
            self.btn_toggle_beaker_view.setEnabled(False)
        h_title.addWidget(self.btn_toggle_beaker_view)
        v_vis.addLayout(h_title)

        self.container = AnimatedContainer(self.engine)
        self.beaker_stack = QStackedLayout()
        stack_host = QWidget()
        stack_host.setLayout(self.beaker_stack)
        self.beaker_stack.addWidget(self.container)
        self.gl_beaker = None
        if HAS_OPENGL:
            self.gl_beaker = GLBeakerCanvas()
            self.beaker_stack.addWidget(self.gl_beaker)
        self.beaker_stack.setCurrentWidget(self.container)
        self._beaker_is_3d = False
        v_vis.addWidget(stack_host, 1)

        info_frame = QFrame()
        info_frame.setStyleSheet("background-color: #1e1e2e; border-radius: 8px; padding: 5px;")
        info_h = QHBoxLayout(info_frame)
        self.lbl_ph_display = QLabel("pH: 7.00")
        self.lbl_ph_display.setStyleSheet("font-size: 22px; color: #a6e3a1; font-weight: bold;")
        self.lbl_temp_display = QLabel("25.0 °C")
        self.lbl_temp_display.setStyleSheet("font-size: 22px; color: #f38ba8; font-weight: bold;")
        self.lbl_stirrer_3d = QLabel("")
        self.lbl_stirrer_3d.setStyleSheet("font-size: 16px; color: #cba6f7; font-weight: bold;")
        info_h.addWidget(self.lbl_ph_display)
        info_h.addStretch()
        info_h.addWidget(self.lbl_stirrer_3d)
        info_h.addWidget(self.lbl_temp_display)
        v_vis.addWidget(info_frame)
        return panel

    def toggle_beaker_view(self):
        if not HAS_OPENGL or self.gl_beaker is None:
            return
        self._beaker_is_3d = not self._beaker_is_3d
        if self._beaker_is_3d:
            self.beaker_stack.setCurrentWidget(self.gl_beaker)
            self.btn_toggle_beaker_view.setText("📐 بازگشت به ۲بعدی")
        else:
            self.beaker_stack.setCurrentWidget(self.container)
            self.btn_toggle_beaker_view.setText("🖥️ ۲بعدی / ۳بعدی")


    def _create_all_tabs(self):
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_about_tab(), "ℹ️ درباره")
        self.tabs.addTab(self.create_report_card_tab(), "📊 کارنامه")
        self.tabs.addTab(self.create_missions_badges_tab(), "🎯 چالش‌ها و مدال‌ها")
        self.tabs.addTab(self.create_notes_tab(), "📝 گزارش و لاگ")
        self.tabs.addTab(self.create_contents_tab(), "🧪 محتویات")
        self.tabs.addTab(self.create_graph_tab(), "📈 نمودار")
        self.tabs.addTab(self.create_discoveries_tab(), "🏆 کشف‌ها")
        self.tabs.addTab(self.create_wiki_tab(), "📖 دانشنامه")
        self.tabs.addTab(self.create_datasheet_tab(), "📚 لیست مواد")
        self.tabs.addTab(BohrModelWidget(), "⚛️ مدل بور (۱۱۸)")
        return self.tabs

    def _create_details_group(self):
        gb = QGroupBox("مشخصات ماده")
        gl = QGridLayout(gb)
        self.lbl_d_name = QLabel("-")
        self.lbl_d_form = QLabel("-")
        self.lbl_d_type = QLabel("-")
        gl.addWidget(QLabel("نام:"), 0, 0)
        gl.addWidget(self.lbl_d_name, 0, 1)
        gl.addWidget(QLabel("فرمول:"), 1, 0)
        gl.addWidget(self.lbl_d_form, 1, 1)
        gl.addWidget(QLabel("نوع:"), 2, 0)
        gl.addWidget(self.lbl_d_type, 2, 1)
        return gb

    # ==================== متدهای مربوط به تب‌ها ====================
    def create_about_tab(self):
        w = QWidget()
        w.setStyleSheet("background-color: #1e1e2e;")
        layout = QVBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
              QScrollArea {
                  background-color: #1e1e2e;
                  border: none;
              }
              QScrollBar:vertical {
                  background: #313244;
                  width: 12px;
                  border-radius: 6px;
              }
              QScrollBar::handle:vertical {
                  background: #89b4fa;
                  border-radius: 6px;
                  min-height: 30px;
              }
              QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                  border: none;
                  background: none;
              }
          """)

        content_widget = QWidget()
        content_widget.setStyleSheet("background-color: #1e1e2e;")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(15, 15, 15, 15)

        about_text = """بسم الله الرحمن الرحیم<br>
      با سلام و احترام به داوران محترم<br>
      <br>
      پروژه «شیمی‌لَب» (Universe ChimiLab) یک شبیه‌ساز پیشرفته آزمایشگاه شیمی است که با هدف حل ریشه‌ای مشکلات آموزش شیمی در ایران طراحی شده است. این نرم‌افزار با ترکیب یادگیری تعاملی، محاسبات دقیق شیمیایی، گرافیک سه‌بعدی و عناصر بازی‌گونه، فضایی امن، کم‌هزینه و کاملاً در دسترس برای همه دانش‌آموزان و علاقه‌مندان به شیمی فراهم می‌کند.<br>
      <br>
      مشکلات موجود در آموزش شیمی کشور:<br>
      ۱. حدود ۶۵ درصد از مدارس کشور فاقد آزمایشگاه شیمی هستند.<br>
      ۲. راه‌اندازی و نگهداری آزمایشگاه واقعی هزینه‌های بسیار بالایی دارد و تعویض تجهیزات و مواد مصرفی، به‌ویژه در مدارس دولتی، عملاً غیرممکن است.<br>
      ۳. دانش‌آموزان مناطق محروم و روستایی هرگز فرصت تجربه یک آزمایش عملی شیمی را نداشته‌اند.<br>
      ۴. سالانه صدها حادثه آتش‌سوزی و مسمومیت در آزمایشگاه‌های مدارس رخ می‌دهد که خطرات جانی و مالی جبران‌ناپذیری به همراه دارد.<br>
      ۵. نتیجه مستقیم این کمبودها، میانگین نمره عملی شیمی دانش‌آموزان کنکور زیر ۳۰ درصد است.<br>
      <br>
      هدف پروژه:<br>
      ما می‌خواهیم هر دانش‌آموز، در هر نقطه از کشور، بدون نیاز به اینترنت، بدون هیچ خطر جانی یا مالی، بدون هزینه‌های سنگین و بدون تجهیزات واقعی، بتواند آزمایش‌های شیمی را شخصاً انجام دهد و مفاهیم را به صورت عمیق و عملی درک کند.<br>
      <br>
      جامعهٔ هدف:<br>
      دانش‌آموزان متوسطه اول و دوم، دانشجویان، معلمان و همه علاقه‌مندان به علم شیمی.<br>
      <br>
      ویژگی‌های اصلی (قلب نرم‌افزار):<br>
      • رابط کاربری پیشرفته و چندحالته با انیمیشن‌های روان و تم‌های سینمایی، علمی و سایبرپانک که حس کار در یک آزمایشگاه واقعی را القا می‌کند.<br>
      • مدل اتمی بور و آرایش اوربیتالی برای ۱۱۸ عنصر جدول تناوبی با نمایش سه‌بعدی (OpenGL) و قابلیت چرخش با ماوس — امکان افزایش یا کاهش الکترون‌ها و مشاهده اطلاعات کامل هر عنصر.<br>
      • شبیه‌سازی فیزیکی دما با انتقال تدریجی حرارت به محیط، محاسبه گرمای واکنش‌ها و تأثیر دما بر سرعت واکنش.<br>
      • محاسبات دقیق شیمیایی با استفاده از کتابخانه تخصصی molmass برای محاسبه جرم مولکولی، تعداد مول، فرمول تجربی مخلوط‌ها و تعادل‌های شیمیایی.<br>
      • حالت Sandbox (آزمایش آزاد): کاربر می‌تواند هر ماده‌ای را با ماده دیگر ترکیب کند، دما را تغییر دهد، مواد را فیلتر کند، از همزن مغناطیسی استفاده کند و نتایج را به‌صورت زنده مشاهده نماید — درست مانند یک زمین بازی علمی بدون محدودیت.<br>
      • سیستم مأموریت، امتیاز (XP) و مدال شامل ۷ مأموریت داخلی (مانند خنثی‌سازی، تیتراسیون، رسیدن به دمای جوش و کشف واکنش) که انگیزه یادگیری را به‌طور چشمگیری افزایش می‌دهد.<br>
      • پایگاه داده SQLite حاوی ۶۵۵ ماده شیمیایی مختلف (با اطلاعات کامل فرمول، رنگ، نوع، pH، گرمای نهان و غلظت) که کاملاً آفلاین کار می‌کند.<br>
      • مشاهده مشخصات مواد با یک کلیک (نام، فرمول، نوع، رنگ، مولاریته، pH و گرمای واکنش) و جستجوی پیشرفته بر اساس نام یا فرمول.<br>
      • ابزارهای پیشرفته آزمایشگاهی شامل: بورت هوشمند (با تیتراسیون خودکار و تشخیص نقطه هم‌ارزی)، فیلتر جامدات، همزن مغناطیسی، گرمایش/سرمایش، عکس‌برداری از ظرف و تغییر برچسب.<br>
      • سیستم ذخیره و بارگذاری وضعیت آزمایش در فایل‌های JSON و امکان گزارش‌گیری حرفه‌ای به‌صورت PDF و TXT همراه با یادداشت‌ها، لاگ زمانی و عکس لحظه‌ای.<br>
      • نمودارهای پویا و لحظه‌ای برای pH و دما همراه با تحلیل تغییرات در طول آزمایش.<br>
      <br>
      ویژگی‌های تکمیلی:<br>
      • پشتیبانی کامل از ۶۵۵ ماده شیمیایی با امکان افزودن واکنش‌های سفارشی و مواد جدید.<br>
      • مدل اتمی بور با نمایش لایه‌های K تا Q و تعداد الکترون‌های هر لایه.<br>
      • محاسبه فرمول تجربی مخلوط بر اساس تعداد مول اتم‌های شرکت‌کننده.<br>
      • تیتراسیون خودکار با الگوریتم تشخیص نقطه هم‌ارزی و اعطای امتیاز اضافی در صورت موفقیت.<br>
      • سیستم اعلان‌های ایمنی (هشدارهایی مانند افزودن آب به اسید، واکنش‌های گرمازا، سرریز ظرف و غیره).<br>
      • وبسایت معرفی پروژه با امکان مشاهده مأموریت‌ها، دانلود نسخه ویندوز، دسترسی به کد منبع در GitHub و ارتباط مستقیم با سازنده.<br>
      • انطباق کامل با زبان فارسی و پشتیبانی از راست‌به‌چپ (RTL) در تمام بخش‌ها.<br>
      <br>
      سازگاری و تست:<br>
      نرم‌افزار با موفقیت روی ویندوز ۷، ۱۰ و ۱۱ تست شده و بدون نیاز به نصب هیچ پیش‌نیاز اضافی اجرا می‌شود. نسخه اجرایی مستقل (exe) به همراه تمام کتابخانه‌های مورد نیاز، از طریق وبسایت پروژه قابل دانلود است.<br>
      <br>
      مزیت‌های رقابتی نسبت به نرم‌افزارهای مشابه:<br>
      ۱. بومی‌سازی کامل به زبان فارسی و متناسب با نیازهای دانش‌آموز ایرانی.<br>
      ۲. کاملاً آفلاین — مناسب مناطق دورافتاده و محروم.<br>
      ۳. حجم کم و عملکرد روان حتی روی ضعیف‌ترین سیستم‌ها (حداقل ۲ گیگابایت رم).<br>
      ۴. حالت Sandbox قدرتمند که در اکثر نرم‌افزارهای آموزشی شیمی وجود ندارد.<br>
      ۵. رویکرد بازی‌گونه (مأموریت، XP و مدال) که یادگیری را به یک تجربه جذاب و چالش‌برانگیز تبدیل می‌کند.<br>
      ۶. وبسایت اختصاصی برای معرفی، دانلود و دریافت بازخورد.<br>
      ۷. مدل اتمی بور سه‌بعدی و ابزارهای گرافیکی پیشرفته (نمودارهای لحظه‌ای، انیمیشن‌های واکنش و افکت‌های بصری) که تجربه‌ای منحصربه‌فرد ایجاد می‌کند.<br>
      <br>
      نتیجه‌گیری:<br>
      با شیمی‌لَب، دیوار بی‌آزمایشگاهی در مدارس کشور فرو می‌ریزد و هر دانش‌آموز، صرف‌نظر از موقعیت جغرافیایی و وضعیت اقتصادی، فرصت درک عملی و عمیق شیمی را پیدا خواهد کرد. این پروژه گامی مؤثر در جهت عدالت آموزشی و ارتقای کیفیت یادگیری علوم پایه در ایران است.<br>
      <br>
      سپاسگزارم از توجه شما.<br>
      <br>
      طراح و برنامه‌نویس: کیانوش فدائی (دانش‌آموز کلاس نهم، مدرسه شهید اسدالله‌زاده)<br>
      ارتباط با سازنده: kianfadaee448@gmail.com<br>
      GitHub: github.com/kianfadaee448-alt/ChimiLab<br>
      وبسایت رسمی: ChimiLab.ir"""

        label = QLabel()
        label.setWordWrap(True)
        label.setTextFormat(Qt.RichText)
        label.setText(f"""
              <div style="font-family: 'Tahoma', sans-serif; font-size: 15px; line-height: 2.2; color: #a6e3a1; text-align: justify; direction: rtl; padding: 20px;">
                  {about_text}
              </div>
          """)
        label.setStyleSheet("""
              QLabel {
                  background-color: #1e1e2e;
                  border: 2px solid #45475a;
                  border-radius: 8px;
                  padding: 20px;
                  margin: 0px;
              }
          """)

        content_layout.addWidget(label)
        content_layout.addStretch()

        scroll.setWidget(content_widget)
        layout.addWidget(scroll)

        return w

    def create_report_card_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        lbl_title = QLabel("📊 کارنامه و آمار عملکرد شیمیدان")
        lbl_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #89b4fa; margin: 10px;")
        l.addWidget(lbl_title)
        self.lbl_stats = QLabel()
        self.lbl_stats.setStyleSheet(
            "font-size: 16px; line-height: 2.0; padding: 15px; background-color: #1e1e2e; border-radius: 10px;")
        l.addWidget(self.lbl_stats)
        l.addStretch()
        return w

    def create_missions_badges_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)

        l.addWidget(QLabel("🎯 چالش‌های داخلی:"))
        self.list_missions = QListWidget()
        self.list_missions.setStyleSheet("QListWidget::item { padding: 8px; border-bottom: 1px solid #313244; }")
        l.addWidget(self.list_missions)

        l.addWidget(QLabel("🏅 اتاق مدال‌ها (موس روی هر مدال برای مشاهده توضیحات):"))
        scroll_badges = QScrollArea()
        scroll_badges.setWidgetResizable(True)
        scroll_badges.setStyleSheet("border: none; background-color: transparent;")
        badges_widget = QWidget()
        badges_layout = QGridLayout(badges_widget)
        badges_layout.setSpacing(10)
        self.badge_widgets = []
        scroll_badges.setWidget(badges_widget)
        l.addWidget(scroll_badges)

        self.update_missions_ui()
        return w

    def create_notes_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("📝 دفترچه یادداشت و صدور گزارش (PDF):"))
        self.txt_notes = QTextEdit()
        self.txt_notes.setStyleSheet(
            "QTextEdit { font-size: 16px; background-color: #1e1e2e; color: #cdd6f4; padding: 15px; border-radius: 8px; font-weight: 500; line-height: 1.8; border: 2px solid #89b4fa; }")
        self.txt_notes.setPlaceholderText("یادداشت‌های خود را بنویسید...")
        self.txt_notes.setText(self.engine.notes)
        self.txt_notes.textChanged.connect(self.save_notes)
        l.addWidget(self.txt_notes)

        l.addWidget(QLabel("⏱️ لاگ زمانی خودکار:"))
        self.list_auto_log = QListWidget()
        self.list_auto_log.setStyleSheet("background-color: #11111b; font-family: monospace; font-size: 12px;")
        l.addWidget(self.list_auto_log)

        h_export = QHBoxLayout()
        btn_txt = QPushButton("📥 گزارش TXT")
        btn_txt.clicked.connect(self.action_export_txt)
        btn_txt.setStyleSheet("background-color: #a6e3a1; color: #1e1e2e; font-weight: bold;")
        btn_pdf = QPushButton("📑 خروجی حرفه‌ای PDF")
        btn_pdf.clicked.connect(self.action_export_pdf)
        btn_pdf.setStyleSheet("background-color: #fab387; color: #1e1e2e; font-weight: bold;")
        h_export.addWidget(btn_txt)
        h_export.addWidget(btn_pdf)
        l.addLayout(h_export)
        return w

    def create_contents_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        self.table_cont = QTableWidget()
        self.table_cont.setColumnCount(5)
        self.table_cont.setHorizontalHeaderLabels(["ماده", "فرمول", "مقدار", "واحد", "حذف"])
        self.table_cont.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        l.addWidget(self.table_cont)

        mix_frame = QFrame()
        mix_frame.setStyleSheet("background-color: #313244; border-radius: 8px; padding: 10px;")
        mix_layout = QHBoxLayout(mix_frame)
        mix_layout.addWidget(QLabel("فرمول تجربی مخلوط: "))
        self.lbl_mix = QLabel("-")
        self.lbl_mix.setStyleSheet("font-size: 18px; font-weight: bold; color: #a6e3a1;")
        mix_layout.addWidget(self.lbl_mix)
        mix_layout.addStretch()
        l.addWidget(mix_frame)
        return w

    def create_graph_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        self.figure = Figure(figsize=(5, 6), facecolor='#11111b')
        self.canvas = FigureCanvas(self.figure)
        self.ax1 = self.figure.add_subplot(211)
        self.ax1.set_facecolor('#1e1e2e')
        self.ax1.set_ylabel('pH', color='white')
        self.ax1.tick_params(colors='white')
        self.ax2 = self.figure.add_subplot(212)
        self.ax2.set_facecolor('#1e1e2e')
        self.ax2.set_ylabel('Temp (°C)', color='white')
        self.ax2.tick_params(colors='white')
        self.line_ph, = self.ax1.plot([], [], color='#a6e3a1', linewidth=2)
        self.line_temp, = self.ax2.plot([], [], color='#f38ba8', linewidth=2)
        l.addWidget(self.canvas)
        return w

    def create_discoveries_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        self.table_disc = QTableWidget()
        self.table_disc.setColumnCount(3)
        self.table_disc.setHorizontalHeaderLabels(["نام واکنش", "امتیاز", "توضیحات"])
        self.table_disc.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table_disc.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        l.addWidget(self.table_disc)
        self.update_discoveries_table()
        return w

    def create_wiki_tab(self):
        """تب دانشنامه با نمایش فقط واکنش‌های کشف شده به صورت کارت"""
        w = QWidget()
        layout = QVBoxLayout(w)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background-color: transparent;")

        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(15)

        # فقط واکنش‌های کشف شده
        discovered_reactions = {k: v for k, v in CUSTOM_REACTIONS.items() if k in self.engine.discovered}
        if not discovered_reactions:
            lbl = QLabel("هیچ واکنشی کشف نشده است. برای کشف واکنش‌ها، مواد مختلف را با هم ترکیب کنید.")
            lbl.setStyleSheet("color: #a6adc8; font-size: 16px; padding: 20px;")
            lbl.setAlignment(Qt.AlignCenter)
            container_layout.addWidget(lbl)
        else:
            for name, rxn in discovered_reactions.items():
                card = QFrame()
                card.setStyleSheet("""
                    QFrame {
                        background-color: #1e1e2e;
                        border: 2px solid #313244;
                        border-radius: 10px;
                        padding: 10px;
                    }
                    QFrame:hover {
                        border: 2px solid #89b4fa;
                    }
                """)
                card_layout = QVBoxLayout(card)

                title_lbl = QLabel(f"🧪 {name}")
                title_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #f9e2af;")
                card_layout.addWidget(title_lbl)

                reactants_text = " + ".join([CHEMILAB_DB.get(r, {}).get('name', r) for r in rxn.get('reactants', [])])
                if reactants_text:
                    lbl_react = QLabel(f"مواد: {reactants_text}")
                    lbl_react.setStyleSheet("color: #cdd6f4; font-size: 13px;")
                    card_layout.addWidget(lbl_react)

                products = rxn.get('products', [])
                if products:
                    prod_layout = QHBoxLayout()
                    prod_layout.addWidget(QLabel("محصولات:"))
                    for p in products:
                        p_data = CHEMILAB_DB.get(p, {})
                        p_name = p_data.get('name', p)
                        p_color = p_data.get('color', '#ffffff')
                        p_btn = QPushButton(f"■ {p_name}")
                        p_btn.setStyleSheet(f"""
                            background-color: {p_color};
                            color: {'#1e1e2e' if QColor(p_color).lightness() > 128 else '#ffffff'};
                            border-radius: 6px;
                            padding: 5px 10px;
                            font-weight: bold;
                            border: 1px solid #45475a;
                        """)
                        p_btn.clicked.connect(lambda checked, name=p_name, c=p_color: self.show_product_detail(name, c))
                        prod_layout.addWidget(p_btn)
                    prod_layout.addStretch()
                    card_layout.addLayout(prod_layout)

                info_lbl = QLabel(f"⚡ امتیاز: {rxn.get('xp', 0)}  |  🌡️ دمای مورد نیاز: {rxn.get('temp_min', '-273')}°C")
                info_lbl.setStyleSheet("color: #a6adc8; font-size: 12px;")
                card_layout.addWidget(info_lbl)

                status_lbl = QLabel("✅ کشف شده")
                status_lbl.setStyleSheet("color: #a6e3a1; font-weight: bold;")
                card_layout.addWidget(status_lbl)

                container_layout.addWidget(card)

        container_layout.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll)

        return w

    def show_product_detail(self, name, color):
        dlg = QDialog(self)
        dlg.setWindowTitle(f"🔬 {name}")
        dlg.setFixedSize(400, 300)
        dlg.setStyleSheet("background-color: #1e1e2e; border: 2px solid #89b4fa; border-radius: 10px;")

        layout = QVBoxLayout(dlg)

        img_label = QLabel()
        pixmap = QPixmap(200, 200)
        pixmap.fill(QColor(color))
        img_label.setPixmap(pixmap)
        img_label.setAlignment(Qt.AlignCenter)
        img_label.setStyleSheet("border: 2px solid #45475a; border-radius: 8px;")
        layout.addWidget(img_label)

        lbl_name = QLabel(f"🧪 {name}")
        lbl_name.setStyleSheet("font-size: 22px; font-weight: bold; color: #f9e2af;")
        lbl_name.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_name)

        lbl_color = QLabel(f"رنگ: {color}")
        lbl_color.setStyleSheet("color: #cdd6f4; font-size: 14px;")
        lbl_color.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_color)

        btn_close = QPushButton("بستن")
        btn_close.clicked.connect(dlg.accept)
        btn_close.setStyleSheet("background-color: #313244; color: #cdd6f4; padding: 8px; border-radius: 6px;")
        layout.addWidget(btn_close)

        dlg.exec_()

    def create_datasheet_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 جستجو (نام یا فرمول)...")
        self.search_input.setStyleSheet(
            "padding: 8px; border-radius: 6px; border: 2px solid #45475a; background-color: #1e1e2e; color: #a6e3a1; font-size: 14px;")
        self.search_input.textChanged.connect(self.filter_datasheet)
        layout.addWidget(self.search_input)

        self.datasheet_table = QTableWidget()
        self.datasheet_table.setColumnCount(7)
        self.datasheet_table.setHorizontalHeaderLabels(["نام", "فرمول", "نوع", "رنگ", "مولاریته (M)", "pH", "دما"])
        self.datasheet_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.datasheet_table.setStyleSheet(
            "QTableWidget { background-color: #11111b; gridline-color: #313244; color: #cdd6f4; border: 1px solid #313244; border-radius: 6px; } QHeaderView::section { background-color: #1e1e2e; padding: 8px; border: 1px solid #313244; color: #f9e2af; font-weight: bold; }")
        layout.addWidget(self.datasheet_table)

        self.all_datasheet_items = sorted(CHEMILAB_DB.items(), key=lambda x: x[1]['name'])
        self.populate_datasheet(self.all_datasheet_items)
        return w

    # ==================== متدهای به‌روزرسانی (Update) ====================
    def update_player_stats(self):
        self.lbl_level.setText(f"سطح: {self.engine.level}")
        self.lbl_score.setText(f"امتیاز: {self.engine.score}")
        self.lbl_welcome.setText(f"👤 شیمیدان: {self.engine.player_name}")
        self.progress_xp.setValue(self.engine.score % 100)

    def update_contents_ui(self):
        self.table_cont.setRowCount(0)
        for i, layer in enumerate(self.engine.visual_layers):
            self.table_cont.insertRow(i)
            self.table_cont.setItem(i, 0, QTableWidgetItem(layer['name']))
            f = CHEMILAB_DB.get(layer['key'], {}).get('formula', '?')
            self.table_cont.setItem(i, 1, QTableWidgetItem(ChemicalCalculator.to_subscript(f)))
            self.table_cont.setItem(i, 2, QTableWidgetItem(f"{layer['amount']:.2f}"))
            ctype = CHEMILAB_DB.get(layer['key'], {}).get('type', '')
            unit = "g" if any(x in ctype for x in ["Solid", "Metal", "Salt", "Precipitate"]) else "mL"
            self.table_cont.setItem(i, 3, QTableWidgetItem(unit))
            btn_del = QPushButton("❌")
            btn_del.setFixedSize(30, 25)
            btn_del.setStyleSheet("background-color: #ff5555; border-radius: 4px;")
            btn_del.clicked.connect(lambda checked, lid=layer['id']: self.remove_item(lid))
            self.table_cont.setCellWidget(i, 4, btn_del)
        self.lbl_mix.setText(self.engine.get_mixture_empirical_formula())

    def update_missions_ui(self):
        self.list_missions.clear()
        for m in self.engine.missions:
            status = "✅" if m['id'] in self.engine.completed_missions else "⏳"
            icons = {
                "m1": "🧪", "m2": "🔬", "m3": "🧪", "m4": "🔥",
                "m5": "⚖️", "m6": "💥", "m7": "💧"
            }
            icon = icons.get(m['id'], "🎯")
            self.list_missions.addItem(f"{icon} {status} | {m['title']} (+{m['xp']} XP)\n   {m['desc']}")

        # به‌روزرسانی مدال‌ها
        scroll_widget = self.tabs.widget(2)
        if scroll_widget:
            for child in scroll_widget.children():
                if isinstance(child, QScrollArea):
                    badges_widget = child.widget()
                    if badges_widget:
                        for wdg in self.badge_widgets:
                            wdg.deleteLater()
                        self.badge_widgets.clear()

                        layout = badges_widget.layout()
                        if layout:
                            while layout.count():
                                item = layout.takeAt(0)
                                if item.widget():
                                    item.widget().deleteLater()

                            row, col = 0, 0
                            for badge in self.engine.badges:
                                bw = BadgeWidget(badge)
                                layout.addWidget(bw, row, col)
                                self.badge_widgets.append(bw)
                                col += 1
                                if col >= 4:
                                    col = 0
                                    row += 1

    def update_report_card(self):
        if not hasattr(self, 'lbl_stats'):
            return
        s = self.engine.stats
        play_m, play_s = divmod(int(s['total_play_time']), 60)
        play_h, play_m = divmod(play_m, 60)
        time_str = f"{play_h} ساعت و {play_m} دقیقه و {play_s} ثانیه"

        score = 0
        reactions = s['reactions_found']
        if reactions >= 15:
            score += 60
        elif reactions >= 10:
            score += 45
        elif reactions >= 5:
            score += 25
        elif reactions >= 1:
            score += 10

        titrations = s['successful_titrations']
        if titrations >= 5:
            score += 20
        elif titrations >= 3:
            score += 12
        elif titrations >= 1:
            score += 5

        filters = s['filter_uses']
        if filters >= 5:
            score += 10
        elif filters >= 2:
            score += 5
        elif filters >= 1:
            score += 2

        breaks = s['flask_breaks']
        if breaks == 0:
            score += 10
        elif breaks == 1:
            score -= 10
        elif breaks == 2:
            score -= 35
        else:
            score -= 70

        final_score = max(0, min(100, score))
        if final_score >= 90:
            grade = "A++ (نابغه)"
        elif final_score >= 75:
            grade = "A+ (عالی)"
        elif final_score >= 65:
            grade = "A (خوب)"
        elif final_score >= 55:
            grade = "B+ (متوسط رو به بالا)"
        elif final_score >= 45:
            grade = "B (متوسط)"
        elif final_score >= 35:
            grade = "C+ (نیاز به تمرین)"
        elif final_score >= 20:
            grade = "C (ضعیف)"
        elif final_score >= 10:
            grade = "D (نیاز به تلاش جدی)"
        else:
            grade = "F (مردود - لطفاً ایمنی را جدی بگیرید!)"

        text = f"""
            <b>⏱️ زمان کل فعالیت:</b> {time_str}<br>
            <b>🧪 تعداد واکنش‌های کشف شده:</b> {s['reactions_found']}<br>
            <b>💥 دفعات شکستن ظرف (خطا):</b> {s['flask_breaks']}<br>
            <b>⚗️ استفاده از فیلتر:</b> {s['filter_uses']} بار<br>
            <b>🎯 تیتراسیون‌های موفق:</b> {s['successful_titrations']}<br><br>
            <hr><br>
            <b>امتیاز نهایی عملکرد: <span style='color:#a6e3a1;'>{final_score} از ۱۰۰</span></b><br>
            <b>نمره ارزیابی کلی سیستم: <span style='color:#f38ba8; font-size: 24px;'>{grade}</span></b>
            """
        self.lbl_stats.setText(text)

    def update_discoveries_table(self):
        self.table_disc.setRowCount(len(CUSTOM_REACTIONS))
        for i, (n, d) in enumerate(CUSTOM_REACTIONS.items()):
            desc = d.get('desc', '')
            temp = d.get('temp_min', '-')
            full_desc = f"{desc} (دمای مورد نیاز: {temp}°C)" if desc else f"دمای مورد نیاز: {temp}°C"
            if n in self.engine.discovered:
                self.table_disc.setItem(i, 0, QTableWidgetItem(f"✅ {n}"))
                self.table_disc.setItem(i, 1, QTableWidgetItem(str(d.get('xp', 0))))
                self.table_disc.setItem(i, 2, QTableWidgetItem(full_desc))
            else:
                self.table_disc.setItem(i, 0, QTableWidgetItem("؟؟؟"))
                self.table_disc.setItem(i, 1, QTableWidgetItem("-"))
                # توضیحات برای همه واکنش‌ها نمایش داده می‌شود حتی اگر کشف نشده باشند
                self.table_disc.setItem(i, 2, QTableWidgetItem(full_desc))

    def update_wiki_tab(self):
        """به‌روزرسانی تب دانشنامه (فقط کشف شده‌ها)"""
        index = self.tabs.indexOf(self.tabs.widget(7))
        if index >= 0:
            new_tab = self.create_wiki_tab()
            self.tabs.removeTab(index)
            self.tabs.insertTab(index, new_tab, "📖 دانشنامه")

    def update_auto_log_ui(self):
        if hasattr(self, 'list_auto_log'):
            self.list_auto_log.clear()
            for log in self.engine.auto_log:
                self.list_auto_log.addItem(log)
            self.list_auto_log.scrollToBottom()

    def populate_datasheet(self, items):
        table = self.datasheet_table
        table.setRowCount(len(items))
        for i, (key, data) in enumerate(items):
            table.setItem(i, 0, QTableWidgetItem(data.get('name', '')))
            table.setItem(i, 1, QTableWidgetItem(ChemicalCalculator.to_subscript(data.get('formula', ''))))
            table.setItem(i, 2, QTableWidgetItem(get_persian_type(data.get('type', ''))))
            color_cell = QTableWidgetItem("")
            color_cell.setBackground(QColor(data.get('color', '#FFFFFF')))
            color_cell.setFlags(Qt.ItemIsEnabled)
            table.setItem(i, 3, color_cell)
            table.setItem(i, 4, QTableWidgetItem(str(data.get('molarity', '-'))))
            table.setItem(i, 5, QTableWidgetItem(str(data.get('pH', '-'))))
            table.setItem(i, 6, QTableWidgetItem(str(data.get('heat', '-'))))
        table.resizeRowsToContents()

    def filter_datasheet(self):
        search = self.search_input.text().strip().lower()
        if not search:
            filtered = self.all_datasheet_items
        else:
            filtered = []
            for key, data in self.all_datasheet_items:
                if search in data.get('name', '').lower() or search in data.get('formula', '').lower():
                    filtered.append((key, data))
        self.populate_datasheet(filtered)

    # ==================== اقدامات کاربر (Actions) ====================
    def action_add(self):
        try:
            k = self.combo_chem.currentData()
            if not k:
                return
            msg, overflow, warnings = self.engine.add_chemical(k, self.spin_vol.value(), self.spin_molarity.value())
            self._log(msg)
            for w in warnings:
                self._log(f"<span style='color:#f38ba8;'>{w}</span>")
            if overflow:
                self.container.trigger_overflow()
            self.update_contents_ui()
            self.handle_reaction_result(self.engine.check_reactions())
            self.update_auto_log_ui()
        except Exception:
            pass

    def action_wash(self):
        self.engine.reset()
        self.container.set_stirrer(False)
        if hasattr(self, 'btn_stirrer'):
            self.btn_stirrer.setChecked(False)
        self.update_contents_ui()
        self._log("🧹 ظرف با موفقیت تعویض و کاملاً تمیز شد.")
        self.update_auto_log_ui()

    def action_heat(self):
        if self.engine.temp_c > FLASK_BREAK_TEMP - 50 and not self.engine.is_broken:
            reply = QMessageBox.question(
                self, "⚠️ هشدار دمای بالا",
                f"دمای فعلی ({self.engine.temp_c:.1f}°C) به دمای شکستن ظرف ({FLASK_BREAK_TEMP}°C) نزدیک است!\n\n"
                "آیا مطمئن هستید که می‌خواهید حرارت را ادامه دهید؟",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        self.engine.change_temperature(HEAT_COOL_DELTA)
        self.container.set_plate_state("heat")
        self._log(f"🔥 گرمایش فعال شد (+{HEAT_COOL_DELTA}°)")

    def action_cool(self):
        self.engine.change_temperature(-HEAT_COOL_DELTA)
        self.container.set_plate_state("cool")
        self._log(f"🧊 سرمایش فعال شد (-{HEAT_COOL_DELTA}°)")

    def action_filter(self):
        removed = self.engine.filter_solids()
        if removed:
            self._log(f"⚗️ مواد جامد فیلتر شدند: {', '.join(removed)}")
            self.update_contents_ui()
        else:
            self._log("⚗️ ماده جامدی برای فیلتر کردن وجود ندارد.")

    def action_toggle_stirrer(self):
        on = self.btn_stirrer.isChecked()
        self.container.set_stirrer(on)
        if hasattr(self, 'lbl_stirrer_3d'):
            self.lbl_stirrer_3d.setText("🌪️ همزن روشن" if on else "")
        if hasattr(self, 'gl_beaker') and self.gl_beaker is not None:
            self.gl_beaker.stirrer_on = on
            self.gl_beaker.update()
        self._log(f"🌪️ همزن مغناطیسی {'روشن' if on else 'خاموش'} شد.")
        self.engine.add_to_log(f"همزن {'روشن' if on else 'خاموش'} شد.")

    def action_toggle_titration(self):
        if self.btn_titrate.isChecked():
            self.btn_titrate.setText("⏹️ توقف بورت")
            self.btn_titrate.setStyleSheet("background-color: #f38ba8; color: #1e1e2e;")
        else:
            self.btn_titrate.setText("💧 بورت هوشمند")
            self.btn_titrate.setStyleSheet("background-color: #89b4fa; color: #1e1e2e;")

    def action_screenshot(self):
        path, _ = QFileDialog.getSaveFileName(self, "ذخیره عکس از ظرف", "ChimiLab_Snapshot.png", "Images (*.png)")
        if path:
            pixmap = self.container.grab()
            painter = QPainterGui(pixmap)
            painter.setPen(QPen(QColor(255, 255, 255, 220), 2))
            font = painter.font()
            font.setPointSize(10)
            font.setBold(True)
            painter.setFont(font)
            info_text = f"🧪 {self.engine.flask_label} | pH: {self.engine.get_ph():.2f} | دما: {self.engine.temp_c:.1f}°C"
            painter.drawText(10, 30, info_text)
            painter.end()
            pixmap.save(path)
            self._log("📸 تصویر ظرف با موفقیت ذخیره شد.")

    def action_save_state_file(self):
        path, _ = QFileDialog.getSaveFileName(self, "ذخیره وضعیت آزمایش", "lab_state.json", "JSON (*.json)")
        if path:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self.engine.to_dict(), f, ensure_ascii=False, indent=2)
            self._log("💾 وضعیت آزمایش در فایل ذخیره شد.")

    def action_load_state_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "بارگذاری وضعیت آزمایش", "", "JSON (*.json)")
        if path:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.engine.from_dict(data)
                self.update_player_stats()
                self.update_contents_ui()
                self.update_missions_ui()
                self.update_wiki_tab()
                self.update_discoveries_table()
                self._log("📂 وضعیت با موفقیت بارگذاری شد.")
            except Exception as e:
                QMessageBox.critical(self, "خطا", f"فایل نامعتبر است.\n{str(e)}")

    def action_export_txt(self):
        filename, _ = QFileDialog.getSaveFileName(self, "ذخیره گزارش آزمایشگاه", "LabReport.txt", "Text Files (*.txt)")
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("=== گزارش سایبری آزمایشگاه شیمی‌لَب ===\n")
                    f.write(f"تاریخ و زمان: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"شیمیدان: {self.engine.player_name} (سطح {self.engine.level})\n")
                    f.write("-" * 40 + "\n\n")
                    f.write("🧪 وضعیت فعلی ظرف:\n")
                    f.write(f"نام ظرف: {self.engine.flask_label}\n")
                    f.write(f"دما: {self.engine.temp_c:.1f} °C\n")
                    f.write(f"میزان pH: {self.engine.get_ph():.2f}\n")
                    f.write(f"فرمول تجربی مخلوط: {self.engine.get_mixture_empirical_formula()}\n")
                    f.write("\nمحتویات:\n")
                    for layer in self.engine.visual_layers:
                        f.write(f"- {layer['name']} ({layer['amount']:.1f} mL/g)\n")
                    f.write("\n" + "-" * 40 + "\n\n")
                    f.write("⏱️ لاگ زمانی:\n")
                    for log_item in self.engine.auto_log:
                        f.write(log_item + "\n")
                    f.write("\n" + "-" * 40 + "\n\n")
                    f.write("📝 یادداشت‌های ثبت شده:\n")
                    f.write(self.txt_notes.toPlainText())
                    f.write("\n\n" + "-" * 40 + "\n\n")
                    f.write("🏅 مدال‌ها:\n")
                    for badge in self.engine.badges:
                        icon, desc = BADGE_CATALOG.get(badge, ("🏅", ""))
                        f.write(f"{icon} {badge}: {desc}\n")
                    if not self.engine.badges:
                        f.write("—\n")
                    f.write("\n" + "-" * 40 + "\n\n")
                    f.write("🎯 مأموریت‌های تکمیل شده:\n")
                    for m in self.engine.missions:
                        if m['id'] in self.engine.completed_missions:
                            f.write(f"✅ {m['title']} (+{m['xp']} XP)\n")
                    if not self.engine.completed_missions:
                        f.write("—\n")
                    f.write("\n" + "-" * 40 + "\n\n")
                    f.write("🧪 واکنش‌های کشف شده:\n")
                    for disc in self.engine.discovered:
                        f.write(f"- {disc}\n")
                    if not self.engine.discovered:
                        f.write("—\n")
                QMessageBox.information(self, "موفق", "گزارش TXT با موفقیت ذخیره شد.")
            except Exception as e:
                QMessageBox.critical(self, "خطا", f"خطا در ذخیره گزارش:\n{str(e)}")

    def action_export_pdf(self):
        filename, _ = QFileDialog.getSaveFileName(self, "ذخیره گزارش PDF", "LabReport.pdf", "PDF Files (*.pdf)")
        if not filename:
            return
        try:
            pdf = QPdfWriter(filename)
            pdf.setPageSize(QPageSize(QPageSize.A4))
            pdf.setResolution(300)
            painter = QPainterGui(pdf)
            w = pdf.width()
            h = pdf.height()
            margin = 120
            y = margin

            def draw_rounded_box(x, y, bw, bh, fill=QColor(240, 245, 255), border=QColor(50, 90, 160)):
                painter.setPen(QPen(border, 3))
                painter.setBrush(fill)
                painter.drawRoundedRect(QRectF(x, y, bw, bh), 20, 20)

            def draw_section_title(text, y_pos):
                painter.setFont(QFont(FONT_NAME, 14, QFont.Bold))
                painter.setPen(QColor(20, 60, 120))
                painter.drawText(QRectF(margin, y_pos, w - 2 * margin, 80), Qt.AlignRight | Qt.AlignVCenter, text)
                return y_pos + 90

            def draw_line_text(text, y_pos, size=11, color=QColor(30, 30, 30)):
                painter.setFont(QFont(FONT_NAME, size))
                painter.setPen(color)
                painter.drawText(QRectF(margin + 30, y_pos, w - 2 * margin - 60, 70), Qt.AlignRight | Qt.AlignVCenter, text)
                return y_pos + 75

            # --- هدر ---
            draw_rounded_box(margin - 20, y, w - 2 * margin + 40, 280, QColor(30, 60, 120), QColor(20, 40, 90))
            painter.setFont(QFont(FONT_NAME, 22, QFont.Bold))
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(QRectF(margin, y + 40, w - 2 * margin, 100), Qt.AlignHCenter, "گزارش رسمی آزمایشگاه شیمی‌لَب")
            painter.setFont(QFont(FONT_NAME, 12))
            painter.drawText(QRectF(margin, y + 150, w - 2 * margin, 60), Qt.AlignHCenter,
                             f"شیمیدان: {self.engine.player_name}  |  سطح: {self.engine.level}")
            painter.drawText(QRectF(margin, y + 200, w - 2 * margin, 50), Qt.AlignHCenter,
                             datetime.now().strftime("%Y-%m-%d  %H:%M:%S"))
            y += 320

            # --- وضعیت ظرف ---
            box_h = 200 + max(1, len(self.engine.visual_layers)) * 70
            draw_rounded_box(margin - 10, y, w - 2 * margin + 20, box_h, QColor(245, 250, 255), QColor(80, 140, 200))
            y = draw_section_title("🧪 وضعیت فعلی ظرف", y + 20)
            y = draw_line_text(f"برچسب ظرف: {self.engine.flask_label}", y)
            y = draw_line_text(f"دما: {self.engine.temp_c:.1f} °C", y)
            y = draw_line_text(f"pH: {self.engine.get_ph():.2f}", y)
            y = draw_line_text(f"فرمول تجربی: {self.engine.get_mixture_empirical_formula()}", y)
            y = draw_line_text("محتویات:", y, 12, QColor(20, 80, 140))
            for layer in self.engine.visual_layers:
                y = draw_line_text(f"• {layer['name']}  —  {layer['amount']:.1f} واحد", y, 10)
            if not self.engine.visual_layers:
                y = draw_line_text("— خالی —", y, 10, QColor(120, 120, 120))
            y += 40

            # --- تصویر ظرف ---
            flask_img = self.container.grab().toImage()
            target_w = int(w * 0.45)
            target_h = int((target_w / max(1, flask_img.width())) * flask_img.height())
            if y + target_h + 100 > h - margin:
                pdf.newPage()
                y = margin
            draw_rounded_box((w - target_w) / 2 - 15, y, target_w + 30, target_h + 30, QColor(250, 250, 255), QColor(100, 150, 200))
            painter.drawImage(QRectF((w - target_w) / 2, y + 15, target_w, target_h), flask_img)
            y += target_h + 60

            # --- یادداشت‌ها ---
            notes = self.txt_notes.toPlainText().strip() or "—"
            notes_h = 180 + min(400, len(notes) // 2)
            if y + notes_h > h - margin:
                pdf.newPage()
                y = margin
            draw_rounded_box(margin - 10, y, w - 2 * margin + 20, notes_h, QColor(255, 252, 240), QColor(200, 150, 50))
            y = draw_section_title("📝 یادداشت‌های شیمیدان", y + 20)
            painter.setFont(QFont(FONT_NAME, 11))
            painter.setPen(QColor(40, 40, 40))
            painter.drawText(QRectF(margin + 30, y, w - 2 * margin - 60, notes_h - 120),
                             Qt.AlignRight | Qt.AlignTop | Qt.TextWordWrap, notes)
            y += notes_h - 40

            # --- مدال و مأموریت ---
            if y + 350 > h - margin:
                pdf.newPage()
                y = margin
            draw_rounded_box(margin - 10, y, w - 2 * margin + 20, 320, QColor(240, 255, 245), QColor(60, 150, 90))
            y = draw_section_title("🏅 مدال‌ها و مأموریت‌ها", y + 20)
            badges_text = "، ".join([f"{BADGE_CATALOG.get(b, ('🏅', ''))[0]} {b}" for b in self.engine.badges]) or "—"
            y = draw_line_text(f"مدال‌ها: {badges_text}", y, 10)
            missions_text = "، ".join(
                [m['title'] for m in self.engine.missions if m['id'] in self.engine.completed_missions]
            ) or "—"
            y = draw_line_text(f"مأموریت‌های تکمیل‌شده: {missions_text}", y, 10)
            y += 30

            # --- کشف‌ها ---
            if y + 250 > h - margin:
                pdf.newPage()
                y = margin
            draw_rounded_box(margin - 10, y, w - 2 * margin + 20, 220, QColor(245, 240, 255), QColor(120, 80, 180))
            y = draw_section_title("🏆 واکنش‌های کشف‌شده", y + 20)
            discs = "، ".join(sorted(self.engine.discovered)) or "—"
            y = draw_line_text(discs, y, 10)
            y += 40

            # --- پاورقی ---
            painter.setFont(QFont(FONT_NAME, 9))
            painter.setPen(QColor(120, 120, 120))
            painter.drawText(QRectF(margin, h - 100, w - 2 * margin, 50), Qt.AlignHCenter,
                             "شیمی‌لَب (Universe ChimiLab) — گزارش تولیدشده توسط نرم‌افزار")

            painter.end()
            QMessageBox.information(self, "موفق", "گزارش PDF با کادرهای مرتب با موفقیت ذخیره شد.")
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در ایجاد PDF:\n{str(e)}")

    def toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        self.setStyleSheet(APP_STYLE_DARK if self.is_dark_mode else APP_STYLE_LIGHT)
        bg = '#1e1e2e' if self.is_dark_mode else '#ffffff'
        fg = 'white' if self.is_dark_mode else 'black'
        self.ax1.set_facecolor(bg)
        self.ax1.tick_params(colors=fg)
        self.ax1.set_ylabel('pH', color=fg)
        self.ax2.set_facecolor(bg)
        self.ax2.tick_params(colors=fg)
        self.ax2.set_ylabel('Temp (°C)', color=fg)
        self.figure.set_facecolor('#11111b' if self.is_dark_mode else '#f0f0f5')
        self.canvas.draw()

    def toggle_tabs(self):
        self.tabs.setVisible(not self.tabs.isVisible())

    def set_speed(self, speed):
        self.engine.speed_multiplier = speed
        self._log(f"⏱️ سرعت زمان به x{speed} تغییر کرد.")

    def handle_reaction_result(self, disc):
        if not disc:
            return
        name, xp, status, has_pr, has_gas = disc
        if status == "new":
            self.timer.stop()
            self._log(f"✨ واکنش جدید کشف شد: {name}")
            self.container.trigger_reaction_animation(has_pr, has_gas)
            self.update_player_stats()
            self.update_discoveries_table()
            self.update_wiki_tab()
            QMessageBox.information(self, "کشف!", f"تبریک! شما واکنش جدیدی کشف کردید:\n{name}\nامتیاز کسب شده: {xp}")
            self.timer.start(50)

    def remove_item(self, layer_id):
        if self.engine.remove_layer(layer_id):
            self.update_contents_ui()
            self._log("یک لایه حذف شد.")
            self.update_auto_log_ui()

    def _log(self, msg, color=None):
        if color:
            self.txt_log.append(f"<span style='color:{color};'>{msg}</span>")
        else:
            self.txt_log.append(msg)

    def save_notes(self):
        self.engine.notes = self.txt_notes.toPlainText()
        self.engine.save_data()

    def get_state_color_text(self, formula):
        clean = re.sub(r"[\[\]\"']", "", str(formula)).strip()
        norm = normalize_key(clean)
        d = None
        if norm in CHEMILAB_DB:
            d = CHEMILAB_DB[norm]
        else:
            for k, v in CHEMILAB_DB.items():
                if norm == str(k).lower() or norm == normalize_key(v.get('formula', '')) or clean == str(v.get('name', '')):
                    d = v
                    break
        if not d:
            return clean
        ptype = get_persian_type(d.get('type', ''))
        return f"{d.get('name', clean)} <span style='color:{d.get('color', '#fff')};'>■</span> <small>({ptype})</small>"

    def populate_chemicals(self):
        self.combo_chem.clear()
        for k, v in sorted(CHEMILAB_DB.items(), key=lambda x: x[1]['name']):
            self.combo_chem.addItem(f"{v['name']} ({v['formula']})", k)

    def filter_chemicals(self, text):
        self.combo_chem.blockSignals(True)
        self.combo_chem.clear()
        t = text.lower()
        cat = self.combo_filter.currentText()
        eng_cat = {"اسید": "Acid", "باز": "Base", "نمک": "Salt", "گاز": "Gas", "جامد": "Solid", "مایع": "Liquid"}.get(cat,
                                                                                                                      "")
        for k, v in sorted(CHEMILAB_DB.items(), key=lambda x: x[1]['name']):
            if (t in v['name'].lower() or t in v['formula'].lower() or t in k.lower()) and (
                    not eng_cat or eng_cat in v['type']):
                self.combo_chem.addItem(f"{v['name']} ({v['formula']})", k)
        self.combo_chem.blockSignals(False)
        if self.combo_chem.count() > 0:
            self.combo_chem.setCurrentIndex(0)
            self.update_chem_details()

    def update_chem_details(self):
        k = self.combo_chem.currentData()
        if k and k in CHEMILAB_DB:
            d = CHEMILAB_DB[k]
            self.lbl_d_name.setText(d.get('name', ''))
            self.lbl_d_form.setText(ChemicalCalculator.to_subscript(d.get('formula', '')))
            self.lbl_d_type.setText(get_persian_type(d.get('type', '')))
            self.spin_molarity.setValue(float(d.get('molarity', 0.1)))

    # ==================== حلقه اصلی بازی ====================
    def game_loop(self):
        try:
            if self.btn_titrate.isChecked() and self.engine.speed_multiplier > 0:
                if self.engine.is_broken:
                    self.btn_titrate.setChecked(False)
                    self.action_toggle_titration()
                else:
                    k = self.combo_chem.currentData()
                    if k:
                        amt = self.spin_drop_rate.value() * 0.1 * self.engine.speed_multiplier
                        msg, overflow, warnings = self.engine.add_chemical(k, amt, self.spin_molarity.value())
                        self.engine.titration_volume += amt
                        for w in warnings:
                            if w not in self.txt_log.toPlainText():
                                self._log(f"<span style='color:#f38ba8;'>{w}</span>")
                        if overflow:
                            self.container.trigger_overflow()
                        if int(self.engine.titration_volume * 10) % 20 == 0:
                            self.update_contents_ui()

            self.engine.update_physics()
            if self.engine.is_broken and "ظرف شکسته" not in self.txt_log.toPlainText():
                self._log("💥 دما بیش از حد بالا رفت و ظرف ترکید! سریعاً آن را تعویض کنید.")

            if not hasattr(self, 'st'):
                self.st = time.time()
            t = time.time() - self.st
            ph = self.engine.get_ph()
            temp = self.engine.temp_c

            if self.btn_titrate.isChecked() and (self.last_ph < 6 and ph > 8 or self.last_ph > 8 and ph < 6):
                self._log("✅ نقطه هم‌ارزی تیتراسیون فرا رسید! (هوش مصنوعی)")
                self.btn_titrate.setChecked(False)
                self.action_toggle_titration()
                self.engine.stats["successful_titrations"] += 1
            self.last_ph = ph

            self.lbl_ph_display.setText(f"pH: {ph:.2f}" if not self.engine.is_broken else "pH: ---")
            self.lbl_temp_display.setText(f"{temp:.1f} °C")

            achv = self.engine.check_missions_and_badges()
            if achv:
                self.update_missions_ui()
                self.update_player_stats()
                t_str = "دستاورد جدید!" if achv.get('type') == 'badge' else "مأموریت تکمیل شد!"
                QMessageBox.information(self, t_str, f"شما '{achv['title']}' را کسب کردید!")

            disc = self.engine.check_reactions()
            self.handle_reaction_result(disc)

            if int(t) % 2 == 0:
                self.update_report_card()

            if self.engine.speed_multiplier > 0:
                self.data_time.append(t)
                self.data_ph.append(ph)
                self.data_temp.append(temp)
                if len(self.data_time) > 100:
                    self.data_time.pop(0)
                    self.data_ph.pop(0)
                    self.data_temp.pop(0)
                self.line_ph.set_data(self.data_time, self.data_ph)
                self.line_temp.set_data(self.data_time, self.data_temp)
                if self.data_time:
                    self.ax1.set_xlim(min(self.data_time), max(self.data_time) + 1)
                    self.ax1.set_ylim(0, 14)
                    self.ax2.set_xlim(min(self.data_time), max(self.data_time) + 1)
                    self.ax2.set_ylim(min(self.data_temp) - 5, max(self.data_temp) + 5)
                self.canvas.draw()
        except Exception as e:
            # جلوگیری از کرش برنامه
            pass


if __name__ == '__main__':
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    app.setLayoutDirection(Qt.RightToLeft)
    app.setFont(QFont(FONT_NAME, 10))
    app.setStyleSheet(APP_STYLE_DARK)
    w = ModernLabWindow()
    w.show()
    sys.exit(app.exec())
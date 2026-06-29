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
        QSizePolicy, QMenu, QInputDialog
    )
    from PyQt5.QtCore import Qt, QTimer, QRectF, QPropertyAnimation, pyqtProperty, QEasingCurve, QPointF
    from PyQt5.QtGui import QFont, QColor, QPainter, QPen, QLinearGradient, QPainterPath, QBrush, QRadialGradient, \
        QPixmap, QPdfWriter, QPageSize
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
    36: ("کریپتون", "Kr", "نافلز (گاز نجیب)", "گاز", 48, [])
}

# تکمیل دیتابیس تا ۱۱۸ عنصر
ELEMENTS_EXT = [
    (37, "روبیدیوم", "Rb", "فلز قلیایی", "جامد", 48), (38, "استرانسیوم", "Sr", "فلز قلیایی خاکی", "جامد", 50),
    (39, "ایتریوم", "Y", "فلز واسطه", "جامد", 50), (40, "زیرکونیوم", "Zr", "فلز واسطه", "جامد", 51),
    (41, "نیوبیوم", "Nb", "فلز واسطه", "جامد", 52), (42, "مولیبدن", "Mo", "فلز واسطه", "جامد", 54),
    (43, "تکنسیم", "Tc", "فلز واسطه", "جامد", 55), (44, "روتنیم", "Ru", "فلز واسطه", "جامد", 57),
    (45, "رودیوم", "Rh", "فلز واسطه", "جامد", 58), (46, "پالادیوم", "Pd", "فلز واسطه", "جامد", 60),
    (47, "نقره", "Ag", "فلز واسطه", "جامد", 61), (48, "کادمیوم", "Cd", "فلز واسطه", "جامد", 64),
    (49, "ایندیوم", "In", "فلز واسطه ضعیف", "جامد", 66), (50, "قلع", "Sn", "فلز واسطه ضعیف", "جامد", 69),
    (51, "آنتیموان", "Sb", "شبه‌فلز", "جامد", 71), (52, "تلوریوم", "Te", "شبه‌فلز", "جامد", 76),
    (53, "ید", "I", "هالوژن", "جامد", 74), (54, "زنون", "Xe", "گاز نجیب", "گاز", 77),
    (55, "سزیم", "Cs", "فلز قلیایی", "جامد", 78), (56, "باریوم", "Ba", "فلز قلیایی خاکی", "جامد", 81),
    (57, "لانتان", "La", "لانتانید", "جامد", 82), (58, "سریوم", "Ce", "لانتانید", "جامد", 82),
    (59, "پرازئودیمیم", "Pr", "لانتانید", "جامد", 82), (60, "نئودیمیم", "Nd", "لانتانید", "جامد", 84),
    (61, "پرومتیم", "Pm", "لانتانید", "جامد", 84), (62, "ساماریم", "Sm", "لانتانید", "جامد", 88),
    (63, "اروپیم", "Eu", "لانتانید", "جامد", 89), (64, "گادولینیم", "Gd", "لانتانید", "جامد", 93),
    (65, "تربیم", "Tb", "لانتانید", "جامد", 94), (66, "دیسپروزیم", "Dy", "لانتانید", "جامد", 97),
    (67, "هولمیم", "Ho", "لانتانید", "جامد", 98), (68, "اربیم", "Er", "لانتانید", "جامد", 99),
    (69, "تولیم", "Tm", "لانتانید", "جامد", 100), (70, "ایتربیم", "Yb", "لانتانید", "جامد", 103),
    (71, "لوتتیم", "Lu", "لانتانید", "جامد", 104), (72, "هافنیم", "Hf", "فلز واسطه", "جامد", 106),
    (73, "تانتال", "Ta", "فلز واسطه", "جامد", 108), (74, "تنگستن", "W", "فلز واسطه", "جامد", 110),
    (75, "رنیوم", "Re", "فلز واسطه", "جامد", 111), (76, "اسمیم", "Os", "فلز واسطه", "جامد", 114),
    (77, "ایریدیم", "Ir", "فلز واسطه", "جامد", 115), (78, "پلاتین", "Pt", "فلز واسطه", "جامد", 117),
    (79, "طلا", "Au", "فلز واسطه", "جامد", 118), (80, "جیوه", "Hg", "فلز واسطه", "مایع", 121),
    (81, "تالیم", "Tl", "فلز واسطه ضعیف", "جامد", 123), (82, "سرب", "Pb", "فلز واسطه ضعیف", "جامد", 125),
    (83, "بیسموت", "Bi", "فلز واسطه ضعیف", "جامد", 126), (84, "پولونیم", "Po", "شبه‌فلز", "جامد", 125),
    (85, "استاتین", "At", "هالوژن", "جامد", 125), (86, "رادون", "Rn", "گاز نجیب", "گاز", 136),
    (87, "فرانسیم", "Fr", "فلز قلیایی", "جامد", 136), (88, "رادیوم", "Ra", "فلز قلیایی خاکی", "جامد", 138),
    (89, "اکتینیم", "Ac", "آکتینید", "جامد", 138), (90, "توریم", "Th", "آکتینید", "جامد", 142),
    (91, "پروتاکتینیم", "Pa", "آکتینید", "جامد", 140), (92, "اورانیوم", "U", "آکتینید", "جامد", 146),
    (93, "نپتونیوم", "Np", "آکتینید", "جامد", 144), (94, "پلوتونیوم", "Pu", "آکتینید", "جامد", 150),
    (95, "امریسیم", "Am", "آکتینید", "جامد", 148), (96, "کوریم", "Cm", "آکتینید", "جامد", 151),
    (97, "برکلیم", "Bk", "آکتینید", "جامد", 150), (98, "کالیفرنیم", "Cf", "آکتینید", "جامد", 153),
    (99, "اینشتینیم", "Es", "آکتینید", "جامد", 153), (100, "فرمیم", "Fm", "آکتینید", "جامد", 157),
    (101, "مندلیفیم", "Md", "آکتینید", "جامد", 157), (102, "نوبلیم", "No", "آکتینید", "جامد", 157),
    (103, "لورنسیم", "Lr", "آکتینید", "جامد", 159), (104, "رادرفوردیم", "Rf", "فلز واسطه", "جامد", 163),
    (105, "دوبنیم", "Db", "فلز واسطه", "جامد", 163), (106, "سیبورگیم", "Sg", "فلز واسطه", "جامد", 165),
    (107, "بوریم", "Bh", "فلز واسطه", "جامد", 165), (108, "هاسیم", "Hs", "فلز واسطه", "جامد", 169),
    (109, "مایتنریم", "Mt", "فلز واسطه", "جامد", 169), (110, "دارمشتادیم", "Ds", "فلز واسطه", "جامد", 171),
    (111, "رونتگنیم", "Rg", "فلز واسطه", "جامد", 171), (112, "کوپرنیسیم", "Cn", "فلز واسطه", "جامد", 173),
    (113, "نیهونیم", "Nh", "فلز واسطه ضعیف", "جامد", 173), (114, "فلروویم", "Fl", "فلز واسطه ضعیف", "جامد", 175),
    (115, "موسکوویم", "Mc", "فلز واسطه ضعیف", "جامد", 173), (116, "لیورموریم", "Lv", "فلز واسطه ضعیف", "جامد", 177),
    (117, "تنسین", "Ts", "هالوژن", "جامد", 177), (118, "اوگانسون", "Og", "گاز نجیب", "گاز", 176)
]
for item in ELEMENTS_EXT:
    ATOMIC_DB[item[0]] = (item[1], item[2], item[3], item[4], item[5], [])


def get_save_path():
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.abspath(".")
    return os.path.join(base_dir, "lab_save.json")


def get_db_path():
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.abspath(".")
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
"""

TYPE_MAP = {
    "Strong Acid": "مایع (اسید قوی)", "Weak Acid": "مایع (اسید ضعیف)", "Strong Base": "مایع (باز قوی)",
    "Weak Base": "مایع (باز ضعیف)", "Acid": "مایع (اسید)", "Base": "مایع (باز)", "Superacid": "ابر اسید",
    "Gas": "گاز", "Liquid": "مایع", "Solid": "جامد", "Metal": "جامد (فلز)", "Oxide": "جامد (اکسید)",
    "Salt": "جامد (نمک)", "Element": "جامد (عنصر)", "Halogen": "هالوژن", "Organic Compound": "ترکیب آلی",
    "Solvent": "مایع (حلال)", "Catalyst": "کاتالیزور", "Precipitate": "جامد (رسوب)"
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
        if not atom_moles_counter: return "ماده‌ای وجود ندارد"
        filtered_atoms = {k: v for k, v in atom_moles_counter.items() if v > 1e-9}
        if not filtered_atoms: return "-"
        min_mole = min(filtered_atoms.values())
        if min_mole < 1e-12: return "ناچیز"
        ratios = {k: v / min_mole for k, v in filtered_atoms.items()}
        best_multiplier = 1
        best_error = float('inf')
        for m in range(1, 21):
            current_error = sum(abs(r * m - round(r * m)) for r in ratios.values())
            if current_error < best_error:
                best_error = current_error
                best_multiplier = m
            if current_error < 0.1: break
        sorted_elements = []
        keys = list(filtered_atoms.keys())
        if 'C' in keys: sorted_elements.append('C'); keys.remove('C')
        if 'H' in keys: sorted_elements.append('H'); keys.remove('H')
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
        if rem <= 0: break
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
            if count == 0: continue
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
            glRotatef(self.angle_y * 0.2, 0.0, 1.0, 0.0)  # Slow overall rotation

            # Draw nucleus
            glColor3f(1.0, 0.7, 0.3)
            gluSphere(self.quadric, 0.5, 32, 32)

            # Draw shells and electrons
            active_shells = sum(1 for s in self.shells if s > 0)
            if active_shells == 0: return

            radius_step = 0.8
            for i in range(7):
                count = self.shells[i]
                if count == 0: continue
                r = 0.8 + (i * radius_step)

                # Draw orbit ring (simplified as a torus or circle, here using line loop for speed)
                glDisable(GL_LIGHTING)
                glColor3f(0.3, 0.3, 0.4)
                glBegin(GL_LINE_LOOP)
                for a in range(0, 360, 5):
                    rad = math.radians(a)
                    glVertex3f(math.cos(rad) * r, 0, math.sin(rad) * r)
                glEnd()
                glEnable(GL_LIGHTING)

                # Draw electrons
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

        # انتخاب بین 2D و 3D (در صورت وجود PyOpenGL)
        if HAS_OPENGL:
            self.canvas = GLBohrCanvas()
            lbl_3d_hint = QLabel("💡 با ماوس مدل سه بعدی را بچرخانید.")
            lbl_3d_hint.setStyleSheet("color: #a6e3a1; font-size: 11px; border:none;")
            lbl_3d_hint.setAlignment(Qt.AlignCenter)
            v_left.addWidget(lbl_3d_hint)
        else:
            self.canvas = BohrCanvas()
            lbl_no_gl = QLabel("⚠️ برای مدل سه‌بعدی کتابخانه PyOpenGL را نصب کنید.")
            lbl_no_gl.setStyleSheet("color: #f38ba8; font-size: 11px; border:none;")
            lbl_no_gl.setAlignment(Qt.AlignCenter)
            v_left.addWidget(lbl_no_gl)

        v_left.addWidget(self.canvas, 1)

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

        self.lbl_e_total = QLabel("📀 الکترون‌ها: 0")
        self.lbl_e_total.setStyleSheet("color: #f9e2af; font-size: 16px; font-weight:bold; border:none; padding: 5px;")
        self.lbl_e_total.setAlignment(Qt.AlignCenter)
        v_left.addLayout(h_btn)
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
            if rem <= 0: break
            fill = min(rem, cap)
            parts.append(f"{orb}{ChemicalCalculator.to_superscript(fill)}")
            rem -= fill
        return " ".join(parts) if parts else "—"

    def get_group_period_valence(self):
        shells = self.canvas.shells
        last_layer = -1
        for i in range(7):
            if shells[i] > 0: last_layer = i
        if last_layer == -1: return "—", "—", 0
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


# ----------------- کلاس‌های شبیه‌ساز آزمایشگاه -----------------
class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ورود به سیستم مرکزی")
        self.setFixedSize(400, 250)
        self.setStyleSheet("""
            QDialog { background-color: #0f0f17; border: 2px solid #89b4fa; border-radius: 10px; }
            QLabel { color: white; font-size: 14px; }
            QLineEdit { padding: 8px; border-radius: 5px; border: 1px solid #45475a; background: #1e1e2e; color: #a6e3a1; font-size: 14px; }
            QPushButton { background-color: #cba6f7; color: #11111b; padding: 10px; border-radius: 5px; font-weight: bold; font-size: 14px; }
            QPushButton:hover { background-color: #b4befe; }
        """)
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)
        title = QLabel("🧪 آزمایشگاه شیمی‌لَب V42 Pro")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #89dceb; margin-bottom: 10px;")
        layout.addWidget(title)
        lbl = QLabel("احراز هویت شیمیدان:")
        layout.addWidget(lbl)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("نام خود را وارد کنید...")
        layout.addWidget(self.name_input)
        btn = QPushButton("اتصال به سرور آزمایشگاه")
        btn.clicked.connect(self.check_input)
        layout.addWidget(btn)

    def check_input(self):
        if self.name_input.text().strip():
            self.accept()
        else:
            self.name_input.setPlaceholderText("⚠️ لطفاً نام معتبر وارد کنید!")
            self.name_input.setStyleSheet("border: 1px solid #f38ba8;")

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

        # امکانات جدید مدیریت پیشرفته
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

        # لیست مأموریت‌های آفلاین
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
        if len(self.auto_log) > 500:  # جلوگیری از پر شدن بیش از حد حافظه
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
        self.score = d.get("score", 0);
        self.level = d.get("level", 1);
        self.player_name = d.get("player_name", "دانشجو")
        self.discovered = set(d.get("discovered", []));
        self.badges = set(d.get("badges", []))
        self.completed_missions = set(d.get("completed_missions", []));
        self.notes = d.get("notes", "")
        self.total_volume = d.get("total_volume", 0.0);
        self.moles_h = d.get("moles_h", 0.0)
        self.moles_oh = d.get("moles_oh", 0.0);
        self.temp_c = d.get("temp_c", 25.0)
        self.contents = d.get("contents", {});
        self.visual_layers = d.get("visual_layers", [])
        self.is_broken = d.get("is_broken", False);
        self.titration_volume = d.get("titration_volume", 0.0)
        self.flask_label = d.get("flask_label", "بشر شماره ۱")
        if "stats" in d: self.stats.update(d["stats"])
        if self.visual_layers: self.layer_id_counter = max([l.get('id', 0) for l in self.visual_layers]) + 1
        self.save_data()
        self.add_to_log("وضعیت آزمایش از فایل بارگذاری شد.")

    def filter_solids(self):
        if self.is_broken: return []
        removed = []
        new_layers = []
        for layer in self.visual_layers:
            ctype = CHEMILAB_DB.get(layer['key'], {}).get('type', '')
            if any(x in ctype for x in ["Solid", "Metal", "Salt", "Powder", "Precipitate", "Alloy", "Mineral"]):
                removed.append(layer['name'])
                self.total_volume -= layer['amount']
                if layer['key'] in self.contents: del self.contents[layer['key']]
            else:
                new_layers.append(layer)
        self.visual_layers = new_layers
        if self.total_volume < 0: self.total_volume = 0
        if removed:
            self.stats["filter_uses"] += 1
            self.add_to_log(f"مواد جامد فیلتر شدند: {','.join(removed)}")
        return removed

    def spill_cleanup(self):
        if self.total_volume > self.max_capacity:
            amount_to_remove = self.total_volume - self.max_capacity
            ratio = self.max_capacity / self.total_volume
            self.total_volume = self.max_capacity
            for l in self.visual_layers: l['amount'] *= ratio; l['moles'] *= ratio
            for k in self.contents: self.contents[k] *= ratio
            self.moles_h *= ratio
            self.moles_oh *= ratio
            self.add_to_log(f"میز تمیز شد و {amount_to_remove:.1f} واحد ماده هدر رفت.")
            return True
        return False

    def add_chemical(self, key, amount, custom_molarity=None):
        warnings = []
        if self.is_broken: return "❌ ظرف شکسته است! ابتدا آن را بشویید.", False, warnings
        key = key.lower()
        if key not in CHEMILAB_DB: return "خطا: ماده یافت نشد", False, warnings

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
        if custom_molarity is not None: molarity = custom_molarity

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
            'moles': added_moles
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
                key = layer['key'];
                moles = layer['moles'];
                amount = layer['amount']
                if key in self.contents:
                    self.contents[key] -= moles
                    if self.contents[key] <= 0: del self.contents[key]
                self.total_volume -= amount
                self.visual_layers.pop(i)
                self.add_to_log(f"ماده حذف شد: {layer['name']}")
                return True
        return False

    def change_temperature(self, delta):
        self.temp_c += delta
        self.add_to_log(f"تغییر دما توسط کاربر (دلتا: {delta})")

    def update_physics(self):
        current_time = time.time()
        dt_real = current_time - self.last_update
        self.last_update = current_time
        dt = dt_real * self.speed_multiplier

        self.stats["total_play_time"] += dt_real

        if self.speed_multiplier == 0: return

        if self.is_broken:
            diff = self.temp_c - 25.0
            self.temp_c -= diff * 0.1 * dt
            return

        room_temp = 25.0
        cooling_rate = 0.05
        diff = self.temp_c - room_temp
        if abs(diff) > 0.1: self.temp_c -= diff * cooling_rate * dt

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
                            if l['key'] in self.contents: self.contents[l['key']] *= ratio
                    self.visual_layers = [l for l in self.visual_layers if l['amount'] > 0.1]

        if self.temp_c > 500.0 and not self.is_broken:
            self.is_broken = True
            self.stats["flask_breaks"] += 1
            self.add_to_log("💥 ظرف به دلیل دمای بسیار بالا منفجر شد!")
            self.total_volume = 0
            self.visual_layers = []
            self.contents = {}
            self.moles_h = 0
            self.moles_oh = 0

    def check_reactions(self):
        if self.is_broken: return None
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
                        if self.score >= self.level * 100: self.level += 1
                        self.save_data()
                        self.temp_c += 15.0
                        self.add_to_log(f"واکنش جدید کشف شد: {name}")
                        return (name, rxn["xp"], "new", has_precipitate, has_gas)
                    else:
                        found_old = (name, 0, "old", has_precipitate, has_gas)
        return found_old

    def check_missions_and_badges(self):
        new_missions = []
        if len(self.contents) >= 2 and "m1" not in self.completed_missions: new_missions.append("m1")
        if self.get_ph() < 2 and "m2" not in self.completed_missions: new_missions.append("m2")
        if self.get_ph() > 12 and "m3" not in self.completed_missions: new_missions.append("m3")
        if self.temp_c > 100 and "m4" not in self.completed_missions: new_missions.append("m4")
        if 6.5 <= self.get_ph() <= 7.5 and self.total_volume > 100 and self.moles_h > 0.01 and "m5" not in self.completed_missions: new_missions.append(
            "m5")
        if self.is_broken and "m6" not in self.completed_missions: new_missions.append("m6")
        if self.titration_volume >= 50 and "m7" not in self.completed_missions: new_missions.append("m7")

        for m_id in new_missions:
            self.completed_missions.add(m_id)
            mission = next((m for m in self.missions if m['id'] == m_id), None)
            if mission:
                self.score += mission['xp']
                if self.score >= self.level * 100: self.level += 1
                self.save_data()
                self.add_to_log(f"ماموریت تکمیل شد: {mission['title']}")
                return mission

        # چک مدال ها
        if self.temp_c >= 200 and "داغی ۲۰۰ درجه" not in self.badges:
            self.badges.add("داغی ۲۰۰ درجه");
            self.save_data();
            self.add_to_log("مدال جدید: داغی ۲۰۰ درجه")
            return {"type": "badge", "title": "داغی ۲۰۰ درجه"}
        if len(self.discovered) >= 1 and "اولین واکنش" not in self.badges:
            self.badges.add("اولین واکنش");
            self.save_data();
            self.add_to_log("مدال جدید: اولین واکنش")
            return {"type": "badge", "title": "اولین واکنش"}

        return None

    def get_ph(self):
        if self.total_volume == 0 or self.is_broken: return 7.0
        vol_l = self.total_volume / 1000.0 if self.total_volume > 0 else 1
        h = self.moles_h / vol_l
        oh = self.moles_oh / vol_l
        if abs(h - oh) < 1e-9: return 7.0
        if h > oh:
            return max(0, min(14, -math.log10(h - oh + 1e-14)))
        else:
            return max(0, min(14, 14 + math.log10(oh - h + 1e-14)))

    def get_mixture_empirical_formula(self):
        if self.is_broken: return "-"
        total_atoms = Counter()
        for key, moles in self.contents.items():
            if moles <= 1e-9: continue
            if key in CHEMILAB_DB:
                form = CHEMILAB_DB[key]["formula"]
                atoms_in_molecule = ChemicalCalculator.parse_formula(form)
                for atom, count in atoms_in_molecule.items():
                    total_atoms[atom] += count * moles
        return ChemicalCalculator.calculate_empirical_from_moles(total_atoms)


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

        # برای منوی کلیک راست روی ظرف
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
        if state != "off": QTimer.singleShot(4000, lambda: self.set_plate_state("off"))

    def set_stirrer(self, state):
        self.stirrer_on = state

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
        if self.engine.is_broken and not self.is_exploding: self.trigger_explosion()
        if not self.engine.is_broken: self.is_exploding = False

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
            if self.stirrer_angle >= 360: self.stirrer_angle -= 360

        total_amount = self.engine.total_volume
        h = self.height()
        margin_x, margin_y = 100, 30
        container_h = h - 2 * margin_y - 30

        if dt_mult > 0:
            for p in self.particles[:]:
                p['x'] += p['vx'] * dt_mult
                p['y'] -= p['vy'] * dt_mult
                p['life'] -= 1 * dt_mult
                if p['life'] <= 0: self.particles.remove(p)

            for sp in self.steam_particles[:]:
                sp['y'] -= sp['vy'] * dt_mult
                sp['x'] += math.sin(sp['life'] * 0.1) * 2
                sp['life'] -= 1 * dt_mult
                if sp['life'] <= 0: self.steam_particles.remove(sp)

            for op in self.overflow_particles[:]:
                op['y'] += op['vy'] * dt_mult
                op['life'] -= 1 * dt_mult
                if op['life'] <= 0: self.overflow_particles.remove(op)

            for sh in self.shards[:]:
                sh['x'] += sh['vx'] * dt_mult
                sh['y'] += sh['vy'] * dt_mult
                sh['vy'] += 0.8 * dt_mult  # gravity
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
            if any(x in t for x in ["جامد", "فلز", "رسوب", "پودر", "آلیاژ"]): return 10
            if "گاز" in t: return 0.1
            return 1.0

        for layer in sorted(self.engine.visual_layers, key=layer_density, reverse=True):
            top_y = current_y - (layer['amount'] * scale)
            if top_y <= y_pos <= current_y and margin_x <= event.x() <= w - margin_x:
                hovered_layer = layer
                break
            current_y = top_y

        if hovered_layer:
            QToolTip.showText(event.globalPos(),
                              f"{hovered_layer['name']}\n{hovered_layer['amount']:.1f} mL/g\n{hovered_layer['type']}",
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
                    if layer_h <= 0: continue
                    if current_y - layer_h < container_rect.top(): layer_h = current_y - container_rect.top()
                    rect = QRectF(container_rect.left(), current_y - layer_h, container_rect.width(), layer_h)
                    painter.setPen(Qt.NoPen)
                    c = QColor(layer['color'])
                    grad = QLinearGradient(rect.topLeft(), rect.topRight())
                    grad.setColorAt(0, c.darker(150))
                    grad.setColorAt(0.5, c)
                    grad.setColorAt(1, c.darker(150))
                    painter.setBrush(grad)
                    painter.drawRect(rect)
                    current_y -= layer_h

            painter.setPen(Qt.NoPen)
            for b in self.bubbles:
                painter.setBrush(QColor(255, 255, 255, 120))
                painter.drawEllipse(QRectF(b['x'], b['y'], b['size'], b['size']))

            if total_amount > 0 and self.engine.visual_layers:
                painter.save()
                painter.translate(container_rect.center().x(), container_rect.bottom() - 5)
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

            # رسم برچسب ظرف
            painter.save()
            font = painter.font()
            font.setPointSize(12)
            font.setBold(True)
            painter.setFont(font)
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(container_rect.adjusted(0, 10, 0, 0), Qt.AlignTop | Qt.AlignHCenter,
                             self.engine.flask_label)
            painter.restore()

            if self.engine.temp_c < 0:
                frost_alpha = min(200, int(abs(self.engine.temp_c) * 5))
                painter.setPen(QPen(QColor(200, 240, 255, frost_alpha), 2))
                for i in range(15):
                    x = container_rect.left() + (i * container_rect.width() / 15)
                    painter.drawLine(int(x), int(container_rect.bottom()), int(x + random.uniform(-15, 15)),
                                     int(container_rect.bottom() - random.uniform(20, 100)))

            painter.setPen(QPen(QColor(255, 255, 255, 150), 1))
            font = painter.font()
            font.setPointSize(9)
            painter.setFont(font)
            for val in range(0, int(self.engine.max_capacity) + 1, 100):
                if val == 0: continue
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

        painter.setPen(QPen(QColor(200, 200, 200), 1))
        for i in range(0, max_t + 1, 100):
            y = ty + th - (th * ((i - min_t) / (max_t - min_t)))
            painter.drawLine(int(tx + tw), int(y), int(tx + tw + 5), int(y))
        painter.setPen(QColor(200, 200, 220))
        painter.drawText(int(tx - 5), int(ty - 10), "°C")

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


class ModernLabWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("آزمایشگاه شیمی پیشرفته - شیمی‌لَب (نسخه 42 Pro + اتم بور + PDF)")
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
        layout = QHBoxLayout(central)

        # پنل کنترل سمت راست/چپ
        panel_ctrl = QFrame()
        panel_ctrl.setFixedWidth(400)
        vbox = QVBoxLayout(panel_ctrl)

        gb_player = QGroupBox("پروفایل شیمیدان")
        v_player = QVBoxLayout()

        h_top_player = QHBoxLayout()
        self.lbl_welcome = QLabel(f"👤 شیمیدان: {self.engine.player_name}")
        self.lbl_welcome.setStyleSheet("color: #a6e3a1; font-size: 18px; font-weight: bold; margin-bottom: 5px;")
        btn_theme = QPushButton("🌓 تم")
        btn_theme.setFixedSize(60, 30)
        btn_theme.clicked.connect(self.toggle_theme)
        h_top_player.addWidget(self.lbl_welcome)
        h_top_player.addWidget(btn_theme)
        v_player.addLayout(h_top_player)

        h_save_load = QHBoxLayout()
        btn_save = QPushButton("💾 ذخیره")
        btn_save.clicked.connect(self.action_save_state_file)
        btn_load = QPushButton("📂 بارگذاری")
        btn_load.clicked.connect(self.action_load_state_file)
        h_save_load.addWidget(btn_save);
        h_save_load.addWidget(btn_load)
        v_player.addLayout(h_save_load)

        self.lbl_level = QLabel("سطح: 1")
        self.lbl_level.setStyleSheet("color: #fab387; font-size: 14px; font-weight: bold;")
        self.lbl_score = QLabel("امتیاز: 0")
        self.progress_xp = QProgressBar()
        self.progress_xp.setRange(0, 100)
        self.progress_xp.setValue(0)
        self.progress_xp.setStyleSheet("QProgressBar::chunk { background-color: #cba6f7; }")
        v_player.addWidget(self.lbl_level)
        v_player.addWidget(self.lbl_score)
        v_player.addWidget(QLabel("پیشرفت تا سطح بعدی:"))
        v_player.addWidget(self.progress_xp)
        gb_player.setLayout(v_player)
        vbox.addWidget(gb_player)

        gb_chem = QGroupBox("افزودن ماده به بشر")
        frm = QFormLayout()

        h_search = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍 جستجو (فارسی یا انگلیسی)...")
        self.search_box.setStyleSheet("font-size: 16px;")
        self.search_box.textChanged.connect(self.filter_chemicals)

        self.combo_filter = QComboBox()
        self.combo_filter.addItems(["همه", "اسید", "باز", "نمک", "گاز", "جامد", "مایع"])
        self.combo_filter.currentTextChanged.connect(lambda _: self.filter_chemicals(self.search_box.text()))
        h_search.addWidget(self.search_box);
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
        self.spin_molarity.setDecimals(2)

        h_vol_mol = QHBoxLayout()
        h_vol_mol.addWidget(QLabel("مقدار:"))
        h_vol_mol.addWidget(self.spin_vol)
        h_vol_mol.addWidget(QLabel("غلظت(M):"))
        h_vol_mol.addWidget(self.spin_molarity)

        h_btn_add = QHBoxLayout()
        btn_add = QPushButton("➕ افزودن یکباره")
        btn_add.clicked.connect(self.action_add)
        btn_add.setStyleSheet("background-color: #a6e3a1; color: #1e1e2e;")

        self.btn_titrate = QPushButton("💧 بورت هوشمند")
        self.btn_titrate.setCheckable(True)
        self.btn_titrate.clicked.connect(self.action_toggle_titration)
        self.btn_titrate.setStyleSheet("background-color: #89b4fa; color: #1e1e2e;")
        h_btn_add.addWidget(btn_add)
        h_btn_add.addWidget(self.btn_titrate)

        self.spin_drop_rate = QDoubleSpinBox()
        self.spin_drop_rate.setRange(0.1, 10.0);
        self.spin_drop_rate.setValue(1.0);
        self.spin_drop_rate.setPrefix("سرعت قطره: ")

        frm.addRow(h_search)
        frm.addRow("ماده:", self.combo_chem)
        frm.addRow(h_vol_mol)
        frm.addRow(self.spin_drop_rate)
        frm.addRow(h_btn_add)
        gb_chem.setLayout(frm)
        vbox.addWidget(gb_chem)

        gb_tools = QGroupBox("ابزارهای آزمایشگاه")
        v_tools = QVBoxLayout()
        h_temp = QHBoxLayout()
        btn_heat = QPushButton("🔥 حرارت")
        btn_heat.setStyleSheet("background-color: #f38ba8; color: #1e1e2e;")
        btn_heat.clicked.connect(self.action_heat)
        btn_cool = QPushButton("🧊 خنک‌کننده")
        btn_cool.setStyleSheet("background-color: #89b4fa; color: #1e1e2e;")
        btn_cool.clicked.connect(self.action_cool)
        h_temp.addWidget(btn_cool)
        h_temp.addWidget(btn_heat)
        v_tools.addLayout(h_temp)

        h_extra = QHBoxLayout()
        btn_filter = QPushButton("⚗️ فیلتر جامدات")
        btn_filter.setStyleSheet("background-color: #f9e2af; color: #1e1e2e;")
        btn_filter.clicked.connect(self.action_filter)

        self.btn_stirrer = QPushButton("🌪️ همزن مغناطیسی")
        self.btn_stirrer.setCheckable(True)
        self.btn_stirrer.clicked.connect(self.action_toggle_stirrer)
        self.btn_stirrer.setStyleSheet("background-color: #cba6f7; color: #1e1e2e;")

        h_extra.addWidget(btn_filter)
        h_extra.addWidget(self.btn_stirrer)
        v_tools.addLayout(h_extra)

        h_extra2 = QHBoxLayout()
        btn_photo = QPushButton("📸 عکس از ظرف")
        btn_photo.clicked.connect(self.action_screenshot)
        btn_wash = QPushButton("🚿 تعویض ظرف")
        btn_wash.setStyleSheet("background-color: #89dceb; color: #1e1e2e;")
        btn_wash.clicked.connect(self.action_wash)
        h_extra2.addWidget(btn_photo);
        h_extra2.addWidget(btn_wash)
        v_tools.addLayout(h_extra2)

        h_time = QHBoxLayout()
        btn_pause = QPushButton("⏸️ توقف")
        btn_normal = QPushButton("▶️ عادی")
        btn_fast = QPushButton("⏩ تند (x5)")
        btn_pause.clicked.connect(lambda: self.set_speed(0))
        btn_normal.clicked.connect(lambda: self.set_speed(1))
        btn_fast.clicked.connect(lambda: self.set_speed(5))
        h_time.addWidget(btn_pause)
        h_time.addWidget(btn_normal)
        h_time.addWidget(btn_fast)
        v_tools.addLayout(h_time)
        gb_tools.setLayout(v_tools)
        vbox.addWidget(gb_tools)

        self.gb_details = self.create_details_group()
        vbox.addWidget(self.gb_details)

        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        vbox.addWidget(QLabel("📜 سیستم گزارش زنده:"))
        vbox.addWidget(self.txt_log)

        btn_toggle_tabs = QPushButton("👁️ نمایش / مخفی‌کردن پنل اطلاعات")
        btn_toggle_tabs.setStyleSheet("background-color: #313244; color: #ffffff; font-weight: bold;")
        btn_toggle_tabs.clicked.connect(self.toggle_tabs)
        vbox.addWidget(btn_toggle_tabs)

        panel_vis = QFrame()
        panel_vis.setStyleSheet("background-color: #11111b; border-radius: 10px; border: 2px solid #313244;")
        v_vis = QVBoxLayout(panel_vis)
        title_vis = QLabel("ظرف واکنش هوشمند (1000 mL)")
        title_vis.setAlignment(Qt.AlignCenter)
        title_vis.setStyleSheet("font-size: 18px; color: #89dceb; font-weight: bold; padding: 10px;")
        v_vis.addWidget(title_vis)

        self.container = AnimatedContainer(self.engine)
        v_vis.addWidget(self.container, 1, Qt.AlignCenter)

        info_frame = QFrame()
        info_frame.setStyleSheet("background-color: #1e1e2e; border-radius: 8px; padding: 5px;")
        info_h = QHBoxLayout(info_frame)
        self.lbl_ph_display = QLabel("pH: 7.00")
        self.lbl_ph_display.setStyleSheet("font-size: 22px; color: #a6e3a1; font-weight: bold;")
        self.lbl_temp_display = QLabel("25.0 °C")
        self.lbl_temp_display.setStyleSheet("font-size: 22px; color: #f38ba8; font-weight: bold;")
        info_h.addWidget(self.lbl_ph_display)
        info_h.addStretch()
        info_h.addWidget(self.lbl_temp_display)
        v_vis.addWidget(info_frame)

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

        self.split = QSplitter(Qt.Horizontal)
        self.split.addWidget(panel_ctrl)
        self.split.addWidget(panel_vis)
        self.split.addWidget(self.tabs)
        self.split.setSizes([400, 450, 700])
        layout.addWidget(self.split)

    def toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        self.setStyleSheet(APP_STYLE_DARK if self.is_dark_mode else APP_STYLE_LIGHT)
        bg = '#1e1e2e' if self.is_dark_mode else '#ffffff'
        fg = 'white' if self.is_dark_mode else 'black'
        self.ax1.set_facecolor(bg);
        self.ax1.tick_params(colors=fg);
        self.ax1.set_ylabel('pH', color=fg)
        self.ax2.set_facecolor(bg);
        self.ax2.tick_params(colors=fg);
        self.ax2.set_ylabel('Temp (°C)', color=fg)
        self.figure.set_facecolor('#11111b' if self.is_dark_mode else '#f0f0f5')
        self.canvas.draw()

    def action_screenshot(self):
        path, _ = QFileDialog.getSaveFileName(self, "ذخیره عکس از ظرف", "ChimiLab_Snapshot.png", "Images (*.png)")
        if path:
            self.container.grab().save(path)
            self.txt_log.append("📸 تصویر ظرف با موفقیت ذخیره شد.")

    def action_save_state_file(self):
        path, _ = QFileDialog.getSaveFileName(self, "ذخیره وضعیت آزمایش", "lab_state.json", "JSON (*.json)")
        if path:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self.engine.to_dict(), f, ensure_ascii=False, indent=2)
            self.txt_log.append("💾 وضعیت آزمایش در فایل ذخیره شد.")

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
                self.txt_log.append("📂 وضعیت با موفقیت بارگذاری شد.")
            except Exception as e:
                QMessageBox.critical(self, "خطا", f"فایل نامعتبر است.\n{str(e)}")

    def set_speed(self, speed):
        self.engine.speed_multiplier = speed
        self.txt_log.append(f"⏱️ سرعت زمان به x{speed} تغییر کرد.")

    def action_heat(self):
        self.engine.change_temperature(15)
        self.container.set_plate_state("heat")
        self.txt_log.append("🔥 گرمایش فعال شد.")

    def action_cool(self):
        self.engine.change_temperature(-15)
        self.container.set_plate_state("cool")
        self.txt_log.append("🧊 سرمایش فعال شد.")

    def action_toggle_stirrer(self):
        is_on = self.btn_stirrer.isChecked()
        self.container.set_stirrer(is_on)
        self.txt_log.append(f"🌪️ همزن مغناطیسی {'روشن' if is_on else 'خاموش'} شد.")
        self.engine.add_to_log(f"همزن {'روشن' if is_on else 'خاموش'} شد.")

    def action_toggle_titration(self):
        if self.btn_titrate.isChecked():
            self.btn_titrate.setText("⏹️ توقف بورت")
            self.btn_titrate.setStyleSheet("background-color: #f38ba8; color: #1e1e2e;")
        else:
            self.btn_titrate.setText("💧 بورت هوشمند")
            self.btn_titrate.setStyleSheet("background-color: #89b4fa; color: #1e1e2e;")

    def action_filter(self):
        removed = self.engine.filter_solids()
        if removed:
            self.txt_log.append(f"⚗️ مواد جامد فیلتر شدند: {', '.join(removed)}")
            self.update_contents_ui()
        else:
            self.txt_log.append("⚗️ ماده جامدی برای فیلتر کردن وجود ندارد.")

    def toggle_tabs(self):
        if self.tabs.isVisible():
            self.tabs.hide()
        else:
            self.tabs.show()

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

    def update_report_card(self):
        if not hasattr(self, 'lbl_stats'): return
        s = self.engine.stats
        play_m, play_s = divmod(int(s['total_play_time']), 60)
        play_h, play_m = divmod(play_m, 60)
        time_str = f"{play_h} ساعت و {play_m} دقیقه و {play_s} ثانیه"

        grade = "A+"
        if s['flask_breaks'] > 5:
            grade = "C"
        elif s['flask_breaks'] > 2:
            grade = "B"
        if s['reactions_found'] > 10: grade = "A++"

        text = f"""
        <b>⏱️ زمان کل فعالیت:</b> {time_str}<br>
        <b>🧪 تعداد واکنش‌های کشف شده:</b> {s['reactions_found']}<br>
        <b>💥 دفعات شکستن ظرف (خطا):</b> {s['flask_breaks']}<br>
        <b>⚗️ استفاده از فیلتر:</b> {s['filter_uses']} بار<br>
        <b>🎯 تیتراسیون‌های موفق:</b> {s['successful_titrations']}<br><br>
        <hr><br>
        <b>نمره ارزیابی کلی سیستم: <span style='color:#f38ba8; font-size: 24px;'>{grade}</span></b>
        """
        self.lbl_stats.setText(text)

    def create_missions_badges_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)

        self.list_missions = QListWidget()
        self.list_badges = QListWidget()

        l.addWidget(QLabel("🎯 چالش‌های داخلی:"))
        l.addWidget(self.list_missions)
        l.addWidget(QLabel("🏅 مدال‌ها و دستاوردها:"))
        l.addWidget(self.list_badges)
        self.update_missions_ui()
        return w

    def update_missions_ui(self):
        self.list_missions.clear()
        for m in self.engine.missions:
            status = "✅" if m['id'] in self.engine.completed_missions else "❌"
            self.list_missions.addItem(f"{status} | {m['title']} (+{m['xp']} XP)\n   {m['desc']}")

        self.list_badges.clear()
        for b in self.engine.badges:
            self.list_badges.addItem(f"🏅 {b}")

    def create_notes_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        lbl_hint = QLabel("📝 دفترچه یادداشت و صدور گزارش (PDF):")
        lbl_hint.setStyleSheet("font-size: 16px; font-weight: bold; color: #cdd6f4;")
        l.addWidget(lbl_hint)

        self.txt_notes = QTextEdit()
        self.txt_notes.setStyleSheet(
            "QTextEdit { font-size: 16px; background-color: #1e1e2e; color: #cdd6f4; padding: 15px; border-radius: 8px; font-weight: 500; line-height: 1.8; border: 2px solid #89b4fa; }")
        self.txt_notes.setPlaceholderText("یادداشت‌های خود را بنویسید...")
        self.txt_notes.setText(self.engine.notes)
        self.txt_notes.textChanged.connect(self.save_notes)
        l.addWidget(self.txt_notes)

        lbl_log = QLabel("⏱️ لاگ زمانی خودکار:")
        lbl_log.setStyleSheet("font-weight: bold; margin-top: 10px;")
        l.addWidget(lbl_log)

        self.list_auto_log = QListWidget()
        self.list_auto_log.setStyleSheet("background-color: #11111b; font-family: monospace; font-size: 12px;")
        l.addWidget(self.list_auto_log)

        h_export = QHBoxLayout()
        btn_export_txt = QPushButton("📥 گزارش TXT")
        btn_export_txt.setStyleSheet("background-color: #a6e3a1; color: #1e1e2e; font-weight: bold;")
        btn_export_txt.clicked.connect(self.export_report_txt)

        btn_export_pdf = QPushButton("📑 خروجی حرفه‌ای PDF")
        btn_export_pdf.setStyleSheet("background-color: #fab387; color: #1e1e2e; font-weight: bold;")
        btn_export_pdf.clicked.connect(self.export_report_pdf)

        h_export.addWidget(btn_export_txt)
        h_export.addWidget(btn_export_pdf)
        l.addLayout(h_export)
        return w

    def export_report_txt(self):
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
                        f.write(f"- {layer['name']} ({layer['amount']} mL/g)\n")
                    f.write("\n" + "-" * 40 + "\n\n")
                    f.write("⏱️ لاگ زمانی:\n")
                    for log_item in self.engine.auto_log:
                        f.write(log_item + "\n")
                    f.write("\n" + "-" * 40 + "\n\n")
                    f.write("📝 یادداشت‌های ثبت شده:\n")
                    f.write(self.txt_notes.toPlainText())
                QMessageBox.information(self, "موفق", "گزارش TXT با موفقیت ذخیره شد.")
            except Exception as e:
                QMessageBox.critical(self, "خطا", f"خطا در ذخیره گزارش:\n{str(e)}")

    def export_report_pdf(self):
        filename, _ = QFileDialog.getSaveFileName(self, "ذخیره گزارش PDF", "LabReport.pdf", "PDF Files (*.pdf)")
        if not filename: return

        try:
            # استفاده از QPdfWriter بومی PyQt برای ایجاد PDF با پشتیبانی از فارسی
            pdf = QPdfWriter(filename)
            pdf.setPageSize(QPageSize(QPageSize.A4))
            pdf.setResolution(300)
            painter = QPainter(pdf)

            font_title = QFont(FONT_NAME, 24, QFont.Bold)
            font_text = QFont(FONT_NAME, 12)

            w = pdf.width()
            h = pdf.height()

            # رسم هدر
            painter.setFont(font_title)
            painter.setPen(QColor(0, 0, 100))
            painter.drawText(QRectF(0, 100, w, 500), Qt.AlignHCenter, "گزارش رسمی آزمایشگاه شیمی‌لَب")

            painter.setFont(font_text)
            painter.setPen(QColor(0, 0, 0))

            y = 800
            line_height = 150

            info = [
                f"شیمیدان: {self.engine.player_name} (سطح {self.engine.level})",
                f"تاریخ و زمان: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"برچسب ظرف: {self.engine.flask_label}",
                f"دما: {self.engine.temp_c:.1f} °C",
                f"میزان pH: {self.engine.get_ph():.2f}",
                f"فرمول تجربی: {self.engine.get_mixture_empirical_formula()}",
                "محتویات ظرف:"
            ]

            for line in info:
                painter.drawText(QRectF(100, y, w - 200, line_height), Qt.AlignRight, line)
                y += line_height

            for layer in self.engine.visual_layers:
                painter.drawText(QRectF(200, y, w - 300, line_height), Qt.AlignRight,
                                 f"- {layer['name']} ({layer['amount']:.1f} واحد)")
                y += line_height

            y += line_height
            painter.drawLine(100, y, w - 100, y)
            y += line_height

            # اضافه کردن عکس ظرف به PDF
            flask_img = self.container.grab().toImage()
            target_w = w // 2
            target_h = int((target_w / flask_img.width()) * flask_img.height())
            painter.drawImage(QRectF((w - target_w) / 2, y, target_w, target_h), flask_img)

            y += target_h + line_height
            painter.drawText(QRectF(100, y, w - 200, line_height), Qt.AlignRight, "یادداشت‌ها:")
            y += line_height

            # رسم یادداشت ها با شکست خط
            notes = self.txt_notes.toPlainText()
            painter.drawText(QRectF(100, y, w - 200, h - y), Qt.AlignRight | Qt.TextWordWrap, notes)

            painter.end()
            QMessageBox.information(self, "موفق", "گزارش PDF با موفقیت و فونت اصلی ذخیره شد.")
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در ایجاد PDF:\n{str(e)}")

    def save_notes(self):
        self.engine.notes = self.txt_notes.toPlainText()
        self.engine.save_data()

    def update_auto_log_ui(self):
        if hasattr(self, 'list_auto_log'):
            self.list_auto_log.clear()
            for log in self.engine.auto_log:
                self.list_auto_log.addItem(log)
            self.list_auto_log.scrollToBottom()

    def create_about_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)

        about_text = """بسم الله الرحمن الرحیم
                با سلام و احترام خدمت داوران گرامی
                پروژهٔ ما «شیمی‌لَب» نام دارد: یک شبیه‌ساز پیشرفتهٔ آزمایشگاه شیمی که برای حل ریشه‌ای مشکلات آموزش شیمی طراحی شده است.

                مشکلات موجود در آموزش شیمی کشور:
                ۱. ۶۵ درصد مدارس کشور اصلاً آزمایشگاه شیمی ندارند.
                ۲. راه‌اندازی یک آزمایشگاه واقعی و کامل هزینه‌ای بسیار بالا دارد و حتی برای مدارسی که آن را ایجاد می‌کنند، تعویض و جایگزینی تجهیزات و لوازم مصرفی بسیار پرهزینه و پرتکرار است.
                ۳. دانش‌آموزان مناطق محروم و روستایی تقریباً هرگز یک آزمایش واقعی شیمی را تجربه نکرده‌اند.
                ۴. هر ساله صدها حادثهٔ آتش‌سوزی و مسمومیت در آزمایشگاه‌های مدارس رخ می‌دهد که هم هزینه‌های سنگین بر مدرسه تحمیل می‌کند و هم گاهی به آسیب‌های مالی و جانی جبران‌ناپذیر می‌انجامد.
                ۵. نتیجهٔ مستقیم این کمبودها این است که میانگین نمرهٔ عملی شیمی دانش‌آموزان کنکور زیر ۳۰ درصد است.

                هدف پروژه:
                ما می‌خواهیم هر دانش‌آموز، در هر نقطه‌ای از کشور، بدون نیاز به اینترنت، بدون کوچک‌ترین خطر جانی و مالی، بدون هزینه‌های سنگین آزمایشگاه و بدون نیاز به تجهیزات واقعی، آزمایش‌های شیمی را شخصاً تجربه کند و مفاهیم را به صورت عملی و عمیق یاد بگیرد.

                جامعهٔ هدف:
                دانش‌آموزان (متوسطهٔ اول و دوم)، دانشجویان و همهٔ علاقه‌مندان به علم شیمی.

                ویژگی‌های اصلی (قلب نرم‌افزار):
                • رابط کاربری مدرن و زیبا با انیمیشن‌های روان که حس کار با یک آزمایشگاه واقعی را القا می‌کند.
                • شبیه‌سازی فیزیکی دما و رساندن تدریجی دمای ظرف به دمای محیط؛ یعنی اگر ماده‌ای گرم شود، به مرور با محیط به تعادل می‌رسد.
                • محاسبات بسیار دقیق با بهره‌گیری از کتابخانهٔ تخصصی شیمی (جرم مولکولی، مول و…) که نتیجه‌ی واکنش‌ها را واقعی نگه می‌دارد.
                • حالت Sandbox (آزمایش آزاد) – مهم‌ترین برگ برندهٔ ما. کاربر می‌تواند هر ماده‌ای را با هر مادهٔ دیگری به دلخواه ترکیب کند، دما را تغییر دهد و نتایج را ببیند؛ درست مثل یک زمین بازی علمی بی‌مرز.
                • سیستم بازیکن (Gamification) که با امتیازدهی و پیشروی مرحله‌ای، انگیزهٔ یادگیری را به شکل چشمگیری بالا می‌برد.
                • پایگاه دادهٔ SQLite که امکان ذخیره و مدیریت ۶۵۵ مادهٔ شیمیایی مختلف را به صورت کاملاً آفلاین فراهم می‌کند.
                • امکان مشاهدهٔ ویژگی‌های هر ماده (فرمول تجربی، چگالی، حالت فیزیکی و…) با یک کلیک.

                ویژگی‌های تکمیلی:
                • پشتیبانی از ۶۵۵ مادهٔ شیمیایی متنوع.
                • تغییر دمای ظرف در حین آزمایش (گرمایش و سرمایش).
                • مشاهدهٔ فرمول تجربی ترکیب‌های ساخته‌شده.
                • نمودارهای پویا و روان pH و دما برای تحلیل لحظه‌ای آزمایش.
                • (تأکید مجدد) حالت آزاد Sandbox که خلاقیت را به حداکثر می‌رساند.

                سازگاری و تست:
                نرم‌افزار با موفقیت روی ویندوز ۷، ۱۰ و ۱۱ آزمایش شده و بدون مشکل اجرا می‌شود.

                مزیت‌های رقابتی نسبت به نمونه‌های مشابه:
                ۱. زبان فارسی – بومی‌سازی کامل، متناسب با نیاز دانش‌آموز ایرانی.
                ۲. آفلاین بودن – بدون نیاز به اینترنت، مخصوص مناطق دورافتاده و محروم.
                ۳. حجم بسیار کم – نصب سریع و اجرا بر روی ضعیف‌ترین سیستم‌ها.
                ۴. حالت Sandbox که در کمتر نرم‌افزار آموزشی شیمی به این شکل دیده می‌شود.
                ۵. رویکرد بازی‌گونه که یادگیری را از یک تکلیف خسته‌کننده به یک چالش جذاب تبدیل می‌کند.

                با شیمی‌لَب، دیوار بی‌آزمایشگاهی در مدارس کشور فرو می‌ریزد و هر دانش‌آموز، صرف‌نظر از موقعیت جغرافیایی و وضعیت اقتصادی، فرصت درک عملی شیمی را پیدا می‌کند.
                سپاس‌گزارم از توجه شما.

                برای مشاهده نحوه استفاده از برنامه لطفا به سایت برناهم ما مراجعه کنید

                @example.com

                طراح و برنامه‌نویس: کیانوش فدائی (دانش‌آموز کلاس نهم، مدرسه شهید اسدالله زاده)"""
        lbl = QLabel(about_text)
        lbl.setWordWrap(True)
        lbl.setStyleSheet("font-size: 15px; line-height: 1.6; color: #000000; padding: 10px;")
        content_layout.addWidget(lbl)
        content_layout.addStretch()
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)
        return w

    def get_state_color_text(self, formula):
        clean_formula = re.sub(r"[\[\]\"']", "", str(formula)).strip()
        norm = normalize_key(clean_formula)
        d = None
        if norm in CHEMILAB_DB:
            d = CHEMILAB_DB[norm]
        else:
            for k, v in CHEMILAB_DB.items():
                if norm == str(k).lower() or norm == normalize_key(v.get('formula', '')) or clean_formula == str(
                        v.get('name', '')):
                    d = v;
                    break
        if not d: return clean_formula
        ptype = get_persian_type(d.get('type', ''))
        return f"{d.get('name', clean_formula)} <span style='color:{d.get('color', '#fff')};'>■</span> <small>({ptype})</small>"

    def create_wiki_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        self.table_wiki = QTableWidget()
        self.table_wiki.setColumnCount(5)
        self.table_wiki.setHorizontalHeaderLabels(["واکنش", "مواد", "محصولات", "دما", "XP"])
        self.table_wiki.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        l.addWidget(self.table_wiki)
        self.update_wiki_table()
        return w

    def update_wiki_table(self):
        disc = {k: v for k, v in CUSTOM_REACTIONS.items() if k in self.engine.discovered}
        self.table_wiki.setRowCount(len(disc))
        for i, (n, d) in enumerate(disc.items()):
            self.table_wiki.setItem(i, 0, QTableWidgetItem(n))
            reactants_list = d['reactants'] if isinstance(d['reactants'], list) else []
            products_list = d['products'] if isinstance(d['products'], list) else []
            lbl_r = QLabel(" + ".join([self.get_state_color_text(r) for r in reactants_list]))
            lbl_r.setWordWrap(True);
            lbl_r.setTextFormat(Qt.RichText)
            self.table_wiki.setCellWidget(i, 1, lbl_r)
            lbl_p = QLabel(" + ".join([self.get_state_color_text(p) for p in products_list]))
            lbl_p.setWordWrap(True);
            lbl_p.setTextFormat(Qt.RichText)
            self.table_wiki.setCellWidget(i, 2, lbl_p)
            self.table_wiki.setItem(i, 3, QTableWidgetItem(str(d.get('temp_min', '-'))))
            self.table_wiki.setItem(i, 4, QTableWidgetItem(str(d.get('xp', 0))))
        self.table_wiki.resizeRowsToContents()

    def create_discoveries_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        self.table_disc = QTableWidget()
        self.table_disc.setColumnCount(2)
        self.table_disc.setHorizontalHeaderLabels(["نام واکنش", "امتیاز"])
        self.table_disc.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        l.addWidget(self.table_disc)
        self.update_discoveries_table()
        return w

    def create_graph_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        self.figure = Figure(figsize=(5, 6), facecolor='#11111b')
        self.canvas = FigureCanvas(self.figure)
        self.ax1 = self.figure.add_subplot(211)
        self.ax1.set_facecolor('#1e1e2e');
        self.ax1.set_ylabel('pH', color='white');
        self.ax1.tick_params(colors='white')
        self.ax2 = self.figure.add_subplot(212)
        self.ax2.set_facecolor('#1e1e2e');
        self.ax2.set_ylabel('Temp (°C)', color='white');
        self.ax2.tick_params(colors='white')
        self.line_ph, = self.ax1.plot([], [], color='#a6e3a1', linewidth=2)
        self.line_temp, = self.ax2.plot([], [], color='#f38ba8', linewidth=2)
        l.addWidget(self.canvas)
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
        lbl_title = QLabel("فرمول تجربی مخلوط: ")
        lbl_title.setStyleSheet("color: #bac2de; font-weight: bold;")
        self.lbl_mix = QLabel("-")
        self.lbl_mix.setStyleSheet("font-size: 18px; font-weight: bold; color: #a6e3a1;")
        mix_layout.addWidget(lbl_title)
        mix_layout.addWidget(self.lbl_mix)
        mix_layout.addStretch()
        l.addWidget(mix_frame)
        return w

    def create_datasheet_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        t = QTableWidget()
        t.setColumnCount(7)
        t.setHorizontalHeaderLabels(["نام", "فرمول", "نوع", "رنگ", "مولاریته (M)", "pH", "دما"])
        t.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        t.setRowCount(len(CHEMILAB_DB))
        for i, (k, v) in enumerate(sorted(CHEMILAB_DB.items(), key=lambda x: x[1]['name'])):
            t.setItem(i, 0, QTableWidgetItem(v.get('name', '')))
            t.setItem(i, 1, QTableWidgetItem(ChemicalCalculator.to_subscript(v.get('formula', ''))))
            t.setItem(i, 2, QTableWidgetItem(get_persian_type(v.get('type', ''))))
            color_cell = QTableWidgetItem("")
            color_cell.setBackground(QColor(v.get('color', '#FFFFFF')))
            color_cell.setFlags(Qt.ItemIsEnabled)
            t.setItem(i, 3, color_cell)
            t.setItem(i, 4, QTableWidgetItem(str(v.get('molarity', '-'))))
            t.setItem(i, 5, QTableWidgetItem(str(v.get('pH', '-'))))
            t.setItem(i, 6, QTableWidgetItem(str(v.get('heat', '-'))))
        l.addWidget(t)
        return w

    def create_details_group(self):
        gb = QGroupBox("مشخصات ماده")
        gl = QGridLayout(gb)
        self.lbl_d_name = QLabel("-")
        self.lbl_d_form = QLabel("-")
        self.lbl_d_type = QLabel("-")
        gl.addWidget(QLabel("نام:"), 0, 0);
        gl.addWidget(self.lbl_d_name, 0, 1)
        gl.addWidget(QLabel("فرمول:"), 1, 0);
        gl.addWidget(self.lbl_d_form, 1, 1)
        gl.addWidget(QLabel("نوع:"), 2, 0);
        gl.addWidget(self.lbl_d_type, 2, 1)
        return gb

    def populate_chemicals(self):
        self.combo_chem.clear()
        for k, v in sorted(CHEMILAB_DB.items(), key=lambda x: x[1]['name']):
            self.combo_chem.addItem(f"{v['name']} ({v['formula']})", k)

    def filter_chemicals(self, text):
        self.combo_chem.blockSignals(True)
        self.combo_chem.clear()
        t = text.lower()
        cat = self.combo_filter.currentText()
        eng_cat = ""
        if cat == "اسید":
            eng_cat = "Acid"
        elif cat == "باز":
            eng_cat = "Base"
        elif cat == "نمک":
            eng_cat = "Salt"
        elif cat == "گاز":
            eng_cat = "Gas"
        elif cat == "جامد":
            eng_cat = "Solid"
        elif cat == "مایع":
            eng_cat = "Liquid"

        for k, v in sorted(CHEMILAB_DB.items(), key=lambda x: x[1]['name']):
            # پشتیبانی از جستجوی همزمان انگلیسی (کلید و فرمول) و فارسی
            match_text = t in v['name'].lower() or t in v['formula'].lower() or t in k.lower()
            match_cat = (eng_cat == "") or (eng_cat in v['type'])
            if match_text and match_cat:
                self.combo_chem.addItem(f"{v['name']} ({v['formula']})", k)
        self.combo_chem.blockSignals(False)
        if self.combo_chem.count() > 0: self.combo_chem.setCurrentIndex(0); self.update_chem_details()

    def update_chem_details(self):
        k = self.combo_chem.currentData()
        if k and k in CHEMILAB_DB:
            d = CHEMILAB_DB[k]
            self.lbl_d_name.setText(d.get('name', ''))
            self.lbl_d_form.setText(ChemicalCalculator.to_subscript(d.get('formula', '')))
            self.lbl_d_type.setText(get_persian_type(d.get('type', '')))
            self.spin_molarity.setValue(float(d.get('molarity', 0.1)))

    def handle_reaction_result(self, disc):
        if not disc: return
        name, xp, status, has_pr, has_gas = disc
        if status == "new":
            self.timer.stop()
            self.txt_log.append(f"✨ واکنش جدید کشف شد: {name}")
            self.container.trigger_reaction_animation(has_pr, has_gas)
            self.update_player_stats()
            self.update_discoveries_table()
            self.update_wiki_table()
            QMessageBox.information(self, "کشف!", f"تبریک! شما واکنش جدیدی کشف کردید:\n{name}\nامتیاز کسب شده: {xp}")
            self.timer.start(50)

    def action_add(self):
        try:
            k = self.combo_chem.currentData()
            if not k: return
            msg, overflow, warnings = self.engine.add_chemical(k, self.spin_vol.value(), self.spin_molarity.value())
            self.txt_log.append(msg)
            for w in warnings: self.txt_log.append(f"<span style='color:#f38ba8;'>{w}</span>")
            if overflow: self.container.trigger_overflow()
            self.update_contents_ui()
            self.handle_reaction_result(self.engine.check_reactions())
            self.update_auto_log_ui()
        except Exception as e:
            pass

    def remove_item(self, layer_id):
        if self.engine.remove_layer(layer_id):
            self.update_contents_ui()
            self.txt_log.append("یک لایه حذف شد.")
            self.update_auto_log_ui()

    def action_wash(self):
        # رفع خطای مربوط به exit code با اصلاح فراخوانی متدها
        if self.engine.is_broken:
            self.engine.stats["flask_breaks"] += 1
        self.engine.reset()

        # خاموش کردن همزن از طریق کنترلر کانتینر
        self.container.set_stirrer(False)

        # اگر دکمه وجود دارد خاموشش کن
        if hasattr(self, 'btn_stirrer'):
            self.btn_stirrer.setChecked(False)

        self.update_contents_ui()
        self.txt_log.append("ظرف تعویض و کاملاً تمیز شد.")
        self.update_auto_log_ui()

    def update_player_stats(self):
        self.lbl_level.setText(f"سطح: {self.engine.level}")
        self.lbl_score.setText(f"امتیاز: {self.engine.score}")
        self.lbl_welcome.setText(f"👤 شیمیدان: {self.engine.player_name}")
        self.progress_xp.setValue(self.engine.score % 100)

    def update_discoveries_table(self):
        self.table_disc.setRowCount(len(CUSTOM_REACTIONS))
        for i, (n, d) in enumerate(CUSTOM_REACTIONS.items()):
            if n in self.engine.discovered:
                self.table_disc.setItem(i, 0, QTableWidgetItem(f"✅ {n}"))
                self.table_disc.setItem(i, 1, QTableWidgetItem(str(d.get('xp', 0))))
            else:
                self.table_disc.setItem(i, 0, QTableWidgetItem("؟؟؟"))
                self.table_disc.setItem(i, 1, QTableWidgetItem("-"))

    def update_contents_ui(self):
        self.table_cont.setRowCount(0)
        for i, layer in enumerate(self.engine.visual_layers):
            self.table_cont.insertRow(i)
            self.table_cont.setItem(i, 0, QTableWidgetItem(layer['name']))
            f = CHEMILAB_DB.get(layer['key'], {}).get('formula', '?')
            self.table_cont.setItem(i, 1, QTableWidgetItem(ChemicalCalculator.to_subscript(f)))
            self.table_cont.setItem(i, 2, QTableWidgetItem(f"{layer['amount']:.2f}"))
            ctype = CHEMILAB_DB.get(layer['key'], {}).get('type', '')
            unit = "g" if "Solid" in ctype or "Metal" in ctype else "mL"
            self.table_cont.setItem(i, 3, QTableWidgetItem(unit))
            btn_del = QPushButton("❌")
            btn_del.setFixedSize(30, 25)
            btn_del.setStyleSheet("background-color: #ff5555; border-radius: 4px;")
            btn_del.clicked.connect(lambda checked, lid=layer['id']: self.remove_item(lid))
            self.table_cont.setCellWidget(i, 4, btn_del)
        self.lbl_mix.setText(f"{self.engine.get_mixture_empirical_formula()}")

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
                            if w not in self.txt_log.toPlainText(): self.txt_log.append(
                                f"<span style='color:#f38ba8;'>{w}</span>")
                        if overflow: self.container.trigger_overflow()
                        if int(self.engine.titration_volume * 10) % 20 == 0: self.update_contents_ui()

            self.engine.update_physics()

            if self.engine.is_broken and "ظرف شکسته" not in self.txt_log.toPlainText():
                self.txt_log.append("💥 دما بیش از حد بالا رفت و ظرف ترکید! سریعاً آن را تعویض کنید.")

            if not hasattr(self, 'st'): self.st = time.time()
            t = time.time() - self.st
            ph = self.engine.get_ph()
            temp = self.engine.temp_c

            if self.btn_titrate.isChecked() and (self.last_ph < 6 and ph > 8 or self.last_ph > 8 and ph < 6):
                self.txt_log.append("✅ نقطه هم‌ارزی تیتراسیون فرا رسید! (هوش مصنوعی)")
                self.btn_titrate.setChecked(False)  # هوش مصنوعی همزن را خاموش می کند
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

            # آپدیت کارنامه
            if int(t) % 2 == 0:
                self.update_report_card()

            if self.engine.speed_multiplier > 0:
                self.data_time.append(t)
                self.data_ph.append(ph)
                self.data_temp.append(temp)
                if len(self.data_time) > 100:
                    self.data_time.pop(0);
                    self.data_ph.pop(0);
                    self.data_temp.pop(0)
                self.line_ph.set_data(self.data_time, self.data_ph)
                self.line_temp.set_data(self.data_time, self.data_temp)
                if self.data_time:
                    self.ax1.set_xlim(min(self.data_time), max(self.data_time) + 1);
                    self.ax1.set_ylim(0, 14)
                    self.ax2.set_xlim(min(self.data_time), max(self.data_time) + 1);
                    self.ax2.set_ylim(min(self.data_temp) - 5, max(self.data_temp) + 5)
                self.canvas.draw()
        except Exception as e:
            pass


if __name__ == '__main__':
    if hasattr(Qt, 'AA_EnableHighDpiScaling'): QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'): QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    app.setLayoutDirection(Qt.RightToLeft)
    app.setFont(QFont(FONT_NAME, 10))
    app.setStyleSheet(APP_STYLE_DARK)
    w = ModernLabWindow()
    w.show()
    sys.exit(app.exec())
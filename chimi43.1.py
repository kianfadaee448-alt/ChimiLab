import json
import sys
import time
import re
import os
import math
import random
from collections import Counter
import sqlite3
from datetime import datetime

# ==========================================
# وارد کردن کتابخانه‌های Kivy و فارسی ساز
# ==========================================
import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.slider import Slider
from kivy.uix.scrollview import ScrollView
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, Line, Ellipse, InstructionGroup
from kivy.core.window import Window
from kivy.core.text import LabelBase

try:
    import arabic_reshaper
    from bidi.algorithm import get_display

    HAS_BIDI = True
except ImportError:
    HAS_BIDI = False
    print("Warning: arabic_reshaper or python-bidi not installed. Persian text will not render correctly.")

# تنظیم فونت پیش‌فرض
FONT_NAME = "Tahoma"
FONT_PATH = "tahoma.ttf"
try:
    LabelBase.register(name=FONT_NAME, fn_regular=FONT_PATH)
except:
    pass


def p_text(text):
    """تابع کمکی جهت معکوس کردن متون فارسی برای نمایش درست در کیوی"""
    if not text: return ""
    text = str(text)
    if HAS_BIDI:
        reshaped_text = arabic_reshaper.reshape(text)
        return get_display(reshaped_text)
    return text


# ==========================================
# دیتابیس جامع عناصر و واکنش‌ها (دقیقاً مشابه نسخه اصلی)
# ==========================================
CUSTOM_REACTIONS = {}
CHEMILAB_DB = {}

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

# تکمیل مابقی عناصر تا ۱۱۸ به صورت پویا و اطلاعات مربوطه
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

TYPE_MAP = {
    "Strong Acid": "مایع (اسید قوی)", "Weak Acid": "مایع (اسید ضعیف)", "Strong Base": "مایع (باز قوی)",
    "Weak Base": "مایع (باز ضعیف)", "Acid": "مایع (اسید)", "Base": "مایع (باز)", "Superacid": "ابر اسید",
    "Gas": "گاز", "Liquid": "مایع", "Solid": "جامد", "Metal": "جامد (فلز)", "Oxide": "جامد (اکسید)",
    "Salt": "جامد (نمک)", "Element": "جامد (عنصر)", "Halogen": "هالوژن", "Organic Compound": "ترکیب آلی",
    "Solvent": "مایع (حلال)", "Catalyst": "کاتالیزور", "Precipitate": "جامد (رسوب)"
}


def get_persian_type(eng_type):
    for k, v in TYPE_MAP.items():
        if k in eng_type: return v
    return eng_type


def normalize_key(key):
    if not key: return ""
    key = re.sub(
        r'\s+(heat|light|conc|dilute|steam|aq|excess|limited|slow|cold|hot|dissolved|decay|solid|liquid|gas|catalyst).*',
        '', str(key), flags=re.IGNORECASE)
    key = re.sub(r'\((s|g|l|aq|solid|gas|liquid)\)', '', key, flags=re.IGNORECASE)
    return key.strip().lower()


def hex_to_rgba(hex_color):
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 6:
        return [int(hex_color[i:i + 2], 16) / 255.0 for i in (0, 2, 4)] + [1.0]
    return [1.0, 1.0, 1.0, 1.0]


def load_databases():
    # دیتابیس پیشفرض
    CHEMILAB_DB["h2o"] = {"name": "آب", "type": "Liquid", "pH": 7.0, "molarity": 55.5, "heat": 0.0, "color": "#2ec27e",
                          "formula": "H2O"}
    CHEMILAB_DB["hcl"] = {"name": "هیدروکلریک اسید", "type": "Strong Acid", "pH": 1.0, "molarity": 1.0, "heat": 0.0,
                          "color": "#e0e0eb", "formula": "HCl"}
    CHEMILAB_DB["naoh"] = {"name": "سدیم هیدروکسید", "type": "Strong Base", "pH": 13.0, "molarity": 1.0, "heat": -44.5,
                           "color": "#f9e2af", "formula": "NaOH"}
    CHEMILAB_DB["agcl"] = {"name": "نقره کلرید", "type": "Precipitate", "pH": 7.0, "molarity": 0.0, "heat": 0.0,
                           "color": "#ffffff", "formula": "AgCl"}
    CHEMILAB_DB["co2"] = {"name": "کربن دی اکسید", "type": "Gas", "pH": 5.5, "molarity": 0.0, "heat": 0.0,
                          "color": "#575757", "formula": "CO2"}
    CHEMILAB_DB["agno3"] = {"name": "نقره نیترات", "type": "Salt", "pH": 6.0, "molarity": 0.5, "heat": 0.0,
                            "color": "#b4befe", "formula": "AgNO3"}
    CHEMILAB_DB["hno3"] = {"name": "نیتریک اسید", "type": "Strong Acid", "pH": 1.2, "molarity": 1.0, "heat": 0.0,
                           "color": "#f38ba8", "formula": "HNO3"}
    CHEMILAB_DB["nacl"] = {"name": "سدیم کلرید", "type": "Salt", "pH": 7.0, "molarity": 1.0, "heat": 0.0,
                           "color": "#cba6f7", "formula": "NaCl"}

    CUSTOM_REACTIONS["خنثی سازی HCl"] = {"reactants": ["hcl", "naoh"], "products": ["h2o", "nacl"],
                                         "desc": "واکنش اسید قوی و باز قوی", "xp": 50, "temp_min": -273}
    CUSTOM_REACTIONS["رسوب نقره کلرید"] = {"reactants": ["agno3", "hcl"], "products": ["agcl", "hno3"],
                                           "desc": "واکنش رسوبی جابجایی دوگانه", "xp": 40, "temp_min": -273}

    # تلاش برای خواندن دیتابیس لوکال SQLite
    db_path = "db.db"
    if os.path.exists(db_path):
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
                CUSTOM_REACTIONS[fa_name] = {
                    "reactants": parse_db_list(i[2]), "products": parse_db_list(i[3]),
                    "desc": str(i[4]), "xp": int(i[5]) if i[5] else 0, "temp_min": float(i[6]) if i[6] else -273
                }

            cursor.execute("SELECT * FROM chemilab WHERE 1")
            for i in cursor.fetchall():
                key_name = normalize_key(str(i[2]))
                CHEMILAB_DB[key_name] = {
                    "name": str(i[1]), "type": str(i[3]), "pH": float(i[4]) if i[4] else 7.0,
                    "molarity": float(i[5]) if i[5] else 0.1, "heat": float(i[6]) if i[6] else 0.0,
                    "color": str(i[7]), "formula": str(i[8])
                }
            connection.close()
        except Exception as e:
            print(f"Database load error: {e}")


load_databases()

# تبدیل تمامی کدهای رنگ دیتابیس به RGBA مناسب Kivy
for k, v in CHEMILAB_DB.items():
    if isinstance(v['color'], str):
        v['color'] = hex_to_rgba(v['color'])


# ==========================================
# محاسبات شیمی و منطق (LabEngine کامل)
# ==========================================
class ChemicalCalculator:
    SUBSCRIPTS = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")
    SUPERSCRIPTS = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")

    @staticmethod
    def to_subscript(text):
        return str(text).translate(ChemicalCalculator.SUBSCRIPTS) if text else ""

    @staticmethod
    def to_superscript(text):
        return str(text).translate(ChemicalCalculator.SUPERSCRIPTS) if text else ""

    @staticmethod
    def parse_formula(formula):
        if formula in ["Mix", "-", None]: return Counter()
        try:
            elements = re.findall(r'([A-Z][a-z]*)(\d*)', formula)
            composition = Counter()
            for el, count in elements:
                composition[el] += int(count) if count else 1
            return composition
        except Exception:
            return Counter()

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
        self.reset()
        self.add_to_log("آزمایشگاه راه‌اندازی شد.")

    def add_to_log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        self.auto_log.append(f"[{ts}] {msg}")
        if len(self.auto_log) > 200:
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

    def filter_solids(self):
        if self.is_broken: return []
        removed = []
        new_layers = []
        for layer in self.visual_layers:
            ctype = CHEMILAB_DB.get(layer['key'], {}).get('type', '')
            if any(x in ctype for x in ["Solid", "Metal", "Salt", "Powder", "Precipitate"]):
                removed.append(layer['name'])
                self.total_volume -= layer['amount']
                if layer['key'] in self.contents:
                    del self.contents[layer['key']]
            else:
                new_layers.append(layer)
        self.visual_layers = new_layers
        if self.total_volume < 0: self.total_volume = 0
        if removed:
            self.stats["filter_uses"] += 1
            self.add_to_log(f"مواد جامد فیلتر شدند: {','.join(removed)}")
        return removed

    def add_chemical(self, key, amount, custom_molarity=None):
        warnings = []
        if self.is_broken: return "❌ ظرف شکسته است! ابتدا آن را بشویید.", False, warnings
        key = key.lower()
        if key not in CHEMILAB_DB: return "خطا: ماده یافت نشد", False, warnings

        data = CHEMILAB_DB[key]
        chem_type = data.get('type', '')

        # هشدارهای امنیتی
        if key == "h2o" and any("Acid" in CHEMILAB_DB.get(k, {}).get('type', '') for k in self.contents):
            warnings.append("⚠️ خطر: افزودن آب به اسید منجر به پاشش خطرناک مایع می‌شود! اسید را به آب اضافه کنید.")
        if "Strong Acid" in chem_type and any(
                "Strong Base" in CHEMILAB_DB.get(k, {}).get('type', '') for k in self.contents):
            warnings.append("⚠️ واکنش خنثی سازی به شدت گرمازاست.")

        ph_val = float(data.get("pH", 7.0))
        molarity = custom_molarity if custom_molarity is not None else float(data.get("molarity", 0.1))

        if any(x in chem_type for x in ["Solid", "Metal", "Salt", "Powder", "Precipitate"]):
            added_moles = (amount / 100.0) * molarity
        else:
            added_moles = molarity * (amount / 1000.0)

        old_vol = self.total_volume
        self.total_volume += amount

        if self.total_volume > 0:
            self.temp_c = ((old_vol * self.temp_c) + (amount * 25.0)) / self.total_volume
            q_joules = added_moles * (-float(data.get("heat", 0.0))) * 1000
            if self.total_volume > 0:
                self.temp_c += q_joules / (self.total_volume * 4.18)

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

        result_msg = f"افزوده شد: {data['name']} ({amount:.1f} واحد)"
        is_overflow = self.total_volume > self.max_capacity
        if is_overflow:
            result_msg += " ⚠️ ظرف سرریز شد!"
            self.spill_cleanup()

        self.add_to_log(result_msg)
        return result_msg, is_overflow, warnings

    def spill_cleanup(self):
        if self.total_volume > self.max_capacity:
            ratio = self.max_capacity / self.total_volume
            self.total_volume = self.max_capacity
            for l in self.visual_layers:
                l['amount'] *= ratio
                l['moles'] *= ratio
            for k in self.contents:
                self.contents[k] *= ratio
            self.moles_h *= ratio
            self.moles_oh *= ratio
            return True
        return False

    def remove_layer(self, layer_id):
        for i, layer in enumerate(self.visual_layers):
            if layer['id'] == layer_id:
                key = layer['key']
                moles = layer['moles']
                amount = layer['amount']
                if key in self.contents:
                    self.contents[key] -= moles
                    if self.contents[key] <= 0: del self.contents[key]
                self.total_volume -= amount
                self.visual_layers.pop(i)
                self.add_to_log(f"حذف شد: {layer['name']}")
                return True
        return False

    def get_ph(self):
        if self.total_volume == 0 or self.is_broken: return 7.0
        vol_l = self.total_volume / 1000.0
        h = self.moles_h / vol_l
        oh = self.moles_oh / vol_l
        if abs(h - oh) < 1e-9: return 7.0
        if h > oh:
            return max(0.0, min(14.0, -math.log10(h - oh + 1e-14)))
        else:
            return max(0.0, min(14.0, 14.0 + math.log10(oh - h + 1e-14)))

    def update_physics(self):
        current_time = time.time()
        dt = (current_time - self.last_update) * self.speed_multiplier
        self.last_update = current_time

        self.stats["total_play_time"] += dt

        if self.is_broken:
            self.temp_c -= (self.temp_c - 25.0) * 0.1 * dt
            return

        # تبادل گرما با هوا
        self.temp_c -= (self.temp_c - 25.0) * 0.05 * dt

        # شبیه‌سازی تبخیر آب در دمای جوش
        if self.temp_c >= 100.0 and self.total_volume > 0:
            evap_rate = (self.temp_c - 100.0) * 0.5 * dt
            if evap_rate > 0:
                liquid_layers = [l for l in self.visual_layers if "مایع" in l['type']]
                if liquid_layers:
                    evap_per_layer = evap_rate / len(liquid_layers)
                    for l in liquid_layers:
                        remove_amt = min(l['amount'], evap_per_layer)
                        l['amount'] -= remove_amt
                        self.total_volume -= remove_amt
                        if l['amount'] > 0 and (l['amount'] + remove_amt) > 0:
                            ratio = l['amount'] / (l['amount'] + remove_amt)
                            l['moles'] *= ratio
                            if l['key'] in self.contents: self.contents[l['key']] *= ratio
                    self.visual_layers = [l for l in self.visual_layers if l['amount'] > 0.1]

        # انفجار ناشی از گرمای بحرانی
        if self.temp_c > 500.0 and not self.is_broken:
            self.is_broken = True
            self.stats["flask_breaks"] += 1
            self.add_to_log("💥 ظرف به دلیل حرارت بیش از حد ذوب شد و شکست!")
            self.reset()
            self.is_broken = True

    def check_reactions(self):
        if self.is_broken: return None
        present = set()
        for k, v in self.contents.items():
            if v > 1e-12:
                present.add(normalize_key(k))
                if k in CHEMILAB_DB:
                    present.add(normalize_key(CHEMILAB_DB[k].get("formula", "")))
                    present.add(normalize_key(CHEMILAB_DB[k].get("name", "")))

        for name, rxn in CUSTOM_REACTIONS.items():
            needed = {normalize_key(r) for r in rxn["reactants"]}
            if needed and needed.issubset(present):
                if self.temp_c >= rxn.get("temp_min", -273):
                    if name not in self.discovered:
                        self.discovered.add(name)
                        self.stats["reactions_found"] += 1
                        self.score += rxn["xp"]
                        if self.score >= self.level * 100: self.level += 1
                        self.add_to_log(f"واکنش کشف شد: {name}")
                        return (name, rxn["xp"], "new")
                    else:
                        return (name, 0, "old")
        return None

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
                return {"type": "mission", "title": mission['title'], "xp": mission['xp']}

        # مدال‌ها
        if self.temp_c >= 200 and "داغی ۲۰۰ درجه" not in self.badges:
            self.badges.add("داغی ۲۰۰ درجه")
            return {"type": "badge", "title": "داغی ۲۰۰ درجه"}
        if len(self.discovered) >= 1 and "اولین واکنش" not in self.badges:
            self.badges.add("اولین واکنش")
            return {"type": "badge", "title": "اولین واکنش"}
        return None

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


# ==========================================
# ویجت‌ها و پویانمایی‌های سفارشی Kivy
# ==========================================
class BohrCanvas(Widget):
    """مدل متحرک اوربیتالی اتم بور در فریم‌ورک Kivy"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.Z = 1
        self.angle_offset = 0.0
        Clock.schedule_interval(self.update_anim, 1.0 / 30.0)

    def update_atom(self, z):
        self.Z = max(1, min(118, z))

    def update_anim(self, dt):
        self.angle_offset += 0.02
        self.draw_atom()

    def get_electron_shells(self, z):
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

    def draw_atom(self):
        self.canvas.clear()
        cx, cy = self.center_x, self.center_y
        n_rad = min(self.width, self.height) * 0.08
        if n_rad <= 0: return

        shells_distribution = self.get_electron_shells(self.Z)
        active_shells = sum(1 for s in shells_distribution if s > 0)
        base_radius = n_rad * 1.8
        radius_step = (min(self.width, self.height) / 2.0 - base_radius - 20) / max(1, active_shells)

        with self.canvas:
            # هسته اتم
            Color(1.0, 0.7, 0.3, 1.0)
            Ellipse(pos=(cx - n_rad, cy - n_rad), size=(n_rad * 2, n_rad * 2))

            # رسم مدارهای دش‌لاین و الکترون‌ها
            for i in range(7):
                count = shells_distribution[i]
                if count == 0: continue
                r = base_radius + (i * radius_step)

                # رسم حلقه مدار الکترونی
                Color(0.3, 0.3, 0.4, 0.8)
                Line(circle=(cx, cy, r), width=1)

                step_angle = 2 * math.pi / count
                layer_angle = self.angle_offset * (1.5 - i * 0.1)

                for j in range(count):
                    ang = layer_angle + j * step_angle
                    ex = cx + r * math.cos(ang)
                    ey = cy + r * math.sin(ang)

                    Color(0.5, 0.9, 0.5, 1.0)  # الکترون سبز رنگ
                    Ellipse(pos=(ex - 5, ey - 5), size=(10, 10))


class AnimatedFlaskContainer(Widget):
    """ظرف آزمایش متحرک، رندر حباب، بخار جوش، لایه‌ها، کریستال‌های یخ و خرده شیشه"""

    def __init__(self, engine, **kwargs):
        super().__init__(**kwargs)
        self.engine = engine
        self.bubbles = []
        self.shards = []
        self.steam_particles = []
        self.stirrer_angle = 0.0
        Clock.schedule_interval(self.update_canvas, 1.0 / 30.0)

    def trigger_explosion(self):
        self.shards = []
        w, h = self.width, self.height
        cx, cy = self.x + w / 2, self.y + h / 2
        for _ in range(40):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(3, 12)
            self.shards.append({
                'x': cx, 'y': cy, 'vx': math.cos(angle) * speed, 'vy': math.sin(angle) * speed,
                'rot': random.uniform(0, 360), 'vrot': random.uniform(-10, 10), 'size': random.uniform(4, 16)
            })

    def update_canvas(self, dt):
        self.canvas.clear()
        w, h = self.width, self.height
        if w <= 0 or h <= 0: return

        cx, cy = self.x + w / 2, self.y + h / 2
        flask_w = w * 0.55
        flask_h = h * 0.65
        flask_x = cx - flask_w / 2
        flask_bottom = self.y + 40
        scale = flask_h / self.engine.max_capacity

        # اگر مخزن شکسته است انیمیشن ترکیدن را شبیه‌سازی کن
        if self.engine.is_broken:
            if not self.shards:
                self.trigger_explosion()
            # آپدیت فیزیک خرده شیشه‌ها
            for sh in self.shards:
                sh['x'] += sh['vx']
                sh['y'] += sh['vy']
                sh['vy'] -= 0.3  # گرانش
                sh['rot'] += sh['vrot']

            with self.canvas:
                Color(0.8, 0.9, 1.0, 0.6)
                for sh in self.shards:
                    # رسم چند ضلعی ساده برای شیشه شکسته
                    Line(points=[sh['x'] - sh['size'] / 2, sh['y'] - sh['size'] / 2,
                                 sh['x'] + sh['size'] / 2, sh['y'] - sh['size'] / 2,
                                 sh['x'], sh['y'] + sh['size'] / 2], close=True, width=1.2)
            return

        self.shards.clear()

        # به روز رسانی حباب‌ها و بخار به صورت پویا
        if self.engine.total_volume > 0:
            liquid_top = flask_bottom + (self.engine.total_volume * scale)
            # تولید حباب‌ها
            if random.random() < 0.15:
                self.bubbles.append({
                    'x': random.uniform(flask_x + 10, flask_x + flask_w - 10),
                    'y': flask_bottom + 5, 'speed': random.uniform(1, 3.5), 'size': random.uniform(3, 8)
                })
            # آپدیت موقعیت حباب‌ها
            for b in self.bubbles[:]:
                b['y'] += b['speed']
                if b['y'] > liquid_top:
                    self.bubbles.remove(b)

            # بخار جوش در دماهای بالای ۱۰۰ درجه سانتی‌گراد
            if self.engine.temp_c >= 100.0 and random.random() < 0.3:
                self.steam_particles.append({
                    'x': random.uniform(flask_x + 10, flask_x + flask_w - 10),
                    'y': liquid_top, 'vy': random.uniform(1, 3), 'life': 1.0, 'size': random.uniform(8, 20)
                })
            for s in self.steam_particles[:]:
                s['y'] += s['vy']
                s['life'] -= 0.02
                if s['life'] <= 0:
                    self.steam_particles.remove(s)
        else:
            self.bubbles.clear()
            self.steam_particles.clear()

        with self.canvas:
            # ۱. رسم مایعات به صورت لایه‌لایه
            current_y = flask_bottom
            for layer in self.engine.visual_layers:
                layer_h = layer['amount'] * scale
                if layer_h <= 0: continue
                # افکت گرادیان رنگی مایع
                Color(*layer['color'])
                Rectangle(pos=(flask_x, current_y), size=(flask_w, layer_h))
                current_y += layer_h

            # ۲. رسم حباب‌ها درون مایعات
            Color(1, 1, 1, 0.6)
            for b in self.bubbles:
                Ellipse(pos=(b['x'] - b['size'] / 2, b['y'] - b['size'] / 2), size=(b['size'], b['size']))

            # ۳. همزن مغناطیسی متحرک
            if self.engine.total_volume > 0:
                self.stirrer_angle += 12.0
                Color(0.9, 0.9, 0.9, 1.0)
                # رسم همزن با افکت چرخش خطی ساده
                Line(points=[cx - 15 * math.cos(math.radians(self.stirrer_angle)), flask_bottom + 5,
                             cx + 15 * math.cos(math.radians(self.stirrer_angle)), flask_bottom + 5], width=3)

            # ۴. شیشه بشر مدرج
            Color(0.8, 0.9, 1.0, 0.5)
            Line(rectangle=(flask_x, flask_bottom, flask_w, flask_h), width=2)

            # ۵. درجه‌بندی بشر روی شیشه
            Color(0.9, 0.9, 0.9, 0.6)
            for val in range(100, 1001, 100):
                line_y = flask_bottom + (val * scale)
                Line(points=[flask_x, line_y, flask_x + 12, line_y], width=1)

            # ۶. رندر یخ‌زدگی در دمای زیر صفر
            if self.engine.temp_c < 0:
                frost_alpha = min(0.8, abs(self.engine.temp_c) * 0.05)
                Color(0.7, 0.9, 1.0, frost_alpha)
                for i in range(12):
                    x_pos = flask_x + (i * flask_w / 12)
                    Line(points=[x_pos, flask_bottom, x_pos + random.uniform(-10, 10),
                                 flask_bottom + random.uniform(15, 60)], width=1.5)

            # ۷. رندر افکت بخار
            for s in self.steam_particles:
                Color(0.9, 0.9, 0.9, s['life'] * 0.4)
                Ellipse(pos=(s['x'] - s['size'] / 2, s['y'] - s['size'] / 2), size=(s['size'], s['size']))


class DoubleGraph(Widget):
    """رسم پویای دو متغیر دما و pH بر روی یک بستر نمودار نیتیو سبک در Kivy"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ph_data = []
        self.temp_data = []

    def append_data(self, ph, temp):
        self.ph_data.append(ph)
        self.temp_data.append(temp)
        if len(self.ph_data) > 60:
            self.ph_data.pop(0)
            self.temp_data.pop(0)
        self.draw_graph()

    def draw_graph(self):
        self.canvas.clear()
        w, h = self.width, self.height
        if w <= 0 or h <= 0 or not self.ph_data: return

        step_x = w / 60.0
        h_half = h / 2.0

        with self.canvas:
            # بکگراند تیره نمودار
            Color(0.12, 0.12, 0.18, 1.0)
            Rectangle(pos=self.pos, size=self.size)

            # خط جداکننده افقی دو نمودار
            Color(0.25, 0.25, 0.35, 1.0)
            Line(points=[self.x, self.y + h_half, self.x + w, self.y + h_half], width=1)

            # --- نمودار اول: pH (بالایی) ---
            # رسم گریدلاین برای pH=7
            Color(0.3, 0.5, 0.3, 0.5)
            Line(points=[self.x, self.y + h_half + (7.0 / 14.0) * h_half, self.x + w,
                         self.y + h_half + (7.0 / 14.0) * h_half], width=1)

            pts_ph = []
            for i, ph_val in enumerate(self.ph_data):
                px = self.x + i * step_x
                # نرمال‌سازی مقدار pH بین صفر و ۱۴ در نیمه بالای نمودار
                py = (self.y + h_half) + (ph_val / 14.0) * h_half
                pts_ph.extend([px, py])

            if len(pts_ph) >= 4:
                Color(0.18, 0.8, 0.44, 1.0)  # رنگ سبز درخشان برای pH
                Line(points=pts_ph, width=2)

            # --- نمودار دوم: دما (پایینی) ---
            max_temp = max(100.0, max(self.temp_data))
            min_temp = min(0.0, min(self.temp_data))
            temp_range = max_temp - min_temp if max_temp != min_temp else 100.0

            pts_temp = []
            for i, temp_val in enumerate(self.temp_data):
                px = self.x + i * step_x
                # نرمال‌سازی دما در نیمه پایین نمودار
                py = self.y + ((temp_val - min_temp) / temp_range) * h_half
                pts_temp.extend([px, py])

            if len(pts_temp) >= 4:
                Color(0.95, 0.38, 0.38, 1.0)  # رنگ قرمز گرم برای دما
                Line(points=pts_temp, width=2)


# ==========================================
# چیدمان و ساختار برنامه (Main Window Layout)
# ==========================================
class ModernLabWindow(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='horizontal', **kwargs)
        self.engine = LabEngine()
        self.active_chemical_key = "h2o"
        self.is_dark_theme = True

        self.setup_ui()
        self.refresh_chemicals_list()
        self.update_player_stats()

        # استارت زدن لوپ پردازش فیزیک و رندرهای برنامه
        Clock.schedule_interval(self.game_loop, 1.0 / 15.0)

    def setup_ui(self):
        # ۱. پنل سمت چپ (کنترل‌ها)
        self.left_panel = BoxLayout(orientation='vertical', size_hint_x=0.32, padding=12, spacing=10)

        # پروفایل شیمیدان
        self.profile_box = BoxLayout(orientation='vertical', size_hint_y=0.22, padding=5, spacing=4)
        self.lbl_welcome = Label(text=p_text(f"👤 شیمیدان: {self.engine.player_name}"), font_name=FONT_NAME,
                                 font_size=15, color=(0.65, 0.89, 0.63, 1))
        self.lbl_level = Label(text=p_text("سطح شیمیدان: 1"), font_name=FONT_NAME, font_size=13,
                               color=(0.98, 0.7, 0.53, 1))
        self.lbl_score = Label(text=p_text("امتیاز کسب شده: 0 XP"), font_name=FONT_NAME, font_size=13)
        self.profile_box.add_widget(self.lbl_welcome)
        self.profile_box.add_widget(self.lbl_level)
        self.profile_box.add_widget(self.lbl_score)
        self.left_panel.add_widget(self.profile_box)

        # جستجو و انتخاب مواد شیمیایی
        self.search_layout = BoxLayout(orientation='horizontal', size_hint_y=0.08, spacing=5)
        self.search_input = TextInput(hint_text=p_text("🔍 جستجوی فرمول/نام..."), font_name=FONT_NAME, multiline=False)
        self.search_input.bind(text_validate=self.filter_chemicals)
        self.search_layout.add_widget(self.search_input)
        self.left_panel.add_widget(self.search_layout)

        self.spinner_chem = Spinner(
            text=p_text("انتخاب ماده شیمیایی"),
            values=[], font_name=FONT_NAME, size_hint_y=0.08
        )
        self.spinner_chem.bind(text=self.on_chemical_selected)
        self.left_panel.add_widget(self.spinner_chem)

        # دابل اسپینر/اسلایدر انتخاب غلظت و میزان حجم افزودنی
        volume_box = BoxLayout(orientation='horizontal', size_hint_y=0.08, spacing=5)
        volume_box.add_widget(Label(text=p_text("میزان (mL):"), font_name=FONT_NAME, size_hint_x=0.3))
        self.slider_volume = Slider(min=1, max=300, value=50, step=1)
        self.lbl_vol_val = Label(text="50", size_hint_x=0.2)
        self.slider_volume.bind(value=lambda instance, val: setattr(self.lbl_vol_val, 'text', str(int(val))))
        volume_box.add_widget(self.slider_volume)
        volume_box.add_widget(self.lbl_vol_val)
        self.left_panel.add_widget(volume_box)

        # کنترل‌های افزودن و بورت هوشمند
        btn_layout = BoxLayout(orientation='horizontal', size_hint_y=0.09, spacing=5)
        btn_add = Button(text=p_text("➕ افزودن یکباره"), font_name=FONT_NAME, background_color=(0.2, 0.8, 0.4, 1.0))
        btn_add.bind(on_press=self.action_add_chemical)
        self.btn_titrate = Button(text=p_text("💧 بورت هوشمند"), font_name=FONT_NAME,
                                  background_color=(0.3, 0.5, 0.9, 1.0))
        self.btn_titrate.bind(on_press=self.toggle_titration)
        btn_layout.add_widget(btn_add)
        btn_layout.add_widget(self.btn_titrate)
        self.left_panel.add_widget(btn_layout)

        # دکمه‌های کنترل دما و سرعت
        temp_control_layout = BoxLayout(orientation='horizontal', size_hint_y=0.08, spacing=5)
        btn_heat = Button(text=p_text("🔥 حرارت"), font_name=FONT_NAME, background_color=(0.95, 0.38, 0.38, 1.0))
        btn_heat.bind(on_press=lambda x: self.engine.change_temperature(15.0))
        btn_cool = Button(text=p_text("🧊 خنک‌کننده"), font_name=FONT_NAME, background_color=(0.38, 0.75, 0.95, 1.0))
        btn_cool.bind(on_press=lambda x: self.engine.change_temperature(-15.0))
        temp_control_layout.add_widget(btn_cool)
        temp_control_layout.add_widget(btn_heat)
        self.left_panel.add_widget(temp_control_layout)

        # ابزارهای تعویض بشر، فیلتر و همزن
        tools_layout = BoxLayout(orientation='horizontal', size_hint_y=0.08, spacing=5)
        btn_filter = Button(text=p_text("⚗️ فیلتر جامدات"), font_name=FONT_NAME,
                            background_color=(0.97, 0.88, 0.68, 1.0))
        btn_filter.bind(on_press=self.action_filter)
        btn_wash = Button(text=p_text("🚿 تعویض ظرف"), font_name=FONT_NAME, background_color=(0.54, 0.86, 0.92, 1.0))
        btn_wash.bind(on_press=self.action_wash)
        tools_layout.add_widget(btn_filter)
        tools_layout.add_widget(btn_wash)
        self.left_panel.add_widget(tools_layout)

        # لاگ رخدادها به صورت فشرده در پایین پنل کنترلر
        self.log_input = TextInput(readonly=True, size_hint_y=0.25, font_name=FONT_NAME)
        self.left_panel.add_widget(self.log_input)
        self.add_widget(self.left_panel)

        # ۲. پنل وسط (بشر واکنش زنده)
        self.mid_panel = BoxLayout(orientation='vertical', size_hint_x=0.35, padding=8, spacing=5)
        self.lbl_ph_display = Label(text="pH: 7.00", font_size=24, size_hint_y=0.08, color=(0.18, 0.8, 0.44, 1.0))
        self.lbl_temp_display = Label(text="25.0 °C", font_size=24, size_hint_y=0.08, color=(0.95, 0.38, 0.38, 1.0))
        self.mid_panel.add_widget(self.lbl_ph_display)
        self.mid_panel.add_widget(self.lbl_temp_display)

        self.flask_container = AnimatedFlaskContainer(self.engine, size_hint_y=0.84)
        self.mid_panel.add_widget(self.flask_container)
        self.add_widget(self.mid_panel)

        # ۳. پنل سمت راست (مجموعه برگه‌ها یا تب‌ها به عنوان دانشنامه و بخش‌های فرعی)
        self.right_panel = TabbedPanel(do_default_tab=False, size_hint_x=0.33)

        # تب اول: مدل اتمی بور تعاملی ۱۱۸ عنصر
        self.tab_bohr = TabbedPanelItem(text=p_text("⚛️ مدل بور"), font_name=FONT_NAME)
        bohr_layout = BoxLayout(orientation='vertical', padding=10, spacing=8)
        self.bohr_visual = BohrCanvas(size_hint_y=0.7)
        bohr_layout.add_widget(self.bohr_visual)

        ctrl_bohr = BoxLayout(orientation='horizontal', size_hint_y=0.15, spacing=10)
        btn_bohr_minus = Button(text="-", font_size=20, size_hint_x=0.25)
        btn_bohr_minus.bind(on_press=lambda x: self.change_bohr_element(-1))
        self.lbl_bohr_element = Label(text=p_text("هیدروژن (Z=1)"), font_name=FONT_NAME, size_hint_x=0.5)
        btn_bohr_plus = Button(text="+", font_size=20, size_hint_x=0.25)
        btn_bohr_plus.bind(on_press=lambda x: self.change_bohr_element(1))

        ctrl_bohr.add_widget(btn_bohr_minus)
        ctrl_bohr.add_widget(self.lbl_bohr_element)
        ctrl_bohr.add_widget(btn_bohr_plus)
        bohr_layout.add_widget(ctrl_bohr)

        self.tab_bohr.add_widget(bohr_layout)
        self.right_panel.add_widget(self.tab_bohr)

        # تب دوم: نمودار دما و pH
        self.tab_graph = TabbedPanelItem(text=p_text("📈 نمودار"), font_name=FONT_NAME)
        self.double_graph = DoubleGraph()
        self.tab_graph.add_widget(self.double_graph)
        self.right_panel.add_widget(self.tab_graph)

        # تب سوم: مأموریت‌ها و نشان‌ها
        self.tab_missions = TabbedPanelItem(text=p_text("🎯 ماموریت"), font_name=FONT_NAME)
        self.missions_scroll = ScrollView()
        self.missions_layout = GridLayout(cols=1, spacing=10, size_hint_y=None)
        self.missions_layout.bind(minimum_height=self.missions_layout.setter('height'))
        self.missions_scroll.add_widget(self.missions_layout)
        self.tab_missions.add_widget(self.missions_scroll)
        self.right_panel.add_widget(self.tab_missions)

        # تب چهارم: محتویات و فرمول تجربی کل بشر
        self.tab_contents = TabbedPanelItem(text=p_text("🧪 لایه‌ها"), font_name=FONT_NAME)
        contents_layout = BoxLayout(orientation='vertical', padding=10, spacing=8)
        self.lbl_mix_empirical = Label(text=p_text("فرمول تجربی ترکیب: -"), font_name=FONT_NAME, size_hint_y=0.15,
                                       font_size=16)
        contents_layout.add_widget(self.lbl_mix_empirical)

        self.contents_scroll = ScrollView(size_hint_y=0.85)
        self.contents_grid = GridLayout(cols=1, spacing=5, size_hint_y=None)
        self.contents_grid.bind(minimum_height=self.contents_grid.setter('height'))
        self.contents_scroll.add_widget(self.contents_grid)
        contents_layout.add_widget(self.contents_scroll)

        self.tab_contents.add_widget(contents_layout)
        self.right_panel.add_widget(self.tab_contents)

        # تب پنجم: گزارش‌کار، خروجی و صدور فایل متنی
        self.tab_report = TabbedPanelItem(text=p_text("📝 یادداشت"), font_name=FONT_NAME)
        report_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        self.notes_input = TextInput(hint_text=p_text("یادداشت‌های آزمایشگاه را بنویسید..."), font_name=FONT_NAME,
                                     size_hint_y=0.75)
        self.notes_input.bind(text=self.on_notes_changed)
        report_layout.add_widget(self.notes_input)

        btn_export = Button(text=p_text("📥 خروجی فایل متنی گزارش کار"), font_name=FONT_NAME, size_hint_y=0.25,
                            background_color=(0.98, 0.7, 0.53, 1.0))
        btn_export.bind(on_press=self.export_txt_report)
        report_layout.add_widget(btn_export)
        self.tab_report.add_widget(report_layout)
        self.right_panel.add_widget(self.tab_report)

        # تب ششم: مشخصات و دیتابیس تمام مواد
        self.tab_wiki = TabbedPanelItem(text=p_text("📚 لیست مواد"), font_name=FONT_NAME)
        wiki_scroll = ScrollView()
        self.wiki_grid = GridLayout(cols=1, spacing=8, size_hint_y=None, padding=10)
        self.wiki_grid.bind(minimum_height=self.wiki_grid.setter('height'))
        for k, v in sorted(CHEMILAB_DB.items(), key=lambda x: x[1]['name']):
            lbl_item = Label(
                text=p_text(f"{v['name']} ({v['formula']}) - نوع: {get_persian_type(v['type'])} - pH: {v['pH']}"),
                font_name=FONT_NAME, size_hint_y=None, height=40, font_size=13
            )
            self.wiki_grid.add_widget(lbl_item)
        wiki_scroll.add_widget(self.wiki_grid)
        self.tab_wiki.add_widget(wiki_scroll)
        self.right_panel.add_widget(self.tab_wiki)

        self.add_widget(self.right_panel)

    def refresh_chemicals_list(self, filter_text=""):
        self.spinner_chem.values = []
        lst = []
        for k, v in sorted(CHEMILAB_DB.items(), key=lambda x: x[1]['name']):
            if filter_text == "" or filter_text.lower() in v['name'].lower() or filter_text.lower() in v[
                'formula'].lower():
                lst.append(p_text(f"{v['name']} ({v['formula']})"))
        self.spinner_chem.values = lst
        if lst:
            self.spinner_chem.text = lst[0]

    def filter_chemicals(self, instance):
        self.refresh_chemicals_list(self.search_input.text)

    def on_chemical_selected(self, spinner, text):
        # استخراج کلید با جستجوی مستقیم در دیتابیس
        for k, v in CHEMILAB_DB.items():
            if v['formula'].lower() in text.lower() or v['name'].lower() in text.lower():
                self.active_chemical_key = k
                break

    def change_bohr_element(self, step):
        new_z = max(1, min(118, self.bohr_visual.Z + step))
        self.bohr_visual.update_atom(new_z)
        info = ATOMIC_DB.get(new_z, ("ناشناخته", "E", "نامشخص", "جامد", 0, []))
        self.lbl_bohr_element.text = p_text(f"{info[0]} ({info[1]}) (Z={new_z})")

    def action_add_chemical(self, instance):
        msg, is_overflow, warnings = self.engine.add_chemical(self.active_chemical_key, self.slider_volume.value)
        self.log_event(msg)
        for w in warnings:
            self.log_event(w)
        self.update_beaker_layers_tab()

    def toggle_titration(self, instance):
        if self.btn_titrate.text == p_text("💧 بورت هوشمند"):
            self.btn_titrate.text = p_text("⏹️ توقف بورت")
            self.btn_titrate.background_color = (0.95, 0.38, 0.38, 1.0)
        else:
            self.btn_titrate.text = p_text("💧 بورت هوشمند")
            self.btn_titrate.background_color = (0.3, 0.5, 0.9, 1.0)

    def action_filter(self, instance):
        removed = self.engine.filter_solids()
        if removed:
            self.log_event(f"مواد جامد فیلتر شدند: {', '.join(removed)}")
            self.update_beaker_layers_tab()
        else:
            self.log_event("هیچ رسوب جامدی برای فیلتر کردن وجود ندارد.")

    def action_wash(self, instance):
        self.engine.reset()
        self.log_event("بشر واکنش کاملاً شسته و تعویض شد.")
        self.update_beaker_layers_tab()

    def log_event(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_input.text = f"[{ts}] {msg}\n" + self.log_input.text

    def on_notes_changed(self, instance, text):
        self.engine.notes = text

    def export_txt_report(self, instance):
        filename = "ChimiLab_Report.txt"
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write("=== گزارش کارنامه سایبری شیمی‌لَب ===\n")
                f.write(f"تاریخ صدور: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"شیمیدان: {self.engine.player_name} (سطح {self.engine.level})\n")
                f.write(f"برچسب مخزن: {self.engine.flask_label}\n")
                f.write(f"فرمول تجربی مخلوط نهایی: {self.engine.get_mixture_empirical_formula()}\n")
                f.write(f"دمای نهایی: {self.engine.temp_c:.1f} °C - pH: {self.engine.get_ph():.2f}\n")
                f.write("-" * 40 + "\n\n")
                f.write("محتویات لایه‌نشانی شده بشر:\n")
                for l in self.engine.visual_layers:
                    f.write(f"- {l['name']} به میزان {l['amount']:.1f} واحد\n")
                f.write("\n" + "-" * 40 + "\n")
                f.write("یادداشت‌های آزمایشگاه:\n")
                f.write(self.notes_input.text)
                f.write("\n\nمأموریت‌های تکمیل‌شده:\n")
                for m_id in self.engine.completed_missions:
                    f.write(f"- مأموریت کدمشخص {m_id}\n")
            self.log_event(f"گزارش متنی در {filename} ذخیره شد.")
        except Exception as e:
            self.log_event(f"خطا در صدور فایل متنی: {str(e)}")

    def update_player_stats(self):
        self.lbl_welcome.text = p_text(f"👤 شیمیدان: {self.engine.player_name}")
        self.lbl_level.text = p_text(f"سطح شیمیدان: {self.engine.level}")
        self.lbl_score.text = p_text(f"امتیاز کسب شده: {self.engine.score} XP")

    def update_beaker_layers_tab(self):
        self.contents_grid.clear_widgets()
        for l in self.engine.visual_layers:
            # ایجاد یک سطر ساده با دکمه حذف برای هر لایه شیمیایی درون بشر
            row = BoxLayout(orientation='horizontal', size_hint_y=None, height=45, spacing=5)
            row.add_widget(
                Label(text=p_text(f"{l['name']} ({l['amount']:.1f} mL)"), font_name=FONT_NAME, size_hint_x=0.8))

            btn_del = Button(text="X", size_hint_x=0.2, background_color=(0.95, 0.38, 0.38, 1.0))
            btn_del.bind(on_press=lambda inst, lid=l['id']: self.delete_beaker_layer(lid))
            row.add_widget(btn_del)

            self.contents_grid.add_widget(row)
        self.lbl_mix_empirical.text = p_text(f"فرمول تجربی ترکیب: {self.engine.get_mixture_empirical_formula()}")

    def delete_beaker_layer(self, layer_id):
        if self.engine.remove_layer(layer_id):
            self.log_event("یک لایه به صورت دستی از بشر تخلیه شد.")
            self.update_beaker_layers_tab()

    def update_missions_ui(self):
        self.missions_layout.clear_widgets()
        for m in self.engine.missions:
            status = "✅" if m['id'] in self.engine.completed_missions else "❌"
            lbl_m = Label(
                text=p_text(f"{status} | {m['title']} (+{m['xp']} XP)\n   {m['desc']}"),
                font_name=FONT_NAME, size_hint_y=None, height=65, font_size=13
            )
            self.missions_layout.add_widget(lbl_m)

    def game_loop(self, dt):
        # بورت هوشمند / تیتراسیون قطره‌ای خودکار
        if self.btn_titrate.text == p_text("⏹️ توقف بورت") and not self.engine.is_broken:
            # تغذیه ۲ واحد در هر فریم
            msg, overflow, warnings = self.engine.add_chemical(self.active_chemical_key, 2.0)
            self.engine.titration_volume += 2.0
            self.update_beaker_layers_tab()

        self.engine.update_physics()

        ph = self.engine.get_ph()
        temp = self.engine.temp_c

        self.lbl_ph_display.text = f"pH: {ph:.2f}" if not self.engine.is_broken else "pH: ---"
        self.lbl_temp_display.text = f"{temp:.1f} °C"

        # رسم پویای نمودار
        self.double_graph.append_data(ph, temp)

        # بررسی واکنش‌ها
        rxn_res = self.engine.check_reactions()
        if rxn_res and rxn_res[2] == "new":
            self.log_event(f"✨ واکنش جدیدی کشف شد: {rxn_res[0]}")
            self.update_player_stats()

        # بررسی مأموریت‌ها و نشان‌ها
        mission_res = self.engine.check_missions_and_badges()
        if mission_res:
            self.log_event(f"🏆 مأموریت/نشان باز شد: {mission_res['title']}")
            self.update_player_stats()
            self.update_missions_ui()


# ==========================================
# استارت پایتون و رانر برنامه
# ==========================================
class ChimiLabApp(App):
    def build(self):
        Window.size = (1280, 750)
        # اعمال تم تیره پیشرفته مشابه کدهای PyQt5
        Window.clearcolor = (0.05, 0.05, 0.08, 1.0)
        return ModernLabWindow()


if __name__ == '__main__':
    ChimiLabApp().run()
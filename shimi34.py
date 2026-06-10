import json
import sys
import time
import re
import os
import math
import random
import urllib.request
import urllib.error
from collections import Counter

try:
    import matplotlib
    matplotlib.use("Qt5Agg")
    from PyQt5.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QLabel, QPushButton, QComboBox, QFrame, QGroupBox, QTextEdit,
        QTabWidget, QMessageBox, QDoubleSpinBox, QFormLayout, QTableWidget,
        QTableWidgetItem, QHeaderView, QSplitter, QLineEdit, QGridLayout,
        QListWidget, QSpinBox, QProgressBar, QScrollArea, QDialog, QToolTip,
        QInputDialog, QMenuBar, QAction
    )
    from PyQt5.QtCore import Qt, QTimer, QRectF, QPropertyAnimation, pyqtProperty, QEasingCurve, QPoint, QThread, \
        pyqtSignal
    from PyQt5.QtGui import QFont, QColor, QPainter, QPen, QLinearGradient, QPainterPath, QBrush, QCursor, QFontMetrics
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
except ImportError as e:
    print(f"Error: {e}")
    print("Please install required libraries: pip install PyQt5 matplotlib")
    sys.exit(1)

SERVER_URL_CHEMICALS = "https://raw.githubusercontent.com/kianfadaee448-alt/ChemLab-DB/main/README.json"
SERVER_URL_REACTIONS = "https://raw.githubusercontent.com/kianfadaee448-alt/CUSTOM-REACTIONS/main/README.md"

CHEMILAB_DB = {
    "naoh": {"name": "سدیم هیدروکسید", "formula": "NaOH", "type": "Strong Base", "pH": 13.0, "molarity": 0.1,
             "heat": -44.5, "color": "#FFFFFF"},
    "hcl": {"name": "هیدروکلریک اسید", "formula": "HCl", "type": "Strong Acid", "pH": 1.0, "molarity": 0.1,
            "heat": -74.8, "color": "#F0F8FF"},
    "h2so4": {"name": "سولفوریک اسید", "formula": "H2SO4", "type": "Strong Acid", "pH": 1.0, "molarity": 0.1,
              "heat": -88.0, "color": "#FFFFFF"},
    "cuso4": {"name": "مس(II) سولفات", "formula": "CuSO4", "type": "Salt", "pH": 4.0, "molarity": 0.1, "heat": -66.0,
              "color": "#0000FF"},
    "h2o": {"name": "آب مقطر", "formula": "H2O", "type": "Liquid", "pH": 7.0, "molarity": 55.5, "heat": 0.0,
            "color": "#E0FFFF"},
    "agno3": {"name": "نقره نیترات", "formula": "AgNO3", "type": "Salt", "pH": 6.0, "molarity": 0.1, "heat": 22.6,
              "color": "#F5F5F5"},
    "nacl": {"name": "سدیم کلرید", "formula": "NaCl", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 3.9,
             "color": "#FFFFFF"},
    "ki": {"name": "پتاسیم یدید", "formula": "KI", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 20.3,
           "color": "#FFFFFF"},
    "pb(no3)2": {"name": "سرب(II) نیترات", "formula": "Pb(NO3)2", "type": "Salt", "pH": 4.0, "molarity": 0.1,
                 "heat": 33.0, "color": "#FDF5E6"},
    "c2h5oh": {"name": "اتانول", "formula": "C2H5OH", "type": "Alcohol", "pH": 7.0, "molarity": 0.1, "heat": -6.6,
               "color": "#FFFFFF"},
    "kmno4": {"name": "پتاسیم پرمنگنات", "formula": "KMnO4", "type": "Salt", "pH": 7.5, "molarity": 0.1, "heat": 43.5,
              "color": "#8B008B"},
    "h2o2": {"name": "هیدروژن پراکسید", "formula": "H2O2", "type": "Oxidizer", "pH": 4.5, "molarity": 0.1,
             "heat": -98.0, "color": "#F0FFFF"},
    "nh3": {"name": "آمونیاک", "formula": "NH3", "type": "Weak Base", "pH": 11.5, "molarity": 0.1, "heat": -30.0,
            "color": "#F0F8FF"},
    "fe": {"name": "پودر آهن", "formula": "Fe", "type": "Metal", "pH": 7.0, "molarity": 1.0, "heat": 0.0,
           "color": "#808080"},
    "s": {"name": "گوگرد", "formula": "S", "type": "Solid", "pH": 7.0, "molarity": 1.0, "heat": 0.0,
          "color": "#FFFF00"},
    "mg": {"name": "نوار منیزیم", "formula": "Mg", "type": "Metal", "pH": 7.0, "molarity": 1.0, "heat": 0.0,
           "color": "#C0C0C0"},
    "c6h12o6": {"name": "گلوکز", "formula": "C6H12O6", "type": "Sugar", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
                "color": "#FFFFFF"},
}

CUSTOM_REACTIONS = {
    "تشکیل اکسید آهن (زنگ آهن)": {"reactants": ["Fe", "O2"], "products": ["Fe2O3"],
                                  "desc": "آهن در حضور اکسیژن و رطوبت زنگ می‌زند.", "xp": 50},
    "خنثی‌سازی اسید و باز": {"reactants": ["HCl", "NaOH"], "products": ["NaCl", "H2O"], "desc": "تولید نمک و آب.",
                             "xp": 75},
    "رسوب کلرید نقره": {"reactants": ["AgNO3", "NaCl"], "products": ["AgCl", "NaNO3"], "desc": "رسوب سفید.",
                        "xp": 60},
    "باران طلایی": {"reactants": ["Pb(NO3)2", "KI"], "products": ["PbI2", "KNO3"], "desc": "رسوب زرد درخشان.",
                    "xp": 100},
    "آتشفشان آمونیوم": {"reactants": ["(NH4)2Cr2O7"], "products": ["Cr2O3", "N2", "H2O"], "desc": "تجزیه حرارتی.",
                        "xp": 150, "temp_min": 150},
    "فیل خمیردندان": {"reactants": ["H2O2", "KI"], "products": ["O2", "H2O"], "desc": "تولید سریع کف اکسیژن.",
                      "xp": 90},
}

FONT_NAME = "Tahoma"
APP_STYLE = """
QMainWindow {
    background-color: #1e1e2e;
}
QWidget {
    color: #cdd6f4;
    font-family: 'Tahoma', sans-serif;
    font-size: 13px;
}
QGroupBox {
    border: 2px solid #313244;
    border-radius: 8px;
    margin-top: 20px;
    background-color: #181825;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top center;
    padding: 0 10px;
    background-color: #1e1e2e;
    color: #89b4fa;
}
QPushButton {
    background-color: #45475a;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    color: white;
    font-weight: bold;
}
    QPushButton:hover {
    background-color: #585b70;
    border: 1px solid #89b4fa;
}
QPushButton:pressed { 
    background-color: #11111b;
    border: 2px solid #fab387;
    padding-top: 10px;
} 
QLineEdit {
    background-color: #e6e9ef; 
    border: 1px solid #45475a;
    border-radius: 4px; padding: 5px;
    color: #000000; font-weight: bold;
}
QComboBox, QDoubleSpinBox, QSpinBox {
    background-color: #313244; 
    border: 1px solid #45475a;
    border-radius: 4px;
    padding: 5px;
    color: white;
}
    QListWidget {
    background-color: #11111b;
    border: 1px solid #313244;
    border-radius: 6px;
    color: #cdd6f4;
    font-size: 14px; 
}
QTableWidget {
    background-color: #11111b;
    gridline-color: #313244;
    color: #cdd6f4;
    border: 1px solid #313244;
    border-radius: 6px;
}
QHeaderView::section {
    background-color: #1e1e2e;
    padding: 6px; border: 1px solid #313244;
    color: #f9e2af;
    font-weight: bold;
}
QTextEdit {
    background-color: #11111b;
    border: 1px solid #313244;
    border-radius: 4px;
    color: #a6e3a1;
}
QTabWidget::pane {
    border: 1px solid #313244;
    background: #1e1e2e;
}
QTabBar::tab {
    background: #313244;
    color: #cdd6f4;
    padding: 8px 12px;
    margin-right: 2px;
    border-top-left-radius: 4px; 
    border-top-right-radius: 4px;
}
QTabBar::tab:selected {
    background: #89b4fa;
    color: #1e1e2e;
    font-weight: bold;
}
QProgressBar {
    border: 2px solid #45475a;
    border-radius: 5px;
    text-align: center;
    color: white;
    background-color: #313244;
}
QProgressBar::chunk { 
    background-color: #fab387;
    width: 20px;
}
QScrollArea { 
    border: none;
    background-color: transparent;
}
QDialog { 
    background-color: #1e1e2e; 
}
"""

TYPE_MAP = {
    # --- اسیدها و بازها ---
    "Strong Acid": "مایع (اسید قوی)",
    "Weak Acid": "مایع (اسید ضعیف)",
    "Strong Base": "مایع (باز قوی)",
    "Weak Base": "مایع (باز ضعیف)",
    "Acid": "مایع (اسید)",
    "Base": "مایع (باز)",
    "Superacid": "ابر اسید",
    "Superacid Base": "پایه ابر اسید",
    "Acidic Oxide": "اکسید اسیدی",

    # --- حالات فیزیکی و ساختار مواد ---
    "Gas": "گاز",
    "Liquid": "مایع",
    "Solid": "جامد",
    "Metal": "جامد (فلز)",
    "Oxide": "جامد (اکسید)",
    "Salt": "جامد (نمک)",
    "Element": "جامد (عنصر)",
    "Halogen": "هالوژن",
    "Ion": "یون",
    "Complex": "کمپلکس",
    "Precipitate": "جامد (رسوب)",
    "Alloy": "آلیاژ",
    "Mineral": "معدنی",

    # --- ترکیبات آلی و زیستی ---
    "Organic Compound": "ترکیب آلی",
    "Organic": "ماده آلی",
    "Organometallic": "ترکیب آلی-فلزی",
    "Hydrocarbon": "هیدروکربن",
    "Alkane": "آلکان",
    "Alcohol": "مایع (الکل)",
    "Aldehyde": "آلدئید",
    "Ester": "استر",
    "Ether": "اتر",
    "Epoxide": "اپوکسید",
    "Sugar": "قند (کربوهیدرات)",
    "Carb": "کربوهیدرات",
    "Fatty Acid": "اسید چرب",
    "Amino Acid": "آمینو اسید",
    "Protein": "پروتئین",
    "Enzyme": "آنزیم",
    "Lipid": "لیپید (چربی)",
    "Alkaloid": "آلکالوئید",

    # --- مواد صنعتی و کاربردی ---
    "Solvent": "مایع (حلال)",
    "Monomer": "مونومر",
    "Polymer": "پلیمر",
    "Catalyst": "کاتالیزور",
    "Chelating Agent": "عامل کلات‌کننده (کمپلکس‌ساز)",
    "Fixative": "تثبیت‌کننده (فیکساتور)",
    "Lubricant": "روان‌کننده",
    "Abrasive": "سایینده",
    "Refrigerant": "مبرد (سرمازا)",
    "Battery Material": "ماده باتری",
    "Fuel": "سوخت",
    "Precursor": "پیش‌ماده",

    # --- مواد پیشرفته و الکترونیک ---
    "Semiconductor": "نیمه‌هادی",
    "Superconductor": "ابررسانا",
    "Dopant": "ناخالصی (دوپ‌کننده)",
    "Dielectric": "دی‌الکتریک (عایق)",
    "Phosphor": "فسفر (ماده تابناک)",
    "Magnet": "آهنربا",
    "Photovoltaic": "فوتوولتائیک",
    "Nanomaterial": "نانومواد",
    "Conductor": "رسانا",

    # --- مواد خاص و خطرناک ---
    "Oxidizer": "اکسیدکننده",
    "Explosive": "ماده منفجره",
    "Primary Explosive": "منفجره اولیه",
    "Radioactive": "رادیواکتیو",
    "Radioisotope": "رادیوایزوتوپ",
    "Pollutant": "آلاینده",
    "Forever Chemical": "مواد شیمیایی ماندگار (PFAS)",
    "Moderator": "کندکننده نوترون",
    "Superheavy": "عنصر فوق سنگین",
    "Medicine": "دارو",

    # --- ترکیبات دوتایی و غیره ---
    "Carbide": "کاربید",
    "Nitride": "نیترید",
    "Hydride": "هیدرید",
    "Silicide": "سیلیسید",
    "Sulfide": "سولفید",
    "Ceramic": "سرامیک",
    "Refractory": "دیرگداز",
"Neurotoxin": "سم عصبی (نوروتوکسین)",
    "Molten Salt": "نمک مذاب",
    "Thermoelectric": "ترمو الکتریک (گرما-برقی)",
    "Reagent": "واکنش‌گر (ری‌اجنت)",
    "Electrolyte": "الکترولیت",
    "Reducing Agent": "عامل کاهنده",
    "Toxin": "سم (توکسین)",
    "Sugar Alcohol": "قند الکلی",
    "Fiber Optic": "فیبر نوری",
    "Ozone Depleting": "تخریب‌کننده لایه ازون",
    "Choking Agent": "عامل خفه‌کننده (شیمیایی-جنگی)",
    "Scintillator": "سوسوزن (سینتیلاتور)",
"Radioactive Gas": "گاز رادیواکتیو",
    "Photocatalyst": "فوتوکاتالیزور",
    "Medical": "پزشکی",
    "Antimicrobial": "ضد میکروب",
    "Additive": "افزودنی",
    "Thermal Storage": "ذخیره‌ساز حرارتی",
    "Etchant": "خورنده (اِچنت)",
    "Stable Isotope": "ایزوتوپ پایدار",
    "Flow Battery": "باتری جریانی",
"Phenol": "فنول",
    "Optical": "نوری (اپتیکال)",
    "Shielding": "محافظ (شیلدینگ)",
    "Herbicide": "علف‌کش",
    "Propellant": "پیش‌ران (سوخت موشک)",
    "Greenhouse Gas": "گاز گلخانه‌ای",
    "Interhalogen": "بین‌هالوژنی",
    "Contrast Agent": "عامل تضاد (در تصویربرداری پزشکی)",
    "Blister Agent": "عامل تاول‌زا (جنگی)",
    "Nerve Agent": "عامل اعصاب (جنگی)",
    "Insulator": "عایق",
}

def get_persian_type(eng_type):
    return TYPE_MAP.get(eng_type, eng_type)

def normalize_key(key):
    key = re.sub(
        r'\s+(heat|light|conc|dilute|steam|aq|excess|limited|slow|cold|hot|dissolved|decay|solid|liquid|gas|catalyst).*',
        '', key, flags=re.IGNORECASE)
    return key.strip().lower()

class UpdateWorker(QThread):
    finished = pyqtSignal(dict, dict, str)

    def run(self):
        new_chems = {}
        new_reactions = {}
        log_msg = ""

        try:
            with urllib.request.urlopen(SERVER_URL_CHEMICALS) as response:
                if response.status == 200:
                    data = response.read().decode('utf-8')
                    json_data = json.loads(data)
                    new_chems = json_data
                    log_msg += f"✅ دیتابیس مواد از سرور دریافت شد ({len(new_chems)} مورد).\n"
        except Exception as e:
            log_msg += f"❌ خطا در اتصال به سرور مواد: {e}\n"

        try:
            with urllib.request.urlopen(SERVER_URL_REACTIONS) as response:
                if response.status == 200:
                    data = response.read().decode('utf-8')
                    json_match = re.search(r'\{.*\}', data, re.DOTALL)
                    if json_match:
                        json_data = json.loads(json_match.group(0))
                    else:
                        json_data = json.loads(data)
                    new_reactions = json_data
                    log_msg += f"✅ دیتابیس واکنش‌ها از سرور دریافت شد ({len(new_reactions)} مورد).\n"
        except Exception as e:
            log_msg += f"❌ خطا در اتصال به سرور واکنش‌ها: {e}\n"

        self.finished.emit(new_chems, new_reactions, log_msg)

class ChemicalCalculator:
    SUBSCRIPTS = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")

    @staticmethod
    def to_subscript(text):
        if not text: return ""
        return text.translate(ChemicalCalculator.SUBSCRIPTS)

    @staticmethod
    def parse_formula(formula):
        if formula == "Mix" or formula == "-" or formula is None: return Counter()
        temp_formula = formula
        while '(' in temp_formula:
            temp_formula = re.sub(
                r'\(([^()]+)\)(\d*)',
                lambda m: m.group(1) * (int(m.group(2)) if m.group(2) else 1),
                temp_formula
            )
        elements = re.findall(r'([A-Z][a-z]*)(\d*)', temp_formula)
        composition = Counter()
        for el, count in elements:
            count = int(count) if count else 1
            composition[el] += count
        return composition

    @staticmethod
    def calculate_empirical_from_moles(atom_moles_counter):
        if not atom_moles_counter:
            return "ماده‌ای وجود ندارد"
        filtered_atoms = {k: v for k, v in atom_moles_counter.items() if v > 1e-9}
        if not filtered_atoms:
            return "-"
        min_mole = min(filtered_atoms.values())
        if min_mole < 1e-12: return "ناچیز"
        ratios = {k: v / min_mole for k, v in filtered_atoms.items()}
        best_multiplier = 1
        best_error = float('inf')
        for m in range(1, 21):
            current_error = 0
            for r in ratios.values():
                val = r * m
                current_error += abs(val - round(val))
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

class RecoveryDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("بازیابی حساب کاربری")
        self.setFixedSize(400, 300)
        self.setStyleSheet("""
            QDialog { background-color: #1e1e2e; border: 2px solid #f38ba8; border-radius: 10px; }
            QLabel { color: white; font-size: 14px; }
            QLineEdit { padding: 8px; border-radius: 5px; border: 1px solid #45475a; background: #313244; color: white; }
            QPushButton { background-color: #89b4fa; color: #1e1e2e; padding: 8px; border-radius: 5px; font-weight: bold; }
        """)

        self.layout = QVBoxLayout(self)
        self.step = 1
        self.generated_code = ""
        self.user_email = ""

        self.lbl_info = QLabel("برای بازیابی حساب، ایمیل خود را وارد کنید:")
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("example@mail.com")
        self.btn_action = QPushButton("ارسال کد تایید")
        self.btn_action.clicked.connect(self.handle_action)

        self.layout.addWidget(self.lbl_info)
        self.layout.addWidget(self.input_field)
        self.layout.addWidget(self.btn_action)

    def handle_action(self):
        if self.step == 1:
            email = self.input_field.text().strip()
            if "@" not in email or "." not in email:
                QMessageBox.warning(self, "خطا", "لطفاً یک ایمیل معتبر وارد کنید.")
                return

            self.user_email = email
            self.generated_code = str(random.randint(1000, 9999))

            print(f"--- EMAIL SIMULATION ---\nTo: {email}\nCode: {self.generated_code}\n------------------------")
            QMessageBox.information(self, "ایمیل ارسال شد",
                                    f"کد تایید به {email} ارسال شد.\n(شبیه‌سازی: کد شما {self.generated_code} است)")

            self.step = 2
            self.lbl_info.setText(f"کد ارسال شده به {email} را وارد کنید:")
            self.input_field.clear()
            self.input_field.setPlaceholderText("کد ۴ رقمی")
            self.btn_action.setText("تایید کد و بازیابی")

        elif self.step == 2:
            code = self.input_field.text().strip()
            if code == self.generated_code:
                QMessageBox.information(self, "موفقیت", "هویت شما تایید شد! حساب کاربری بازیابی می‌شود.")
                self.accept()
            else:
                QMessageBox.critical(self, "خطا", "کد وارد شده صحیح نیست.")

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ورود به آزمایشگاه")
        self.setFixedSize(480, 420)
        self.setLayoutDirection(Qt.RightToLeft)
        self.setStyleSheet("""
            QDialog { background-color: #1e1e2e; border: 2px solid #89b4fa; border-radius: 10px; }
            QLabel { color: white; font-size: 14px; margin-bottom: 5px; }
            QLineEdit { padding: 8px; border-radius: 5px; border: 1px solid #45475a; background: #313244; color: white; font-size: 14px; }
            QPushButton { background-color: #a6e3a1; color: #1e1e2e; padding: 10px; border-radius: 5px; font-weight: bold; font-size: 14px; margin-top: 10px; }
            QPushButton:hover { background-color: #94e2d5; }
            QPushButton#recover { background-color: transparent; color: #f38ba8; border: none; text-decoration: underline; font-size: 12px; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(50, 40, 50, 40)
        layout.setSpacing(20)

        title = QLabel("👋 ثبت نام در آزمایشگاه")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #fab387;")
        layout.addWidget(title)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        form.setSpacing(12)
        form.setFormAlignment(Qt.AlignRight)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("مثلاً: علی شیمیدان")
        form.addRow("نام واقعی:", self.name_input)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("نام کاربری انگلیسی")
        form.addRow("نام کاربری:", self.username_input)


        btn = QPushButton("ثبت و ورود")
        btn.clicked.connect(self.check_input)
        layout.addWidget(btn)

    def check_input(self):
        if self.name_input.text().strip() and self.username_input.text().strip() and self.email_input.text().strip():
            self.accept()
        else:
            QMessageBox.warning(self, "خطا", "لطفاً تمام فیلدها را پر کنید.")


    def get_data(self):
        return {
            "name": self.name_input.text().strip(),
            "username": self.username_input.text().strip(),
        }

class AnimatedContainer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(250, 400)
        self.setMouseTracking(True)
        self._layers = []
        self.max_capacity = 1000.0
        self._flash_opacity = 0.0

        self.anim_flash = QPropertyAnimation(self, b"flashOpacity")
        self.anim_flash.setDuration(600)
        self.anim_flash.setEasingCurve(QEasingCurve.OutQuad)

    @pyqtProperty(float)
    def flashOpacity(self):
        return self._flash_opacity

    @flashOpacity.setter
    def flashOpacity(self, value):
        self._flash_opacity = value
        self.update()

    def update_layers(self, visual_layers):
        self._layers = visual_layers
        self.update()

    def trigger_reaction_animation(self):
        self.anim_flash.setStartValue(1.0)
        self.anim_flash.setEndValue(0.0)
        self.anim_flash.start()

    def mouseMoveEvent(self, event):
        y_pos = event.y()
        w, h = self.width(), self.height()
        margin_x, margin_y = 50, 30
        container_h = h - 2 * margin_y
        scale = container_h / self.max_capacity
        current_y = h - margin_y
        hovered_layer = None
        for layer in self._layers:
            layer_h = layer['amount'] * scale
            top_y = current_y - layer_h
            if top_y <= y_pos <= current_y and margin_x <= event.x() <= w - 30:
                hovered_layer = layer
                break
            current_y = top_y
        if hovered_layer:
            info = f"{hovered_layer['name']}\n{hovered_layer['amount']:.1f} mL/g\n{hovered_layer['type']}"
            QToolTip.showText(event.globalPos(), info, self)
        else:
            QToolTip.hideText()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        margin_x, margin_y = 60, 30
        container_rect = QRectF(margin_x, margin_y, w - margin_x - 30, h - 2 * margin_y)
        total_amount = sum(l['amount'] for l in self._layers)
        scale = container_rect.height() / self.max_capacity
        current_y = container_rect.bottom()
        if total_amount > 0:
            for layer in self._layers:
                layer_h = layer['amount'] * scale
                if current_y - layer_h < container_rect.top():
                    layer_h = current_y - container_rect.top()
                rect = QRectF(container_rect.left(), current_y - layer_h, container_rect.width(), layer_h)
                painter.setPen(Qt.NoPen)
                c = QColor(layer['color'])
                grad = QLinearGradient(rect.topLeft(), rect.topRight())
                grad.setColorAt(0, c.darker(110))
                grad.setColorAt(0.5, c)
                grad.setColorAt(1, c.darker(110))
                painter.setBrush(grad)
                painter.drawRect(rect)
                current_y -= layer_h
        glass_pen = QPen(QColor(200, 200, 200, 180), 3)
        painter.setPen(glass_pen)
        painter.setBrush(Qt.NoBrush)
        path = QPainterPath()
        path.moveTo(container_rect.topLeft())
        path.lineTo(container_rect.bottomLeft())
        path.lineTo(container_rect.bottomRight())
        path.lineTo(container_rect.topRight())
        painter.drawPath(path)
        painter.setPen(QPen(QColor(255, 255, 255, 150), 1))
        font = painter.font()
        font.setPointSize(9)
        painter.setFont(font)
        step_val = 100
        for val in range(0, int(self.max_capacity) + 1, step_val):
            if val == 0: continue
            y_ratio = val / self.max_capacity
            y_coord = container_rect.bottom() - (y_ratio * container_rect.height())
            painter.drawLine(int(container_rect.left()), int(y_coord), int(container_rect.left() + 15), int(y_coord))
            painter.drawLine(int(container_rect.right()), int(y_coord), int(container_rect.right() - 15), int(y_coord))
            painter.drawText(int(container_rect.left()) - 45, int(y_coord) + 5, f"{val}")
        painter.drawText(int(container_rect.left()) - 45, int(container_rect.top()) - 5, "mL / g")
        if self._flash_opacity > 0.01:
            fc = QColor(255, 255, 200, int(self._flash_opacity * 200))
            painter.setBrush(fc)
            painter.setPen(Qt.NoPen)
            painter.drawRect(self.rect())
##################################################################################
#
#                    lab engine

##################################################################################
class LabEngine:
    def __init__(self):
        self.score = 0
        self.level = 1
        self.player_data = {"name": "دانشجو", "username": ""}
        self.discovered = set()
        self.visual_layers = []
        self.layer_id_counter = 0
        self.max_capacity = 1000.0
        self.load_data()
        self.reset()

    def reset(self):
        self.total_volume = 0.0
        self.moles_h = 0.0
        self.moles_oh = 0.0
        self.temp_c = 25.0
        self.contents = {}
        self.visual_layers = []
        self.last_update = time.time()

    def hard_reset(self):
        self.score = 0
        self.level = 1
        self.discovered = set()
        if os.path.exists("lab_save.json"):
            try:
                with open("lab_save.json", "r") as f:
                    d = json.load(f)
                    p_data = d.get("player_data", self.player_data)
                os.remove("lab_save.json")
                self.player_data = p_data
                self.save_data()
            except:
                pass
        self.reset()

    def load_data(self):
        if os.path.exists("lab_save.json"):
            try:
                with open("lab_save.json", "r") as f:
                    d = json.load(f)
                    self.score = d.get("score", 0)
                    self.level = d.get("level", 1)
                    self.discovered = set(d.get("discovered", []))
            except:
                pass

    def save_data(self):
        try:
            with open("lab_save.json", "w") as f:
                json.dump({
                    "score": self.score,
                    "level": self.level,
                    "discovered": list(self.discovered),
                    "player_data": self.player_data
                }, f)
        except:
            pass

    def set_player_data(self, data):
        self.player_data = data
        self.save_data()

    def update_db(self, new_chems, new_reactions):
        count_c = 0
        count_r = 0
        if new_chems:
            for k, v in new_chems.items():
                CHEMILAB_DB[k.lower()] = v
                count_c += 1
        if new_reactions:
            for k, v in new_reactions.items():
                CUSTOM_REACTIONS[k] = v
                count_r += 1
        return count_c, count_r

    def add_chemical(self, key, amount):
        if self.total_volume + amount > self.max_capacity:
            return f"❌ خطا: ظرف پر شده است! (ظرفیت باقی‌مانده: {self.max_capacity - self.total_volume:.1f})"
        key = key.lower()
        if key not in CHEMILAB_DB: return "خطا: ماده یافت نشد"
        data = CHEMILAB_DB[key]
        chem_type = data.get('type', '')
        if "Solid" in chem_type or "Metal" in chem_type or "Salt" in chem_type:
            added_moles = (amount / 100.0) * data.get("molarity", 1.0)
            unit_display = "g"
        else:
            added_moles = data.get("molarity", 0.1) * (amount / 1000.0)
            unit_display = "mL"
        self.total_volume += amount
        self.contents[key] = self.contents.get(key, 0) + added_moles
        self.layer_id_counter += 1
        self.visual_layers.append({
            'id': self.layer_id_counter,
            'key': key,
            'name': data['name'],
            'amount': amount,
            'color': data.get('color', '#FFFFFF'),
            'type': get_persian_type(chem_type),
            'moles': added_moles
        })
        if self.total_volume > 0:
            heat_effect = data.get("heat", 0) * (amount / self.total_volume)
            self.temp_c += heat_effect
        ph_val = data.get("pH", 7.0)
        if ph_val < 7:
            self.moles_h += added_moles * (1 if ph_val < 2 else 0.1)
        elif ph_val > 7:
            self.moles_oh += added_moles * (1 if ph_val > 12 else 0.1)
        return f"افزوده شد: {data['name']} ({amount} {unit_display})"

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
                return True
        return False

    def change_temperature(self, delta):
        self.temp_c += delta

    def update_physics(self):
        current_time = time.time()
        dt = current_time - self.last_update
        self.last_update = current_time
        room_temp = 25.0
        cooling_rate = 0.05
        diff = self.temp_c - room_temp
        if abs(diff) > 0.1:
            change = diff * cooling_rate * dt
            self.temp_c -= change

    def check_reactions(self):
        present = {k.lower() for k, v in self.contents.items() if v > 1e-5}
        found_old = None
        for name, rxn in CUSTOM_REACTIONS.items():
            needed = {normalize_key(r) for r in rxn["reactants"]}
            if needed.issubset(present):
                req_temp = rxn.get("temp_min", -273)
                if self.temp_c >= req_temp:
                    if name not in self.discovered:
                        self.discovered.add(name)
                        self.score += rxn["xp"]
                        if self.score >= self.level * 100: self.level += 1
                        self.save_data()
                        self.temp_c += 10.0
                        return (name, rxn["xp"], "new")
                    else:
                        found_old = (name, 0, "old")
        return found_old

    def get_ph(self):
        if self.total_volume == 0: return 7.0
        vol_l = self.total_volume / 1000.0 if self.total_volume > 0 else 1
        h = self.moles_h / vol_l
        oh = self.moles_oh / vol_l
        if abs(h - oh) < 1e-9: return 7.0
        if h > oh:
            return max(0, min(14, -math.log10(h - oh + 1e-14)))
        else:
            return max(0, min(14, 14 + math.log10(oh - h + 1e-14)))

    def get_mixture_empirical_formula(self):
        total_atoms = Counter()
        for key, moles in self.contents.items():
            if moles <= 1e-9: continue
            if key in CHEMILAB_DB:
                form = CHEMILAB_DB[key].get("formula", "")
                atoms_in_molecule = ChemicalCalculator.parse_formula(form)
                for atom, count in atoms_in_molecule.items():
                    total_atoms[atom] += count * moles
        return ChemicalCalculator.calculate_empirical_from_moles(total_atoms)

class ModernLabWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("آزمایشگاه شیمی پیشرفته")
        self.resize(1500, 950)
        self.setLayoutDirection(Qt.RightToLeft)

        self.engine = LabEngine()
        self.data_time, self.data_ph, self.data_temp = [], [], []
        self.datasheet_table = None

        self.setup_ui()
        self.update_player_stats()

        self.timer = QTimer()
        self.timer.timeout.connect(self.game_loop)

        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.start_auto_update)
        self.update_timer.start(300000)

        QTimer.singleShot(2000, self.start_auto_update)
        QTimer.singleShot(500, self.start_simulation)

        menubar = self.menuBar()
        help_menu = menubar.addMenu("📖 کمک")
        guide_action = QAction("راهنما", self)
        guide_action.triggered.connect(self.show_guide)
        help_menu.addAction(guide_action)

    def show_guide(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("راهنمای کامل برنامه")
        dlg.setFixedSize(720, 720)
        dlg.setStyleSheet("background-color: #1e1e2e; color: #cdd6f4;")

        txt = QTextEdit()
        txt.setReadOnly(True)
        txt.setHtml("""
        <h2 style='color:#89b4fa'>راهنمای آزمایشگاه شیمی پیشرفته</h2>
        <p><b>شروع کار:</b> نام، نام کاربری و ایمیل خود را وارد کنید.</p>
        <p><b>افزودن ماده:</b> از لیست انتخاب کنید، مقدار بدهید و <b>➕ افزودن</b> بزنید.</p>
        <p><b>کشف واکنش:</b> وقتی واکنش جدید رخ داد، امتیاز می‌گیرید و انیمیشن پخش می‌شود.</p>
        <p><b>آپدیت خودکار:</b> هر ۵ دقیقه دیتابیس از اینترنت چک می‌شود.</p>
        <p><b>دکمه‌های جدید:</b><br>
        • <b>🔄 رفرش لیست‌ها</b> → فقط لیست مواد و کشف‌ها را تازه می‌کند<br>
        • <b>📖 راهنما</b> → همین صفحه</p>
        <p><b>شست‌وشو:</b> ظرف را کامل خالی می‌کند.</p>
        """)
        layout = QVBoxLayout(dlg)
        layout.addWidget(txt)

    def start_simulation(self):
        self.timer.start(50)

    def start_auto_update(self):
        self.txt_log.append("⏳ در حال بررسی به‌روزرسانی دیتابیس از سرور...")
        self.worker = UpdateWorker()
        self.worker.finished.connect(self.on_update_finished)
        self.worker.start()

    def on_update_finished(self, new_chems, new_reactions, log_msg):
        c, r = self.engine.update_db(new_chems, new_reactions)
        self.txt_log.append(log_msg)
        if c > 0 or r > 0:
            self.txt_log.append(f"🎉 دیتابیس به‌روز شد: {c} ماده و {r} واکنش جدید اضافه/آپدیت شد.")
            self.refresh_all_lists()
        else:
            self.txt_log.append("دیتابیس تغییر جدیدی نداشت.")

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)

        panel_ctrl = QFrame()
        panel_ctrl.setFixedWidth(380)
        vbox = QVBoxLayout(panel_ctrl)

        gb_player = QGroupBox("پروفایل کاربری")
        v_player = QVBoxLayout()
        self.lbl_welcome = QLabel(f"👤 {self.engine.player_data['name']}")
        self.lbl_welcome.setStyleSheet("color: #a6e3a1; font-size: 18px; font-weight: bold; margin-bottom: 5px;")
        self.lbl_level = QLabel("سطح: 1")
        self.lbl_level.setStyleSheet("color: #fab387; font-size: 14px; font-weight: bold;")
        self.lbl_score = QLabel("امتیاز: 0")
        self.progress_xp = QProgressBar()
        self.progress_xp.setRange(0, 100)
        self.progress_xp.setValue(0)
        self.progress_xp.setStyleSheet("QProgressBar::chunk { background-color: #f9e2af; }")

        v_player.addWidget(self.lbl_welcome)
        v_player.addWidget(self.lbl_level)
        v_player.addWidget(self.lbl_score)
        v_player.addWidget(QLabel("پیشرفت:"))
        v_player.addWidget(self.progress_xp)
        gb_player.setLayout(v_player)
        vbox.addWidget(gb_player)

        gb_chem = QGroupBox("افزودن ماده")
        frm = QFormLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("جستجو...")
        self.search_box.textChanged.connect(self.filter_chemicals)
        self.combo_chem = QComboBox()
        self.populate_chemicals()
        self.combo_chem.currentIndexChanged.connect(self.update_chem_details)
        self.spin_vol = QDoubleSpinBox()
        self.spin_vol.setRange(0.1, 500)
        self.spin_vol.setValue(50)
        self.spin_vol.setSuffix(" mL/g")
        btn_add = QPushButton("➕ افزودن")
        btn_add.clicked.connect(self.action_add)
        btn_add.setStyleSheet("background-color: #a6e3a1; color: #1e1e2e; font-size: 14px;")
        frm.addRow("جستجو:", self.search_box)
        frm.addRow("ماده:", self.combo_chem)
        self.lbl_amount_text = QLabel("مقدار:")
        frm.addRow(self.lbl_amount_text, self.spin_vol)
        frm.addRow(btn_add)
        gb_chem.setLayout(frm)
        vbox.addWidget(gb_chem)

        gb_temp = QGroupBox("کنترل دما")
        h_temp = QHBoxLayout()
        btn_heat = QPushButton("🔥 حرارت")
        btn_heat.setStyleSheet("background-color: #f38ba8; color: #1e1e2e;")
        btn_heat.clicked.connect(lambda: self.engine.change_temperature(15))
        btn_cool = QPushButton("🧊 خنک")
        btn_cool.setStyleSheet("background-color: #89b4fa; color: #1e1e2e;")
        btn_cool.clicked.connect(lambda: self.engine.change_temperature(-15))
        h_temp.addWidget(btn_cool)
        h_temp.addWidget(btn_heat)
        gb_temp.setLayout(h_temp)
        vbox.addWidget(gb_temp)

        self.gb_details = self.create_details_group()
        vbox.addWidget(self.gb_details)

        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        vbox.addWidget(QLabel("📜 گزارش:"))
        vbox.addWidget(self.txt_log)

        btn_wash = QPushButton("🚿 شست و شو")
        btn_wash.setStyleSheet("background-color: #89dceb; color: #1e1e2e; font-weight: bold;")
        btn_wash.clicked.connect(self.action_wash)
        vbox.addWidget(btn_wash)

        btn_hard_reset = QPushButton("⚠️ خروج و ریست")
        btn_hard_reset.setStyleSheet("background-color: #ff5555; color: white;")
        btn_hard_reset.clicked.connect(self.action_hard_reset)
        vbox.addWidget(btn_hard_reset)

        panel_vis = QFrame()
        panel_vis.setStyleSheet("background-color: #181825; border-radius: 10px;")
        v_vis = QVBoxLayout(panel_vis)
        title_vis = QLabel("بشر (1000 mL)")
        title_vis.setAlignment(Qt.AlignCenter)
        title_vis.setStyleSheet("font-size: 16px; color: #cdd6f4; font-weight: bold;")
        v_vis.addWidget(title_vis)
        self.container = AnimatedContainer()
        v_vis.addWidget(self.container, 1, Qt.AlignCenter)
        info_frame = QFrame()
        info_frame.setStyleSheet("background-color: #313244; border-radius: 8px; padding: 5px;")
        info_h = QHBoxLayout(info_frame)
        self.lbl_ph_display = QLabel("pH: 7.00")
        self.lbl_ph_display.setStyleSheet("font-size: 20px; color: #fab387; font-weight: bold;")
        self.lbl_temp_display = QLabel("25.0 °C")
        self.lbl_temp_display.setStyleSheet("font-size: 20px; color: #f38ba8; font-weight: bold;")
        info_h.addWidget(self.lbl_ph_display)
        info_h.addStretch()
        info_h.addWidget(self.lbl_temp_display)
        v_vis.addWidget(info_frame)

        tabs = QTabWidget()
        tabs.addTab(self.create_contents_tab(), "🧪 محتویات")
        tabs.addTab(self.create_graph_tab(), "📈 نمودار")
        tabs.addTab(self.create_discoveries_tab(), "🏆 کشف‌ها")
        tabs.addTab(self.create_wiki_tab(), "📖 دانشنامه")
        tabs.addTab(self.create_datasheet_tab(), "📚 لیست مواد")

        split = QSplitter(Qt.Horizontal)
        split.addWidget(panel_ctrl)
        split.addWidget(panel_vis)
        split.addWidget(tabs)
        split.setSizes([380, 450, 600])
        layout.addWidget(split)

    def get_state_color_text(self, formula):
        norm = normalize_key(formula)
        d = CHEMILAB_DB.get(norm)
        if not d: return formula
        ptype = get_persian_type(d.get('type', ''))
        return f"{d.get('name', formula)} <span style='color:{d.get('color', '#fff')};'>■</span> <small>({ptype})</small>"

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
            lbl_r = QLabel(" + ".join([self.get_state_color_text(r) for r in d['reactants']]))
            lbl_r.setWordWrap(True)
            self.table_wiki.setCellWidget(i, 1, lbl_r)
            lbl_p = QLabel(" + ".join([self.get_state_color_text(p) for p in d['products']]))
            lbl_p.setWordWrap(True)
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
        self.figure = Figure(figsize=(5, 6), facecolor='#1e1e2e')
        self.canvas = FigureCanvas(self.figure)
        self.ax1 = self.figure.add_subplot(211)
        self.ax1.set_facecolor('#1e1e2e')
        self.ax1.set_ylabel('pH', color='white')
        self.ax1.tick_params(colors='white')
        self.ax2 = self.figure.add_subplot(212)
        self.ax2.set_facecolor('#1e1e2e')
        self.ax2.set_ylabel('Temp', color='white')
        self.ax2.tick_params(colors='white')
        self.line_ph, = self.ax1.plot([], [], color='#fab387')
        self.line_temp, = self.ax2.plot([], [], color='#f38ba8')
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
        self.datasheet_table = QTableWidget()
        self.datasheet_table.setColumnCount(7)
        self.datasheet_table.setHorizontalHeaderLabels(["نام", "فرمول", "نوع", "رنگ", "مولاریته", "pH", "گرما"])
        self.datasheet_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.refresh_datasheet()
        l.addWidget(self.datasheet_table)
        return w

    def refresh_datasheet(self):
        if not hasattr(self, 'datasheet_table') or self.datasheet_table is None:
            return
        t = self.datasheet_table
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

    def create_details_group(self):
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

    def populate_chemicals(self):
        self.combo_chem.clear()
        for k, v in sorted(CHEMILAB_DB.items(), key=lambda x: x[1]['name']):
            self.combo_chem.addItem(f"{v['name']} ({v['formula']})", k)

    def filter_chemicals(self, text):
        self.combo_chem.blockSignals(True)
        self.combo_chem.clear()
        t = text.lower()
        for k, v in sorted(CHEMILAB_DB.items(), key=lambda x: x[1]['name']):
            if t in v['name'].lower() or t in v.get('formula', '').lower() or t in k:
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
            ptype = get_persian_type(d.get('type', ''))
            self.lbl_d_type.setText(ptype)
            ctype = d.get('type', '')
            if "Solid" in ctype or "Metal" in ctype or "Salt" in ctype:
                self.spin_vol.setSuffix(" g")
            else:
                self.spin_vol.setSuffix(" mL")

    def handle_reaction_result(self, disc):
        if not disc: return
        name, xp, status = disc
        if status == "new":
            self.timer.stop()
            self.txt_log.append(f"✨ واکنش جدید: {name}")
            self.container.trigger_reaction_animation()
            self.update_player_stats()
            self.update_discoveries_table()
            self.update_wiki_table()
            QMessageBox.information(self, "کشف!", f"تبریک! واکنش کشف شد:\n{name}\nامتیاز: {xp}")
            self.timer.start(50)

    def action_add(self):
        k = self.combo_chem.currentData()
        if not k: return
        msg = self.engine.add_chemical(k, self.spin_vol.value())
        self.txt_log.append(msg)
        self.container.update_layers(self.engine.visual_layers)
        self.update_contents_ui()
        self.handle_reaction_result(self.engine.check_reactions())

    def remove_item(self, layer_id):
        if self.engine.remove_layer(layer_id):
            self.container.update_layers(self.engine.visual_layers)
            self.update_contents_ui()
            self.txt_log.append("لایه حذف شد.")

    def action_wash(self):
        self.engine.reset()
        self.container.update_layers([])
        self.update_contents_ui()
        self.txt_log.append("ظرف شسته شد.")

    def action_hard_reset(self):
        if QMessageBox.question(self, "خروج", "اطلاعات پاک شود؟", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.engine.hard_reset()
            sys.exit(0)

    def update_player_stats(self):
        self.lbl_level.setText(f"سطح: {self.engine.level}")
        self.lbl_score.setText(f"امتیاز: {self.engine.score}")
        self.lbl_welcome.setText(f"👤 {self.engine.player_data['name']}")
        self.lbl_username.setText(f"ID: @{self.engine.player_data['username']}")
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
        f = self.engine.get_mixture_empirical_formula()
        self.lbl_mix.setText(f"{f}")

    def refresh_all_lists(self):
        self.populate_chemicals()
        self.refresh_datasheet()
        self.update_discoveries_table()
        self.update_wiki_table()
        self.txt_log.append("✅ لیست مواد، کشف‌ها و ویکی به‌روزرسانی شد.")

    def game_loop(self):
        self.engine.update_physics()
        if not hasattr(self, 'st'): self.st = time.time()
        t = time.time() - self.st
        ph = self.engine.get_ph()
        temp = self.engine.temp_c
        self.lbl_ph_display.setText(f"pH: {ph:.2f}")
        self.lbl_temp_display.setText(f"{temp:.1f} °C")
        disc = self.engine.check_reactions()
        self.handle_reaction_result(disc)
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

if __name__ == '__main__':
    if hasattr(Qt, 'AA_EnableHighDpiScaling'): QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'): QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    app.setFont(QFont(FONT_NAME, 10))
    app.setStyleSheet(APP_STYLE)
    w = ModernLabWindow()
    w.show()
    sys.exit(app.exec())
import json
import sys
import time
import re
import os
import math
from collections import Counter
import sqlite3
import matplotlib
from molmass import Formula

import  sqlite3

CUSTOM_REACTIONS = {}
CHEMILAB_DB = {}

def custom_reactions():

    connection = sqlite3.connect("db.db")
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM custom_reactions WHERE 1")
    data_ = cursor.fetchall()
    for i in data_:
        fa_name = i[1]
        reactants = i[2]
        products = i[3]
        desc = i[4]
        xp = i[5]
        temp = i[6]

        CUSTOM_REACTIONS[fa_name] = {
            "reactants": reactants,
            "products": products,
            "desc": desc,
            "xp": xp,
            "temp": temp,
        }

def chemilab():

    connection = sqlite3.connect("db.db")
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM chemilab WHERE 1")
    data_ = cursor.fetchall()
    for i in data_:
        name = i[1]
        fa_name = i[2]
        type = i[3]
        ph = i[4]
        molarity = i[5]
        heat = i[6]
        color = i[7]
        formula = i[8]

        CHEMILAB_DB[fa_name] = {
            "name": name,
            "type": type,
            "ph": ph,
            "molarity": molarity,
            "heat": heat,
            "color": color,
            "formula": formula,
        }

custom_reactions()
chemilab()

try:
    matplotlib.use("Qt5Agg")
    from PyQt5.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QLabel, QPushButton, QComboBox, QFrame, QGroupBox, QTextEdit,
        QTabWidget, QMessageBox, QDoubleSpinBox, QFormLayout, QTableWidget,
        QTableWidgetItem, QHeaderView, QSplitter, QLineEdit, QGridLayout,
        QListWidget, QSpinBox, QProgressBar, QScrollArea, QDialog, QToolTip, QFileDialog,
    )
    from PyQt5.QtCore import Qt, QTimer, QRectF, QPropertyAnimation, pyqtProperty, QEasingCurve, QPoint
    from PyQt5.QtGui import QFont, QColor, QPainter, QPen, QLinearGradient, QPainterPath, QBrush, QCursor, QFontMetrics, QPixmap
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
except ImportError as e:
    print(f"Error: {e}")
    print("Please install required libraries: pip install PyQt5 matplotlib")
    sys.exit(0)



FONT_NAME = "Tahoma"
APP_STYLE = """
QMainWindow { background-color: #1e1e2e; }
QWidget { color: #cdd6f4; font-family: 'Tahoma', sans-serif; font-size: 13px; }
QGroupBox { border: 2px solid #313244; border-radius: 8px; margin-top: 10px; background-color: #181825; font-weight: bold; }
QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top center; padding: 0 10px; background-color: #1e1e2e; color: #89b4fa; }
QPushButton { background-color: #45475a; border: 1px solid #313244; border-radius: 6px; padding: 8px 16px; color: white; font-weight: bold; }
QPushButton:hover { background-color: #585b70; border: 1px solid #89b4fa; }
QPushButton:pressed { background-color: #11111b; border: 2px solid #fab387; padding-top: 10px; } 
QLineEdit { background-color: #e6e9ef; border: 1px solid #45475a; border-radius: 4px; padding: 5px; color: #000000; font-weight: bold; }
QComboBox, QDoubleSpinBox, QSpinBox { background-color: #313244; border: 1px solid #45475a; border-radius: 4px; padding: 5px; color: white; }
QListWidget { background-color: #11111b; border: 1px solid #313244; border-radius: 6px; color: #cdd6f4; font-size: 14px; }
QTableWidget { background-color: #11111b; gridline-color: #313244; color: #cdd6f4; border: 1px solid #313244; border-radius: 6px; }
QHeaderView::section { background-color: #1e1e2e; padding: 6px; border: 1px solid #313244; color: #f9e2af; font-weight: bold; }
QTextEdit { background-color: #11111b; border: 1px solid #313244; border-radius: 4px; color: #a6e3a1; }
QTabWidget::pane { border: 1px solid #313244; background: #1e1e2e; }
QTabBar::tab { background: #313244; color: #cdd6f4; padding: 8px 12px; margin-right: 2px; border-top-left-radius: 4px; border-top-right-radius: 4px; }
QTabBar::tab:selected { background: #89b4fa; color: #1e1e2e; font-weight: bold; }
QProgressBar { border: 2px solid #45475a; border-radius: 5px; text-align: center; color: white; background-color: #313244; }
QProgressBar::chunk { background-color: #fab387; width: 20px; }
QScrollArea { border: none; background-color: transparent; }
QDialog { background-color: #1e1e2e; }
QPushButton { font-size: 16px; padding: 12px 24px; }
QLineEdit { font-size: 14px; padding: 8px; }

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
    """برمی‌گرداند نوع فارسی برای نوع انگلیسی داده شده."""
    return TYPE_MAP.get(eng_type, eng_type)

def normalize_key(key):
    """این تابع کلید ورودی را برای تطابق بهتر با الگوهای شیمیایی نرمال می‌کند."""
    key = re.sub(
        r'\s+(heat|light|conc|dilute|steam|aq|excess|limited|slow|cold|hot|dissolved|decay|solid|liquid|gas|catalyst).*',
        '', key, flags=re.IGNORECASE
    )
    return key.strip().lower()


# ----------------- کلاس‌های محاسباتی -----------------

class ChemicalCalculator:
    SUBSCRIPTS = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")

    @staticmethod
    def to_subscript(text):
        if not text:
            return ""
        return text.translate(ChemicalCalculator.SUBSCRIPTS)

    @staticmethod
    def parse_formula(formula):
        if formula in ["Mix", "-", None]:
            return Counter()
        try:
            f = Formula(formula)
            composition = Counter()
            for el in f.composition.keys():
                composition[el] = int(round(f.composition[el]))
            return composition
        except Exception as e:
            # fallback to regex if molmass fails
            elements = re.findall(r'([A-Z][a-z]*)(\d*)', formula)
            composition = Counter()
            for el, count in elements:
                composition[el] += int(count) if count else 1
            return composition

    @staticmethod
    def calculate_empirical_from_moles(atom_moles_counter):
        if not atom_moles_counter:
            return "ماده‌ای وجود ندارد"
        filtered_atoms = {k: v for k, v in atom_moles_counter.items() if v > 1e-9}
        if not filtered_atoms:
            return "-"
        min_mole = min(filtered_atoms.values())
        if min_mole < 1e-12:
            return "ناچیز"

        ratios = {k: v / min_mole for k, v in filtered_atoms.items()}
        best_multiplier = 1
        best_error = float('inf')

        for m in range(1, 21):
            current_error = sum(abs(r * m - round(r * m)) for r in ratios.values())
            if current_error < best_error:
                best_error = current_error
                best_multiplier = m
            if current_error < 0.1:
                break

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


# ----------------- دیالوگ ورود -----------------
class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ورود به آزمایشگاه")
        self.setFixedSize(400, 250)
        self.setStyleSheet("""
            QDialog { background-color: #1e1e2e; border: 2px solid #89b4fa; border-radius: 10px; }
            QLabel { color: white; font-size: 14px; }
            QLineEdit { padding: 8px; border-radius: 5px; border: 1px solid #45475a; background: #313244; color: white; font-size: 14px; }
            QPushButton { background-color: #a6e3a1; color: #1e1e2e; padding: 10px; border-radius: 5px; font-weight: bold; font-size: 14px; }
            QPushButton:hover { background-color: #94e2d5; }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)

        title = QLabel("👋 به آزمایشگاه خوش آمدید")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #fab387; margin-bottom: 10px;")
        layout.addWidget(title)

        lbl = QLabel("لطفاً نام خود را وارد کنید:")
        layout.addWidget(lbl)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("مثلاً: علی شیمیدان")
        layout.addWidget(self.name_input)

        btn = QPushButton("ورود به آزمایشگاه")
        btn.clicked.connect(self.check_input)
        layout.addWidget(btn)

    def check_input(self):
        if self.name_input.text().strip():
            self.accept()
        else:
            self.name_input.setPlaceholderText("⚠️ لطفاً نام را وارد کنید!")
            self.name_input.setStyleSheet("border: 1px solid #f38ba8;")

    def get_name(self):
        return self.name_input.text().strip()


# ----------------- ویجت ظرف آزمایش (مدرج) -----------------
class AnimatedContainer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(250, 400)  # کمی بلندتر برای نمایش بهتر
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
        margin_x, margin_y = 50, 30  # حاشیه چپ بیشتر برای اعداد
        container_h = h - 2 * margin_y

        # محاسبه مقیاس بر اساس ظرفیت کل (ثابت) برای اینکه ارتفاع معنی داشته باشد
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
        margin_x, margin_y = 60, 30  # حاشیه چپ بیشتر برای اعداد

        container_rect = QRectF(margin_x, margin_y, w - margin_x - 30, h - 2 * margin_y)

        # رسم محتویات
        total_amount = sum(l['amount'] for l in self._layers)
        scale = container_rect.height() / self.max_capacity  # مقیاس ثابت بر اساس ظرفیت

        current_y = container_rect.bottom()

        if total_amount > 0:
            for layer in self._layers:
                layer_h = layer['amount'] * scale
                # جلوگیری از رسم خارج از ظرف
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

        # رسم شیشه ظرف
        glass_pen = QPen(QColor(200, 200, 200, 180), 3)
        painter.setPen(glass_pen)
        painter.setBrush(Qt.NoBrush)
        path = QPainterPath()
        path.moveTo(container_rect.topLeft())
        path.lineTo(container_rect.bottomLeft())
        path.lineTo(container_rect.bottomRight())
        path.lineTo(container_rect.topRight())
        painter.drawPath(path)

        # رسم خطوط مدرج (Graduations)
        painter.setPen(QPen(QColor(255, 255, 255, 150), 1))
        font = painter.font()
        font.setPointSize(9)
        painter.setFont(font)

        # خطوط هر 100 میلی لیتر
        step_val = 100
        for val in range(0, int(self.max_capacity) + 1, step_val):
            if val == 0: continue
            y_ratio = val / self.max_capacity
            y_coord = container_rect.bottom() - (y_ratio * container_rect.height())

            # خط اصلی
            painter.drawLine(int(container_rect.left()), int(y_coord), int(container_rect.left() + 15), int(y_coord))
            painter.drawLine(int(container_rect.right()), int(y_coord), int(container_rect.right() - 15), int(y_coord))

            # عدد
            painter.drawText(int(container_rect.left()) - 45, int(y_coord) + 5, f"{val}")

        # برچسب واحد
        painter.drawText(int(container_rect.left()) - 45, int(container_rect.top()) - 5, "mL / g")

        # افکت فلش هنگام واکنش
        if self._flash_opacity > 0.01:
            fc = QColor(255, 255, 200, int(self._flash_opacity * 200))
            painter.setBrush(fc)
            painter.setPen(Qt.NoPen)
            painter.drawRect(self.rect())


# ----------------- موتور منطق -----------------
class LabEngine:
    def __init__(self):
        self.score = 0
        self.level = 1
        self.player_name = "دانشجو"
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
        # نام را نگه می‌داریم، فقط پیشرفت بازی ریست شود
        if os.path.exists("lab_save.json"):
            try:
                # خواندن نام قبل از حذف
                with open("lab_save.json", "r") as f:
                    d = json.load(f)
                    name = d.get("player_name", self.player_name)

                os.remove("lab_save.json")

                # ذخیره مجدد نام
                self.player_name = name
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
                    self.player_name = d.get("player_name", "دانشجو")
            except:
                pass

    def save_data(self):
        try:
            with open("lab_save.json", "w") as f:
                json.dump({
                    "score": self.score,
                    "level": self.level,
                    "discovered": list(self.discovered),
                    "player_name": self.player_name
                }, f)
        except:
            pass

    def set_player_name(self, name):
        self.player_name = name
        self.save_data()

    def add_chemical(self, key, amount):
        # بررسی ظرفیت
        if self.total_volume + amount > self.max_capacity:
            return f"❌ خطا: ظرف پر شده است! (ظرفیت باقی‌مانده: {self.max_capacity - self.total_volume:.1f})"

        key = key.lower()
        if key not in CHEMILAB_DB: return "خطا: ماده یافت نشد"
        data = CHEMILAB_DB[key]
        chem_type = data.get('type', '')

        if "Solid" in chem_type or "Metal" in chem_type or "Salt" in chem_type or "Powder" in chem_type:
            added_moles = (amount / 100.0) * data["molarity"]
            unit_display = "g"
        else:
            added_moles = data["molarity"] * (amount / 1000.0)
            unit_display = "mL"

        self.total_volume += amount
        self.contents[key] = self.contents.get(key, 0) + added_moles

        self.layer_id_counter += 1
        self.visual_layers.append({
            'id': self.layer_id_counter,
            'key': key,
            'name': data['name'],
            'amount': amount,
            'color': data['color'],
            'type': get_persian_type(chem_type),
            'moles': added_moles
        })

        if self.total_volume > 0:
            heat_effect = data["heat"] * (amount / self.total_volume)
            self.temp_c += heat_effect

        if data["pH"] < 7:
            self.moles_h += added_moles * (1 if data["pH"] < 2 else 0.1)
        elif data["pH"] > 7:
            self.moles_oh += added_moles * (1 if data["pH"] > 12 else 0.1)

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
                form = CHEMILAB_DB[key]["formula"]
                atoms_in_molecule = ChemicalCalculator.parse_formula(form)
                for atom, count in atoms_in_molecule.items():
                    total_atoms[atom] += count * moles
        return ChemicalCalculator.calculate_empirical_from_moles(total_atoms)


# ----------------- رابط کاربری -----------------
class ModernLabWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("آزمایشگاه شیمی پیشرفته")
        self.resize(1500, 950)
        self.setLayoutDirection(Qt.RightToLeft)

        self.engine = LabEngine()

        # بررسی ورود کاربر در ابتدای اجرا
        self.check_login()

        self.data_time, self.data_ph, self.data_temp = [], [], []

        self.setup_ui()
        self.update_player_stats()
        self.timer = QTimer()
        self.timer.timeout.connect(self.game_loop)

        # نمایش دیالوگ راهنما پس از لود کامل
        QTimer.singleShot(500, self.start_simulation)

    def check_login(self):
        # اگر نام پیش فرض است یا فایل وجود ندارد، دیالوگ ورود را نشان بده
        if self.engine.player_name == "دانشجو" or not os.path.exists("lab_save.json"):
            dlg = LoginDialog(self)
            if dlg.exec_() == QDialog.Accepted:
                name = dlg.get_name()
                self.engine.set_player_name(name)

    def start_simulation(self):
        self.timer.start(50)

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)

        # پنل راست (کنترل)
        panel_ctrl = QFrame()
        panel_ctrl.setFixedWidth(380)
        vbox = QVBoxLayout(panel_ctrl)

        # باکس خوش آمدگویی و وضعیت
        gb_player = QGroupBox("پروفایل شیمیدان")
        v_player = QVBoxLayout()

        self.lbl_welcome = QLabel(f"👤 شیمیدان: {self.engine.player_name}")
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
        v_player.addWidget(QLabel("پیشرفت تا سطح بعدی:"))
        v_player.addWidget(self.progress_xp)
        gb_player.setLayout(v_player)
        vbox.addWidget(gb_player)

        gb_chem = QGroupBox("افزودن ماده به بشر")
        frm = QFormLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("جستجو (نام یا فرمول)...")
        self.search_box.textChanged.connect(self.filter_chemicals)
        self.combo_chem = QComboBox()
        self.populate_chemicals()
        self.combo_chem.currentIndexChanged.connect(self.update_chem_details)

        self.spin_vol = QDoubleSpinBox()
        self.spin_vol.setRange(0.1, 500)  # حداکثر مقدار در هر بار اضافه کردن
        self.spin_vol.setValue(50)
        self.spin_vol.setSuffix(" mL")

        btn_add = QPushButton("➕ افزودن به ظرف")
        btn_add.clicked.connect(self.action_add)
        btn_add.setStyleSheet("background-color: #a6e3a1; color: #1e1e2e; font-size: 14px;")

        frm.addRow("جستجو:", self.search_box)
        frm.addRow("انتخاب ماده:", self.combo_chem)
        self.lbl_amount_text = QLabel("مقدار:")
        frm.addRow(self.lbl_amount_text, self.spin_vol)
        frm.addRow(btn_add)
        gb_chem.setLayout(frm)
        vbox.addWidget(gb_chem)

        gb_temp = QGroupBox("کنترل دمای ظرف")
        h_temp = QHBoxLayout()
        btn_heat = QPushButton("🔥 حرارت دادن")
        btn_heat.setStyleSheet("background-color: #f38ba8; color: #1e1e2e;")
        btn_heat.clicked.connect(lambda: self.engine.change_temperature(15))
        btn_cool = QPushButton("🧊 خنک کردن")
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
        vbox.addWidget(QLabel("📜 گزارش آزمایشگاه:"))
        vbox.addWidget(self.txt_log)

        btn_wash = QPushButton("🚿 شست و شوی کامل ظرف")
        btn_wash.setStyleSheet("background-color: #89dceb; color: #1e1e2e; font-weight: bold;")
        btn_wash.clicked.connect(self.action_wash)
        vbox.addWidget(btn_wash)

        btn_hard_reset = QPushButton("⚠️ شروع مجدد بازی (Reset)")
        btn_hard_reset.setStyleSheet("background-color: #ff5555; color: white;")
        btn_hard_reset.clicked.connect(self.action_hard_reset)
        vbox.addWidget(btn_hard_reset)

        # پنل وسط (ظرف آزمایش)
        panel_vis = QFrame()
        panel_vis.setStyleSheet("background-color: #181825; border-radius: 10px;")
        v_vis = QVBoxLayout(panel_vis)

        title_vis = QLabel("ظرف واکنش (1000 mL)")
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

        # پنل چپ (تب‌ها)
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
        self.table_disc = QTableWidget();
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

        # بخش فرمول تجربی مخلوط
        mix_frame = QFrame()
        mix_frame.setStyleSheet("background-color: #313244; border-radius: 8px; padding: 10px;")
        mix_layout = QHBoxLayout(mix_frame)

        lbl_title = QLabel("فرمول تجربی مخلوط (استوکیومتری کل): ")
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
        t.setHorizontalHeaderLabels(["نام", "فرمول", "نوع", "رنگ", "مولاریته (M)", "pH", "گرما (Heat)"])
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
        gb = QGroupBox("مشخصات ماده انتخاب شده");
        gl = QGridLayout(gb)
        self.lbl_d_name = QLabel("-");
        self.lbl_d_form = QLabel("-");
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
        for k, v in sorted(CHEMILAB_DB.items(), key=lambda x: x[1]['name']):
            if t in v['name'].lower() or t in v['formula'].lower() or t in k:
                self.combo_chem.addItem(f"{v['name']} ({v['formula']})", k)
        self.combo_chem.blockSignals(False)
        if self.combo_chem.count() > 0: self.combo_chem.setCurrentIndex(0); self.update_chem_details()

    def update_chem_details(self):
        k = self.combo_chem.currentData()
        if k and k in CHEMILAB_DB:
            d = CHEMILAB_DB[k]
            self.lbl_d_name.setText(d.get('name', ''))
            self.lbl_d_form.setText(ChemicalCalculator.to_subscript(d.get('formula', '')))
            ptype = get_persian_type(d.get('type', ''))
            self.lbl_d_type.setText(ptype)

            ctype = d.get('type', '')
            if "Solid" in ctype or "Metal" in ctype or "Salt" in ctype or "Powder" in ctype:
                self.spin_vol.setSuffix(" g")
            else:
                self.spin_vol.setSuffix(" mL")

    def handle_reaction_result(self, disc):
        if not disc: return
        name, xp, status = disc
        if status == "new":
            self.timer.stop()
            self.txt_log.append(f"✨ واکنش جدید کشف شد: {name}")
            self.container.trigger_reaction_animation()
            self.update_player_stats()
            self.update_discoveries_table()
            self.update_wiki_table()
            QMessageBox.information(self, "کشف!", f"تبریک! شما واکنش جدیدی کشف کردید:\n{name}\nامتیاز کسب شده: {xp}")
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
            self.txt_log.append("یک لایه حذف شد.")

    def action_wash(self):
        self.engine.reset()
        self.container.update_layers([])
        self.update_contents_ui()
        self.txt_log.append("ظرف کاملاً شسته شد.")

    def action_hard_reset(self):
        if QMessageBox.question(self, "ریست", "آیا از پاک کردن کامل پیشرفت مطمئن هستید؟",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.engine.hard_reset()
            self.container.update_layers([])
            self.update_player_stats()
            self.update_contents_ui()
            self.update_discoveries_table()
            self.update_wiki_table()
            self.txt_log.clear()
            self.check_login()  # دوباره نام را می پرسد اگر لازم باشد

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

        f = self.engine.get_mixture_empirical_formula()
        self.lbl_mix.setText(f"{f}")

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
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
    )
    from PyQt5.QtCore import Qt, QTimer, QRectF, QPropertyAnimation, pyqtProperty, QEasingCurve, QPointF
    from PyQt5.QtGui import QFont, QColor, QPainter, QPen, QLinearGradient, QPainterPath, QBrush
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
except ImportError as e:
    print(f"Error: {e}")
    sys.exit(0)

CUSTOM_REACTIONS = {}
CHEMILAB_DB = {}


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
    if not key:
        return ""
    key = re.sub(
        r'\s+(heat|light|conc|dilute|steam|aq|excess|limited|slow|cold|hot|dissolved|decay|solid|liquid|gas|catalyst).*',
        '', str(key), flags=re.IGNORECASE
    )
    key = re.sub(r'\((s|g|l|aq|solid|gas|liquid)\)', '', key, flags=re.IGNORECASE)
    return key.strip().lower()


def load_databases():
    db_path = get_db_path()
    if not os.path.exists(db_path):
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
                "reactants": parse_db_list(i[2]),
                "products": parse_db_list(i[3]),
                "desc": str(i[4]),
                "xp": xp_val,
                "temp_min": temp_min_val,
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
                "name": str(i[1]),
                "type": str(i[3]),
                "pH": ph_val,
                "molarity": mol_val,
                "heat": heat_val,
                "color": str(i[7]),
                "formula": str(i[8]),
            }
        connection.close()
    except:
        pass


load_databases()

FONT_NAME = "Tahoma"
APP_STYLE = """
QMainWindow { background-color: #0d0d14; }
QWidget { color: #cdd6f4; font-family: 'Tahoma', sans-serif; font-size: 13px; }
QGroupBox { border: 2px solid #313244; border-radius: 8px; margin-top: 15px; background-color: #161622; font-weight: bold; }
QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top center; padding: 0 10px; background-color: #0d0d14; color: #89b4fa; border-radius: 4px; }
QPushButton { background-color: #313244; border: 1px solid #45475a; border-radius: 6px; padding: 8px 16px; color: #cdd6f4; font-weight: bold; }
QPushButton:hover { background-color: #45475a; border: 1px solid #89b4fa; }
QPushButton:pressed { background-color: #11111b; border: 2px solid #fab387; padding-top: 10px; } 
QPushButton:checked { background-color: #a6e3a1; color: #11111b; border: 2px solid #94e2d5; }
QLineEdit { background-color: #1e1e2e; border: 1px solid #45475a; border-radius: 4px; padding: 5px; color: #a6e3a1; font-weight: bold; }
QComboBox, QDoubleSpinBox, QSpinBox { background-color: #1e1e2e; border: 1px solid #45475a; border-radius: 4px; padding: 5px; color: #cdd6f4; }
QListWidget { background-color: #11111b; border: 1px solid #313244; border-radius: 6px; color: #cdd6f4; font-size: 14px; }
QTableWidget { background-color: #11111b; gridline-color: #313244; color: #cdd6f4; border: 1px solid #313244; border-radius: 6px; }
QHeaderView::section { background-color: #1e1e2e; padding: 6px; border: 1px solid #313244; color: #f9e2af; font-weight: bold; }
QTextEdit { background-color: #11111b; border: 1px solid #313244; border-radius: 4px; color: #a6e3a1; }
QTabWidget::pane { border: 1px solid #313244; background: #161622; }
QTabBar::tab { background: #313244; color: #cdd6f4; padding: 8px 12px; margin-right: 2px; border-top-left-radius: 4px; border-top-right-radius: 4px; }
QTabBar::tab:selected { background: #89b4fa; color: #1e1e2e; font-weight: bold; }
QProgressBar { border: 2px solid #45475a; border-radius: 5px; text-align: center; color: white; background-color: #1e1e2e; }
QProgressBar::chunk { background-color: #fab387; width: 20px; }
QScrollArea { border: none; background-color: transparent; }
QDialog { background-color: #161622; }
QPushButton { font-size: 14px; padding: 10px 20px; }
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
    return TYPE_MAP.get(eng_type, eng_type)


class ChemicalCalculator:
    SUBSCRIPTS = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")

    @staticmethod
    def to_subscript(text):
        if not text: return ""
        return text.translate(ChemicalCalculator.SUBSCRIPTS)

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

        title = QLabel("🧪 آزمایشگاه شیمی‌لَب V40")
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
        self.notes = ""
        self.visual_layers = []
        self.layer_id_counter = 0
        self.max_capacity = 1000.0
        self.speed_multiplier = 1.0
        self.is_broken = False
        self.load_data()
        self.reset()

    def reset(self):
        self.total_volume = 0.0
        self.moles_h = 0.0
        self.moles_oh = 0.0
        self.temp_c = 25.0
        self.contents = {}
        self.visual_layers = []
        self.is_broken = False
        self.last_update = time.time()

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
            except:
                pass

    def save_data(self):
        save_path = get_save_path()
        try:
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump({
                    "score": self.score,
                    "level": self.level,
                    "discovered": list(self.discovered),
                    "player_name": self.player_name,
                    "notes": self.notes
                }, f, ensure_ascii=False)
        except:
            pass

    def set_player_name(self, name):
        self.player_name = name
        self.save_data()

    def filter_solids(self):
        if self.is_broken: return []
        removed = []
        new_layers = []
        for layer in self.visual_layers:
            ctype = CHEMILAB_DB.get(layer['key'], {}).get('type', '')
            if any(x in ctype for x in ["Solid", "Metal", "Salt", "Powder", "Precipitate", "Alloy", "Mineral"]):
                removed.append(layer['name'])
                self.total_volume -= layer['amount']
                if layer['key'] in self.contents:
                    del self.contents[layer['key']]
            else:
                new_layers.append(layer)
        self.visual_layers = new_layers
        if self.total_volume < 0: self.total_volume = 0
        return removed

    def add_chemical(self, key, amount, custom_molarity=None):
        if self.is_broken:
            return "❌ ظرف شکسته است! ابتدا آن را بشویید.", False

        key = key.lower()
        if key not in CHEMILAB_DB: return "خطا: ماده یافت نشد", False
        data = CHEMILAB_DB[key]
        chem_type = data.get('type', '')

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
            'id': self.layer_id_counter,
            'key': key,
            'name': data['name'],
            'amount': amount,
            'color': data['color'],
            'type': get_persian_type(chem_type),
            'moles': added_moles
        })

        if ph_val < 7:
            self.moles_h += added_moles * (1 if ph_val < 2 else 0.1)
        elif ph_val > 7:
            self.moles_oh += added_moles * (1 if ph_val > 12 else 0.1)

        result_msg = f"افزوده شد: {data['name']} ({amount} {unit_display})"
        is_overflow = False

        if self.total_volume > self.max_capacity:
            is_overflow = True
            ratio = self.max_capacity / self.total_volume
            self.total_volume = self.max_capacity
            for l in self.visual_layers:
                l['amount'] *= ratio
                l['moles'] *= ratio
            for k in self.contents:
                self.contents[k] *= ratio
            self.moles_h *= ratio
            self.moles_oh *= ratio
            result_msg += " ⚠️ ظرف سرریز شد!"

        return result_msg, is_overflow

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
                return True
        return False

    def change_temperature(self, delta):
        self.temp_c += delta

    def update_physics(self):
        current_time = time.time()
        dt_real = current_time - self.last_update
        self.last_update = current_time
        dt = dt_real * self.speed_multiplier

        if self.speed_multiplier == 0: return

        if self.is_broken:
            # Cool down to room temp rapidly if broken
            diff = self.temp_c - 25.0
            self.temp_c -= diff * 0.1 * dt
            return

        room_temp = 25.0
        cooling_rate = 0.05
        diff = self.temp_c - room_temp
        if abs(diff) > 0.1:
            self.temp_c -= diff * cooling_rate * dt

        # Evaporation / Boiling
        if self.temp_c >= 100.0 and self.total_volume > 0:
            evap_rate = (self.temp_c - 100.0) * 0.5 * dt
            if evap_rate > 0:
                liquid_layers = [l for l in self.visual_layers if
                                 "مایع" in l['type'] or "آب" in l['type'] or "محلول" in l['type'] or "اسید" in l[
                                     'type'] or "باز" in l['type']]
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

        # Explosion checks
        if self.temp_c > 500.0 and not self.is_broken:
            self.is_broken = True
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
                    if name not in self.discovered:
                        self.discovered.add(name)
                        self.score += rxn["xp"]
                        if self.score >= self.level * 100: self.level += 1
                        self.save_data()
                        self.temp_c += 15.0
                        return (name, rxn["xp"], "new")
                    else:
                        found_old = (name, 0, "old")
        return found_old

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

        self.bubbles = []
        self.particles = []
        self.steam_particles = []
        self.overflow_particles = []
        self.shards = []

        self.plate_state = "off"
        self.plate_glow_alpha = 0
        self.plate_glow_dir = 5
        self.stirrer_on = False
        self.stirrer_angle = 0.0
        self.is_exploding = False

    def set_plate_state(self, state):
        self.plate_state = state
        if state != "off":
            QTimer.singleShot(4000, lambda: self.set_plate_state("off"))

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
                'x': cx, 'y': cy,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'rot': random.uniform(0, 360),
                'vrot': random.uniform(-30, 30),
                'size': random.uniform(5, 25)
            })

    def process_animations(self):
        if self.engine.is_broken and not self.is_exploding:
            self.trigger_explosion()
        if not self.engine.is_broken:
            self.is_exploding = False

        dt_mult = self.engine.speed_multiplier
        if dt_mult <= 0: dt_mult = 0  # Paused

        if self.plate_state != "off" and dt_mult > 0:
            self.plate_glow_alpha += self.plate_glow_dir * dt_mult
            if self.plate_glow_alpha >= 200:
                self.plate_glow_alpha = 200;
                self.plate_glow_dir = -8
            elif self.plate_glow_alpha <= 60:
                self.plate_glow_alpha = 60;
                self.plate_glow_dir = 8
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

            # Steam Emission
            if self.engine.temp_c >= 100.0 and total_amount > 0 and not self.engine.is_broken:
                if random.random() < 0.4 * dt_mult:
                    self.steam_particles.append({
                        'x': random.uniform(margin_x, self.width() - margin_x),
                        'y': h - margin_y - 30 - (total_amount * (container_h / self.engine.max_capacity)),
                        'vy': random.uniform(1.0, 4.0),
                        'life': 100,
                        'size': random.uniform(10, 30)
                    })

            # Bubbles
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

    def trigger_reaction_animation(self):
        self.anim_flash.setStartValue(1.0)
        self.anim_flash.setEndValue(0.0)
        self.anim_flash.start()

        h = self.height()
        margin_x, margin_y = 100, 30
        base_y = h - margin_y - 30
        total_amount = self.engine.total_volume
        if total_amount > 0:
            scale = (h - 2 * margin_y - 30) / self.engine.max_capacity
            base_y -= (total_amount * scale)

        for _ in range(50):
            self.particles.append({
                'x': random.uniform(margin_x + 20, self.width() - margin_x - 20),
                'y': base_y,
                'vx': random.uniform(-4.0, 4.0),
                'vy': random.uniform(3.0, 8.0),
                'life': random.randint(20, 70),
                'color': random.choice([QColor(255, 200, 50), QColor(0, 255, 255), QColor(255, 100, 255)])
            })

    def trigger_overflow(self):
        w, h = self.width(), self.height()
        margin_x, margin_y = 100, 30
        top_y = margin_y
        for _ in range(15):
            self.overflow_particles.append({
                'x': margin_x - random.uniform(0, 15),
                'y': top_y + random.uniform(0, 15),
                'vy': random.uniform(3, 6),
                'life': 80, 'size': random.uniform(4, 8)
            })
            self.overflow_particles.append({
                'x': w - margin_x + random.uniform(0, 15),
                'y': top_y + random.uniform(0, 15),
                'vy': random.uniform(3, 6),
                'life': 80, 'size': random.uniform(4, 8)
            })

    def mouseMoveEvent(self, event):
        if self.engine.is_broken:
            QToolTip.hideText()
            return

        y_pos = event.y()
        w, h = self.width(), self.height()
        margin_x, margin_y = 100, 30
        container_h = h - 2 * margin_y - 30
        scale = container_h / self.engine.max_capacity

        current_y = h - margin_y - 30
        hovered_layer = None

        def layer_density(layer):
            t = layer['type']
            if any(x in t for x in ["جامد", "فلز", "رسوب", "پودر", "آلیاژ"]): return 10
            if "گاز" in t: return 0.1
            return 1.0

        sorted_layers = sorted(self.engine.visual_layers, key=layer_density, reverse=True)

        for layer in sorted_layers:
            layer_h = layer['amount'] * scale
            top_y = current_y - layer_h
            if top_y <= y_pos <= current_y and margin_x <= event.x() <= w - margin_x:
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
        margin_x, margin_y = 100, 30

        plate_height = 25
        container_rect = QRectF(margin_x, margin_y, w - 2 * margin_x, h - 2 * margin_y - plate_height)
        scale = container_rect.height() / self.engine.max_capacity

        # Controls UI Draw
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
                if any(x in t for x in ["جامد", "فلز", "رسوب", "پودر", "آلیاژ"]): return 10
                if "گاز" in t: return 0.1
                return 1.0

            sorted_layers = sorted(self.engine.visual_layers, key=layer_density, reverse=True)

            if total_amount > 0:
                for layer in sorted_layers:
                    layer_h = layer['amount'] * scale
                    if layer_h <= 0: continue
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
                    current_y -= layer_h

            painter.setPen(Qt.NoPen)
            for b in self.bubbles:
                painter.setBrush(QColor(255, 255, 255, 120))
                painter.drawEllipse(QRectF(b['x'], b['y'], b['size'], b['size']))

            if total_amount > 0 and self.engine.visual_layers:
                center_x = container_rect.center().x()
                bottom_y = container_rect.bottom() - 5
                painter.save()
                painter.translate(center_x, bottom_y)
                painter.rotate(self.stirrer_angle)
                painter.setBrush(QColor(220, 220, 220))
                painter.setPen(QPen(QColor(100, 100, 100), 1))
                painter.drawRoundedRect(QRectF(-15, -4, 30, 8), 4, 4)
                painter.restore()

            glass_pen = QPen(QColor(200, 220, 255, 180), 3)
            painter.setPen(glass_pen)
            painter.setBrush(Qt.NoBrush)
            path = QPainterPath()
            path.moveTo(container_rect.topLeft())
            path.lineTo(container_rect.bottomLeft())
            path.lineTo(container_rect.bottomRight())
            path.lineTo(container_rect.topRight())
            painter.drawPath(path)

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
            step_val = 100
            for val in range(0, int(self.engine.max_capacity) + 1, step_val):
                if val == 0: continue
                y_ratio = val / self.engine.max_capacity
                y_coord = container_rect.bottom() - (y_ratio * container_rect.height())
                painter.drawLine(int(container_rect.left()), int(y_coord), int(container_rect.left() + 15),
                                 int(y_coord))
                painter.drawText(int(container_rect.left()) - 45, int(y_coord) + 5, f"{val}")
            painter.drawText(int(container_rect.left()) - 45, int(container_rect.top()) - 5, "mL/g")

        else:
            # Draw Broken Glass
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

        # Hotplate
        plate_rect = QRectF(container_rect.left() - 20, container_rect.bottom() + 2, container_rect.width() + 40,
                            plate_height)
        painter.setPen(Qt.NoPen)
        plate_grad = QLinearGradient(plate_rect.topLeft(), plate_rect.bottomLeft())
        plate_grad.setColorAt(0, QColor(40, 42, 54))
        plate_grad.setColorAt(1, QColor(20, 22, 30))
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

        # Draw Particles
        for p in self.particles:
            alpha = int(255 * (p['life'] / 70.0))
            c = QColor(p['color'])
            c.setAlpha(max(0, min(255, alpha)))
            painter.setBrush(c)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(p['x'], p['y']), 3, 3)

        for sp in self.steam_particles:
            alpha = int(120 * (sp['life'] / 100.0))
            painter.setBrush(QColor(220, 220, 220, max(0, min(255, alpha))))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(sp['x'], sp['y']), sp['size'], sp['size'])

        for op in self.overflow_particles:
            painter.setBrush(QColor(100, 150, 255, 200))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(op['x'], op['y']), op['size'], op['size'])

        if self._flash_opacity > 0.01:
            fc = QColor(255, 255, 200, int(self._flash_opacity * 200))
            painter.setBrush(fc)
            painter.setPen(Qt.NoPen)
            painter.drawRect(self.rect())

    def draw_thermometer(self, painter, rect):
        tx = rect.right() + 30
        ty = rect.top()
        th = rect.height()
        tw = 12
        painter.setPen(QPen(QColor(100, 100, 100), 2))
        painter.setBrush(QColor(30, 30, 40))
        painter.drawRoundedRect(QRectF(tx, ty, tw, th), 6, 6)
        painter.drawEllipse(QRectF(tx - 4, ty + th - 5, 20, 20))

        min_t, max_t = -50, 600
        temp = max(min_t, min(self.engine.temp_c, max_t))
        ratio = (temp - min_t) / (max_t - min_t)

        fill_h = th * ratio
        fill_y = ty + th - fill_h

        fill_color = QColor(255, 50, 50) if temp > 50 else (QColor(50, 150, 255) if temp < 0 else QColor(255, 100, 50))
        painter.setPen(Qt.NoPen)
        painter.setBrush(fill_color)
        painter.drawRoundedRect(QRectF(tx + 2, fill_y, tw - 4, fill_h), 4, 4)
        painter.drawEllipse(QRectF(tx - 2, ty + th - 3, 16, 16))

        painter.setPen(QPen(QColor(200, 200, 200), 1))
        for i in range(0, max_t + 1, 100):
            r = (i - min_t) / (max_t - min_t)
            y = ty + th - (th * r)
            painter.drawLine(int(tx + tw), int(y), int(tx + tw + 5), int(y))

        painter.setPen(QColor(200, 200, 220))
        painter.drawText(int(tx - 5), int(ty - 10), "°C")

    def draw_ph_strip(self, painter, rect):
        px = rect.left() - 40
        py = rect.top()
        ph = rect.height()
        pw = 10

        grad = QLinearGradient(0, py, 0, py + ph)
        grad.setColorAt(0, QColor(128, 0, 128))
        grad.setColorAt(0.5, QColor(0, 255, 0))
        grad.setColorAt(1, QColor(255, 0, 0))

        painter.setPen(QPen(QColor(100, 100, 100), 1))
        painter.setBrush(grad)
        painter.drawRect(QRectF(px, py, pw, ph))

        current_ph = self.engine.get_ph()
        ratio = current_ph / 14.0
        arrow_y = py + ph - (ph * ratio)

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
        self.setWindowTitle("آزمایشگاه شیمی پیشرفته - شیمی‌لَب (نسخه 40)")
        self.resize(1500, 950)

        self.engine = LabEngine()
        self.check_login()

        self.data_time, self.data_ph, self.data_temp = [], [], []

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
                name = dlg.get_name()
                self.engine.set_player_name(name)

    def start_simulation(self):
        self.timer.start(50)

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)

        panel_ctrl = QFrame()
        panel_ctrl.setFixedWidth(400)
        vbox = QVBoxLayout(panel_ctrl)

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
        self.progress_xp.setStyleSheet("QProgressBar::chunk { background-color: #cba6f7; }")
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
        self.search_box.setPlaceholderText("🔍 جستجو (نام یا فرمول)...")
        self.search_box.setStyleSheet("font-size: 16px;")
        self.search_box.textChanged.connect(self.filter_chemicals)

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

        self.btn_titrate = QPushButton("💧 قطره‌چکان")
        self.btn_titrate.setCheckable(True)
        self.btn_titrate.clicked.connect(self.action_toggle_titration)
        self.btn_titrate.setStyleSheet("background-color: #89b4fa; color: #1e1e2e;")

        h_btn_add.addWidget(btn_add)
        h_btn_add.addWidget(self.btn_titrate)

        frm.addRow("جستجو:", self.search_box)
        frm.addRow("ماده:", self.combo_chem)
        frm.addRow(h_vol_mol)
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
        self.btn_stirrer = QPushButton("🌪️ همزن مغناطیسی")
        self.btn_stirrer.setStyleSheet("background-color: #cba6f7; color: #1e1e2e;")
        self.btn_stirrer.setCheckable(True)
        self.btn_stirrer.clicked.connect(self.action_toggle_stirrer)

        btn_filter = QPushButton("⚗️ فیلتر جامدات")
        btn_filter.setStyleSheet("background-color: #f9e2af; color: #1e1e2e;")
        btn_filter.clicked.connect(self.action_filter)

        h_extra.addWidget(self.btn_stirrer)
        h_extra.addWidget(btn_filter)
        v_tools.addLayout(h_extra)

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

        btn_wash = QPushButton("🚿 شست‌وشو و تعویض ظرف")
        btn_wash.setStyleSheet("background-color: #89dceb; color: #1e1e2e; font-weight: bold; font-size: 16px;")
        btn_wash.clicked.connect(self.action_wash)
        vbox.addWidget(btn_wash)

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
        self.tabs.addTab(self.create_notes_tab(), "📝 یادداشت‌ها")
        self.tabs.addTab(self.create_contents_tab(), "🧪 محتویات")
        self.tabs.addTab(self.create_graph_tab(), "📈 نمودار")
        self.tabs.addTab(self.create_discoveries_tab(), "🏆 کشف‌ها")
        self.tabs.addTab(self.create_wiki_tab(), "📖 دانشنامه")
        self.tabs.addTab(self.create_datasheet_tab(), "📚 لیست مواد")

        self.split = QSplitter(Qt.Horizontal)
        self.split.addWidget(panel_ctrl)
        self.split.addWidget(panel_vis)
        self.split.addWidget(self.tabs)
        self.split.setSizes([400, 500, 600])
        layout.addWidget(self.split)

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

    def action_toggle_titration(self):
        if self.btn_titrate.isChecked():
            self.btn_titrate.setText("⏹️ توقف قطره‌چکان")
            self.btn_titrate.setStyleSheet("background-color: #f38ba8; color: #1e1e2e;")
        else:
            self.btn_titrate.setText("💧 قطره‌چکان")
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

    def create_notes_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        lbl_hint = QLabel("📝 دفترچه یادداشت و صدور گزارش:")
        lbl_hint.setStyleSheet("font-size: 16px; font-weight: bold; color: #cdd6f4;")
        l.addWidget(lbl_hint)

        self.txt_notes = QTextEdit()
        self.txt_notes.setStyleSheet("""
            QTextEdit { font-size: 18px; background-color: #1e1e2e; color: #cdd6f4; 
            padding: 15px; border-radius: 8px; font-weight: 500; line-height: 1.8; border: 2px solid #89b4fa; }
        """)
        self.txt_notes.setPlaceholderText("یادداشت‌های خود را بنویسید...")
        self.txt_notes.setText(self.engine.notes)
        self.txt_notes.textChanged.connect(self.save_notes)
        l.addWidget(self.txt_notes)

        btn_export = QPushButton("📥 صدور گزارش کامل آزمایشگاه (TXT)")
        btn_export.setStyleSheet("background-color: #a6e3a1; color: #1e1e2e; font-weight: bold;")
        btn_export.clicked.connect(self.export_report)
        l.addWidget(btn_export)
        return w

    def export_report(self):
        filename, _ = QFileDialog.getSaveFileName(self, "ذخیره گزارش آزمایشگاه", "LabReport.txt", "Text Files (*.txt)")
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("=== گزارش سایبری آزمایشگاه شیمی‌لَب ===\n")
                    f.write(f"تاریخ و زمان: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"شیمیدان: {self.engine.player_name} (سطح {self.engine.level})\n")
                    f.write("-" * 40 + "\n\n")
                    f.write("🧪 وضعیت فعلی ظرف:\n")
                    f.write(f"دما: {self.engine.temp_c:.1f} °C\n")
                    f.write(f"میزان pH: {self.engine.get_ph():.2f}\n")
                    f.write(f"فرمول تجربی مخلوط: {self.engine.get_mixture_empirical_formula()}\n")
                    f.write("\nمحتویات:\n")
                    for layer in self.engine.visual_layers:
                        f.write(f"- {layer['name']} ({layer['amount']} mL/g)\n")
                    f.write("\n" + "-" * 40 + "\n\n")
                    f.write("📝 یادداشت‌های ثبت شده:\n")
                    f.write(self.txt_notes.toPlainText())
                QMessageBox.information(self, "موفق", "گزارش با موفقیت ذخیره شد.")
            except Exception as e:
                QMessageBox.critical(self, "خطا", f"خطا در ذخیره گزارش:\n{str(e)}")

    def save_notes(self):
        self.engine.notes = self.txt_notes.toPlainText()
        self.engine.save_data()

    def create_about_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)

        about_text = """شیمی‌لَب: شبیه‌ساز پیشرفته آزمایشگاه شیمی (نسخه ۴۰ - نسخه سایبری)

امکانات ویژه این نسخه:
🌡️ تبخیر و جوشش واقعی (بخار شدن در دمای > ۱۰۰)
❄️ افکت یخ‌زدگی (تشکیل برفک در دمای < ۰)
⚖️ سیستم چگالی هوشمند (ته‌نشینی رسوبات و جامدات)
💥 شکستن ظرف (انفجار در دمای > ۵۰۰)
💧 سیستم قطره‌چکان (تیتراسیون قطره‌ای)
⏱️ ماشین زمان (کنترل سرعت واکنش)
🧪 غلظت سفارشی برای مواد
🌡️ نشانگرهای گرافیکی pH و دماسنج
🌊 انیمیشن سرریز شدن از ظرف
🎨 رابط کاربری سایبرپانکی و پیشرفته
        """
        lbl = QLabel(about_text)
        lbl.setWordWrap(True)
        lbl.setStyleSheet("font-size: 16px; line-height: 1.8; color: #89b4fa; padding: 10px; font-weight: bold;")
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
            lbl_r.setWordWrap(True)
            lbl_r.setTextFormat(Qt.RichText)
            self.table_wiki.setCellWidget(i, 1, lbl_r)
            lbl_p = QLabel(" + ".join([self.get_state_color_text(p) for p in products_list]))
            lbl_p.setWordWrap(True)
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
            self.spin_molarity.setValue(float(d.get('molarity', 0.1)))

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
        try:
            k = self.combo_chem.currentData()
            if not k: return
            msg, overflow = self.engine.add_chemical(k, self.spin_vol.value(), self.spin_molarity.value())
            self.txt_log.append(msg)
            if overflow: self.container.trigger_overflow()
            self.update_contents_ui()
            self.handle_reaction_result(self.engine.check_reactions())
        except Exception as e:
            pass

    def remove_item(self, layer_id):
        if self.engine.remove_layer(layer_id):
            self.update_contents_ui()
            self.txt_log.append("یک لایه حذف شد.")

    def action_wash(self):
        self.engine.reset()
        self.btn_stirrer.setChecked(False)
        self.container.set_stirrer(False)
        self.update_contents_ui()
        self.txt_log.append("ظرف تعویض و کاملاً تمیز شد.")

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
        try:
            # Titration Logic
            if self.btn_titrate.isChecked() and self.engine.speed_multiplier > 0:
                if self.engine.is_broken:
                    self.btn_titrate.setChecked(False)
                    self.action_toggle_titration()
                else:
                    k = self.combo_chem.currentData()
                    if k:
                        msg, overflow = self.engine.add_chemical(k, 0.5 * self.engine.speed_multiplier,
                                                                 self.spin_molarity.value())
                        if overflow: self.container.trigger_overflow()
                        self.update_contents_ui()

            # Physics Update
            self.engine.update_physics()

            if self.engine.is_broken and "ظرف شکسته" not in self.txt_log.toPlainText():
                self.txt_log.append("💥 دما بیش از حد بالا رفت و ظرف ترکید! سریعاً آن را بشویید.")

            if not hasattr(self, 'st'): self.st = time.time()
            t = time.time() - self.st
            ph = self.engine.get_ph()
            temp = self.engine.temp_c

            self.lbl_ph_display.setText(f"pH: {ph:.2f}" if not self.engine.is_broken else "pH: ---")
            self.lbl_temp_display.setText(f"{temp:.1f} °C")

            disc = self.engine.check_reactions()
            self.handle_reaction_result(disc)

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
            pass


if __name__ == '__main__':
    if hasattr(Qt, 'AA_EnableHighDpiScaling'): QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'): QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    app.setLayoutDirection(Qt.RightToLeft)
    app.setFont(QFont(FONT_NAME, 10))
    app.setStyleSheet(APP_STYLE)
    w = ModernLabWindow()
    w.show()
    sys.exit(app.exec())
import json
import sys
import time
import re
import os
import math
from collections import Counter

try:
    import matplotlib

    matplotlib.use("Qt5Agg")
    from PyQt5.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QLabel, QPushButton, QComboBox, QFrame, QGroupBox, QTextEdit,
        QTabWidget, QMessageBox, QDoubleSpinBox, QFormLayout, QTableWidget,
        QTableWidgetItem, QHeaderView, QSplitter, QLineEdit, QGridLayout,
        QListWidget, QSpinBox, QProgressBar, QScrollArea
    )
    from PyQt5.QtCore import Qt, QTimer, QRectF, QPropertyAnimation, pyqtProperty, QEasingCurve
    from PyQt5.QtGui import QFont, QColor, QPainter, QPen, QLinearGradient, QPainterPath
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
except ImportError as e:
    print(f"Error: {e}")
    print("Please install required libraries: pip install PyQt5 matplotlib")
    sys.exit(1)

# =============================================================================
# دیتابیس داخلی برنامه
# شما می‌توانید مواد و واکنش‌های خود را در این بخش وارد کنید.
# =============================================================================

CHEMILAB_DB = {
    "h2o": {"name": "آب", "formula": "H2O", "molarity": 55.5, "pH": 7.0, "color": "#E0FFFF", "heat": 0.0,
            "type": "Solvent"},
    "h2so4": {"name": "سولفوریک اسید", "formula": "H2SO4", "molarity": 18.0, "pH": 1.0, "color": "#FFFFFF",
              "heat": 25.0, "type": "Strong Acid"},
    "naoh": {"name": "سدیم هیدروکسید", "formula": "NaOH", "molarity": 10.0, "pH": 14.0, "color": "#F0F0F0",
             "heat": 10.0, "type": "Strong Base"},
    "cuso4": {"name": "مس(II) سولفات", "formula": "CuSO4", "molarity": 0.5, "pH": 4.0, "color": "#0000FF", "heat": -5.0,
              "type": "Salt"},
    "fe": {"name": "آهن", "formula": "Fe", "molarity": 1.0, "pH": 7.0, "color": "#808080", "heat": 0.0,
           "type": "Metal"},
}

CUSTOM_REACTIONS = {
    "خنثی‌سازی اسید و باز قوی": {
        "reactants": ["h2so4", "naoh"],
        "products": ["na2so4", "h2o"],
        "temp_min": 0,
        "xp": 50
    }
}

# =============================================================================

# ----------------- تنظیمات گرافیکی -----------------
FONT_NAME = "Tahoma"
APP_STYLE = """
QMainWindow { background-color: #1e1e2e; }
QWidget { color: #cdd6f4; font-family: 'Tahoma', sans-serif; font-size: 13px; }
QGroupBox { border: 2px solid #313244; border-radius: 8px; margin-top: 10px; background-color: #181825; font-weight: bold; }
QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top center; padding: 0 10px; background-color: #1e1e2e; color: #89b4fa; }
QPushButton { background-color: #45475a; border: 1px solid #313244; border-radius: 6px; padding: 8px 16px; color: white; font-weight: bold; }
QPushButton:hover { background-color: #585b70; border: 1px solid #89b4fa; }
QPushButton:pressed { background-color: #11111b; border: 2px solid #fab387; padding-top: 10px; } 
QComboBox, QDoubleSpinBox, QLineEdit, QSpinBox { background-color: #313244; border: 1px solid #45475a; border-radius: 4px; padding: 5px; color: white; }
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
"""

TYPE_MAP = {
    "Strong Acid": "مایع (اسید قوی)", "Weak Acid": "مایع (اسید ضعیف)",
    "Strong Base": "مایع (باز قوی)", "Weak Base": "مایع (باز ضعیف)",
    "Acid": "مایع (اسید)", "Base": "مایع (باز)", "Salt": "جامد (نمک)",
    "Gas": "گاز", "Liquid": "مایع", "Solid": "جامد", "Metal": "جامد (فلز)",
    "Oxide": "جامد (اکسید)", "Solvent": "مایع (حلال)", "Element": "جامد (عنصر)",
    "Alcohol": "مایع (الکل)", "Precipitate": "جامد (رسوب)",
    "Halogen": "هالوژن", "Organic Compound": "ترکیب آلی",
    "Complex": "کمپلکس", "Monomer": "مونومر", "Polymer": "پلیمر",
    "Carbide": "کاربید", "Nitride": "نیترید", "Hydride": "هیدرید",
    "Silicide": "سیلیسید", "Radioactive": "رادیواکتیو", "Ion": "یون",
    "Medicine": "دارو", "Explosive": "ماده منفجره", "Catalyst": "کاتالیزور",
    "Sugar": "قند", "Fatty Acid": "اسید چرب", "Amino Acid": "آمینو اسید",
    "Protein": "پروتئین", "Enzyme": "آنزیم", "Alkaloid": "آلکالوئید",
    "Nanomaterial": "نانومواد", "Semiconductor": "نیمه‌هادی",
    "Superconductor": "ابررسانا", "Refrigerant": "مبرد",
    "Pollutant": "آلاینده", "Mineral": "معدنی", "Alloy": "آلیاژ"
}


def get_persian_type(eng_type):
    return TYPE_MAP.get(eng_type, eng_type)


def normalize_key(key):
    key = re.sub(
        r'\s+(heat|light|conc|dilute|steam|aq|excess|limited|slow|cold|hot|dissolved|decay|solid|liquid|gas|catalyst).*',
        '', key, flags=re.IGNORECASE)
    return key.strip().lower()


# ----------------- کلاس‌های محاسباتی -----------------
class ChemicalCalculator:
    SUBSCRIPTS = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")

    @staticmethod
    def to_subscript(text):
        if not text: return ""
        return text.translate(ChemicalCalculator.SUBSCRIPTS)

    @staticmethod
    def parse_formula(formula):
        """تجزیه دقیق فرمول شیمیایی با پشتیبانی از پرانتز"""
        if formula == "Mix" or formula == "-" or formula is None: return Counter()

        temp_formula = formula
        # باز کردن پرانتزها
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
        """محاسبه فرمول تجربی دقیق بر اساس نسبت مولی اتم‌ها"""
        if not atom_moles_counter:
            return "ماده‌ای وجود ندارد"

        # حذف مقادیر بسیار ناچیز (خطای محاسباتی)
        filtered_atoms = {k: v for k, v in atom_moles_counter.items() if v > 1e-9}
        if not filtered_atoms:
            return "-"

        # پیدا کردن کوچکترین مقدار مول برای نرمال‌سازی
        min_mole = min(filtered_atoms.values())

        # محاسبه نسبت‌ها
        ratios = {}
        for k, v in filtered_atoms.items():
            ratios[k] = v / min_mole

        # رند کردن نسبت‌ها به نزدیکترین عدد صحیح اگر خیلی نزدیک باشند
        final_counts = {}
        for k, r in ratios.items():
            # اگر به عدد صحیح نزدیک است (مثلا 1.001 یا 1.999)
            if abs(r - round(r)) < 0.1:
                final_counts[k] = int(round(r))
            else:
                # اگر اعشاری معنادار است (مثلا 1.5)، فعلا با یک رقم اعشار نگه می‌داریم
                final_counts[k] = round(r, 1)

        # مرتب‌سازی عناصر (C اول، H دوم، بقیه الفبایی)
        sorted_elements = []
        keys = list(final_counts.keys())
        if 'C' in keys: sorted_elements.append('C'); keys.remove('C')
        if 'H' in keys: sorted_elements.append('H'); keys.remove('H')
        sorted_elements.extend(sorted(keys))

        formula_str = ""
        for el in sorted_elements:
            count = final_counts[el]
            if count > 0:
                # اگر عدد 1 است، نوشته نمی‌شود
                display_str = "" if count == 1 else str(count)
                formula_str += f"{el}{display_str}"

        return ChemicalCalculator.to_subscript(formula_str)


# ----------------- بشر گرافیکی -----------------
class AnimatedBeaker(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(220, 320)
        self._fluid_height = 0.0
        self._fluid_color = QColor("#E0FFFF")
        self._flash_opacity = 0.0
        self.max_volume = 1000.0

    @pyqtProperty(float)
    def fluidHeight(self):
        return self._fluid_height

    @fluidHeight.setter
    def fluidHeight(self, value):
        self._fluid_height = value;
        self.update()

    @pyqtProperty(QColor)
    def fluidColor(self):
        return self._fluid_color

    @fluidColor.setter
    def fluidColor(self, color):
        self._fluid_color = color;
        self.update()

    @pyqtProperty(float)
    def flashOpacity(self):
        return self._flash_opacity

    @flashOpacity.setter
    def flashOpacity(self, value):
        self._flash_opacity = value;
        self.update()

    def set_target_state(self, current_volume, hex_color):
        target_h = min((current_volume / self.max_volume) * 80.0, 90.0)
        self.anim_h = QPropertyAnimation(self, b"fluidHeight")
        self.anim_h.setDuration(800)
        self.anim_h.setStartValue(self._fluid_height)
        self.anim_h.setEndValue(target_h)
        self.anim_h.setEasingCurve(QEasingCurve.OutCubic)
        self.anim_h.start()

        self.anim_c = QPropertyAnimation(self, b"fluidColor")
        self.anim_c.setDuration(800)
        self.anim_c.setStartValue(self._fluid_color)
        self.anim_c.setEndValue(QColor(hex_color))
        self.anim_c.start()

    def trigger_reaction_animation(self):
        self.anim_flash = QPropertyAnimation(self, b"flashOpacity")
        self.anim_flash.setDuration(600)
        self.anim_flash.setStartValue(1.0)
        self.anim_flash.setEndValue(0.0)
        self.anim_flash.setEasingCurve(QEasingCurve.OutQuad)
        self.anim_flash.start()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        margin_x, margin_y = 30, 20
        beaker_w, beaker_h = w - 2 * margin_x, h - 2 * margin_y
        ellipse_h = 20
        beaker_rect = QRectF(margin_x, margin_y, beaker_w, beaker_h)

        if self._fluid_height > 0:
            fluid_h_px = (self._fluid_height / 100.0) * (beaker_h - ellipse_h)
            fluid_top_y = beaker_rect.bottom() - ellipse_h / 2 - fluid_h_px
            path_fluid = QPainterPath()
            path_fluid.addEllipse(margin_x + 2, beaker_rect.bottom() - ellipse_h - 2, beaker_w - 4, ellipse_h)
            path_fluid.addRect(margin_x + 2, fluid_top_y + ellipse_h / 2, beaker_w - 4, fluid_h_px - ellipse_h / 2)
            painter.setPen(Qt.NoPen)
            fluid_grad = QLinearGradient(margin_x, 0, w - margin_x, 0)
            c = self._fluid_color
            fluid_grad.setColorAt(0, c.darker(120))
            fluid_grad.setColorAt(0.5, c)
            fluid_grad.setColorAt(1, c.darker(120))
            painter.setBrush(fluid_grad)
            painter.drawPath(path_fluid)
            painter.setBrush(c.lighter(115))
            painter.drawEllipse(QRectF(margin_x + 2, fluid_top_y, beaker_w - 4, ellipse_h))

        glass_pen = QPen(QColor(220, 230, 255, 150), 2)
        painter.setPen(glass_pen)
        painter.setBrush(QColor(255, 255, 255, 20))
        path_glass = QPainterPath()
        path_glass.moveTo(margin_x, margin_y + ellipse_h / 2)
        path_glass.lineTo(margin_x, beaker_rect.bottom() - ellipse_h / 2)
        path_glass.arcTo(margin_x, beaker_rect.bottom() - ellipse_h, beaker_w, ellipse_h, 180, -180)
        path_glass.lineTo(beaker_rect.right(), margin_y + ellipse_h / 2)
        path_glass.addEllipse(QRectF(margin_x, margin_y, beaker_w, ellipse_h))
        painter.drawPath(path_glass)

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
        self.discovered = set()
        self.load_data()
        self.reset()

    def reset(self):
        self.total_volume = 0.0
        self.moles_h = 0.0
        self.moles_oh = 0.0
        self.temp_c = 25.0
        self.contents = {}  # {chem_key: moles}
        self.composition_log = {}
        self.dominant_color = "#E0FFFF"
        self.last_update = time.time()

    def hard_reset(self):
        self.score = 0
        self.level = 1
        self.discovered = set()
        if os.path.exists("lab_save.json"):
            try:
                os.remove("lab_save.json")
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
                json.dump({"score": self.score, "level": self.level, "discovered": list(self.discovered)}, f)
        except:
            pass

    def add_chemical(self, key, vol):
        key = key.lower()
        if key not in CHEMILAB_DB: return "خطا در یافتن ماده"
        data = CHEMILAB_DB[key]

        # محاسبه مول افزوده شده: Molarity * Volume(L)
        added_moles = data["molarity"] * (vol / 1000.0)
        self.total_volume += vol
        self.contents[key] = self.contents.get(key, 0) + added_moles
        self.composition_log[key] = self.composition_log.get(key, 0) + vol

        if self.total_volume > 0:
            heat_effect = data["heat"] * (vol / self.total_volume)
            self.temp_c += heat_effect

        if data["pH"] < 7:
            self.moles_h += added_moles * (1 if data["pH"] < 2 else 0.1)
        elif data["pH"] > 7:
            self.moles_oh += added_moles * (1 if data["pH"] > 12 else 0.1)
        self.update_color()
        return f"افزوده شد: {data['name']}"

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
        vol_l = self.total_volume / 1000.0
        h = self.moles_h / vol_l if vol_l else 0
        oh = self.moles_oh / vol_l if vol_l else 0
        if abs(h - oh) < 1e-9: return 7.0
        if h > oh:
            return max(0, min(14, -math.log10(h - oh + 1e-14)))
        else:
            return max(0, min(14, 14 + math.log10(oh - h + 1e-14)))

    def calculate_mixed_color(self):
        if self.total_volume == 0: return "#E0FFFF"
        r, g, b, total_w = 0, 0, 0, 0
        base_w = 0.1 * self.total_volume
        bc = QColor("#E0FFFF")
        r += bc.red() * base_w;
        g += bc.green() * base_w;
        b += bc.blue() * base_w;
        total_w += base_w

        vol_l = self.total_volume / 1000.0
        for k, moles in self.contents.items():
            if moles > 1e-5:
                conc = moles / vol_l
                data = CHEMILAB_DB.get(k)
                if data:
                    c = QColor(data["color"])
                    w_ = conc * 100
                    r += c.red() * w_;
                    g += c.green() * w_;
                    b += c.blue() * w_;
                    total_w += w_

        if total_w == 0: return "#E0FFFF"
        return QColor(int(min(255, r / total_w)), int(min(255, g / total_w)), int(min(255, b / total_w))).name()

    def update_color(self):
        self.dominant_color = self.calculate_mixed_color()

    def get_mixture_empirical_formula(self):
        """
        محاسبه فرمول تجربی مخلوط بر اساس مول‌های واقعی مواد موجود در بشر.
        """
        total_atoms = Counter()

        # حرکت روی تمام موادی که در بشر هستند
        for key, moles in self.contents.items():
            if moles <= 1e-9: continue

            if key in CHEMILAB_DB:
                form = CHEMILAB_DB[key]["formula"]
                # تجزیه فرمول هر ماده به اتم‌های سازنده
                atoms_in_molecule = ChemicalCalculator.parse_formula(form)

                # ضرب تعداد اتم‌ها در تعداد مول آن ماده
                for atom, count in atoms_in_molecule.items():
                    total_atoms[atom] += count * moles

        # تبدیل شمارشگر اتم‌های کل به فرمول فرمت شده
        return ChemicalCalculator.calculate_empirical_from_moles(total_atoms)


# ----------------- رابط کاربری -----------------
class ModernLabWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("آزمایشگاه شیمی پیشرفته - Shimi 32")
        self.resize(1500, 900)
        self.setLayoutDirection(Qt.RightToLeft)

        self.engine = LabEngine()
        self.data_time, self.data_ph, self.data_temp = [], [], []

        self.setup_ui()
        self.update_player_stats()
        self.timer = QTimer()
        self.timer.timeout.connect(self.game_loop)
        self.timer.start(50)

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)

        # پنل راست (کنترل)
        panel_ctrl = QFrame()
        panel_ctrl.setFixedWidth(350)
        vbox = QVBoxLayout(panel_ctrl)

        gb_player = QGroupBox("وضعیت شیمیدان")
        v_player = QVBoxLayout()
        self.lbl_level = QLabel("سطح: 1")
        self.lbl_level.setStyleSheet("color: #fab387; font-size: 16px; font-weight: bold;")
        self.lbl_score = QLabel("امتیاز: 0")
        self.progress_xp = QProgressBar()
        self.progress_xp.setRange(0, 100)
        self.progress_xp.setValue(0)
        v_player.addWidget(self.lbl_level)
        v_player.addWidget(self.lbl_score)
        v_player.addWidget(QLabel("XP:"))
        v_player.addWidget(self.progress_xp)
        gb_player.setLayout(v_player)
        vbox.addWidget(gb_player)

        gb_chem = QGroupBox("افزودن ماده")
        frm = QFormLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("جستجو (نام یا فرمول)...")
        self.search_box.textChanged.connect(self.filter_chemicals)
        self.combo_chem = QComboBox()
        self.populate_chemicals()
        self.combo_chem.currentIndexChanged.connect(self.update_chem_details)
        self.spin_vol = QDoubleSpinBox()
        self.spin_vol.setRange(1, 1000);
        self.spin_vol.setValue(50);
        self.spin_vol.setSuffix(" mL")
        btn_add = QPushButton("افزودن")
        btn_add.clicked.connect(self.action_add)
        btn_add.setStyleSheet("background-color: #a6e3a1; color: #1e1e2e;")
        frm.addRow("جستجو:", self.search_box)
        frm.addRow("ماده:", self.combo_chem)
        frm.addRow("حجم:", self.spin_vol)
        frm.addRow(btn_add)
        gb_chem.setLayout(frm)
        vbox.addWidget(gb_chem)

        gb_temp = QGroupBox("کنترل دما")
        h_temp = QHBoxLayout()
        btn_heat = QPushButton("🔥 گرما")
        btn_heat.setStyleSheet("background-color: #f38ba8; color: #1e1e2e;")
        btn_heat.clicked.connect(lambda: self.engine.change_temperature(15))
        btn_cool = QPushButton("🧊 سرما")
        btn_cool.setStyleSheet("background-color: #89b4fa; color: #1e1e2e;")
        btn_cool.clicked.connect(lambda: self.engine.change_temperature(-15))
        h_temp.addWidget(btn_cool)
        h_temp.addWidget(btn_heat)
        gb_temp.setLayout(h_temp)
        vbox.addWidget(gb_temp)

        self.gb_details = self.create_details_group()
        vbox.addWidget(self.gb_details)

        self.txt_log = QTextEdit();
        self.txt_log.setReadOnly(True)
        vbox.addWidget(QLabel("گزارش:"))
        vbox.addWidget(self.txt_log)

        btn_wash = QPushButton("شست و شوی بشر")
        btn_wash.setStyleSheet("background-color: #89dceb; color: #1e1e2e; font-weight: bold;")
        btn_wash.clicked.connect(self.action_wash)
        vbox.addWidget(btn_wash)

        btn_hard_reset = QPushButton("شروع مجدد بازی (Reset)")
        btn_hard_reset.setStyleSheet("background-color: #ff5555; color: white;")
        btn_hard_reset.clicked.connect(self.action_hard_reset)
        vbox.addWidget(btn_hard_reset)

        # پنل وسط (بشر)
        panel_vis = QFrame()
        v_vis = QVBoxLayout(panel_vis)
        self.beaker = AnimatedBeaker()
        v_vis.addWidget(self.beaker, 0, Qt.AlignCenter)
        info_h = QHBoxLayout()
        self.lbl_ph_display = QLabel("pH: 7.00")
        self.lbl_ph_display.setStyleSheet("font-size: 20px; color: #fab387; font-weight: bold;")
        self.lbl_temp_display = QLabel("25.0 °C")
        self.lbl_temp_display.setStyleSheet("font-size: 20px; color: #f38ba8; font-weight: bold;")
        info_h.addWidget(self.lbl_ph_display)
        info_h.addWidget(self.lbl_temp_display)
        v_vis.addLayout(info_h)

        # پنل چپ (تب‌ها)
        tabs = QTabWidget()
        tabs.addTab(self.create_discoveries_tab(), "🏆 کشف‌ها")
        tabs.addTab(self.create_wiki_tab(), "📖 دانشنامه")
        tabs.addTab(self.create_graph_tab(), "📈 نمودار")
        tabs.addTab(self.create_contents_tab(), "🧪 محتویات")
        tabs.addTab(self.create_datasheet_tab(), "📚 لیست مواد")

        split = QSplitter(Qt.Horizontal)
        split.addWidget(panel_ctrl)
        split.addWidget(panel_vis)
        split.addWidget(tabs)
        split.setSizes([350, 400, 600])
        layout.addWidget(split)

    # --- متدهای تولید تب‌ها ---

    def get_state_color_text(self, formula):
        norm = normalize_key(formula)
        d = CHEMILAB_DB.get(norm)
        if not d: return formula
        ptype = get_persian_type(d.get('type', ''))
        return f"{d.get('name', formula)} <span style='color:{d.get('color', '#fff')};'>■</span> <small>({ptype})</small>"

    def create_wiki_tab(self):
        w = QWidget();
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
        w = QWidget();
        l = QVBoxLayout(w)
        self.table_disc = QTableWidget()
        self.table_disc.setColumnCount(2)
        self.table_disc.setHorizontalHeaderLabels(["نام واکنش", "امتیاز"])
        self.table_disc.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        l.addWidget(self.table_disc)
        self.update_discoveries_table()
        return w

    def create_graph_tab(self):
        w = QWidget();
        l = QVBoxLayout(w)
        self.figure = Figure(figsize=(5, 6), facecolor='#1e1e2e')
        self.canvas = FigureCanvas(self.figure)
        self.ax1 = self.figure.add_subplot(211);
        self.ax1.set_facecolor('#1e1e2e');
        self.ax1.set_ylabel('pH', color='white');
        self.ax1.tick_params(colors='white')
        self.ax2 = self.figure.add_subplot(212);
        self.ax2.set_facecolor('#1e1e2e');
        self.ax2.set_ylabel('Temp', color='white');
        self.ax2.tick_params(colors='white')
        self.line_ph, = self.ax1.plot([], [], color='#fab387')
        self.line_temp, = self.ax2.plot([], [], color='#f38ba8')
        l.addWidget(self.canvas)
        return w

    def create_contents_tab(self):
        w = QWidget();
        l = QVBoxLayout(w)
        self.table_cont = QTableWidget()
        self.table_cont.setColumnCount(3)
        self.table_cont.setHorizontalHeaderLabels(["ماده", "فرمول", "مول"])
        self.table_cont.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        l.addWidget(self.table_cont)
        self.lbl_mix = QLabel("فرمول تجربی مخلوط: -")
        self.lbl_mix.setStyleSheet("font-size: 16px; font-weight: bold; color: #a6e3a1; margin-top: 10px;")
        l.addWidget(self.lbl_mix)
        return w

    def create_datasheet_tab(self):
        """لیست کامل مواد با تمام فیلدها و رنگ به صورت مربع"""
        w = QWidget();
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

            # نمایش رنگ به صورت مربع بدون متن
            color_cell = QTableWidgetItem("")
            color_cell.setBackground(QColor(v.get('color', '#FFFFFF')))
            color_cell.setFlags(Qt.ItemIsEnabled)  # غیرقابل ویرایش
            t.setItem(i, 3, color_cell)

            t.setItem(i, 4, QTableWidgetItem(str(v.get('molarity', '-'))))
            t.setItem(i, 5, QTableWidgetItem(str(v.get('pH', '-'))))
            t.setItem(i, 6, QTableWidgetItem(str(v.get('heat', '-'))))

        l.addWidget(t)
        return w

    def create_details_group(self):
        gb = QGroupBox("مشخصات ماده انتخاب شده")
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

    # --- اکشن‌های اصلی و بازی ---

    def handle_reaction_result(self, disc):
        if not disc: return
        name, xp, status = disc
        if status == "new":
            self.timer.stop()
            self.txt_log.append(f"✨ واکنش جدید: {name}")
            self.beaker.trigger_reaction_animation()
            self.update_player_stats()
            self.update_discoveries_table()
            self.update_wiki_table()
            QMessageBox.information(self, "کشف!", f"شما یک واکنش جدید کشف کردید:\n{name}\nامتیاز کسب شده: {xp}")
            self.timer.start(50)

    def action_add(self):
        k = self.combo_chem.currentData()
        if not k: return
        msg = self.engine.add_chemical(k, self.spin_vol.value())
        self.txt_log.append(msg)
        self.beaker.set_target_state(self.engine.total_volume, self.engine.dominant_color)
        self.update_contents_ui()
        self.handle_reaction_result(self.engine.check_reactions())

    def action_wash(self):
        self.engine.reset()
        self.beaker.set_target_state(0, "#E0FFFF")
        self.update_contents_ui()
        self.txt_log.append("بشر کاملاً شسته شد.")

    def action_hard_reset(self):
        if QMessageBox.question(self, "ریست", "آیا از پاک کردن کامل پیشرفت و شروع مجدد مطمئن هستید؟",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.engine.hard_reset()
            self.beaker.set_target_state(0, "#E0FFFF")
            self.update_player_stats()
            self.update_contents_ui()
            self.update_discoveries_table()
            self.update_wiki_table()
            self.txt_log.clear()

    def update_player_stats(self):
        self.lbl_level.setText(f"سطح: {self.engine.level}")
        self.lbl_score.setText(f"امتیاز: {self.engine.score}")
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
        r = 0
        for k, v in self.engine.contents.items():
            if v > 0.0001:
                self.table_cont.insertRow(r)
                n = CHEMILAB_DB.get(k, {}).get('name', k)
                f = CHEMILAB_DB.get(k, {}).get('formula', '?')
                self.table_cont.setItem(r, 0, QTableWidgetItem(n))
                self.table_cont.setItem(r, 1, QTableWidgetItem(ChemicalCalculator.to_subscript(f)))
                self.table_cont.setItem(r, 2, QTableWidgetItem(f"{v:.4f}"))
                r += 1

        # محاسبه و نمایش فرمول تجربی مخلوط
        f = self.engine.get_mixture_empirical_formula()
        self.lbl_mix.setText(f"فرمول تجربی مخلوط: {f}")

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
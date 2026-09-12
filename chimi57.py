import os as _os_gl
# ویندوز: ANGLE/OpenGL ES از glBegin پشتیبانی نمی‌کند → صفحه سیاه
# باید قبل از import کردن PySide6 باشد
_os_gl.environ.setdefault("QT_OPENGL", "desktop")
_os_gl.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")

import json
import sys
import time
import re
import os
import math
import random
from collections import Counter
import sqlite3
import numpy as np
from functools import lru_cache
import matplotlib
try:
    from molmass import Formula
    HAS_MOLMASS = True
except ImportError:
    Formula = None  # type: ignore
    HAS_MOLMASS = False
    print("[WARN] molmass نصب نیست — از fallback داخلی برای جرم مولی استفاده می‌شود.", flush=True)
import shutil
from datetime import datetime
import copy

# Backend را تا قبل از اطمینان از وجود Qt دست‌کاری نمی‌کنیم؛ این جلوی crash بی‌دلیل در startup را می‌گیرد.
try:
    matplotlib.use("Agg")
except Exception:
    pass

try:
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QLabel, QPushButton, QComboBox, QFrame, QGroupBox, QTextEdit,
        QTabWidget, QMessageBox, QDoubleSpinBox, QFormLayout, QTableWidget,
        QTableWidgetItem, QHeaderView, QSplitter, QLineEdit, QGridLayout,
        QListWidget, QSpinBox, QProgressBar, QScrollArea, QDialog, QToolTip, QFileDialog,
        QSizePolicy, QMenu, QInputDialog, QStackedLayout, QGraphicsDropShadowEffect,
        QScrollBar, QToolBar, QSlider, QCheckBox, QToolButton, QMenuBar
    )
    from PySide6.QtCore import Qt, QTimer, QRectF, QPropertyAnimation, Property, QEasingCurve, QPointF, QSize, QRect, QEvent, QMimeData, QPoint
    from PySide6.QtGui import QFont, QColor, QPainter, QPen, QLinearGradient, QPainterPath, QBrush, QRadialGradient, \
        QPixmap, QPdfWriter, QPageSize, QImage, QAction, QIcon, QDrag, QShortcut, QKeySequence, QSurfaceFormat
    try:
        matplotlib.use("QtAgg")
    except Exception:
        pass
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
except ImportError as e:
    print(f"Error importing UI libraries: {e}", flush=True)
    sys.exit(1)

QPainterGui = QPainter

# مدل مولکولی m1 — اختیاری ولی ترجیحی؛ در صورت نصب RDKit، مختصات ۳بعدی واقعی‌تر تولید می‌شود.
try:
    from rdkit import Chem as _RDKitChem
    from rdkit.Chem import AllChem as _RDKitAllChem
    HAS_RDKIT = True
except Exception as _rdkit_exc:
    _RDKitChem = None
    _RDKitAllChem = None
    HAS_RDKIT = False
    print(f"[WARN] RDKit در دسترس نیست؛ مدل‌های ذخیره‌شده/آموزشی استفاده می‌شوند: {_rdkit_exc}", flush=True)

M1_COMMON_FORMULAS = {
    "H2O": "O", "H2O2": "OO", "NH3": "N", "CH4": "C", "CO2": "O=C=O",
    "CO": "[C-]#[O+]", "N2": "N#N", "O2": "O=O", "HCL": "Cl", "HF": "F",
    "H2S": "S", "SO2": "O=S=O", "SO3": "O=S(=O)=O", "NO": "[N]=O",
    "NO2": "N(=O)[O]", "N2O": "N#[N+][O-]", "CH3OH": "CO", "C2H5OH": "CCO",
    "C2H6O": "CCO", "C3H8O": "CCCO", "C2H4O": "CC=O", "C2H4O2": "CC(=O)O",
    "C3H6O": "CC(=O)C", "C6H6": "c1ccccc1", "C7H8": "Cc1ccccc1",
    "C6H5OH": "c1ccc(cc1)O",
    "C6H12O6": "OC[C@H]1OC(O)[C@H](O)[C@@H](O)[C@@H]1O",
    "C12H22O11": "OC[C@H]1O[C@H](O[C@H]2[C@H](O)[C@@H](O)[C@H](O)[C@@H](CO)O2)[C@H](O)[C@@H](O)[C@@H]1O",
    "C9H8O4": "CC(=O)Oc1ccccc1C(=O)O",
    "C8H10N4O2": "CN1C=NC2=C1C(=O)N(C(=O)N2C)C",
    "C10H14N2": "CN1CCCC1c2cccnc2", "C2H2": "C#C", "C2H4": "C=C",
    "C2H6": "CC", "C3H8": "CCC", "C4H10": "CCCC", "C5H12": "CCCCC",
    "C6H14": "CCCCCC", "CH2O": "C=O", "CH3COOH": "CC(=O)O", "HCOOH": "C(=O)O",
    "C6H5COOH": "c1ccc(cc1)C(=O)O", "C6H12": "C1CCCCC1", "C5H5N": "c1ccncc1",
    "C4H4O": "c1ccoc1", "C4H5N": "c1cc[nH]c1", "C4H8O2": "CCOC(=O)C",
    "C3H6O2": "CC(=O)OC", "C2H3N": "CC#N", "CH3NH2": "CN", "C2H5NH2": "CCN",
    "C6H5NH2": "c1ccc(cc1)N", "C7H6O": "c1ccc(cc1)C=O",
    "C8H8O": "CC(=O)c1ccccc1", "C10H8": "c1ccc2ccccc2c1",
    "C14H10": "c1ccc2cc3ccccc3cc2c1",
}

ELEMENT_COLORS_3D = {
    "H": "#FFFFFF", "C": "#555555", "N": "#3050F8", "O": "#FF0D0D",
    "F": "#90E050", "Cl": "#1FF01F", "Br": "#A62929", "I": "#940094",
    "S": "#FFFF30", "P": "#FF8000", "B": "#FFB5B5", "Si": "#F0C8A0",
    "Na": "#AB5CF2", "Mg": "#8AFF00", "Ca": "#3DFF00", "Fe": "#E06633",
    "Zn": "#7D80B0", "K": "#8F40D4", "Li": "#CC80FF", "Cu": "#C88033",
    "Ag": "#C0C0C0", "Au": "#FFD700",
}
ATOM_SIZES_3D = {
    "H": 120, "C": 280, "N": 260, "O": 250, "F": 220, "Cl": 340,
    "Br": 360, "I": 390, "S": 320, "P": 300, "Na": 360, "K": 400,
    "Ca": 380, "Fe": 300, "Cu": 300, "Ag": 320, "default": 240,
}

def _normalize_formula_key(value):
    return re.sub(r"[^A-Za-z0-9]", "", str(value or "")).upper()

def resolve_molecular_smiles(value):
    key = _normalize_formula_key(value)
    if not key:
        return None
    # ابتدا از دیتابیس ماده استفاده می‌کنیم تا ایزومر اشتباه تحمیل نشود.
    for _k, _d in CHEMILAB_DB.items() if "CHEMILAB_DB" in globals() else []:
        if _normalize_formula_key(_d.get("formula")) == key and _d.get("smiles"):
            return str(_d["smiles"]).strip()
    return M1_COMMON_FORMULAS.get(key)

def generate_rdkit_structure(smiles):
    if not HAS_RDKIT or not smiles:
        return None
    try:
        mol = _RDKitChem.MolFromSmiles(smiles)
        if mol is None:
            return None
        mol = _RDKitChem.AddHs(mol)
        params = _RDKitAllChem.ETKDGv3()
        params.randomSeed = 0xF00D
        rc = _RDKitAllChem.EmbedMolecule(mol, params)
        if rc != 0:
            rc = _RDKitAllChem.EmbedMolecule(mol, _RDKitAllChem.ETKDG())
        if rc != 0:
            return None
        try:
            _RDKitAllChem.MMFFOptimizeMolecule(mol, maxIters=200)
        except Exception:
            try:
                _RDKitAllChem.UFFOptimizeMolecule(mol, maxIters=200)
            except Exception:
                pass
        conf = mol.GetConformer()
        atoms = []
        for i in range(mol.GetNumAtoms()):
            p = conf.GetAtomPosition(i)
            atoms.append((mol.GetAtomWithIdx(i).GetSymbol(), float(p.x), float(p.y), float(p.z)))
        bonds = [(b.GetBeginAtomIdx(), b.GetEndAtomIdx(), int(b.GetBondTypeAsDouble())) for b in mol.GetBonds()]
        return {"atoms": atoms, "bonds": bonds, "note": "مختصات ۳بعدی تولیدشده با RDKit/ETKDG + بهینه‌سازی", "smiles": smiles}
    except Exception as exc:
        print(f"[MOLECULE][WARN] RDKit 3D: {exc}", flush=True)
        return None


HAS_OPENGL = False
OPENGL_ERROR = ""
try:
    from PySide6.QtOpenGLWidgets import QOpenGLWidget
    from OpenGL.GL import *
    from OpenGL.GLU import *
    HAS_OPENGL = True
except Exception as e:
    OPENGL_ERROR = str(e)
    print(f"[WARN] OpenGL/PyOpenGL در دسترس نیست — حالت fallback فعال می‌شود: {e}", flush=True)
    HAS_OPENGL = False
    class QOpenGLWidget(object):
        pass


def configure_opengl_compatibility():
    """تنظیم یک context دسکتاپ پایدار برای رندرهای OpenGL برنامه."""
    if not HAS_OPENGL:
        return False
    try:
        fmt = QSurfaceFormat()
        fmt.setRenderableType(QSurfaceFormat.OpenGL)
        fmt.setDepthBufferSize(24)
        fmt.setStencilBufferSize(8)
        fmt.setSwapBehavior(QSurfaceFormat.DoubleBuffer)
        fmt.setSamples(4)
        fmt.setVersion(2, 1)
        try:
            fmt.setProfile(QSurfaceFormat.CompatibilityProfile)
        except Exception:
            pass
        QSurfaceFormat.setDefaultFormat(fmt)
        print("[GL] Desktop OpenGL 2.1 Compatibility context configured", flush=True)
        return True
    except Exception as e:
        print(f"[GL][WARN] تنظیم SurfaceFormat ناموفق: {e}", flush=True)
        return False

FLASK_BREAK_TEMP = 500.0
HEAT_COOL_DELTA = 5.0
TEMP_TOLERANCE = 3.0  # تلورانس دمای واکنش (± درجه سانتی‌گراد)
BROCHURE_FOLDER = "element_brochures"
APP_VERSION = "57.0.0"
APP_NAME = "شیمی‌لَب"
GITHUB_URL = "https://github.com/kianfadaee448-alt/ChimiLab"
CONTACT_EMAIL = "kianfadaee448@gmail.com"
SCHEMA_VERSION = 2
MIN_ADMIN_PASSWORD_LEN = 8

FONT_NAME = "Tahoma"
APP_STYLE_DARK = """
/* ── Modern Violet / Purple theme ── */
QMainWindow { background-color: #0a0612; }
QWidget { color: #e8e0f5; font-family: 'Tahoma', sans-serif; font-size: 13px; }
QGroupBox {
    border: 1px solid #6d28d9; border-radius: 14px; margin-top: 18px;
    background-color: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #1e1033, stop:1 #12081f);
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin; subcontrol-position: top center;
    padding: 5px 16px; background-color: #3b0764; color: #e9d5ff;
    border-radius: 10px; border: 1px solid #a78bfa;
}
QPushButton {
    background-color: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #5b21b6, stop:1 #3b0764);
    border: 1px solid #7c3aed; border-radius: 10px;
    padding: 7px 14px; color: #f5f3ff; font-weight: bold; font-size: 13px;
    min-height: 28px;
}
QPushButton:hover {
    background-color: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #7c3aed, stop:1 #6d28d9);
    border: 2px solid #c4b5fd;
    color: #ffffff;
}
QPushButton:pressed {
    background-color: #2e1065;
    border: 2px solid #e879f9;
    padding-top: 9px; padding-bottom: 5px;
}
QPushButton:checked {
    background-color: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #e879f9, stop:1 #a78bfa);
    color: #0c0914; border: 2px solid #f5d0fe;
}
QLineEdit {
    background-color: #160f22; border: 1px solid #3d2a55; border-radius: 10px;
    padding: 8px 12px; color: #c4b5fd; font-weight: bold;
}
QLineEdit:focus { border: 1px solid #a78bfa; background-color: #1e1530; }
QComboBox, QDoubleSpinBox, QSpinBox {
    background-color: #160f22; border: 1px solid #3d2a55; border-radius: 10px;
    padding: 7px 10px; color: #e8e0f5;
}
QComboBox:hover, QDoubleSpinBox:hover { border: 1px solid #a78bfa; }
QComboBox QAbstractItemView {
    background-color: #160f22; color: #c4b5fd;
    selection-background-color: #3b2a55; selection-color: #f0e8ff;
    border: 1px solid #3d2a55; outline: 0; padding: 4px;
}
QComboBox QAbstractItemView::item {
    background-color: #160f22; color: #c4b5fd; padding: 8px 12px; min-height: 30px;
}
QComboBox QAbstractItemView::item:selected { background-color: #3b2a55; color: #ddd6fe; }
QListWidget {
    background-color: #160f22; border: 1px solid #6d28d9; border-radius: 12px;
    color: #e9d5ff; font-size: 14px; padding: 4px;
}
QListWidget::item { padding: 8px; border-radius: 8px; }
QListWidget::item:selected { background-color: #3b2a55; color: #ddd6fe; }
QListWidget::item:hover { background-color: #1e1530; }
QTableWidget {
    background-color: #160f22; gridline-color: #4c1d95; color: #e9d5ff;
    border: 1px solid #6d28d9; border-radius: 12px;
}
QHeaderView::section {
    background-color: #1a1228; padding: 9px; border: 1px solid #2e2040;
    color: #f0abfc; font-weight: bold;
}
QTextEdit {
    background-color: #120e1c; border: 1px solid #2e2040; border-radius: 12px;
    color: #c4b5fd; padding: 8px;
}
QTabWidget::pane {
    border: 1px solid #2e2040; background: #140f20; border-radius: 14px; top: -1px;
}
QTabBar::tab {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #2a1e3d, stop:1 #1a1228);
    color: #e9d5ff; padding: 8px 14px; margin-right: 3px;
    border-top-left-radius: 10px; border-top-right-radius: 10px;
    border: 1px solid #4c1d95; border-bottom: none;
    font-size: 12px; font-weight: bold; min-height: 26px; min-width: 70px;
}
QTabBar::tab:selected {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #7c3aed, stop:1 #e879f9);
    color: #0c0914; font-weight: bold; border: 1px solid #f0abfc;
}
QTabBar::tab:hover:!selected {
    background: #3b0764; color: #f5d0fe;
}
QProgressBar {
    border: 1px solid #3d2a55; border-radius: 9px; text-align: center;
    color: white; background-color: #120e1c; height: 18px;
}
QProgressBar::chunk {
    background-color: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #8b5cf6, stop:1 #e879f9);
    border-radius: 8px;
}
 QToolTip {
     background: #21152f; color: #f5f3ff; border: 1px solid #a78bfa;
     padding: 6px 9px; border-radius: 7px;
 }
 QTableWidget::item:hover { background: #241735; }
 QHeaderView::section:hover { background: #241735; color: #f5d0fe; }
 QCheckBox { spacing: 7px; color: #e9d5ff; }
 QCheckBox::indicator { width: 16px; height: 16px; border-radius: 5px; border: 1px solid #6d28d9; background: #160f22; }
 QCheckBox::indicator:checked { background: #a78bfa; border: 1px solid #f0abfc; }
 QSlider::groove:horizontal { height: 5px; background: #2e2040; border-radius: 3px; }
 QSlider::handle:horizontal { width: 16px; margin: -6px 0; background: #c084fc; border: 1px solid #f0abfc; border-radius: 8px; }

QScrollArea { border: none; background-color: transparent; }
QScrollBar:vertical {
    background: #100a18; width: 11px; border-radius: 5px; margin: 2px;
}
QScrollBar::handle:vertical {
    background: #3d2a55; border-radius: 5px; min-height: 30px;
}
QScrollBar::handle:vertical:hover { background: #a78bfa; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QDialog { background-color: #160f22; border-radius: 14px; }
QToolTip {
    background-color: #1a1228; color: #c4b5fd; border: 1px solid #a78bfa;
    border-radius: 8px; padding: 8px; font-size: 12px;
}
QToolBar { background-color: #140f20; border: none; spacing: 10px; }
QToolBar QPushButton {
    background-color: #2a1e3d; border: 1px solid #3d2a55; border-radius: 10px;
    padding: 7px 12px; color: #e8e0f5; font-weight: bold; font-size: 13px;
}
QToolBar QPushButton:hover { background-color: #3b2a55; border: 1px solid #a78bfa; }
QSlider::groove:horizontal { height: 8px; background: #2a1e3d; border-radius: 4px; }
QSlider::handle:horizontal {
    width: 18px; margin: -6px 0; background: #a78bfa; border-radius: 9px;
}
QSlider::sub-page:horizontal { background: #8b5cf6; border-radius: 4px; }
"""


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


# ============================================================
# آزمایشگاه سه‌بعدی — معادل src/game (LabRoom + Equipment + Player + stations)
# از نسخه وب React/Three.js پورت‌شده به OpenGL
# ============================================================
CUSTOM_REACTIONS = {}
CHEMILAB_DB = {}

def get_app_base_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    try:
        return os.path.dirname(os.path.abspath(__file__))
    except Exception:
        return os.path.abspath(".")

def get_db_path():
    """جستجوی db.db در چند مسیر؛ جدیدترین فایل معتبر برمی‌گردد."""
    base_dir = get_app_base_dir()
    candidates = []
    candidates.append(os.path.join(base_dir, "db.db"))
    candidates.append(os.path.join(os.path.abspath("."), "db.db"))
    for extra in ("artifacts", "attachments", os.path.join("..", "attachments"), os.path.join("..", "artifacts")):
        candidates.append(os.path.join(base_dir, extra, "db.db"))
        candidates.append(os.path.join(os.path.abspath("."), extra, "db.db"))
    if hasattr(sys, "_MEIPASS"):
        candidates.append(os.path.join(sys._MEIPASS, "db.db"))

    existing = []
    seen = set()
    for p in candidates:
        try:
            ap = os.path.abspath(p)
        except Exception:
            continue
        if ap in seen:
            continue
        seen.add(ap)
        if os.path.isfile(ap) and os.path.getsize(ap) > 1000:
            existing.append(ap)

    if not existing:
        local_db = os.path.join(base_dir, "db.db")
        if hasattr(sys, "_MEIPASS"):
            bundled = os.path.join(sys._MEIPASS, "db.db")
            if os.path.isfile(bundled):
                try:
                    shutil.copy2(bundled, local_db)
                    return local_db
                except Exception as e:
                    print(f"[DB][WARN] کپی db.db از bundle ناموفق: {e}", flush=True)
                    return bundled
        return local_db

    existing.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    chosen = existing[0]
    local_db = os.path.join(base_dir, "db.db")
    try:
        if os.path.abspath(chosen) != os.path.abspath(local_db):
            if (not os.path.exists(local_db)) or (os.path.getmtime(chosen) > os.path.getmtime(local_db) + 1):
                try:
                    shutil.copy2(chosen, local_db)
                    print(f"[DB] همگام‌سازی db.db از {chosen}", flush=True)
                    return local_db
                except Exception:
                    return chosen
    except Exception:
        pass
    print(f"[DB] مسیر دیتابیس: {chosen}", flush=True)
    return chosen

def db_is_writable_for_role(is_admin):
    """دانش‌آموز اجازه تغییر فایل دیتابیس را ندارد"""
    return bool(is_admin)

def safe_float(val, default=0.0):
    """تبدیل امن به float؛ NaN/Inf و مقادیر نامعتبر → default."""
    try:
        if val is None:
            return default
        f = float(val)
        if not math.isfinite(f):
            return default
        return f
    except (TypeError, ValueError):
        return default

def safe_int(val, default=0):
    try:
        if val is None:
            return default
        return int(val)
    except (TypeError, ValueError):
        return default

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
        CHEMILAB_DB["h2o"] = {"name": "آب", "type": "Liquid", "pH": 7.0, "molarity": 55.5, "heat": 0.0,
                              "color": "#aaddff", "formula": "H2O", "state": "مایع"}
        CHEMILAB_DB["hcl"] = {"name": "هیدروکلریک اسید", "type": "Strong Acid", "pH": 1.0, "molarity": 1.0, "heat": 0.0,
                              "color": "#ffffff", "formula": "HCl", "state": "مایع"}
        CHEMILAB_DB["naoh"] = {"name": "سدیم هیدروکسید", "type": "Strong Base", "pH": 13.0, "molarity": 1.0,
                               "heat": -44.5, "color": "#eeeeee", "formula": "NaOH", "state": "جامد"}
        CHEMILAB_DB["agcl"] = {"name": "نقره کلرید", "type": "Precipitate", "pH": 7.0, "molarity": 0.0, "heat": 0.0,
                               "color": "#ffffff", "formula": "AgCl", "state": "جامد"}
        CHEMILAB_DB["agno3"] = {"name": "نقره نیترات", "type": "Salt", "pH": 7.0, "molarity": 1.0, "heat": 0.0,
                                "color": "#eeeeee", "formula": "AgNO3", "state": "جامد"}
        CHEMILAB_DB["nacl"] = {"name": "سدیم کلرید", "type": "Salt", "pH": 7.0, "molarity": 1.0, "heat": 0.0,
                               "color": "#eeeeee", "formula": "NaCl", "state": "جامد"}
        CHEMILAB_DB["hno3"] = {"name": "نیتریک اسید", "type": "Strong Acid", "pH": 1.0, "molarity": 1.0, "heat": 0.0,
                               "color": "#ffffff", "formula": "HNO3", "state": "مایع"}
        CHEMILAB_DB["co2"] = {"name": "کربن دی اکسید", "type": "Gas", "pH": 5.5, "molarity": 0.0, "heat": 0.0,
                              "color": "#dddddd", "formula": "CO2"}
        CUSTOM_REACTIONS["خنثی سازی HCl"] = {"reactants": ["hcl", "naoh"], "products": ["h2o", "nacl"],
                                             "desc": "خنثی سازی", "xp": 50, "temp_min": -273}
        CUSTOM_REACTIONS["رسوب AgCl"] = {"reactants": ["agno3", "hcl"], "products": ["agcl", "hno3"],
                                         "desc": "رسوب‌گذاری", "xp": 40, "temp_min": -273}
        return

    try:
        CHEMILAB_DB.clear()
        CUSTOM_REACTIONS.clear()
        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()

        def parse_db_list(val):
            if isinstance(val, list): return val
            if not val or str(val).strip() == "": return []
            val_str = str(val).strip()
            if val_str.startswith('[') and val_str.endswith(']'):
                try:
                    return json.loads(val_str.replace("'", '"'))
                except Exception as e:
                    print(f"[DB][WARN] parse_db_list JSON: {e}", flush=True)
            return [x.strip(" []\"'") for x in val_str.split(',')]

        cursor.execute("SELECT * FROM custom_reactions WHERE 1")
        for i in cursor.fetchall():
            fa_name = str(i[1])
            try:
                xp_val = int(i[5])
            except (TypeError, ValueError):
                xp_val = 0
            try:
                temp_min_val = float(i[6])
            except (TypeError, ValueError):
                temp_min_val = -273.0

            raw_r = parse_db_list(i[2])
            raw_p = parse_db_list(i[3])
            dH_val = 0.0
            cond_val = ""
            try:
                if len(i) > 7 and i[7] is not None:
                    dH_val = float(i[7])
            except (TypeError, ValueError):
                dH_val = 0.0
            try:
                if len(i) > 8 and i[8]:
                    cond_val = str(i[8])
            except Exception:
                cond_val = ""
            CUSTOM_REACTIONS[fa_name] = {
                "reactants": [normalize_key(x) for x in raw_r],
                "products": [normalize_key(x) for x in raw_p],
                "desc": str(i[4]), "xp": xp_val, "temp_min": temp_min_val,
                "dH": dH_val, "condition": cond_val,
            }

        cursor.execute("SELECT * FROM chemilab WHERE 1")
        for i in cursor.fetchall():
            fa_name = normalize_key(str(i[2]))
            try:
                ph_val = float(i[4])
            except (TypeError, ValueError):
                ph_val = 7.0
            try:
                mol_val = float(i[5])
            except (TypeError, ValueError):
                mol_val = 0.1
            try:
                heat_val = float(i[6])
            except (TypeError, ValueError):
                heat_val = 0.0

            state_val = "جامد"
            hazard_val = "کم‌خطر — احتیاط معمولی"
            try:
                if len(i) > 9 and i[9]:
                    state_val = str(i[9])
                if len(i) > 10 and i[10]:
                    hazard_val = str(i[10])
            except Exception:
                pass
            dens_val = 1.0
            mp_val = None
            bp_val = None
            try:
                if len(i) > 11 and i[11] is not None:
                    dens_val = float(i[11])
            except (TypeError, ValueError):
                dens_val = 1.0
            try:
                if len(i) > 12 and i[12] is not None:
                    mp_val = float(i[12])
            except (TypeError, ValueError):
                mp_val = None
            try:
                if len(i) > 13 and i[13] is not None:
                    bp_val = float(i[13])
            except (TypeError, ValueError):
                bp_val = None
            smiles_val = ""
            try:
                if len(i) > 14 and i[14]:
                    smiles_val = str(i[14]).strip()
            except Exception:
                smiles_val = ""
            if not smiles_val:
                smiles_val = M1_COMMON_FORMULAS.get(_normalize_formula_key(i[8]), "")
            CHEMILAB_DB[fa_name] = {
                "name": str(i[1]), "type": str(i[3]), "pH": ph_val,
                "molarity": mol_val, "heat": heat_val, "color": str(i[7]), "formula": str(i[8]),
                "state": state_val, "hazard": hazard_val,
                "density": dens_val, "mp": mp_val, "bp": bp_val,
                "smiles": smiles_val,
            }
        connection.close()
        print(f"[DB] بارگذاری موفق: {len(CHEMILAB_DB)} ماده، {len(CUSTOM_REACTIONS)} واکنش از {db_path}", flush=True)
    except Exception as e:
        print(f"[DB][ERROR] خطا در بارگذاری دیتابیس ({db_path}): {e}", flush=True)
        import traceback
        traceback.print_exc()
        if not CHEMILAB_DB:
            CHEMILAB_DB["h2o"] = {"name": "آب", "type": "Liquid", "pH": 7.0, "molarity": 55.5, "heat": 0.0,
                                  "color": "#aaddff", "formula": "H2O", "state": "مایع"}
            CHEMILAB_DB["hcl"] = {"name": "هیدروکلریک اسید", "type": "Strong Acid", "pH": 1.0, "molarity": 1.0, "heat": 0.0,
                                  "color": "#ffffff", "formula": "HCl", "state": "مایع"}
            CHEMILAB_DB["naoh"] = {"name": "سدیم هیدروکسید", "type": "Strong Base", "pH": 13.0, "molarity": 1.0,
                                   "heat": -44.5, "color": "#eeeeee", "formula": "NaOH", "state": "جامد"}
            print("[DB][WARN] از داده‌های پیش‌فرض استفاده شد.", flush=True)

load_databases()

import hashlib
import hmac
import secrets

ADMIN_AUTH_FILE = "admin_auth.json"
DB_WRITE_UNLOCKED = False  # فقط بعد از تأیید رمز در نشست ادمین True می‌شود

def get_admin_auth_path():
    return os.path.join(get_app_base_dir(), ADMIN_AUTH_FILE)

class AdminAuth:
    """مدیریت رمز ادمین — هش PBKDF2؛ رمز خام هرگز ذخیره نمی‌شود."""
    ITERATIONS = 120_000
    SALT_BYTES = 16

    @staticmethod
    def _hash(password: str, salt_hex: str) -> str:
        salt = bytes.fromhex(salt_hex)
        dk = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, AdminAuth.ITERATIONS
        )
        return dk.hex()

    @staticmethod
    def load():
        p = get_admin_auth_path()
        if not os.path.exists(p):
            return None
        try:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("salt") and data.get("hash"):
                return data
        except Exception as e:
            print(f"[AUTH] خطا در خواندن فایل رمز: {e}", flush=True)
        return None

    @staticmethod
    def is_password_set() -> bool:
        return AdminAuth.load() is not None

    @staticmethod
    def set_password(password: str) -> bool:
        password = (password or "").strip()
        if len(password) < MIN_ADMIN_PASSWORD_LEN:
            return False
        salt = secrets.token_hex(AdminAuth.SALT_BYTES)
        h = AdminAuth._hash(password, salt)
        data = {
            "salt": salt,
            "hash": h,
            "iterations": AdminAuth.ITERATIONS,
            "updated_at": datetime.now().isoformat(timespec="seconds"),
        }
        try:
            with open(get_admin_auth_path(), "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"[AUTH] خطا در ذخیره رمز: {e}", flush=True)
            return False

    @staticmethod
    def verify(password: str) -> bool:
        data = AdminAuth.load()
        if not data:
            return False
        try:
            expected = data["hash"]
            got = AdminAuth._hash(password, data["salt"])
            return hmac.compare_digest(expected, got)
        except Exception:
            return False

    @staticmethod
    def change_password(old_password: str, new_password: str) -> tuple:
        if not AdminAuth.verify(old_password):
            return False, "رمز فعلی اشتباه است."
        if len((new_password or "").strip()) < MIN_ADMIN_PASSWORD_LEN:
            return False, f"رمز جدید باید حداقل {MIN_ADMIN_PASSWORD_LEN} کاراکتر باشد."
        if AdminAuth.set_password(new_password):
            return True, "رمز با موفقیت تغییر کرد."
        return False, "خطا در ذخیره رمز جدید."

def _backup_db_file(db_path):
    """کپی پشتیبان قبل از mutation؛ حداکثر ۳ نسخه چرخشی نگه می‌دارد."""
    try:
        if not os.path.isfile(db_path):
            return
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        bak = f"{db_path}.bak.{ts}"
        shutil.copy2(db_path, bak)
        parent = os.path.dirname(db_path) or "."
        base = os.path.basename(db_path) + ".bak."
        baks = sorted(
            [os.path.join(parent, f) for f in os.listdir(parent) if f.startswith(base)],
            key=lambda p: os.path.getmtime(p),
            reverse=True,
        )
        for old in baks[3:]:
            try:
                os.remove(old)
            except Exception:
                pass
        simple = db_path + ".bak"
        try:
            shutil.copy2(db_path, simple)
        except Exception:
            pass
    except Exception as e:
        print(f"[DB][WARN] backup failed: {e}", flush=True)

def save_chemilab_to_db():
    """ذخیره CHEMILAB_DB در SQLite — فقط وقتی قفل ادمین باز باشد."""
    global DB_WRITE_UNLOCKED
    if not DB_WRITE_UNLOCKED:
        return False, "دسترسی نوشتن قفل است. ابتدا رمز ادمین را تأیید کنید."
    db_path = get_db_path()
    try:
        _backup_db_file(db_path)
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("BEGIN")
        cur.execute(
            """CREATE TABLE IF NOT EXISTS chemilab (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT, fa_name TEXT, type TEXT,
                pH REAL, molarity REAL, heat REAL,
                color TEXT, formula TEXT, state TEXT, hazard TEXT,
                density REAL DEFAULT 1.0, mp REAL, bp REAL, smiles TEXT
            )"""
        )
        for col, default in (
            ("state", "جامد"),
            ("hazard", "کم‌خطر — احتیاط معمولی"),
            ("density", "1.0"),
            ("mp", "NULL"),
            ("bp", "NULL"),
            ("smiles", "''"),
        ):
            try:
                if default == "NULL":
                    cur.execute(f"ALTER TABLE chemilab ADD COLUMN {col} REAL")
                elif col == "density":
                    cur.execute(f"ALTER TABLE chemilab ADD COLUMN {col} REAL DEFAULT 1.0")
                else:
                    cur.execute(f"ALTER TABLE chemilab ADD COLUMN {col} TEXT DEFAULT '{default}'")
            except Exception:
                pass
        cur.execute("DELETE FROM chemilab")
        for key, d in CHEMILAB_DB.items():
            cur.execute(
                "INSERT INTO chemilab (name, fa_name, type, pH, molarity, heat, color, formula, state, hazard, density, mp, bp, smiles) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    str(d.get("name", "")),
                    str(key),
                    str(d.get("type", "")),
                    float(d.get("pH", 7.0) or 7.0),
                    float(d.get("molarity", 0.1) or 0.1),
                    float(d.get("heat", 0.0) or 0.0),
                    str(d.get("color", "#FFFFFF")),
                    str(d.get("formula", "")),
                    str(d.get("state", "جامد") or "جامد"),
                    str(d.get("hazard", "کم‌خطر — احتیاط معمولی") or "کم‌خطر — احتیاط معمولی"),
                    float(d.get("density", 1.0) or 1.0),
                    d.get("mp"),
                    d.get("bp"),
                    str(d.get("smiles", "") or ""),
                ),
            )
        conn.commit()
        conn.close()
        return True, f"{len(CHEMILAB_DB)} ماده ذخیره شد."
    except Exception as e:
        try:
            conn.rollback()
            conn.close()
        except Exception:
            pass
        return False, str(e)

def save_reactions_to_db():
    """ذخیره CUSTOM_REACTIONS در SQLite."""
    global DB_WRITE_UNLOCKED
    if not DB_WRITE_UNLOCKED:
        return False, "دسترسی نوشتن قفل است. ابتدا رمز ادمین را تأیید کنید."
    db_path = get_db_path()
    try:
        _backup_db_file(db_path)
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("BEGIN")
        cur.execute(
            """CREATE TABLE IF NOT EXISTS custom_reactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fa_name TEXT, reactants TEXT, products TEXT,
                desc TEXT, xp INTEGER, temp_min REAL,
                dH REAL DEFAULT 0, condition TEXT DEFAULT ''
            )"""
        )
        for col, decl in (("dH", "REAL DEFAULT 0"), ("condition", "TEXT DEFAULT ''")):
            try:
                cur.execute(f"ALTER TABLE custom_reactions ADD COLUMN {col} {decl}")
            except Exception:
                pass
        cur.execute("DELETE FROM custom_reactions")
        for name, rxn in CUSTOM_REACTIONS.items():
            cur.execute(
                "INSERT INTO custom_reactions (fa_name, reactants, products, desc, xp, temp_min, dH, condition) VALUES (?,?,?,?,?,?,?,?)",
                (
                    str(name),
                    json.dumps(rxn.get("reactants", []), ensure_ascii=False),
                    json.dumps(rxn.get("products", []), ensure_ascii=False),
                    str(rxn.get("desc", "")),
                    int(rxn.get("xp", 0) or 0),
                    float(rxn.get("temp_min", -273) if rxn.get("temp_min") is not None else -273),
                    float(rxn.get("dH", 0) or 0),
                    str(rxn.get("condition", "") or ""),
                ),
            )
        conn.commit()
        conn.close()
        return True, f"{len(CUSTOM_REACTIONS)} واکنش ذخیره شد."
    except Exception as e:
        try:
            conn.rollback()
            conn.close()
        except Exception:
            pass
        return False, str(e)

def _user_id_from_name(name: str) -> str:
    """شناسه پایدار کاربر از نام — برای مسیر ذخیرهٔ جداگانه (ضد path traversal)."""
    raw = (name or "guest").strip().lower()
    if not raw:
        raw = "guest"
    # حذف جداکننده‌های مسیر و کاراکترهای خطرناک
    raw = raw.replace("..", "").replace("/", "_").replace("\\", "_").replace("\x00", "")
    safe = re.sub(r'[^\w\u0600-\u06FF\-]+', '_', raw, flags=re.UNICODE)
    safe = safe.strip('._')[:48] or "guest"
    if safe in (".", "..") or safe.startswith("."):
        safe = "guest"
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]
    return f"{safe}_{digest}"

def get_users_root():
    root = os.path.join(get_app_base_dir(), "data", "users")
    os.makedirs(root, exist_ok=True)
    return root

def get_user_dir(player_name: str):
    uid = _user_id_from_name(player_name)
    d = os.path.join(get_users_root(), uid)
    os.makedirs(d, exist_ok=True)
    return d

def get_save_path(player_name=None):
    """مسیر ذخیرهٔ پیشرفت — اگر نام کاربر داده شود، فایل جدا برای هر کاربر."""
    if player_name:
        return os.path.join(get_user_dir(player_name), "lab_state.json")
    return os.path.join(get_app_base_dir(), "lab_save.json")

def get_session_path():
    """نشست فعال — اگر باشد ورود خودکار بدون پرسش نام"""
    return os.path.join(get_app_base_dir(), "active_session.json")

def load_active_session():
    """بارگذاری نشست — حداکثر ۷ روز اعتبار؛ admin هرگز از session."""
    p = get_session_path()
    if not os.path.exists(p):
        return None
    try:
        with open(p, "r", encoding="utf-8") as f:
            d = json.load(f)
        if not isinstance(d, dict) or not d.get("player_name"):
            return None
        # اعتبارسنجی سن نشست
        ts = d.get("saved_at")
        if ts:
            try:
                from datetime import datetime as _dt
                saved = _dt.fromisoformat(str(ts))
                age_days = (_dt.now() - saved).total_seconds() / 86400.0
                if age_days > 7.0:
                    clear_active_session()
                    return None
            except Exception:
                pass
        d["is_admin"] = False  # هرگز admin از session
        return d
    except Exception as e:
        print(f"[SESSION] load failed: {e}", flush=True)
    return None

def save_active_session(player_name, is_admin=False):
    try:
        with open(get_session_path(), "w", encoding="utf-8") as f:
            json.dump({
                "player_name": str(player_name or "").strip()[:64],
                "user_id": _user_id_from_name(player_name),
                "is_admin": False,  # هرگز admin را در session پایدار نکن
                "schema_version": SCHEMA_VERSION,
                "saved_at": datetime.now().isoformat(timespec="seconds"),
            }, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[SESSION] save failed: {e}", flush=True)

def clear_active_session():
    p = get_session_path()
    try:
        if os.path.exists(p):
            os.remove(p)
    except Exception:
        pass

def wipe_all_user_progress():
    """پاک‌سازی کامل پیشرفت *همه* کاربران — فقط برای reset ادمین/تست. هرگز در logout فراخوانی نشود."""
    clear_active_session()
    for fname in ("lab_save.json", "lab_save.json.tmp"):
        p = os.path.join(get_app_base_dir(), fname)
        try:
            if os.path.exists(p):
                os.remove(p)
        except Exception as e:
            print(f"[WIPE] remove {fname}: {e}", flush=True)
    try:
        root = get_users_root()
        if os.path.isdir(root):
            shutil.rmtree(root, ignore_errors=True)
            os.makedirs(root, exist_ok=True)
    except Exception as e:
        print(f"[WIPE] rmtree users: {e}", flush=True)

def wipe_current_user_progress(player_name: str):
    """پاک‌سازی پیشرفت فقط یک کاربر مشخص — سایر کاربران دست‌نخورده می‌مانند."""
    clear_active_session()
    name = (player_name or "").strip()
    if not name:
        return
    try:
        udir = get_user_dir(name)
        if os.path.isdir(udir):
            shutil.rmtree(udir, ignore_errors=True)
    except Exception as e:
        print(f"[WIPE] current user dir: {e}", flush=True)
    # legacy single-file save فقط اگر متعلق به همین نام باشد
    try:
        leg = os.path.join(get_app_base_dir(), "lab_save.json")
        if os.path.isfile(leg):
            with open(leg, "r", encoding="utf-8") as f:
                d = json.load(f)
            if str(d.get("player_name", "")).strip() == name:
                os.remove(leg)
    except Exception as e:
        print(f"[WIPE] legacy save: {e}", flush=True)


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
    """تشخیص جامد با اولویت کلیدواژه‌های صریح؛ از همپوشانی مایع/گاز اجتناب می‌کند."""
    if not ctype:
        return False
    ctype = str(ctype)
    has_lg = any(k in ctype for k in LIQUID_GAS_KEYWORDS)
    has_solid = any(k in ctype for k in SOLID_TYPE_KEYWORDS)
    if has_lg and not has_solid:
        return False
    strong_solid = ("Solid", "Metal", "Salt", "Precipitate", "Powder", "Alloy",
                    "Oxide", "Ceramic", "جامد", "فلز", "نمک", "رسوب", "پودر")
    if any(k in ctype for k in strong_solid):
        return True
    return has_solid and not has_lg

class AppLogger:
    """لاگ دقیق: ترمینال + فایل + حافظه — برای تشخیص باگ layout/UI"""
    def __init__(self, filename="chimi49_lab.log"):
        self.path = os.path.join(get_app_base_dir(), filename)
        self.memory = []
        self.max_mem = 500
        self.to_terminal = True
        try:
            with open(self.path, "a", encoding="utf-8") as f:
                f.write("\n" + "=" * 60 + "\n")
                f.write(f"SESSION START {datetime.now().isoformat()}\n")
                f.write("=" * 60 + "\n")
        except Exception:
            pass
        print(f"[LOG] فایل لاگ: {self.path}", flush=True)

    def log(self, level, msg, **extra):
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        extra_s = ""
        if extra:
            extra_s = " | " + " ".join(f"{k}={v}" for k, v in extra.items())
        line = f"[{ts}] [{level}] {msg}{extra_s}"
        self.memory.append(line)
        if len(self.memory) > self.max_mem:
            self.memory.pop(0)
        noisy = level in ("UI", "LAYOUT", "CLICK")
        if self.to_terminal and not noisy:
            try:
                print(line, flush=True)
            except Exception:
                pass
        if not noisy:
            try:
                with open(self.path, "a", encoding="utf-8") as f:
                    f.write(line + "\n")
            except Exception:
                pass
        return line

    def info(self, msg, **kw):
        return self.log("INFO", msg, **kw)

    def warn(self, msg, **kw):
        return self.log("WARN", msg, **kw)

    def error(self, msg, **kw):
        return self.log("ERROR", msg, **kw)

    def ui(self, msg, **kw):
        return self.log("UI", msg, **kw)

    def layout(self, msg, **kw):
        return self.log("LAYOUT", msg, **kw)

    def click(self, msg, **kw):
        return self.log("CLICK", msg, **kw)

    def clear_file(self):
        try:
            open(self.path, "w", encoding="utf-8").close()
        except Exception:
            pass

APP_LOGGER = None

def get_logger():
    global APP_LOGGER
    if APP_LOGGER is None:
        APP_LOGGER = AppLogger()
    return APP_LOGGER

def tlog(msg, level="INFO", **kw):
    """میانبر لاگ ترمینال"""
    try:
        get_logger().log(level, msg, **kw)
    except Exception:
        print(f"[{level}] {msg}", flush=True)

class DimensionController:
    """قفل اندازه ویجت‌ها تا با تغییر استایل/متن/تمام‌صفحه نپرند."""
    _registry = {}

    @classmethod
    def lock(cls, widget, w=None, h=None, min_w=None, min_h=None, max_w=None, max_h=None):
        if widget is None:
            return
        key = id(widget)
        if w is not None and h is not None:
            widget.setFixedSize(int(w), int(h))
        else:
            if w is not None:
                widget.setFixedWidth(int(w))
            if h is not None:
                widget.setFixedHeight(int(h))
        if min_w is not None:
            widget.setMinimumWidth(int(min_w))
        if min_h is not None:
            widget.setMinimumHeight(int(min_h))
        if max_w is not None:
            widget.setMaximumWidth(int(max_w))
        if max_h is not None:
            widget.setMaximumHeight(int(max_h))
        cls._registry[key] = {
            "w": w, "h": h, "min_w": min_w, "min_h": min_h,
            "max_w": max_w, "max_h": max_h, "widget": widget,
        }

    @classmethod
    def lock_btn(cls, btn, w=110, h=34):
        """دکمه با اندازه ثابت — متن عوض شود هم اندازه ثابت می‌ماند"""
        if btn is None:
            return btn
        btn.setFixedSize(int(w), int(h))
        btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        cls._registry[id(btn)] = {"w": w, "h": h, "widget": btn}
        return btn

    @classmethod
    def lock_row_buttons(cls, buttons, h=34, min_w=90):
        for b in buttons:
            if b is None:
                continue
            b.setFixedHeight(int(h))
            b.setMinimumWidth(int(min_w))
            b.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

    @classmethod
    def preserve_splitter(cls, splitter):
        """برگرداندن اندازه‌های اسپلیتر بعد از تغییر استایل"""
        if splitter is None:
            return
        sizes = splitter.sizes()
        def _restore():
            try:
                splitter.setSizes(sizes)
            except Exception:
                pass
        QTimer.singleShot(0, _restore)
        QTimer.singleShot(50, _restore)

    @classmethod
    def reapply_all(cls):
        for info in list(cls._registry.values()):
            wdg = info.get("widget")
            if wdg is None:
                continue
            try:
                if info.get("w") and info.get("h"):
                    wdg.setFixedSize(int(info["w"]), int(info["h"]))
                elif info.get("h"):
                    wdg.setFixedHeight(int(info["h"]))
            except Exception as e:
                print(f"[LAYOUT] reapply_all: {e}", flush=True)

def get_persian_type(eng_type):
    for k, v in TYPE_MAP.items():
        if k in eng_type:
            return v
    return eng_type

class ChemicalCalculator:
    """
    مدل «۱۱۸ ظرف اتمی»:
    ────────────────────
    هر عنصر یک ظرف دارد. وقتی ماده اضافه می‌شود، اتم‌هایش
    داخل ظرف همان عنصر می‌روند. برای نمایش فرمول:
      • اگر مقدار ظرف ۱ باشد → فقط نماد (H نه H1)
      • اگر بیشتر باشد → نماد + عدد (H2, O, …)
    ترتیب نمایش: Hill (C، بعد H، بعد بقیه الفبا).
    """
    SUBSCRIPTS = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")
    SUPERSCRIPTS = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")

    ISOTOPE_MAP = {"D": "H", "T": "H"}

    ATOMIC_MASS = {
        "H": 1.008, "D": 2.014, "T": 3.016, "He": 4.0026, "Li": 6.94, "Be": 9.0122,
        "B": 10.81, "C": 12.011, "N": 14.007, "O": 15.999, "F": 18.998, "Ne": 20.180,
        "Na": 22.990, "Mg": 24.305, "Al": 26.982, "Si": 28.085, "P": 30.974, "S": 32.06,
        "Cl": 35.45, "Ar": 39.948, "K": 39.098, "Ca": 40.078, "Sc": 44.956, "Ti": 47.867,
        "V": 50.942, "Cr": 51.996, "Mn": 54.938, "Fe": 55.845, "Co": 58.933, "Ni": 58.693,
        "Cu": 63.546, "Zn": 65.38, "Ga": 69.723, "Ge": 72.630, "As": 74.922, "Se": 78.971,
        "Br": 79.904, "Kr": 83.798, "Rb": 85.468, "Sr": 87.62, "Y": 88.906, "Zr": 91.224,
        "Nb": 92.906, "Mo": 95.95, "Tc": 98.0, "Ru": 101.07, "Rh": 102.91, "Pd": 106.42,
        "Ag": 107.87, "Cd": 112.41, "In": 114.82, "Sn": 118.71, "Sb": 121.76, "Te": 127.60,
        "I": 126.90, "Xe": 131.29, "Cs": 132.91, "Ba": 137.33, "La": 138.91, "Ce": 140.12,
        "Pr": 140.91, "Nd": 144.24, "Pm": 145.0, "Sm": 150.36, "Eu": 151.96, "Gd": 157.25,
        "Tb": 158.93, "Dy": 162.50, "Ho": 164.93, "Er": 167.26, "Tm": 168.93, "Yb": 173.05,
        "Lu": 174.97, "Hf": 178.49, "Ta": 180.95, "W": 183.84, "Re": 186.21, "Os": 190.23,
        "Ir": 192.22, "Pt": 195.08, "Au": 196.97, "Hg": 200.59, "Tl": 204.38, "Pb": 207.2,
        "Bi": 208.98, "Po": 209.0, "At": 210.0, "Rn": 222.0, "Fr": 223.0, "Ra": 226.0,
        "Ac": 227.0, "Th": 232.04, "Pa": 231.04, "U": 238.03, "Np": 237.0, "Pu": 244.0,
        "Am": 243.0, "Cm": 247.0, "Bk": 247.0, "Cf": 251.0, "Es": 252.0, "Fm": 257.0,
        "Md": 258.0, "No": 259.0, "Lr": 266.0, "Rf": 267.0, "Db": 268.0, "Sg": 269.0,
        "Bh": 270.0, "Hs": 269.0, "Mt": 278.0, "Ds": 281.0, "Rg": 282.0, "Cn": 285.0,
        "Nh": 286.0, "Fl": 289.0, "Mc": 290.0, "Lv": 293.0, "Ts": 294.0, "Og": 294.0,
    }

    @staticmethod
    @lru_cache(maxsize=256)
    def atomic_mass_of(el):
        """
        جرم اتمی دقیق یک عنصر. ابتدا از کتابخانهٔ molmass (منبع اصلی و دقیق‌تر که
        در molar_mass هم استفاده می‌شود) گرفته می‌شود تا با بقیهٔ محاسبات همخوان
        بماند؛ اگر molmass نتواند نماد را تشخیص دهد (یا در دسترس نباشد)، از جدول
        کامل ۱۱۸‌تایی ATOMIC_MASS استفاده می‌شود.
        """
        if el in ("D", "T"):
            return ChemicalCalculator.ATOMIC_MASS.get(el, 0.0)
        if HAS_MOLMASS and Formula is not None:
            try:
                m = float(Formula(el).mass)
                if m > 0:
                    return m
            except Exception:
                pass
        return ChemicalCalculator.ATOMIC_MASS.get(el, 0.0)

    @staticmethod
    def to_subscript(text):
        if text is None:
            return ""
        return str(text).translate(ChemicalCalculator.SUBSCRIPTS)

    @staticmethod
    def to_superscript(text):
        if text is None:
            return ""
        return str(text).translate(ChemicalCalculator.SUPERSCRIPTS)

    @staticmethod
    def _normalize_input(formula):
        if formula is None:
            return ""
        s = str(formula).strip()
        if not s or s in ("Mix", "-", "None", "nan", "?"):
            return ""
        s = normalize_chem_formula(s)
        s = re.sub(r'\(\s*(s|l|g|aq)\s*\)', '', s, flags=re.I)
        s = s.replace("·", ".").replace("•", ".")
        s = re.sub(
            r'\.(\d*)\s*H\s*2\s*O',
            lambda m: "(H2O)" + (m.group(1) if m.group(1) else "1"),
            s,
            flags=re.I,
        )
        return s.strip()

    @staticmethod
    @lru_cache(maxsize=2048)
    def _parse_formula_cached(s, merge_isotopes):
        """نسخهٔ کش‌شدهٔ تجزیهٔ فرمول (ورودی نرمال‌شده)."""
        if not s:
            return ()
        if HAS_MOLMASS and Formula is not None:
            try:
                f = Formula(s)
                items = []
                for key, count in f.composition.items():
                    sym = getattr(key, "symbol", None) or str(key)
                    m = re.match(r'^([A-Z][a-z]?)$', str(sym).strip())
                    if not m:
                        m = re.search(r'([A-Z][a-z]?)', str(sym))
                    if not m:
                        continue
                    el = m.group(1)
                    if merge_isotopes:
                        el = ChemicalCalculator.ISOTOPE_MAP.get(el, el)
                    n = int(round(float(count)))
                    if n > 0:
                        items.append((el, n))
                if items:
                    return tuple(items)
            except Exception:
                pass
        # بدون molmass، fallback سادهٔ regex نباید قبل از parser گروهی اجرا شود؛
        # در غیر این صورت Ca(OH)2 به Ca:1,O:1,H:1 تبدیل می‌شد.
        return ()

    @staticmethod
    def parse_formula(formula, merge_isotopes=False):
        """
        یک مولکول از ماده → چند اتم در هر ظرف.
        مثال: H2O → {H: 2, O: 1}
              D2O → {D: 2, O: 1} یا با merge → {H: 2, O: 1}
        """
        s = ChemicalCalculator._normalize_input(formula)
        if not s:
            return Counter()
        # ورودی‌های دارای HTML/SQL/کاراکترهای تصادفی را به‌عنوان فرمول شیمیایی نپذیر.
        # بار یونی انتهایی (+/-) مجاز است ولی بخشی از فرمول اتمی نیست.
        s = re.sub(r"[+-]+$", "", s)
        if not s or not re.fullmatch(r"[A-Za-z0-9().]+", s) or not s[0].isupper():
            return Counter()
        try:
            items = ChemicalCalculator._parse_formula_cached(s, bool(merge_isotopes))
            if items:
                return Counter(dict(items))
        except Exception:
            pass

        if HAS_MOLMASS and Formula is not None:
            try:
                f = Formula(s)
                comp = Counter()
                for key, count in f.composition.items():
                    sym = getattr(key, "symbol", None) or str(key)
                    m = re.match(r'^([A-Z][a-z]?)$', str(sym).strip())
                    if not m:
                        m = re.search(r'([A-Z][a-z]?)', str(sym))
                    if not m:
                        continue
                    el = m.group(1)
                    if merge_isotopes:
                        el = ChemicalCalculator.ISOTOPE_MAP.get(el, el)
                    n = int(round(float(count)))
                    if n > 0:
                        comp[el] += n
                if comp:
                    return comp
            except Exception:
                pass

        i, nlen = 0, len(s)

        def parse_int():
            nonlocal i
            start = i
            while i < nlen and s[i].isdigit():
                i += 1
            return 1 if start == i else int(s[start:i])

        def parse_element():
            nonlocal i
            if i >= nlen or not s[i].isupper():
                return None, 0
            start = i
            i += 1
            if i < nlen and s[i].islower():
                i += 1
            el = s[start:i]
            cnt = parse_int()
            if merge_isotopes:
                el = ChemicalCalculator.ISOTOPE_MAP.get(el, el)
            return el, cnt

        def parse_group():
            nonlocal i
            counts = Counter()
            while i < nlen:
                ch = s[i]
                if ch == '(':
                    i += 1
                    inner = parse_group()
                    if i < nlen and s[i] == ')':
                        i += 1
                    mult = parse_int()
                    for el, c in inner.items():
                        counts[el] += c * mult
                elif ch == ')':
                    break
                elif ch.isupper():
                    el, cnt = parse_element()
                    if el:
                        counts[el] += cnt
                else:
                    i += 1
            return counts

        try:
            result = parse_group()
            if result:
                # نماد ناشناخته نباید جرم مولی جعلی تولید کند.
                if any(el not in ChemicalCalculator.ATOMIC_MASS for el in result):
                    return Counter()
                return result
        except Exception:
            pass

        flat = Counter()
        for el, num in re.findall(r'([A-Z][a-z]*)(\d*)', s):
            if merge_isotopes:
                el = ChemicalCalculator.ISOTOPE_MAP.get(el, el)
            flat[el] += int(num) if num else 1
        return flat

    @staticmethod
    def molar_mass(formula):
        s = ChemicalCalculator._normalize_input(formula)
        if not s:
            return 0.0
        if HAS_MOLMASS and Formula is not None:
            try:
                return float(Formula(s).mass)
            except Exception:
                pass
        total = 0.0
        for el, cnt in ChemicalCalculator.parse_formula(s, merge_isotopes=False).items():
            total += ChemicalCalculator.atomic_mass_of(el) * cnt
        return total

    @staticmethod
    def _hill_order(symbols):
        syms = list(symbols)
        ordered = []
        for prefer in ("C", "H", "D", "T"):
            if prefer in syms:
                ordered.append(prefer)
                syms.remove(prefer)
        ordered.extend(sorted(syms))
        return ordered

    @staticmethod
    def format_from_slots(slots, subscript=True):
        """
        خواندن ظرف‌ها و ساخت فرمول.
        تعداد ۱ → بدون عدد | تعداد > ۱ → با عدد
        """
        if not slots:
            return ""
        parts = []
        for el in ChemicalCalculator._hill_order(slots.keys()):
            try:
                n = float(slots[el])
            except (TypeError, ValueError):
                continue
            n_int = int(round(n))
            if n_int <= 0:
                continue
            parts.append(el if n_int == 1 else f"{el}{n_int}")
        text = "".join(parts)
        return ChemicalCalculator.to_subscript(text) if subscript else text

    @staticmethod
    def reduce_slots(atom_amounts):
        """نسبت صحیح ساده با NumPy — سریع و پایدار."""
        if not atom_amounts:
            return {}
        els = []
        vals = []
        for k, v in atom_amounts.items():
            try:
                fv = float(v)
            except (TypeError, ValueError):
                continue
            if np.isfinite(fv) and fv > 1e-12:
                els.append(str(k))
                vals.append(fv)
        if not els:
            return {}
        arr = np.asarray(vals, dtype=np.float64)
        min_v = float(arr.min())
        if min_v <= 0:
            return {}
        ratios = arr / min_v
        mults = np.arange(1, 49, dtype=np.float64)
        targets = ratios[np.newaxis, :] * mults[:, np.newaxis]  # (48, n)
        rounded = np.maximum(1, np.rint(targets)).astype(np.int64)
        err = np.abs(targets - rounded) + 0.05 * np.abs(targets - rounded) / np.maximum(1.0, targets)
        err_sum = err.sum(axis=1)
        too_small = (targets < 0.5).any(axis=1)
        err_sum = err_sum + too_small.astype(np.float64) * 2.0
        best_i = int(np.argmin(err_sum))
        best_rounded = rounded[best_i]
        g = int(best_rounded[0])
        for n in best_rounded[1:]:
            g = int(np.gcd(g, int(n)))
        if g > 1:
            best_rounded = best_rounded // g
        return {els[i]: int(best_rounded[i]) for i in range(len(els))}

    @staticmethod
    def calculate_empirical_from_moles(atom_moles_counter):
        if not atom_moles_counter:
            return "ماده‌ای وجود ندارد"
        slots = ChemicalCalculator.reduce_slots(atom_moles_counter)
        if not slots:
            return "-"
        return ChemicalCalculator.format_from_slots(slots, subscript=True)

    @staticmethod
    def moles_of_elements(formula, compound_moles):
        try:
            cm = float(compound_moles)
        except (TypeError, ValueError):
            cm = 0.0
        comp = ChemicalCalculator.parse_formula(formula)
        return Counter({el: cm * n for el, n in comp.items()})

    @staticmethod
    def fill_atom_jars(contents_moles, db, merge_isotopes=True):
        """
        قلب ایدهٔ ۱۱۸ ظرف:
        contents = {کلید_ماده: مول_ماده}
        برای هر ماده فرمولش را بخوان و اتم‌ها را در ظرف‌ها بریز.
        """
        jars = Counter()  # نماد عنصر → مجموع «اتم·مول»
        details = []      # برای دیباگ
        if not contents_moles:
            return jars, details

        for key, moles in contents_moles.items():
            try:
                m = float(moles)
            except (TypeError, ValueError):
                continue
            if m <= 1e-12:
                continue

            form = ""
            name = key
            db_entry = None
            if db:
                if key in db:
                    db_entry = db[key]
                else:
                    nk = str(key).strip().lower()
                    if nk in db:
                        db_entry = db[nk]
                    else:
                        for dk, dv in db.items():
                            if str(dk).lower() == nk or str(dv.get("formula", "")).lower() == nk:
                                db_entry = dv
                                break
            if db_entry:
                form = str(db_entry.get("formula") or "")
                name = db_entry.get("name", key)
            if not form or form in ("-", "?", "None", "nan"):
                form = str(key)

            atoms = ChemicalCalculator.parse_formula(form, merge_isotopes=merge_isotopes)
            if not atoms:
                atoms = ChemicalCalculator.parse_formula(form, merge_isotopes=False)
            if not atoms:
                details.append(f"{name}: فرمول «{form}» قابل تجزیه نبود")
                continue

            for el, cnt in atoms.items():
                jars[el] += cnt * m
            details.append(
                f"{name} ({form}) × {m:.4g} mol → " +
                ", ".join(f"{el}:{cnt*m:.4g}" for el, cnt in atoms.items())
            )
        return jars, details

    @staticmethod
    def mixture_formula(contents_moles, db, merge_isotopes=True):
        """
        ساخت فرمول از ظرف‌های اتمی.
        - یک ماده → فرمول مولکولی همان ماده (از دیتابیس)
        - چند ماده → فرمول تجربی از روی ظرف‌ها
        """
        if not contents_moles:
            return "-"
        active = {}
        for k, v in contents_moles.items():
            try:
                fv = float(v)
            except (TypeError, ValueError):
                continue
            if fv > 1e-10:
                active[k] = fv
        if not active:
            return "-"

        if len(active) == 1:
            key = next(iter(active))
            if db and key in db:
                form = str(db[key].get("formula") or "").strip()
                if form and form not in ("-", "?", "None", "nan"):
                    norm = ChemicalCalculator._normalize_input(form) or form
                    return ChemicalCalculator.to_subscript(norm)
            return ChemicalCalculator.to_subscript(
                ChemicalCalculator._normalize_input(str(key)) or str(key)
            )

        jars, _details = ChemicalCalculator.fill_atom_jars(
            active, db, merge_isotopes=merge_isotopes
        )
        if not jars:
            return "-"
        return ChemicalCalculator.calculate_empirical_from_moles(jars)

    @staticmethod
    def convert_temperature(value, from_unit, to_unit):
        """°C / K / °F"""
        try:
            v = float(value)
        except (TypeError, ValueError):
            return None
        if from_unit == "C":
            k = v + 273.15
        elif from_unit == "F":
            k = (v - 32) * 5.0 / 9.0 + 273.15
        else:
            k = v
        if to_unit == "C":
            return k - 273.15
        if to_unit == "F":
            return (k - 273.15) * 9.0 / 5.0 + 32
        return k

    @staticmethod
    def convert_energy(value, from_unit, to_unit):
        """kJ / kcal / eV  (بر اساس ۱ مول معادل برای eV از kJ/mol تقریبی)"""
        factors = {"kJ": 1000.0, "kcal": 4184.0, "eV": 1.602176634e-19}
        try:
            v = float(value)
        except (TypeError, ValueError):
            return None
        joules = v * factors.get(from_unit, 1.0)
        return joules / factors.get(to_unit, 1.0)

    @staticmethod
    def ideal_gas_volume(n, T_c, P_atm, R=0.082057):
        """PV=nRT → V (لیتر). T به کلوین، P اتمسفر"""
        try:
            n, T_c, P_atm = float(n), float(T_c), float(P_atm)
            if P_atm <= 0 or n < 0:
                return None
            T_k = T_c + 273.15
            if T_k <= 0 or not math.isfinite(T_k):
                return None
            return (n * R * T_k) / P_atm
        except (TypeError, ValueError):
            return None

    @staticmethod
    def elemental_mass_percent(formula):
        """فرمول → {عنصر: درصد جرمی}"""
        atoms = ChemicalCalculator.parse_formula(formula)
        if not atoms:
            return {}
        total = 0.0
        masses = {}
        for el, cnt in atoms.items():
            m = ChemicalCalculator.atomic_mass_of(el) * cnt
            masses[el] = m
            total += m
        if total <= 0:
            return {}
        return {el: (m / total) * 100.0 for el, m in masses.items()}

    @staticmethod
    def empirical_from_percentages(percent_dict):
        """{عنصر: درصد جرمی} → فرمول تجربی"""
        if not percent_dict:
            return "-"
        moles = {}
        for el, pct in percent_dict.items():
            try:
                p = float(pct)
            except (TypeError, ValueError):
                continue
            mass = ChemicalCalculator.atomic_mass_of(el)
            if mass > 0 and p > 0:
                moles[el] = p / mass
        if not moles:
            return "-"
        return ChemicalCalculator.calculate_empirical_from_moles(moles)

    @staticmethod
    def simple_stoichiometry(reactants_coeffs, products_coeffs, known_key, known_mass_g):
        """
        reactants_coeffs / products_coeffs: dict نماد→ضریب
        known_key: نماد ماده‌ای که جرمش معلوم است
        خروجی: dict نماد → جرم محاسبه‌شده (g)
        """
        try:
            known_mass = float(known_mass_g)
        except (TypeError, ValueError):
            return {}
        all_coeffs = {}
        all_coeffs.update(reactants_coeffs or {})
        all_coeffs.update(products_coeffs or {})
        if known_key not in all_coeffs or all_coeffs[known_key] <= 0:
            return {}
        mm_known = ChemicalCalculator.molar_mass(known_key)
        if mm_known <= 0:
            return {}
        moles_known = known_mass / mm_known
        base = moles_known / all_coeffs[known_key]
        result = {}
        for sym, coef in all_coeffs.items():
            mm = ChemicalCalculator.molar_mass(sym)
            if mm > 0:
                result[sym] = base * coef * mm
        return result

    @staticmethod
    def colligative_delta(molality, i_factor=1.0, Kb=0.512, Kf=1.86):
        """افزایش نقطه جوش و کاهش نقطه انجماد آب"""
        try:
            m = float(molality)
            i = float(i_factor)
        except (TypeError, ValueError):
            return None, None
        dTb = i * Kb * m
        dTf = i * Kf * m
        return dTb, dTf

    @staticmethod
    def electron_configuration(z):
        """آرایش الکترونی با استثناهای شناخته‌شده (Cr, Cu, Mo, Ag, Au, ...)"""
        try:
            z = int(z)
        except (TypeError, ValueError):
            return ""
        if z <= 0 or z > 118:
            return ""
        # استثناهای Madelung شناخته‌شده (آموزشی — تا Z~100)
        EXCEPTIONS = {
            24: "1s² 2s² 2p⁶ 3s² 3p⁶ 4s¹ 3d⁵",   # Cr
            29: "1s² 2s² 2p⁶ 3s² 3p⁶ 4s¹ 3d¹⁰",  # Cu
            41: "1s² 2s² 2p⁶ 3s² 3p⁶ 4s² 3d¹⁰ 4p⁶ 5s¹ 4d⁴",  # Nb approx
            42: "1s² 2s² 2p⁶ 3s² 3p⁶ 4s² 3d¹⁰ 4p⁶ 5s¹ 4d⁵",  # Mo
            44: "1s² 2s² 2p⁶ 3s² 3p⁶ 4s² 3d¹⁰ 4p⁶ 5s¹ 4d⁷",  # Ru
            45: "1s² 2s² 2p⁶ 3s² 3p⁶ 4s² 3d¹⁰ 4p⁶ 5s¹ 4d⁸",  # Rh
            46: "1s² 2s² 2p⁶ 3s² 3p⁶ 4s² 3d¹⁰ 4p⁶ 4d¹⁰",     # Pd
            47: "1s² 2s² 2p⁶ 3s² 3p⁶ 4s² 3d¹⁰ 4p⁶ 5s¹ 4d¹⁰", # Ag
            78: "1s² 2s² 2p⁶ 3s² 3p⁶ 4s² 3d¹⁰ 4p⁶ 5s² 4d¹⁰ 5p⁶ 6s¹ 4f¹⁴ 5d⁹",  # Pt approx
            79: "1s² 2s² 2p⁶ 3s² 3p⁶ 4s² 3d¹⁰ 4p⁶ 5s² 4d¹⁰ 5p⁶ 6s¹ 4f¹⁴ 5d¹⁰", # Au
        }
        if z in EXCEPTIONS:
            # occupancy از قبل با superscript است؛ شماره پوسته را دست نزن
            return EXCEPTIONS[z]
        order = [
            ("1s", 2), ("2s", 2), ("2p", 6), ("3s", 2), ("3p", 6),
            ("4s", 2), ("3d", 10), ("4p", 6), ("5s", 2), ("4d", 10),
            ("5p", 6), ("6s", 2), ("4f", 14), ("5d", 10), ("6p", 6),
            ("7s", 2), ("5f", 14), ("6d", 10), ("7p", 6),
        ]
        rem = z
        parts = []
        for orb, cap in order:
            if rem <= 0:
                break
            fill = min(rem, cap)
            if fill > 0:
                parts.append(f"{orb}{ChemicalCalculator.to_superscript(str(fill))}")
            rem -= fill
        return " ".join(parts)

    @staticmethod
    def estimate_reaction_delta_h(reactants_keys, products_keys, db, rxn_dH=None):
        """
        ΔH واکنش:
        - اگر rxn_dH از دیتابیس واکنش داده شده باشد همان استفاده می‌شود
        - وگرنه تقریب از فیلد heat مواد
        """
        if rxn_dH is not None:
            try:
                return float(rxn_dH)
            except (TypeError, ValueError):
                pass
        def heats(keys):
            if not keys:
                return np.array([], dtype=np.float64)
            vals = []
            for k in keys:
                nk = normalize_key(k)
                data = db.get(nk) or db.get(k) or {}
                vals.append(safe_float(data.get("heat", 0.0), 0.0))
            return np.asarray(vals, dtype=np.float64)
        return float(heats(products_keys).sum() - heats(reactants_keys).sum())

    @staticmethod
    def find_limiting_reagent(reactants_needed, contents_moles, db, coeffs=None):
        """
        خروجی: (کلید محدودکننده, مول موجود, درصد تبدیل, extent)
        با NumPy برای سرعت و پایداری عددی.
        """
        if not reactants_needed:
            return None, 0.0, 0.0, 0.0
        if coeffs is None:
            coeffs = {}
        content_pairs = []
        for ck, cm in (contents_moles or {}).items():
            nk = normalize_key(ck)
            form = normalize_key((db.get(ck) or {}).get("formula", ""))
            content_pairs.append((nk, form, safe_float(cm, 0.0)))

        keys = []
        moles_list = []
        coef_list = []
        for r in reactants_needed:
            nk = normalize_key(r)
            moles = 0.0
            for cn, cf, cm in content_pairs:
                if cn == nk or cf == nk:
                    moles += cm
            coef = max(1e-12, float(coeffs.get(r, coeffs.get(nk, 1)) or 1))
            keys.append(r)
            moles_list.append(moles)
            coef_list.append(coef)

        if not keys:
            return None, 0.0, 0.0, 0.0
        moles_arr = np.asarray(moles_list, dtype=np.float64)
        coef_arr = np.asarray(coef_list, dtype=np.float64)
        extent_arr = moles_arr / coef_arr
        masked = np.where(extent_arr > 1e-15, extent_arr, 1e99)
        i = int(np.argmin(masked))
        lim_extent = float(extent_arr[i])
        lim_key = keys[i]
        lim_moles = float(moles_arr[i])
        if lim_extent <= 1e-15:
            return lim_key, 0.0, 0.0, 0.0
        # Conversion: درصد مصرف ماده محدودکننده نسبت به موجودی خودش
        # (تعریف آموزشی پایدار و deterministic — نه میانگین extent دیگران)
        if lim_moles > 1e-15:
            used = lim_extent * float(coef_arr[i])
            conv = float(np.clip((used / lim_moles) * 100.0, 0.0, 100.0))
        else:
            conv = 0.0
        return lim_key, lim_moles, conv, lim_extent

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
        self._undo_stack = []  # تاریخچه وضعیت ظرف برای Undo
        self._redo_stack = []  # تاریخچه برای Redo
        self.safety_warnings_count = 0  # تعداد هشدارهای ایمنی
        self.last_titration_endpoint_vol = 0.0
        self.titration_analyte_conc = None

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
            {"id": "m8", "title": "واکنش گرمازا", "desc": "یک واکنش گرمازا (ΔH منفی) کشف کنید.", "xp": 35},
        ]
        self.last_reaction_thermo = None  # آخرین تحلیل ترمودینامیکی واکنش
        self.last_limiting_reagent = None

        self.reset()
        self.load_data()  # بعد از reset تا پیشرفت و محتویات از lab_save.json برگردد
        self.add_to_log("آزمایشگاه راه‌اندازی شد.")

    def add_to_log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{ts}] {msg}"
        self.auto_log.append(log_entry)
        if len(self.auto_log) > 500:
            self.auto_log.pop(0)
        try:
            get_logger().info(msg)
        except Exception:
            pass

    def reset(self):
        self.total_volume = 0.0
        self.moles_h = 0.0
        self.moles_oh = 0.0
        self.temp_c = 25.0
        self.contents = {}
        self.visual_layers = []
        self.is_broken = False
        self.titration_volume = 0.0
        self.last_titration_endpoint_vol = 0.0
        self.titration_analyte_conc = None
        self._titration_initial_volume = None
        self.last_update = time.time()
        self.add_to_log("ظرف آزمایش ریست شد.")

    def load_data(self):
        save_path = get_save_path(self.player_name)
        legacy = get_save_path(None)
        path_to_use = save_path if os.path.exists(save_path) else None
        if path_to_use is None and os.path.exists(legacy):
            try:
                with open(legacy, "r", encoding="utf-8") as f:
                    leg = json.load(f)
                if isinstance(leg, dict) and str(leg.get("player_name", "")).strip() == str(self.player_name or "").strip():
                    path_to_use = legacy
            except Exception:
                path_to_use = None
        if not path_to_use:
            return
        try:
            with open(path_to_use, "r", encoding="utf-8") as f:
                d = json.load(f)
            if not isinstance(d, dict):
                return
            self.score = max(0, min(10_000_000, safe_int(d.get("score", 0), 0)))
            self.level = max(1, min(9999, safe_int(d.get("level", 1), 1)))
            raw_disc = d.get("discovered", []) or []
            self.discovered = (
                set(str(x) for x in raw_disc[:5000])
                if isinstance(raw_disc, (list, tuple, set)) else set()
            )
            saved_name = str(d.get("player_name", "") or "").strip()
            if saved_name and saved_name == str(self.player_name or "").strip():
                self.player_name = saved_name[:64]
            self.notes = str(d.get("notes", "") or "")[:50000]
            raw_badges = d.get("badges", []) or []
            self.badges = (
                set(str(x) for x in raw_badges[:500])
                if isinstance(raw_badges, (list, tuple, set)) else set()
            )
            raw_missions = d.get("completed_missions", []) or []
            self.completed_missions = (
                set(str(x) for x in raw_missions[:500])
                if isinstance(raw_missions, (list, tuple, set)) else set()
            )
            self.flask_label = str(d.get("flask_label", "بشر شماره ۱") or "بشر شماره ۱")
            if isinstance(d.get("stats"), dict):
                self.stats.update(d["stats"])
            if "temp_c" in d:
                self.temp_c = max(-273.15, min(2000.0, safe_float(d.get("temp_c"), 25.0)))
            if isinstance(d.get("contents"), dict):
                self.contents = {str(k): max(0.0, safe_float(v, 0.0)) for k, v in d["contents"].items()}
            if "total_volume" in d:
                self.total_volume = max(0.0, safe_float(d.get("total_volume"), 0.0))
            if "moles_h" in d:
                self.moles_h = max(0.0, safe_float(d.get("moles_h"), 0.0))
            if "moles_oh" in d:
                self.moles_oh = max(0.0, safe_float(d.get("moles_oh"), 0.0))
            if isinstance(d.get("visual_layers"), list):
                self.visual_layers = d["visual_layers"]
            if path_to_use == legacy:
                try:
                    self.save_data()
                except Exception:
                    pass
        except Exception as e:
            print(f"[SAVE][ERROR] بارگذاری وضعیت کاربر ناموفق: {e}", flush=True)

    def save_data(self):
        save_path = get_save_path(self.player_name)
        try:
            os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)
            payload = {
                "schema_version": SCHEMA_VERSION,
                "score": int(max(0, min(10_000_000, self.score))),
                "level": int(max(1, min(9999, self.level))),
                "discovered": list(self.discovered),
                "player_name": str(self.player_name or "دانشجو"),
                "user_id": _user_id_from_name(self.player_name),
                "notes": str(self.notes or ""),
                "badges": list(self.badges),
                "completed_missions": list(self.completed_missions),
                "flask_label": str(self.flask_label or "بشر شماره ۱"),
                "stats": dict(self.stats) if isinstance(self.stats, dict) else {},
                "temp_c": float(self.temp_c),
                "contents": {str(k): float(v) for k, v in (self.contents or {}).items()},
                "total_volume": float(self.total_volume),
                "moles_h": float(getattr(self, "moles_h", 0) or 0),
                "moles_oh": float(getattr(self, "moles_oh", 0) or 0),
                "last_titration_endpoint_vol": float(getattr(self, "last_titration_endpoint_vol", 0) or 0),
                "titration_analyte_conc": getattr(self, "titration_analyte_conc", None),
                "visual_layers": list(self.visual_layers or []),
            }
            tmp = save_path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
                f.flush()
                try:
                    os.fsync(f.fileno())
                except Exception:
                    pass
            os.replace(tmp, save_path)
        except Exception as e:
            print(f"[SAVE][ERROR] ذخیره وضعیت کاربر ناموفق ({save_path}): {e}", flush=True)
            try:
                get_logger().error(f"save_data failed: {e}")
            except Exception:
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
            "last_titration_endpoint_vol": self.last_titration_endpoint_vol,
            "titration_analyte_conc": self.titration_analyte_conc,
            "flask_label": self.flask_label, "stats": self.stats
        }

    def from_dict(self, d):
        if not isinstance(d, dict):
            raise ValueError("داده بارگذاری باید dict باشد")
        # اعتبارسنجی سخت‌گیرانه — JSON دستکاری‌شده نباید state را خراب کند
        score = max(0, safe_int(d.get("score", 0), 0))
        level = max(1, min(9999, safe_int(d.get("level", 1), 1)))
        self.score = score
        self.level = level
        # Imported state cannot change the identity of the logged-in user.
        imported_name = str(d.get("player_name", "") or "").strip()
        if not self.player_name:
            self.player_name = imported_name[:64] or "دانشجو"
        disc = d.get("discovered", []) or []
        self.discovered = set(str(x) for x in disc) if isinstance(disc, (list, set, tuple)) else set()
        badges = d.get("badges", []) or []
        self.badges = set(str(x) for x in badges) if isinstance(badges, (list, set, tuple)) else set()
        cm = d.get("completed_missions", []) or []
        self.completed_missions = set(str(x) for x in cm) if isinstance(cm, (list, set, tuple)) else set()
        self.notes = str(d.get("notes", "") or "")[:50000]
        vol = safe_float(d.get("total_volume", 0.0), 0.0)
        self.total_volume = max(0.0, min(self.max_capacity, vol))
        self.moles_h = max(0.0, safe_float(d.get("moles_h", 0.0), 0.0))
        self.moles_oh = max(0.0, safe_float(d.get("moles_oh", 0.0), 0.0))
        temp = safe_float(d.get("temp_c", 25.0), 25.0)
        self.temp_c = max(-273.15, min(5000.0, temp))
        raw_contents = d.get("contents", {}) if isinstance(d.get("contents"), dict) else {}
        clean_contents = {}
        for k, v in raw_contents.items():
            sk = str(k).strip().lower()
            if not sk or len(sk) > 64:
                continue
            fv = safe_float(v, 0.0)
            if fv > 0 and math.isfinite(fv) and fv < 1e9:
                clean_contents[sk] = fv
        self.contents = clean_contents
        layers = d.get("visual_layers", [])
        self.visual_layers = []
        if isinstance(layers, list):
            for layer in layers[:200]:
                if not isinstance(layer, dict):
                    continue
                amt = safe_float(layer.get("amount", 0), 0.0)
                moles = safe_float(layer.get("moles", 0), 0.0)
                if amt <= 0 and moles <= 0:
                    continue
                cl = copy.deepcopy(layer)
                cl["amount"] = max(0.0, min(1e6, amt))
                cl["moles"] = max(0.0, min(1e9, moles))
                cl["key"] = str(cl.get("key", ""))[:64]
                cl["name"] = str(cl.get("name", ""))[:128]
                self.visual_layers.append(cl)
        raw_broken = d.get("is_broken", False)
        self.is_broken = (
            raw_broken if isinstance(raw_broken, bool)
            else str(raw_broken).strip().lower() in {"1", "true", "yes", "on"}
        )
        self.titration_volume = max(0.0, safe_float(d.get("titration_volume", 0.0), 0.0))
        self.last_titration_endpoint_vol = max(0.0, safe_float(d.get("last_titration_endpoint_vol", 0.0), 0.0))
        raw_analyte = d.get("titration_analyte_conc")
        self.titration_analyte_conc = max(0.0, safe_float(raw_analyte, 0.0)) if raw_analyte is not None else None
        self._titration_initial_volume = None
        self.flask_label = str(d.get("flask_label", "بشر شماره ۱") or "بشر شماره ۱")[:64]
        if "stats" in d and isinstance(d["stats"], dict):
            for sk, sv in d["stats"].items():
                if sk in self.stats:
                    if isinstance(self.stats[sk], (int, float)):
                        self.stats[sk] = max(0, safe_int(sv, 0) if isinstance(self.stats[sk], int) else max(0.0, safe_float(sv, 0.0)))
                    else:
                        self.stats[sk] = sv
        if self.visual_layers:
            try:
                self.layer_id_counter = max([safe_int(l.get('id', 0), 0) for l in self.visual_layers]) + 1
            except Exception as e:
                print(f"[LOAD] layer_id_counter: {e}", flush=True)
                self.layer_id_counter = len(self.visual_layers) + 1
        # Rebuild derived chemistry values instead of trusting stale serialized values.
        try:
            self.rebuild_acid_base_moles()
            if self.visual_layers:
                self.total_volume = max(0.0, sum(safe_float(l.get("amount", 0), 0.0) for l in self.visual_layers))
        except Exception as e:
            tlog(f"state consistency rebuild: {e}", "WARN")
        self.save_data()
        self.add_to_log("وضعیت آزمایش از فایل بارگذاری شد.")

    def _make_snapshot(self):
        """ساخت snapshot کامل وضعیت ظرف"""
        return {
            "total_volume": self.total_volume,
            "moles_h": self.moles_h,
            "moles_oh": self.moles_oh,
            "temp_c": self.temp_c,
            "contents": copy.deepcopy(self.contents),
            "visual_layers": copy.deepcopy(self.visual_layers),
            "is_broken": self.is_broken,
            "titration_volume": self.titration_volume,
        }

    def push_undo(self):
        """ذخیره وضعیت فعلی ظرف برای بازگشت (deepcopy برای جلوگیری از ارجاع مشترک)"""
        snap = self._make_snapshot()
        self._undo_stack.append(snap)
        self._redo_stack.clear()  # هر عمل جدید، redo را پاک می‌کند
        if len(self._undo_stack) > 40:
            self._undo_stack.pop(0)

    def undo(self):
        if not self._undo_stack:
            return False
        self._redo_stack.append(self._make_snapshot())
        snap = self._undo_stack.pop()
        self.total_volume = snap["total_volume"]
        self.moles_h = snap["moles_h"]
        self.moles_oh = snap["moles_oh"]
        self.temp_c = snap["temp_c"]
        self.contents = copy.deepcopy(snap["contents"])
        self.visual_layers = copy.deepcopy(snap["visual_layers"])
        self.is_broken = snap["is_broken"]
        self.titration_volume = snap["titration_volume"]
        self.add_to_log(f"↩ بازگشت به حالت قبل (باقی‌مانده: {len(self._undo_stack)})")
        return True

    def redo(self):
        if not self._redo_stack:
            return False
        self._undo_stack.append(self._make_snapshot())
        snap = self._redo_stack.pop()
        self.total_volume = snap["total_volume"]
        self.moles_h = snap["moles_h"]
        self.moles_oh = snap["moles_oh"]
        self.temp_c = snap["temp_c"]
        self.contents = copy.deepcopy(snap["contents"])
        self.visual_layers = copy.deepcopy(snap["visual_layers"])
        self.is_broken = snap["is_broken"]
        self.titration_volume = snap["titration_volume"]
        self.add_to_log(f"↪ جلو رفتن (Redo) — باقی‌مانده Redo: {len(self._redo_stack)}")
        return True

    def undo_count(self):
        return len(self._undo_stack)

    def redo_count(self):
        return len(self._redo_stack)

    def filter_solids(self):
        """جداسازی: جامدات در ظرف می‌مانند؛ مایع و گاز دور ریخته می‌شوند."""
        if self.is_broken:
            return []
        self.push_undo()
        discarded = []
        kept_layers = []
        discarded_moles = Counter()
        for layer in self.visual_layers:
            db_type = CHEMILAB_DB.get(layer['key'], {}).get('type', '')
            layer_type = layer.get('type', '')
            combined_type = f"{db_type} {layer_type}"
            is_solid = is_solid_chemical_type(combined_type)
            is_solid = is_solid or any(
                k in str(layer_type) for k in ["جامد", "فلز", "رسوب", "پودر", "آلیاژ", "نمک", "Solid", "Metal", "Salt", "Precipitate"]
            )
            if is_solid:
                kept_layers.append(layer)
            else:
                discarded.append(layer['name'])
                self.total_volume -= layer['amount']
                discarded_moles[layer['key']] += layer.get('moles', 0.0)
        for key, moles in discarded_moles.items():
            if key in self.contents:
                self.contents[key] -= moles
                if self.contents[key] <= 1e-12:
                    del self.contents[key]
        self.visual_layers = kept_layers
        self.total_volume = sum(l.get('amount', 0) for l in kept_layers)
        if self.total_volume < 0:
            self.total_volume = 0
        try:
            self.rebuild_acid_base_moles()
        except Exception:
            pass
        if discarded:
            self.stats["filter_uses"] += 1
            self.add_to_log(f"مایع/گاز دور ریخته شد؛ جامدات باقی ماند: {', '.join(discarded)}")
        return discarded

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
        # ── اعتبارسنجی ورودی: هیچ مقدار نامعتبر نباید state را خراب کند ──
        try:
            amount = float(amount)
        except (TypeError, ValueError):
            return "خطا: مقدار افزودن نامعتبر است.", False, warnings
        if not math.isfinite(amount) or amount <= 0:
            return "خطا: مقدار باید عدد مثبت و محدود باشد.", False, warnings
        if amount > 1e6:
            return "خطا: مقدار بیش از حد مجاز است.", False, warnings
        if custom_molarity is not None:
            try:
                custom_molarity = float(custom_molarity)
            except (TypeError, ValueError):
                return "خطا: غلظت نامعتبر است.", False, warnings
            if not math.isfinite(custom_molarity) or custom_molarity < 0:
                return "خطا: غلظت باید عدد غیرمنفی و محدود باشد.", False, warnings
            if custom_molarity > 1e4:
                return "خطا: غلظت بیش از حد مجاز است.", False, warnings
        if not key or not isinstance(key, str):
            return "خطا: کلید ماده نامعتبر است.", False, warnings
        key = key.lower().strip()
        if key not in CHEMILAB_DB:
            return "خطا: ماده یافت نشد", False, warnings

        # Snapshot only after the material key has been validated.
        self.push_undo()
        data = CHEMILAB_DB[key]
        chem_type = data.get('type', '')

        existing_types = [CHEMILAB_DB.get(k, {}).get('type', '') for k in self.contents]
        existing_keys = list(self.contents.keys())
        if key == "h2o" and any("Acid" in t for t in existing_types):
            warnings.append(
                "⚠️ خطر ایمنی: افزودن آب به اسید می‌تواند باعث پاشش خطرناک شود! (همیشه اسید به آب افزوده شود)")
            self.safety_warnings_count += 1
        if "Strong Acid" in chem_type and any("Strong Base" in t for t in existing_types):
            warnings.append("⚠️ این مخلوط به شدت گرمازاست (اسید قوی + باز قوی) — احتیاط کنید.")
            self.safety_warnings_count += 1
        elif "Strong Base" in chem_type and any("Strong Acid" in t for t in existing_types):
            warnings.append("⚠️ این مخلوط به شدت گرمازاست (اسید قوی + باز قوی) — احتیاط کنید.")
            self.safety_warnings_count += 1
        if "Gas" in chem_type or any("Gas" in t for t in existing_types):
            if any(x in chem_type for x in ["Acid", "Base"]) or any(
                    any(x in t for x in ["Acid", "Base"]) for t in existing_types):
                warnings.append("💨 احتمال تولید گاز وجود دارد — ظرف را در فضای باز فرض کنید.")
                self.safety_warnings_count += 1
        if any("Oxidizer" in t or "Explosive" in t for t in existing_types + [chem_type]):
            warnings.append("🔥 ماده اکسیدکننده/منفجره در ظرف است — از حرارت شدید پرهیز کنید.")
            self.safety_warnings_count += 1
        if "Metal" in chem_type and any("Acid" in t for t in existing_types):
            warnings.append("💨 فلز + اسید → احتمال تولید گاز هیدروژن.")
            self.safety_warnings_count += 1
        if self.temp_c > 150:
            warnings.append(f"🌡️ دمای ظرف بسیار بالاست ({self.temp_c:.0f}°C) — افزودن ماده می‌تواند خطرناک باشد.")
            self.safety_warnings_count += 1
        if self.temp_c < -20:
            warnings.append(f"❄️ دمای ظرف بسیار پایین است ({self.temp_c:.0f}°C) — احتیاط در افزودن مایع.")
            self.safety_warnings_count += 1
        incompat = [
            ({"cl", "hcl", "naocl"}, {"nh3", "nh4oh", "ammonia"}, "کلر/هیپوکلریت + آمونیاک → گاز سمی"),
            ({"h2o2", "peroxide"}, {"organic", "acetone", "alcohol"}, "پراکسید + ماده آلی → خطر انفجار"),
        ]
        key_l = key.lower()
        for group_a, group_b, msg in incompat:
            if any(g in key_l for g in group_a) and any(
                    any(g in str(ek).lower() for g in group_b) for ek in existing_keys):
                warnings.append(f"☠️ ناسازگاری شیمیایی: {msg}")
                self.safety_warnings_count += 1
            if any(g in key_l for g in group_b) and any(
                    any(g in str(ek).lower() for g in group_a) for ek in existing_keys):
                warnings.append(f"☠️ ناسازگاری شیمیایی: {msg}")
                self.safety_warnings_count += 1
        if self.total_volume + amount > self.max_capacity * 0.9:
            warnings.append("⚠️ حجم ظرف نزدیک به ظرفیت حداکثر است — خطر سرریز.")
            self.safety_warnings_count += 1

        ph_val = safe_float(data.get("pH", 7.0), 7.0)
        molarity = safe_float(data.get("molarity", 0.1), 0.1)
        if custom_molarity is not None:
            molarity = custom_molarity

        formula = str(data.get("formula") or key)
        if any(x in chem_type for x in ["Solid", "Metal", "Salt", "Powder", "Precipitate"]):
            mm = ChemicalCalculator.molar_mass(formula)
            if mm > 1e-9:
                added_moles = float(amount) / mm
            else:
                added_moles = (amount / 100.0) * max(molarity, 0.01)
            unit_display = "g"
        else:
            added_moles = molarity * (amount / 1000.0)
            unit_display = "mL"

        old_vol = self.total_volume
        self.total_volume += amount

        if self.total_volume > 0:
            self.temp_c = ((old_vol * self.temp_c) + (amount * 25.0)) / self.total_volume
            q_joules = added_moles * (-safe_float(data.get("heat", 0.0), 0.0)) * 1000
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
                self.push_undo()
                key = layer['key']
                moles = layer['moles']
                amount = layer['amount']
                if key in self.contents:
                    self.contents[key] -= moles
                    if self.contents[key] <= 0:
                        del self.contents[key]
                self.total_volume -= amount
                self.visual_layers.pop(i)
                try:
                    self.rebuild_acid_base_moles()
                except Exception:
                    pass
                self.add_to_log(f"ماده حذف شد: {layer['name']}")
                return True
        return False

    def change_temperature(self, delta):
        try:
            self.push_undo()
            self.temp_c = safe_float(self.temp_c, 25.0) + safe_float(delta, 0.0)
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

        boil_pts = []
        for l in self.visual_layers:
            d = CHEMILAB_DB.get(l.get('key'), {})
            bp = d.get('bp')
            if bp is not None and any(x in l.get('type', '') for x in ("مایع", "آب", "محلول", "اسید", "باز")):
                try:
                    boil_pts.append(float(bp))
                except (TypeError, ValueError):
                    pass
        boil_t = float(np.mean(boil_pts)) if boil_pts else 100.0
        if self.temp_c >= boil_t and self.total_volume > 0:
            evap_rate = (self.temp_c - boil_t) * 0.5 * dt
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

    def _resolve_content_key(self, reactant_key):
        """پیدا کردن کلید واقعی موجود در contents برای یک واکنش‌دهنده"""
        nk = normalize_key(reactant_key)
        for ck in list(self.contents.keys()):
            if normalize_key(ck) == nk:
                return ck
            if ck in CHEMILAB_DB:
                if normalize_key(CHEMILAB_DB[ck].get("formula", "")) == nk:
                    return ck
                if normalize_key(CHEMILAB_DB[ck].get("name", "")) == nk:
                    return ck
        return None

    def _parse_simple_coeffs(self, rxn):
        """استخراج ضرایب ساده از فیلد coeffs یا پیش‌فرض ۱"""
        coeffs = {}
        raw = rxn.get("coeffs") or rxn.get("stoich") or {}
        if isinstance(raw, dict):
            for k, v in raw.items():
                try:
                    coeffs[normalize_key(k)] = max(1, int(float(v)))
                except (TypeError, ValueError):
                    coeffs[normalize_key(k)] = 1
        for r in rxn.get("reactants", []):
            nk = normalize_key(r)
            if nk not in coeffs:
                coeffs[nk] = 1
        for p in rxn.get("products", []):
            nk = normalize_key(p)
            if nk not in coeffs:
                coeffs[nk] = 1
        return coeffs

    def _apply_reaction_stoich(self, rxn, extent):
        """
        اعمال واقعی واکنش روی محتویات:
        - کاهش واکنش‌دهنده‌ها به اندازه extent * coeff
        - افزودن محصولات
        - به‌روزرسانی visual_layers و حجم تقریبی
        moles_h/oh فقط از طریق rebuild_acid_base_moles همگام می‌شوند.
        """
        if extent <= 1e-12:
            return
        coeffs = self._parse_simple_coeffs(rxn)
        # ── محدود کردن extent به موجودی واقعی (جلوگیری از تولید محصول جعلی) ──
        max_extent = float(extent)
        for r in rxn.get("reactants", []):
            ck = self._resolve_content_key(r)
            coef = max(1e-12, float(coeffs.get(normalize_key(r), 1) or 1))
            avail = safe_float(self.contents.get(ck, 0.0), 0.0) if ck else 0.0
            max_extent = min(max_extent, avail / coef)
        extent = max(0.0, max_extent)
        if extent <= 1e-12:
            return
        for r in rxn.get("reactants", []):
            ck = self._resolve_content_key(r)
            if not ck:
                continue
            coef = float(coeffs.get(normalize_key(r), 1) or 1)
            consume = extent * coef
            if ck in self.contents:
                self.contents[ck] = max(0.0, self.contents[ck] - consume)
                if self.contents[ck] <= 1e-12:
                    del self.contents[ck]
            remaining = consume
            new_layers = []
            for layer in self.visual_layers:
                if remaining > 1e-15 and layer.get('key') == ck:
                    take = min(safe_float(layer.get('moles', 0), 0.0), remaining)
                    if take > 1e-15:
                        old_m = max(safe_float(layer.get('moles', 0), 0.0), 1e-12)
                        ratio = 1.0 - (take / old_m)
                        layer = dict(layer)  # کپی تا ارجاع مشترک خراب نشود
                        layer['moles'] = max(0.0, old_m - take)
                        layer['amount'] = max(0.0, safe_float(layer.get('amount', 0), 0.0) * max(0.0, ratio))
                        remaining -= take
                        if layer['moles'] > 1e-12 and layer['amount'] > 0.05:
                            new_layers.append(layer)
                        continue
                new_layers.append(layer)
            self.visual_layers = new_layers
        for p in rxn.get("products", []):
            pk = normalize_key(p)
            db_key = None
            if pk in CHEMILAB_DB:
                db_key = pk
            else:
                for k, v in CHEMILAB_DB.items():
                    if normalize_key(v.get("formula", "")) == pk or normalize_key(k) == pk:
                        db_key = k
                        break
            if not db_key:
                db_key = pk
            coef = float(coeffs.get(normalize_key(p), 1) or 1)
            add_moles = extent * coef
            self.contents[db_key] = self.contents.get(db_key, 0.0) + add_moles
            data = CHEMILAB_DB.get(db_key, {})
            chem_type = data.get('type', 'Solid')
            form_p = str(data.get("formula") or p)
            mm_p = ChemicalCalculator.molar_mass(form_p)
            dens = safe_float(data.get("density", 1.0), 1.0) or 1.0
            if any(x in str(chem_type) for x in ["Solid", "Metal", "Salt", "Powder", "Precipitate", "جامد"]):
                amt = (add_moles * mm_p) if mm_p > 1e-9 else add_moles * 20.0
            elif "Gas" in str(chem_type) or "گاز" in str(chem_type):
                amt = add_moles * 24.0 * 1000.0 / 40.0  # ~600 mL/mol مقیاس آموزشی
                amt = max(1.0, min(amt, 200.0))
            else:
                mass_g = (add_moles * mm_p) if mm_p > 1e-9 else add_moles * 30.0
                amt = mass_g / dens if dens > 1e-9 else mass_g
            self.layer_id_counter += 1
            self.visual_layers.append({
                'id': self.layer_id_counter,
                'key': db_key,
                'name': data.get('name', p) if data else str(p),
                'amount': amt,
                'color': data.get('color', '#cccccc') if data else '#cccccc',
                'type': get_persian_type(chem_type),
                'moles': add_moles,
                'formula': data.get('formula', p) if data else str(p),
            })
        self.total_volume = sum(safe_float(l.get('amount', 0), 0.0) for l in self.visual_layers)
        if self.total_volume < 0:
            self.total_volume = 0.0
        self.contents = {k: v for k, v in self.contents.items() if v > 1e-12}

    def check_reactions(self):
        """حداکثر یک واکنش در هر فراخوانی اعمال می‌شود (اولویت با کشف جدید)."""
        if self.is_broken:
            return None
        present = set()
        for k, v in self.contents.items():
            if v > 1e-12:
                present.add(normalize_key(k))
                if k in CHEMILAB_DB:
                    present.add(normalize_key(CHEMILAB_DB[k].get("formula", "")))
                    present.add(normalize_key(CHEMILAB_DB[k].get("name", "")))

        candidates_new = []
        candidates_old = []
        for name, rxn in CUSTOM_REACTIONS.items():
            needed = {normalize_key(r) for r in rxn.get("reactants", [])}
            if not needed or not needed.issubset(present):
                continue
            req_temp = safe_float(rxn.get("temp_min", -273), -273.0)
            if self.temp_c + TEMP_TOLERANCE < req_temp:
                continue
            has_precipitate = any(
                "Precipitate" in CHEMILAB_DB.get(normalize_key(p), {}).get('type', '')
                or "Precipitate" in CHEMILAB_DB.get(p, {}).get('type', '')
                for p in rxn.get("products", []))
            has_gas = any(
                "Gas" in CHEMILAB_DB.get(normalize_key(p), {}).get('type', '')
                or "Gas" in CHEMILAB_DB.get(p, {}).get('type', '')
                for p in rxn.get("products", []))
            coeffs = self._parse_simple_coeffs(rxn)
            dH = ChemicalCalculator.estimate_reaction_delta_h(
                rxn.get("reactants", []), rxn.get("products", []), CHEMILAB_DB,
                rxn_dH=rxn.get("dH"))
            lim_key, lim_moles, conv_pct, extent = ChemicalCalculator.find_limiting_reagent(
                rxn.get("reactants", []), self.contents, CHEMILAB_DB, coeffs)
            if lim_key is None:
                lim_key = next(iter(rxn.get("reactants", [])), None)
            # هرگز بیشتر از extent واقعی (محدود به limiting) مصرف نکن
            applied_extent = float(extent) * 0.85 if extent > 1e-12 else 0.0
            if applied_extent > extent:
                applied_extent = float(extent)
            thermo = {
                "dH": dH,
                "is_exothermic": dH < -0.5,
                "is_endothermic": dH > 0.5,
                "limiting": lim_key,
                "limiting_moles": lim_moles,
                "conversion_pct": conv_pct,
                "extent": applied_extent,
                "has_gas": has_gas,
                "has_precipitate": has_precipitate,
                "yield_approx": min(100.0, conv_pct * 0.92),
            }
            is_new = name not in self.discovered
            entry = (name, rxn, thermo, has_precipitate, has_gas, applied_extent, lim_key, conv_pct, is_new)
            if is_new:
                candidates_new.append(entry)
            else:
                candidates_old.append(entry)

        chosen = candidates_new[0] if candidates_new else (candidates_old[0] if candidates_old else None)
        if not chosen:
            return None
        name, rxn, thermo, has_precipitate, has_gas, applied_extent, lim_key, conv_pct, is_new = chosen
        self.last_reaction_thermo = thermo
        self.last_limiting_reagent = lim_key

        cooldown_key = f"_rxn_cd_{normalize_key(name)}"
        last_t = safe_float(getattr(self, cooldown_key, 0), 0.0)
        now_t = time.time()
        can_apply = is_new or (now_t - last_t) > 2.5
        if can_apply and applied_extent > 1e-12:
            self.push_undo()
            # واکنش تکراری: کندتر اجرا شود ولی هرگز از available تجاوز نکند
            if is_new:
                run_extent = applied_extent
            else:
                run_extent = min(applied_extent, applied_extent * 0.35)
                if run_extent > applied_extent:
                    run_extent = applied_extent
            self._apply_reaction_stoich(rxn, run_extent)
            setattr(self, cooldown_key, now_t)
            dH = thermo["dH"]
            if thermo["is_exothermic"]:
                self.temp_c += max(2.0, min(40.0 if is_new else 15.0, abs(dH) * (0.8 if is_new else 0.3)))
            elif thermo["is_endothermic"]:
                self.temp_c -= max(1.0, min(20.0 if is_new else 8.0, abs(dH) * (0.4 if is_new else 0.15)))
            elif is_new:
                self.temp_c += 5.0
            try:
                self.rebuild_acid_base_moles()
            except Exception as e:
                tlog(f"rebuild_acid_base after reaction: {e}", "WARN")

        if is_new:
            self.discovered.add(name)
            self.stats["reactions_found"] += 1
            self.score += safe_int(rxn.get("xp", 0), 0)
            while self.score >= self.level * 100 and self.level < 9999:
                self.level += 1
            self.save_data()
            self.add_to_log(
                f"واکنش جدید کشف شد: {name} | محدودکننده: {lim_key} | "
                f"بازده تقریبی: {thermo['yield_approx']:.0f}% | تبدیل: {conv_pct:.0f}%")
            return (name, rxn.get("xp", 0), "new", has_precipitate, has_gas, thermo)
        return (name, 0, "old", has_precipitate, has_gas, thermo)

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
        if (self.last_reaction_thermo and self.last_reaction_thermo.get("is_exothermic")
                and "m8" not in self.completed_missions):
            new_missions.append("m8")

        achieved = []
        for m_id in new_missions:
            self.completed_missions.add(m_id)
            mission = next((m for m in self.missions if m['id'] == m_id), None)
            if mission:
                self.score += mission['xp']
                while self.score >= self.level * 100 and self.level < 9999:
                    self.level += 1
                self.add_to_log(f"ماموریت تکمیل شد: {mission['title']}")
                achieved.append({"type": "mission", "title": mission['title'], "xp": mission.get("xp", 0)})
        if new_missions:
            self.save_data()

        if self.temp_c >= 200 and "داغی ۲۰۰ درجه" not in self.badges:
            self.badges.add("داغی ۲۰۰ درجه")
            self.save_data()
            self.add_to_log("مدال جدید: داغی ۲۰۰ درجه")
            achieved.append({"type": "badge", "title": "داغی ۲۰۰ درجه"})
        if len(self.discovered) >= 1 and "اولین واکنش" not in self.badges:
            self.badges.add("اولین واکنش")
            self.save_data()
            self.add_to_log("مدال جدید: اولین واکنش")
            achieved.append({"type": "badge", "title": "اولین واکنش"})

        if not achieved:
            return None
        if len(achieved) == 1:
            return achieved[0]
        # چند دستاورد همزمان — لیست برمی‌گردد تا UI همه را نشان دهد
        return {"type": "multi", "items": achieved, "title": "، ".join(a["title"] for a in achieved)}

    def rebuild_acid_base_moles(self):
        """بازمحاسبهٔ مول H+/OH− از محتویات با NumPy — دقت بالاتر."""
        if not self.contents or self.is_broken:
            self.moles_h = 0.0
            self.moles_oh = 0.0
            return
        keys = list(self.contents.keys())
        moles = np.array([float(self.contents[k]) for k in keys], dtype=np.float64)
        h_arr = np.zeros(len(keys), dtype=np.float64)
        oh_arr = np.zeros(len(keys), dtype=np.float64)
        for i, k in enumerate(keys):
            d = CHEMILAB_DB.get(k) or CHEMILAB_DB.get(normalize_key(k), {})
            if not d:
                continue
            ph_val = float(d.get("pH", 7.0) or 7.0)
            typ = str(d.get("type", ""))
            m = moles[i]
            if m <= 1e-15:
                continue
            if "Strong Acid" in typ or ph_val < 2:
                h_arr[i] = m
            elif "Acid" in typ or ph_val < 6:
                h_arr[i] = m * 0.1
            elif "Strong Base" in typ or ph_val > 12:
                oh_arr[i] = m
            elif "Base" in typ or ph_val > 8:
                oh_arr[i] = m * 0.1
        self.moles_h = float(h_arr.sum())
        self.moles_oh = float(oh_arr.sum())

    def get_ph(self):
        if self.total_volume <= 0 or self.is_broken:
            return 7.0
        try:
            self.rebuild_acid_base_moles()
        except Exception:
            pass
        vol_l = max(self.total_volume / 1000.0, 1e-9)
        h = float(self.moles_h) / vol_l
        oh = float(self.moles_oh) / vol_l
        net = h - oh
        if abs(net) < 1e-12:
            return 7.0
        try:
            if net > 0:
                ph = -np.log10(net + 1e-14)
            else:
                ph = 14.0 + np.log10((-net) + 1e-14)
            return float(np.clip(ph, 0.0, 14.0))
        except Exception:
            return 7.0

    def get_mixture_empirical_formula(self):
        if self.is_broken:
            return "-"
        if not self.contents:
            return "-"
        return ChemicalCalculator.mixture_formula(self.contents, CHEMILAB_DB)

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
        self.timer.start(120)  # کمتر از ۶۰ms — کاهش لگ

    def rotate_electrons(self):
        if not self.isVisible():
            return
        self.angle_offset += 0.02
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
        grad_nucleus.setColorAt(0, QColor("#fbbf24"))
        grad_nucleus.setColorAt(1, QColor("#fab387").darker(150))
        painter.setBrush(QBrush(grad_nucleus))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(cx, cy), n_rad, n_rad)

        painter.setPen(QColor("#100a18"))
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

            pen_shell = QPen(QColor("#3d2a55" if active_shells < 5 else "#2a1e3d"))
            pen_shell.setWidth(1)
            pen_shell.setStyle(Qt.DashLine)
            painter.setPen(pen_shell)
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(QPointF(cx, cy), r, r)

            painter.setPen(QColor("#818cf8"))
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

                painter.setBrush(QColor("#c4b5fd"))
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(QPointF(ex, ey), 4, 4)

        painter.setPen(QColor("#bac2de"))
        font_stat = painter.font()
        font_stat.setPointSize(9)
        painter.setFont(font_stat)
        stat_text = " | ".join([f"{shell_names[i]}:{self.shells[i]}" for i in range(7) if self.shells[i] > 0])
        painter.drawText(QRectF(10, h - 25, w, 25), Qt.AlignLeft | Qt.AlignVCenter, stat_text)

if HAS_OPENGL:
    class GLBeakerCanvas(QOpenGLWidget):
        """بشر شیشه‌ای سه‌بعدی با OpenGL + نمایش مایع و همزن"""
        def __init__(self, engine=None, parent=None):
            super().__init__(parent)
            self.engine = engine
            self.setMinimumSize(360, 480)
            self.angle_x = 18.0
            self.angle_y = 25.0
            self.last_pos = None
            self.quadric = None
            self.stirrer_on = False
            self.stirrer_angle = 0.0
            self._stirrer_timer = QTimer(self)
            self._stirrer_timer.timeout.connect(self._tick_stirrer)
            # تایمر فقط وقتی ویجت ۳بعدی دیده می‌شود روشن می‌شود
            self._stirrer_timer.setInterval(80)
            self._needs_redraw = True

        def set_engine(self, engine):
            self.engine = engine

        def _tick_stirrer(self):
            if not self.isVisible():
                return
            if not hasattr(self, 'bubbles_3d'):
                self.bubbles_3d = []
            need = bool(self._needs_redraw) or self.stirrer_on or bool(self.bubbles_3d)
            if self.stirrer_on:
                self.stirrer_angle = (self.stirrer_angle + 16) % 360
                need = True
            eng = self.engine
            has_liquid = bool(
                eng and not getattr(eng, 'is_broken', False)
                and float(getattr(eng, 'total_volume', 0) or 0) > 0.5
            )
            if has_liquid:
                heat = float(getattr(eng, 'temp_c', 25) or 25) > 70 or self.stirrer_on
                rate = 0.55 if heat else 0.22
                if len(self.bubbles_3d) < 35 and random.random() < rate:
                    self.bubbles_3d.append({
                        'x': random.uniform(-0.55, 0.55),
                        'z': random.uniform(-0.55, 0.55),
                        'y': -1.85 + random.uniform(0, 0.25),
                        'vy': random.uniform(0.04, 0.09),
                        'r': random.uniform(0.05, 0.12),
                        'life': random.randint(45, 90),
                    })
                    need = True
            if self.bubbles_3d:
                need = True
                for b in self.bubbles_3d[:]:
                    b['y'] += b['vy']
                    b['x'] += random.uniform(-0.01, 0.01)
                    b['life'] -= 1
                    if b['life'] <= 0 or b['y'] > 1.55:
                        self.bubbles_3d.remove(b)
            if need:
                self._needs_redraw = False
                self.update()

        def initializeGL(self):
            glEnable(GL_DEPTH_TEST)
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            glEnable(GL_LIGHTING)
            glEnable(GL_LIGHT0)
            glEnable(GL_COLOR_MATERIAL)
            glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
            glLightfv(GL_LIGHT0, GL_POSITION, [2.5, 5.0, 5.0, 1.0])
            glLightfv(GL_LIGHT0, GL_AMBIENT, [0.6, 0.6, 0.65, 1.0])
            glLightfv(GL_LIGHT0, GL_DIFFUSE, [1.15, 1.15, 1.2, 1.0])
            glClearColor(0.06, 0.07, 0.10, 1.0)
            try:
                self.quadric = gluNewQuadric()
            except Exception:
                self.quadric = None

        def resizeGL(self, w, h):
            glViewport(0, 0, max(1, w), max(1, h))
            glMatrixMode(GL_PROJECTION)
            glLoadIdentity()
            gluPerspective(36, w / max(h, 1), 0.1, 80.0)
            glMatrixMode(GL_MODELVIEW)

        def _hex_to_rgb(self, hex_color):
            try:
                c = str(hex_color).lstrip('#')
                if len(c) >= 6:
                    return int(c[0:2], 16) / 255.0, int(c[2:4], 16) / 255.0, int(c[4:6], 16) / 255.0
            except Exception:
                pass
            return 0.4, 0.7, 0.9

        def paintGL(self):
            glClearColor(0.06, 0.07, 0.10, 1.0)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glLoadIdentity()
            # دوربین نزدیک‌تر و کمی بالاتر برای دیدن داخل
            glTranslatef(0.0, 0.05, -6.2)
            glRotatef(self.angle_x, 1.0, 0.0, 0.0)
            glRotatef(self.angle_y, 0.0, 1.0, 0.0)

            y_b, y_t = -2.0, 1.6
            r_b, r_t = 1.15, 0.95
            steps = 40

            def ring(y, r, rgba=(0.9, 0.95, 1.0, 0.9)):
                glColor4f(*rgba)
                glBegin(GL_LINE_LOOP)
                for i in range(steps):
                    a = math.radians(i * (360.0 / steps))
                    glVertex3f(math.cos(a) * r, y, math.sin(a) * r)
                glEnd()

            def cylinder_side(y0, y1, r0, r1, rgba):
                glColor4f(*rgba)
                glBegin(GL_QUAD_STRIP)
                for i in range(steps + 1):
                    a = math.radians(i * (360.0 / steps))
                    c, s = math.cos(a), math.sin(a)
                    glVertex3f(c * r0, y0, s * r0)
                    glVertex3f(c * r1, y1, s * r1)
                glEnd()

            def disk(y, r, rgba):
                glColor4f(*rgba)
                glBegin(GL_TRIANGLE_FAN)
                glVertex3f(0, y, 0)
                for i in range(steps + 1):
                    a = math.radians(i * (360.0 / steps))
                    glVertex3f(math.cos(a) * r, y, math.sin(a) * r)
                glEnd()

            glDisable(GL_LIGHTING)
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            glDisable(GL_DEPTH_TEST)

            # پایه
            disk(y_b - 0.15, r_b + 0.25, (0.22, 0.24, 0.30, 1.0))
            disk(y_b - 0.08, r_b + 0.12, (0.35, 0.38, 0.45, 1.0))

            # --- مایع لایه‌لایه (مات و پررنگ مثل ۲بعدی) ---
            eng = self.engine
            layers = []
            total_vol = 0.0
            if eng and not getattr(eng, 'is_broken', False):
                layers = list(getattr(eng, 'visual_layers', []) or [])
                total_vol = float(getattr(eng, 'total_volume', 0) or 0)
                if total_vol <= 0 and layers:
                    total_vol = sum(float(l.get('amount', 0) or 0) for l in layers)

            if total_vol > 0.05:
                max_cap = max(1.0, float(getattr(eng, 'max_capacity', 1000) or 1000))
                fill = min(0.92, max(0.04, total_vol / max_cap))
                liq_top = y_b + (y_t - y_b) * fill

                def dens(L):
                    t = str(L.get('type', ''))
                    if any(x in t for x in ["جامد", "فلز", "رسوب", "Solid", "Salt", "Metal"]):
                        return 10
                    if "گاز" in t or "Gas" in t:
                        return 0.1
                    return 1.0

                if not layers:
                    layers = [{'amount': total_vol, 'color': '#3b9eff', 'type': 'مایع', 'name': '?'}]
                layers = sorted(layers, key=dens, reverse=True)
                sum_a = sum(max(0.01, float(l.get('amount', 0) or 0)) for l in layers) or 1.0
                cur = y_b
                for L in layers:
                    frac = max(0.01, float(L.get('amount', 0) or 0)) / sum_a
                    lh = max(0.05, (liq_top - y_b) * frac)
                    if cur + lh > liq_top:
                        lh = max(0.04, liq_top - cur)
                    r, g, b = self._hex_to_rgb(L.get('color', '#3b9eff'))
                    # روشن‌تر کردن رنگ‌های خیلی تیره
                    if r + g + b < 0.5:
                        r, g, b = min(1, r + 0.25), min(1, g + 0.25), min(1, b + 0.25)
                    t0 = (cur - y_b) / max(0.01, y_t - y_b)
                    t1 = (cur + lh - y_b) / max(0.01, y_t - y_b)
                    rr0 = (r_b + (r_t - r_b) * t0) * 0.92
                    rr1 = (r_b + (r_t - r_b) * t1) * 0.92
                    is_solid = dens(L) >= 10
                    alpha = 1.0 if is_solid else 0.92
                    cylinder_side(cur, cur + lh, rr0, rr1, (r, g, b, alpha))
                    # سطح بالا روشن‌تر
                    disk(cur + lh, rr1, (min(1, r + 0.15), min(1, g + 0.15), min(1, b + 0.15), 0.98))
                    # کف لایه
                    disk(cur + 0.001, rr0, (r * 0.7, g * 0.7, b * 0.7, alpha))
                    cur += lh
                    if cur >= liq_top - 0.01:
                        break

            glEnable(GL_DEPTH_TEST)

            # --- شیشه: لبه روشن مشخص ---
            glLineWidth(3.0)
            ring(y_b, r_b, (0.85, 0.92, 1.0, 0.95))
            ring(y_t, r_t, (0.95, 0.98, 1.0, 1.0))
            # دهانه ضخیم (دو حلقه)
            ring(y_t + 0.02, r_t + 0.04, (1.0, 1.0, 1.0, 0.9))
            ring(y_t + 0.02, r_t - 0.02, (0.8, 0.9, 1.0, 0.7))
            # خطوط عمودی شیشه
            glLineWidth(1.5)
            glColor4f(0.75, 0.88, 1.0, 0.45)
            for i in range(0, steps, 5):
                a = math.radians(i * (360.0 / steps))
                c, s = math.cos(a), math.sin(a)
                glBegin(GL_LINES)
                glVertex3f(c * r_b, y_b, s * r_b)
                glVertex3f(c * r_t, y_t, s * r_t)
                glEnd()
            # دیواره شیشه‌ای کم‌رنگ (فقط حس حجم)
            cylinder_side(y_b, y_t, r_b, r_t, (0.7, 0.85, 1.0, 0.10))

            # --- همزن مغناطیسی بیضی/میله ---
            glDisable(GL_DEPTH_TEST)
            glPushMatrix()
            glTranslatef(0, y_b + 0.12, 0)
            ang = self.stirrer_angle if self.stirrer_on else 20.0
            glRotatef(ang, 0, 1, 0)
            if self.stirrer_on:
                # هاله
                glColor4f(1.0, 0.85, 0.2, 0.25)
                disk(0.0, 0.55, (1.0, 0.85, 0.2, 0.2))
                glColor4f(1.0, 0.82, 0.15, 1.0)
            else:
                glColor4f(0.55, 0.58, 0.65, 1.0)
            # میله بیضی‌مانند (چند بخش)
            glBegin(GL_QUADS)
            hw, hh, hd = 0.48, 0.07, 0.10
            # بالا
            glVertex3f(-hw, hh, -hd); glVertex3f(hw, hh, -hd); glVertex3f(hw, hh, hd); glVertex3f(-hw, hh, hd)
            # پایین
            glVertex3f(-hw, 0, -hd); glVertex3f(hw, 0, -hd); glVertex3f(hw, 0, hd); glVertex3f(-hw, 0, hd)
            # جلو
            glVertex3f(-hw, 0, hd); glVertex3f(hw, 0, hd); glVertex3f(hw, hh, hd); glVertex3f(-hw, hh, hd)
            # عقب
            glVertex3f(-hw, 0, -hd); glVertex3f(hw, 0, -hd); glVertex3f(hw, hh, -hd); glVertex3f(-hw, hh, -hd)
            # چپ
            glVertex3f(-hw, 0, -hd); glVertex3f(-hw, 0, hd); glVertex3f(-hw, hh, hd); glVertex3f(-hw, hh, -hd)
            # راست
            glVertex3f(hw, 0, -hd); glVertex3f(hw, 0, hd); glVertex3f(hw, hh, hd); glVertex3f(hw, hh, -hd)
            glEnd()
            glPopMatrix()
            glEnable(GL_DEPTH_TEST)

            # حباب‌ها — روشن و بدون depth-test
            if hasattr(self, 'bubbles_3d') and self.bubbles_3d:
                glDisable(GL_LIGHTING)
                glDisable(GL_DEPTH_TEST)
                glEnable(GL_BLEND)
                glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
                for b in self.bubbles_3d:
                    life_f = max(0.15, min(1.0, b['life'] / 70.0))
                    glColor4f(1.0, 1.0, 1.0, 0.55 * life_f)
                    glPushMatrix()
                    glTranslatef(b['x'], b['y'], b['z'])
                    if self.quadric:
                        try:
                            gluSphere(self.quadric, b['r'], 12, 12)
                        except Exception:
                            disk(0, b['r'], (1.0, 1.0, 1.0, 0.5 * life_f))
                    else:
                        disk(0, b['r'], (1.0, 1.0, 1.0, 0.55 * life_f))
                    glColor4f(0.7, 0.9, 1.0, 0.35 * life_f)
                    if self.quadric:
                        try:
                            gluSphere(self.quadric, b['r'] * 1.15, 10, 10)
                        except Exception:
                            pass
                    glPopMatrix()
                glEnable(GL_DEPTH_TEST)
                glEnable(GL_LIGHTING)

        def mousePressEvent(self, event):
            self.last_pos = event.position() if hasattr(event, "position") else event.pos()

        def mouseMoveEvent(self, event):
            if self.last_pos is not None:
                pos = event.position() if hasattr(event, "position") else event.pos()
                dx = pos.x() - self.last_pos.x()
                dy = pos.y() - self.last_pos.y()
                self.angle_y += dx * 0.4
                self.angle_x = max(-5, min(40, self.angle_x + dy * 0.3))
                self.last_pos = pos
                self.update()


# --- 3D OpenGL Bohr Model ---

        def redraw(self):
            self._needs_redraw = True
            self.update()

        def set_stirrer(self, state):
            self.stirrer_on = bool(state)
            if self.stirrer_on:
                if hasattr(self, "_stirrer_timer") and not self._stirrer_timer.isActive():
                    self._stirrer_timer.start(80)
            else:
                self.stirrer_angle = 0.0
                if hasattr(self, "_stirrer_timer") and self._stirrer_timer.isActive():
                    self._stirrer_timer.stop()
            self._needs_redraw = True
            self.update()

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
            self.last_pos = event.position() if hasattr(event, "position") else event.pos()

        def mouseMoveEvent(self, event):
            if self.last_pos is not None:
                pos = event.position() if hasattr(event, "position") else event.pos()
                dx = pos.x() - self.last_pos.x()
                dy = pos.y() - self.last_pos.y()
                self.angle_x += dy * 0.5
                self.angle_y += dx * 0.5
                self.last_pos = pos
                self.update()


if True:
    class ReliableBeaker3DWidget(QWidget):
        """Fallback سه‌بعدی بدون PyOpenGL؛ با matplotlib و قابل چرخش با ماوس."""
        def __init__(self, engine=None, parent=None):
            super().__init__(parent)
            self.engine = engine
            self.stirrer_on = False
            self._needs_redraw = True
            self._last = None
            self.figure = Figure(figsize=(5, 5), facecolor="#0d1520")
            self.canvas = FigureCanvas(self.figure)
            self.ax = self.figure.add_subplot(111, projection="3d")
            lay = QVBoxLayout(self); lay.setContentsMargins(0,0,0,0); lay.addWidget(self.canvas)
            self.canvas.mpl_connect("button_press_event", self._press)
            self.canvas.mpl_connect("button_release_event", self._release)
            self.canvas.mpl_connect("motion_notify_event", self._move)
            self._draw()
            self._stirrer_timer = QTimer(self); self._stirrer_timer.timeout.connect(self.update); self._stirrer_timer.setInterval(80)
        def set_stirrer(self, state):
            self.stirrer_on = bool(state)
            if hasattr(self, "_stirrer_timer"):
                if self.stirrer_on and not self._stirrer_timer.isActive():
                    self._stirrer_timer.start(80)
                elif (not self.stirrer_on) and self._stirrer_timer.isActive():
                    self._stirrer_timer.stop()
            if hasattr(self, "_draw"):
                self._draw()
            else:
                self.update()

        def redraw(self):
            self._needs_redraw = True
            if hasattr(self, "_draw"):
                self._draw()
            else:
                self.update()

        def set_engine(self, engine): self.engine = engine; self._draw()
        def _press(self,e): self._last=(e.x,e.y)
        def _release(self,e): self._last=None
        def _move(self,e):
            if self._last is None or e.x is None or e.y is None: return
            dx=e.x-self._last[0]; dy=e.y-self._last[1]
            self.ax.view_init(elev=self.ax.elev-dy*0.35, azim=self.ax.azim+dx*0.35); self._last=(e.x,e.y); self.canvas.draw_idle()
        def _draw(self):
            ax=self.ax; ax.clear(); ax.set_facecolor("#0d1520")
            import numpy as _np
            t=_np.linspace(0,2*_np.pi,64); z=_np.linspace(0,3.2,20); T,Z=_np.meshgrid(t,z)
            R=1.45; X=R*_np.cos(T); Y=R*_np.sin(T)
            ax.plot_surface(X,Y,Z,alpha=0.10,linewidth=0,shade=True)
            fill=0.0
            try: fill=max(0.0,min(1.0,float(getattr(self.engine,'total_volume',0) or 0)/1000.0))
            except Exception: pass
            if fill>0:
                zz=_np.full_like(T,0.25+2.5*fill)
                ax.plot_surface(0.92*R*_np.cos(T),0.92*R*_np.sin(T),zz,alpha=0.42,linewidth=0)
            ax.set_xlim(-2,2); ax.set_ylim(-2,2); ax.set_zlim(0,3.6); ax.set_box_aspect((1,1,1.4)); ax.set_axis_off(); ax.set_proj_type("ortho"); self.canvas.draw_idle()
        def update(self): self._draw()

    class ReliableBohr3DWidget(QWidget):
        """Fallback سه‌بعدی مدل بور بدون PyOpenGL."""
        def __init__(self,parent=None):
            super().__init__(parent); self.Z=0; self.shells=[0]*7; self._last=None
            self.figure=Figure(figsize=(5,5),facecolor="#0d1520"); self.canvas=FigureCanvas(self.figure); self.ax=self.figure.add_subplot(111,projection="3d")
            lay=QVBoxLayout(self); lay.setContentsMargins(0,0,0,0); lay.addWidget(self.canvas)
            self.canvas.mpl_connect("button_press_event",lambda e:setattr(self,"_last",(e.x,e.y))); self.canvas.mpl_connect("button_release_event",lambda e:setattr(self,"_last",None)); self.canvas.mpl_connect("motion_notify_event",self._move); self._draw()
        def _move(self,e):
            if self._last is None or e.x is None or e.y is None:return
            dx=e.x-self._last[0]; dy=e.y-self._last[1]; self.ax.view_init(elev=self.ax.elev-dy*.3,azim=self.ax.azim+dx*.3); self._last=(e.x,e.y); self.canvas.draw_idle()
        def update_atom(self,z,symbol=None):
            self.Z=int(z); self.shells=[0]*7; rem=self.Z; caps=[2,8,18,32,32,18,8]
            for i,c in enumerate(caps): self.shells[i]=min(rem,c); rem=max(0,rem-c)
            self._draw()
        def _draw(self):
            import numpy as _np
            ax=self.ax; ax.clear(); ax.set_facecolor("#0d1520"); u=_np.linspace(0,2*_np.pi,100)
            ax.scatter([0],[0],[0],s=260,depthshade=True)
            for i,n in enumerate(self.shells):
                r=0.75*(i+1)
                ax.plot(r*_np.cos(u),r*_np.sin(u),0*u,alpha=.5,linewidth=1)
                if n:
                    ang=_np.linspace(0,2*_np.pi,n,endpoint=False); ax.scatter(r*_np.cos(ang),r*_np.sin(ang),0*ang,s=18)
            lim=max(2.2,0.8*sum(1 for n in self.shells if n)+1); ax.set_xlim(-lim,lim); ax.set_ylim(-lim,lim); ax.set_zlim(-lim*.35,lim*.35); ax.set_box_aspect((1,1,.35)); ax.set_axis_off(); ax.set_proj_type("ortho"); self.canvas.draw_idle()


# ============================================================
# ساختار مولکولی و نمایش ۳بعدی matplotlib (از نسخه ۵۴ — بخش‌های خوب)
# ============================================================
class MolecularStructureDB:
    """
    داده‌های ساختار مولکولی قابل‌توسعه.
    مختصات تقریبی آموزشی (Å) — برای visualization علمی/آموزشی.
    فرمت: formula -> {atoms: [(el, x, y, z), ...], bonds: [(i, j, order), ...]}
    """
    _DATA = {
        "H2O": {
            "name": "آب",
            "atoms": [("O", 0.0, 0.0, 0.0), ("H", 0.96, 0.0, 0.0), ("H", -0.24, 0.93, 0.0)],
            "bonds": [(0, 1, 1), (0, 2, 1)],
            "note": "زاویه پیوند ~104.5° (نمایش آموزشی)",
        },
        "CO2": {
            "name": "کربن دی‌اکسید",
            "atoms": [("C", 0.0, 0.0, 0.0), ("O", 1.16, 0.0, 0.0), ("O", -1.16, 0.0, 0.0)],
            "bonds": [(0, 1, 2), (0, 2, 2)],
            "note": "مولکول خطی",
        },
        "HCl": {
            "name": "هیدروکلریک اسید",
            "atoms": [("Cl", 0.0, 0.0, 0.0), ("H", 1.27, 0.0, 0.0)],
            "bonds": [(0, 1, 1)],
            "note": "",
        },
        "NH3": {
            "name": "آمونیاک",
            "atoms": [
                ("N", 0.0, 0.0, 0.0),
                ("H", 0.94, 0.0, -0.38),
                ("H", -0.47, 0.81, -0.38),
                ("H", -0.47, -0.81, -0.38),
            ],
            "bonds": [(0, 1, 1), (0, 2, 1), (0, 3, 1)],
            "note": "هرمی",
        },
        "CH4": {
            "name": "متان",
            "atoms": [
                ("C", 0.0, 0.0, 0.0),
                ("H", 0.63, 0.63, 0.63),
                ("H", -0.63, -0.63, 0.63),
                ("H", -0.63, 0.63, -0.63),
                ("H", 0.63, -0.63, -0.63),
            ],
            "bonds": [(0, 1, 1), (0, 2, 1), (0, 3, 1), (0, 4, 1)],
            "note": "چهاروجهی",
        },
        "O2": {
            "name": "اکسیژن",
            "atoms": [("O", -0.60, 0.0, 0.0), ("O", 0.60, 0.0, 0.0)],
            "bonds": [(0, 1, 2)],
            "note": "",
        },
        "H2": {
            "name": "هیدروژن",
            "atoms": [("H", -0.37, 0.0, 0.0), ("H", 0.37, 0.0, 0.0)],
            "bonds": [(0, 1, 1)],
            "note": "",
        },
        "N2": {
            "name": "نیتروژن",
            "atoms": [("N", -0.55, 0.0, 0.0), ("N", 0.55, 0.0, 0.0)],
            "bonds": [(0, 1, 3)],
            "note": "پیوند سه‌گانه",
        },
        "Cl2": {
            "name": "کلر",
            "atoms": [("Cl", -0.99, 0.0, 0.0), ("Cl", 0.99, 0.0, 0.0)],
            "bonds": [(0, 1, 1)],
            "note": "",
        },
        "NaCl": {
            "name": "سدیم کلرید (یون)",
            "atoms": [("Na", -1.4, 0.0, 0.0), ("Cl", 1.4, 0.0, 0.0)],
            "bonds": [(0, 1, 1)],
            "note": "نمایش یونی آموزشی — نه کریستال واقعی",
        },
        "CO": {
            "name": "کربن مونوکسید",
            "atoms": [("C", -0.56, 0.0, 0.0), ("O", 0.56, 0.0, 0.0)],
            "bonds": [(0, 1, 3)],
            "note": "",
        },
        "SO2": {
            "name": "گوگرد دی‌اکسید",
            "atoms": [("S", 0.0, 0.0, 0.0), ("O", 1.43, 0.0, 0.0), ("O", -0.36, 1.28, 0.0)],
            "bonds": [(0, 1, 2), (0, 2, 2)],
            "note": "زاویه‌دار",
        },
        "H2S": {
            "name": "هیدروژن سولفید",
            "atoms": [("S", 0.0, 0.0, 0.0), ("H", 1.34, 0.0, 0.0), ("H", -0.34, 1.05, 0.0)],
            "bonds": [(0, 1, 1), (0, 2, 1)],
            "note": "",
        },
        "HF": {
            "name": "هیدروژن فلوئورید",
            "atoms": [("F", 0.0, 0.0, 0.0), ("H", 0.92, 0.0, 0.0)],
            "bonds": [(0, 1, 1)],
            "note": "",
        },
        "C2H4": {
            "name": "اتیلن",
            "atoms": [
                ("C", -0.67, 0.0, 0.0), ("C", 0.67, 0.0, 0.0),
                ("H", -1.24, 0.93, 0.0), ("H", -1.24, -0.93, 0.0),
                ("H", 1.24, 0.93, 0.0), ("H", 1.24, -0.93, 0.0),
            ],
            "bonds": [(0, 1, 2), (0, 2, 1), (0, 3, 1), (1, 4, 1), (1, 5, 1)],
            "note": "پیوند دوگانه",
        },
        "C2H2": {
            "name": "استیلن",
            "atoms": [
                ("C", -0.60, 0.0, 0.0), ("C", 0.60, 0.0, 0.0),
                ("H", -1.66, 0.0, 0.0), ("H", 1.66, 0.0, 0.0),
            ],
            "bonds": [(0, 1, 3), (0, 2, 1), (1, 3, 1)],
            "note": "خطی، پیوند سه‌گانه",
        },
        "OH": {
            "name": "یون هیدروکسید",
            "atoms": [("O", 0.0, 0.0, 0.0), ("H", 0.96, 0.0, 0.0)],
            "bonds": [(0, 1, 1)],
            "note": "",
        },
        "H3O": {
            "name": "یون هیدرونیوم",
            "atoms": [
                ("O", 0.0, 0.0, 0.0),
                ("H", 0.96, 0.0, 0.0),
                ("H", -0.48, 0.83, 0.0),
                ("H", -0.48, -0.42, 0.73),
            ],
            "bonds": [(0, 1, 1), (0, 2, 1), (0, 3, 1)],
            "note": "",
        },

        "NaOH": {
            "name": "سدیم هیدروکسید",
            "atoms": [("Na", -1.5, 0.0, 0.0), ("O", 0.3, 0.0, 0.0), ("H", 1.26, 0.0, 0.0)],
            "bonds": [(0, 1, 1), (1, 2, 1)],
            "note": "یونی/مولکولی آموزشی",
        },
        "H2SO4": {
            "name": "سولفوریک اسید",
            "atoms": [
                ("S", 0.0, 0.0, 0.0),
                ("O", 1.45, 0.0, 0.0), ("O", -1.45, 0.0, 0.0),
                ("O", 0.0, 1.45, 0.0), ("O", 0.0, -1.45, 0.0),
                ("H", 0.0, 2.35, 0.0), ("H", 0.0, -2.35, 0.0),
            ],
            "bonds": [(0, 1, 2), (0, 2, 2), (0, 3, 1), (0, 4, 1), (3, 5, 1), (4, 6, 1)],
            "note": "تقریبی آموزشی",
        },
        "HNO3": {
            "name": "نیتریک اسید",
            "atoms": [
                ("N", 0.0, 0.0, 0.0),
                ("O", 1.2, 0.0, 0.0), ("O", -0.6, 1.0, 0.0), ("O", -0.6, -1.0, 0.0),
                ("H", -1.4, -1.3, 0.0),
            ],
            "bonds": [(0, 1, 2), (0, 2, 2), (0, 3, 1), (3, 4, 1)],
            "note": "",
        },
        "CaCO3": {
            "name": "کلسیم کربنات",
            "atoms": [
                ("Ca", -2.0, 0.0, 0.0),
                ("C", 0.5, 0.0, 0.0),
                ("O", 1.7, 0.0, 0.0), ("O", 0.0, 1.1, 0.0), ("O", 0.0, -1.1, 0.0),
            ],
            "bonds": [(0, 1, 1), (1, 2, 2), (1, 3, 1), (1, 4, 1)],
            "note": "یونی آموزشی",
        },
        "CuSO4": {
            "name": "مس سولفات",
            "atoms": [
                ("Cu", -2.0, 0.0, 0.0),
                ("S", 0.5, 0.0, 0.0),
                ("O", 1.9, 0.0, 0.0), ("O", -0.3, 1.4, 0.0),
                ("O", -0.3, -1.4, 0.0), ("O", 0.5, 0.0, 1.5),
            ],
            "bonds": [(0, 1, 1), (1, 2, 2), (1, 3, 2), (1, 4, 1), (1, 5, 1)],
            "note": "",
        },
        "AgNO3": {
            "name": "نقره نیترات",
            "atoms": [
                ("Ag", -2.0, 0.0, 0.0),
                ("N", 0.5, 0.0, 0.0),
                ("O", 1.7, 0.0, 0.0), ("O", -0.1, 1.1, 0.0), ("O", -0.1, -1.1, 0.0),
            ],
            "bonds": [(0, 1, 1), (1, 2, 2), (1, 3, 2), (1, 4, 1)],
            "note": "",
        },
        "KOH": {
            "name": "پتاسیم هیدروکسید",
            "atoms": [("K", -1.8, 0.0, 0.0), ("O", 0.4, 0.0, 0.0), ("H", 1.36, 0.0, 0.0)],
            "bonds": [(0, 1, 1), (1, 2, 1)],
            "note": "",
        },
        "C2H5OH": {
            "name": "اتانول",
            "atoms": [
                ("C", -1.2, 0.0, 0.0), ("C", 0.3, 0.0, 0.0),
                ("O", 1.1, 1.1, 0.0), ("H", 1.9, 0.9, 0.0),
                ("H", -1.6, 1.0, 0.0), ("H", -1.6, -0.5, 0.9), ("H", -1.6, -0.5, -0.9),
                ("H", 0.7, -0.5, 0.9), ("H", 0.7, -0.5, -0.9),
            ],
            "bonds": [(0, 1, 1), (1, 2, 1), (2, 3, 1), (0, 4, 1), (0, 5, 1), (0, 6, 1), (1, 7, 1), (1, 8, 1)],
            "note": "",
        },
        "CH3COOH": {
            "name": "استیک اسید",
            "atoms": [
                ("C", -1.0, 0.0, 0.0), ("C", 0.5, 0.0, 0.0),
                ("O", 1.2, 1.1, 0.0), ("O", 1.1, -1.1, 0.0), ("H", 2.0, -1.0, 0.0),
                ("H", -1.4, 1.0, 0.0), ("H", -1.4, -0.5, 0.9), ("H", -1.4, -0.5, -0.9),
            ],
            "bonds": [(0, 1, 1), (1, 2, 2), (1, 3, 1), (3, 4, 1), (0, 5, 1), (0, 6, 1), (0, 7, 1)],
            "note": "",
        },
    }

    @classmethod
    def get(cls, formula):
        if not formula:
            return None
        key = normalize_chem_formula(str(formula)).upper().replace(" ", "")
        key = re.sub(r"[^A-Z0-9]", "", key)
        # مدل m1/RDKit اولویت دارد؛ اگر کد مولکولی در DB موجود باشد،
        # مختصات سه‌بعدی با ETKDG + MMFF/UFF تولید می‌شود.
        try:
            smiles = resolve_molecular_smiles(key)
            rd = generate_rdkit_structure(smiles)
            if rd:
                rd["name"] = key
                return rd
        except Exception:
            pass
        if key in cls._DATA:
            return cls._DATA[key]
        for k, v in cls._DATA.items():
            if k.upper() == key:
                return v
        return cls.synthetic(key)

    @classmethod
    def synthetic(cls, formula_key):
        """مدل سه‌بعدی آموزشی خودکار برای هر فرمول.

        این مدل جایگزین ساختارهای تصادفی/مارپیچی شده است: ابتدا عناصر فرمول
        درست خوانده می‌شوند، اتم‌های سنگین به صورت زنجیره‌ای و هیدروژن‌ها
        پیرامون نزدیک‌ترین اتم سنگین قرار می‌گیرند. برای نمایش آموزشی مناسب
        است و عمداً ادعای تعیین ساختار واقعی ایزومرها را ندارد.
        """
        if not formula_key:
            return None
        key = normalize_chem_formula(str(formula_key))
        key = re.sub(r"[^A-Za-z0-9]", "", key)
        parts = re.findall(r"([A-Z][a-z]?)(\d*)", key)
        if not parts:
            return None

        expanded = []
        for el, n in parts:
            count = min(max(int(n) if n else 1, 1), 80)
            expanded.extend([el] * count)
        if not expanded:
            return None

        heavy = [e for e in expanded if e != "H"]
        hydrogens = [e for e in expanded if e == "H"]
        atoms, bonds = [], []

        # اتم‌های سنگین روی مسیر خمیده سه‌بعدی؛ پیوندهای بعدی خوانا و غیرتصادفی
        if heavy:
            for i, el in enumerate(heavy):
                if i == 0:
                    pos = (0.0, 0.0, 0.0)
                else:
                    a = (i - 1) * 2.15
                    pos = (1.45 * i, 0.45 * math.sin(a), 0.35 * math.cos(a))
                atoms.append((el, *pos))
                if i:
                    bonds.append((i - 1, i, 1))
        else:
            atoms.append(("H", 0.0, 0.0, 0.0))

        # هیدروژن‌ها دور اتم‌های سنگین توزیع می‌شوند تا یک «توپ خطی» ایجاد نشود.
        centers = list(range(len(heavy))) or [0]
        golden = math.pi * (3.0 - math.sqrt(5.0))
        for hi, el in enumerate(hydrogens):
            ci = centers[hi % len(centers)]
            _, cx, cy, cz = atoms[ci]
            a = hi * golden
            z = 1.0 - 2.0 * ((hi % 7) + 0.5) / 7.0
            rxy = math.sqrt(max(0.15, 1.0 - z * z))
            dist = 1.0
            atoms.append((el, cx + dist*rxy*math.cos(a), cy + dist*rxy*math.sin(a), cz + dist*z))
            bonds.append((ci, len(atoms) - 1, 1))

        return {
            "name": formula_key,
            "atoms": atoms,
            "bonds": bonds,
            "note": "ساختار خودکار آموزشی؛ برای ترکیبات ناشناخته نمایش تقریبی است.",
        }

    @classmethod
    def formulas(cls):
        return sorted(cls._DATA.keys())


    @classmethod
    def load_from_sqlite(cls, db_path=None):
        """بارگذاری ساختارهای ۳بعدی از جدول molecule_structures (اختیاری/آفلاین)."""
        try:
            path = db_path or get_db_path()
            if not path or not os.path.exists(path):
                return 0
            conn = sqlite3.connect(path)
            cur = conn.cursor()
            cur.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='molecule_structures'"
            )
            if not cur.fetchone():
                conn.close()
                return 0  # جدول اختیاری است — بدون هشدار نویزی
            cur.execute(
                "SELECT formula, name, atoms_json, bonds_json, note FROM molecule_structures"
            )
            n = 0
            for formula, name, atoms_json, bonds_json, note in cur.fetchall():
                try:
                    atoms = json.loads(atoms_json)
                    bonds = json.loads(bonds_json)
                    atoms = [tuple(a) for a in atoms]
                    bonds = [tuple(b) for b in bonds]
                    key = str(formula).upper().replace(" ", "")
                    cls._DATA[key] = {
                        "name": name or key,
                        "atoms": atoms,
                        "bonds": bonds,
                        "note": note or "",
                    }
                    n += 1
                except Exception as e:
                    print(f"[WARN] molecule_structures row skip: {e}", flush=True)
                    continue
            conn.close()
            if n:
                print(f"[DB] {n} ساختار مولکولی از SQLite بارگذاری شد", flush=True)
            return n
        except Exception as e:
            print(f"[WARN] molecule_structures load: {e}", flush=True)
            return 0


    @classmethod
    def from_engine_contents(cls, contents, db):
        """اولین مولکول شناخته‌شده از محتویات ظرف."""
        if not contents:
            return None, None
        for key, moles in contents.items():
            try:
                if float(moles) <= 1e-12:
                    continue
            except (TypeError, ValueError):
                continue
            form = ""
            if db and key in db:
                form = str(db[key].get("formula") or "")
            if not form:
                form = str(key)
            struct = cls.get(form)
            if struct:
                return form, struct
        return None, None

class MplMolecule3DWidget(QWidget):
    """
    نمایش سه‌بعدی مولکول با Matplotlib (آفلاین) — Ball & Stick آموزشی.
    بدون نیاز به اینترنت یا سرور؛ چرخش با ماوس روی canvas.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._structure = None
        lay = QVBoxLayout(self)
        lay.setContentsMargins(4, 4, 4, 4)
        self.lbl = QLabel("مولکول را انتخاب کنید")
        self.lbl.setAlignment(Qt.AlignCenter)
        self.lbl.setStyleSheet("color:#a89bb8; border:none; background:transparent;")
        lay.addWidget(self.lbl)
        self.figure = Figure(figsize=(5, 4), facecolor="#100a18")
        self.canvas = FigureCanvas(self.figure)
        lay.addWidget(self.canvas, 1)
        try:
            from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
            self.ax = self.figure.add_subplot(111, projection="3d")
        except Exception:
            self.ax = self.figure.add_subplot(111)
            self.ax.text(0.5, 0.5, "mplot3d در دسترس نیست", ha="center", color="white")
        self._style_ax()
        self._cid = self.canvas.mpl_connect("motion_notify_event", self._on_move)
        self._press = self.canvas.mpl_connect("button_press_event", self._on_press)
        self._release = self.canvas.mpl_connect("button_release_event", self._on_release)
        self._rotating = False
        self._last = None

    def _style_ax(self):
        try:
            self.ax.set_facecolor("#100a18")
            self.figure.patch.set_facecolor("#100a18")
            self.ax.xaxis.pane.fill = False
            self.ax.yaxis.pane.fill = False
            self.ax.zaxis.pane.fill = False
            self.ax.tick_params(colors="#6b5b80", labelsize=7)
            for a in (self.ax.xaxis, self.ax.yaxis, self.ax.zaxis):
                try:
                    a.pane.set_edgecolor("#2a1e3d")
                except Exception:
                    pass
            self.ax.set_xticks([])
            self.ax.set_yticks([])
            self.ax.set_zticks([])
            self.ax.grid(False)
            try: self.ax.set_proj_type("ortho")
            except Exception: pass
        except Exception:
            pass

    def _on_press(self, event):
        if event.inaxes == self.ax:
            self._rotating = True
            self._last = (event.x, event.y)

    def _on_release(self, event):
        self._rotating = False
        self._last = None

    def _on_move(self, event):
        if not self._rotating or self._last is None or event.inaxes != self.ax:
            return
        dx = event.x - self._last[0]
        dy = event.y - self._last[1]
        self._last = (event.x, event.y)
        try:
            elev = self.ax.elev + dy * 0.3
            azim = self.ax.azim + dx * 0.3
            self.ax.view_init(elev=elev, azim=azim)
            self.canvas.draw_idle()
        except Exception:
            pass

    def show_structure(self, structure, title=None):
        """مدل میله و گلوله (Ball & Stick) سه‌بعدی — Matplotlib آفلاین."""
        self._structure = structure
        self.ax.clear()
        self._style_ax()
        if not structure:
            self.lbl.setText("ساختار در دسترس نیست")
            self.canvas.draw_idle()
            return
        def _norm_atom(a):
            if isinstance(a, dict):
                el = a.get("el") or a.get("element") or a.get("symbol") or "C"
                return (str(el), float(a.get("x", 0) or 0), float(a.get("y", 0) or 0), float(a.get("z", 0) or 0))
            if isinstance(a, (list, tuple)) and len(a) >= 4:
                return (str(a[0]), float(a[1]), float(a[2]), float(a[3]))
            return ("C", 0.0, 0.0, 0.0)
        atoms = [_norm_atom(a) for a in (structure.get("atoms") or [])]
        bonds = structure.get("bonds") or []
        name = title or structure.get("name") or ""
        note = structure.get("note") or ""
        self.lbl.setText(f"🔵 میله و گلوله: {name}" + (f"  —  {note}" if note else ""))
        if not atoms:
            self.lbl.setText("اتمی برای نمایش نیست")
            self.canvas.draw_idle()
            return
        for bond in bonds:
            try:
                if isinstance(bond, dict):
                    bi, bj, order = bond.get("i", 0), bond.get("j", 1), bond.get("order", 1)
                else:
                    bi, bj = bond[0], bond[1]
                    order = bond[2] if len(bond) > 2 else 1
            except Exception:
                continue
            if bi >= len(atoms) or bj >= len(atoms):
                continue
            a, b = atoms[bi], atoms[bj]
            xs, ys, zs = [a[1], b[1]], [a[2], b[2]], [a[3], b[3]]
            # پیوند چندگانه: چند خط موازی تقریبی
            n_lines = max(1, min(3, int(order or 1)))
            for k in range(n_lines):
                off = (k - (n_lines - 1) / 2) * 0.06
                self.ax.plot(
                    [xs[0], xs[1]], [ys[0] + off, ys[1] + off], [zs[0], zs[1]],
                    color="#e9d5ff", linewidth=3.2 if n_lines == 1 else 2.2,
                    solid_capstyle="round", zorder=1,
                )
        # گلوله‌ها (atoms)
        size_map = ATOM_SIZES_3D
        for el, x, y, z in atoms:
            col = ELEMENT_COLORS_3D.get(el, "#b0b0b0")
            s = size_map.get(el, size_map["default"])
            self.ax.scatter(
                [x], [y], [z], s=s, c=[col], depthshade=True,
                edgecolors="#0a0612", linewidths=1.2, alpha=0.95, zorder=5,
            )
            self.ax.text(x, y, z + 0.28, el, color="#f8fafc", fontsize=9,
                         ha="center", va="bottom", fontweight="bold")
        try:
            pts = [(a[1], a[2], a[3]) for a in atoms]
            if pts:
                xs, ys, zs = zip(*pts)
                span = max(max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs), 1.0) * 0.7
                mid = (sum(xs) / len(xs), sum(ys) / len(ys), sum(zs) / len(zs))
                self.ax.set_xlim(mid[0] - span, mid[0] + span)
                self.ax.set_ylim(mid[1] - span, mid[1] + span)
                self.ax.set_zlim(mid[2] - span, mid[2] + span)
        except Exception:
            pass
        try:
            self.ax.view_init(elev=18, azim=35)
        except Exception:
            pass
        self.canvas.draw_idle()


    def show_formula(self, formula, title=None):
        st = MolecularStructureDB.get(formula)
        self.show_structure(st, title=title or formula)

class MplMolecule3DDialog(QDialog):
    """پنجرهٔ مستقل نمایش ۳بعدی matplotlib."""
    def __init__(self, structure=None, formula=None, title="", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title or "نمایش سه‌بعدی مولکول")
        self.resize(560, 480)
        self.setStyleSheet("background:#0a0612; color:#e8e0f5;")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 14, 14, 14)
        head = QFrame()
        head.setStyleSheet("QFrame { background:#151022; border:1px solid #3d2a55; border-radius:12px; }")
        hl = QHBoxLayout(head)
        hl.setContentsMargins(12, 8, 12, 8)
        title_lbl = QLabel(title or "نمایش سه‌بعدی مولکول")
        title_lbl.setStyleSheet("color:#f5d0fe; font-size:14px; font-weight:800;")
        hl.addWidget(title_lbl, 1)
        badge = QLabel("BALL & STICK  •  RDKit")
        badge.setStyleSheet("color:#a78bfa; font-size:10px; font-weight:bold;")
        hl.addWidget(badge)
        lay.addWidget(head)
        self.view = MplMolecule3DWidget(self)
        lay.addWidget(self.view, 1)
        tip = QLabel("مدل میله و گلوله · درگ ماوس برای چرخش · چرخ‌ماوس برای زوم · کاملاً آفلاین")
        tip.setStyleSheet("color:#9f8fb3; font-size:11px; border:none; padding:3px;")
        tip.setAlignment(Qt.AlignCenter)
        lay.addWidget(tip)
        btn = QPushButton("بستن")
        btn.setObjectName("secondaryButton")
        btn.clicked.connect(self.accept)
        lay.addWidget(btn)
        if structure:
            self.view.show_structure(structure, title=title)
        elif formula:
            self.view.show_formula(formula, title=title)

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
        self.canvas_3d = None
        if HAS_OPENGL:
            try:
                self.canvas_3d = GLBohrCanvas()
                self.canvas = self.canvas_3d
                self.lbl_bohr_mode = QLabel("💡 حالت سه‌بعدی OpenGL — با ماوس بچرخانید.")
                self.lbl_bohr_mode.setStyleSheet("color: #a6e3a1; font-size: 11px; border:none;")
            except Exception as e:
                print(f"[WARN] ساخت مدل بور سه‌بعدی ناموفق: {e}", flush=True)
                self.canvas_3d = None
                self.canvas = self.canvas_2d
                self.lbl_bohr_mode = QLabel("⚠️ مدل سه‌بعدی در دسترس نیست — حالت دوبعدی.")
                self.lbl_bohr_mode.setStyleSheet("color: #f38ba8; font-size: 11px; border:none;")
        else:
            self.canvas = self.canvas_2d
            self.lbl_bohr_mode = QLabel("⚠️ مدل سه‌بعدی فقط با PyOpenGL در دسترس است — حالت دوبعدی فعال است.")
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
            "background-color: #cba6f7; color: #1e1e2e; border:none; padding: 6px; font-weight: bold;")
        self.btn_toggle_bohr_dim.clicked.connect(self.toggle_bohr_dimension)
        self.btn_toggle_bohr_dim.setEnabled(bool(self.canvas_3d))
        v_left.addWidget(self.btn_toggle_bohr_dim)

        h_btn = QHBoxLayout()
        btn_add = QPushButton("➕ افزودن الکترون")
        btn_add.setStyleSheet("background-color: #a6e3a1; color: #1e1e2e; border:none; padding: 6px;")
        btn_add.clicked.connect(self.add_electron)

        btn_remove = QPushButton("➖ حذف آخرین")
        btn_remove.setStyleSheet("background-color: #f38ba8; color: #1e1e2e; border:none; padding: 6px;")
        btn_remove.clicked.connect(self.remove_electron)

        btn_reset = QPushButton("🌀 تخلیه مدارها")
        btn_reset.setStyleSheet("background-color: #89dceb; color: #1e1e2e; border:none; padding: 6px;")
        btn_reset.clicked.connect(self.reset_electrons)

        h_btn.addWidget(btn_add)
        h_btn.addWidget(btn_remove)
        h_btn.addWidget(btn_reset)

        btn_brochure = QPushButton("📥 دانلود بروشور عنصر")
        btn_brochure.setStyleSheet("background-color: #f9e2af; color: #1e1e2e; border:none; padding: 6px;")
        btn_brochure.clicked.connect(self.download_brochure)

        self.lbl_e_total = QLabel("📀 الکترون‌ها: 0")
        self.lbl_e_total.setStyleSheet("color: #f9e2af; font-size: 16px; font-weight:bold; border:none; padding: 5px;")
        self.lbl_e_total.setAlignment(Qt.AlignCenter)
        v_left.addLayout(h_btn)
        v_left.addWidget(btn_brochure)
        v_left.addWidget(self.lbl_e_total)

        right_panel = QScrollArea()
        right_panel.setWidgetResizable(True)
        right_panel.setStyleSheet(
            "QScrollArea { border: none; background-color: #12081f; }"
            "QScrollArea > QWidget > QWidget { background-color: #12081f; }"
        )
        right_content = QWidget()
        right_content.setStyleSheet("background-color: #12081f;")
        v_right = QVBoxLayout(right_content)
        v_right.setContentsMargins(6, 6, 6, 6)
        v_right.setSpacing(6)

        self.gb_main = QGroupBox("🧪 اطلاعات عنصر")
        f_main = QFormLayout(self.gb_main)
        f_main.setLabelAlignment(Qt.AlignRight)
        f_main.setContentsMargins(8, 10, 8, 6)
        f_main.setHorizontalSpacing(10)
        f_main.setVerticalSpacing(4)

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
        v_orb.setContentsMargins(8, 8, 8, 6)
        v_orb.setSpacing(2)
        self.lbl_orbital = QLabel("—")
        self.lbl_orbital.setStyleSheet(
            "color: #fab387; font-size: 14px; font-family: Consolas, monospace; letter-spacing: 1px;"
            "background: transparent; padding: 2px;")
        self.lbl_orbital.setWordWrap(True)
        v_orb.addWidget(self.lbl_orbital)
        v_right.addWidget(self.gb_orbital)

        self.gb_compounds = QGroupBox("🔗 ترکیبات شناخته شده")
        v_comp = QVBoxLayout(self.gb_compounds)
        v_comp.setContentsMargins(6, 8, 6, 6)
        v_comp.setSpacing(2)
        self.list_compounds = QListWidget()
        self.list_compounds.setMaximumHeight(140)
        self.list_compounds.setStyleSheet(
            "background-color: #1e1e2e; border: 1px solid #45475a; border-radius: 6px; padding: 3px;")
        v_comp.addWidget(self.list_compounds)
        v_right.addWidget(self.gb_compounds)

        lbl_rule = QLabel("💡 قانون بور: گسترش یافته برای 118 عنصر بر اساس قانون مادلونگ.")
        lbl_rule.setStyleSheet(
            "color: #a6adc8; font-size: 11px; font-style: italic; background-color: #181825; padding: 6px; border-radius: 5px;")
        lbl_rule.setWordWrap(True)
        v_right.addWidget(lbl_rule)
        v_right.addStretch(0)

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
        if self.canvas_3d is None:
            return
        self._use_3d_bohr = not self._use_3d_bohr
        if self._use_3d_bohr:
            self.canvas = self.canvas_3d
            self.canvas_stack.setCurrentWidget(self.canvas_3d)
            self.canvas_3d.show()
            self.canvas_3d.raise_()
            try:
                self.canvas_3d.makeCurrent()
            except Exception:
                pass
            self.canvas_3d.update()
            QTimer.singleShot(50, self.canvas_3d.update)
            QTimer.singleShot(200, self.canvas_3d.update)
            self.lbl_bohr_mode.setText("💡 حالت سه‌بعدی — با ماوس بچرخانید.")
            self.lbl_bohr_mode.setStyleSheet("color: #a6e3a1; font-size: 11px; border:none;")
        else:
            self.canvas = self.canvas_2d
            self.canvas_stack.setCurrentWidget(self.canvas_2d)
            self.lbl_bohr_mode.setText("📐 حالت دوبعدی")
            self.lbl_bohr_mode.setStyleSheet("color: #89b4fa; font-size: 11px; border:none;")
        if hasattr(self, "Z") and self.Z:
            try:
                data = ATOMIC_DB.get(self.Z)
                sym = data[1] if data else ""
                if hasattr(self.canvas, "update_atom"):
                    self.canvas.update_atom(self.Z, sym)
            except Exception:
                pass


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

class AnimatedContainer(QWidget):
    def __init__(self, engine, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.setFixedSize(400, 520)
        DimensionController.lock(self, w=400, h=520)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setMouseTracking(True)
        self.setAcceptDrops(True)
        self._flash_opacity = 0.0
        self.display_volume = 0.0  # برای انیمیشن نرم سطح مایع
        self.animations_enabled = True

        self.anim_flash = QPropertyAnimation(self, b"flashOpacity")
        self.anim_flash.setDuration(600)
        self.anim_flash.setEasingCurve(QEasingCurve.OutQuad)

        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.process_animations)
        self.animation_timer.start(50)

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
        # سطح مایع: سریع به حجم واقعی برسد تا ماده دیده شود
        target_vol = float(self.engine.total_volume)
        if not self.animations_enabled or abs(target_vol - self.display_volume) > 50:
            self.display_volume = target_vol
        else:
            diff = target_vol - self.display_volume
            self.display_volume += diff * 0.35
            if abs(diff) < 0.5:
                self.display_volume = target_vol

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
        margin_x, margin_y = 55, 20
        container_h = h - 2 * margin_y - 30

        if dt_mult > 0 and self.animations_enabled:
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
                sh['life'] = sh.get('life', 90) - dt_mult
                if sh['life'] <= 0 or sh['y'] > h + 50 or sh['x'] < -50 or sh['x'] > self.width() + 50:
                    self.shards.remove(sh)

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

            # سقف تعداد ذرات — جلوگیری از رشد نامحدود حافظه
            for _name, _cap in (
                ("bubbles", 80), ("particles", 120), ("steam_particles", 60),
                ("overflow_particles", 40), ("shards", 80),
            ):
                _lst = getattr(self, _name, None)
                if isinstance(_lst, list) and len(_lst) > _cap:
                    setattr(self, _name, _lst[-_cap:])

        self.update()

    @Property(float)
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
        h, margin_x, margin_y = self.height(), 55, 20
        base_y = h - margin_y - 30
        total_amount = self.engine.total_volume
        if total_amount > 0:
            scale = (h - 2 * margin_y - 30) / self.engine.max_capacity
            base_y -= (total_amount * scale)

        n_spawn = min(50, max(0, 120 - len(self.particles)))
        for _ in range(n_spawn):
            self.particles.append({
                'x': random.uniform(margin_x + 20, self.width() - margin_x - 20),
                'y': base_y, 'vx': random.uniform(-4.0, 4.0), 'vy': random.uniform(3.0, 8.0),
                'life': random.randint(20, 70),
                'color': random.choice([QColor(255, 200, 50), QColor(0, 255, 255), QColor(255, 100, 255)])
            })

    def trigger_overflow(self):
        w, margin_x, margin_y = self.width(), 55, 20
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
        # Qt6: از position() به‌جای event.x()/y() deprecated استفاده می‌کنیم
        pos = event.position() if hasattr(event, "position") else event.pos()
        y_pos = pos.y()
        x_pos = pos.x()
        w, h, margin_x, margin_y = self.width(), self.height(), 55, 20
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
            if top_y <= y_pos <= current_y and margin_x <= x_pos <= w - margin_x:
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

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        text = event.mimeData().text().strip() if event.mimeData().hasText() else ""
        if not text:
            event.ignore()
            return
        key = text.split('|')[0].strip().lower()
        amt = 50.0
        if '|' in text:
            try:
                amt = float(text.split('|')[1])
            except Exception:
                pass
        win = self.window()
        if not hasattr(win, 'engine') or key not in CHEMILAB_DB:
            if hasattr(win, '_log'):
                win._log(f"ماده نامعتبر برای رها کردن: {key}")
            event.ignore()
            return
        msg, overflow, warnings = win.engine.add_chemical(key, amt)
        if hasattr(win, '_log'):
            win._log(f"📥 Drag&Drop: {msg}")
            for w in warnings:
                win._log(w)
        if overflow:
            self.trigger_overflow()
        if hasattr(win, 'update_contents_ui'):
            win.update_contents_ui()
        if hasattr(win, 'gl_beaker') and win.gl_beaker:
            win.gl_beaker._needs_redraw = True
            win.gl_beaker.update()
        self.update()
        event.acceptProposedAction()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        # حاشیه کمتر = بشر بزرگ‌تر و خواناتر
        w, h, margin_x, margin_y, plate_height = self.width(), self.height(), 55, 20, 30
        container_rect = QRectF(margin_x, margin_y, w - 2 * margin_x, h - 2 * margin_y - plate_height)
        scale = container_rect.height() / self.engine.max_capacity

        self.draw_thermometer(painter, container_rect)
        self.draw_ph_strip(painter, container_rect)

        if not self.engine.is_broken:
            # شکل بشر: دهانه کمی پهن‌تر، بدنه با گوشه پایین گرد
            lip = 10  # بیرون‌زدگی دهانه
            beaker = QPainterPath()
            tl = container_rect.topLeft() + QPointF(-lip, 0)
            tr = container_rect.topRight() + QPointF(lip, 0)
            bl = container_rect.bottomLeft()
            br = container_rect.bottomRight()
            beaker.moveTo(tl)
            beaker.lineTo(bl + QPointF(4, -6))
            beaker.quadTo(bl + QPointF(container_rect.width()/2, 8), br + QPointF(-4, -6))
            beaker.lineTo(tr)
            # پرشدگی داخلی خیلی کم
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(30, 40, 55, 70))
            painter.drawPath(beaker)
            # قاب
            painter.setPen(QPen(QColor(180, 210, 240, 230), 3.5))
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(beaker)
            # دهانه ضخیم
            painter.setPen(QPen(QColor(210, 230, 255, 250), 5))
            painter.drawLine(tl, tr)
            # بازتاب
            painter.setPen(QPen(QColor(255, 255, 255, 60), 2))
            painter.drawLine(tl + QPointF(12, 10), bl + QPointF(12, -20))

            # اگر انیمیشن عقب است، از حجم واقعی استفاده کن تا ماده دیده شود
            real_total = float(self.engine.total_volume or 0)
            if real_total > 0 and self.display_volume < real_total * 0.5:
                self.display_volume = real_total  # همگام‌سازی فوری
            total_amount = max(self.display_volume, real_total) if real_total > 0 else 0.0
            real_total = max(1e-9, real_total)
            current_y = container_rect.bottom()

            if total_amount < 0.5 or not self.engine.visual_layers:
                painter.setPen(QColor(160, 175, 200, 180))
                font_e = painter.font()
                font_e.setPointSize(12)
                painter.setFont(font_e)
                painter.drawText(container_rect, Qt.AlignCenter, "ظرف خالی\nماده اضافه کنید")

            def layer_density(layer):
                t = layer['type']
                return 10 if any(x in t for x in ["جامد", "فلز", "رسوب", "پودر", "آلیاژ"]) else (
                    0.1 if "گاز" in t else 1.0)

            if total_amount > 0 and self.engine.visual_layers:
                vol_ratio = 1.0  # همیشه ارتفاع واقعی
                layers_sorted = sorted(self.engine.visual_layers, key=layer_density, reverse=True)
                for idx, layer in enumerate(layers_sorted):
                    layer_h = float(layer.get('amount', 0)) * scale
                    # حداقل ارتفاع برای دیده شدن حتی حجم کم
                    if layer.get('amount', 0) > 0.3:
                        layer_h = max(layer_h, 8.0)
                    if layer_h <= 0.5:
                        continue
                    max_h = current_y - container_rect.top()
                    if layer_h > max_h:
                        layer_h = max_h
                    if layer_h <= 0:
                        continue
                    rect = QRectF(container_rect.left() + 3, current_y - layer_h,
                                  container_rect.width() - 6, layer_h)

                    t = str(layer.get('type', ''))
                    is_solid = any(x in t for x in ["جامد", "فلز", "رسوب", "پودر", "آلیاژ", "Solid", "Salt", "Metal"])
                    is_gas = "گاز" in t or "Gas" in t

                    c = QColor(layer.get('color', '#4aa3ff'))
                    if not c.isValid():
                        c = QColor('#4aa3ff')

                    painter.setPen(Qt.NoPen)
                    if is_solid:
                        # جامد: الگوی هاشور + رنگ مات
                        c.setAlpha(255)
                        painter.setBrush(c)
                        painter.drawRect(rect)
                        painter.setPen(QPen(c.darker(140), 1))
                        step = 8
                        x0, y0, x1, y1 = int(rect.left()), int(rect.top()), int(rect.right()), int(rect.bottom())
                        for xx in range(x0 - (y1 - y0), x1, step):
                            painter.drawLine(xx, y1, xx + (y1 - y0), y0)
                    elif is_gas:
                        c.setAlpha(90)
                        painter.setBrush(c)
                        painter.drawRect(rect)
                        painter.setPen(QPen(c.lighter(150), 1, Qt.DotLine))
                        painter.drawRect(rect.adjusted(1, 1, -1, -1))
                    else:
                        # مایع کاملاً مات و مشخص
                        c.setAlpha(255)
                        fill = QColor(c)
                        if fill.lightness() < 40:
                            fill = fill.lighter(160)
                        grad = QLinearGradient(rect.topLeft(), rect.bottomLeft())
                        grad.setColorAt(0, fill.lighter(120))
                        grad.setColorAt(1, fill.darker(120))
                        painter.setBrush(grad)
                        painter.setPen(QPen(fill.darker(140), 1))
                        painter.drawRect(rect)
                        # سطح براق
                        painter.setPen(QPen(QColor(255, 255, 255, 180), 2))
                        painter.drawLine(rect.topLeft() + QPointF(2, 1),
                                         rect.topRight() + QPointF(-2, 1))

                    # جداکننده لایه
                    painter.setPen(QPen(QColor(20, 25, 35, 180), 1))
                    painter.drawLine(rect.topLeft(), rect.topRight())

                    # برچسب واضح: نام + مقدار + نوع
                    if self.show_layer_labels and layer_h >= 12:
                        painter.save()
                        font = painter.font()
                        font.setPointSize(9 if layer_h >= 22 else 8)
                        font.setBold(True)
                        painter.setFont(font)
                        # پس‌زمینه تیره برای خوانایی متن
                        name = layer.get('name', '?')
                        amt = layer.get('amount', 0)
                        form = layer.get('formula', '')
                        kind = "جامد" if is_solid else ("گاز" if is_gas else "مایع")
                        if form:
                            form_s = ChemicalCalculator.to_subscript(form)
                            label = f"{name} ({form_s})  {amt:.0f}  [{kind}]"
                        else:
                            label = f"{name}  {amt:.0f}  [{kind}]"
                        # سایه متن
                        painter.setPen(QColor(0, 0, 0, 160))
                        painter.drawText(rect.adjusted(7, 2, -5, -2), Qt.AlignLeft | Qt.AlignVCenter, label)
                        painter.setPen(QColor(255, 255, 255, 245))
                        painter.drawText(rect.adjusted(6, 1, -5, -2), Qt.AlignLeft | Qt.AlignVCenter, label)
                        painter.restore()

                    current_y -= layer_h

            painter.setPen(Qt.NoPen)
            for b in self.bubbles:
                painter.setBrush(QColor(255, 255, 255, 120))
                painter.drawEllipse(QRectF(b['x'], b['y'], b['size'], b['size']))

            # همزن مغناطیسی بیضی‌شکل ته بشر
            painter.save()
            painter.translate(container_rect.center().x(), container_rect.bottom() - 14)
            if self.stirrer_on:
                painter.rotate(self.stirrer_angle)
                # هاله چرخش
                painter.setPen(Qt.NoPen)
                painter.setBrush(QColor(200, 180, 50, 50))
                painter.drawEllipse(QRectF(-28, -12, 56, 24))
            # بدنه بیضی
            if self.stirrer_on:
                painter.setBrush(QColor(255, 210, 60))
                painter.setPen(QPen(QColor(180, 120, 20), 2))
            else:
                painter.setBrush(QColor(160, 165, 175))
                painter.setPen(QPen(QColor(80, 85, 95), 2))
            painter.drawEllipse(QRectF(-22, -7, 44, 14))
            # خط وسط
            painter.setPen(QPen(QColor(40, 40, 50, 180), 1.5))
            painter.drawLine(-16, 0, 16, 0)
            painter.restore()

            painter.setPen(QPen(QColor(150, 170, 200, 100), 2))
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

            # خط‌کش حجم دقیق (هر ۵۰ واحد تیک کوچک، هر ۱۰۰ عدد)
            font = painter.font()
            font.setPointSize(8)
            painter.setFont(font)
            for val in range(0, int(self.engine.max_capacity) + 1, 50):
                if val == 0:
                    continue
                y_coord = container_rect.bottom() - ((val / self.engine.max_capacity) * container_rect.height())
                is_major = (val % 100 == 0)
                tick_len = 14 if is_major else 7
                painter.setPen(QPen(QColor(200, 210, 230, 200 if is_major else 120), 1))
                painter.drawLine(int(container_rect.left()), int(y_coord),
                                 int(container_rect.left() + tick_len), int(y_coord))
                if is_major:
                    painter.setPen(QColor(180, 190, 210))
                    painter.drawText(int(container_rect.left()) - 42, int(y_coord) + 4, f"{val}")
            painter.setPen(QColor(150, 160, 180))
            painter.drawText(int(container_rect.left()) - 42, int(container_rect.top()) - 4, "mL")

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
        painter.setPen(QPen(QColor(255, 0, 0, 200), 1, Qt.DashLine))
        painter.drawLine(int(tx - 8), int(break_y), int(tx + tw + 8), int(break_y))
        painter.setPen(QPen(QColor(255, 80, 80, 230), 1))
        font_br = painter.font()
        font_br.setPointSize(8)
        font_br.setBold(True)
        painter.setFont(font_br)
        painter.drawText(int(tx + tw + 8), int(break_y) + 4, f"شکست {int(FLASK_BREAK_TEMP)}°C")

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
    """ویجت مدال با کارت مدرن و hover"""
    def __init__(self, badge_name, earned=True, parent=None):
        super().__init__(parent)
        self.badge_name = badge_name
        self.earned = earned
        icon, desc = BADGE_CATALOG.get(badge_name, ("🏅", "بدون توضیح"))
        self.icon = icon
        self.desc = desc
        self.setFixedSize(110, 120)
        self.setToolTip(f"{icon} {badge_name}\n{desc}")
        self.setCursor(Qt.PointingHandCursor)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect().adjusted(4, 4, -4, -4)
        # کارت پس‌زمینه
        if self.earned:
            painter.setBrush(QColor(30, 30, 46, 230))
            painter.setPen(QPen(QColor(249, 226, 175, 180), 2))
        else:
            painter.setBrush(QColor(20, 20, 28, 200))
            painter.setPen(QPen(QColor(69, 71, 90, 120), 1))
        painter.drawRoundedRect(rect, 14, 14)
        # دایره مدال
        cx, cy = rect.center().x(), rect.top() + 38
        rad = 28
        if self.earned:
            grad = QRadialGradient(cx - 6, cy - 6, rad)
            grad.setColorAt(0, QColor(255, 230, 120, 220))
            grad.setColorAt(1, QColor(200, 140, 30, 180))
            painter.setBrush(grad)
            painter.setPen(QPen(QColor(255, 215, 0), 2))
        else:
            painter.setBrush(QColor(50, 50, 60))
            painter.setPen(QPen(QColor(80, 80, 90), 1))
        painter.drawEllipse(QPointF(cx, cy), rad, rad)
        font = painter.font()
        font.setPointSize(22)
        painter.setFont(font)
        painter.setPen(QColor(255, 255, 255) if self.earned else QColor(100, 100, 110))
        painter.drawText(QRectF(cx - rad, cy - rad, rad * 2, rad * 2), Qt.AlignCenter, self.icon)
        font.setPointSize(9)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor(249, 226, 175) if self.earned else QColor(120, 120, 130))
        name = self.badge_name if len(self.badge_name) <= 12 else self.badge_name[:11] + "…"
        painter.drawText(QRectF(rect.x() + 4, rect.bottom() - 36, rect.width() - 8, 28),
                         Qt.AlignHCenter | Qt.AlignTop | Qt.TextWordWrap, name)


# ----------------- دیالوگ‌ها -----------------
class LoginDialog(QDialog):
    """پنجره ورود به آزمایشگاه."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("شیمی‌لَب V48 — ورود")
        self.setFixedSize(480, 420)
        self.setModal(True)
        self._is_admin = False
        self._admin_unlocked = False
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 #0c0914, stop:0.5 #1a0f2e, stop:1 #12081f);
                border: 2px solid #7c3aed; border-radius: 16px;
            }
            QLabel { color: #e8e0f5; font-size: 14px; font-weight: bold; background: transparent; }
            QLineEdit {
                padding: 12px 16px; border-radius: 12px; border: 1px solid #5b3d7a;
                background: #160f22; color: #c4b5fd; font-size: 15px; font-weight: bold;
            }
            QLineEdit:focus { border: 2px solid #a78bfa; background: #1e1530; }
            QPushButton#primary {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #7c3aed, stop:1 #a78bfa);
                color: #0c0914; padding: 12px; border-radius: 12px; font-weight: bold; font-size: 15px;
                border: none;
            }
            QPushButton#primary:hover {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #8b5cf6, stop:1 #c4b5fd);
            }
            QPushButton#primary:pressed { background: #5b21b6; color: #fff; }
        """)
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(36, 28, 36, 28)

        title = QLabel("🧪 شیمی‌لَب V48")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 26px; font-weight: bold; color: #c4b5fd;")
        layout.addWidget(title)

        sub = QLabel("Universe ChimiLab V49  •  خراسان رضوی")
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet("font-size: 12px; color: #a78bfa; font-weight: normal;")
        layout.addWidget(sub)
        layout.addSpacing(6)

        layout.addWidget(QLabel("نام کاربری:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("نام خود را وارد کنید…")
        self.name_input.textChanged.connect(self._on_name_changed)
        self.name_input.returnPressed.connect(self.check_input)
        layout.addWidget(self.name_input)

        self.pass_lbl = QLabel("رمز محافظ دیتابیس:")
        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.Password)
        self.pass_input.setPlaceholderText("رمز ادمین…")
        self.pass_input.returnPressed.connect(self.check_input)
        self.pass_lbl.setVisible(False)
        self.pass_input.setVisible(False)
        layout.addWidget(self.pass_lbl)
        layout.addWidget(self.pass_input)

        self.pass2_lbl = QLabel("تکرار رمز (اولین بار):")
        self.pass2_input = QLineEdit()
        self.pass2_input.setEchoMode(QLineEdit.Password)
        self.pass2_input.setPlaceholderText("تأیید رمز جدید…")
        self.pass2_lbl.setVisible(False)
        self.pass2_input.setVisible(False)
        layout.addWidget(self.pass2_lbl)
        layout.addWidget(self.pass2_input)

        self.err_lbl = QLabel("")
        self.err_lbl.setStyleSheet("color: #f38ba8; font-size: 12px;")
        self.err_lbl.setAlignment(Qt.AlignCenter)
        self.err_lbl.setWordWrap(True)
        layout.addWidget(self.err_lbl)

        btn = QPushButton("✅ ورود")
        btn.setObjectName("primary")
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(self.check_input)
        layout.addWidget(btn)

        hint = QLabel("نام خود را وارد کنید و وارد آزمایشگاه شوید")
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet("color: #6b5b80; font-size: 11px; font-weight: normal;")
        layout.addWidget(hint)

    def _on_name_changed(self, text):
        is_adm = text.strip().lower() == "admin"
        self.pass_lbl.setVisible(is_adm)
        self.pass_input.setVisible(is_adm)
        need_set = is_adm and not AdminAuth.is_password_set()
        self.pass2_lbl.setVisible(need_set)
        self.pass2_input.setVisible(need_set)
        if need_set:
            self.pass_lbl.setText("تعیین رمز جدید دیتابیس:")
            self.pass_input.setPlaceholderText("حداقل ۴ کاراکتر")
        else:
            self.pass_lbl.setText("رمز محافظ دیتابیس:")
            self.pass_input.setPlaceholderText("رمز ادمین…")
        self.err_lbl.setText("")

    def check_input(self):
        global DB_WRITE_UNLOCKED
        name = self.name_input.text().strip()
        if not name:
            self.err_lbl.setText("⚠️ لطفاً نام معتبر وارد کنید")
            return
        if name.lower() != "admin":
            self._is_admin = False
            self._admin_unlocked = False
            DB_WRITE_UNLOCKED = False
            self.accept()
            return

        # مسیر ادمین
        pwd = self.pass_input.text()
        if not AdminAuth.is_password_set():
            pwd2 = self.pass2_input.text()
            if len(pwd.strip()) < 4:
                self.err_lbl.setText("⚠️ رمز باید حداقل ۴ کاراکتر باشد")
                return
            if pwd != pwd2:
                self.err_lbl.setText("⚠️ تکرار رمز مطابقت ندارد")
                return
            if not AdminAuth.set_password(pwd):
                self.err_lbl.setText("❌ خطا در ذخیره رمز")
                return
            self._is_admin = True
            self._admin_unlocked = True
            DB_WRITE_UNLOCKED = True
            self.accept()
            return

        if not AdminAuth.verify(pwd):
            self.err_lbl.setText("❌ رمز اشتباه است — دسترسی به دیتابیس رد شد")
            return
        self._is_admin = True
        self._admin_unlocked = True
        DB_WRITE_UNLOCKED = True
        self.accept()

    def get_name(self):
        return self.name_input.text().strip()

    def is_admin(self):
        return self._is_admin

    def is_admin_unlocked(self):
        return self._admin_unlocked



class ModernLabWindow(QMainWindow):
    def __init__(self, player_name="دانشجو", is_admin=False):
        super().__init__()
        self.is_admin = bool(is_admin)
        self._logout_requested = False
        role = "مدیر" if self.is_admin else "دانش‌آموز"
        self.setWindowTitle(f"{APP_NAME} {APP_VERSION} — {role}: {player_name}")
        self.resize(1550, 950)
        self.is_dark_mode = True

        self.engine = LabEngine()
        if player_name:
            self.engine.player_name = str(player_name).strip()[:64] or "دانشجو"
            # LabEngine initially loads its default identity. Reload here for the
            # actual logged-in user before any save can overwrite their progress.
            self.engine.load_data()
            self.engine.save_data()
        else:
            self.engine.player_name = "دانشجو"

        self.data_time, self.data_ph, self.data_temp = [], [], []
        self.last_ph = 7.0

        self.setup_ui()
        self._setup_shortcuts()
        try:
            self.update_player_stats()
        except Exception:
            pass
        if hasattr(self, "combo_chem") and self.combo_chem is not None:
            try:
                self.combo_chem.installEventFilter(self)
            except Exception:
                pass
        self.setFocusPolicy(Qt.StrongFocus)
        try:
            get_logger().info(f"شروع — کاربر: {self.engine.player_name} | admin={self.is_admin}")
        except Exception:
            pass

        self.timer = QTimer()
        self.timer.timeout.connect(self.game_loop)
        if self.is_admin:
            pass
        else:
            QTimer.singleShot(400, self.start_simulation)
            if self.engine.score == 0:
                QTimer.singleShot(700, self.show_tutorial)

        self._last_warning_temp = 0

    def start_simulation(self):
        self.timer.start(120)  # ~8 FPS کافی است؛ کاهش لگ UI  # 12.5 fps — سبک‌تر و پایدارتر

    def request_logout(self):
        """خروج از حساب — فقط نشست فعلی پاک می‌شود؛ پیشرفت سایر کاربران حفظ می‌ماند."""
        global DB_WRITE_UNLOCKED
        msg = (
            "آیا از حساب خارج می‌شوید؟\n\n"
            "پیشرفت شما روی دیسک ذخیره می‌ماند و دفعه بعد با همان نام قابل بازیابی است.\n"
            "برای پاک‌کردن کامل پیشرفت همین کاربر از منوی مدیریت استفاده کنید."
        )
        reply = QMessageBox.question(
            self, "خروج از حساب", msg,
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        DB_WRITE_UNLOCKED = False
        try:
            if hasattr(self, "timer") and self.timer is not None:
                self.timer.stop()
        except Exception as e:
            tlog(f"logout timer stop: {e}", "WARN")
        try:
            # ذخیرهٔ آخرین وضعیت همین کاربر قبل از خروج
            if hasattr(self, "engine") and self.engine is not None and not getattr(self, "is_admin", False):
                self.engine.save_data()
        except Exception as e:
            tlog(f"logout save: {e}", "WARN")
        try:
            clear_active_session()
        except Exception as e:
            tlog(f"logout clear session: {e}", "WARN")
        # هرگز wipe_all_user_progress را در logout صدا نزن — فقط نشست فعلی
        self._logout_requested = True
        self.close()

    def closeEvent(self, event):
        try:
            if not getattr(self, "_logout_requested", False):
                if hasattr(self, "engine") and self.engine is not None:
                    self.engine.save_data()
                if not getattr(self, "is_admin", False) and hasattr(self, "engine") and self.engine is not None:
                    save_active_session(self.engine.player_name, is_admin=False)
                else:
                    clear_active_session()
        except Exception as e:
            tlog(f"closeEvent save/session failed: {e}", "WARN")
        event.accept()

    def _setup_admin_ui(self):
        """رابط اختصاصی مدیر — فقط امنیت و مدیریت دیتابیس (بدون بشر و مدل بور)."""
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        top = QHBoxLayout()
        title = QLabel(f"🛡️ {APP_NAME} {APP_VERSION} — پنل مدیریت دیتابیس")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #c4b5fd;")
        top.addWidget(title, 1)
        lock = "🔓 ویرایش فعال" if DB_WRITE_UNLOCKED else "🔒 قفل"
        self.lbl_admin_lock = QLabel(lock)
        self.lbl_admin_lock.setStyleSheet("color: #c4b5fd; font-weight: bold; font-size: 13px;")
        top.addWidget(self.lbl_admin_lock)
        btn_logout = QPushButton("🚪 خروج")
        btn_logout.clicked.connect(self.request_logout)
        btn_logout.setStyleSheet(
            "background: #7c3aed; color: white; font-weight: bold; padding: 8px 14px; border-radius: 8px;")
        top.addWidget(btn_logout)
        layout.addLayout(top)

        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_admin_dashboard_tab(), "🛡️ داشبورد")
        self.tabs.addTab(self.create_admin_db_tab(), "🗄️ مواد")
        self.tabs.addTab(self.create_admin_reactions_tab(), "⚗️ واکنش‌ها")
        self.tabs.addTab(self.create_admin_security_tab(), "🔐 رمز و امنیت")
        self.tabs.addTab(self.create_about_tab(), "ℹ️ درباره")
        layout.addWidget(self.tabs, 1)

        self.main_splitter = None
        self.left_panel = None
        self.center_panel = None
        self.right_tabs = self.tabs
        self.container = None
        self.gl_beaker = None
        self.btn_titrate = type("B", (), {"isChecked": lambda self: False, "setChecked": lambda self, v: None})()
        self.txt_log = type("T", (), {"append": lambda self, m: None, "toPlainText": lambda self: ""})()
        self.txt_notes = type("T", (), {"toPlainText": lambda self: "", "setPlainText": lambda self, t: None})()
        self.lbl_ph_display = QLabel("")
        self.lbl_temp_display = QLabel("")
        self.last_ph = 7.0
        self.data_time, self.data_ph, self.data_temp = [], [], []

    def _build_menubar(self):
        """منوی کشویی سراسری — جایگزین دکمه‌های پراکنده."""
        mb = self.menuBar()
        mb.clear()

        m_file = mb.addMenu("📁 فایل")
        act_save = QAction("💾 ذخیره وضعیت…", self)
        act_save.setShortcut(QKeySequence("Ctrl+S"))
        act_save.triggered.connect(self.action_save_state_file)
        m_file.addAction(act_save)
        act_load = QAction("📂 بارگذاری وضعیت…", self)
        act_load.triggered.connect(self.action_load_state_file)
        m_file.addAction(act_load)
        m_file.addSeparator()
        act_txt = QAction("📥 خروجی TXT", self)
        act_txt.triggered.connect(self.action_export_txt)
        m_file.addAction(act_txt)
        act_pdf = QAction("📑 خروجی PDF", self)
        act_pdf.triggered.connect(self.action_export_pdf)
        m_file.addAction(act_pdf)
        act_shot = QAction("📸 عکس از ظرف", self)
        act_shot.triggered.connect(self.action_screenshot)
        m_file.addAction(act_shot)
        m_file.addSeparator()
        act_logout = QAction("🚪 خروج از حساب", self)
        act_logout.triggered.connect(self.request_logout)
        m_file.addAction(act_logout)

        m_edit = mb.addMenu("✏️ ویرایش")
        self.act_undo = QAction("↩ بازگشت", self)
        self.act_undo.setShortcut(QKeySequence("Ctrl+Z"))
        self.act_undo.triggered.connect(self.action_undo)
        m_edit.addAction(self.act_undo)
        self.act_redo = QAction("↪ جلو", self)
        self.act_redo.setShortcut(QKeySequence("Ctrl+Y"))
        self.act_redo.triggered.connect(self.action_redo)
        m_edit.addAction(self.act_redo)

        m_lab = mb.addMenu("🧪 آزمایشگاه")
        act_filter = QAction("⚗️ فیلتر جامدات", self)
        act_filter.setShortcut(QKeySequence("F"))
        act_filter.triggered.connect(self.action_filter)
        m_lab.addAction(act_filter)
        act_wash = QAction("🚿 تعویض / شستشوی ظرف", self)
        act_wash.triggered.connect(self.action_wash)
        m_lab.addAction(act_wash)
        m_lab.addSeparator()
        act_heat = QAction("🔥 گرمایش (+۵°)", self)
        act_heat.setShortcut(QKeySequence("H"))
        act_heat.triggered.connect(self.action_heat)
        m_lab.addAction(act_heat)
        act_cool = QAction("🧊 سرمایش (−۵°)", self)
        act_cool.setShortcut(QKeySequence("C"))
        act_cool.triggered.connect(self.action_cool)
        m_lab.addAction(act_cool)
        m_lab.addSeparator()
        self.act_stirrer = QAction("🌪️ همزن مغناطیسی", self)
        self.act_stirrer.setCheckable(True)
        self.act_stirrer.setShortcut(QKeySequence("Space"))
        self.act_stirrer.triggered.connect(self._menu_toggle_stirrer)
        m_lab.addAction(self.act_stirrer)
        self.act_titrate = QAction("💧 بورت / تیتراسیون", self)
        self.act_titrate.setCheckable(True)
        self.act_titrate.triggered.connect(self._menu_toggle_titration)
        m_lab.addAction(self.act_titrate)

        m_view = mb.addMenu("👁️ نمایش")
        act_3d = QAction("🔄 نمای ۲بعدی / ۳بعدی بشر", self)
        act_3d.triggered.connect(self.toggle_beaker_view)
        m_view.addAction(act_3d)
        act_mol = QAction("🧬 مدل مولکولی سه‌بعدی", self)
        act_mol.triggered.connect(self.show_selected_molecule_3d)
        m_view.addAction(act_mol)
        act_mix = QAction("🧪 مولکول ۳بعدی (مخلوط ظرف)", self)
        act_mix.triggered.connect(self.show_mixture_molecule_3d)
        m_view.addAction(act_mix)
        m_view.addSeparator()
        act_tabs = QAction("پنل تب‌ها (نمایش/مخفی)", self)
        act_tabs.triggered.connect(self.toggle_tabs)
        m_view.addAction(act_tabs)

        m_help = mb.addMenu("❓ راهنما")
        act_tut = QAction("📖 راهنمای سریع", self)
        act_tut.triggered.connect(self.show_tutorial)
        m_help.addAction(act_tut)
        act_set = QAction("⚙️ تنظیمات", self)
        act_set.triggered.connect(self.open_settings_panel)
        m_help.addAction(act_set)
        act_prof = QAction("👤 پروفایل شیمیدان", self)
        act_prof.triggered.connect(self.open_profile_dialog)
        m_help.addAction(act_prof)

    def _menu_toggle_stirrer(self):
        if hasattr(self, "btn_stirrer") and self.btn_stirrer is not None:
            self.btn_stirrer.setChecked(self.act_stirrer.isChecked())
        self.action_toggle_stirrer()

    def _menu_toggle_titration(self):
        if hasattr(self, "btn_titrate") and self.btn_titrate is not None:
            self.btn_titrate.setChecked(self.act_titrate.isChecked())
        self.action_toggle_titration()

    def setup_ui(self):
        if self.is_admin:
            self._setup_admin_ui()
            return
        self._build_menubar()
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        top_bar = QFrame()
        top_bar.setFixedHeight(50)
        top_bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        top_bar.setStyleSheet(
            "background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #0e0a16, stop:1 #1a1228);"
            "border-bottom: 1px solid #2e2e48;")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(12, 6, 12, 6)
        top_layout.setSpacing(10)

        self.btn_profile = QPushButton("👤 پروفایل")
        self.btn_profile.setCursor(Qt.PointingHandCursor)
        self.btn_profile.setStyleSheet(
            "background-color: #3b2a55; color: #e8e0f5; font-weight: bold; padding: 6px 12px; "
            "border-radius: 8px; font-size: 12px; border: 1px solid #5b21b6;")
        self.btn_profile.clicked.connect(self.open_profile_dialog)
        top_layout.addWidget(self.btn_profile)

        self.btn_undo = QPushButton("↩")
        self.btn_undo.setToolTip("بازگشت (Ctrl+Z)")
        self.btn_undo.setFixedWidth(40)
        self.btn_undo.setStyleSheet(
            "background-color: #fab387; color: #160f22; font-weight: bold; padding: 6px; "
            "border-radius: 8px; font-size: 14px;")
        self.btn_undo.clicked.connect(self.action_undo)
        top_layout.addWidget(self.btn_undo)

        self.btn_redo = QPushButton("↪")
        self.btn_redo.setToolTip("جلو (Ctrl+Y)")
        self.btn_redo.setFixedWidth(40)
        self.btn_redo.setStyleSheet(
            "background-color: #c4b5fd; color: #160f22; font-weight: bold; padding: 6px; "
            "border-radius: 8px; font-size: 14px;")
        self.btn_redo.clicked.connect(self.action_redo)
        top_layout.addWidget(self.btn_redo)

        self.lbl_safety_status = QLabel("✅ ایمن")
        self.lbl_safety_status.setStyleSheet(
            "background-color: #1e2e1a; color: #a6e3a1; font-weight: bold; padding: 4px 10px; "
            "border-radius: 8px; border: 1px solid #a6e3a1; font-size: 12px;")
        top_layout.addWidget(self.lbl_safety_status)

        top_layout.addStretch()

        self.lbl_top_status = QLabel(f"{APP_NAME} {APP_VERSION}")
        self.lbl_top_status.setStyleSheet("color: #89dceb; font-weight: bold; font-size: 13px;")
        top_layout.addWidget(self.lbl_top_status)

        self.btn_logout = QPushButton("🚪 خروج")
        self.btn_logout.setCursor(Qt.PointingHandCursor)
        self.btn_logout.setStyleSheet(
            "QPushButton { background: #5b21b6; color: #fff; font-weight: bold; "
            "padding: 6px 12px; border-radius: 8px; font-size: 12px; border: 1px solid #a78bfa; }"
            "QPushButton:hover { background: #7c3aed; }")
        self.btn_logout.clicked.connect(self.request_logout)
        top_layout.addWidget(self.btn_logout)
        layout.addWidget(top_bar)

        main_splitter = QSplitter(Qt.Horizontal)
        self.left_panel = self._create_left_panel()
        self.center_panel = self._create_center_panel()
        tabs_inner = self._create_all_tabs()
        if getattr(self, "_tab_nav_bar", None) is not None:
            wrap = QWidget()
            wl = QVBoxLayout(wrap)
            wl.setContentsMargins(0, 0, 0, 0)
            wl.setSpacing(2)
            wl.addWidget(self._tab_nav_bar)
            wl.addWidget(tabs_inner, 1)
            self.right_tabs = wrap
            self.tabs = tabs_inner  # keep ref
        else:
            self.right_tabs = tabs_inner


        main_splitter.addWidget(self.left_panel)
        main_splitter.addWidget(self.center_panel)
        main_splitter.addWidget(self.right_tabs)
        main_splitter.setSizes([400, 500, 600])
        main_splitter.setStretchFactor(0, 0)
        main_splitter.setStretchFactor(1, 1)
        main_splitter.setStretchFactor(2, 1)
        main_splitter.setChildrenCollapsible(False)
        # سه پنل جدا — بشر وسط نباید زیر تب‌ها برود
        self.left_panel.setMinimumWidth(360)
        self.center_panel.setMinimumWidth(320)
        self.center_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.right_tabs.setMinimumWidth(280)
        self.right_tabs.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        main_splitter.setHandleWidth(6)
        main_splitter.setStyleSheet(
            "QSplitter::handle { background: #3d2a55; width: 6px; }"
            "QSplitter::handle:hover { background: #a78bfa; }"
        )
        main_splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.main_splitter = main_splitter

        layout.addWidget(main_splitter, 1)
        tlog("main_splitter اضافه شد", "LAYOUT", sizes=main_splitter.sizes())
        # بعد از نمایش، اندازه‌ها را دوباره اجبار کن تا قاطی نشوند
        QTimer.singleShot(80, self._enforce_splitter_layout)
        QTimer.singleShot(400, self._enforce_splitter_layout)

        self._create_bottom_toolbar(layout)
        layout.setStretch(0, 0)  # top
        layout.setStretch(1, 1)  # splitter
        layout.setStretch(2, 0)  # bottom
        if getattr(self, '_bottom_toolbar_ref', None):
            tlog("پس از ساخت نوار پایین", "LAYOUT",
                 visible=self._bottom_toolbar_ref.isVisible(),
                 h=self._bottom_toolbar_ref.height(),
                 geo=str(self._bottom_toolbar_ref.geometry()))
        self.setMinimumSize(1180, 720)

    def show_tutorial(self):
        dlg = QDialog(self)
        dlg.setWindowTitle(f"راهنما — {APP_NAME} {APP_VERSION}")
        dlg.setMinimumSize(520, 360)
        dlg.setStyleSheet(
            "QDialog { background: #12081f; } "
            "QLabel { color: #e8e0f5; font-size: 13px; } "
            "QPushButton { background: #5b21b6; color: #fff; font-weight: bold; "
            "padding: 10px 16px; border-radius: 10px; border: 1px solid #a78bfa; }"
            "QPushButton:hover { background: #7c3aed; }"
        )
        lay = QVBoxLayout(dlg)
        lay.setSpacing(14)
        title = QLabel("🧪 شیمی‌لَب — شبیه‌ساز آزمایشگاه شیمی")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #c4b5fd;")
        title.setAlignment(Qt.AlignCenter)
        lay.addWidget(title)
        desc = QLabel(
            "در این برنامه می‌توانید مواد را به بشر اضافه کنید، واکنش‌ها را کشف کنید، "
            "دما و pH را کنترل کنید و با مأموریت‌ها پیشرفت کنید.\n\n"
            "میانبرها: H گرمایش | C سرمایش | F فیلتر | Space همزن | Ctrl+S ذخیره"
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #c4b5fd; padding: 8px;")
        lay.addWidget(desc)
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("📄 مشاهده سورس و صفحه گیت‌هاب:"))
        btn_gh = QPushButton("صفحه گیت‌هاب")
        btn_gh.setCursor(Qt.PointingHandCursor)
        def open_github():
            from PySide6.QtGui import QDesktopServices
            from PySide6.QtCore import QUrl
            QDesktopServices.openUrl(QUrl("https://github.com/kianfadaee448-alt/ChimiLab"))
        btn_gh.clicked.connect(open_github)
        row1.addWidget(btn_gh)
        lay.addLayout(row1)
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("✉️ ارتباط با سازنده:"))
        btn_mail = QPushButton("ارسال ایمیل")
        btn_mail.setCursor(Qt.PointingHandCursor)
        def open_mail():
            from PySide6.QtGui import QDesktopServices
            from PySide6.QtCore import QUrl
            QDesktopServices.openUrl(QUrl(f"mailto:{CONTACT_EMAIL}?subject=ChimiLab%20{APP_VERSION}"))
        btn_mail.clicked.connect(open_mail)
        row2.addWidget(btn_mail)
        lay.addLayout(row2)
        lay.addStretch()
        btn_ok = QPushButton("باشه")
        btn_ok.clicked.connect(dlg.accept)
        lay.addWidget(btn_ok, 0, Qt.AlignCenter)
        dlg.exec()

    def eventFilter(self, obj, event):
        return super().eventFilter(obj, event)

    def start_chem_drag(self):
        """شروع کشیدن ماده انتخاب‌شده به ظرف"""
        from PySide6.QtCore import QMimeData
        from PySide6.QtGui import QDrag
        key = self.combo_chem.currentData() if hasattr(self, 'combo_chem') else None
        if not key:
            self._log("ابتدا یک ماده انتخاب کنید.")
            return
        drag = QDrag(self)
        mime = QMimeData()
        amt = self.spin_vol.value() if hasattr(self, 'spin_vol') else 50
        mime.setText(f"{key}|{amt}")
        drag.setMimeData(mime)
        self._log(f"در حال کشیدن… روی ظرف رها کنید ({amt:.0f})")
        drag.exec(Qt.CopyAction)

    def action_undo(self):
        if self.engine.undo():
            self.update_contents_ui()
            if hasattr(self, 'gl_beaker') and self.gl_beaker:
                self.gl_beaker._needs_redraw = True
                self.gl_beaker.update()
            n = self.engine.undo_count()
            self._log(f"↩ به حالت قبل برگشتید. (قابل بازگشت: {n})")
            self.update_auto_log_ui()
            self._update_undo_redo_labels()
        else:
            self._log("چیزی برای بازگشت وجود ندارد.")

    def action_redo(self):
        if self.engine.redo():
            self.update_contents_ui()
            if hasattr(self, 'gl_beaker') and self.gl_beaker:
                self.gl_beaker._needs_redraw = True
                self.gl_beaker.update()
            self._log(f"↪ جلو رفتید. (Redo باقی: {self.engine.redo_count()})")
            self.update_auto_log_ui()
            self._update_undo_redo_labels()
        else:
            self._log("چیزی برای جلو رفتن وجود ندارد.")

    def _update_undo_redo_labels(self):
        if hasattr(self, 'btn_undo'):
            n = self.engine.undo_count()
            self.btn_undo.setText(f"↩{n}" if n else "↩")
            self.btn_undo.setToolTip(f"بازگشت ({n})" if n else "بازگشت (Ctrl+Z)")
        if hasattr(self, 'btn_redo'):
            n = self.engine.redo_count()
            self.btn_redo.setText(f"↪{n}" if n else "↪")
            self.btn_redo.setToolTip(f"جلو ({n})" if n else "جلو (Ctrl+Y)")
        if hasattr(self, "act_undo"):
            n = self.engine.undo_count()
            self.act_undo.setText(f"↩ بازگشت ({n})" if n else "↩ بازگشت")
        if hasattr(self, "act_redo"):
            n = self.engine.redo_count()
            self.act_redo.setText(f"↪ جلو ({n})" if n else "↪ جلو")
        self._update_safety_status()

    def _update_safety_status(self):
        """نوار وضعیت ایمنی رنگی: سبز / زرد / قرمز"""
        if not hasattr(self, 'lbl_safety_status'):
            return
        count = getattr(self.engine, 'safety_warnings_count', 0)
        temp = self.engine.temp_c
        ph = self.engine.get_ph()
        broken = self.engine.is_broken
        level = "green"
        msg = "✅ وضعیت ایمنی: ایمن"
        if broken:
            level = "red"
            msg = "🔴 ظرف شکسته! تعویض کنید"
        elif temp > 300 or count >= 8:
            level = "red"
            msg = f"🔴 خطر بالا — هشدارها: {count} | دما: {temp:.0f}°C"
        elif temp > 120 or count >= 3 or ph < 1 or ph > 13:
            level = "yellow"
            msg = f"🟡 احتیاط — هشدارها: {count} | pH={ph:.1f} | T={temp:.0f}°C"
        else:
            msg = f"✅ ایمن — هشدارها: {count}"
        colors = {
            "green": ("#c4b5fd", "#1e2e1a"),
            "yellow": ("#f9e2af", "#2e2a1a"),
            "red": ("#f38ba8", "#2e1a1a"),
        }
        fg, bg = colors.get(level, colors["green"])
        self.lbl_safety_status.setText(msg)
        self.lbl_safety_status.setStyleSheet(
            f"background-color: {bg}; color: {fg}; font-weight: bold; padding: 4px 10px; "
            f"border-radius: 8px; border: 1px solid {fg}; font-size: 12px;")

    def open_settings_panel(self):
        """تنظیمات: پنل‌ها، انیمیشن، بازگردانی"""
        dlg = QDialog(self)
        dlg.setWindowTitle("تنظیمات برنامه")
        dlg.setFixedSize(440, 480)
        dlg.setStyleSheet("background-color: #160f22; color: #e8e0f5;")
        v = QVBoxLayout(dlg)
        v.addWidget(QLabel("نمایش پنل‌ها:"))
        from PySide6.QtWidgets import QCheckBox
        if not hasattr(self, '_panel_vis_backup'):
            self._panel_vis_backup = {}
        cb_left = QCheckBox("پنل چپ (مواد و ابزار)")
        cb_left.setChecked(self.left_panel.isVisible())
        cb_center = QCheckBox("ظرف واکنش (مرکز)")
        cb_center.setChecked(self.center_panel.isVisible())
        cb_right = QCheckBox("تب‌های راست (اطلاعات)")
        cb_right.setChecked(self.right_tabs.isVisible())
        bottom_bar = getattr(self, '_bottom_toolbar_ref', None)
        if bottom_bar is None:
            for i in range(self.centralWidget().layout().count()):
                item = self.centralWidget().layout().itemAt(i)
                if item and item.widget() and isinstance(item.widget(), QFrame):
                    w = item.widget()
                    if "border-top" in (w.styleSheet() or ""):
                        bottom_bar = w
                        self._bottom_toolbar_ref = w
                        break
        cb_bottom = QCheckBox("نوار ابزار پایین")
        cb_bottom.setChecked(bottom_bar.isVisible() if bottom_bar else True)
        cb_anim = QCheckBox("انیمیشن‌ها (حباب، ذرات، سطح مایع)")
        cb_anim.setChecked(getattr(self.container, 'animations_enabled', True))
        for cb in (cb_left, cb_center, cb_right, cb_bottom, cb_anim):
            cb.setStyleSheet("font-size: 14px; padding: 6px;")
            v.addWidget(cb)
        v.addStretch()
        h_btns = QHBoxLayout()
        btn_ok = QPushButton("اعمال")
        btn_ok.setStyleSheet("background-color: #c4b5fd; color: #160f22; font-weight: bold; padding: 10px; border-radius: 8px;")
        btn_restore = QPushButton("بازگردانی پنل‌ها")
        btn_restore.setStyleSheet("background-color: #fab387; color: #160f22; font-weight: bold; padding: 10px; border-radius: 8px;")
        btn_log = QPushButton("📋 باز کردن فایل لاگ")
        btn_log.setStyleSheet("background-color: #89b4fa; color: #160f22; font-weight: bold; padding: 10px; border-radius: 8px;")
        def open_log():
            import subprocess
            p = get_logger().path
            try:
                if sys.platform.startswith('win'):
                    os.startfile(p)
                else:
                    subprocess.Popen(['xdg-open', p])
            except Exception:
                QMessageBox.information(dlg, "لاگ", f"مسیر فایل لاگ:\n{p}")
        btn_log.clicked.connect(open_log)
        v.addWidget(btn_log)
        def apply():
            self._panel_vis_backup = {
                'left': self.left_panel.isVisible(),
                'center': self.center_panel.isVisible(),
                'right': self.right_tabs.isVisible(),
                'bottom': bottom_bar.isVisible() if bottom_bar else True,
            }
            self.left_panel.setVisible(cb_left.isChecked())
            self.center_panel.setVisible(cb_center.isChecked())
            self.right_tabs.setVisible(cb_right.isChecked())
            if bottom_bar:
                bottom_bar.setVisible(cb_bottom.isChecked())
            self.container.animations_enabled = cb_anim.isChecked()
            dlg.accept()
        def restore():
            bak = getattr(self, '_panel_vis_backup', None)
            if bak:
                self.left_panel.setVisible(bak.get('left', True))
                self.center_panel.setVisible(bak.get('center', True))
                self.right_tabs.setVisible(bak.get('right', True))
                if bottom_bar:
                    bottom_bar.setVisible(bak.get('bottom', True))
                QMessageBox.information(dlg, "بازگردانی", "وضعیت قبلی پنل‌ها برگردانده شد.")
            else:
                self.left_panel.setVisible(True)
                self.center_panel.setVisible(True)
                self.right_tabs.setVisible(True)
                if bottom_bar:
                    bottom_bar.setVisible(True)
                QMessageBox.information(dlg, "بازگردانی", "همه پنل‌ها نمایش داده شدند.")
        btn_ok.clicked.connect(apply)
        btn_restore.clicked.connect(restore)
        h_btns.addWidget(btn_restore)
        h_btns.addWidget(btn_ok)
        v.addLayout(h_btns)
        dlg.exec()

    def _create_left_panel(self):
        """پنل افزودن ماده — اسکرول‌پذیر، بدون پروفایل (پروفایل در نوار بالا)."""
        outer = QFrame()
        DimensionController.lock(outer, min_w=360)
        outer.setMinimumWidth(360)
        outer_lay = QVBoxLayout(outer)
        outer_lay.setContentsMargins(0, 0, 0, 0)
        outer_lay.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        panel = QWidget()
        vbox = QVBoxLayout(panel)
        vbox.setSpacing(10)
        vbox.setContentsMargins(8, 8, 8, 8)

        gb_chem = QGroupBox("افزودن ماده به بشر")
        frm = QFormLayout()
        frm.setSpacing(8)
        frm.setContentsMargins(8, 14, 8, 8)

        h_search = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍 جستجو...")
        self.search_box.setMinimumHeight(32)
        self.search_box.setStyleSheet(
            "background-color: #160f22; color: #c4b5fd; border: 1px solid #3d2a55; "
            "border-radius: 8px; padding: 6px; font-weight: bold;")
        self.search_box.textChanged.connect(self.filter_chemicals)
        self.combo_filter = QComboBox()
        self.combo_filter.addItems([
            "همه", "اسید", "باز", "نمک", "گاز", "جامد", "مایع",
            "اسید قوی", "باز قوی", "رسوب", "اکسید", "عنصر"
        ])
        self.combo_filter.setMinimumHeight(32)
        self.combo_filter.currentTextChanged.connect(lambda _: self.filter_chemicals(self.search_box.text()))
        h_search.addWidget(self.search_box, 2)
        h_search.addWidget(self.combo_filter, 1)

        self.combo_chem = QComboBox()
        self.combo_chem.setMinimumHeight(34)
        self.combo_chem.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.combo_chem.setStyleSheet("""
            QComboBox {
                background-color: #160f22; color: #c4b5fd; border: 1px solid #3d2a55;
                border-radius: 8px; padding: 6px; font-weight: bold; min-height: 30px;
            }
            QComboBox QAbstractItemView {
                background-color: #160f22; color: #c4b5fd;
                selection-background-color: #3d2a55; outline: 0;
            }
            QComboBox QAbstractItemView::item {
                min-height: 28px; padding: 6px;
            }
        """)
        self.populate_chemicals()
        self.combo_chem.currentIndexChanged.connect(self.update_chem_details)
        self.combo_chem.setToolTip("ماده را انتخاب کنید؛ افزودن یا Drag & Drop")

        self.spin_vol = QDoubleSpinBox()
        self.spin_vol.setRange(0.1, 500)
        self.spin_vol.setValue(50)
        self.spin_vol.setSuffix(" mL/g")
        self.spin_vol.setMinimumHeight(30)
        self.spin_molarity = QDoubleSpinBox()
        self.spin_molarity.setRange(0.01, 20.0)
        self.spin_molarity.setValue(0.1)
        self.spin_molarity.setSingleStep(0.1)
        self.spin_molarity.setMinimumHeight(30)

        h_vol = QHBoxLayout()
        h_vol.addWidget(QLabel("مقدار:"))
        h_vol.addWidget(self.spin_vol)
        h_vol.addWidget(QLabel("M:"))
        h_vol.addWidget(self.spin_molarity)

        h_btn = QHBoxLayout()
        h_btn.setSpacing(8)
        btn_add = QPushButton("➕ افزودن")
        btn_add.setFixedHeight(34)
        btn_add.clicked.connect(self.action_add)
        btn_add.setStyleSheet("background-color: #c4b5fd; color: #160f22; font-weight: bold; border-radius: 8px; font-size: 13px;")
        btn_drag = QPushButton("🖐️ کشیدن")
        btn_drag.setFixedHeight(34)
        btn_drag.setToolTip("بزنید و روی ظرف رها کنید")
        btn_drag.setStyleSheet("background-color: #f9e2af; color: #160f22; font-weight: bold; border-radius: 8px; font-size: 13px;")
        btn_drag.clicked.connect(self.start_chem_drag)
        self.btn_titrate = QPushButton("💧 بورت")
        self.btn_titrate.setFixedHeight(34)
        self.btn_titrate.setCheckable(True)
        self.btn_titrate.clicked.connect(self.action_toggle_titration)
        self.btn_titrate.setStyleSheet("background-color: #89b4fa; color: #160f22; font-weight: bold; border-radius: 8px; font-size: 13px;")
        h_btn.addWidget(btn_add)
        h_btn.addWidget(btn_drag)
        h_btn.addWidget(self.btn_titrate)
        DimensionController.lock_row_buttons([btn_add, btn_drag, self.btn_titrate], h=34, min_w=88)

        h_btn2 = QHBoxLayout()
        h_btn2.setSpacing(8)
        self.btn_mol3d = QToolButton()
        self.btn_mol3d.setText("🧬 نمایش ۳بعدی ▾")
        self.btn_mol3d.setFixedHeight(34)
        self.btn_mol3d.setPopupMode(QToolButton.InstantPopup)
        self.btn_mol3d.setCursor(Qt.PointingHandCursor)
        self.btn_mol3d.setToolTip("ساختار سه‌بعدی ماده یا مخلوط")
        self.btn_mol3d.setStyleSheet(
            "QToolButton { background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #a6e3a1, stop:1 #a6e3a1);"
            "color: #0c0914; font-weight: bold; border-radius: 9px; font-size: 12px; border: 1px solid #a6e3a1; padding: 6px 10px; }"
            "QToolButton:hover { border: 2px solid #a6e3a1; }"
            "QToolButton::menu-indicator { image: none; width: 0; }")
        mol_menu = QMenu(self.btn_mol3d)
        mol_menu.addAction("🧬 مدل مولکولی ماده", self.show_selected_molecule_3d)
        mol_menu.addAction("🧪 اولین لایهٔ مخلوط ظرف", self.show_mixture_molecule_3d)
        self.btn_mol3d.setMenu(mol_menu)
        self.btn_mix3d = self.btn_mol3d  # سازگاری با کدهای قدیمی
        h_btn2.addWidget(self.btn_mol3d, 1)

        self.spin_drop_rate = QDoubleSpinBox()
        self.spin_drop_rate.setRange(0.1, 10.0)
        self.spin_drop_rate.setValue(1.0)
        self.spin_drop_rate.setPrefix("قطره: ")
        self.spin_drop_rate.setMinimumHeight(28)

        frm.addRow(h_search)
        frm.addRow("ماده:", self.combo_chem)
        frm.addRow(h_vol)
        frm.addRow(self.spin_drop_rate)
        frm.addRow(h_btn)
        frm.addRow(h_btn2)
        gb_chem.setLayout(frm)
        vbox.addWidget(gb_chem)

        gb_tools = QGroupBox("دما و سرعت")
        v_tools = QVBoxLayout(gb_tools)
        v_tools.setSpacing(8)
        h_temp = QHBoxLayout()
        btn_cool = QPushButton("🧊 −۵°")
        btn_heat = QPushButton("🔥 +۵°")
        btn_cool.setMinimumHeight(34)
        btn_heat.setMinimumHeight(34)
        btn_cool.clicked.connect(self.action_cool)
        btn_heat.clicked.connect(self.action_heat)
        btn_cool.setStyleSheet("background-color: #89b4fa; color: #160f22; font-weight: bold; border-radius: 8px;")
        btn_heat.setStyleSheet("background-color: #f38ba8; color: #160f22; font-weight: bold; border-radius: 8px;")
        h_temp.addWidget(btn_cool)
        h_temp.addWidget(btn_heat)
        v_tools.addLayout(h_temp)
        h_sp = QHBoxLayout()
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(0, 50)
        self.speed_slider.setValue(10)
        self.lbl_speed_val = QLabel("×1.0")
        DimensionController.lock(self.lbl_speed_val, w=44, h=28)
        self.lbl_speed_val.setStyleSheet("color: #c4b5fd; font-weight: bold;")
        def on_speed_slider(v):
            sp = v / 10.0
            self.set_speed(sp)
            self.lbl_speed_val.setText(f"×{sp:.1f}")
        self.speed_slider.valueChanged.connect(on_speed_slider)
        h_sp.addWidget(QLabel("سرعت"))
        h_sp.addWidget(self.speed_slider, 1)
        h_sp.addWidget(self.lbl_speed_val)
        v_tools.addLayout(h_sp)
        vbox.addWidget(gb_tools)

        self.gb_details = self._create_details_group()
        vbox.addWidget(self.gb_details)

        status_row = QHBoxLayout()
        self.lbl_stirrer_status = QLabel("همزن: خاموش")
        self.lbl_stirrer_status.setStyleSheet("color: #c4b5fd; font-weight: bold; font-size: 12px;")
        self.lbl_titration_status = QLabel("")
        self.lbl_titration_status.setStyleSheet("color: #89b4fa; font-weight: bold; font-size: 12px;")
        status_row.addWidget(self.lbl_stirrer_status)
        status_row.addWidget(self.lbl_titration_status)
        vbox.addLayout(status_row)

        self.lbl_active_mission = QLabel("🎯 مأموریت: —")
        self.lbl_active_mission.setStyleSheet(
            "background-color: #160f22; border: 1px solid #3d2a55; border-radius: 8px; "
            "padding: 6px; color: #f9e2af; font-size: 11px;")
        self.lbl_active_mission.setWordWrap(True)
        vbox.addWidget(self.lbl_active_mission)

        self.lbl_suggested_rxn = QLabel("💡 پیشنهاد: —")
        self.lbl_suggested_rxn.setStyleSheet(
            "background-color: #1a1a28; border: 1px solid #3d2a55; border-radius: 8px; "
            "padding: 6px; color: #c4b5fd; font-size: 11px;")
        self.lbl_suggested_rxn.setWordWrap(True)
        vbox.addWidget(self.lbl_suggested_rxn)

        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setMinimumHeight(100)
        self.txt_log.setMaximumHeight(160)
        self.txt_log.setStyleSheet(
            "QTextEdit { background-color: #100a18; color: #c4b5fd; font-size: 12px; "
            "border: 1px solid #3d2a55; border-radius: 8px; padding: 4px; }")
        vbox.addWidget(QLabel("📜 گزارش زنده:"))
        vbox.addWidget(self.txt_log)

        self.lbl_welcome = QLabel("")
        self.lbl_level = QLabel("سطح: 1")
        self.lbl_score = QLabel("امتیاز: 0")
        self.progress_xp = QProgressBar()
        self.progress_xp.setRange(0, 100)
        for w in (self.lbl_welcome, self.lbl_level, self.lbl_score, self.progress_xp):
            w.setVisible(False)

        vbox.addStretch(1)
        scroll.setWidget(panel)
        outer_lay.addWidget(scroll)
        return outer

    def open_profile_dialog(self):
        """پروفایل شیمیدان در پنجره جدا — دیگر پنل چپ را شلوغ نمی‌کند."""
        dlg = QDialog(self)
        dlg.setWindowTitle("👤 پروفایل شیمیدان")
        dlg.setMinimumWidth(380)
        dlg.setStyleSheet(
            "QDialog { background: #12081f; } QLabel { color: #e8e0f5; }"
            "QPushButton { background: #5b21b6; color: #fff; font-weight: bold; "
            "padding: 8px 14px; border-radius: 8px; }"
        )
        lay = QVBoxLayout(dlg)
        lay.setSpacing(12)
        name = getattr(self.engine, "player_name", "دانشجو")
        title = QLabel(f"👤 {name}")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #c4b5fd;")
        title.setAlignment(Qt.AlignCenter)
        lay.addWidget(title)
        self._dlg_lbl_level = QLabel(f"سطح: {self.engine.level}")
        self._dlg_lbl_score = QLabel(f"امتیاز: {self.engine.score}")
        self._dlg_lbl_level.setStyleSheet("color: #fab387; font-size: 14px; font-weight: bold;")
        self._dlg_lbl_score.setStyleSheet("color: #c4b5fd; font-size: 14px; font-weight: bold;")
        lay.addWidget(self._dlg_lbl_level)
        lay.addWidget(self._dlg_lbl_score)
        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(int(self.engine.score) % 100)
        lay.addWidget(QLabel("پیشرفت تا سطح بعدی:"))
        lay.addWidget(bar)
        h = QHBoxLayout()
        btn_save = QPushButton("💾 ذخیره فایل")
        btn_load = QPushButton("📂 بارگذاری فایل")
        btn_save.clicked.connect(self.action_save_state_file)
        btn_load.clicked.connect(self.action_load_state_file)
        h.addWidget(btn_save)
        h.addWidget(btn_load)
        lay.addLayout(h)
        btn_ok = QPushButton("بستن")
        btn_ok.clicked.connect(dlg.accept)
        lay.addWidget(btn_ok)
        dlg.exec()

    def _create_bottom_toolbar(self, parent_layout=None):
        """نوار ابزار مینیمال؛ فقط وضعیت و سه عمل پرتکرار، بقیه داخل منوی ابزارها."""
        toolbar = QFrame(); toolbar.setObjectName("bottomToolbar"); toolbar.setFixedHeight(58)
        lay = QHBoxLayout(toolbar); lay.setContentsMargins(14,10,14,10); lay.setSpacing(12)
        def quick(text, slot, checkable=False):
            b=QPushButton(text); b.setFixedHeight(38); b.setCheckable(checkable); b.clicked.connect(slot); return b
        self.btn_stirrer = quick("🌪 همزن", self.action_toggle_stirrer, True); lay.addWidget(self.btn_stirrer)
        lay.addWidget(quick("🔥 گرما", self.action_heat)); lay.addWidget(quick("🧊 سرما", self.action_cool))
        lay.addStretch(1)
        tools=QToolButton(); tools.setText("🧰 ابزارها ▾"); tools.setPopupMode(QToolButton.InstantPopup); tools.setFixedHeight(34)
        menu=QMenu(tools)
        menu.addAction("⚗️ فیلتر", self.action_filter); menu.addAction("🚿 شستشو", self.action_wash)
        menu.addSeparator(); menu.addAction("💧 تیتراسیون", self._menu_toggle_titration); menu.addAction("🧬 مولکول ۳بعدی", self.show_selected_molecule_3d); menu.addAction("🧪 ۳بعدی مخلوط", self.show_mixture_molecule_3d)
        menu.addSeparator(); menu.addAction("📸 عکس", self.action_screenshot); menu.addAction("💾 ذخیره", self.action_save_state_file); menu.addAction("📂 بارگذاری", self.action_load_state_file)
        menu.addSeparator(); menu.addAction("⚙️ تنظیمات", self.open_settings_panel); menu.addAction("❓ راهنما", self.show_tutorial)
        tools.setMenu(menu); lay.addWidget(tools)
        if parent_layout is not None: parent_layout.addWidget(toolbar,0)
        self._bottom_toolbar_ref=toolbar; toolbar.show()

    def show_3d_beaker(self):
        """نمایش مستقل بشر سه‌بعدی؛ در نبود PyOpenGL از fallback matplotlib استفاده می‌شود."""
        dlg=QDialog(self); dlg.setWindowTitle("بشر سه‌بعدی"); dlg.resize(620,700)
        layout=QVBoxLayout(dlg)
        try:
            view = GLBeakerCanvas(self.engine, dlg) if HAS_OPENGL else None
            if hasattr(view, "set_stirrer"):
                view.set_stirrer(bool(getattr(getattr(self, "container", None), "stirrer_on", False)))
            layout.addWidget(view,1)
            tip=QLabel("نمای سه‌بعدی آفلاین · Drag ماوس برای چرخش · همزن برای انیمیشن")
            tip.setAlignment(Qt.AlignCenter); layout.addWidget(tip)
            btn=QPushButton("بستن"); btn.clicked.connect(dlg.accept); layout.addWidget(btn); dlg.exec()
        except Exception as e:
            QMessageBox.warning(self,"خطای نمای سه‌بعدی",f"ساخت نمای سه‌بعدی ممکن نشد:\n{e}")

    def _create_center_panel(self):
        panel = QFrame()
        panel.setObjectName("panel")
        v_vis = QVBoxLayout(panel)
        v_vis.setContentsMargins(8, 8, 8, 8)
        v_vis.setSpacing(6)

        h_title = QHBoxLayout()
        title = QLabel("ظرف واکنش (1000 mL)")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            "font-size: 16px; color: #89dceb; font-weight: bold; padding: 6px;")
        h_title.addWidget(title, 1)
        self.btn_toggle_beaker_view = QPushButton("۳بعدی")
        DimensionController.lock_btn(self.btn_toggle_beaker_view, w=100, h=34)
        self.btn_toggle_beaker_view.setStyleSheet(
            "background-color: #c4b5fd; color: #160f22; font-weight: bold; border-radius: 8px; font-size: 13px;")
        self.btn_toggle_beaker_view.clicked.connect(self.toggle_beaker_view)
        h_title.addWidget(self.btn_toggle_beaker_view, 0)
        v_vis.addLayout(h_title)

        self.container = AnimatedContainer(self.engine)
        self.container.setAcceptDrops(True)

        self.beaker_area = QWidget()
        self.beaker_area.setMinimumHeight(360)
        self.beaker_stack = QStackedLayout(self.beaker_area)
        self.beaker_stack.setContentsMargins(0, 0, 0, 0)

        beaker_holder_2d = QWidget()
        hold_lay = QVBoxLayout(beaker_holder_2d)
        hold_lay.setContentsMargins(0, 0, 0, 0)
        hold_lay.addStretch(1)
        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(self.container, 0, Qt.AlignCenter)
        row.addStretch(1)
        hold_lay.addLayout(row)
        hold_lay.addStretch(1)
        self.beaker_stack.addWidget(beaker_holder_2d)

        # نمای سه‌بعدی بشر با OpenGL
        try:
            self.gl_beaker = GLBeakerCanvas(self.engine) if HAS_OPENGL else None
        except Exception as e:
            print(f"[WARN] ساخت بشر ۳بعدی: {e}", flush=True)
            try:
                self.gl_beaker = GLBeakerCanvas(self.engine) if HAS_OPENGL else None
            except Exception as e2:
                print(f"[WARN] fallback: {e2}", flush=True)
                self.gl_beaker = None
        if self.gl_beaker is not None:
            self.gl_beaker.setMinimumSize(320, 400)
            self.beaker_stack.addWidget(self.gl_beaker)
        else:
            placeholder = QLabel("نمای ۳بعدی در دسترس نیست")
            placeholder.setAlignment(Qt.AlignCenter)
            self.beaker_stack.addWidget(placeholder)
        self.beaker_stack.setCurrentIndex(0)
        self._beaker_is_3d = False
        v_vis.addWidget(self.beaker_area, 1)

        info_frame = QFrame()
        info_frame.setStyleSheet(
            "background-color: #160f22; border-radius: 10px; border: 1px solid #3d2a55;")
        info_frame.setMinimumHeight(44)
        info_frame.setMaximumHeight(52)
        info_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        info_h = QHBoxLayout(info_frame)
        info_h.setContentsMargins(14, 8, 14, 8)
        info_h.setSpacing(16)
        self.lbl_ph_display = QLabel("pH: 7.00")
        self.lbl_ph_display.setStyleSheet("font-size: 16px; color: #c4b5fd; font-weight: bold;")
        self.lbl_ph_display.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self.lbl_temp_display = QLabel("25.0 °C")
        self.lbl_temp_display.setStyleSheet("font-size: 16px; color: #f38ba8; font-weight: bold;")
        self.lbl_temp_display.setAlignment(Qt.AlignVCenter | Qt.AlignRight)
        self.lbl_stirrer_3d = QLabel("")
        self.lbl_stirrer_3d.setStyleSheet("font-size: 13px; color: #c4b5fd; font-weight: bold;")
        self.lbl_stirrer_3d.setAlignment(Qt.AlignVCenter | Qt.AlignHCenter)
        info_h.addWidget(self.lbl_ph_display, 1)
        info_h.addWidget(self.lbl_stirrer_3d, 0)
        info_h.addWidget(self.lbl_temp_display, 1)
        v_vis.addWidget(info_frame)
        return panel

    def toggle_beaker_view(self):
        tlog("toggle_beaker_view", "CLICK", is_3d=getattr(self, "_beaker_is_3d", None))
        if self.gl_beaker is None:
            tlog("ویجت سه‌بعدی بشر ساخته نشد", "WARN")
            return
        sizes = self.main_splitter.sizes() if hasattr(self, 'main_splitter') else None
        self._beaker_is_3d = not self._beaker_is_3d
        if self._beaker_is_3d:
            self.beaker_stack.setCurrentIndex(1)
            self.btn_toggle_beaker_view.setText("۲بعدی")
            self.gl_beaker.show()
            self.gl_beaker.raise_()
            try:
                self.gl_beaker.makeCurrent()
            except Exception:
                pass
            setattr(self.gl_beaker, "_needs_redraw", True)
            if hasattr(self.gl_beaker, "set_stirrer"):
                self.gl_beaker.set_stirrer(bool(getattr(self.container, "stirrer_on", False)))
            if hasattr(self.gl_beaker, "redraw"):
                self.gl_beaker.redraw()
            else:
                self.gl_beaker.update()
            if hasattr(self.gl_beaker, "_stirrer_timer") and not self.gl_beaker._stirrer_timer.isActive():
                self.gl_beaker._stirrer_timer.start(80)
            # به‌روزرسانی پس از نمایش در stack برای پایداری رندر
            QTimer.singleShot(50, lambda: self.gl_beaker.update() if self.gl_beaker else None)
            QTimer.singleShot(200, lambda: self.gl_beaker.update() if self.gl_beaker else None)
        else:
            self.beaker_stack.setCurrentIndex(0)
            self.btn_toggle_beaker_view.setText("۳بعدی")
            if hasattr(self.gl_beaker, "set_stirrer"):
                self.gl_beaker.set_stirrer(False)
            if hasattr(self.gl_beaker, "_stirrer_timer") and self.gl_beaker._stirrer_timer.isActive():
                self.gl_beaker._stirrer_timer.stop()
        DimensionController.lock_btn(self.btn_toggle_beaker_view, w=100, h=34)
        if sizes:
            self.main_splitter.setSizes(sizes)
        DimensionController.preserve_splitter(getattr(self, 'main_splitter', None))
        DimensionController.reapply_all()

    def _create_all_tabs(self):
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setUsesScrollButtons(True)
        self.tabs.tabBar().setExpanding(False)
        self.tabs.tabBar().setElideMode(Qt.ElideNone)  # نمایش کامل نام تب — نه نقطه
        self.tabs.tabBar().setUsesScrollButtons(True)
        try:
            self.tabs.tabBar().setMovable(False)
        except Exception:
            pass
        self.tabs.currentChanged.connect(self._on_graph_tab_changed)
        self.tabs.setStyleSheet(
            "QTabWidget::pane { background: #140f20; border: 1px solid #6d28d9; border-radius: 12px; }"
            "QTabBar::tab {"
            "  background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #2a1e3d, stop:1 #1a1228);"
            "  color: #e9d5ff; padding: 8px 14px; margin-right: 3px;"
            "  border-top-left-radius: 10px; border-top-right-radius: 10px;"
            "  border: 1px solid #4c1d95; border-bottom: none;"
            "  font-size: 12px; font-weight: bold; min-width: 72px; min-height: 26px;"
            "}"
            "QTabBar::tab:selected {"
            "  background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #7c3aed, stop:1 #e879f9);"
            "  color: #0c0914; border: 1px solid #f0abfc;"
            "}"
            "QTabBar::tab:hover:!selected { background: #3b0764; color: #f5d0fe; }"
            "QTabBar::scroller { width: 28px; }"
            "QTabBar QToolButton {"
            "  background: #3b0764; color: #f5d0fe; border: 1px solid #a78bfa;"
            "  border-radius: 6px; padding: 2px; font-weight: bold;"
            "}"
            "QTabBar QToolButton:hover { background: #7c3aed; color: white; }"
        )
        if self.is_admin:
            self.tabs.addTab(self.create_admin_dashboard_tab(), "🛡️ داشبورد مدیر")
            self.tabs.addTab(self.create_admin_db_tab(), "🗄️ مدیریت مواد")
            self.tabs.addTab(self.create_admin_reactions_tab(), "⚗️ مدیریت واکنش‌ها")
            self.tabs.addTab(self.create_admin_security_tab(), "🔐 امنیت و رمز")
            self.tabs.addTab(self.create_about_tab(), "ℹ️ درباره")
        else:
            self.tabs.addTab(self.create_about_tab(), "ℹ️ درباره")
            self.tabs.addTab(self.create_report_card_tab(), "📊 کارنامه")
            self.tabs.addTab(self.create_missions_badges_tab(), "🏅 مدال‌ها")
            self.tabs.addTab(self.create_notes_tab(), "📝 گزارش")
            self.tabs.addTab(self.create_contents_tab(), "🧪 محتویات")
            self.graph_tab_widget = self.create_graph_tab()
            self.tabs.addTab(self.graph_tab_widget, "📈 نمودار")
            self.tabs.addTab(self.create_discoveries_tab(), "🏆 کشف‌ها")
            self.tabs.addTab(self.create_wiki_tab(), "📖 دانشنامه")
            self.tabs.addTab(self.create_datasheet_tab(), "📚 مواد")
            self.tabs.addTab(BohrModelWidget(), "⚛️ مدل بور")
            # نوار جابه‌جایی تب (جدا از corner تا در RTL خراب نشود)
            try:
                self._tab_nav_bar = QWidget()
                ch = QHBoxLayout(self._tab_nav_bar)
                ch.setContentsMargins(4, 2, 4, 2)
                ch.setSpacing(4)
                ch.addStretch(1)
                for label, tip, slot in (
                    ("⏮ اول", "اولین تب", self._tab_go_first),
                    ("◀ قبلی", "تب قبلی", self._tab_go_prev),
                    ("▶ بعدی", "تب بعدی", self._tab_go_next),
                    ("آخر ⏭", "آخرین تب", self._tab_go_last),
                ):
                    b = QPushButton(label)
                    b.setFixedHeight(26)
                    b.setToolTip(tip)
                    b.setStyleSheet(
                        "QPushButton{background:#3b0764;color:#f5d0fe;border:1px solid #a78bfa;"
                        "border-radius:8px;font-weight:bold;font-size:11px;padding:2px 8px;}"
                        "QPushButton:hover{background:#7c3aed;color:white;}"
                    )
                    b.clicked.connect(slot)
                    ch.addWidget(b)
                # بعداً در layout کنار tabs قرار می‌گیرد
            except Exception as e:
                print(f"[WARN] tab nav: {e}", flush=True)
                self._tab_nav_bar = None
        return self.tabs

    def create_admin_dashboard_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(14)
        title = QLabel("🛡️ داشبورد مدیریت دیتابیس")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #c4b5fd; margin: 8px;")
        lay.addWidget(title)
        lock_txt = "🔓 باز — امکان ویرایش" if DB_WRITE_UNLOCKED else "🔒 قفل — فقط مشاهده"
        info = QLabel(
            f"<b>وضعیت قفل نوشتن:</b> {lock_txt}<br>"
            f"<b>مواد در حافظه:</b> {len(CHEMILAB_DB)}<br>"
            f"<b>واکنش‌ها در حافظه:</b> {len(CUSTOM_REACTIONS)}<br>"
            f"<b>مسیر دیتابیس:</b> {get_db_path()}<br>"
            f"<b>فایل رمز:</b> {get_admin_auth_path()}<br><br>"
            "از تب‌های مدیریت مواد و واکنش‌ها برای افزودن/ویرایش/حذف استفاده کنید.<br>"
            "تغییرات پس از «ذخیره در دیتابیس» روی فایل db.db نوشته می‌شوند."
        )
        info.setStyleSheet(
            "font-size: 13px; color: #e8e0f5; background: #1a1228;"
            "border: 1px solid #5b3d7a; border-radius: 12px; padding: 16px;")
        info.setWordWrap(True)
        info.setTextFormat(Qt.RichText)
        self._admin_dash_info = info
        lay.addWidget(info)
        row = QHBoxLayout()
        btn_reload = QPushButton("🔄 بارگذاری مجدد از فایل")
        btn_reload.clicked.connect(self.admin_reload_db)
        btn_save_all = QPushButton("💾 ذخیره همه در دیتابیس")
        btn_save_all.clicked.connect(self.admin_save_all_db)
        for b in (btn_reload, btn_save_all):
            b.setStyleSheet(
                "background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #7c3aed, stop:1 #a78bfa);"
                "color: #0c0914; font-weight: bold; padding: 10px; border-radius: 10px;")
            row.addWidget(b)
        lay.addLayout(row)
        lay.addStretch()
        return w

    def create_admin_db_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.addWidget(QLabel("🗄️ مدیریت مواد شیمیایی (افزودن / ویرایش / حذف)"))
        self.admin_chem_table = QTableWidget()
        self.admin_chem_table.setColumnCount(10)
        self.admin_chem_table.setHorizontalHeaderLabels(
            ["کلید", "نام", "فرمول", "کد SMILES", "نوع", "حالت", "درجه خطر", "pH", "مولاریته", "رنگ"])
        self.admin_chem_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.admin_chem_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.admin_chem_table.setEditTriggers(QTableWidget.NoEditTriggers)
        lay.addWidget(self.admin_chem_table, 1)
        self._refresh_admin_chem_table()

        form = QFormLayout()
        self.adm_c_key = QLineEdit(); self.adm_c_key.setPlaceholderText("مثلاً nacl")
        self.adm_c_name = QLineEdit(); self.adm_c_name.setPlaceholderText("نام فارسی")
        self.adm_c_form = QLineEdit(); self.adm_c_form.setPlaceholderText("NaCl")
        self.adm_c_smiles = QLineEdit(); self.adm_c_smiles.setPlaceholderText("SMILES؛ مثلاً CCO")
        self.adm_c_type = QLineEdit(); self.adm_c_type.setPlaceholderText("Salt / Strong Acid / …")
        self.adm_c_ph = QDoubleSpinBox(); self.adm_c_ph.setRange(0, 14); self.adm_c_ph.setValue(7)
        self.adm_c_mol = QDoubleSpinBox(); self.adm_c_mol.setRange(0, 50); self.adm_c_mol.setDecimals(3); self.adm_c_mol.setValue(0.1)
        self.adm_c_color = QLineEdit(); self.adm_c_color.setText("#FFFFFF")
        self.adm_c_heat = QDoubleSpinBox(); self.adm_c_heat.setRange(-5000, 5000); self.adm_c_heat.setDecimals(2)
        self.adm_c_state = QComboBox()
        self.adm_c_state.addItems(["جامد", "مایع", "گاز", "پلاسما"])
        self.adm_c_hazard = QLineEdit()
        self.adm_c_hazard.setPlaceholderText("مثلاً خورنده — اسید قوی")
        form.addRow("کلید (fa_name):", self.adm_c_key)
        form.addRow("نام:", self.adm_c_name)
        form.addRow("فرمول:", self.adm_c_form)
        form.addRow("کد مولکولی (SMILES):", self.adm_c_smiles)
        form.addRow("نوع:", self.adm_c_type)
        form.addRow("حالت فیزیکی:", self.adm_c_state)
        form.addRow("درجه خطر:", self.adm_c_hazard)
        form.addRow("pH:", self.adm_c_ph)
        form.addRow("مولاریته:", self.adm_c_mol)
        form.addRow("گرما (kJ):", self.adm_c_heat)
        form.addRow("رنگ (#hex):", self.adm_c_color)
        lay.addLayout(form)

        self.admin_chem_table.itemSelectionChanged.connect(self._admin_chem_fill_form)
        btns = QHBoxLayout()
        b_add = QPushButton("➕ افزودن / به‌روزرسانی")
        b_del = QPushButton("🗑️ حذف انتخاب‌شده")
        b_save = QPushButton("💾 ذخیره مواد در DB")
        b_add.clicked.connect(self.admin_chem_upsert)
        b_del.clicked.connect(self.admin_chem_delete)
        b_save.clicked.connect(self.admin_save_chems)
        for b in (b_add, b_del, b_save):
            b.setStyleSheet("font-weight: bold; padding: 8px 12px; border-radius: 8px;")
            btns.addWidget(b)
        lay.addLayout(btns)
        return w

    def create_admin_reactions_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.addWidget(QLabel("⚗️ مدیریت واکنش‌ها (افزودن / ویرایش / حذف)"))
        self.admin_rxn_table = QTableWidget()
        self.admin_rxn_table.setColumnCount(5)
        self.admin_rxn_table.setHorizontalHeaderLabels(
            ["نام", "واکنش‌دهنده‌ها", "محصولات", "XP", "دمای حداقل"])
        self.admin_rxn_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.admin_rxn_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.admin_rxn_table.setEditTriggers(QTableWidget.NoEditTriggers)
        lay.addWidget(self.admin_rxn_table, 1)
        self._refresh_admin_rxn_table()

        form = QFormLayout()
        self.adm_r_name = QLineEdit(); self.adm_r_name.setPlaceholderText("نام فارسی واکنش")
        self.adm_r_react = QLineEdit(); self.adm_r_react.setPlaceholderText("hcl, naoh")
        self.adm_r_prod = QLineEdit(); self.adm_r_prod.setPlaceholderText("nacl, h2o")
        self.adm_r_desc = QLineEdit(); self.adm_r_desc.setPlaceholderText("توضیح کوتاه")
        self.adm_r_xp = QSpinBox(); self.adm_r_xp.setRange(0, 9999); self.adm_r_xp.setValue(50)
        self.adm_r_temp = QDoubleSpinBox(); self.adm_r_temp.setRange(-273, 2000); self.adm_r_temp.setValue(0)
        form.addRow("نام واکنش:", self.adm_r_name)
        form.addRow("واکنش‌دهنده‌ها (با کاما):", self.adm_r_react)
        form.addRow("محصولات (با کاما):", self.adm_r_prod)
        form.addRow("توضیح:", self.adm_r_desc)
        form.addRow("XP:", self.adm_r_xp)
        form.addRow("دمای حداقل °C:", self.adm_r_temp)
        lay.addLayout(form)

        self.admin_rxn_table.itemSelectionChanged.connect(self._admin_rxn_fill_form)
        btns = QHBoxLayout()
        b_add = QPushButton("➕ افزودن / به‌روزرسانی")
        b_del = QPushButton("🗑️ حذف انتخاب‌شده")
        b_save = QPushButton("💾 ذخیره واکنش‌ها در DB")
        b_add.clicked.connect(self.admin_rxn_upsert)
        b_del.clicked.connect(self.admin_rxn_delete)
        b_save.clicked.connect(self.admin_save_rxns)
        for b in (b_add, b_del, b_save):
            b.setStyleSheet("font-weight: bold; padding: 8px 12px; border-radius: 8px;")
            btns.addWidget(b)
        lay.addLayout(btns)
        return w

    def create_admin_security_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        title = QLabel("🔐 امنیت دیتابیس")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #f9e2af;")
        lay.addWidget(title)
        status = "رمز تعیین شده است" if AdminAuth.is_password_set() else "رمز هنوز تعیین نشده"
        lay.addWidget(QLabel(f"وضعیت: {status}"))
        form = QFormLayout()
        self.adm_old_pass = QLineEdit(); self.adm_old_pass.setEchoMode(QLineEdit.Password)
        self.adm_new_pass = QLineEdit(); self.adm_new_pass.setEchoMode(QLineEdit.Password)
        self.adm_new_pass2 = QLineEdit(); self.adm_new_pass2.setEchoMode(QLineEdit.Password)
        form.addRow("رمز فعلی:", self.adm_old_pass)
        form.addRow("رمز جدید:", self.adm_new_pass)
        form.addRow("تکرار رمز جدید:", self.adm_new_pass2)
        lay.addLayout(form)
        btn = QPushButton("🔑 تغییر رمز")
        btn.setStyleSheet(
            "background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #e879f9, stop:1 #a78bfa);"
            "color: #0c0914; font-weight: bold; padding: 10px; border-radius: 10px;")
        btn.clicked.connect(self.admin_change_password)
        lay.addWidget(btn)
        tip = QLabel(
            "• رمز با الگوریتم PBKDF2-SHA256 ذخیره می‌شود (نه متن خام).\n"
            "• بدون رمز صحیح، ذخیره روی db.db ممکن نیست.\n"
            "• فایل admin_auth.json را محرمانه نگه دارید."
        )
        tip.setStyleSheet("color: #a6adc8; padding: 10px;")
        tip.setWordWrap(True)
        lay.addWidget(tip)
        lay.addStretch()
        return w

    def _refresh_admin_chem_table(self):
        if not hasattr(self, "admin_chem_table"):
            return
        items = sorted(CHEMILAB_DB.items(), key=lambda x: x[1].get("name", ""))
        self.admin_chem_table.setRowCount(len(items))
        for i, (k, d) in enumerate(items):
            vals = [k, d.get("name", ""), d.get("formula", ""), d.get("smiles", ""),
                    d.get("type", ""), d.get("state", "جامد"), d.get("hazard", "کم‌خطر"),
                    str(d.get("pH", "")), str(d.get("molarity", "")), d.get("color", "")]
            for c, v in enumerate(vals):
                self.admin_chem_table.setItem(i, c, QTableWidgetItem(str(v)))

    def _refresh_admin_rxn_table(self):
        if not hasattr(self, "admin_rxn_table"):
            return
        items = sorted(CUSTOM_REACTIONS.items(), key=lambda x: x[0])
        self.admin_rxn_table.setRowCount(len(items))
        for i, (name, rxn) in enumerate(items):
            vals = [
                name,
                ", ".join(rxn.get("reactants", [])),
                ", ".join(rxn.get("products", [])),
                str(rxn.get("xp", 0)),
                str(rxn.get("temp_min", -273)),
            ]
            for c, v in enumerate(vals):
                self.admin_rxn_table.setItem(i, c, QTableWidgetItem(str(v)))

    def _admin_chem_fill_form(self):
        rows = self.admin_chem_table.selectionModel().selectedRows()
        if not rows:
            return
        r = rows[0].row()
        key = self.admin_chem_table.item(r, 0).text()
        d = CHEMILAB_DB.get(key, {})
        self.adm_c_key.setText(key)
        self.adm_c_name.setText(str(d.get("name", "")))
        self.adm_c_form.setText(str(d.get("formula", "")))
        self.adm_c_smiles.setText(str(d.get("smiles", "") or ""))
        self.adm_c_type.setText(str(d.get("type", "")))
        self.adm_c_ph.setValue(float(d.get("pH", 7) or 7))
        self.adm_c_mol.setValue(float(d.get("molarity", 0.1) or 0.1))
        self.adm_c_heat.setValue(float(d.get("heat", 0) or 0))
        self.adm_c_color.setText(str(d.get("color", "#FFFFFF")))
        st = str(d.get("state", "جامد") or "جامد")
        idx = self.adm_c_state.findText(st)
        self.adm_c_state.setCurrentIndex(idx if idx >= 0 else 0)
        if hasattr(self, "adm_c_hazard"):
            self.adm_c_hazard.setText(str(d.get("hazard", "کم‌خطر")))

    def _admin_rxn_fill_form(self):
        rows = self.admin_rxn_table.selectionModel().selectedRows()
        if not rows:
            return
        r = rows[0].row()
        name = self.admin_rxn_table.item(r, 0).text()
        rxn = CUSTOM_REACTIONS.get(name, {})
        self.adm_r_name.setText(name)
        self.adm_r_react.setText(", ".join(rxn.get("reactants", [])))
        self.adm_r_prod.setText(", ".join(rxn.get("products", [])))
        self.adm_r_desc.setText(str(rxn.get("desc", "")))
        self.adm_r_xp.setValue(int(rxn.get("xp", 0) or 0))
        self.adm_r_temp.setValue(float(rxn.get("temp_min") if rxn.get("temp_min") is not None else -273))

    def _require_db_unlock(self):
        if not DB_WRITE_UNLOCKED:
            QMessageBox.warning(self, "قفل دیتابیس",
                                "نشست ادمین قفل است. با رمز صحیح وارد شوید.")
            return False
        return True

    def admin_chem_upsert(self):
        if not self._require_db_unlock():
            return
        key = normalize_key(self.adm_c_key.text().strip())
        if not key:
            QMessageBox.warning(self, "خطا", "کلید ماده الزامی است.")
            return
        ph = float(self.adm_c_ph.value())
        mol = float(self.adm_c_mol.value())
        heat = float(self.adm_c_heat.value())
        if not (0.0 <= ph <= 14.0):
            QMessageBox.warning(self, "اعتبارسنجی", "pH باید بین ۰ تا ۱۴ باشد.")
            return
        if mol < 0 or mol > 100:
            QMessageBox.warning(self, "اعتبارسنجی", "مولاریته باید بین ۰ تا ۱۰۰ باشد.")
            return
        if not (-1e6 <= heat <= 1e6):
            QMessageBox.warning(self, "اعتبارسنجی", "مقدار ΔH نامعتبر است.")
            return
        formula = self.adm_c_form.text().strip() or ""
        smiles = self.adm_c_smiles.text().strip() if hasattr(self, "adm_c_smiles") else ""
        if not smiles:
            smiles = M1_COMMON_FORMULAS.get(_normalize_formula_key(formula), "")
        if not formula:
            QMessageBox.warning(self, "اعتبارسنجی", "فرمول ماده الزامی است.")
            return
        if not ChemicalCalculator.parse_formula(formula):
            QMessageBox.warning(self, "اعتبارسنجی", "فرمول شیمیایی قابل تجزیه نیست.")
            return
        color = self.adm_c_color.text().strip() or "#FFFFFF"
        if not re.match(r'^#?[0-9A-Fa-f]{3,8}$', color.replace(' ', '')):
            QMessageBox.warning(self, "اعتبارسنجی", "رنگ باید کد هگز معتبر باشد (مثل #aaddff).")
            return
        if not color.startswith('#'):
            color = '#' + color
        prev = dict(CHEMILAB_DB.get(key, {}) or {})
        entry = {
            "name": self.adm_c_name.text().strip() or prev.get("name") or key,
            "type": self.adm_c_type.text().strip() or prev.get("type") or "Solid",
            "pH": ph,
            "molarity": mol,
            "heat": heat,
            "color": color,
            "formula": formula or prev.get("formula") or key,
            "smiles": smiles or prev.get("smiles", ""),
            "state": self.adm_c_state.currentText() or prev.get("state") or "جامد",
            "hazard": (self.adm_c_hazard.text().strip() if hasattr(self, "adm_c_hazard") else "")
                      or prev.get("hazard")
                      or "کم‌خطر — احتیاط معمولی",
            # فیلدهایی که در فرم ادمین نیستند نباید نابود شوند
            "density": prev.get("density", 1.0),
            "mp": prev.get("mp"),
            "bp": prev.get("bp"),
        }
        for extra_k, extra_v in prev.items():
            if extra_k not in entry:
                entry[extra_k] = extra_v
        CHEMILAB_DB[key] = entry
        self._refresh_admin_chem_table()
        QMessageBox.information(self, "موفق", f"ماده «{key}» در حافظه ثبت شد.\nبرای ماندگاری «ذخیره در DB» را بزنید.")

    def admin_chem_delete(self):
        if not self._require_db_unlock():
            return
        rows = self.admin_chem_table.selectionModel().selectedRows()
        if not rows:
            return
        key = self.admin_chem_table.item(rows[0].row(), 0).text()
        if key in CHEMILAB_DB:
            del CHEMILAB_DB[key]
            self._refresh_admin_chem_table()
            QMessageBox.information(self, "حذف", f"«{key}» از حافظه حذف شد. ذخیره در DB را فراموش نکنید.")

    def admin_rxn_upsert(self):
        if not self._require_db_unlock():
            return
        name = self.adm_r_name.text().strip()
        if not name:
            QMessageBox.warning(self, "خطا", "نام واکنش الزامی است.")
            return
        reactants = [normalize_key(x) for x in self.adm_r_react.text().split(",") if x.strip()]
        products = [normalize_key(x) for x in self.adm_r_prod.text().split(",") if x.strip()]
        if not reactants or not products:
            QMessageBox.warning(self, "اعتبارسنجی", "حداقل یک واکنش‌دهنده و یک محصول لازم است.")
            return
        xp = int(self.adm_r_xp.value())
        if xp < 0 or xp > 10000:
            QMessageBox.warning(self, "اعتبارسنجی", "XP باید بین ۰ تا ۱۰۰۰۰ باشد.")
            return
        unknown = [r for r in reactants + products if r not in CHEMILAB_DB
                   and not any(normalize_key(v.get('formula','')) == r for v in CHEMILAB_DB.values())]
        if unknown:
            QMessageBox.warning(
                self, "اعتبارسنجی",
                "این کلیدها در کاتالوگ مواد نیستند:\n" + ", ".join(unknown[:12])
                + "\nابتدا ماده را اضافه کنید یا کلید را اصلاح کنید.")
            return
        prev = dict(CUSTOM_REACTIONS.get(name, {}) or {})
        CUSTOM_REACTIONS[name] = {
            "reactants": reactants,
            "products": products,
            "desc": self.adm_r_desc.text().strip() or prev.get("desc", ""),
            "xp": int(self.adm_r_xp.value()),
            "temp_min": float(self.adm_r_temp.value()),
            # فیلدهای خارج از فرم نباید reset شوند
            "dH": prev.get("dH", 0.0),
            "condition": prev.get("condition", ""),
            "coeffs": prev.get("coeffs") or prev.get("stoich") or {},
        }
        self._refresh_admin_rxn_table()
        QMessageBox.information(self, "موفق", f"واکنش «{name}» ثبت شد.")

    def admin_rxn_delete(self):
        if not self._require_db_unlock():
            return
        rows = self.admin_rxn_table.selectionModel().selectedRows()
        if not rows:
            return
        name = self.admin_rxn_table.item(rows[0].row(), 0).text()
        if name in CUSTOM_REACTIONS:
            del CUSTOM_REACTIONS[name]
            self._refresh_admin_rxn_table()

    def admin_save_chems(self):
        ok, msg = save_chemilab_to_db()
        QMessageBox.information(self, "ذخیره مواد", msg) if ok else QMessageBox.critical(self, "خطا", msg)

    def admin_save_rxns(self):
        ok, msg = save_reactions_to_db()
        QMessageBox.information(self, "ذخیره واکنش‌ها", msg) if ok else QMessageBox.critical(self, "خطا", msg)

    def admin_save_all_db(self):
        if not self._require_db_unlock():
            return
        # یک تراکنش منطقی: اگر یکی fail شد، پیام واضح؛ هر save خودش BEGIN/COMMIT دارد
        # برای atomicity کامل‌تر ابتدا reactions سپس chemicals (هر دو backup می‌گیرند)
        ok1, m1 = save_chemilab_to_db()
        if not ok1:
            QMessageBox.critical(self, "خطا", f"ذخیره مواد ناموفق — واکنش‌ها ذخیره نشد.\n{m1}")
            return
        ok2, m2 = save_reactions_to_db()
        if ok1 and ok2:
            QMessageBox.information(self, "ذخیره", f"{m1}\n{m2}")
        else:
            QMessageBox.critical(self, "خطا", f"مواد ذخیره شد اما واکنش‌ها نه:\n{m1}\n{m2}")

    def admin_change_password(self):
        old = self.adm_old_pass.text()
        new = self.adm_new_pass.text()
        new2 = self.adm_new_pass2.text()
        if new != new2:
            QMessageBox.warning(self, "رمز", "تکرار رمز جدید مطابقت ندارد.")
            return
        ok, msg = AdminAuth.change_password(old, new)
        if ok:
            self.adm_old_pass.clear(); self.adm_new_pass.clear(); self.adm_new_pass2.clear()
            QMessageBox.information(self, "رمز", msg)
        else:
            QMessageBox.warning(self, "رمز", msg)

    def admin_reload_db(self):
        try:
            CHEMILAB_DB.clear()
            CUSTOM_REACTIONS.clear()
            load_databases()
            self._refresh_admin_chem_table()
            self._refresh_admin_rxn_table()
            QMessageBox.information(
                self, "مدیر",
                f"بارگذاری شد: {len(CHEMILAB_DB)} ماده، {len(CUSTOM_REACTIONS)} واکنش")
        except Exception as e:
            QMessageBox.critical(self, "خطا", str(e))

    def _create_details_group(self):
        gb = QGroupBox("مشخصات ماده")
        gl = QGridLayout(gb)
        self.lbl_d_name = QLabel("-")
        self.lbl_d_form = QLabel("-")
        self.lbl_d_type = QLabel("-")
        self.lbl_d_state = QLabel("-")
        self.lbl_d_hazard = QLabel("-")
        gl.addWidget(QLabel("نام:"), 0, 0)
        gl.addWidget(self.lbl_d_name, 0, 1)
        gl.addWidget(QLabel("فرمول:"), 1, 0)
        gl.addWidget(self.lbl_d_form, 1, 1)
        gl.addWidget(QLabel("نوع:"), 2, 0)
        gl.addWidget(self.lbl_d_type, 2, 1)
        gl.addWidget(QLabel("حالت:"), 3, 0)
        gl.addWidget(self.lbl_d_state, 3, 1)
        gl.addWidget(QLabel("خطر:"), 4, 0)
        gl.addWidget(self.lbl_d_hazard, 4, 1)
        return gb

    def create_about_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(16)
        title = QLabel(f"🧪 {APP_NAME} {APP_VERSION}")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #c4b5fd;")
        title.setAlignment(Qt.AlignCenter)
        lay.addWidget(title)
        desc = QLabel(
            "شبیه‌ساز آزمایشگاه شیمی برای یادگیری ایمن و تعاملی.\n"
            "مواد را مخلوط کنید، واکنش کشف کنید و پیشرفت خود را ذخیره کنید."
        )
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet(
            "color: #e8e0f5; font-size: 14px; background: #1a1228; border-radius: 12px; "
            "padding: 16px; border: 1px solid #5b3d7a;"
        )
        lay.addWidget(desc)
        r1 = QHBoxLayout()
        r1.addWidget(QLabel("📄 مشاهده سورس و صفحه گیت‌هاب"))
        r1.addStretch()
        btn_gh = QPushButton("صفحه گیت‌هاب")
        btn_gh.setCursor(Qt.PointingHandCursor)
        btn_gh.setStyleSheet(
            "background: #7c3aed; color: #fff; font-weight: bold; padding: 10px 18px; border-radius: 10px;"
        )
        def open_github():
            try:
                from PySide6.QtGui import QDesktopServices
                from PySide6.QtCore import QUrl
                QDesktopServices.openUrl(QUrl("https://github.com/kianfadaee448-alt/ChimiLab"))
            except Exception as e:
                QMessageBox.information(self, "گیت‌هاب", "https://github.com/kianfadaee448-alt/ChimiLab")
        btn_gh.clicked.connect(open_github)
        r1.addWidget(btn_gh)
        lay.addLayout(r1)
        r2 = QHBoxLayout()
        r2.addWidget(QLabel("✉️ ارتباط با سازنده"))
        r2.addStretch()
        btn_mail = QPushButton("ارسال ایمیل")
        btn_mail.setCursor(Qt.PointingHandCursor)
        btn_mail.setStyleSheet(
            "background: #89b4fa; color: #160f22; font-weight: bold; padding: 10px 18px; border-radius: 10px;"
        )
        def open_mail():
            try:
                from PySide6.QtGui import QDesktopServices
                from PySide6.QtCore import QUrl
                QDesktopServices.openUrl(QUrl(f"mailto:{CONTACT_EMAIL}?subject=ChimiLab%20{APP_VERSION}"))
            except Exception:
                QMessageBox.information(self, "ایمیل", "kianfadaee448@gmail.com")
        btn_mail.clicked.connect(open_mail)
        r2.addWidget(btn_mail)
        lay.addLayout(r2)
        foot = QLabel("سازنده: کیان فدایی  •  kianfadaee448@gmail.com")
        foot.setAlignment(Qt.AlignCenter)
        foot.setStyleSheet("color: #6b5b80; font-size: 12px; margin-top: 12px;")
        lay.addWidget(foot)
        lay.addStretch()
        return w



    def create_report_card_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        lbl_title = QLabel("📊 کارنامه و آمار عملکرد شیمیدان")
        lbl_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #89b4fa; margin: 10px;")
        l.addWidget(lbl_title)
        self.lbl_stats = QLabel()
        self.lbl_stats.setStyleSheet(
            "font-size: 16px; line-height: 2.0; padding: 15px; background-color: #160f22; border-radius: 10px;")
        l.addWidget(self.lbl_stats)
        l.addStretch()
        return w

    def create_missions_badges_tab(self):
        w = QWidget()
        w.setStyleSheet("background-color: #100a18;")
        outer = QVBoxLayout(w)
        outer.setContentsMargins(12, 12, 12, 12)
        outer.setSpacing(12)

        header = QFrame()
        header.setStyleSheet(
            "background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #160f22, stop:1 #3d2a55);"
            "border-radius: 14px; border: 1px solid #3d2a55;")
        h_lay = QHBoxLayout(header)
        title = QLabel("🎯 مرکز چالش‌ها و دستاوردها")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #89b4fa; border: none; background: transparent;")
        h_lay.addWidget(title)
        h_lay.addStretch()
        self.lbl_mission_progress = QLabel("")
        self.lbl_mission_progress.setStyleSheet("color: #c4b5fd; font-size: 13px; font-weight: bold; border: none; background: transparent;")
        h_lay.addWidget(self.lbl_mission_progress)
        outer.addWidget(header)

        nav = QHBoxLayout()
        self.btn_show_missions = QPushButton("🎯 نمایش چالش‌ها")
        self.btn_show_missions.setCheckable(True)
        self.btn_show_missions.setChecked(True)
        self.btn_show_missions.setStyleSheet(
            "QPushButton { background-color: #89b4fa; color: #160f22; font-weight: bold; padding: 12px; border-radius: 10px; font-size: 14px; }"
            "QPushButton:checked { background-color: #89b4fa; }"
            "QPushButton:!checked { background-color: #2a2a3a; color: #e8e0f5; }")
        self.btn_show_badges = QPushButton("🏅 نمایش مدال‌ها")
        self.btn_show_badges.setCheckable(True)
        self.btn_show_badges.setStyleSheet(
            "QPushButton { background-color: #2a2a3a; color: #e8e0f5; font-weight: bold; padding: 12px; border-radius: 10px; font-size: 14px; }"
            "QPushButton:checked { background-color: #f9e2af; color: #160f22; }"
            "QPushButton:!checked { background-color: #2a2a3a; color: #e8e0f5; }")
        nav.addWidget(self.btn_show_missions)
        nav.addWidget(self.btn_show_badges)
        outer.addLayout(nav)

        self.missions_stack = QStackedLayout()
        stack_host = QWidget()
        stack_host.setLayout(self.missions_stack)

        page_m = QWidget()
        pm = QVBoxLayout(page_m)
        pm.setContentsMargins(0, 0, 0, 0)
        prog_frame = QFrame()
        prog_frame.setStyleSheet("background-color: #160f22; border-radius: 12px; border: 1px solid #3d2a55; padding: 8px;")
        pf = QVBoxLayout(prog_frame)
        pf.addWidget(QLabel("📊 پیشرفت مأموریت‌ها"))
        self.mission_overall_bar = QProgressBar()
        self.mission_overall_bar.setRange(0, 100)
        self.mission_overall_bar.setTextVisible(True)
        self.mission_overall_bar.setStyleSheet(
            "QProgressBar { border: 1px solid #3d2a55; border-radius: 8px; background: #100a18; height: 22px; text-align: center; color: white; }"
            "QProgressBar::chunk { background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #89b4fa, stop:1 #c4b5fd); border-radius: 7px; }")
        pf.addWidget(self.mission_overall_bar)
        pm.addWidget(prog_frame)
        scroll_m = QScrollArea()
        scroll_m.setWidgetResizable(True)
        scroll_m.setStyleSheet("border: none; background: transparent;")
        self.missions_cards_host = QWidget()
        self.missions_cards_layout = QVBoxLayout(self.missions_cards_host)
        self.missions_cards_layout.setSpacing(10)
        self.missions_cards_layout.addStretch()
        scroll_m.setWidget(self.missions_cards_host)
        pm.addWidget(scroll_m, 1)
        self.missions_stack.addWidget(page_m)

        page_b = QWidget()
        pb = QVBoxLayout(page_b)
        pb.setContentsMargins(0, 0, 0, 0)
        blbl = QLabel("🏅 اتاق مدال‌ها — کسب‌شده طلایی، باقی خاکستری")
        blbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #f9e2af;")
        pb.addWidget(blbl)
        scroll_badges = QScrollArea()
        scroll_badges.setWidgetResizable(True)
        scroll_badges.setStyleSheet("border: none; background-color: transparent;")
        badges_widget = QWidget()
        badges_layout = QGridLayout(badges_widget)
        badges_layout.setSpacing(14)
        self.badge_widgets = []
        self._badges_layout_ref = badges_layout
        scroll_badges.setWidget(badges_widget)
        pb.addWidget(scroll_badges, 1)
        self.missions_stack.addWidget(page_b)

        outer.addWidget(stack_host, 1)

        def show_missions():
            self.btn_show_missions.setChecked(True)
            self.btn_show_badges.setChecked(False)
            self.missions_stack.setCurrentIndex(0)
        def show_badges():
            self.btn_show_missions.setChecked(False)
            self.btn_show_badges.setChecked(True)
            self.missions_stack.setCurrentIndex(1)
        self.btn_show_missions.clicked.connect(show_missions)
        self.btn_show_badges.clicked.connect(show_badges)

        self.list_missions = QListWidget()
        self.list_missions.hide()

        self.update_missions_ui()
        return w

    def create_notes_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("📝 دفترچه یادداشت و صدور گزارش (PDF):"))
        self.txt_notes = QTextEdit()
        self.txt_notes.setStyleSheet(
            "QTextEdit { font-size: 16px; background-color: #160f22; color: #e8e0f5; padding: 15px; border-radius: 8px; font-weight: 500; line-height: 1.8; border: 2px solid #89b4fa; }")
        self.txt_notes.setPlaceholderText("یادداشت‌های خود را بنویسید...")
        self.txt_notes.setText(self.engine.notes)
        self.txt_notes.textChanged.connect(self.save_notes)
        l.addWidget(self.txt_notes)

        l.addWidget(QLabel("⏱️ لاگ زمانی خودکار:"))
        self.list_auto_log = QListWidget()
        self.list_auto_log.setStyleSheet("background-color: #100a18; font-family: Tahoma, monospace; font-size: 14px; color: #c4b5fd;")
        l.addWidget(self.list_auto_log)

        h_export = QHBoxLayout()
        btn_txt = QPushButton("📥 گزارش TXT")
        btn_txt.clicked.connect(self.action_export_txt)
        btn_txt.setStyleSheet("background-color: #c4b5fd; color: #160f22; font-weight: bold;")
        btn_pdf = QPushButton("📑 خروجی حرفه‌ای PDF")
        btn_pdf.clicked.connect(self.action_export_pdf)
        btn_pdf.setStyleSheet("background-color: #fab387; color: #160f22; font-weight: bold;")
        h_export.addWidget(btn_txt)
        h_export.addWidget(btn_pdf)
        l.addLayout(h_export)
        return w

    def _style_table(self, table):
        """استایل یکدست و مرتب برای همه جدول‌ها."""
        table.setAlternatingRowColors(True)
        table.setShowGrid(False)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setSelectionMode(QTableWidget.SingleSelection)
        table.verticalHeader().setVisible(False)
        table.setSortingEnabled(True)
        table.setWordWrap(False)
        hh = table.horizontalHeader()
        hh.setDefaultAlignment(Qt.AlignCenter)
        hh.setHighlightSections(False)
        hh.setStretchLastSection(True)
        table.verticalHeader().setDefaultSectionSize(36)
        table.setStyleSheet(
            "QTableWidget { background-color: #100a18; alternate-background-color: #160f22; "
            "gridline-color: transparent; color: #e8e0f5; border: 1px solid #3d2a55; "
            "border-radius: 12px; font-size: 13px; outline: 0; }"
            "QTableWidget::item { padding: 6px 8px; border-bottom: 1px solid #1e1530; }"
            "QTableWidget::item:selected { background-color: #4c1d95; color: #f5f3ff; }"
            "QHeaderView::section { background: #1a1228; color: #f0abfc; font-weight: bold; "
            "padding: 10px 6px; border: none; border-bottom: 2px solid #7c3aed; "
            "border-right: 1px solid #2e2040; }"
        )

    def create_contents_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(8, 8, 8, 8)
        l.setSpacing(8)
        tip = QLabel("💡 دوبار کلیک روی ردیف = نمایش ۳بعدی مولکول")
        tip.setStyleSheet("color: #a89bb8; font-size: 11px; padding: 2px 4px;")
        l.addWidget(tip)
        self.table_cont = QTableWidget()
        self.table_cont.setColumnCount(8)
        self.table_cont.setHorizontalHeaderLabels(
            ["ماده", "فرمول", "مقدار", "واحد", "مول (mol)", "جرم تقریبی (g)", "مولاریته (M)", "حذف"])
        self.table_cont.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_cont.horizontalHeader().setSectionResizeMode(7, QHeaderView.Fixed)
        self.table_cont.setColumnWidth(7, 56)
        self.table_cont.cellDoubleClicked.connect(self._on_contents_double_click)
        self._style_table(self.table_cont)
        self.table_cont.setSortingEnabled(False)  # حذف/لایه وابسته به ترتیب
        l.addWidget(self.table_cont)
        row_mix_btns = QHBoxLayout()
        btn_mix3d = QPushButton("🧬 ۳بعدی مخلوط")
        btn_mix3d.setStyleSheet("background-color: #a6e3a1; color: #0c0914; font-weight: bold; border-radius: 7px; padding: 6px 10px;")
        btn_mix3d.setToolTip("نمایش سه‌بعدی اولین مولکول شناخته‌شده در ظرف")
        btn_mix3d.clicked.connect(self.show_mixture_molecule_3d)
        row_mix_btns.addWidget(btn_mix3d)
        row_mix_btns.addStretch()
        l.addLayout(row_mix_btns)

        mix_frame = QFrame()
        mix_frame.setStyleSheet("background-color: #3d2a55; border-radius: 8px; padding: 10px;")
        mix_layout = QVBoxLayout(mix_frame)
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("فرمول مولکولی / تجربی: "))
        self.lbl_mix = QLabel("-")
        self.lbl_mix.setStyleSheet("font-size: 18px; font-weight: bold; color: #c4b5fd;")
        row1.addWidget(self.lbl_mix)
        row1.addStretch()
        mix_layout.addLayout(row1)
        row2 = QHBoxLayout()
        self.lbl_total_mass = QLabel("جرم کل مخلوط: —")
        self.lbl_total_mass.setStyleSheet("font-size: 14px; color: #f9e2af; font-weight: bold;")
        row2.addWidget(self.lbl_total_mass)
        btn_mass = QPushButton("⚖️ محاسبه جرم کل مخلوط")
        btn_mass.setStyleSheet("background-color: #89b4fa; color: #160f22; font-weight: bold; padding: 6px 12px;")
        btn_mass.clicked.connect(self.action_calc_total_mass)
        row2.addWidget(btn_mass)
        row2.addStretch()
        mix_layout.addLayout(row2)
        l.addWidget(mix_frame)
        return w

    def _refresh_graph(self):
        """بازرسم سبک و روان نمودار؛ بدون بازسازی Figure در هر فریم."""
        if not hasattr(self, "graph_canvas") or not hasattr(self, "ax1"):
            return
        try:
            if not self.data_time:
                lo, hi = 0.0, 10.0
                self.ax1.set_xlim(lo, hi)
                self.ax2.set_xlim(lo, hi)
                self.ax1.set_ylim(0, 14)
                self.ax2.set_ylim(20, 40)
                if hasattr(self, "lbl_graph_state"):
                    self.lbl_graph_state.setText("داده‌ها با اجرای شبیه‌سازی ثبت می‌شوند.")
                return

            lo = float(self.data_time[0])
            hi = max(float(self.data_time[-1]), lo + 1.0)
            xpad = max(0.5, (hi - lo) * 0.025)
            self.ax1.set_xlim(lo, hi + xpad)
            self.ax2.set_xlim(lo, hi + xpad)
            self.ax1.set_ylim(0, 14)

            temps = [float(v) for v in self.data_temp if np.isfinite(v)]
            if temps:
                tlo = min(temps) - 3.0
                thi = max(temps) + 3.0
                if thi - tlo < 10.0:
                    mid = (thi + tlo) / 2.0
                    tlo, thi = mid - 5.0, mid + 5.0
                self.ax2.set_ylim(tlo, thi)

            if hasattr(self, "lbl_graph_state"):
                self.lbl_graph_state.setText(
                    f"نقاط ثبت‌شده: {len(self.data_time)}  |  زمان: {self.data_time[-1]:.1f} s"
                )
        except Exception as e:
            tlog(f"graph refresh: {e}", "WARN")

    def _on_graph_tab_changed(self, index):
        """به‌روزرسانی سبک تب نمودار هنگام جابه‌جایی."""
        try:
            cur = self.tabs.currentWidget()
            if cur is getattr(self, "graph_tab_widget", None):
                self._refresh_graph()
                self.graph_canvas.draw_idle()
        except Exception as e:
            print(f"[tab change] {e}", flush=True)

    def create_graph_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(10, 10, 10, 8)
        l.setSpacing(6)

        header = QFrame()
        header.setStyleSheet(
            "QFrame { background:#100a18; border:1px solid #2e2040; border-radius:10px; }"
            "QLabel { border:none; }"
        )
        hl = QHBoxLayout(header)
        hl.setContentsMargins(12, 8, 12, 8)
        title = QLabel("📈 نمودار زنده آزمایش")
        title.setStyleSheet("font-size:14px; font-weight:700; color:#e8e0f5;")
        hl.addWidget(title)
        hl.addStretch(1)
        self.lbl_graph_state = QLabel("داده‌ها با اجرای شبیه‌سازی ثبت می‌شوند.")
        self.lbl_graph_state.setStyleSheet("font-size:11px; color:#8191a8;")
        hl.addWidget(self.lbl_graph_state)
        l.addWidget(header)

        self.figure = Figure(figsize=(7, 7), facecolor="#0a0612")
        self.figure.subplots_adjust(left=0.10, right=0.97, top=0.96, bottom=0.10, hspace=0.28)
        self.graph_canvas = FigureCanvas(self.figure)
        self.graph_canvas.setMinimumHeight(430)
        self.canvas = self.graph_canvas

        self.ax1 = self.figure.add_subplot(211)
        self.ax2 = self.figure.add_subplot(212, sharex=self.ax1)
        for ax in (self.ax1, self.ax2):
            ax.set_facecolor("#120e1c")
            ax.grid(True, alpha=0.16, linewidth=0.7)
            ax.tick_params(colors="#cba6f7", labelsize=9)
            for spine in ax.spines.values():
                spine.set_color("#3d2a55")
                spine.set_linewidth(0.8)

        self.ax1.set_ylabel("pH", color="#e8e0f5", fontsize=10)
        self.ax1.set_ylim(0, 14)
        self.ax1.set_title("pH", loc="left", color="#e8e0f5", fontsize=10, pad=6)
        self.ax2.set_ylabel("دما (°C)", color="#e8e0f5", fontsize=10)
        self.ax2.set_xlabel("زمان (s)", color="#e8e0f5", fontsize=10)
        self.ax2.set_title("دما", loc="left", color="#e8e0f5", fontsize=10, pad=6)

        self.line_ph, = self.ax1.plot([], [], linewidth=2.2, antialiased=True, solid_capstyle="round", label="pH")
        self.line_temp, = self.ax2.plot([], [], linewidth=2.2, antialiased=True, solid_capstyle="round", label="دما")
        self.eq_line = self.ax1.axhline(7.0, linestyle="--", linewidth=1.0, alpha=0.0)

        l.addWidget(self.graph_canvas, 1)
        return w

    def create_discoveries_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(8, 8, 8, 8)
        tip = QLabel("🏆 واکنش‌های کشف‌شده طلایی‌اند؛ بقیه هنوز قفل‌اند.")
        tip.setStyleSheet("color: #a89bb8; font-size: 11px; padding: 2px 4px;")
        l.addWidget(tip)
        self.table_disc = QTableWidget()
        self.table_disc.setColumnCount(3)
        self.table_disc.setHorizontalHeaderLabels(["نام واکنش", "امتیاز", "توضیحات"])
        self.table_disc.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table_disc.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table_disc.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self._style_table(self.table_disc)
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

        if not CUSTOM_REACTIONS:
            lbl = QLabel("واکنشی در دیتابیس نیست.")
            lbl.setStyleSheet("color: #a6adc8; font-size: 16px; padding: 20px;")
            lbl.setAlignment(Qt.AlignCenter)
            container_layout.addWidget(lbl)
        else:
            sorted_rxns = sorted(
                CUSTOM_REACTIONS.items(),
                key=lambda kv: (0 if kv[0] in self.engine.discovered else 1, kv[0])
            )
            for name, rxn in sorted_rxns:
                is_disc = name in self.engine.discovered
                card = QFrame()
                card.setStyleSheet("""
                    QFrame {
                        background-color: #160f22;
                        border: 2px solid #3d2a55;
                        border-radius: 10px;
                        padding: 10px;
                    }
                    QFrame:hover {
                        border: 2px solid #89b4fa;
                    }
                """)
                card_layout = QVBoxLayout(card)

                if is_disc:
                    title_lbl = QLabel(f"🧪 {name}")
                    title_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #f9e2af;")
                else:
                    title_lbl = QLabel(f"🔒 واکنش قفل‌شده")
                    title_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #2a1e3d;")
                card_layout.addWidget(title_lbl)

                reactants_text = " + ".join([CHEMILAB_DB.get(r, {}).get('name', r) for r in rxn.get('reactants', [])])
                if reactants_text and is_disc:
                    lbl_react = QLabel(f"مواد: {reactants_text}")
                    lbl_react.setStyleSheet("color: #e8e0f5; font-size: 13px;")
                    card_layout.addWidget(lbl_react)
                elif not is_disc:
                    n_need = len(rxn.get('reactants', []))
                    lbl_react = QLabel(f"برای کشف: {n_need} ماده لازم — XP: {rxn.get('xp', 0)}")
                    lbl_react.setStyleSheet("color: #a6adc8; font-size: 13px;")
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
                            color: {'#160f22' if QColor(p_color).lightness() > 128 else '#ffffff'};
                            border-radius: 6px;
                            padding: 5px 10px;
                            font-weight: bold;
                            border: 1px solid #3d2a55;
                        """)
                        p_btn.clicked.connect(lambda checked, name=p_name, c=p_color: self.show_product_detail(name, c))
                        prod_layout.addWidget(p_btn)
                    prod_layout.addStretch()
                    card_layout.addLayout(prod_layout)

                info_lbl = QLabel(f"⚡ امتیاز: {rxn.get('xp', 0)}  |  🌡️ دمای مورد نیاز: {rxn.get('temp_min', '-273')}°C")
                info_lbl.setStyleSheet("color: #a6adc8; font-size: 12px;")
                card_layout.addWidget(info_lbl)

                if is_disc:
                    status_lbl = QLabel("✅ کشف شده")
                    status_lbl.setStyleSheet("color: #c4b5fd; font-weight: bold;")
                else:
                    status_lbl = QLabel("🔒 هنوز کشف نشده — هدف آزمایش شما")
                    status_lbl.setStyleSheet("color: #fab387; font-weight: bold;")
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
        dlg.setStyleSheet("background-color: #160f22; border: 2px solid #89b4fa; border-radius: 10px;")

        layout = QVBoxLayout(dlg)

        img_label = QLabel()
        pixmap = QPixmap(200, 200)
        pixmap.fill(QColor(color))
        img_label.setPixmap(pixmap)
        img_label.setAlignment(Qt.AlignCenter)
        img_label.setStyleSheet("border: 2px solid #3d2a55; border-radius: 8px;")
        layout.addWidget(img_label)

        lbl_name = QLabel(f"🧪 {name}")
        lbl_name.setStyleSheet("font-size: 22px; font-weight: bold; color: #f9e2af;")
        lbl_name.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_name)

        lbl_color = QLabel(f"رنگ: {color}")
        lbl_color.setStyleSheet("color: #e8e0f5; font-size: 14px;")
        lbl_color.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_color)

        btn_close = QPushButton("بستن")
        btn_close.clicked.connect(dlg.accept)
        btn_close.setStyleSheet("background-color: #3d2a55; color: #e8e0f5; padding: 8px; border-radius: 6px;")
        layout.addWidget(btn_close)

        dlg.exec()

    def create_datasheet_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)

        self._datasheet_hidden = set()
        try:
            sp = os.path.join(get_app_base_dir(), "datasheet_shelf.json")
            if os.path.exists(sp):
                with open(sp, "r", encoding="utf-8") as f:
                    self._datasheet_hidden = set(json.load(f).get("hidden", []))
        except Exception:
            self._datasheet_hidden = set()

        top = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔎 جستجو: نام، فرمول، SMILES، حالت یا خطر...")
        self.search_input.setStyleSheet(
            "padding: 8px; border-radius: 8px; border: 1px solid #3d2a55; "
            "background-color: #160f22; color: #c4b5fd; font-size: 14px; font-weight: bold;")
        self.search_input.textChanged.connect(self.filter_datasheet)
        top.addWidget(self.search_input, 1)

        btn_hide = QPushButton("➖ از لیست بردار")
        btn_hide.setToolTip("ماده انتخاب‌شده را از لیست پنهان می‌کند (قابل بازگشت)")
        btn_hide.clicked.connect(self.datasheet_hide_selected)
        btn_hide.setStyleSheet("background:#f38ba8; color:#160f22; font-weight:bold; padding:6px 10px; border-radius:8px;")
        top.addWidget(btn_hide)

        btn_restore = QPushButton("➕ برگرداندن")
        btn_restore.setToolTip("همه مواد پنهان‌شده را برمی‌گرداند")
        btn_restore.clicked.connect(self.datasheet_restore_all)
        btn_restore.setStyleSheet("background:#c4b5fd; color:#160f22; font-weight:bold; padding:6px 10px; border-radius:8px;")
        top.addWidget(btn_restore)

        btn_restore_one = QPushButton("📋 پنهان‌شده‌ها")
        btn_restore_one.clicked.connect(self.datasheet_show_hidden_dialog)
        btn_restore_one.setStyleSheet("background:#89b4fa; color:#160f22; font-weight:bold; padding:6px 10px; border-radius:8px;")
        top.addWidget(btn_restore_one)
        layout.addLayout(top)

        self.lbl_ds_count = QLabel("")
        self.lbl_ds_count.setStyleSheet("color:#a6adc8; font-size:12px;")
        layout.addWidget(self.lbl_ds_count)

        self.datasheet_table = QTableWidget()
        self.datasheet_table.setColumnCount(10)
        self.datasheet_table.setHorizontalHeaderLabels(
            ["نام", "فرمول", "کد مولکولی (SMILES)", "نوع", "حالت", "درجه خطر", "رنگ", "مولاریته (M)", "pH", "ΔH"])
        self.datasheet_table.cellDoubleClicked.connect(self._on_datasheet_double_click)
        self.datasheet_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.datasheet_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Fixed)
        self.datasheet_table.setColumnWidth(5, 56)
        self._style_table(self.datasheet_table)
        self.datasheet_table.setSelectionMode(QTableWidget.ExtendedSelection)
        layout.addWidget(self.datasheet_table)

        self.all_datasheet_items = sorted(CHEMILAB_DB.items(), key=lambda x: x[1]['name'])
        self.populate_datasheet(self._datasheet_visible_items())
        return w

    def _datasheet_shelf_path(self):
        return os.path.join(get_app_base_dir(), "datasheet_shelf.json")

    def _save_datasheet_shelf(self):
        try:
            with open(self._datasheet_shelf_path(), "w", encoding="utf-8") as f:
                json.dump({"hidden": list(getattr(self, "_datasheet_hidden", set()))}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[SHELF] save error: {e}", flush=True)

    def _datasheet_visible_items(self):
        hidden = getattr(self, "_datasheet_hidden", set())
        items = list(getattr(self, "all_datasheet_items", sorted(CHEMILAB_DB.items(), key=lambda x: x[1]['name'])))
        return [(k, d) for k, d in items if k not in hidden]

    def datasheet_hide_selected(self):
        if not hasattr(self, "datasheet_table"):
            return
        rows = self.datasheet_table.selectionModel().selectedRows()
        if not rows:
            QMessageBox.information(self, "لیست مواد", "حداقل یک ردیف را انتخاب کنید.")
            return
        if not hasattr(self, "_datasheet_hidden"):
            self._datasheet_hidden = set()
        visible = self._datasheet_visible_items()
        search = self.search_input.text().strip().lower() if hasattr(self, "search_input") else ""
        filtered = []
        for key, data in visible:
            if not search or search in data.get("name", "").lower() or search in data.get("formula", "").lower() or search in str(data.get("state", "")).lower() or search in str(data.get("type", "")).lower() or search in str(data.get("hazard", "")).lower():
                filtered.append((key, data))
        for r in rows:
            idx = r.row()
            if 0 <= idx < len(filtered):
                self._datasheet_hidden.add(filtered[idx][0])
        self._save_datasheet_shelf()
        self.filter_datasheet()

    def datasheet_restore_all(self):
        self._datasheet_hidden = set()
        self._save_datasheet_shelf()
        self.filter_datasheet()
        QMessageBox.information(self, "لیست مواد", "همه مواد پنهان‌شده برگردانده شدند.")

    def datasheet_show_hidden_dialog(self):
        hidden = list(getattr(self, "_datasheet_hidden", set()))
        if not hidden:
            QMessageBox.information(self, "پنهان‌شده‌ها", "ماده پنهانی وجود ندارد.")
            return
        dlg = QDialog(self)
        dlg.setWindowTitle("مواد برداشته‌شده از لیست")
        dlg.setMinimumSize(420, 360)
        lay = QVBoxLayout(dlg)
        lst = QListWidget()
        for k in sorted(hidden):
            d = CHEMILAB_DB.get(k, {})
            lst.addItem(f"{d.get('name', k)}  ({d.get('formula', k)})")
            lst.item(lst.count() - 1).setData(Qt.UserRole, k)
        lst.setSelectionMode(QListWidget.ExtendedSelection)
        lay.addWidget(lst)
        btn = QPushButton("برگرداندن انتخاب‌شده‌ها")
        btn.setStyleSheet("background:#c4b5fd; color:#160f22; font-weight:bold; padding:8px; border-radius:8px;")
        def restore_sel():
            for it in lst.selectedItems():
                k = it.data(Qt.UserRole)
                self._datasheet_hidden.discard(k)
            self._save_datasheet_shelf()
            self.filter_datasheet()
            dlg.accept()
        btn.clicked.connect(restore_sel)
        lay.addWidget(btn)
        dlg.exec()

    def update_player_stats(self):
        if getattr(self, "is_admin", False):
            return
        if hasattr(self, "lbl_level"):
            self.lbl_level.setText(f"سطح: {self.engine.level}")
        if hasattr(self, "lbl_score"):
            self.lbl_score.setText(f"امتیاز: {self.engine.score}")
        if hasattr(self, "lbl_welcome"):
            self.lbl_welcome.setText(f"👤 شیمیدان: {self.engine.player_name}")
        if hasattr(self, "progress_xp"):
            self.progress_xp.setValue(int(self.engine.score) % 100)
        if hasattr(self, "btn_profile"):
            self.btn_profile.setText(f"👤 {self.engine.player_name} | Lv.{self.engine.level}")

    def update_contents_ui(self):
        if getattr(self, "is_admin", False):
            return
        self.table_cont.setRowCount(0)
        vol_l = max(self.engine.total_volume / 1000.0, 1e-9)
        total_mass = 0.0
        for i, layer in enumerate(self.engine.visual_layers):
            self.table_cont.insertRow(i)
            self.table_cont.setItem(i, 0, QTableWidgetItem(layer['name']))
            f = CHEMILAB_DB.get(layer['key'], {}).get('formula', layer.get('formula', '?'))
            self.table_cont.setItem(i, 1, QTableWidgetItem(ChemicalCalculator.to_subscript(f)))
            self.table_cont.setItem(i, 2, QTableWidgetItem(f"{layer['amount']:.2f}"))
            ctype = CHEMILAB_DB.get(layer['key'], {}).get('type', '')
            unit = "g" if any(x in ctype for x in ["Solid", "Metal", "Salt", "Precipitate"]) else "mL"
            self.table_cont.setItem(i, 3, QTableWidgetItem(unit))
            moles = safe_float(layer.get('moles', 0), 0.0)
            self.table_cont.setItem(i, 4, QTableWidgetItem(f"{moles:.4g}"))
            mm = ChemicalCalculator.molar_mass(f) if f and f not in ('?', '-') else 0.0
            mass_g = moles * mm if mm > 0 else 0.0
            total_mass += mass_g
            self.table_cont.setItem(i, 5, QTableWidgetItem(f"{mass_g:.3g}" if mass_g > 0 else "—"))
            molarity_now = moles / vol_l if self.engine.total_volume > 0.5 else 0.0
            self.table_cont.setItem(i, 6, QTableWidgetItem(f"{molarity_now:.3f}"))
            btn_del = QPushButton("❌")
            btn_del.setFixedSize(30, 25)
            btn_del.setStyleSheet("background-color: #ff5555; border-radius: 4px;")
            btn_del.clicked.connect(lambda checked, lid=layer['id']: self.remove_item(lid))
            self.table_cont.setCellWidget(i, 7, btn_del)
        formula_text = self.engine.get_mixture_empirical_formula()
        n_active = sum(1 for v in self.engine.contents.values() if v > 1e-12)
        if n_active == 1:
            self.lbl_mix.setText(f"مولکولی: {formula_text}")
        else:
            self.lbl_mix.setText(f"تجربی مخلوط: {formula_text}")
        if hasattr(self, 'lbl_total_mass'):
            self.lbl_total_mass.setText(f"جرم کل مخلوط: {total_mass:.3g} g")

    def action_calc_total_mass(self):
        total = 0.0
        details = []
        for layer in self.engine.visual_layers:
            f = CHEMILAB_DB.get(layer['key'], {}).get('formula', layer.get('formula', ''))
            moles = safe_float(layer.get('moles', 0), 0.0)
            mm = ChemicalCalculator.molar_mass(f) if f else 0.0
            mass = moles * mm
            total += mass
            if mass > 0:
                details.append(f"{layer['name']}: {mass:.3g} g")
        msg = f"جرم کل تقریبی مخلوط: {total:.4g} g\n\n" + "\n".join(details[:12])
        if len(details) > 12:
            msg += f"\n... و {len(details)-12} مورد دیگر"
        QMessageBox.information(self, "جرم کل مخلوط", msg)
        if hasattr(self, 'lbl_total_mass'):
            self.lbl_total_mass.setText(f"جرم کل مخلوط: {total:.3g} g")
        self._log(f"⚖️ جرم کل مخلوط محاسبه شد: {total:.3g} g")

    def update_missions_ui(self):
        if getattr(self, "is_admin", False):
            return
        icons = {
            "m1": "🧪", "m2": "🔬", "m3": "🧪", "m4": "🔥",
            "m5": "⚖️", "m6": "💥", "m7": "💧", "m8": "🔥"
        }
        if hasattr(self, 'list_missions') and self.list_missions is not None:
            self.list_missions.clear()
            for m in self.engine.missions:
                status = "✅" if m['id'] in self.engine.completed_missions else "⏳"
                icon = icons.get(m['id'], "🎯")
                self.list_missions.addItem(f"{icon} {status} | {m['title']} (+{m['xp']} XP)\n   {m['desc']}")

        if hasattr(self, 'missions_cards_layout') and self.missions_cards_layout is not None:
            lay = self.missions_cards_layout
            while lay.count():
                item = lay.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            done = 0
            for m in self.engine.missions:
                completed = m['id'] in self.engine.completed_missions
                if completed:
                    done += 1
                card = QFrame()
                if completed:
                    card.setStyleSheet(
                        "QFrame { background-color: #1a2e1a; border: 1px solid #c4b5fd; border-radius: 12px; padding: 6px; }")
                else:
                    card.setStyleSheet(
                        "QFrame { background-color: #160f22; border: 1px solid #3d2a55; border-radius: 12px; padding: 6px; }"
                        "QFrame:hover { border: 1px solid #89b4fa; }")
                cl = QHBoxLayout(card)
                icon = icons.get(m['id'], "🎯")
                status = "✅" if completed else "⏳"
                left = QLabel(f"{icon}\n{status}")
                left.setAlignment(Qt.AlignCenter)
                left.setFixedWidth(50)
                left.setStyleSheet("font-size: 18px; border: none; background: transparent;")
                cl.addWidget(left)
                mid = QVBoxLayout()
                t = QLabel(m['title'])
                t.setStyleSheet(
                    f"font-size: 14px; font-weight: bold; color: {'#c4b5fd' if completed else '#e8e0f5'}; border: none; background: transparent;")
                d = QLabel(m['desc'])
                d.setWordWrap(True)
                d.setStyleSheet("font-size: 12px; color: #a6adc8; border: none; background: transparent;")
                mid.addWidget(t)
                mid.addWidget(d)
                cl.addLayout(mid, 1)
                xp = QLabel(f"+{m['xp']} XP")
                xp.setStyleSheet(
                    "font-size: 13px; font-weight: bold; color: #f9e2af; background: #3d2a55; "
                    "border-radius: 8px; padding: 6px 10px;")
                cl.addWidget(xp)
                lay.addWidget(card)
            lay.addStretch()
            total = max(1, len(self.engine.missions))
            pct = int(100 * done / total)
            if hasattr(self, 'mission_overall_bar'):
                self.mission_overall_bar.setValue(pct)
                self.mission_overall_bar.setFormat(f"{done} از {total}  —  {pct}%")
            if hasattr(self, 'lbl_mission_progress'):
                self.lbl_mission_progress.setText(f"{done}/{total} تکمیل‌شده")

        layout = getattr(self, '_badges_layout_ref', None)
        if layout is None:
            try:
                scroll_widget = self.tabs.widget(2)
                if scroll_widget:
                    for child in scroll_widget.findChildren(QScrollArea):
                        bw = child.widget()
                        if bw and isinstance(bw.layout(), QGridLayout):
                            layout = bw.layout()
                            break
            except Exception:
                layout = None
        if layout is not None:
            for wdg in getattr(self, 'badge_widgets', []):
                try:
                    wdg.deleteLater()
                except Exception:
                    pass
            self.badge_widgets = []
            while layout.count():
                item = layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            row, col = 0, 0
            all_badges = list(BADGE_CATALOG.keys())
            for badge in all_badges:
                earned = badge in self.engine.badges
                bw = BadgeWidget(badge, earned=earned)
                layout.addWidget(bw, row, col)
                self.badge_widgets.append(bw)
                col += 1
                if col >= 4:
                    col = 0
                    row += 1

    def update_report_card(self):
        if getattr(self, "is_admin", False):
            return
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

        warn_count = getattr(self.engine, 'safety_warnings_count', 0)
        titr_info = ""
        if getattr(self.engine, 'last_titration_endpoint_vol', 0) > 0:
            titr_info = (f"<br><b>💧 آخرین تیتراسیون:</b> حجم={self.engine.last_titration_endpoint_vol:.1f} mL"
                         f" | غلظت تقریبی آنالیت={getattr(self.engine, 'titration_analyte_conc', 0) or 0:.3g} M")
        text = f"""
            <b>⏱️ زمان کل فعالیت:</b> {time_str}<br>
            <b>🧪 تعداد واکنش‌های کشف شده:</b> {s['reactions_found']}<br>
            <b>💥 دفعات شکستن ظرف (خطا):</b> {s['flask_breaks']}<br>
            <b>⚗️ استفاده از فیلتر:</b> {s['filter_uses']} بار<br>
            <b>🎯 تیتراسیون‌های موفق:</b> {s['successful_titrations']}{titr_info}<br>
            <b>🛡️ تعداد هشدارهای ایمنی ثبت‌شده:</b> {warn_count}<br><br>
            <hr><br>
            <b>امتیاز نهایی عملکرد: <span style='color:#c4b5fd;'>{final_score} از ۱۰۰</span></b><br>
            <b>نمره ارزیابی کلی سیستم: <span style='color:#f38ba8; font-size: 24px;'>{grade}</span></b>
            """
        self.lbl_stats.setText(text)

    def update_discoveries_table(self):
        if getattr(self, "is_admin", False):
            return
        items = sorted(
            CUSTOM_REACTIONS.items(),
            key=lambda kv: (0 if kv[0] in self.engine.discovered else 1, kv[0])
        )
        self.table_disc.setRowCount(len(items))
        self.table_disc.setStyleSheet(
            "QTableWidget { background-color: #100a18; gridline-color: #3d2a55; color: #e8e0f5; "
            "border: 1px solid #3d2a55; border-radius: 10px; font-size: 13px; }"
            "QHeaderView::section { background-color: #160f22; color: #f9e2af; font-weight: bold; padding: 8px; }"
            "QTableWidget::item { padding: 6px; }")
        for i, (n, d) in enumerate(items):
            desc = d.get('desc', '')
            temp = d.get('temp_min', '-')
            full_desc = f"{desc} (دمای مورد نیاز: {temp}°C)" if desc else f"دمای مورد نیاز: {temp}°C"
            if n in self.engine.discovered:
                name_item = QTableWidgetItem(f"✅ {n}")
                name_item.setForeground(QColor("#c4b5fd"))
                xp_item = QTableWidgetItem(str(d.get('xp', 0)))
                xp_item.setForeground(QColor("#f9e2af"))
                desc_item = QTableWidgetItem(full_desc)
                desc_item.setForeground(QColor("#e8e0f5"))
                self.table_disc.setItem(i, 0, name_item)
                self.table_disc.setItem(i, 1, xp_item)
                self.table_disc.setItem(i, 2, desc_item)
            else:
                name_item = QTableWidgetItem("🔒 هنوز کشف نشده")
                name_item.setForeground(QColor("#2a1e3d"))
                self.table_disc.setItem(i, 0, name_item)
                self.table_disc.setItem(i, 1, QTableWidgetItem("—"))
                desc_item = QTableWidgetItem(full_desc)
                desc_item.setForeground(QColor("#585b70"))
                self.table_disc.setItem(i, 2, desc_item)

    def update_wiki_tab(self):
        if getattr(self, "is_admin", False):
            return
        """به‌روزرسانی تب دانشنامه بدون از دست رفتن اسکرول (replace widget)."""
        try:
            index = -1
            for i in range(self.tabs.count()):
                if "دانشنامه" in self.tabs.tabText(i):
                    index = i
                    break
            if index < 0:
                return
            current = self.tabs.currentIndex()
            new_tab = self.create_wiki_tab()
            self.tabs.removeTab(index)
            self.tabs.insertTab(index, new_tab, "📖 دانشنامه")
            if current == index:
                self.tabs.setCurrentIndex(index)
            elif current > index:
                self.tabs.setCurrentIndex(current)
        except Exception as e:
            tlog(f"update_wiki_tab: {e}", "WARN")

    def update_auto_log_ui(self):
        if getattr(self, "is_admin", False):
            return
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
            table.setItem(i, 2, QTableWidgetItem(str(data.get('smiles', '') or "—")))
            table.setItem(i, 3, QTableWidgetItem(get_persian_type(data.get('type', ''))))
            table.setItem(i, 4, QTableWidgetItem(str(data.get('state', 'جامد'))))
            table.setItem(i, 5, QTableWidgetItem(str(data.get('hazard', 'کم‌خطر'))))
            color_cell = QTableWidgetItem("")
            try:
                color_cell.setBackground(QColor(data.get('color', '#FFFFFF')))
            except Exception:
                pass
            color_cell.setFlags(Qt.ItemIsEnabled)
            table.setItem(i, 6, color_cell)
            table.setItem(i, 7, QTableWidgetItem(str(data.get('molarity', '-'))))
            table.setItem(i, 8, QTableWidgetItem(str(data.get('pH', '-'))))
            table.setItem(i, 9, QTableWidgetItem(str(data.get('heat', '-'))))
        if hasattr(self, "lbl_ds_count"):
            hid = len(getattr(self, "_datasheet_hidden", set()))
            self.lbl_ds_count.setText(f"نمایش {len(items)} ماده  |  پنهان‌شده: {hid}")

    def filter_datasheet(self, *_args):
        search = self.search_input.text().strip().lower() if hasattr(self, "search_input") else ""
        base = self._datasheet_visible_items() if hasattr(self, "_datasheet_visible_items") else list(getattr(self, "all_datasheet_items", []))
        if not search:
            filtered = base
        else:
            filtered = []
            for key, data in base:
                if (search in data.get('name', '').lower()
                        or search in data.get('formula', '').lower()
                        or search in str(data.get('state', '')).lower()
                        or search in str(data.get('type', '')).lower()
                        or search in str(data.get('hazard', '')).lower()
                        or search in str(data.get('smiles', '')).lower()):
                    filtered.append((key, data))
        self.populate_datasheet(filtered)

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
            if hasattr(self, 'gl_beaker') and self.gl_beaker is not None:
                self.gl_beaker._needs_redraw = True
                self.gl_beaker.update()
            self.handle_reaction_result(self.engine.check_reactions())
            self.update_auto_log_ui()
        except Exception as e:
            tlog(f"action_add error: {e}", "ERROR")
            self._log(f"❌ خطا در افزودن ماده: {e}")

    def action_wash(self):
        tlog("action_wash", "CLICK")
        self.engine.reset()
        self.container.set_stirrer(False)
        self.container.display_volume = 0.0
        if hasattr(self, 'btn_stirrer'):
            self.btn_stirrer.setChecked(False)
        self.update_contents_ui()
        if hasattr(self, 'gl_beaker') and self.gl_beaker:
            self.gl_beaker._needs_redraw = True
            self.gl_beaker.update()
        self._log("🧹 ظرف با موفقیت تعویض و کاملاً تمیز شد.")
        self.update_auto_log_ui()

    def action_heat(self):
        tlog("action_heat", "CLICK", temp=self.engine.temp_c)
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
        tlog("action_cool", "CLICK", temp=self.engine.temp_c)
        self.engine.change_temperature(-HEAT_COOL_DELTA)
        self.container.set_plate_state("cool")
        self.container.plate_glow_alpha = 180
        self._log(f"🧊 سرمایش فعال شد (-{HEAT_COOL_DELTA}°) — دمای فعلی: {self.engine.temp_c:.1f}°C")

    def action_filter(self):
        tlog("action_filter", "CLICK")
        removed = self.engine.filter_solids()
        if removed:
            self._log(f"⚗️ مایع/گاز دور ریخته شد؛ جامدات در ظرف ماند. دورریز: {', '.join(removed)}")
            self.update_contents_ui()
        else:
            self._log("⚗️ فقط جامد در ظرف است یا ماده‌ای برای جداسازی نیست.")

    def action_toggle_stirrer(self):
        on = False
        if hasattr(self, "btn_stirrer") and self.btn_stirrer is not None:
            on = self.btn_stirrer.isChecked()
        if hasattr(self, "act_stirrer"):
            self.act_stirrer.blockSignals(True)
            self.act_stirrer.setChecked(on)
            self.act_stirrer.blockSignals(False)
        if self.container is not None:
            self.container.set_stirrer(on)
        if hasattr(self, 'lbl_stirrer_3d'):
            self.lbl_stirrer_3d.setText("🌪️ همزن روشن" if on else "")
        if hasattr(self, 'lbl_stirrer_status'):
            self.lbl_stirrer_status.setText("همزن: 🌪️ روشن" if on else "همزن: خاموش")
            self.lbl_stirrer_status.setStyleSheet(
                "color: #c4b5fd; font-weight: bold; font-size: 12px;")
        if hasattr(self, 'gl_beaker') and self.gl_beaker is not None:
            self.gl_beaker.stirrer_on = on
            self.gl_beaker.update()
        self._log(f"🌪️ همزن مغناطیسی {'روشن' if on else 'خاموش'} شد.")
        self.engine.add_to_log(f"همزن {'روشن' if on else 'خاموش'} شد.")

    def action_toggle_titration(self):
        checked = False
        if hasattr(self, "btn_titrate") and self.btn_titrate is not None:
            checked = self.btn_titrate.isChecked()
        if hasattr(self, "act_titrate"):
            self.act_titrate.blockSignals(True)
            self.act_titrate.setChecked(checked)
            self.act_titrate.blockSignals(False)
        if checked:
            if self.engine.is_broken:
                self.btn_titrate.setChecked(False)
                QMessageBox.warning(self, "تیتراسیون", "ظرف شکسته است؛ ابتدا آن را بشویید.")
                return
            self.engine.titration_volume = 0.0
            self.engine._titration_initial_volume = float(self.engine.total_volume)
            if hasattr(self, "btn_titrate") and self.btn_titrate is not None:
                self.btn_titrate.setText("⏹️ توقف")
                self.btn_titrate.setStyleSheet(
                    "background-color: #f38ba8; color: #160f22; font-weight: bold; border-radius: 8px; font-size: 13px;")
            if hasattr(self, 'lbl_titration_status'):
                self.lbl_titration_status.setText("💧 در حال تیتراسیون…")
        else:
            if hasattr(self, "btn_titrate") and self.btn_titrate is not None:
                self.btn_titrate.setText("💧 بورت")
                self.btn_titrate.setStyleSheet(
                    "background-color: #89b4fa; color: #160f22; font-weight: bold; border-radius: 8px; font-size: 13px;")
            if hasattr(self, 'lbl_titration_status'):
                self.lbl_titration_status.setText("")

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
            margin = 100
            y = margin
            page_num = [1]

            def new_page_if_needed(need):
                nonlocal y
                if y + need > h - margin - 80:
                    painter.setFont(QFont(FONT_NAME, 8))
                    painter.setPen(QColor(140, 140, 160))
                    painter.drawText(QRectF(margin, h - 70, w - 2 * margin, 40), Qt.AlignHCenter,
                                     f"شیمی‌لَب  |  صفحه {page_num[0]}")
                    pdf.newPage()
                    page_num[0] += 1
                    y = margin
                    return True
                return False

            def card(x, yy, bw, bh, fill, border):
                painter.setPen(QPen(border, 4))
                painter.setBrush(fill)
                painter.drawRoundedRect(QRectF(x, yy, bw, bh), 24, 24)

            def title_bar(text, yy, accent=QColor(30, 80, 160)):
                card(margin - 10, yy, w - 2 * margin + 20, 90, accent, accent.darker(120))
                painter.setFont(QFont(FONT_NAME, 14, QFont.Bold))
                painter.setPen(QColor(255, 255, 255))
                painter.drawText(QRectF(margin + 20, yy, w - 2 * margin - 40, 90),
                                 Qt.AlignRight | Qt.AlignVCenter, text)
                return yy + 110

            def line(text, yy, size=11, color=QColor(30, 30, 40), bold=False):
                painter.setFont(QFont(FONT_NAME, size, QFont.Bold if bold else QFont.Normal))
                painter.setPen(color)
                painter.drawText(QRectF(margin + 40, yy, w - 2 * margin - 80, 70),
                                 Qt.AlignRight | Qt.AlignVCenter, text)
                return yy + 68

            card(margin - 20, y, w - 2 * margin + 40, 420,
                 QColor(25, 45, 90), QColor(15, 30, 70))
            painter.setFont(QFont(FONT_NAME, 28, QFont.Bold))
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(QRectF(margin, y + 60, w - 2 * margin, 100), Qt.AlignHCenter, "گزارش رسمی آزمایشگاه")
            painter.setFont(QFont(FONT_NAME, 20, QFont.Bold))
            painter.setPen(QColor(166, 227, 161))
            painter.drawText(QRectF(margin, y + 160, w - 2 * margin, 70), Qt.AlignHCenter, f"{APP_NAME}  •  Universe ChimiLab {APP_VERSION}")
            painter.setFont(QFont(FONT_NAME, 12))
            painter.setPen(QColor(220, 220, 240))
            painter.drawText(QRectF(margin, y + 250, w - 2 * margin, 50), Qt.AlignHCenter,
                             f"شیمیدان: {self.engine.player_name}   |   سطح: {self.engine.level}   |   امتیاز: {self.engine.score}")
            painter.drawText(QRectF(margin, y + 310, w - 2 * margin, 50), Qt.AlignHCenter,
                             datetime.now().strftime("%Y/%m/%d  —  %H:%M:%S"))
            y += 460

            y = title_bar("🧪 وضعیت فعلی ظرف", y, QColor(40, 100, 140))
            card(margin - 10, y, w - 2 * margin + 20,
                 160 + max(1, len(self.engine.visual_layers)) * 65,
                 QColor(245, 248, 255), QColor(100, 150, 200))
            y += 30
            y = line(f"برچسب ظرف: {self.engine.flask_label}", y, 12, bold=True)
            y = line(f"دما: {self.engine.temp_c:.1f} °C    |    pH: {self.engine.get_ph():.2f}", y, 12)
            y = line(f"فرمول تجربی مخلوط: {self.engine.get_mixture_empirical_formula()}", y, 12, QColor(20, 100, 80), True)
            y = line("محتویات:", y, 12, QColor(80, 80, 120), True)
            if self.engine.visual_layers:
                for layer in self.engine.visual_layers:
                    y = line(f"• {layer['name']}  —  {layer['amount']:.1f} واحد  ({layer.get('type', '')})", y, 10)
            else:
                y = line("— ظرف خالی است —", y, 10, QColor(140, 140, 140))
            y += 50

            if self.engine.total_volume > 0.5 and self.engine.visual_layers:
                new_page_if_needed(900)
                y = title_bar("📸 تصویر لحظه‌ای ظرف", y, QColor(90, 60, 140))
                flask_img = self.container.grab().toImage()
                target_w = int(w * 0.42)
                target_h = int((target_w / max(1, flask_img.width())) * flask_img.height())
                new_page_if_needed(target_h + 80)
                card((w - target_w) / 2 - 20, y, target_w + 40, target_h + 40, QColor(250, 250, 255), QColor(120, 140, 200))
                painter.drawImage(QRectF((w - target_w) / 2, y + 20, target_w, target_h), flask_img)
                y += target_h + 70

            notes = self.txt_notes.toPlainText().strip() or "—"
            notes_block = 200 + min(500, max(80, len(notes) * 2))
            new_page_if_needed(notes_block + 120)
            y = title_bar("📝 یادداشت‌های شیمیدان", y, QColor(160, 110, 40))
            card(margin - 10, y, w - 2 * margin + 20, notes_block, QColor(255, 252, 240), QColor(200, 150, 60))
            painter.setFont(QFont(FONT_NAME, 11))
            painter.setPen(QColor(40, 40, 40))
            painter.drawText(QRectF(margin + 40, y + 30, w - 2 * margin - 80, notes_block - 60),
                             Qt.AlignRight | Qt.AlignTop | Qt.TextWordWrap, notes)
            y += notes_block + 40

            new_page_if_needed(400)
            y = title_bar("📊 آمار عملکرد", y, QColor(40, 120, 80))
            s = self.engine.stats
            play_m, play_s = divmod(int(s.get('total_play_time', 0)), 60)
            play_h, play_m = divmod(play_m, 60)
            card(margin - 10, y, w - 2 * margin + 20, 320, QColor(240, 255, 245), QColor(60, 150, 90))
            y += 25
            y = line(f"زمان فعالیت: {play_h}س {play_m}د {play_s}ث", y, 11)
            y = line(f"واکنش‌های کشف‌شده: {s.get('reactions_found', 0)}", y, 11)
            y = line(f"شکستن ظرف: {s.get('flask_breaks', 0)}  |  فیلتر: {s.get('filter_uses', 0)}  |  تیتراسیون موفق: {s.get('successful_titrations', 0)}", y, 11)
            y = line(f"سطح: {self.engine.level}  |  امتیاز: {self.engine.score}", y, 12, QColor(20, 90, 50), True)
            y += 40

            new_page_if_needed(350)
            y = title_bar("🏅 مدال‌ها و مأموریت‌ها", y, QColor(140, 100, 30))
            card(margin - 10, y, w - 2 * margin + 20, 280, QColor(255, 250, 230), QColor(200, 160, 50))
            y += 25
            badges_text = "، ".join([f"{BADGE_CATALOG.get(b, ('🏅', ''))[0]} {b}" for b in self.engine.badges]) or "—"
            y = line(f"مدال‌ها: {badges_text}", y, 10)
            missions_text = "، ".join(
                [m['title'] for m in self.engine.missions if m['id'] in self.engine.completed_missions]
            ) or "—"
            y = line(f"مأموریت‌های تکمیل‌شده: {missions_text}", y, 10)
            y += 40

            new_page_if_needed(280)
            y = title_bar("🏆 واکنش‌های کشف‌شده", y, QColor(100, 60, 140))
            card(margin - 10, y, w - 2 * margin + 20, 200, QColor(248, 245, 255), QColor(130, 90, 180))
            y += 30
            discs = "، ".join(sorted(self.engine.discovered)) or "هنوز واکنشی کشف نشده"
            y = line(discs, y, 11)

            new_page_if_needed(400)
            y = title_bar("⏱️ آخرین رویدادهای لاگ", y, QColor(60, 70, 100))
            logs = self.engine.auto_log[-12:] if self.engine.auto_log else ["—"]
            card(margin - 10, y, w - 2 * margin + 20, 80 + len(logs) * 55,
                 QColor(245, 245, 250), QColor(100, 110, 140))
            y += 25
            for log_item in logs:
                y = line(str(log_item)[:90], y, 9, QColor(50, 50, 70))

            painter.setFont(QFont(FONT_NAME, 8))
            painter.setPen(QColor(120, 120, 140))
            painter.drawText(QRectF(margin, h - 70, w - 2 * margin, 40), Qt.AlignHCenter,
                             f"{APP_NAME} (Universe ChimiLab {APP_VERSION})  |  صفحه {page_num[0]}  |  تولید خودکار گزارش")

            painter.end()
            QMessageBox.information(self, "موفق", "گزارش PDF چندصفحه‌ای با کادرهای حرفه‌ای ذخیره شد.")
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در ایجاد PDF:\n{str(e)}")

    def toggle_theme(self):
        """تم روشن حذف شده — فقط تم بنفش تیره"""
        sizes = self.main_splitter.sizes() if hasattr(self, 'main_splitter') else None
        self.setStyleSheet(APP_STYLE_DARK)
        if sizes:
            self.main_splitter.setSizes(sizes)
        DimensionController.preserve_splitter(getattr(self, 'main_splitter', None))
        DimensionController.reapply_all()

    def _setup_shortcuts(self):
        """میانبرهای سراسری با QShortcut — مستقل از فوکوس ویجت فرزند"""
        if getattr(self, "is_admin", False):
            return
        always = [
            ("Ctrl+Z", self.action_undo),
            ("Ctrl+Y", self.action_redo),
            ("Ctrl+S", self.action_save_state_file),
            ("F11", self._shortcut_toggle_fullscreen),
        ]
        soft = [
            ("Space", self._shortcut_toggle_stirrer),
            ("H", self.action_heat),
            ("C", self.action_cool),
            ("F", self.action_filter),
        ]
        self._shortcuts = []
        for seq, slot in always:
            sc = QShortcut(QKeySequence(seq), self)
            sc.setContext(Qt.ApplicationShortcut)
            sc.activated.connect(slot)
            self._shortcuts.append(sc)
        for seq, slot in soft:
            sc = QShortcut(QKeySequence(seq), self)
            sc.setContext(Qt.ApplicationShortcut)
            sc.setAutoRepeat(False)
            sc.activated.connect(lambda s=slot: self._run_soft_shortcut(s))
            self._shortcuts.append(sc)

    def _run_soft_shortcut(self, slot):
        """حروف تکی را وقتی فوکوس روی فیلد متنی است نادیده بگیر"""
        focus = self.focusWidget()
        if focus is not None and focus.__class__.__name__ in (
            "QLineEdit", "QTextEdit", "QPlainTextEdit", "QSpinBox", "QDoubleSpinBox", "QComboBox"
        ):
            return
        try:
            slot()
        except Exception as e:
            tlog(f"soft shortcut error: {e}", "ERROR")

    def _shortcut_toggle_stirrer(self):
        if hasattr(self, 'btn_stirrer'):
            self.btn_stirrer.toggle()
            self.action_toggle_stirrer()

    def _shortcut_toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def keyPressEvent(self, event):
        """پشتیبان میانبرها (اگر QShortcut به‌خاطر فوکوس فعال نشود)"""
        key = event.key()
        mods = event.modifiers()
        try:
            if mods & Qt.ControlModifier:
                if key == Qt.Key_Z:
                    self.action_undo()
                    return
                if key == Qt.Key_Y:
                    self.action_redo()
                    return
                if key == Qt.Key_S:
                    self.action_save_state_file()
                    return
            focus = self.focusWidget()
            typing = focus is not None and focus.__class__.__name__ in (
                "QLineEdit", "QTextEdit", "QPlainTextEdit", "QSpinBox", "QDoubleSpinBox", "QComboBox"
            )
            if not typing:
                if key == Qt.Key_Space:
                    self._shortcut_toggle_stirrer()
                    return
                if key == Qt.Key_H:
                    self.action_heat()
                    return
                if key == Qt.Key_C:
                    self.action_cool()
                    return
                if key == Qt.Key_F:
                    self.action_filter()
                    return
            if key == Qt.Key_F11:
                self._shortcut_toggle_fullscreen()
                return
        except Exception as e:
            tlog(f"keyPress error: {e}", "ERROR")
        super().keyPressEvent(event)

    def _enforce_splitter_layout(self):
        """اجبار جدا بودن سه پنل — جلوگیری از هم‌پوشانی راست با بشر."""
        sp = getattr(self, "main_splitter", None)
        if sp is None:
            return
        try:
            total = max(1, sp.width())
            left = 400
            right = 600
            mid = max(320, total - left - right)
            if left + mid + right > total:
                # Keep V47's minimum panel widths when the window is narrower.
                left = 360
                right = 280
                mid = max(320, total - left - right)
            sp.setSizes([left, mid, right])
            tlog("enforce splitter V47", "LAYOUT", sizes=sp.sizes(), total=total)
        except Exception as e:
            tlog(f"enforce splitter: {e}", "WARN")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        try:
            tb = getattr(self, '_bottom_toolbar_ref', None)
            if tb is not None:
                tb.setFixedHeight(58)
                tb.setVisible(True)
                if self.centralWidget() and self.centralWidget().layout():
                    self.centralWidget().layout().activate()

            if hasattr(self, 'main_splitter'):
                sizes = self.main_splitter.sizes()
                if len(sizes) >= 3 and (sizes[0] < 260 or sizes[1] < 360 or sizes[2] < 280):
                    self._enforce_splitter_layout()

        except Exception as e:
            tlog(f"resize error: {e}", "ERROR")

    def _tab_go_first(self):
        if hasattr(self, "tabs") and self.tabs.count() > 0:
            self.tabs.setCurrentIndex(0)

    def _tab_go_last(self):
        if hasattr(self, "tabs") and self.tabs.count() > 0:
            self.tabs.setCurrentIndex(self.tabs.count() - 1)

    def _tab_go_prev(self):
        if hasattr(self, "tabs") and self.tabs.count() > 0:
            i = self.tabs.currentIndex()
            self.tabs.setCurrentIndex(max(0, i - 1))

    def _tab_go_next(self):
        if hasattr(self, "tabs") and self.tabs.count() > 0:
            i = self.tabs.currentIndex()
            self.tabs.setCurrentIndex(min(self.tabs.count() - 1, i + 1))

    def toggle_tabs(self):
        self.tabs.setVisible(not self.tabs.isVisible())

    def set_speed(self, speed):
        self.engine.speed_multiplier = speed
        self._log(f"⏱️ سرعت زمان به x{speed} تغییر کرد.")

    def handle_reaction_result(self, disc):
        if not disc:
            return
        if len(disc) >= 6:
            name, xp, status, has_pr, has_gas, thermo = disc[:6]
        else:
            name, xp, status, has_pr, has_gas = disc[:5]
            thermo = getattr(self.engine, "last_reaction_thermo", None) or {}
        if status == "new":
            self.timer.stop()
            self._log(f"✨ واکنش جدید کشف شد: {name}")
            dH = thermo.get("dH", 0)
            if thermo.get("is_exothermic"):
                self._log(f"🔥 واکنش گرمازا است (ΔH ≈ {dH:.1f} kJ/mol تقریبی)")
            elif thermo.get("is_endothermic"):
                self._log(f"❄️ واکنش گرماگیر است (ΔH ≈ {dH:.1f} kJ/mol تقریبی)")
            else:
                self._log(f"ΔH تقریبی نزدیک صفر است ({dH:.1f})")
            lim = thermo.get("limiting")
            if lim:
                lim_name = CHEMILAB_DB.get(normalize_key(lim), {}).get("name", lim)
                self._log(f"⚖️ ماده محدودکننده: {lim_name} — تبدیل تقریبی ~{thermo.get('conversion_pct', 0):.0f}%")
            if thermo.get("has_gas"):
                self._log("💨 گاز نیز در محصولات شناسایی شد.")
            if thermo.get("has_precipitate"):
                self._log("🪨 رسوب در محصولات شناسایی شد.")
            self.container.trigger_reaction_animation(has_pr, has_gas)
            self.update_player_stats()
            self.update_discoveries_table()
            self.update_wiki_tab()
            extra = ""
            if thermo.get("is_exothermic"):
                extra += "\n🔥 این واکنش گرمازا است."
            elif thermo.get("is_endothermic"):
                extra += "\n❄️ این واکنش گرماگیر است."
            if lim:
                extra += f"\n⚖️ ماده محدودکننده: {CHEMILAB_DB.get(normalize_key(lim), {}).get('name', lim)}"
            QMessageBox.information(
                self, "کشف!",
                f"تبریک! شما واکنش جدیدی کشف کردید:\n{name}\nامتیاز کسب شده: {xp}{extra}")
            self.timer.start(60)

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
        try:
            plain = re.sub(r'<[^>]+>', '', str(msg))
            get_logger().info(plain)
        except Exception:
            pass

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


    def _on_datasheet_double_click(self, row, col):
        meta = getattr(self, "_datasheet_row_meta", None) or []
        if 0 <= row < len(meta):
            formula, name = meta[row]
            self.open_molecule_3d(formula, name)

    def _on_contents_double_click(self, row, col):
        meta = getattr(self, "_contents_row_meta", None) or []
        if 0 <= row < len(meta):
            formula, name = meta[row]
            self.open_molecule_3d(formula, name)

    def open_molecule_3d(self, formula, name=None):
        """نمایش ۳بعدی برای هر ماده/ترکیب — ساختار دقیق یا تقریبی خودکار."""
        try:
            formula = (formula or "").strip()
            if not formula or formula in ("?", "-", "Mix"):
                QMessageBox.information(self, "۳بعدی", "فرمول معتبری برای نمایش نیست.")
                return
            name = name or formula
            st = None
            try:
                st = MolecularStructureDB.get(formula)
            except Exception:
                st = None
            if not st:
                try:
                    st = MolecularStructureDB.synthetic(formula)
                except Exception as e:
                    tlog(f"synthetic structure fail: {e}", "WARN")
                    st = None
            if not st:
                # fallback minimal sphere model for any formula
                try:
                    from types import SimpleNamespace
                    atoms = []
                    # crude parse: element tokens
                    import re as _re
                    toks = _re.findall(r"[A-Z][a-z]?\d*", formula)
                    x = 0.0
                    for t in toks[:24]:
                        m = _re.match(r"([A-Z][a-z]?)(\d*)", t)
                        if not m:
                            continue
                        el, n = m.group(1), int(m.group(2) or 1)
                        for _ in range(min(n, 6)):
                            atoms.append({"el": el, "x": x, "y": 0.0, "z": 0.0})
                            x += 1.2
                    if not atoms:
                        atoms = [{"el": "C", "x": 0, "y": 0, "z": 0}]
                    st = {"atoms": atoms, "bonds": [], "formula": formula, "name": name}
                except Exception:
                    QMessageBox.information(self, "۳بعدی", f"نتوانستیم مدلی برای {name} بسازیم.")
                    return
            smiles = ""
            try:
                for _k, _d in CHEMILAB_DB.items():
                    if normalize_chem_formula(_d.get("formula", "")) == normalize_chem_formula(formula):
                        smiles = str(_d.get("smiles", "") or "")
                        if smiles:
                            break
                smiles = smiles or resolve_molecular_smiles(formula) or ""
            except Exception:
                smiles = ""
            title = f"{name} — {formula}" + (f"  |  {smiles}" if smiles else "")
            dlg = MplMolecule3DDialog(structure=st, title=title, parent=self)
            dlg.exec()
        except Exception as e:
            QMessageBox.warning(self, "خطا", f"نمایش ۳بعدی ممکن نشد:\n{e}")

    def show_selected_molecule_3d(self):
        """مادهٔ انتخاب‌شده در کمبو — برای همه مواد."""
        try:
            k = self.combo_chem.currentData() if hasattr(self, "combo_chem") else None
            if not k:
                # تلاش از متن کمبو
                txt = self.combo_chem.currentText() if hasattr(self, "combo_chem") else ""
                for key, val in CHEMILAB_DB.items():
                    if val.get("name") and val["name"] in txt:
                        k = key
                        break
            if not k or k not in CHEMILAB_DB:
                QMessageBox.information(self, "۳بعدی", "ابتدا یک ماده از لیست انتخاب کنید.")
                return
            d = CHEMILAB_DB[k]
            formula = d.get("formula") or k
            name = d.get("name") or formula
            self.open_molecule_3d(formula, name)
        except Exception as e:
            QMessageBox.warning(self, "۳بعدی", f"خطا در باز کردن مدل:\n{e}")

    def show_mixture_molecule_3d(self):
        """۳بعدی برای اولین لایهٔ ظرف."""
        layers = getattr(self.engine, "visual_layers", None) or []
        if not layers:
            QMessageBox.information(self, "۳بعدی مخلوط", "ظرف خالی است. اول ماده اضافه کنید.")
            return
        layer = layers[0]
        key = layer.get("key")
        f = CHEMILAB_DB.get(key, {}).get("formula") if key else None
        f = f or layer.get("formula") or key or "?"
        name = layer.get("name") or f
        self.open_molecule_3d(f, name)

    def populate_chemicals(self):
        if getattr(self, "is_admin", False):
            return
        self.combo_chem.clear()
        for k, v in sorted(CHEMILAB_DB.items(), key=lambda x: x[1]['name']):
            self.combo_chem.addItem(f"{v['name']} ({v['formula']})", k)

    def filter_chemicals(self, text):
        self.combo_chem.blockSignals(True)
        self.combo_chem.clear()
        t = text.lower()
        cat = self.combo_filter.currentText()
        eng_cat = {
            "اسید": "Acid", "باز": "Base", "نمک": "Salt", "گاز": "Gas",
            "جامد": "Solid", "مایع": "Liquid", "اسید قوی": "Strong Acid",
            "باز قوی": "Strong Base", "رسوب": "Precipitate", "اکسید": "Oxide", "عنصر": "Element"
        }.get(cat, "")
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
            if hasattr(self, 'lbl_d_state'):
                self.lbl_d_state.setText(str(d.get('state', 'جامد')))
            if hasattr(self, 'lbl_d_hazard'):
                self.lbl_d_hazard.setText(str(d.get('hazard', 'کم‌خطر')))
            self.spin_molarity.setValue(float(d.get('molarity', 0.1)))

    def _update_live_hints(self):
        if getattr(self, "is_admin", False):
            return
        if hasattr(self, 'lbl_active_mission'):
            next_m = None
            for m in self.engine.missions:
                if m['id'] not in self.engine.completed_missions:
                    next_m = m
                    break
            if next_m:
                self.lbl_active_mission.setText(f"🎯 مأموریت بعدی: {next_m['title']} — {next_m['desc']}")
            else:
                self.lbl_active_mission.setText("🎯 همه مأموریت‌ها تکمیل شد!")
        if hasattr(self, 'lbl_suggested_rxn'):
            present = set()
            for k, v in self.engine.contents.items():
                if v > 1e-12:
                    present.add(normalize_key(k))
            tips = []
            for name, rxn in CUSTOM_REACTIONS.items():
                if name in self.engine.discovered:
                    continue
                needed = {normalize_key(r) for r in rxn.get("reactants", [])}
                if not needed:
                    continue
                have = needed & present
                missing = needed - present
                if have and missing:
                    miss_names = []
                    for mkey in missing:
                        miss_names.append(CHEMILAB_DB.get(mkey, {}).get('name', mkey))
                    tips.append(f"نزدیک به «{name}» — کم دارید: {', '.join(miss_names[:3])}")
                elif needed.issubset(present):
                    tips.append(f"آماده: «{name}» — شرایط را بررسی کنید")
            if tips:
                self.lbl_suggested_rxn.setText("💡 " + tips[0])
            elif not present:
                self.lbl_suggested_rxn.setText("💡 ماده اضافه کنید تا پیشنهاد واکنش ببینید")
            else:
                self.lbl_suggested_rxn.setText("💡 واکنش شناخته‌شده‌ای برای این ترکیب پیشنهاد نشد")

    def game_loop(self):
        try:
            if self.is_admin:
                return
            if not hasattr(self, '_frame_i'):
                self._frame_i = 0
            self._frame_i += 1
            fi = self._frame_i

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
                        if fi % 12 == 0:
                            self.update_contents_ui()

            self.engine.update_physics()
            if self.engine.is_broken and not getattr(self, '_broke_logged', False):
                self._broke_logged = True
                self._log("💥 دما بیش از حد بالا رفت و ظرف ترکید! سریعاً آن را تعویض کنید.")
                try:
                    QApplication.beep()
                except Exception:
                    pass
            elif not self.engine.is_broken:
                self._broke_logged = False

            if not hasattr(self, 'st'):
                self.st = time.time()
            t = time.time() - self.st
            ph = self.engine.get_ph()
            temp = self.engine.temp_c

            if not hasattr(self, '_eq_cross_count'):
                self._eq_cross_count = 0
            if not hasattr(self, '_eq_near_frames'):
                self._eq_near_frames = 0
            crossed = False
            if self.btn_titrate.isChecked():
                jumped = (self.last_ph < 5.5 and ph > 8.5) or (self.last_ph > 8.5 and ph < 5.5)
                near7 = 6.2 <= ph <= 7.8
                approaching = near7 and abs(ph - 7.0) <= abs(self.last_ph - 7.0) + 0.05
                if jumped:
                    self._eq_cross_count += 2
                elif approaching:
                    self._eq_cross_count += 1
                    self._eq_near_frames += 1
                else:
                    self._eq_cross_count = max(0, self._eq_cross_count - 1)
                    self._eq_near_frames = max(0, self._eq_near_frames - 1)
                if self._eq_cross_count >= 4 and (jumped or self._eq_near_frames >= 3):
                    crossed = True
                    self._eq_cross_count = 0
                    self._eq_near_frames = 0
            if crossed:
                vol = self.engine.titration_volume
                self.engine.last_titration_endpoint_vol = vol
                titrant_M = self.spin_molarity.value() if hasattr(self, 'spin_molarity') else 0.1
                analyte_vol_ml = max(
                    1.0,
                    safe_float(getattr(self.engine, "_titration_initial_volume", None),
                               max(1.0, self.engine.total_volume - vol)),
                )
                # Educational 1:1 endpoint assumption: C_a V_a = C_t V_t.
                approx_conc = (titrant_M * (vol / 1000.0)) / (analyte_vol_ml / 1000.0)
                self.engine.titration_analyte_conc = approx_conc
                bonus_xp = 25
                self.engine.score += bonus_xp
                self._log(
                    f"✅ نقطه هم‌ارزی تیتراسیون فرا رسید! "
                    f"حجم مصرفی بورت: {vol:.1f} mL | "
                    f"غلظت تقریبی آنالیت: {approx_conc:.3g} M | "
                    f"+{bonus_xp} XP ویژه")
                self.btn_titrate.setChecked(False)
                self.action_toggle_titration()
                self.engine.stats["successful_titrations"] += 1
                if hasattr(self, 'lbl_titration_status'):
                    self.lbl_titration_status.setText(
                        f"✅ کامل — V={vol:.1f}mL | C≈{approx_conc:.3g}M")
                try:
                    QApplication.beep()
                except Exception:
                    pass
                QMessageBox.information(
                    self, "تیتراسیون موفق",
                    f"نقطه پایانی تشخیص داده شد!\n\n"
                    f"حجم تیترانت مصرفی: {vol:.2f} mL\n"
                    f"غلظت تقریبی آنالیت: {approx_conc:.4g} M\n"
                    f"امتیاز ویژه: +{bonus_xp} XP")
                self.update_player_stats()
            self.last_ph = ph

            self.lbl_ph_display.setText(f"pH: {ph:.2f}" if not self.engine.is_broken else "pH: ---")
            self.lbl_temp_display.setText(f"{temp:.1f} °C")

            if fi % 30 == 0:
                self._update_safety_status()
                self._update_undo_redo_labels()

            if fi % 12 == 0:
                achv = self.engine.check_missions_and_badges()
                if achv:
                    self.update_missions_ui()
                    self.update_player_stats()
                    if achv.get('type') == 'multi':
                        titles = [it.get('title', '') for it in achv.get('items', [])]
                        t_str = "دستاوردهای جدید!"
                        self._log(f"🏅 {t_str}: " + "، ".join(titles))
                        try:
                            QTimer.singleShot(0, lambda titles=titles: QMessageBox.information(
                                self, "دستاوردهای جدید", "شما کسب کردید:\n• " + "\n• ".join(titles)))
                        except Exception as e:
                            tlog(f"achv multi ui: {e}", "WARN")
                    else:
                        t_str = "دستاورد جدید!" if achv.get('type') == 'badge' else "مأموریت تکمیل شد!"
                        self._log(f"🏅 {t_str}: {achv.get('title', '')}")
                        try:
                            QTimer.singleShot(0, lambda a=achv, t=t_str: QMessageBox.information(
                                self, t, f"شما '{a.get('title', '')}' را کسب کردید!"))
                        except Exception as e:
                            tlog(f"achv ui: {e}", "WARN")

            if fi % 12 == 0:
                disc = self.engine.check_reactions()
                self.handle_reaction_result(disc)

            if fi % 90 == 0:
                self.update_report_card()
            if fi % 120 == 0:
                try:
                    self.engine.save_data()
                except Exception:
                    pass

            graph_tab_active = False
            try:
                graph_tab_active = hasattr(self, 'tabs') and hasattr(self, 'canvas') and self.tabs.currentWidget() is getattr(self, 'graph_tab_widget', None)
            except Exception:
                graph_tab_active = False

            if self.engine.speed_multiplier > 0:
                # داده در هر تیک ثبت می‌شود؛ رسم فقط وقتی لازم است انجام می‌شود تا UI روان بماند.
                self.data_time.append(t)
                self.data_ph.append(ph)
                self.data_temp.append(temp)
                if len(self.data_time) > 120:
                    self.data_time.pop(0)
                    self.data_ph.pop(0)
                    self.data_temp.pop(0)
                self.line_ph.set_data(self.data_time, self.data_ph)
                self.line_temp.set_data(self.data_time, self.data_temp)
                try:
                    if hasattr(self, "eq_line"):
                        self.eq_line.set_alpha(0.85 if self.btn_titrate.isChecked() else 0.0)
                except Exception:
                    pass
                if graph_tab_active:
                    try:
                        self._refresh_graph()
                        # QTimer/Qt redraw را coalesce می‌کند و از draw() سنگین‌تر جلوگیری می‌شود.
                        self.graph_canvas.draw_idle()
                    except Exception:
                        pass

            if fi % 40 == 0:
                try:
                    self._update_live_hints()
                except Exception:
                    pass
        except Exception as e:
            try:
                tlog(f"game_loop error: {e}", "ERROR")
            except Exception:
                print(f"[ERROR] game_loop: {e}", flush=True)

try:
    MolecularStructureDB.load_from_sqlite()
except Exception:
    pass

if __name__ == '__main__':
    # Desktop OpenGL اجباری — قبل از QApplication (جلوگیری از ANGLE/سیاه)
    try:
        from PySide6.QtCore import Qt as _QtGL, QCoreApplication
        # High-DPI قبل از ساخت QApplication تا viewport و mouse deltas هماهنگ بمانند.
        try:
            QCoreApplication.setAttribute(
                _QtGL.HighDpiScaleFactorRoundingPolicy.PassThrough, True
            )
        except Exception:
            pass
        QApplication.setAttribute(_QtGL.AA_UseDesktopOpenGL, True)
        try:
            QApplication.setAttribute(_QtGL.AA_ShareOpenGLContexts, False)
        except Exception:
            pass
    except Exception as e:
        print(f"[GL] Desktop OpenGL attributes: {e}", flush=True)
    try:
        configure_opengl_compatibility()
    except Exception as e:
        print(f"[GL] configure before app: {e}", flush=True)
    app = QApplication(sys.argv)
    app.setLayoutDirection(Qt.RightToLeft)
    app.setFont(QFont(FONT_NAME, 10))
    app.setStyleSheet(APP_STYLE_DARK)
    print(f"[APP] {APP_NAME} {APP_VERSION} | OpenGL={HAS_OPENGL} | molmass={HAS_MOLMASS}", flush=True)

    while True:
        name = None
        is_admin = False
        sess = load_active_session()
        if sess and not sess.get("is_admin"):
            name = str(sess.get("player_name") or "").strip()
            is_admin = False
        if not name:
            login = LoginDialog()
            if login.exec() != QDialog.Accepted:
                sys.exit(0)
            name = login.get_name()
            is_admin = login.is_admin()
        if not is_admin:
            save_active_session(name, is_admin=False)
        else:
            clear_active_session()  # ادمین همیشه با رمز وارد شود
        w = ModernLabWindow(player_name=name, is_admin=is_admin)
        w.show()
        app.exec()
        if getattr(w, "_logout_requested", False):
            try:
                w.deleteLater()
            except Exception:
                pass
            continue
        break
    sys.exit(0)

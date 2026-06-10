import sys
import time
import random
import math
import re
import json
import os
from collections import Counter

try:
    import matplotlib

    # تغییر برای سازگاری با ویندوز 7 و PyQt5
    matplotlib.use("Qt5Agg")

    from PyQt5.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QLabel, QPushButton, QComboBox, QFrame, QGroupBox, QTextEdit,
        QTabWidget, QMessageBox, QDoubleSpinBox, QFormLayout, QTableWidget,
        QTableWidgetItem, QHeaderView, QSplitter, QLineEdit, QGridLayout,
        QListWidget, QSpinBox, QProgressBar, QSizePolicy, QSlider
    )
    from PyQt5.QtCore import Qt, QTimer, QRectF, QPropertyAnimation, pyqtProperty, QEasingCurve, QRect
    from PyQt5.QtGui import QFont, QColor, QPainter, QBrush, QPen, QLinearGradient, QPainterPath

    from matplotlib.figure import Figure
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
except ImportError as e:
    print(f"Error: {e}")
    print("Please install required libraries: pip install PyQt5 matplotlib")
    sys.exit(1)

# ----------------- تنظیمات -----------------
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
"""

PERIODIC_TABLE = {
    "H": "هیدروژن", "He": "هلیوم", "Li": "لیتیوم", "Be": "بریلیم", "B": "بور", "C": "کربن", "N": "نیتروژن",
    "O": "اکسیژن",
    "F": "فلوئور", "Ne": "نئون", "Na": "سدیم", "Mg": "منیزیم", "Al": "آلومینیوم", "Si": "سیلیسیم", "P": "فسفر",
    "S": "گوگرد",
    "Cl": "کلر", "Ar": "آرگون", "K": "پتاسیم", "Ca": "کلسیم", "Fe": "آهن", "Cu": "مس", "Zn": "روی", "Ag": "نقره",
    "Au": "طلا",
    "Hg": "جیوه", "Pb": "سرب", "Sn": "قلع", "Mn": "منگنز", "Cr": "کروم", "Ni": "نیکل", "Co": "کبالت", "Br": "برم",
    "I": "ید"
}


def normalize_key(key):
    key = re.sub(
        r'\s+(heat|light|conc|dilute|steam|aq|excess|limited|slow|cold|hot|dissolved|decay|solid|liquid|gas|catalyst).*',
        '', key, flags=re.IGNORECASE)
    return key.strip().lower()


# دیتابیس‌های خالی اولیه (بعداً پر می‌شوند)
CHEMICAL_DB = {
    "h2so4": {"name": "سولفوریک اسید", "formula": "H2SO4", "type": "Strong Acid", "pH": 1.0, "molarity": 0.1,
              "heat": -88.0, "color": "#FFFFFF"},
    "naoh": {"name": "سدیم هیدروکسید", "formula": "NaOH", "type": "Strong Base", "pH": 13.0, "molarity": 0.1,
             "heat": -44.5, "color": "#FFFFFF"},
    "hcl": {"name": "هیدروکلریک اسید", "formula": "HCl", "type": "Strong Acid", "pH": 1.1, "molarity": 0.1,
            "heat": -74.8, "color": "#F0F8FF"},
    "c2h4": {"name": "اتیلن", "formula": "C2H4", "type": "Gas", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
             "color": "#FFFFFF"},
    "o2": {"name": "اکسیژن", "formula": "O2", "type": "Gas", "pH": 7.0, "molarity": 0.01, "heat": 0.0,
           "color": "#FFFFFF"},
    "h2o": {"name": "آب", "formula": "H2O", "type": "Solvent", "pH": 7.0, "molarity": 55.5, "heat": 0.1,
            "color": "#E0FFFF"},
    "fe": {"name": "آهن", "formula": "Fe", "type": "Metal", "pH": 7.0, "molarity": 1.0, "heat": 0.0,
           "color": "#808080"},
    "s": {"name": "گوگرد", "formula": "S", "type": "Element", "pH": 7.0, "molarity": 1.0, "heat": 0.0,
          "color": "#FFFF00"},
    "ch4": {"name": "متان", "formula": "CH4", "type": "Gas", "pH": 7.0, "molarity": 0.1, "heat": -12.9,
            "color": "#F0F8FF"},
    "n2": {"name": "نیتروژن", "formula": "N2", "type": "Gas", "pH": 7.0, "molarity": 0.01, "heat": 0.0,
           "color": "#FFFFFF"},
    "nh3": {"name": "آمونیاک", "formula": "NH3", "type": "Weak Base", "pH": 11.1, "molarity": 0.1, "heat": -34.0,
            "color": "#FDF5E6"},
    "cuso4": {"name": "مس(II) سولفات", "formula": "CuSO4", "type": "Salt", "pH": 4.0, "molarity": 0.1, "heat": -66.0,
              "color": "#0000FF"},
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
    "k2cr2o7": {"name": "پتاسیم دی‌کرومات", "formula": "K2Cr2O7", "type": "Salt", "pH": 4.0, "molarity": 0.1,
                "heat": 75.0, "color": "#FF8C00"},
    "ch3cooh": {"name": "استیک اسید", "formula": "CH3COOH", "type": "Weak Acid", "pH": 2.9, "molarity": 0.1,
                "heat": -0.4, "color": "#F8F8FF"},
    "caco3": {"name": "کلسیم کربنات", "formula": "CaCO3", "type": "Salt", "pH": 9.4, "molarity": 0.1, "heat": -12.0,
              "color": "#FFFAF0"},
    "fecl3": {"name": "آهن(III) کلرید", "formula": "FeCl3", "type": "Salt", "pH": 2.0, "molarity": 0.1, "heat": -48.0,
              "color": "#B8860B"},
    "zn": {"name": "روی", "formula": "Zn", "type": "Metal", "pH": 7.0, "molarity": 1.0, "heat": 0.0,
           "color": "#808080"},
    "bacl2": {"name": "باریم کلرید", "formula": "BaCl2", "type": "Salt", "pH": 6.0, "molarity": 0.1, "heat": 8.8,
              "color": "#FFFFFF"},
    "na2so4": {"name": "سدیم سولفات", "formula": "Na2SO4", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 1.2,
               "color": "#FFFFFF"},
    "(nh4)2cr2o7": {"name": "آمونیوم دی‌کرومات", "formula": "(NH4)2Cr2O7", "type": "Salt", "pH": 4.0, "molarity": 0.1,
                    "heat": 75.0, "color": "#FF8C00"},
    "nahco3": {"name": "سدیم بی‌کربنات", "formula": "NaHCO3", "type": "Salt", "pH": 8.3, "molarity": 0.1, "heat": 18.7,
               "color": "#FFFFFF"},
    "c3h8": {"name": "پروپان", "formula": "C3H8", "type": "Gas", "pH": 7.0, "molarity": 0.01, "heat": 0.0,
             "color": "#FFFFFF"},
    "hno3": {"name": "نیتریک اسید", "formula": "HNO3", "type": "Strong Acid", "pH": 1.0, "molarity": 0.1, "heat": -33.3,
             "color": "#FFFFE0"},
    "cacl2": {"name": "کلسیم کلرید", "formula": "CaCl2", "type": "Salt", "pH": 7.5, "molarity": 0.1, "heat": -81.3,
              "color": "#FFFFFF"},
    "na3po4": {"name": "تری‌سدیم فسفات", "formula": "Na3PO4", "type": "Base", "pH": 12.0, "molarity": 0.1,
               "heat": -64.0, "color": "#FFFFFF"},
    "nh4cl": {"name": "آمونیوم کلرید", "formula": "NH4Cl", "type": "Salt", "pH": 4.6, "molarity": 0.1, "heat": 14.8,
              "color": "#FFFFFF"},
    "na": {"name": "سدیم", "formula": "Na", "type": "Metal", "pH": 7.0, "molarity": 1.0, "heat": 0.0,
           "color": "#C0C0C0"},
    "cl2": {"name": "کلر", "formula": "Cl2", "type": "Gas", "pH": 3.0, "molarity": 0.1, "heat": -25.0,
            "color": "#ADFF2F"},
    "zncl2": {"name": "روی کلرید", "formula": "ZnCl2", "type": "Salt", "pH": 4.0, "molarity": 0.1, "heat": -15.6,
              "color": "#FFFFFF"},
    "so3": {"name": "گوگرد تری‌اکسید", "formula": "SO3", "type": "Oxide", "pH": 1.0, "molarity": 0.1, "heat": -90.0,
            "color": "#FFFFFF"},
    "k2cro4": {"name": "پتاسیم کرومات", "formula": "K2CrO4", "type": "Salt", "pH": 8.5, "molarity": 0.1, "heat": 14.5,
               "color": "#FFFF00"},
    "h2c2o4": {"name": "اگزالیک اسید", "formula": "H2C2O4", "type": "Weak Acid", "pH": 1.3, "molarity": 0.1,
               "heat": 9.5, "color": "#FFFFFF"},
    "nabr": {"name": "سدیم برومید", "formula": "NaBr", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": -0.6,
             "color": "#FFFFFF"},
    "ca3p2": {"name": "کلسیم فسفید", "formula": "Ca3P2", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
              "color": "#8B4513"},
    "na2co3": {"name": "سدیم کربنات", "formula": "Na2CO3", "type": "Salt", "pH": 11.6, "molarity": 0.1, "heat": -24.0,
               "color": "#FFFFFF"},
    "c5h12": {"name": "پنتان", "formula": "C5H12", "type": "Alkane", "pH": 7.0, "molarity": 0.1, "heat": -0.5,
              "color": "#FFFFFF"},
    "niso4": {"name": "نیکل(II) سولفات", "formula": "NiSO4", "type": "Salt", "pH": 4.5, "molarity": 0.1, "heat": -80.0,
              "color": "#7FFF00"},
    "nan3": {"name": "سدیم آزید", "formula": "NaN3", "type": "Salt", "pH": 10.0, "molarity": 0.1, "heat": 21.0,
             "color": "#FFFFFF"},
    "na2so3": {"name": "سدیم سولفیت", "formula": "Na2SO3", "type": "Salt", "pH": 9.5, "molarity": 0.1, "heat": -11.0,
               "color": "#FFFFFF"},
    "c6h14": {"name": "هگزان", "formula": "C6H14", "type": "Alkane", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
              "color": "#FFFFFF"},
    "fes": {"name": "آهن(II) سولفید", "formula": "FeS", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
            "color": "#000000"},
    "naf": {"name": "سدیم فلورید", "formula": "NaF", "type": "Salt", "pH": 7.5, "molarity": 0.1, "heat": 0.9,
            "color": "#FFFFFF"},
    "h3po4": {"name": "فسفریک اسید", "formula": "H3PO4", "type": "Weak Acid", "pH": 1.5, "molarity": 0.1, "heat": -11.7,
              "color": "#F8F8FF"},
    "c8h18": {"name": "اوکتان", "formula": "C8H18", "type": "Alkane", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
              "color": "#FFFFFF"},
    "kscn": {"name": "پتاسیم تیوسیانات", "formula": "KSCN", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 24.0,
             "color": "#FFFFFF"},
    "mno2": {"name": "منگنز دی‌اکسید", "formula": "MnO2", "type": "Oxide", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
             "color": "#2F4F4F"},
    "mnso4": {"name": "منگنز(II) سولفات", "formula": "MnSO4", "type": "Salt", "pH": 5.0, "molarity": 0.1, "heat": -62.0,
              "color": "#FFC0CB"},
    "c6h6": {"name": "بنزن", "formula": "C6H6", "type": "Hydrocarbon", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
             "color": "#FFFFFF"},
    "na2sio3": {"name": "سدیم سیلیکات", "formula": "Na2SiO3", "type": "Base", "pH": 12.5, "molarity": 0.1,
                "heat": -32.0, "color": "#F5F5F5"},
    "cocl2": {"name": "کبالت کلرید", "formula": "CoCl2", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
              "color": "#FF00FF"},
    "cu": {"name": "مس", "formula": "Cu", "type": "Metal", "pH": 7.0, "molarity": 1.0, "heat": 0.0, "color": "#B87333"},
    "h3bo3": {"name": "بوریک اسید", "formula": "H3BO3", "type": "Weak Acid", "pH": 5.1, "molarity": 0.1, "heat": 21.8,
              "color": "#F0FFFF"},
    "c7h8": {"name": "تولوئن", "formula": "C7H8", "type": "Hydrocarbon", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
             "color": "#FFFFFF"},
    "crcl3": {"name": "کروم(III) کلرید", "formula": "CrCl3", "type": "Salt", "pH": 2.5, "molarity": 0.1, "heat": -50.0,
              "color": "#4B0082"},
    "nh4no3": {"name": "آمونیوم نیترات", "formula": "NH4NO3", "type": "Salt", "pH": 4.8, "molarity": 0.1, "heat": 25.7,
               "color": "#FFFFFF"},
    "br2": {"name": "بروم", "formula": "Br2", "type": "Liquid", "pH": 3.5, "molarity": 0.1, "heat": -5.0,
            "color": "#A52A2A"},
    "c8h10": {"name": "زایلن", "formula": "C8H10", "type": "Hydrocarbon", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
              "color": "#FFFFFF"},
    "cdso4": {"name": "کادمیوم سولفات", "formula": "CdSO4", "type": "Salt", "pH": 5.0, "molarity": 0.1, "heat": -55.0,
              "color": "#FFFFFF"},
    "as": {"name": "آرسنیک", "formula": "As", "type": "Element", "pH": 7.0, "molarity": 1.0, "heat": 0.0,
           "color": "#808080"},
    "c6h5oh": {"name": "فنول", "formula": "C6H5OH", "type": "Weak Acid", "pH": 6.0, "molarity": 0.1, "heat": 12.5,
               "color": "#FFF5EE"},
    "srcl2": {"name": "استرانسیم کلرید", "formula": "SrCl2", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": -31.0,
              "color": "#FFFFFF"},
    "ch3i": {"name": "متیل یدید", "formula": "CH3I", "type": "Organic", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
             "color": "#FFFFFF"},
    "c3h6o3": {"name": "لاکتیک اسید", "formula": "C3H6O3", "type": "Weak Acid", "pH": 2.4, "molarity": 0.1,
               "heat": -8.0, "color": "#FFFACD"},
    "c6h5nh2": {"name": "آنیلین", "formula": "C6H5NH2", "type": "Weak Base", "pH": 8.8, "molarity": 0.1, "heat": 1.9,
                "color": "#F5DEB3"},
    "khco3": {"name": "پتاسیم بی‌کربنات", "formula": "KHCO3", "type": "Salt", "pH": 8.2, "molarity": 0.1, "heat": 0.0,
              "color": "#FFFFFF"},
    "sn": {"name": "قلع", "formula": "Sn", "type": "Metal", "pH": 7.0, "molarity": 1.0, "heat": 0.0,
           "color": "#C0C0C0"},
    "c5h5n": {"name": "پیریدین", "formula": "C5H5N", "type": "Weak Base", "pH": 8.5, "molarity": 0.1, "heat": -20.0,
              "color": "#FFFFF0"},
    "c4h4o4": {"name": "مالئیک اسید", "formula": "C4H4O4", "type": "Weak Acid", "pH": 1.9, "molarity": 0.1,
               "heat": 18.5, "color": "#FFFFFF"},
    "c7h16": {"name": "هپتان", "formula": "C7H16", "type": "Hydrocarbon", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
              "color": "#FFFFFF"},
    "c10h22": {"name": "دکان", "formula": "C10H22", "type": "Alkane", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
               "color": "#FFFFFF"},
    "cd(no3)2": {"name": "کادمیوم نیترات", "formula": "Cd(NO3)2", "type": "Salt", "pH": 5.0, "molarity": 0.1,
                 "heat": 0.0, "color": "#FFFFFF"},
    "bao2": {"name": "باریم پراکسید", "formula": "BaO2", "type": "Oxidizer", "pH": 12.0, "molarity": 0.1, "heat": 0.0,
             "color": "#FFFFFF"},
    "c4h6o4": {"name": "سوکینیک اسید", "formula": "C4H6O4", "type": "Weak Acid", "pH": 2.7, "molarity": 0.1,
               "heat": 27.0, "color": "#FFFFFF"},
    "c6h12": {"name": "سیکلوهگزان", "formula": "C6H12", "type": "Alkane", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
              "color": "#FFFFFF"},
    "k2o2": {"name": "پتاسیم پراکسید", "formula": "K2O2", "type": "Oxidizer", "pH": 13.0, "molarity": 0.1, "heat": 0.0,
             "color": "#FFA500"},
    "p": {"name": "فسفر", "formula": "P", "type": "Element", "pH": 7.0, "molarity": 1.0, "heat": 0.0,
          "color": "#8B0000"},
    "methyl methacrylate": {"name": "متیل متاکریلات", "formula": "C5H8O2", "type": "Monomer", "pH": 7.0,
                            "molarity": 0.1, "heat": 0.0, "color": "#FFFFFF"},
    "cao": {"name": "کلسیم اکسید", "formula": "CaO", "type": "Oxide", "pH": 12.0, "molarity": 0.1, "heat": -60.0,
            "color": "#FFFFFF"},
    "c": {"name": "کربن", "formula": "C", "type": "Element", "pH": 7.0, "molarity": 1.0, "heat": 0.0,
          "color": "#000000"},
    "c6h4(oh)cooh": {"name": "سالیسیلیک اسید", "formula": "C7H6O3", "type": "Acid", "pH": 3.0, "molarity": 0.1,
                     "heat": 0.0, "color": "#FFFFFF"},
    "c10h16": {"name": "ترپنتین (کاج)", "formula": "C10H16", "type": "Organic", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
               "color": "#FFFFE0"},
    "na2s2o3": {"name": "سدیم تیوسولفات", "formula": "Na2S2O3", "type": "Salt", "pH": 7.5, "molarity": 0.1, "heat": 7.3,
                "color": "#FFFFFF"},
    "c6h13oh": {"name": "هگزانول", "formula": "C6H13OH", "type": "Alcohol", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
                "color": "#FFFFFF"},
    "edta": {"name": "EDTA", "formula": "C10H16N2O8", "type": "Chelating Agent", "pH": 2.5, "molarity": 0.1,
             "heat": 0.0, "color": "#FFFFFF"},
    "nano2": {"name": "سدیم نیتریت", "formula": "NaNO2", "type": "Salt", "pH": 9.0, "molarity": 0.1, "heat": 13.9,
              "color": "#FFFACD"},
    "c4h9cooh": {"name": "والریک اسید", "formula": "C5H10O2", "type": "Acid", "pH": 4.8, "molarity": 0.1, "heat": 0.0,
                 "color": "#FFFFFF"},
    "c9h20": {"name": "نونان", "formula": "C9H20", "type": "Alkane", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
              "color": "#FFFFFF"},
    "hf": {"name": "هیدروفلوئوریک اسید", "formula": "HF", "type": "Weak Acid", "pH": 2.1, "molarity": 0.1,
           "heat": -13.0, "color": "#FFFFFF"},
    "k2s2o8": {"name": "پتاسیم پرسولفات", "formula": "K2S2O8", "type": "Oxidizer", "pH": 5.0, "molarity": 0.1,
               "heat": 0.0, "color": "#FFFFFF"},
    "as2o3": {"name": "آرسنیک تری‌اکسید", "formula": "As2O3", "type": "Oxide", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
              "color": "#FFFFFF"},
    "c12h26": {"name": "دودکان", "formula": "C12H26", "type": "Alkane", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
               "color": "#FFFFFF"},
    "bi(no3)3": {"name": "بیسموت نیترات", "formula": "Bi(NO3)3", "type": "Salt", "pH": 1.0, "molarity": 0.1,
                 "heat": 0.0, "color": "#FFFFFF"},
    "na2o2": {"name": "سدیم پراکسید", "formula": "Na2O2", "type": "Oxidizer", "pH": 12.0, "molarity": 0.1,
              "heat": -50.0, "color": "#FFFFE0"},
    "c5h11cooh": {"name": "کاپروئیک اسید", "formula": "C6H12O2", "type": "Acid", "pH": 4.8, "molarity": 0.1,
                  "heat": 0.0, "color": "#FFFFFF"},
    "c5h10": {"name": "سیکلوپنتان", "formula": "C5H10", "type": "Alkane", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
              "color": "#FFFFFF"},
    "ca(no3)2": {"name": "کلسیم نیترات", "formula": "Ca(NO3)2", "type": "Salt", "pH": 6.0, "molarity": 0.1, "heat": 0.0,
                 "color": "#FFFFFF"},
    "nah2po2": {"name": "سدیم هیپوفسفیت", "formula": "NaH2PO2", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
                "color": "#FFFFFF"},
    "hgcl2": {"name": "جیوه(II) کلرید", "formula": "HgCl2", "type": "Salt", "pH": 3.2, "molarity": 0.1, "heat": 14.0,
              "color": "#FFFFFF"},
    "c6h13cooh": {"name": "هپتانوئیک اسید", "formula": "C7H14O2", "type": "Acid", "pH": 4.8, "molarity": 0.1,
                  "heat": 0.0, "color": "#FFFFFF"},
    "hcho": {"name": "فرمالدئید", "formula": "HCHO", "type": "Aldehyde", "pH": 4.0, "molarity": 0.1, "heat": 0.0,
             "color": "#FFFFFF"},
    "fe2o3": {"name": "آهن(III) اکسید", "formula": "Fe2O3", "type": "Oxide", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
              "color": "#8B4513"},
    "co": {"name": "کربن مونوکسید", "formula": "CO", "type": "Gas", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
           "color": "#FFFFFF"},
    "c7h15cooh": {"name": "کاپریلیک اسید", "formula": "C8H16O2", "type": "Acid", "pH": 4.8, "molarity": 0.1,
                  "heat": 0.0, "color": "#FFFFFF"},
    "c4h8o2": {"name": "اتیل استات", "formula": "C4H8O2", "type": "Ester", "pH": 7.0, "molarity": 0.1, "heat": -10.0,
               "color": "#FFFFFF"},
    "sbcl5": {"name": "آنتیموان پنتاکلرید", "formula": "SbCl5", "type": "Salt", "pH": 1.0, "molarity": 0.1, "heat": 0.0,
              "color": "#FFFFFF"},
    "aucl3": {"name": "طلا(III) کلرید", "formula": "AuCl3", "type": "Salt", "pH": 1.5, "molarity": 0.1, "heat": 0.0,
              "color": "#FFD700"},
    "c11h23cooh": {"name": "لوریک اسید", "formula": "C12H24O2", "type": "Acid", "pH": 5.0, "molarity": 0.1, "heat": 0.0,
                   "color": "#FFFFFF"},
    "c4h10o": {"name": "دی‌اتیل اتر", "formula": "C4H10O", "type": "Ether", "pH": 7.0, "molarity": 0.1, "heat": -6.0,
               "color": "#FFFFFF"},
    "naocl": {"name": "سدیم هیپوکلریت", "formula": "NaOCl", "type": "Base", "pH": 12.0, "molarity": 0.1, "heat": -35.0,
              "color": "#FFFACD"},
    "c3h8o3": {"name": "گلیسیرین", "formula": "C3H8O3", "type": "Alcohol", "pH": 7.0, "molarity": 0.1, "heat": -5.0,
               "color": "#FFFFFF"},
    "c3h3n": {"name": "آکریلونیتریل", "formula": "C3H3N", "type": "Monomer", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
              "color": "#FFFFFF"},
    "agbr": {"name": "نقره برومید", "formula": "AgBr", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
             "color": "#FFFFE0"},
    "c13h27cooh": {"name": "میریستیک اسید", "formula": "C14H28O2", "type": "Acid", "pH": 5.0, "molarity": 0.1,
                   "heat": 0.0, "color": "#FFFFFF"},
    "c6h5cho": {"name": "بنزآلدئید", "formula": "C7H6O", "type": "Aldehyde", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
                "color": "#F5F5DC"},
    "v2o5": {"name": "وانادیوم پنتااکسید", "formula": "V2O5", "type": "Oxide", "pH": 3.0, "molarity": 0.1,
             "heat": -40.0, "color": "#FF8C00"},
    "c12h22o11": {"name": "ساکارز", "formula": "C12H22O11", "type": "Sugar", "pH": 7.0, "molarity": 0.1, "heat": 5.4,
                  "color": "#FFFFFF"},
    "c4h6": {"name": "بوتادین", "formula": "C4H6", "type": "Gas", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
             "color": "#FFFFFF"},
    "cr2o3": {"name": "کروم(III) اکسید", "formula": "Cr2O3", "type": "Oxide", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
              "color": "#008000"},
    "al": {"name": "آلومینیوم", "formula": "Al", "type": "Metal", "pH": 7.0, "molarity": 1.0, "heat": 0.0,
           "color": "#C0C0C0"},
    "c16h30o2": {"name": "پالمیتولئیک اسید", "formula": "C16H30O2", "type": "Acid", "pH": 5.0, "molarity": 0.1,
                 "heat": 0.0, "color": "#FFFFFF"},
    "c6h5ch2ch2oh": {"name": "فنیل‌اتانول", "formula": "C8H10O", "type": "Alcohol", "pH": 7.0, "molarity": 0.1,
                     "heat": 0.0, "color": "#FFFFFF"},
    "coso4": {"name": "کبالت(II) سولفات", "formula": "CoSO4", "type": "Salt", "pH": 5.0, "molarity": 0.1, "heat": -70.0,
              "color": "#FF1493"},
    "ti": {"name": "تیتانیوم", "formula": "Ti", "type": "Metal", "pH": 7.0, "molarity": 1.0, "heat": 0.0,
           "color": "#C0C0C0"},
    "c6h12o6": {"name": "گلوکز", "formula": "C6H12O6", "type": "Sugar", "pH": 7.0, "molarity": 0.1, "heat": 11.0,
                "color": "#FFFFFF"},
    "bisphenol a": {"name": "بیس‌فنول A", "formula": "C15H16O2", "type": "Organic", "pH": 7.0, "molarity": 0.1,
                    "heat": 0.0, "color": "#FFFFFF"},
    "phosgene": {"name": "فسژن", "formula": "COCl2", "type": "Gas", "pH": 3.0, "molarity": 0.1, "heat": 0.0,
                 "color": "#FFFFFF"},
    "zrcl4": {"name": "زیرکونیم کلرید", "formula": "ZrCl4", "type": "Salt", "pH": 1.0, "molarity": 0.1, "heat": 0.0,
              "color": "#FFFFFF"},
    "mg": {"name": "منیزیم", "formula": "Mg", "type": "Metal", "pH": 7.0, "molarity": 1.0, "heat": 0.0,
           "color": "#C0C0C0"},
    "c20h32o2": {"name": "آراشیدونیک اسید", "formula": "C20H32O2", "type": "Acid", "pH": 5.0, "molarity": 0.1,
                 "heat": 0.0, "color": "#FFFFFF"},
    "c9h12": {"name": "کومن", "formula": "C9H12", "type": "Hydrocarbon", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
              "color": "#FFFFFF"},
    "u-235": {"name": "اورانیوم-235", "formula": "U", "type": "Radioactive", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
              "color": "#C0C0C0"},
    "neutron": {"name": "نوترون", "formula": "n", "type": "Particle", "pH": 7.0, "molarity": 0.0, "heat": 0.0,
                "color": "#FFFFFF"},
    "alcl3": {"name": "آلومینیوم کلرید", "formula": "AlCl3", "type": "Salt", "pH": 2.4, "molarity": 0.1, "heat": -324.0,
              "color": "#FFFFF0"},
    "kcn": {"name": "پتاسیم سیانید", "formula": "KCN", "type": "Salt", "pH": 11.0, "molarity": 0.1, "heat": 11.7,
            "color": "#FFFFFF"},
    "nh4no2": {"name": "آمونیوم نیتریت", "formula": "NH4NO2", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
               "color": "#FFFFFF"},
    "p4": {"name": "فسفر سفید", "formula": "P4", "type": "Element", "pH": 7.0, "molarity": 1.0, "heat": 0.0,
           "color": "#FFFF00"},
    "no2": {"name": "نیتروژن دی‌اکسید", "formula": "NO2", "type": "Gas", "pH": 3.0, "molarity": 0.1, "heat": -15.0,
            "color": "#A52A2A"},
    "c2h2": {"name": "استیلن", "formula": "C2H2", "type": "Gas", "pH": 7.0, "molarity": 0.1, "heat": -22.0,
             "color": "#FFFFFF"},
    "znso4": {"name": "روی سولفات", "formula": "ZnSO4", "type": "Salt", "pH": 4.5, "molarity": 0.1, "heat": -77.0,
              "color": "#FFFFFF"},
    "h2s": {"name": "هیدروژن سولفید", "formula": "H2S", "type": "Weak Acid", "pH": 4.1, "molarity": 0.1, "heat": -19.7,
            "color": "#F5F5F5"},
    "cac2": {"name": "کلسیم کاربید", "formula": "CaC2", "type": "Carbide", "pH": 12.5, "molarity": 0.1, "heat": -120.0,
             "color": "#808080"},
    "c6h8o7": {"name": "اسید سیتریک", "formula": "C6H8O7", "type": "Weak Acid", "pH": 2.2, "molarity": 0.1, "heat": 6.4,
               "color": "#FFFFFF"},
    "c4h10": {"name": "بوتان", "formula": "C4H10", "type": "Gas", "pH": 7.0, "molarity": 0.1, "heat": -21.0,
              "color": "#FFFFFF"},
    "na2c2o4": {"name": "سدیم اگزالات", "formula": "Na2C2O4", "type": "Salt", "pH": 8.0, "molarity": 0.1, "heat": 15.0,
                "color": "#FFFFFF"},
    "c10h8": {"name": "نفتالین", "formula": "C10H8", "type": "Hydrocarbon", "pH": 7.0, "molarity": 0.01, "heat": 18.1,
              "color": "#FFFFFF"},
    "hexamethylenediamine": {"name": "هگزامتیلن دی‌آمین", "formula": "C6H16N2", "type": "Organic", "pH": 12.0,
                             "molarity": 0.1, "heat": 0.0, "color": "#FFFFFF"},
    "adipoyl chloride": {"name": "آدیپویل کلرید", "formula": "C6H8Cl2O2", "type": "Organic", "pH": 1.0, "molarity": 0.1,
                         "heat": 0.0, "color": "#FFFFFF"},
    "ca3p2": {"name": "کلسیم فسفید", "formula": "Ca3P2", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
              "color": "#8B4513"},
    "c3h7oh": {"name": "ایزوپروپیل الکل", "formula": "C3H8O", "type": "Alcohol", "pH": 7.0, "molarity": 0.1,
               "heat": -13.0, "color": "#FFFFFF"},
    "n2h4": {"name": "هیدرازین", "formula": "H4N2", "type": "Base", "pH": 10.5, "molarity": 0.1, "heat": -18.0,
             "color": "#FFFFFF"},
    "na2s": {"name": "سدیم سولفید", "formula": "Na2S", "type": "Base", "pH": 12.5, "molarity": 0.1, "heat": -63.0,
             "color": "#FFE4B5"},
    "c5h11oh": {"name": "آمیل الکل", "formula": "C5H12O", "type": "Alcohol", "pH": 7.0, "molarity": 0.1, "heat": -10.0,
                "color": "#FFFFFF"},
    "no": {"name": "نیتروژن مونوکسید", "formula": "NO", "type": "Gas", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
           "color": "#FFFFFF"},
    "kclo3": {"name": "پتاسیم کلرات", "formula": "KClO3", "type": "Oxidizer", "pH": 7.0, "molarity": 0.1, "heat": 41.3,
              "color": "#FFFFFF"},
    "na3po3": {"name": "سدیم فسفیت", "formula": "Na3PO3", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
               "color": "#FFFFFF"},
    "i2": {"name": "ید", "formula": "I2", "type": "Solid", "pH": 5.0, "molarity": 0.1, "heat": 20.0,
           "color": "#4B0082"},
    "c10h22": {"name": "دکان", "formula": "C10H22", "type": "Alkane", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
               "color": "#FFFFFF"},
    "c2h5cooh": {"name": "پروپیونیک اسید", "formula": "C3H6O2", "type": "Weak Acid", "pH": 3.9, "molarity": 0.1,
                 "heat": -0.7, "color": "#FDF5E6"},
    "c4h8": {"name": "بوتن", "formula": "C4H8", "type": "Gas", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
             "color": "#FFFFFF"},
    "kbr": {"name": "پتاسیم برومید", "formula": "KBr", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
            "color": "#FFFFFF"},
    "namno4": {"name": "سدیم پرمنگنات", "formula": "NaMnO4", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
               "color": "#8B008B"},
    "pcc": {"name": "پیریدینیوم کلروکرومات", "formula": "C5H5NHClCrO3", "type": "Oxidizer", "pH": 4.0, "molarity": 0.1,
            "heat": 0.0, "color": "#FFA500"},
    "c5h8": {"name": "پنتادین", "formula": "C5H8", "type": "Liquid", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
             "color": "#FFFFFF"},
    "sncl2": {"name": "قلع(II) کلرید", "formula": "SnCl2", "type": "Salt", "pH": 2.1, "molarity": 0.1, "heat": -12.0,
              "color": "#FFFFFF"},
    "c3h7cooh": {"name": "بوتریک اسید", "formula": "C4H8O2", "type": "Acid", "pH": 4.8, "molarity": 0.1, "heat": 0.0,
                 "color": "#FFFFFF"},
    "c10h16": {"name": "ترپنتین", "formula": "C10H16", "type": "Organic", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
               "color": "#FFFFFF"},
    "catalase": {"name": "کاتالاز (خون)", "formula": "Enzyme", "type": "Catalyst", "pH": 7.0, "molarity": 0.0,
                 "heat": 0.0, "color": "#FF0000"},
    "c6h13oh": {"name": "هگزانول", "formula": "C6H13OH", "type": "Alcohol", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
                "color": "#FFFFFF"},
    "c3h5n": {"name": "پروپیونیتریل", "formula": "C3H5N", "type": "Organic", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
              "color": "#FFFFFF"},
    "c2f4": {"name": "تترافلورواتیلن", "formula": "C2F4", "type": "Monomer", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
             "color": "#FFFFFF"},
    "so2": {"name": "گوگرد دی‌اکسید", "formula": "SO2", "type": "Gas", "pH": 3.0, "molarity": 0.1, "heat": -33.0,
            "color": "#FFFFFF"},
    "mg2+": {"name": "یون منیزیم", "formula": "Mg2+", "type": "Ion", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
             "color": "#FFFFFF"},
    "nh4+": {"name": "یون آمونیوم", "formula": "NH4+", "type": "Ion", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
             "color": "#FFFFFF"},
    "po4": {"name": "یون فسفات", "formula": "PO4 3-", "type": "Ion", "pH": 12.0, "molarity": 0.1, "heat": 0.0,
            "color": "#FFFFFF"},
    "u-238": {"name": "اورانیوم-238", "formula": "U", "type": "Radioactive", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
              "color": "#C0C0C0"},
    "hcho": {"name": "فرمالدئید", "formula": "HCHO", "type": "Aldehyde", "pH": 4.0, "molarity": 0.1, "heat": -62.0,
             "color": "#FFFFFF"},
    "c12h26": {"name": "دودکان", "formula": "C12H26", "type": "Alkane", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
               "color": "#FFFFFF"},
    "starch": {"name": "نشاسته", "formula": "(C6H10O5)n", "type": "Carb", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
               "color": "#FFFFFF"},
    "fat": {"name": "چربی", "formula": "Lipid", "type": "Lipid", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
            "color": "#FFFFE0"},
    "protein": {"name": "پروتئین", "formula": "Polypeptide", "type": "Protein", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
                "color": "#F0E68C"},
    "mgso4": {"name": "منیزیم سولفات", "formula": "MgSO4", "type": "Salt", "pH": 6.0, "molarity": 0.1, "heat": -91.0,
              "color": "#FFFFFF"},
    "na2hpo4": {"name": "دی‌سدیم هیدروژن فسفات", "formula": "Na2HPO4", "type": "Salt", "pH": 9.0, "molarity": 0.1,
                "heat": 0.0, "color": "#FFFFFF"},
    "ticl4": {"name": "تیتانیوم تتراکلرید", "formula": "TiCl4", "type": "Salt", "pH": 1.0, "molarity": 0.1,
              "heat": -160.0, "color": "#FFFFFF"},
    "c18h32o2": {"name": "لینولئیک اسید", "formula": "C18H32O2", "type": "Acid", "pH": 5.0, "molarity": 0.1,
                 "heat": 0.0, "color": "#FFFFFF"},
    "c6h5ch3": {"name": "تولوئن", "formula": "C7H8", "type": "Solvent", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
                "color": "#FFFFFF"},
    "c4h6": {"name": "بوتادین", "formula": "C4H6", "type": "Gas", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
             "color": "#FFFFFF"},
    "ba(no3)2": {"name": "باریم نیترات", "formula": "Ba(NO3)2", "type": "Salt", "pH": 6.0, "molarity": 0.1, "heat": 0.0,
                 "color": "#FFFFFF"},
    "c4h8": {"name": "ایزوبوتن", "formula": "C4H8", "type": "Gas", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
             "color": "#FFFFFF"},
    "kio3": {"name": "پتاسیم یدات", "formula": "KIO3", "type": "Salt", "pH": 6.5, "molarity": 0.1, "heat": 27.0,
             "color": "#FFFFFF"},
    "c3h7oh": {"name": "پروپانول", "formula": "C3H7OH", "type": "Alcohol", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
               "color": "#FFFFFF"},
    "h2": {"name": "هیدروژن", "formula": "H2", "type": "Gas", "pH": 7.0, "molarity": 0.01, "heat": 0.0,
           "color": "#FFFFFF"},
    "k2co3": {"name": "پتاسیم کربنات", "formula": "K2CO3", "type": "Base", "pH": 11.6, "molarity": 0.1, "heat": -27.6,
              "color": "#FFFFFF"},
    "kcl": {"name": "پتاسیم کلرید", "formula": "KCl", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
            "color": "#FFFFFF"},
    "k2so3": {"name": "پتاسیم سولفیت", "formula": "K2SO3", "type": "Salt", "pH": 9.0, "molarity": 0.1, "heat": -12.0,
              "color": "#FFFFFF"},
    "feso4": {"name": "آهن(II) سولفات", "formula": "FeSO4", "type": "Salt", "pH": 3.5, "molarity": 0.1, "heat": -11.7,
              "color": "#90EE90"},
    "k4[fe(cn)6]": {"name": "پتاسیم فروسیانید", "formula": "K4Fe(CN)6", "type": "Salt", "pH": 7.0, "molarity": 0.1,
                    "heat": 0.0, "color": "#FFFF00"},
    "sr(no3)2": {"name": "استرانسیم نیترات", "formula": "Sr(NO3)2", "type": "Salt", "pH": 7.0, "molarity": 0.1,
                 "heat": 20.0, "color": "#FFFFFF"},
    "air": {"name": "هوا", "formula": "N2/O2", "type": "Gas", "pH": 7.0, "molarity": 0.0, "heat": 0.0,
            "color": "#FFFFFF"},
    "c6h5cooh": {"name": "بنزوئیک اسید", "formula": "C7H6O2", "type": "Weak Acid", "pH": 2.8, "molarity": 0.1,
                 "heat": 18.0, "color": "#FFFFFF"},
    "ch3coch3": {"name": "استون", "formula": "C3H6O", "type": "Solvent", "pH": 7.0, "molarity": 0.1, "heat": -0.8,
                 "color": "#FFFFFF"},
    "c2h3cl": {"name": "وینیل کلرید", "formula": "C2H3Cl", "type": "Monomer", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
               "color": "#F0F8FF"},
    "sbcl3": {"name": "آنتیموان تریکلرید", "formula": "SbCl3", "type": "Salt", "pH": 1.5, "molarity": 0.1,
              "heat": -45.0, "color": "#F5F5F5"},
    "c18h34o2": {"name": "اولئیک اسید", "formula": "C18H34O2", "type": "Fatty Acid", "pH": 6.0, "molarity": 0.1,
                 "heat": 0.0, "color": "#FFFFF0"},
    "ch3oh": {"name": "متانول", "formula": "CH3OH", "type": "Alcohol", "pH": 7.0, "molarity": 0.1, "heat": -7.3,
              "color": "#FFFFFF"},
    "nh3 excess": {"name": "آمونیاک (اضافی)", "formula": "NH3", "type": "Weak Base", "pH": 11.5, "molarity": 0.5,
                   "heat": 0.0, "color": "#FDF5E6"},
    "(nh4)2s2o8": {"name": "آمونیوم پرسولفات", "formula": "(NH4)2S2O8", "type": "Oxidizer", "pH": 3.5, "molarity": 0.1,
                   "heat": 28.0, "color": "#FFFFFF"},
    "c8h8": {"name": "استایرن", "formula": "C8H8", "type": "Monomer", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
             "color": "#FFFFFF"},
    "po4^3-": {"name": "یون فسفات", "formula": "PO4 3-", "type": "Ion", "pH": 12.0, "molarity": 0.1, "heat": 0.0,
               "color": "#FFFFFF"},
    "molybdate": {"name": "مولیبدات", "formula": "MoO4 2-", "type": "Ion", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
                  "color": "#FFFFFF"},
    "ni2+": {"name": "یون نیکل", "formula": "Ni2+", "type": "Ion", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
             "color": "#00FF00"},
    "dmg": {"name": "دی‌متیل‌گلیوکسیم", "formula": "C4H8N2O2", "type": "Reagent", "pH": 7.0, "molarity": 0.1,
            "heat": 0.0, "color": "#FFFFFF"},
    "c20h42": {"name": "پارافین (ایکوسان)", "formula": "C20H42", "type": "Alkane", "pH": 7.0, "molarity": 0.1,
               "heat": 0.0, "color": "#FFFFFF"},
    "p4o10": {"name": "فسفر پنتااکسید", "formula": "P4O10", "type": "Acidic Oxide", "pH": 1.5, "molarity": 0.1,
              "heat": -170.0, "color": "#FFFFFF"},
    "mg2si": {"name": "منیزیم سیلیسید", "formula": "Mg2Si", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
              "color": "#4682B4"},
    "c16h32o2": {"name": "پالمیتیک اسید", "formula": "C16H32O2", "type": "Fatty Acid", "pH": 6.5, "molarity": 0.1,
                 "heat": 0.0, "color": "#FFFFFF"},
    "c2h6o": {"name": "دی‌متیل اتر", "formula": "C2H6O", "type": "Ether", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
              "color": "#FFFFFF"},
    "cr2(so4)3": {"name": "کروم(III) سولفات", "formula": "Cr2(SO4)3", "type": "Salt", "pH": 2.0, "molarity": 0.1,
                  "heat": 0.0, "color": "#006400"},
    "ca(ocl)2": {"name": "کلسیم هیپوکلریت", "formula": "Ca(OCl)2", "type": "Base", "pH": 11.5, "molarity": 0.1,
                 "heat": -40.0, "color": "#FFFFFF"},
    "xanthate": {"name": "گزانتات", "formula": "ROCS2Na", "type": "Salt", "pH": 8.0, "molarity": 0.1, "heat": 0.0,
                 "color": "#FFFF00"},
    "c4h6o6": {"name": "تارتاریک اسید", "formula": "C4H6O6", "type": "Weak Acid", "pH": 2.0, "molarity": 0.1,
               "heat": 14.2, "color": "#FFFFFF"},
"h2so4": {"name": "سولفوریک اسید", "formula": "H2SO4", "type": "Strong Acid", "pH": 1.0, "molarity": 0.1,
              "heat": -88.0, "color": "#FFFFFF", "desc": "اسید قوی و بسیار خورنده، مورد استفاده در باتری خودرو"},
    "naoh": {"name": "سدیم هیدروکسید", "formula": "NaOH", "type": "Strong Base", "pH": 13.0, "molarity": 0.1,
             "heat": -44.5, "color": "#FFFFFF", "desc": "معروف به سود پرک، چربی‌گیر قوی در صنایع شوینده"},
    "hcl": {"name": "هیدروکلریک اسید", "formula": "HCl", "type": "Strong Acid", "pH": 1.1, "molarity": 0.1,
            "heat": -74.8, "color": "#F0F8FF", "desc": "اسید معده، استفاده در جرم‌گیری فلزات"},
    "nh3": {"name": "آمونیاک", "formula": "NH3", "type": "Weak Base", "pH": 11.1, "molarity": 0.1, "heat": -34.0,
            "color": "#FDF5E6", "desc": "گاز تند و زننده، ماده اولیه کودهای شیمیایی"},
    "nacl": {"name": "سدیم کلرید", "formula": "NaCl", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 3.9,
             "color": "#FFFFFF", "desc": "نمک خوراکی معمولی، تنظیم‌کننده فشار اسمزی"},
    "knos3": {"name": "پتاسیم نیترات", "formula": "KNO3", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 34.9,
              "color": "#F0FFF0", "desc": "شوره قلمی، استفاده در باروت و کود کشاورزی"},
    "ch3cooh": {"name": "استیک اسید", "formula": "CH3COOH", "type": "Weak Acid", "pH": 2.9, "molarity": 0.1,
                "heat": -0.4, "color": "#F8F8FF", "desc": "اسید سرکه، حلال آلی در سنتز مواد شیمیایی"},
    "cuso4": {"name": "مس(II) سولفات", "formula": "CuSO4", "type": "Salt", "pH": 4.0, "molarity": 0.1, "heat": -66.0,
              "color": "#0000FF", "desc": "کات‌کبود، ضد قارچ و جلبک در استخرها"},
    "nahco3": {"name": "سدیم بی‌کربنات", "formula": "NaHCO3", "type": "Salt", "pH": 8.3, "molarity": 0.1, "heat": 18.7,
               "color": "#FFFFFF", "desc": "جوش شیرین، عامل پف‌دهنده در پخت نان"},
    "kmnos4": {"name": "پتاسیم پرمنگنات", "formula": "KMnO4", "type": "Salt", "pH": 7.5, "molarity": 0.1, "heat": 43.5,
               "color": "#8B008B", "desc": "اکسیدکننده قوی، ضدعفونی‌کننده بنفش رنگ"},
    "caco3": {"name": "کلسیم کربنات", "formula": "CaCO3", "type": "Salt", "pH": 9.4, "molarity": 0.1, "heat": -12.0,
              "color": "#FFFAF0", "desc": "گچ سنگ، جزء اصلی پوسته تخم‌مرغ و سنگ مرمر"},
    "agno3": {"name": "نقره نیترات", "formula": "AgNO3", "type": "Salt", "pH": 6.0, "molarity": 0.1, "heat": 22.6,
              "color": "#F5F5F5", "desc": "استفاده در عکاسی و درمان زگیل"},
    "h2o2": {"name": "هیدروژن پراکسید", "formula": "H2O2", "type": "Oxidizer", "pH": 4.5, "molarity": 0.1,
             "heat": -98.0, "color": "#F0FFFF", "desc": "آب‌اکسیژنه، سفیدکننده و ضدعفونی‌کننده"},
    "fecl3": {"name": "آهن(III) کلرید", "formula": "FeCl3", "type": "Salt", "pH": 2.0, "molarity": 0.1, "heat": -48.0,
              "color": "#B8860B", "desc": "تصفیه‌کننده فاضلاب و حکاکی روی فلزات"},
    "k2cr2o7": {"name": "پتاسیم دی‌کرومات", "formula": "K2Cr2O7", "type": "Salt", "pH": 4.0, "molarity": 0.1,
                "heat": 75.0, "color": "#FF8C00", "desc": "اکسیدکننده در آزمایشگاه و دباغی چرم"},
    "c2h5oh": {"name": "اتانول", "formula": "C2H5OH", "type": "Alcohol", "pH": 7.0, "molarity": 0.1, "heat": -6.6,
               "color": "#FFFFFF", "desc": "الکل طبی، حلال و سوخت زیستی"},
    "hno3": {"name": "نیتریک اسید", "formula": "HNO3", "type": "Strong Acid", "pH": 1.0, "molarity": 0.1, "heat": -33.3,
             "color": "#FFFFE0", "desc": "تیزاب سلطانی، مورد استفاده در ساخت مواد منفجره"},
    "feso4": {"name": "آهن(II) سولفات", "formula": "FeSO4", "type": "Salt", "pH": 3.5, "molarity": 0.1, "heat": -11.7,
              "color": "#90EE90", "desc": "زاج سبز، برای درمان کم‌خونی و رنگرزی"},
    "na2s2o3": {"name": "سدیم تیوسولفات", "formula": "Na2S2O3", "type": "Salt", "pH": 7.5, "molarity": 0.1, "heat": 7.3,
                "color": "#FFFFFF", "desc": "داروی ضد سم سیانید و ثبیت‌کننده در عکاسی"},
    "znso4": {"name": "روی سولفات", "formula": "ZnSO4", "type": "Salt", "pH": 4.5, "molarity": 0.1, "heat": -77.0,
              "color": "#FFFFFF", "desc": "مکمل روی برای کشاورزی و پیشگیری از خوردگی"},
    "ki": {"name": "پتاسیم یدید", "formula": "KI", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 20.3,
           "color": "#FFFFFF", "desc": "محافظت در برابر تشعشعات رادیواکتیو"},
    "pb(no3)2": {"name": "سرب(II) نیترات", "formula": "Pb(NO3)2", "type": "Salt", "pH": 4.0, "molarity": 0.1,
                 "heat": 33.0, "color": "#FDF5E6", "desc": "ماده اولیه در تولید رنگدانه‌ها و مواد منفجره"},
    "c6h12o6": {"name": "گلوکز", "formula": "C6H12O6", "type": "Sugar", "pH": 7.0, "molarity": 0.1, "heat": 11.0,
                "color": "#FFFFFF", "desc": "قند ساده، منبع اصلی انرژی در موجودات زنده"},
    "s": {"name": "گوگرد", "formula": "S", "type": "Element", "pH": 7.0, "molarity": 1.0, "heat": 0.0,
          "color": "#FFFF00", "desc": "پودر زرد"},
    "c": {"name": "کربن (زغال)", "formula": "C", "type": "Element", "pH": 7.0, "molarity": 1.0, "heat": 0.0,
          "color": "#000000", "desc": "زغال"},
    "h2o": {"name": "آب", "formula": "H2O", "type": "Solvent", "pH": 7.0, "molarity": 55.5, "heat": 0.0,
            "color": "#E0FFFF", "desc": "مایه حیات"},
    "fe": {"name": "آهن", "formula": "Fe", "type": "Metal", "pH": 7.0, "molarity": 1.0, "heat": 0.0, "color": "#808080",
           "desc": "فلز سخت"},
    "o2": {"name": "اکسیژن", "formula": "O2", "type": "Gas", "pH": 7.0, "molarity": 0.01, "heat": 0.0,
           "color": "#FFFFFF", "desc": "گاز حیاتی"},
    "h2so4": {"name": "سولفوریک اسید", "formula": "H2SO4", "type": "Strong Acid", "pH": 1.0, "molarity": 0.1,
              "heat": -88.0, "color": "#FFFFFF", "desc": "اسید قوی و بسیار خورنده، مورد استفاده در باتری خودرو"},
    "naoh": {"name": "سدیم هیدروکسید", "formula": "NaOH", "type": "Strong Base", "pH": 13.0, "molarity": 0.1,
             "heat": -44.5, "color": "#FFFFFF", "desc": "معروف به سود پرک، چربی‌گیر قوی در صنایع شوینده"},
    "hcl": {"name": "هیدروکلریک اسید", "formula": "HCl", "type": "Strong Acid", "pH": 1.1, "molarity": 0.1,
            "heat": -74.8, "color": "#F0F8FF", "desc": "اسید معده، استفاده در جرم‌گیری فلزات"},
    "nh3": {"name": "آمونیاک", "formula": "NH3", "type": "Weak Base", "pH": 11.1, "molarity": 0.1, "heat": -34.0,
            "color": "#FDF5E6", "desc": "گاز تند و زننده، ماده اولیه کودهای شیمیایی"},
    "nacl": {"name": "سدیم کلرید", "formula": "NaCl", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 3.9,
             "color": "#FFFFFF", "desc": "نمک خوراکی معمولی، تنظیم‌کننده فشار اسمزی"},
    "knos3": {"name": "پتاسیم نیترات", "formula": "KNO3", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 34.9,
              "color": "#F0FFF0", "desc": "شوره قلمی، استفاده در باروت و کود کشاورزی"},
    "ch3cooh": {"name": "استیک اسید", "formula": "CH3COOH", "type": "Weak Acid", "pH": 2.9, "molarity": 0.1,
                "heat": -0.4, "color": "#F8F8FF", "desc": "اسید سرکه، حلال آلی در سنتز مواد شیمیایی"},
    "cuso4": {"name": "مس(II) سولفات", "formula": "CuSO4", "type": "Salt", "pH": 4.0, "molarity": 0.1, "heat": -66.0,
              "color": "#0000FF", "desc": "کات‌کبود، ضد قارچ و جلبک در استخرها"},
    "nahco3": {"name": "سدیم بی‌کربنات", "formula": "NaHCO3", "type": "Salt", "pH": 8.3, "molarity": 0.1, "heat": 18.7,
               "color": "#FFFFFF", "desc": "جوش شیرین، عامل پف‌دهنده در پخت نان"},
    "kmnos4": {"name": "پتاسیم پرمنگنات", "formula": "KMnO4", "type": "Salt", "pH": 7.5, "molarity": 0.1, "heat": 43.5,
               "color": "#8B008B", "desc": "اکسیدکننده قوی، ضدعفونی‌کننده بنفش رنگ"},
    "caco3": {"name": "کلسیم کربنات", "formula": "CaCO3", "type": "Salt", "pH": 9.4, "molarity": 0.1, "heat": -12.0,
              "color": "#FFFAF0", "desc": "گچ سنگ، جزء اصلی پوسته تخم‌مرغ و سنگ مرمر"},
    "agno3": {"name": "نقره نیترات", "formula": "AgNO3", "type": "Salt", "pH": 6.0, "molarity": 0.1, "heat": 22.6,
              "color": "#F5F5F5", "desc": "استفاده در عکاسی و درمان زگیل"},
    "mgso4": {"name": "منیزیم سولفات", "formula": "MgSO4", "type": "Salt", "pH": 6.0, "molarity": 0.1, "heat": -91.0,
              "color": "#FFFFFF", "desc": "نمک اپسوم، مکمل منیزیم و ملین"},
    "h2o2": {"name": "هیدروژن پراکسید", "formula": "H2O2", "type": "Oxidizer", "pH": 4.5, "molarity": 0.1,
             "heat": -98.0, "color": "#F0FFFF", "desc": "آب‌اکسیژنه، سفیدکننده و ضدعفونی‌کننده"},
    "ki": {"name": "پتاسیم یدید", "formula": "KI", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 20.3,
           "color": "#FFFFFF", "desc": "محافظت در برابر تشعشعات رادیواکتیو"},
    "fecl3": {"name": "آهن(III) کلرید", "formula": "FeCl3", "type": "Salt", "pH": 2.0, "molarity": 0.1, "heat": -48.0,
              "color": "#B8860B", "desc": "تصفیه‌کننده فاضلاب و حکاکی روی فلزات"},
    "na2co3": {"name": "سدیم کربنات", "formula": "Na2CO3", "type": "Salt", "pH": 11.6, "molarity": 0.1, "heat": -24.0,
               "color": "#FFFFFF", "desc": "سودا اش، استفاده در صنعت شیشه‌سازی"},
    "baos": {"name": "باریم اکسید", "formula": "BaO", "type": "Base", "pH": 12.0, "molarity": 0.1, "heat": -102.0,
             "color": "#F5F5DC", "desc": "جاذب رطوبت و پوشش کاتدها"},
    "alcl3": {"name": "آلومینیوم کلرید", "formula": "AlCl3", "type": "Salt", "pH": 2.4, "molarity": 0.1, "heat": -324.0,
              "color": "#FFFFF0", "desc": "کاتالیزور در واکنش‌های شیمیایی آلی"},
    "k2cr2o7": {"name": "پتاسیم دی‌کرومات", "formula": "K2Cr2O7", "type": "Salt", "pH": 4.0, "molarity": 0.1,
                "heat": 75.0, "color": "#FF8C00", "desc": "اکسیدکننده در آزمایشگاه و دباغی چرم"},

    "c2h5oh": {"name": "اتانول", "formula": "C2H5OH", "type": "Alcohol", "pH": 7.0, "molarity": 0.1, "heat": -6.6,
               "color": "#FFFFFF", "desc": "الکل طبی، حلال و سوخت زیستی"},
    "ch3oh": {"name": "متانول", "formula": "CH3OH", "type": "Alcohol", "pH": 7.0, "molarity": 0.1, "heat": -7.3,
              "color": "#FFFFFF", "desc": "الکل صنعتی، بسیار سمی و حلال قطبی"},
    "h3po4": {"name": "فسفریک اسید", "formula": "H3PO4", "type": "Weak Acid", "pH": 1.5, "molarity": 0.1, "heat": -11.7,
              "color": "#F8F8FF", "desc": "افزودنی در نوشابه‌های گازدار و تولید کود"},
    "hno3": {"name": "نیتریک اسید", "formula": "HNO3", "type": "Strong Acid", "pH": 1.0, "molarity": 0.1, "heat": -33.3,
             "color": "#FFFFE0", "desc": "تیزاب سلطانی، مورد استفاده در ساخت مواد منفجره"},
    "koh": {"name": "پتاسیم هیدروکسید", "formula": "KOH", "type": "Strong Base", "pH": 13.5, "molarity": 0.1,
            "heat": -57.6, "color": "#FFFFFF", "desc": "پتاس سوز آور، استفاده در تولید صابون مایع"},
    "c6h12o6": {"name": "گلوکز", "formula": "C6H12O6", "type": "Sugar", "pH": 7.0, "molarity": 0.1, "heat": 11.0,
                "color": "#FFFFFF", "desc": "قند ساده، منبع اصلی انرژی در موجودات زنده"},
    "c12h22o11": {"name": "ساکارز", "formula": "C12H22O11", "type": "Sugar", "pH": 7.0, "molarity": 0.1, "heat": 5.4,
                  "color": "#FFFFFF", "desc": "قند و شکر معمولی استخراج شده از نیشکر"},
    "mg(oh)2": {"name": "منیزیم هیدروکسید", "formula": "Mg(OH)2", "type": "Weak Base", "pH": 10.5, "molarity": 0.1,
                "heat": 2.1, "color": "#FFFAFA", "desc": "شیر منیزیم، آنتی‌اسید معده و ملین"},
    "ca(oh)2": {"name": "کلسیم هیدروکسید", "formula": "Ca(OH)2", "type": "Base", "pH": 12.4, "molarity": 0.1,
                "heat": -16.7, "color": "#F5F5F5", "desc": "آب‌آهک، استفاده در تصفیه آب و صنعت ساختمان"},
    "feso4": {"name": "آهن(II) سولفات", "formula": "FeSO4", "type": "Salt", "pH": 3.5, "molarity": 0.1, "heat": -11.7,
              "color": "#90EE90", "desc": "زاج سبز، برای درمان کم‌خونی و رنگرزی"},
    "al2(so4)3": {"name": "آلومینیوم سولفات", "formula": "Al2(SO4)3", "type": "Salt", "pH": 3.0, "molarity": 0.1,
                  "heat": -229.0, "color": "#FFFFFF", "desc": "زاج سفید، منعقدکننده در تصفیه آب"},
    "cucl2": {"name": "مس(II) کلرید", "formula": "CuCl2", "type": "Salt", "pH": 3.6, "molarity": 0.1, "heat": -51.5,
              "color": "#20B2AA", "desc": "کاتالیزور در واکنش‌های کلردار کردن"},
    "znso4": {"name": "روی سولفات", "formula": "ZnSO4", "type": "Salt", "pH": 4.5, "molarity": 0.1, "heat": -77.0,
              "color": "#FFFFFF", "desc": "مکمل روی برای کشاورزی و پیشگیری از خوردگی"},
    "licl": {"name": "لیتیوم کلرید", "formula": "LiCl", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": -37.0,
             "color": "#FFFFFF", "desc": "تولید فلز لیتیوم و جاذب رطوبت هوا"},
    "h2c2o4": {"name": "اگزالیک اسید", "formula": "H2C2O4", "type": "Weak Acid", "pH": 1.3, "molarity": 0.1,
               "heat": 9.5, "color": "#FFFFFF", "desc": "پاک‌کننده زنگ آهن و سفیدکننده چوب"},
    "kmno4": {"name": "پتاسیم پرمنگنات", "formula": "KMnO4", "type": "Salt", "pH": 7.2, "molarity": 0.1, "heat": 43.5,
              "color": "#4B0082", "desc": "اکسیدکننده قوی و ضدعفونی‌کننده زخم"},
    "nh4cl": {"name": "آمونیوم کلرید", "formula": "NH4Cl", "type": "Salt", "pH": 4.6, "molarity": 0.1, "heat": 14.8,
              "color": "#FFFFFF", "desc": "نشادر، استفاده در لحیم‌کاری و باتری‌سازی"},
    "pb(no3)2": {"name": "سرب(II) نیترات", "formula": "Pb(NO3)2", "type": "Salt", "pH": 4.0, "molarity": 0.1,
                 "heat": 33.0, "color": "#FDF5E6", "desc": "ماده اولیه در تولید رنگدانه‌ها و مواد منفجره"},
    "h3bo3": {"name": "بوریک اسید", "formula": "H3BO3", "type": "Weak Acid", "pH": 5.1, "molarity": 0.1, "heat": 21.8,
              "color": "#F0FFFF", "desc": "حشره‌کش و گندزدای ملایم"},
    "lic2o3": {"name": "لیتیوم کربنات", "formula": "Li2CO3", "type": "Salt", "pH": 11.0, "molarity": 0.1, "heat": -12.8,
               "color": "#FFFFFF", "desc": "داروی اصلی درمان اختلال دوقطبی"},
    "bacl2": {"name": "باریم کلرید", "formula": "BaCl2", "type": "Salt", "pH": 6.0, "molarity": 0.1, "heat": 8.8,
              "color": "#FFFFFF", "desc": "تست شناسایی یون سولفات در آزمایشگاه"},
    "nabr": {"name": "سدیم برومید", "formula": "NaBr", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": -0.6,
             "color": "#FFFFFF", "desc": "خواب‌آور در پزشکی قدیم و عکاسی"},
    "k2so4": {"name": "پتاسیم سولفات", "formula": "K2SO4", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 23.8,
              "color": "#FFFFFF", "desc": "کود شیمیایی بدون کلر برای گیاهان حساس"},
    "nano2": {"name": "سدیم نیتریت", "formula": "NaNO2", "type": "Salt", "pH": 9.0, "molarity": 0.1, "heat": 13.9,
              "color": "#FFFACD", "desc": "نگهدارنده رنگ در گوشت‌های فرآوری شده"},
    "c3h8o3": {"name": "گلیسیرین", "formula": "C3H8O3", "type": "Alcohol", "pH": 7.0, "molarity": 0.1, "heat": -5.0,
               "color": "#FFFFFF", "desc": "نرم‌کننده پوست و ماده اولیه نیتروگلیسیرین"},
    "cscl": {"name": "سزیم کلرید", "formula": "CsCl", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 17.2,
             "color": "#FFFFFF", "desc": "استفاده در سانتریفیوژ شیب چگالی برای DNA"},
    "hcooh": {"name": "فورمیک اسید", "formula": "HCOOH", "type": "Weak Acid", "pH": 2.4, "molarity": 0.1, "heat": -0.3,
              "color": "#F0F8FF", "desc": "جوهر مورچه، استفاده در صنعت نساجی و دباغی"},
    "ni(no3)2": {"name": "نیکل(II) نیترات", "formula": "Ni(NO3)2", "type": "Salt", "pH": 4.5, "molarity": 0.1,
                 "heat": -30.0, "color": "#98FB98", "desc": "ماده اولیه آبکاری نیکل و کاتالیزورها"},
    "sbcl3": {"name": "آنتیموان تریکلرید", "formula": "SbCl3", "type": "Salt", "pH": 1.5, "molarity": 0.1,
              "heat": -45.0, "color": "#F5F5F5", "desc": "معرف رنگی برای ویتامین A و کاتالیزور"},
    "na3po4": {"name": "تری‌سدیم فسفات", "formula": "Na3PO4", "type": "Base", "pH": 12.0, "molarity": 0.1,
               "heat": -64.0, "color": "#FFFFFF", "desc": "پاک‌کننده صنعتی و چربی‌گیر بسیار قوی"},
    "sncl2": {"name": "قلع(II) کلرید", "formula": "SnCl2", "type": "Salt", "pH": 2.1, "molarity": 0.1, "heat": -12.0,
              "color": "#FFFFFF", "desc": "عامل کاهنده و استفاده در نقره‌کاری آینه"},
    "kh2po4": {"name": "پتاسیم دی‌هیدروژن فسفات", "formula": "KH2PO4", "type": "Salt", "pH": 4.4, "molarity": 0.1,
               "heat": 19.6, "color": "#FFFFFF", "desc": "کود فسفره و تنظیم‌کننده pH در آزمایشگاه"},
    "sr(no3)2": {"name": "استرانسیم نیترات", "formula": "Sr(NO3)2", "type": "Salt", "pH": 7.0, "molarity": 0.1,
                 "heat": 20.0, "color": "#FFFFFF", "desc": "ایجاد رنگ قرمز در آتش‌بازی"},
    "hio3": {"name": "یدیک اسید", "formula": "HIO3", "type": "Strong Acid", "pH": 1.1, "molarity": 0.1, "heat": 8.0,
             "color": "#FDF5E6", "desc": "اکسیدکننده قوی در سنتزهای شیمیایی"},
    "nas": {"name": "سدیم سولفید", "formula": "Na2S", "type": "Base", "pH": 12.5, "molarity": 0.1, "heat": -63.0,
            "color": "#FFE4B5", "desc": "استفاده در جداسازی مو از پوست در دباغی"},
    "al(oh)3": {"name": "آلومینیوم هیدروکسید", "formula": "Al(OH)3", "type": "Weak Base", "pH": 8.5, "molarity": 0.1,
                "heat": 10.0, "color": "#FFFFFF", "desc": "آنتی‌اسید معده و ضد حریق در پلاستیک"},
    "mno2": {"name": "منگنز دی‌اکسید", "formula": "MnO2", "type": "Oxide", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
             "color": "#2F4F4F", "desc": "استفاده در باتری‌های خشک و کاتالیزور تجزیه آب‌اکسیژنه"},
    "nacn": {"name": "سدیم سیانید", "formula": "NaCN", "type": "Salt", "pH": 11.5, "molarity": 0.1, "heat": 12.1,
             "color": "#FFFFFF", "desc": "بسیار سمی، مورد استفاده در استخراج طلا"},
    "lif": {"name": "لیتیوم فلورید", "formula": "LiF", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 4.7,
            "color": "#FFFFFF", "desc": "استفاده در صنعت شیشه و دزیمتری تابش"},
    "hclo4": {"name": "پرکلریک اسید", "formula": "HClO4", "type": "Strong Acid", "pH": 1.0, "molarity": 0.1,
              "heat": -88.0, "color": "#FFFFFF", "desc": "قوی‌ترین اسید معدنی شناخته شده"},
    "cus": {"name": "مس(II) سولفید", "formula": "CuS", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
            "color": "#000000", "desc": "کانی نیلیک، هادی الکتریسیته در قطعات الکترونیک"},
    "agcl": {"name": "نقره کلرید", "formula": "AgCl", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 65.0,
             "color": "#F8F8FF", "desc": "حساس به نور، استفاده در الکترودهای مرجع"},
    "feno3": {"name": "آهن(III) نیترات", "formula": "Fe(NO3)3", "type": "Salt", "pH": 2.2, "molarity": 0.1,
              "heat": -30.0, "color": "#E6E6FA", "desc": "کاتالیزور در سنتز آلی و رنگرزی منسوجات"},
    "c2h2o4": {"name": "اتان‌دی‌اوئیک اسید", "formula": "(COOH)2", "type": "Weak Acid", "pH": 1.3, "molarity": 0.1,
               "heat": 9.5, "color": "#FFFFFF", "desc": "نام دیگر اگزالیک اسید، پاک‌کننده رسوبات فلزی"},
    "na2so4": {"name": "سدیم سولفات", "formula": "Na2SO4", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 1.2,
               "color": "#FFFFFF", "desc": "پرکننده در پودرهای شوینده لباسشویی"},
    "hbr": {"name": "هیدروبرومیک اسید", "formula": "HBr", "type": "Strong Acid", "pH": 1.1, "molarity": 0.1,
            "heat": -85.1, "color": "#FDF5E6", "desc": "تولید ترکیبات بروم‌دار آلی و کاتالیزور"},
    "hgcl2": {"name": "جیوه(II) کلرید", "formula": "HgCl2", "type": "Salt", "pH": 3.2, "molarity": 0.1, "heat": 14.0,
              "color": "#FFFFFF", "desc": "بسیار سمی، معروف به سوبلیمه کوروزیف"},
    "kio3": {"name": "پتاسیم یدات", "formula": "KIO3", "type": "Salt", "pH": 6.5, "molarity": 0.1, "heat": 27.0,
             "color": "#FFFFFF", "desc": "منبع ید در نمک‌های یددار خوراکی"},
    "nh4no3": {"name": "آمونیوم نیترات", "formula": "NH4NO3", "type": "Salt", "pH": 4.8, "molarity": 0.1, "heat": 25.7,
               "color": "#FFFFFF", "desc": "کود کشاورزی با نیتروژن بالا و ماده انفجاری"},

    "c6h8o7": {"name": "اسید سیتریک", "formula": "C6H8O7", "type": "Weak Acid", "pH": 2.2, "molarity": 0.1, "heat": 6.4,
               "color": "#FFFFFF", "desc": "جوهر لیمو، نگهدارنده و طعم‌دهنده مواد غذایی"},
    "c3h6o": {"name": "استون", "formula": "C3H6O", "type": "Solvent", "pH": 7.0, "molarity": 0.1, "heat": -0.8,
              "color": "#FFFFFF", "desc": "حلال آلی قوی، پاک‌کننده لاک و چربی‌گیر"},
    "c6h5oh": {"name": "فنول", "formula": "C6H5OH", "type": "Weak Acid", "pH": 6.0, "molarity": 0.1, "heat": 12.5,
               "color": "#FFF5EE", "desc": "اسید کربولیک، ماده اولیه در تولید پلاستیک و رزین"},
    "k2co3": {"name": "پتاسیم کربنات", "formula": "K2CO3", "type": "Base", "pH": 11.6, "molarity": 0.1, "heat": -27.6,
              "color": "#FFFFFF", "desc": "پتاس مروارید، استفاده در ساخت شیشه و صابون"},
    "na2s2o3": {"name": "سدیم تیوسولفات", "formula": "Na2S2O3", "type": "Salt", "pH": 7.5, "molarity": 0.1, "heat": 7.3,
                "color": "#FFFFFF", "desc": "داروی ضد سم سیانید و ثبیت‌کننده در عکاسی"},
    "c2h6o2": {"name": "اتیلن گلیکول", "formula": "C2H6O2", "type": "Alcohol", "pH": 7.0, "molarity": 0.1, "heat": -6.0,
               "color": "#F0FFFF", "desc": "ضدیخ خودرو و ماده اولیه پلی‌اتیلن"},
    "nh4oh": {"name": "آمونیوم هیدروکسید", "formula": "NH4OH", "type": "Weak Base", "pH": 11.6, "molarity": 0.1,
              "heat": -35.4, "color": "#F0F8FF", "desc": "محلول آمونیاک در آب، پاک‌کننده خانگی"},
    "c4h6o6": {"name": "تارتاریک اسید", "formula": "C4H6O6", "type": "Weak Acid", "pH": 2.0, "molarity": 0.1,
               "heat": 14.2, "color": "#FFFFFF", "desc": "موجود در انگور، استفاده در جوش‌شیرین پخت‌وپز"},
    "baso4": {"name": "باریم سولفات", "formula": "BaSO4", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
              "color": "#FFFFFF", "desc": "ماده حاجب در تصویربرداری ایکس از گوارش"},
    "pbcl2": {"name": "سرب(II) کلرید", "formula": "PbCl2", "type": "Salt", "pH": 4.5, "molarity": 0.1, "heat": 23.4,
              "color": "#FFFFFF", "desc": "نیمه‌هادی و مورد استفاده در تولید شیشه‌های سربی"},
    "li2so4": {"name": "لیتیوم سولفات", "formula": "Li2SO4", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": -29.8,
               "color": "#FFFFFF", "desc": "استفاده در درمان افسردگی و ساخت شیشه‌های نشکن"},
    "naclq3": {"name": "سدیم کلرات", "formula": "NaClO3", "type": "Oxidizer", "pH": 7.0, "molarity": 0.1, "heat": 21.7,
               "color": "#FFFFFF", "desc": "علف‌کش قوی و سفیدکننده خمیر کاغذ"},
    "k2crq4": {"name": "پتاسیم کرومات", "formula": "K2CrO4", "type": "Salt", "pH": 8.5, "molarity": 0.1, "heat": 14.5,
               "color": "#FFFF00", "desc": "نشانگر در تیتراسیون و بازدارنده خوردگی"},
    "h2s": {"name": "هیدروژن سولفید", "formula": "H2S", "type": "Weak Acid", "pH": 4.1, "molarity": 0.1, "heat": -19.7,
            "color": "#F5F5F5", "desc": "گاز با بوی تخم‌مرغ گندیده، بسیار سمی"},
    "c6h12o": {"name": "سیکلوهگزانول", "formula": "C6H12O", "type": "Alcohol", "pH": 7.0, "molarity": 0.1, "heat": -4.2,
               "color": "#FDF5E6", "desc": "ماده اولیه تولید نایلون و حلال لاک"},
    "niicq2": {"name": "نیکل(II) کلرید", "formula": "NiCl2", "type": "Salt", "pH": 4.0, "molarity": 0.1, "heat": -16.0,
               "color": "#00FF00", "desc": "استفاده در آبکاری الکتریکی نیکل"},
    "zncl2": {"name": "روی کلرید", "formula": "ZnCl2", "type": "Salt", "pH": 4.0, "molarity": 0.1, "heat": -15.6,
              "color": "#FFFFFF", "desc": "لحیم‌کاری و محافظ چوب در برابر پوسیدگی"},
    "caso4": {"name": "کلسیم سولفات", "formula": "CaSO4", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": -1.1,
              "color": "#FFFFFF", "desc": "گچ پاریس، مورد استفاده در قالب‌گیری و پزشکی"},
    "ch4": {"name": "متان", "formula": "CH4", "type": "Gas", "pH": 7.0, "molarity": 0.1, "heat": -12.9,
            "color": "#F0F8FF", "desc": "گاز طبیعی، سوخت اصلی خانگی و صنعتی"},
    "c2h2": {"name": "استیلن", "formula": "C2H2", "type": "Gas", "pH": 7.0, "molarity": 0.1, "heat": -22.0,
             "color": "#FFFFFF", "desc": "گاز مورد استفاده در جوشکاری فشار بالا"},
    "c6h6": {"name": "بنزن", "formula": "C6H6", "type": "Hydrocarbon", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
             "color": "#FFFFFF", "desc": "ترکیب حلقوی معطر، حلال و سرطان‌زا"},
    "c7h8": {"name": "تولوئن", "formula": "C7H8", "type": "Hydrocarbon", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
             "color": "#FFFFFF", "desc": "حلال رنگ و تینر، جایگزین ایمن‌تر بنزن"},
    "c8h10": {"name": "زایلن", "formula": "C8H10", "type": "Hydrocarbon", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
              "color": "#FFFFFF", "desc": "حلال در صنایع چاپ، لاستیک و چرم"},
    "c3h7oh": {"name": "ایزوپروپیل الکل", "formula": "C3H8O", "type": "Alcohol", "pH": 7.0, "molarity": 0.1,
               "heat": -13.0, "color": "#FFFFFF", "desc": "الکل مالشی، ضدعفونی‌کننده سطوح"},
    "c4h10o": {"name": "دی‌اتیل اتر", "formula": "C4H10O", "type": "Ether", "pH": 7.0, "molarity": 0.1, "heat": -6.0,
               "color": "#FFFFFF", "desc": "ماده بیهوشی قدیمی و حلال استخراج"},
    "chcl3": {"name": "کلروفرم", "formula": "CHCl3", "type": "Solvent", "pH": 7.0, "molarity": 0.1, "heat": -4.0,
              "color": "#FFFFFF", "desc": "حلال چربی و ماده بیهوشی در گذشته"},
    "ccl4": {"name": "کربن تتراکلرید", "formula": "CCl4", "type": "Solvent", "pH": 7.0, "molarity": 0.1, "heat": -2.0,
             "color": "#FFFFFF", "desc": "پاک‌کننده لکه خشک و کپسول آتش‌نشانی قدیمی"},
    "c2h4o2": {"name": "وینیل استات", "formula": "C4H6O2", "type": "Monomer", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
               "color": "#FFFFFF", "desc": "ماده اولیه چسب چوب و رنگ‌های پلاستیک"},
    "nh2ch2cooh": {"name": "گلیسین", "formula": "C2H5NO2", "type": "Amino Acid", "pH": 6.0, "molarity": 0.1,
                   "heat": 14.2, "color": "#FFFFFF", "desc": "ساده‌ترین اسید آمینه در ساختار پروتئین"},
    "c6h5cooh": {"name": "بنزوئیک اسید", "formula": "C7H6O2", "type": "Weak Acid", "pH": 2.8, "molarity": 0.1,
                 "heat": 18.0, "color": "#FFFFFF", "desc": "نگهدارنده مواد غذایی و ضد قارچ"},
    "c6h5coona": {"name": "سدیم بنزوات", "formula": "C7H5NaO2", "type": "Salt", "pH": 8.0, "molarity": 0.1, "heat": 7.8,
                  "color": "#FFFFFF", "desc": "نگهدارنده رایج در نوشابه‌ها و ترشیجات"},
    "na2siq3": {"name": "سدیم سیلیکات", "formula": "Na2SiO3", "type": "Base", "pH": 12.5, "molarity": 0.1,
                "heat": -32.0, "color": "#F5F5F5", "desc": "چسب شیشه مایع، حفاظت از تخم‌مرغ"},
    "h2c2q4": {"name": "اگزالیک اسید", "formula": "H2C2O4", "type": "Weak Acid", "pH": 1.3, "molarity": 0.1,
               "heat": 9.5, "color": "#FFFFFF", "desc": "پاک‌کننده زنگ فلزات و براق‌کننده چوب"},
    "c3h6o3": {"name": "لاکتیک اسید", "formula": "C3H6O3", "type": "Weak Acid", "pH": 2.4, "molarity": 0.1,
               "heat": -8.0, "color": "#FFFACD", "desc": "اسید شیر، عامل گرفتگی عضلات"},
    "c6h8o6": {"name": "ویتامین ث", "formula": "C6H8O6", "type": "Weak Acid", "pH": 2.5, "molarity": 0.1, "heat": 15.0,
               "color": "#FFFFFF", "desc": "اسید اسکوربیک، آنتی‌اکسیدان ضروری بدن"},
    "k2so3": {"name": "پتاسیم سولفیت", "formula": "K2SO3", "type": "Salt", "pH": 9.0, "molarity": 0.1, "heat": -12.0,
              "color": "#FFFFFF", "desc": "نگهدارنده در شراب‌سازی و عکاسی"},
    "na2sq4": {"name": "سدیم سولفات", "formula": "Na2SO4", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 1.2,
               "color": "#FFFFFF", "desc": "پرکننده پودرهای لباسشویی و صنعت شیشه"},
    "liiqh": {"name": "لیتیوم هیدروکسید", "formula": "LiOH", "type": "Strong Base", "pH": 13.0, "molarity": 0.1,
              "heat": -23.6, "color": "#FFFFFF", "desc": "جاذب دی‌اکسید کربن در سفینه‌های فضایی"},
    "beiq": {"name": "بریلیوم اکسید", "formula": "BeO", "type": "Oxide", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
             "color": "#FFFFFF", "desc": "عایق الکتریکی با رسانایی گرمایی بالا"},
    "mgcl2": {"name": "منیزیم کلرید", "formula": "MgCl2", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": -155.0,
              "color": "#FFFFFF", "desc": "کنترل گرد و غبار جاده و مکمل منیزیم"},
    "cacl2": {"name": "کلسیم کلرید", "formula": "CaCl2", "type": "Salt", "pH": 7.5, "molarity": 0.1, "heat": -81.3,
              "color": "#FFFFFF", "desc": "نمک ضد یخ جاده و جاذب رطوبت قوی"},
    "srcl2": {"name": "استرانسیم کلرید", "formula": "SrCl2", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": -31.0,
              "color": "#FFFFFF", "desc": "استفاده در خمیردندان‌های حساس"},
    "feiq": {"name": "آهن(II) اکسید", "formula": "FeO", "type": "Oxide", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
             "color": "#000000", "desc": "رنگدانه سیاه در سرامیک‌سازی"},
    "fe2q3": {"name": "آهن(III) اکسید", "formula": "Fe2O3", "type": "Oxide", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
              "color": "#8B4513", "desc": "هماتیت، زنگ آهن و رنگدانه قرمز پودری"},
    "fe3q4": {"name": "آهن(II,III) اکسید", "formula": "Fe3O4", "type": "Oxide", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
              "color": "#000000", "desc": "مگنتیت، اکسید مغناطیسی سیاه آهن"},
    "cuiq": {"name": "مس(II) اکسید", "formula": "CuO", "type": "Oxide", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
             "color": "#000000", "desc": "استفاده در لعاب‌کاری برای ایجاد رنگ سبز"},
    "cu2q": {"name": "مس(I) اکسید", "formula": "Cu2O", "type": "Oxide", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
             "color": "#B22222", "desc": "رنگدانه قرمز در شیشه و نیمه‌هادی"},
    "zno": {"name": "روی اکسید", "formula": "ZnO", "type": "Oxide", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
            "color": "#FFFFFF", "desc": "پماد زینک اکساید، محافظ پوست و ضد آفتاب"},
    "al2q3": {"name": "آلومینیوم اکسید", "formula": "Al2O3", "type": "Oxide", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
              "color": "#FFFFFF", "desc": "آلومینا، ماده ساینده و پایه کاتالیزور"},
    "siq2": {"name": "سیلیسیم دی‌اکسید", "formula": "SiO2", "type": "Oxide", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
             "color": "#FFFFFF", "desc": "ماسه کوارتز، ماده اصلی شیشه‌سازی"},
    "p4q10": {"name": "فسفر پنتااکسید", "formula": "P4O10", "type": "Acidic Oxide", "pH": 1.5, "molarity": 0.1,
              "heat": -170.0, "color": "#FFFFFF", "desc": "عامل آب‌گیر بسیار قوی در آزمایشگاه"},
    "so2": {"name": "گوگرد دی‌اکسید", "formula": "SO2", "type": "Gas", "pH": 3.0, "molarity": 0.1, "heat": -33.0,
            "color": "#FFFFFF", "desc": "گاز سمی، ایجاد باران اسیدی و سفیدکننده"},
    "so3": {"name": "گوگرد تری‌اکسید", "formula": "SO3", "type": "Oxide", "pH": 1.0, "molarity": 0.1, "heat": -90.0,
            "color": "#FFFFFF", "desc": "پیش‌ساز مستقیم اسید سولفوریک"},
    "co": {"name": "کربن مونوکسید", "formula": "CO", "type": "Gas", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
           "color": "#FFFFFF", "desc": "گاز بی‌بو و کشنده ناشی از احتراق ناقص"},
    "co2": {"name": "کربن دی‌اکسید", "formula": "CO2", "type": "Gas", "pH": 5.5, "molarity": 0.1, "heat": -20.0,
            "color": "#FFFFFF", "desc": "گاز گلخانه‌ای، یخ خشک و کپسول آتش‌نشانی"},
    "n2o": {"name": "دی‌نیتروژن مونوکسید", "formula": "N2O", "type": "Gas", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
            "color": "#FFFFFF", "desc": "گاز خنده، بیهوشی ملایم و تقویت موتور خودرو"},
    "no": {"name": "نیتروژن مونوکسید", "formula": "NO", "type": "Gas", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
           "color": "#FFFFFF", "desc": "رادیکال آزاد، نقش در انتقال پیام عصبی"},
    "no2": {"name": "نیتروژن دی‌اکسید", "formula": "NO2", "type": "Gas", "pH": 3.0, "molarity": 0.1, "heat": -15.0,
            "color": "#A52A2A", "desc": "گاز قهوه‌ای مایل به قرمز، آلاینده هوا"},
    "pbi2": {"name": "سرب(II) یدید", "formula": "PbI2", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 63.0,
             "color": "#FFFF00", "desc": "باران طلایی، استفاده در سلول‌های خورشیدی"},
    "hgi2": {"name": "جیوه(II) یدید", "formula": "HgI2", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 45.0,
             "color": "#FF4500", "desc": "ترکیب ترموکرومیک (تغییر رنگ با دما)"},
    "snf2": {"name": "قلع(II) فلورید", "formula": "SnF2", "type": "Salt", "pH": 3.5, "molarity": 0.1, "heat": 2.0,
             "color": "#FFFFFF", "desc": "فلوراید مورد استفاده در خمیردندان"},
    "naf": {"name": "سدیم فلورید", "formula": "NaF", "type": "Salt", "pH": 7.5, "molarity": 0.1, "heat": 0.9,
            "color": "#FFFFFF", "desc": "جلوگیری از پوسیدگی دندان و سم حشرات"},
    "niis": {"name": "نیکل(II) سولفید", "formula": "NiS", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
             "color": "#000000", "desc": "موجود در کانی میلریت، کاتالیزور صنعتی"},
    "zns": {"name": "روی سولفید", "formula": "ZnS", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
            "color": "#FFFFFF", "desc": "ماده فلورسنت در صفحات رادیولوژی قدیمی"},
    "cds": {"name": "کادمیوم سولفید", "formula": "CdS", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
            "color": "#FFFF00", "desc": "رنگدانه زرد کادمیوم و فتوسل‌ها"},
    "as2s3": {"name": "آرسنیک(III) سولفید", "formula": "As2S3", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
              "color": "#FFA500", "desc": "رنگدانه زرد رهج، سمی و نیمه‌هادی"},
    "sb2s3": {"name": "آنتیموان(III) سولفید", "formula": "Sb2S3", "type": "Salt", "pH": 7.0, "molarity": 0.1,
              "heat": 0.0, "color": "#2F4F4F", "desc": "سرمه چشم قدیم و چاشنی مواد منفجره"},
    "hg s": {"name": "جیوه(II) سولفید", "formula": "HgS", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
             "color": "#FF0000", "desc": "شنگرف، رنگدانه قرمز درخشان و کانی جیوه"},
    "cs2": {"name": "کربن دی‌سولفید", "formula": "CS2", "type": "Solvent", "pH": 7.0, "molarity": 0.1, "heat": -3.0,
            "color": "#FFFFFF", "desc": "حلال فسفر و گوگرد، بسیار آتش‌گیر"},
    "p4 s3": {"name": "فسفر سسکوئی‌سولفید", "formula": "P4S3", "type": "Sulfide", "pH": 7.0, "molarity": 0.1,
              "heat": 0.0, "color": "#FFFF00", "desc": "مورد استفاده در نوک کبریت‌های بی‌خطر"},
    "na n3": {"name": "سدیم آزید", "formula": "NaN3", "type": "Salt", "pH": 10.0, "molarity": 0.1, "heat": 21.0,
              "color": "#FFFFFF", "desc": "تولید گاز در کیسه هوای خودرو، بسیار سمی"},
    "k n3": {"name": "پتاسیم آزید", "formula": "KN3", "type": "Salt", "pH": 9.5, "molarity": 0.1, "heat": 25.0,
             "color": "#FFFFFF", "desc": "تجزیه حرارتی برای تولید پتاسیم خالص"},
    "h cn": {"name": "هیدروژن سیانید", "formula": "HCN", "type": "Weak Acid", "pH": 5.1, "molarity": 0.1, "heat": -20.0,
             "color": "#F0F8FF", "desc": "اسید پیروسیک، گاز فوق‌العاده سمی بوی بادام تلخ"},
    "k cn": {"name": "پتاسیم سیانید", "formula": "KCN", "type": "Salt", "pH": 11.0, "molarity": 0.1, "heat": 11.7,
             "color": "#FFFFFF", "desc": "سم مشهور، استفاده در استخراج طلا و آبکاری"},
    "na ocl": {"name": "سدیم هیپوکلریت", "formula": "NaOCl", "type": "Base", "pH": 12.0, "molarity": 0.1, "heat": -35.0,
               "color": "#FFFACD", "desc": "وایتکس، سفیدکننده و گندزدای قوی"},
    "ca ocl2": {"name": "کلسیم هیپوکلریت", "formula": "Ca(OCl)2", "type": "Base", "pH": 11.5, "molarity": 0.1,
                "heat": -40.0, "color": "#FFFFFF", "desc": "پودر کلر، ضدعفونی‌کننده آب استخر"},
    "k clo3": {"name": "پتاسیم کلرات", "formula": "KClO3", "type": "Oxidizer", "pH": 7.0, "molarity": 0.1, "heat": 41.3,
               "color": "#FFFFFF", "desc": "اکسیدکننده در سر کبریت و آتش‌بازی"},
    "k clo4": {"name": "پتاسیم پرکلرات", "formula": "KClO4", "type": "Oxidizer", "pH": 7.0, "molarity": 0.1,
               "heat": 51.0, "color": "#FFFFFF", "desc": "سوخت پیشران موشک و ترقه"},
    "nh4 clo4": {"name": "آمونیوم پرکلرات", "formula": "NH4ClO4", "type": "Oxidizer", "pH": 4.5, "molarity": 0.1,
                 "heat": 33.5, "color": "#FFFFFF", "desc": "سوخت جامد شاتل‌های فضایی"},
    "ag br": {"name": "نقره برومید", "formula": "AgBr", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 84.0,
              "color": "#FFFFE0", "desc": "ماده اصلی فیلم‌های عکاسی سیاه و سفید"},
    "ag i": {"name": "نقره یدید", "formula": "AgI", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 105.0,
             "color": "#FFFF00", "desc": "استفاده در بارورسازی ابرها برای تولید باران"},
    "ca f2": {"name": "کلسیم فلورید", "formula": "CaF2", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 13.0,
              "color": "#FFFFFF", "desc": "فلوریت، استفاده در لنزهای اپتیکال با کیفیت"},
    "ba f2": {"name": "باریم فلورید", "formula": "BaF2", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 4.0,
              "color": "#FFFFFF", "desc": "پوشش‌های ضد انعکاس و پنجره‌های مادون قرمز"},
    "mg f2": {"name": "منیزیم فلورید", "formula": "MgF2", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": -2.0,
              "color": "#FFFFFF", "desc": "پوشش لنز دوربین برای حذف بازتاب نور"},
    "cu i": {"name": "مس(I) یدید", "formula": "CuI", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 20.0,
             "color": "#F5F5DC", "desc": "تأمین ید در خوراک دام و کاتالیزور آلی"},
    "k i o3": {"name": "پتاسیم یدات", "formula": "KIO3", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 28.0,
               "color": "#FFFFFF", "desc": "یددار کردن نمک طعام برای جلوگیری از گواتر"},
    "na i o3": {"name": "سدیم یدات", "formula": "NaIO3", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 20.0,
                "color": "#FFFFFF", "desc": "ضدعفونی‌کننده و پیش‌ساز تولید ید"},
    "li b r": {"name": "لیتیوم برومید", "formula": "LiBr", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": -48.8,
               "color": "#FFFFFF", "desc": "جاذب رطوبت در سیستم‌های تهویه مطبوع"},
    "zn br2": {"name": "روی برومید", "formula": "ZnBr2", "type": "Salt", "pH": 4.0, "molarity": 0.1, "heat": -67.0,
               "color": "#FFFFFF", "desc": "مایع حفاری چاه‌های نفت و محافظ اشعه"},
    "cd cl2": {"name": "کادمیوم کلرید", "formula": "CdCl2", "type": "Salt", "pH": 5.0, "molarity": 0.1, "heat": -18.0,
               "color": "#FFFFFF", "desc": "آبکاری کادمیوم و چاپ عکس روی پارچه"},
    "al i3": {"name": "آلومینیوم یدید", "formula": "AlI3", "type": "Salt", "pH": 3.0, "molarity": 0.1, "heat": -300.0,
              "color": "#F0F8FF", "desc": "کاتالیزور در واکنش‌های تشکیل پیوند کربن-کربن"},
    "ti cl4": {"name": "تیتانیوم تتراکلرید", "formula": "TiCl4", "type": "Salt", "pH": 1.0, "molarity": 0.1,
               "heat": -160.0, "color": "#FFFFFF", "desc": "تولید تیتانیوم خالص و ایجاد پرده دود در ارتش"},
    "v2 o5": {"name": "وانادیوم پنتااکسید", "formula": "V2O5", "type": "Oxide", "pH": 3.0, "molarity": 0.1,
              "heat": -40.0, "color": "#FF8C00", "desc": "کاتالیزور تولید اسید سولفوریک در فرآیند تماسی"},
    "cr o3": {"name": "کروم تری‌اکسید", "formula": "CrO3", "type": "Acidic Oxide", "pH": 1.0, "molarity": 0.1,
              "heat": -7.0, "color": "#8B0000", "desc": "اسید کرومیک، اکسیدکننده بسیار قوی و سرطان‌زا"},
    "mn so4": {"name": "منگنز(II) سولفات", "formula": "MnSO4", "type": "Salt", "pH": 5.0, "molarity": 0.1,
               "heat": -62.0, "color": "#FFC0CB", "desc": "کود کشاورزی منگنز و افزودنی خوراک دام"},
    "co so4": {"name": "کبالت(II) سولفات", "formula": "CoSO4", "type": "Salt", "pH": 5.0, "molarity": 0.1,
               "heat": -70.0, "color": "#FF1493", "desc": "تولید باتری‌های لیتیم-یون و مکمل ویتامین B12"},
    "ni so4": {"name": "نیکل(II) سولفات", "formula": "NiSO4", "type": "Salt", "pH": 4.5, "molarity": 0.1, "heat": -80.0,
               "color": "#7FFF00", "desc": "نمک اصلی آبکاری نیکل و ساخت کاتالیزور"},
    "cd so4": {"name": "کادمیوم سولفات", "formula": "CdSO4", "type": "Salt", "pH": 5.0, "molarity": 0.1, "heat": -55.0,
               "color": "#FFFFFF", "desc": "استفاده در سلول‌های استاندارد وستون برای ولتاژ"},
    "sn so4": {"name": "قلع(II) سولفات", "formula": "SnSO4", "type": "Salt", "pH": 2.5, "molarity": 0.1, "heat": -40.0,
               "color": "#FFFFFF", "desc": "آبکاری قلع و آنودایز کردن آلومینیوم"},
    "tl2 so4": {"name": "تالیوم(I) سولفات", "formula": "Tl2SO4", "type": "Salt", "pH": 7.0, "molarity": 0.1,
                "heat": 20.0, "color": "#FFFFFF", "desc": "سم موش بسیار خطرناک (در اکثر کشورها ممنوع است)"},

    "c6h8o7": {"name": "اسید سیتریک", "formula": "C6H8O7", "type": "Weak Acid", "pH": 2.2, "molarity": 0.1, "heat": 6.4,
               "color": "#FFFFFF", "desc": "جوهر لیمو، نگهدارنده و طعم‌دهنده مواد غذایی"},
    "c3h6o": {"name": "استون", "formula": "C3H6O", "type": "Solvent", "pH": 7.0, "molarity": 0.1, "heat": -0.8,
              "color": "#FFFFFF", "desc": "حلال آلی قوی، پاک‌کننده لاک و چربی‌گیر"},
    "c6h5oh": {"name": "فنول", "formula": "C6H5OH", "type": "Weak Acid", "pH": 6.0, "molarity": 0.1, "heat": 12.5,
               "color": "#FFF5EE", "desc": "اسید کربولیک، ماده اولیه در تولید پلاستیک و رزین"},
    "k2co3": {"name": "پتاسیم کربنات", "formula": "K2CO3", "type": "Base", "pH": 11.6, "molarity": 0.1, "heat": -27.6,
              "color": "#FFFFFF", "desc": "پتاس مروارید، استفاده در ساخت شیشه و صابون"},
    "na2s2o3": {"name": "سدیم تیوسولفات", "formula": "Na2S2O3", "type": "Salt", "pH": 7.5, "molarity": 0.1, "heat": 7.3,
                "color": "#FFFFFF", "desc": "داروی ضد سم سیانید و ثبیت‌کننده در عکاسی"},
    "c2h6o2": {"name": "اتیلن گلیکول", "formula": "C2H6O2", "type": "Alcohol", "pH": 7.0, "molarity": 0.1, "heat": -6.0,
               "color": "#F0FFFF", "desc": "ضدیخ خودرو و ماده اولیه پلی‌اتیلن"},
    "nh4oh": {"name": "آمونیوم هیدروکسید", "formula": "NH4OH", "type": "Weak Base", "pH": 11.6, "molarity": 0.1,
              "heat": -35.4, "color": "#F0F8FF", "desc": "محلول آمونیاک در آب، پاک‌کننده خانگی"},
    "c4h6o6": {"name": "تارتاریک اسید", "formula": "C4H6O6", "type": "Weak Acid", "pH": 2.0, "molarity": 0.1,
               "heat": 14.2, "color": "#FFFFFF", "desc": "موجود در انگور، استفاده در جوش‌شیرین پخت‌وپز"},
    "baso4": {"name": "باریم سولفات", "formula": "BaSO4", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
              "color": "#FFFFFF", "desc": "ماده حاجب در تصویربرداری ایکس از گوارش"},
    "pbcl2": {"name": "سرب(II) کلرید", "formula": "PbCl2", "type": "Salt", "pH": 4.5, "molarity": 0.1, "heat": 23.4,
              "color": "#FFFFFF", "desc": "نیمه‌هادی و مورد استفاده در تولید شیشه‌های سربی"},
    "li2so4": {"name": "لیتیوم سولفات", "formula": "Li2SO4", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": -29.8,
               "color": "#FFFFFF", "desc": "استفاده در درمان افسردگی و ساخت شیشه‌های نشکن"},
    "naclq3": {"name": "سدیم کلرات", "formula": "NaClO3", "type": "Oxidizer", "pH": 7.0, "molarity": 0.1, "heat": 21.7,
               "color": "#FFFFFF", "desc": "علف‌کش قوی و سفیدکننده خمیر کاغذ"},
    "k2crq4": {"name": "پتاسیم کرومات", "formula": "K2CrO4", "type": "Salt", "pH": 8.5, "molarity": 0.1, "heat": 14.5,
               "color": "#FFFF00", "desc": "نشانگر در تیتراسیون و بازدارنده خوردگی"},
    "h2s": {"name": "هیدروژن سولفید", "formula": "H2S", "type": "Weak Acid", "pH": 4.1, "molarity": 0.1, "heat": -19.7,
            "color": "#F5F5F5", "desc": "گاز با بوی تخم‌مرغ گندیده، بسیار سمی"},
    "c6h12o": {"name": "سیکلوهگزانول", "formula": "C6H12O", "type": "Alcohol", "pH": 7.0, "molarity": 0.1, "heat": -4.2,
               "color": "#FDF5E6", "desc": "ماده اولیه تولید نایلون و حلال لاک"},
    "niicq2": {"name": "نیکل(II) کلرید", "formula": "NiCl2", "type": "Salt", "pH": 4.0, "molarity": 0.1, "heat": -16.0,
               "color": "#00FF00", "desc": "استفاده در آبکاری الکتریکی نیکل"},
    "zncl2": {"name": "روی کلرید", "formula": "ZnCl2", "type": "Salt", "pH": 4.0, "molarity": 0.1, "heat": -15.6,
              "color": "#FFFFFF", "desc": "لحیم‌کاری و محافظ چوب در برابر پوسیدگی"},
    "caso4": {"name": "کلسیم سولفات", "formula": "CaSO4", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": -1.1,
              "color": "#FFFFFF", "desc": "گچ پاریس، مورد استفاده در قالب‌گیری و پزشکی"},
    "ch4": {"name": "متان", "formula": "CH4", "type": "Gas", "pH": 7.0, "molarity": 0.1, "heat": -12.9,
            "color": "#F0F8FF", "desc": "گاز طبیعی، سوخت اصلی خانگی و صنعتی"},
    "c2h2": {"name": "استیلن", "formula": "C2H2", "type": "Gas", "pH": 7.0, "molarity": 0.1, "heat": -22.0,
             "color": "#FFFFFF", "desc": "گاز مورد استفاده در جوشکاری فشار بالا"},
    "c6h6": {"name": "بنزن", "formula": "C6H6", "type": "Hydrocarbon", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
             "color": "#FFFFFF", "desc": "ترکیب حلقوی معطر، حلال و سرطان‌زا"},
    "c7h8": {"name": "تولوئن", "formula": "C7H8", "type": "Hydrocarbon", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
             "color": "#FFFFFF", "desc": "حلال رنگ و تینر، جایگزین ایمن‌تر بنزن"},
    "c8h10": {"name": "زایلن", "formula": "C8H10", "type": "Hydrocarbon", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
              "color": "#FFFFFF", "desc": "حلال در صنایع چاپ، لاستیک و چرم"},
    "c3h7oh": {"name": "ایزوپروپیل الکل", "formula": "C3H8O", "type": "Alcohol", "pH": 7.0, "molarity": 0.1,
               "heat": -13.0, "color": "#FFFFFF", "desc": "الکل مالشی، ضدعفونی‌کننده سطوح"},
    "c4h10o": {"name": "دی‌اتیل اتر", "formula": "C4H10O", "type": "Ether", "pH": 7.0, "molarity": 0.1, "heat": -6.0,
               "color": "#FFFFFF", "desc": "ماده بیهوشی قدیمی و حلال استخراج"},
    "chcl3": {"name": "کلروفرم", "formula": "CHCl3", "type": "Solvent", "pH": 7.0, "molarity": 0.1, "heat": -4.0,
              "color": "#FFFFFF", "desc": "حلال چربی و ماده بیهوشی در گذشته"},
    "ccl4": {"name": "کربن تتراکلرید", "formula": "CCl4", "type": "Solvent", "pH": 7.0, "molarity": 0.1, "heat": -2.0,
             "color": "#FFFFFF", "desc": "پاک‌کننده لکه خشک و کپسول آتش‌نشانی قدیمی"},
    "c2h4o2": {"name": "وینیل استات", "formula": "C4H6O2", "type": "Monomer", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
               "color": "#FFFFFF", "desc": "ماده اولیه چسب چوب و رنگ‌های پلاستیک"},
    "nh2ch2cooh": {"name": "گلیسین", "formula": "C2H5NO2", "type": "Amino Acid", "pH": 6.0, "molarity": 0.1,
                   "heat": 14.2, "color": "#FFFFFF", "desc": "ساده‌ترین اسید آمینه در ساختار پروتئین"},
    "c6h5cooh": {"name": "بنزوئیک اسید", "formula": "C7H6O2", "type": "Weak Acid", "pH": 2.8, "molarity": 0.1,
                 "heat": 18.0, "color": "#FFFFFF", "desc": "نگهدارنده مواد غذایی و ضد قارچ"},
    "c6h5coona": {"name": "سدیم بنزوات", "formula": "C7H5NaO2", "type": "Salt", "pH": 8.0, "molarity": 0.1, "heat": 7.8,
                  "color": "#FFFFFF", "desc": "نگهدارنده رایج در نوشابه‌ها و ترشیجات"},
    "na2siq3": {"name": "سدیم سیلیکات", "formula": "Na2SiO3", "type": "Base", "pH": 12.5, "molarity": 0.1,
                "heat": -32.0, "color": "#F5F5F5", "desc": "چسب شیشه مایع، حفاظت از تخم‌مرغ"},
    "h2c2q4": {"name": "اگزالیک اسید", "formula": "H2C2O4", "type": "Weak Acid", "pH": 1.3, "molarity": 0.1,
               "heat": 9.5, "color": "#FFFFFF", "desc": "پاک‌کننده زنگ فلزات و براق‌کننده چوب"},
    "c3h6o3": {"name": "لاکتیک اسید", "formula": "C3H6O3", "type": "Weak Acid", "pH": 2.4, "molarity": 0.1,
               "heat": -8.0, "color": "#FFFACD", "desc": "اسید شیر، عامل گرفتگی عضلات"},
    "c6h8o6": {"name": "ویتامین ث", "formula": "C6H8O6", "type": "Weak Acid", "pH": 2.5, "molarity": 0.1, "heat": 15.0,
               "color": "#FFFFFF", "desc": "اسید اسکوربیک، آنتی‌اکسیدان ضروری بدن"},
    "k2so3": {"name": "پتاسیم سولفیت", "formula": "K2SO3", "type": "Salt", "pH": 9.0, "molarity": 0.1, "heat": -12.0,
              "color": "#FFFFFF", "desc": "نگهدارنده در شراب‌سازی و عکاسی"},
    "na2sq4": {"name": "سدیم سولفات", "formula": "Na2SO4", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 1.2,
               "color": "#FFFFFF", "desc": "پرکننده پودرهای لباسشویی و صنعت شیشه"},
    "liiqh": {"name": "لیتیوم هیدروکسید", "formula": "LiOH", "type": "Strong Base", "pH": 13.0, "molarity": 0.1,
              "heat": -23.6, "color": "#FFFFFF", "desc": "جاذب دی‌اکسید کربن در سفینه‌های فضایی"},
    "beiq": {"name": "بریلیوم اکسید", "formula": "BeO", "type": "Oxide", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
             "color": "#FFFFFF", "desc": "عایق الکتریکی با رسانایی گرمایی بالا"},
    "mgcl2": {"name": "منیزیم کلرید", "formula": "MgCl2", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": -155.0,
              "color": "#FFFFFF", "desc": "کنترل گرد و غبار جاده و مکمل منیزیم"},
    "cacl2": {"name": "کلسیم کلرید", "formula": "CaCl2", "type": "Salt", "pH": 7.5, "molarity": 0.1, "heat": -81.3,
              "color": "#FFFFFF", "desc": "نمک ضد یخ جاده و جاذب رطوبت قوی"},
    "srcl2": {"name": "استرانسیم کلرید", "formula": "SrCl2", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": -31.0,
              "color": "#FFFFFF", "desc": "استفاده در خمیردندان‌های حساس"},
    "feiq": {"name": "آهن(II) اکسید", "formula": "FeO", "type": "Oxide", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
             "color": "#000000", "desc": "رنگدانه سیاه در سرامیک‌سازی"},
    "fe2q3": {"name": "آهن(III) اکسید", "formula": "Fe2O3", "type": "Oxide", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
              "color": "#8B4513", "desc": "هماتیت، زنگ آهن و رنگدانه قرمز پودری"},
    "fe3q4": {"name": "آهن(II,III) اکسید", "formula": "Fe3O4", "type": "Oxide", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
              "color": "#000000", "desc": "مگنتیت، اکسید مغناطیسی سیاه آهن"},
    "cuiq": {"name": "مس(II) اکسید", "formula": "CuO", "type": "Oxide", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
             "color": "#000000", "desc": "استفاده در لعاب‌کاری برای ایجاد رنگ سبز"},
    "cu2q": {"name": "مس(I) اکسید", "formula": "Cu2O", "type": "Oxide", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
             "color": "#B22222", "desc": "رنگدانه قرمز در شیشه و نیمه‌هادی"},
    "zno": {"name": "روی اکسید", "formula": "ZnO", "type": "Oxide", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
            "color": "#FFFFFF", "desc": "پماد زینک اکساید، محافظ پوست و ضد آفتاب"},
    "al2q3": {"name": "آلومینیوم اکسید", "formula": "Al2O3", "type": "Oxide", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
              "color": "#FFFFFF", "desc": "آلومینا، ماده ساینده و پایه کاتالیزور"},
    "siq2": {"name": "سیلیسیم دی‌اکسید", "formula": "SiO2", "type": "Oxide", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
             "color": "#FFFFFF", "desc": "ماسه کوارتز، ماده اصلی شیشه‌سازی"},
    "p4q10": {"name": "فسفر پنتااکسید", "formula": "P4O10", "type": "Acidic Oxide", "pH": 1.5, "molarity": 0.1,
              "heat": -170.0, "color": "#FFFFFF", "desc": "عامل آب‌گیر بسیار قوی در آزمایشگاه"},
    "so2": {"name": "گوگرد دی‌اکسید", "formula": "SO2", "type": "Gas", "pH": 3.0, "molarity": 0.1, "heat": -33.0,
            "color": "#FFFFFF", "desc": "گاز سمی، ایجاد باران اسیدی و سفیدکننده"},
    "so3": {"name": "گوگرد تری‌اکسید", "formula": "SO3", "type": "Oxide", "pH": 1.0, "molarity": 0.1, "heat": -90.0,
            "color": "#FFFFFF", "desc": "پیش‌ساز مستقیم اسید سولفوریک"},
    "co": {"name": "کربن مونوکسید", "formula": "CO", "type": "Gas", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
           "color": "#FFFFFF", "desc": "گاز بی‌بو و کشنده ناشی از احتراق ناقص"},
    "co2": {"name": "کربن دی‌اکسید", "formula": "CO2", "type": "Gas", "pH": 5.5, "molarity": 0.1, "heat": -20.0,
            "color": "#FFFFFF", "desc": "گاز گلخانه‌ای، یخ خشک و کپسول آتش‌نشانی"},
    "n2o": {"name": "دی‌نیتروژن مونوکسید", "formula": "N2O", "type": "Gas", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
            "color": "#FFFFFF", "desc": "گاز خنده، بیهوشی ملایم و تقویت موتور خودرو"},
    "no": {"name": "نیتروژن مونوکسید", "formula": "NO", "type": "Gas", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
           "color": "#FFFFFF", "desc": "رادیکال آزاد، نقش در انتقال پیام عصبی"},
    "no2": {"name": "نیتروژن دی‌اکسید", "formula": "NO2", "type": "Gas", "pH": 3.0, "molarity": 0.1, "heat": -15.0,
            "color": "#A52A2A", "desc": "گاز قهوه‌ای مایل به قرمز، آلاینده هوا"},
    "pbi2": {"name": "سرب(II) یدید", "formula": "PbI2", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 63.0,
             "color": "#FFFF00", "desc": "باران طلایی، استفاده در سلول‌های خورشیدی"},
    "hgi2": {"name": "جیوه(II) یدید", "formula": "HgI2", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 45.0,
             "color": "#FF4500", "desc": "ترکیب ترموکرومیک (تغییر رنگ با دما)"},
    "snf2": {"name": "قلع(II) فلورید", "formula": "SnF2", "type": "Salt", "pH": 3.5, "molarity": 0.1, "heat": 2.0,
             "color": "#FFFFFF", "desc": "فلوراید مورد استفاده در خمیردندان"},
    "naf": {"name": "سدیم فلورید", "formula": "NaF", "type": "Salt", "pH": 7.5, "molarity": 0.1, "heat": 0.9,
            "color": "#FFFFFF", "desc": "جلوگیری از پوسیدگی دندان و سم حشرات"},
    "niis": {"name": "نیکل(II) سولفید", "formula": "NiS", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
             "color": "#000000", "desc": "موجود در کانی میلریت، کاتالیزور صنعتی"},
    "zns": {"name": "روی سولفید", "formula": "ZnS", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
            "color": "#FFFFFF", "desc": "ماده فلورسنت در صفحات رادیولوژی قدیمی"},
    "cds": {"name": "کادمیوم سولفید", "formula": "CdS", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
            "color": "#FFFF00", "desc": "رنگدانه زرد کادمیوم و فتوسل‌ها"},
    "as2s3": {"name": "آرسنیک(III) سولفید", "formula": "As2S3", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
              "color": "#FFA500", "desc": "رنگدانه زرد رهج، سمی و نیمه‌هادی"},
    "sb2s3": {"name": "آنتیموان(III) سولفید", "formula": "Sb2S3", "type": "Salt", "pH": 7.0, "molarity": 0.1,
              "heat": 0.0, "color": "#2F4F4F", "desc": "سرمه چشم قدیم و چاشنی مواد منفجره"},
    "hg s": {"name": "جیوه(II) سولفید", "formula": "HgS", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
             "color": "#FF0000", "desc": "شنگرف، رنگدانه قرمز درخشان و کانی جیوه"},
    "cs2": {"name": "کربن دی‌سولفید", "formula": "CS2", "type": "Solvent", "pH": 7.0, "molarity": 0.1, "heat": -3.0,
            "color": "#FFFFFF", "desc": "حلال فسفر و گوگرد، بسیار آتش‌گیر"},
    "p4 s3": {"name": "فسفر سسکوئی‌سولفید", "formula": "P4S3", "type": "Sulfide", "pH": 7.0, "molarity": 0.1,
              "heat": 0.0, "color": "#FFFF00", "desc": "مورد استفاده در نوک کبریت‌های بی‌خطر"},
    "na n3": {"name": "سدیم آزید", "formula": "NaN3", "type": "Salt", "pH": 10.0, "molarity": 0.1, "heat": 21.0,
              "color": "#FFFFFF", "desc": "تولید گاز در کیسه هوای خودرو، بسیار سمی"},
    "k n3": {"name": "پتاسیم آزید", "formula": "KN3", "type": "Salt", "pH": 9.5, "molarity": 0.1, "heat": 25.0,
             "color": "#FFFFFF", "desc": "تجزیه حرارتی برای تولید پتاسیم خالص"},
    "h cn": {"name": "هیدروژن سیانید", "formula": "HCN", "type": "Weak Acid", "pH": 5.1, "molarity": 0.1, "heat": -20.0,
             "color": "#F0F8FF", "desc": "اسید پیروسیک، گاز فوق‌العاده سمی بوی بادام تلخ"},
    "k cn": {"name": "پتاسیم سیانید", "formula": "KCN", "type": "Salt", "pH": 11.0, "molarity": 0.1, "heat": 11.7,
             "color": "#FFFFFF", "desc": "سم مشهور، استفاده در استخراج طلا و آبکاری"},
    "na ocl": {"name": "سدیم هیپوکلریت", "formula": "NaOCl", "type": "Base", "pH": 12.0, "molarity": 0.1, "heat": -35.0,
               "color": "#FFFACD", "desc": "وایتکس، سفیدکننده و گندزدای قوی"},
    "ca ocl2": {"name": "کلسیم هیپوکلریت", "formula": "Ca(OCl)2", "type": "Base", "pH": 11.5, "molarity": 0.1,
                "heat": -40.0, "color": "#FFFFFF", "desc": "پودر کلر، ضدعفونی‌کننده آب استخر"},
    "k clo3": {"name": "پتاسیم کلرات", "formula": "KClO3", "type": "Oxidizer", "pH": 7.0, "molarity": 0.1, "heat": 41.3,
               "color": "#FFFFFF", "desc": "اکسیدکننده در سر کبریت و آتش‌بازی"},
    "k clo4": {"name": "پتاسیم پرکلرات", "formula": "KClO4", "type": "Oxidizer", "pH": 7.0, "molarity": 0.1,
               "heat": 51.0, "color": "#FFFFFF", "desc": "سوخت پیشران موشک و ترقه"},
    "nh4 clo4": {"name": "آمونیوم پرکلرات", "formula": "NH4ClO4", "type": "Oxidizer", "pH": 4.5, "molarity": 0.1,
                 "heat": 33.5, "color": "#FFFFFF", "desc": "سوخت جامد شاتل‌های فضایی"},
    "ag br": {"name": "نقره برومید", "formula": "AgBr", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 84.0,
              "color": "#FFFFE0", "desc": "ماده اصلی فیلم‌های عکاسی سیاه و سفید"},
    "ag i": {"name": "نقره یدید", "formula": "AgI", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 105.0,
             "color": "#FFFF00", "desc": "استفاده در بارورسازی ابرها برای تولید باران"},
    "ca f2": {"name": "کلسیم فلورید", "formula": "CaF2", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 13.0,
              "color": "#FFFFFF", "desc": "فلوریت، استفاده در لنزهای اپتیکال با کیفیت"},
    "ba f2": {"name": "باریم فلورید", "formula": "BaF2", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 4.0,
              "color": "#FFFFFF", "desc": "پوشش‌های ضد انعکاس و پنجره‌های مادون قرمز"},
    "mg f2": {"name": "منیزیم فلورید", "formula": "MgF2", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": -2.0,
              "color": "#FFFFFF", "desc": "پوشش لنز دوربین برای حذف بازتاب نور"},
    "cu i": {"name": "مس(I) یدید", "formula": "CuI", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 20.0,
             "color": "#F5F5DC", "desc": "تأمین ید در خوراک دام و کاتالیزور آلی"},
    "k i o3": {"name": "پتاسیم یدات", "formula": "KIO3", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 28.0,
               "color": "#FFFFFF", "desc": "یددار کردن نمک طعام برای جلوگیری از گواتر"},
    "na i o3": {"name": "سدیم یدات", "formula": "NaIO3", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 20.0,
                "color": "#FFFFFF", "desc": "ضدعفونی‌کننده و پیش‌ساز تولید ید"},
    "li b r": {"name": "لیتیوم برومید", "formula": "LiBr", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": -48.8,
               "color": "#FFFFFF", "desc": "جاذب رطوبت در سیستم‌های تهویه مطبوع"},
    "zn br2": {"name": "روی برومید", "formula": "ZnBr2", "type": "Salt", "pH": 4.0, "molarity": 0.1, "heat": -67.0,
               "color": "#FFFFFF", "desc": "مایع حفاری چاه‌های نفت و محافظ اشعه"},
    "cd cl2": {"name": "کادمیوم کلرید", "formula": "CdCl2", "type": "Salt", "pH": 5.0, "molarity": 0.1, "heat": -18.0,
               "color": "#FFFFFF", "desc": "آبکاری کادمیوم و چاپ عکس روی پارچه"},
    "al i3": {"name": "آلومینیوم یدید", "formula": "AlI3", "type": "Salt", "pH": 3.0, "molarity": 0.1, "heat": -300.0,
              "color": "#F0F8FF", "desc": "کاتالیزور در واکنش‌های تشکیل پیوند کربن-کربن"},
    "ti cl4": {"name": "تیتانیوم تتراکلرید", "formula": "TiCl4", "type": "Salt", "pH": 1.0, "molarity": 0.1,
               "heat": -160.0, "color": "#FFFFFF", "desc": "تولید تیتانیوم خالص و ایجاد پرده دود در ارتش"},
    "v2 o5": {"name": "وانادیوم پنتااکسید", "formula": "V2O5", "type": "Oxide", "pH": 3.0, "molarity": 0.1,
              "heat": -40.0, "color": "#FF8C00", "desc": "کاتالیزور تولید اسید سولفوریک در فرآیند تماسی"},
    "cr o3": {"name": "کروم تری‌اکسید", "formula": "CrO3", "type": "Acidic Oxide", "pH": 1.0, "molarity": 0.1,
              "heat": -7.0, "color": "#8B0000", "desc": "اسید کرومیک، اکسیدکننده بسیار قوی و سرطان‌زا"},
    "mn so4": {"name": "منگنز(II) سولفات", "formula": "MnSO4", "type": "Salt", "pH": 5.0, "molarity": 0.1,
               "heat": -62.0, "color": "#FFC0CB", "desc": "کود کشاورزی منگنز و افزودنی خوراک دام"},
    "co so4": {"name": "کبالت(II) سولفات", "formula": "CoSO4", "type": "Salt", "pH": 5.0, "molarity": 0.1,
               "heat": -70.0, "color": "#FF1493", "desc": "تولید باتری‌های لیتیم-یون و مکمل ویتامین B12"},
    "ni so4": {"name": "نیکل(II) سولفات", "formula": "NiSO4", "type": "Salt", "pH": 4.5, "molarity": 0.1, "heat": -80.0,
               "color": "#7FFF00", "desc": "نمک اصلی آبکاری نیکل و ساخت کاتالیزور"},
    "cd so4": {"name": "کادمیوم سولفات", "formula": "CdSO4", "type": "Salt", "pH": 5.0, "molarity": 0.1, "heat": -55.0,
               "color": "#FFFFFF", "desc": "استفاده در سلول‌های استاندارد وستون برای ولتاژ"},
    "sn so4": {"name": "قلع(II) سولفات", "formula": "SnSO4", "type": "Salt", "pH": 2.5, "molarity": 0.1, "heat": -40.0,
               "color": "#FFFFFF", "desc": "آبکاری قلع و آنودایز کردن آلومینیوم"},
    "tl2 so4": {"name": "تالیوم(I) سولفات", "formula": "Tl2SO4", "type": "Salt", "pH": 7.0, "molarity": 0.1,
                "heat": 20.0, "color": "#FFFFFF", "desc": "سم موش بسیار خطرناک (در اکثر کشورها ممنوع است)"},
    "crcl3": {"name": "کروم(III) کلرید", "formula": "CrCl3", "type": "Salt", "pH": 2.5, "molarity": 0.1, "heat": -50.0,
              "color": "#4B0082", "desc": "منبع یون کروم برای آبکاری و تولید مکمل غذایی"},
    "c10h8": {"name": "نفتالین", "formula": "C10H8", "type": "Hydrocarbon", "pH": 7.0, "molarity": 0.01, "heat": 18.1,
              "color": "#FFFFFF", "desc": "ضد بید لباس و ماده اولیه در تولید رزین‌ها"},
    "c6h5ch3": {"name": "تولوئن", "formula": "C7H8", "type": "Solvent", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
                "color": "#FFFFFF", "desc": "حلال صنعتی در رنگ و رزین و تولید TNT"},
    "nh2conh2": {"name": "اوره", "formula": "CH4N2O", "type": "Organic Compound", "pH": 7.2, "molarity": 0.1,
                 "heat": 15.3, "color": "#FFFFFF", "desc": "کود نیتروژنه بسیار غنی و مکمل خوراک دام"},
    "c4h8o2": {"name": "اتیل استات", "formula": "C4H8O2", "type": "Ester", "pH": 7.0, "molarity": 0.1, "heat": -10.0,
               "color": "#FFFFFF", "desc": "حلال با بوی میوه، استفاده در لاک‌پاک‌کن‌ها"},
    "c2h3cl": {"name": "وینیل کلرید", "formula": "C2H3Cl", "type": "Monomer", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
               "color": "#F0F8FF", "desc": "گاز سمی، ماده اولیه برای تولید پلاستیک PVC"},
    "c2cl4": {"name": "تتراکلرواتیلن", "formula": "C2Cl4", "type": "Solvent", "pH": 7.0, "molarity": 0.1, "heat": -3.0,
              "color": "#FFFFFF", "desc": "حلال اصلی در خشک‌شویی لباس‌ها"},
    "c6h14": {"name": "هگزان", "formula": "C6H14", "type": "Alkane", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
              "color": "#FFFFFF", "desc": "حلال برای استخراج روغن‌های گیاهی از دانه‌ها"},
    "c8h18": {"name": "اوکتان", "formula": "C8H18", "type": "Alkane", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
              "color": "#FFFFFF", "desc": "جزء کلیدی بنزین برای اندازه‌گیری آرام‌سوزی"},
    "c3h6o2": {"name": "پروپیونیک اسید", "formula": "C3H6O2", "type": "Weak Acid", "pH": 3.9, "molarity": 0.1,
               "heat": -0.7, "color": "#FDF5E6", "desc": "نگهدارنده در خوراک دام و محصولات نانوایی"},
    "c4h10": {"name": "بوتان", "formula": "C4H10", "type": "Gas", "pH": 7.0, "molarity": 0.1, "heat": -21.0,
              "color": "#FFFFFF", "desc": "گاز فندک و جزء اصلی گاز مایع LPG"},
    "c5h12": {"name": "پنتان", "formula": "C5H12", "type": "Alkane", "pH": 7.0, "molarity": 0.1, "heat": -0.5,
              "color": "#FFFFFF", "desc": "عامل پف‌دهنده در تولید فوم پلی‌استایرن"},
    "c6h5cl": {"name": "کلروبنزن", "formula": "C6H5Cl", "type": "Solvent", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
               "color": "#FFFFFF", "desc": "واسطه شیمیایی در تولید آفت‌کش‌ها و پلیمرها"},
    "c6h5nh2": {"name": "آنیلین", "formula": "C6H5NH2", "type": "Weak Base", "pH": 8.8, "molarity": 0.1, "heat": 1.9,
                "color": "#F5DEB3", "desc": "پایه اصلی ساخت رنگ‌های نساجی و داروها"},
    "c6h5no2": {"name": "نیتروبنزن", "formula": "C6H5NO2", "type": "Organic Compound", "pH": 7.0, "molarity": 0.1,
                "heat": 0.0, "color": "#FFFFE0", "desc": "ماده اولیه تولید آنیلین با بوی بادام تلخ"},
    "c2h5oc2h5": {"name": "دی‌اتیل اتر", "formula": "C4H10O", "type": "Ether", "pH": 7.0, "molarity": 0.1, "heat": -6.7,
                  "color": "#FFFFFF", "desc": "حلال استخراجی با فراریت بسیار بالا"},
    "ch3coch3": {"name": "استون", "formula": "C3H6O", "type": "Solvent", "pH": 7.0, "molarity": 0.1, "heat": -0.8,
                 "color": "#FFFFFF", "desc": "حلال جهانی برای رزین‌ها و چسب‌ها"},
    "c4h9oh": {"name": "نرمال بوتانول", "formula": "C4H10O", "type": "Alcohol", "pH": 7.0, "molarity": 0.1,
               "heat": -9.3, "color": "#FFFFFF", "desc": "حلال در لاک‌ها و ماده اولیه پلاستیک‌سازها"},
    "c5h11oh": {"name": "آمیل الکل", "formula": "C5H12O", "type": "Alcohol", "pH": 7.0, "molarity": 0.1, "heat": -10.0,
                "color": "#FFFFFF", "desc": "استفاده در تولید اسانس‌های میوه‌ای مصنوعی"},
    "ch3cooh": {"name": "اسید استیک گلاسیال", "formula": "C2H4O2", "type": "Weak Acid", "pH": 2.4, "molarity": 1.0,
                "heat": -0.4, "color": "#F8F8FF", "desc": "شکل خالص اسید سرکه، حلال بسیار مهم صنعتی"},
    "hcooh": {"name": "اسید فرمیک", "formula": "CH2O2", "type": "Weak Acid", "pH": 2.3, "molarity": 0.1, "heat": -0.3,
              "color": "#FFFFFF", "desc": "ساده‌ترین اسید کربوکسیلیک، استفاده در دباغی"},
    "c2h2o4": {"name": "اسید اگزالیک", "formula": "C2H2O4", "type": "Weak Acid", "pH": 1.3, "molarity": 0.1,
               "heat": 9.5, "color": "#FFFFFF", "desc": "جداکننده کلسیم و رسوب‌زدای قوی"},
    "c7h6o2": {"name": "اسید بنزوئیک", "formula": "C7H6O2", "type": "Weak Acid", "pH": 2.8, "molarity": 0.1,
               "heat": 18.0, "color": "#FFFFFF", "desc": "نگهدارنده غذایی و پیش‌ساز سنتز ترکیبات آلی"},
    "c8h6o4": {"name": "فتالیک اسید", "formula": "C8H6O4", "type": "Weak Acid", "pH": 2.0, "molarity": 0.1,
               "heat": 15.0, "color": "#FFFFFF", "desc": "ماده اولیه تولید رنگدانه‌های فتالوسیانین"},
    "c4h4o4": {"name": "مالئیک اسید", "formula": "C4H4O4", "type": "Weak Acid", "pH": 1.9, "molarity": 0.1,
               "heat": 18.5, "color": "#FFFFFF", "desc": "استفاده در تولید رزین‌های پلی‌استر ناپیوسته"},
    "c4h6o4": {"name": "سوکینیک اسید", "formula": "C4H6O4", "type": "Weak Acid", "pH": 2.7, "molarity": 0.1,
               "heat": 27.0, "color": "#FFFFFF", "desc": "تنظیم‌کننده اسیدیته در صنایع غذایی"},
    "c6h10o4": {"name": "آدیپیک اسید", "formula": "C6H10O4", "type": "Weak Acid", "pH": 2.7, "molarity": 0.1,
                "heat": 35.0, "color": "#FFFFFF", "desc": "ماده اولیه اصلی برای تولید نایلون ۶،۶"},
    "c3h4o4": {"name": "مالونیک اسید", "formula": "C3H4O4", "type": "Weak Acid", "pH": 2.2, "molarity": 0.1,
               "heat": 19.0, "color": "#FFFFFF", "desc": "واسطه در سنتز داروها و ویتامین‌های B1 و B6"},
    "c18h36o2": {"name": "استئاریک اسید", "formula": "C18H36O2", "type": "Fatty Acid", "pH": 6.5, "molarity": 0.1,
                 "heat": 0.0, "color": "#FFFFFF", "desc": "اسید چرب اشباع، استفاده در شمع‌سازی و لوازم آرایشی"},
    "c16h32o2": {"name": "پالمیتیک اسید", "formula": "C16H32O2", "type": "Fatty Acid", "pH": 6.5, "molarity": 0.1,
                 "heat": 0.0, "color": "#FFFFFF", "desc": "رایج‌ترین اسید چرب موجود در روغن نخل"},
    "c18h34o2": {"name": "اولئیک اسید", "formula": "C18H34O2", "type": "Fatty Acid", "pH": 6.0, "molarity": 0.1,
                 "heat": 0.0, "color": "#FFFFF0", "desc": "اسید چرب غیراشباع موجود در روغن زیتون"},
    "c6h5cho": {"name": "بنزآلدئید", "formula": "C7H6O", "type": "Aldehyde", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
                "color": "#F5F5DC", "desc": "اسانس بادام تلخ، استفاده در عطرسازی و طعم‌دهنده"},
    "ch2o": {"name": "فرمالدئید", "formula": "CH2O", "type": "Aldehyde", "pH": 4.0, "molarity": 0.1, "heat": -62.0,
             "color": "#F0FFFF", "desc": "محلول فرمالین، نگهدارنده بافت‌های بیولوژیک"},
    "ch3cho": {"name": "استالدئید", "formula": "C2H4O", "type": "Aldehyde", "pH": 7.0, "molarity": 0.1, "heat": -17.0,
               "color": "#FFFFFF", "desc": "واسطه در تولید اسید استیک و مواد معطر"},
    "c3h4o": {"name": "آکرولئین", "formula": "C3H4O", "type": "Aldehyde", "pH": 7.0, "molarity": 0.1, "heat": -15.0,
              "color": "#FFFFE0", "desc": "بسیار بدبو و تحریک‌کننده، حاصل از سوختن روغن‌ها"},
    "c3h6o": {"name": "پروپیلن اکسید", "formula": "C3H6O", "type": "Epoxide", "pH": 7.0, "molarity": 0.1, "heat": -1.0,
              "color": "#FFFFFF", "desc": "ماده اولیه برای تولید پلی‌یورتان‌ها"},
    "c2h4o": {"name": "اتیلن اکسید", "formula": "C2H4O", "type": "Epoxide", "pH": 7.0, "molarity": 0.1, "heat": -6.0,
              "color": "#FFFFFF", "desc": "گاز استریل‌کننده تجهیزات پزشکی حساس"},
    "c4h8o": {"name": "تتراهیدروفوران", "formula": "C4H8O", "type": "Ether", "pH": 7.0, "molarity": 0.1, "heat": -15.0,
              "color": "#FFFFFF", "desc": "حلال THF، بسیار موثر برای حل کردن PVC"},
    "c4h8o2": {"name": "دی‌اکسان", "formula": "C4H8O2", "type": "Ether", "pH": 7.0, "molarity": 0.1, "heat": -5.0,
               "color": "#FFFFFF", "desc": "حلال قطبی آپروتیک در واکنش‌های آزمایشگاهی"},
    "c5h5n": {"name": "پیریدین", "formula": "C5H5N", "type": "Weak Base", "pH": 8.5, "molarity": 0.1, "heat": -20.0,
              "color": "#FFFFF0", "desc": "حلال آلی با بوی بسیار تند و ناخوشایند"},
    "c4h5n": {"name": "پیرول", "formula": "C4H5N", "type": "Organic Compound", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
              "color": "#FDF5E6", "desc": "جزء اصلی ساختار هموگلوبین و کلروفیل"},
    "c4h4o": {"name": "فوران", "formula": "C4H4O", "type": "Organic Compound", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
              "color": "#FFFFFF", "desc": "ترکیب هتروسیکل معطر ساده"},
    "c4h4s": {"name": "تیوفن", "formula": "C4H4S", "type": "Organic Compound", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
              "color": "#FFFFFF", "desc": "مشابه بنزن، موجود در قطران زغال سنگ"},
    "c10h14n2": {"name": "نیکوتین", "formula": "C10H14N2", "type": "Alkaloid", "pH": 10.2, "molarity": 0.1, "heat": 0.0,
                 "color": "#F5F5DC", "desc": "آلکالوئید سمی موجود در گیاه تنباکو"},
    "c8h10n4o2": {"name": "کافئین", "formula": "C8H10N4O2", "type": "Alkaloid", "pH": 6.9, "molarity": 0.01,
                  "heat": 5.0, "color": "#FFFFFF", "desc": "محرک سیستم عصبی موجود در قهوه و چای"},
    "c17h19no3": {"name": "مورفین", "formula": "C17H19NO3", "type": "Alkaloid", "pH": 8.5, "molarity": 0.01,
                  "heat": 0.0, "color": "#FFFFFF", "desc": "مسکن بسیار قوی مشتق از اپیوم"},
    "c20h24n2o2": {"name": "کینین", "formula": "C20H24N2O2", "type": "Alkaloid", "pH": 8.8, "molarity": 0.01,
                   "heat": 0.0, "color": "#FFFFFF", "desc": "داروی کلاسیک برای درمان مالاریا"},
    "c21h22n2o2": {"name": "استریکنین", "formula": "C21H22N2O2", "type": "Alkaloid", "pH": 9.0, "molarity": 0.1,
                   "heat": 0.0, "color": "#FFFFFF", "desc": "سم بسیار قوی و تشنج‌آور عصبی"},
    "c22h25no6": {"name": "کلشیسین", "formula": "C22H25NO6", "type": "Alkaloid", "pH": 7.0, "molarity": 0.1,
                  "heat": 0.0, "color": "#FFFFE0", "desc": "داروی درمان نقرس و القای پلی‌پلوئیدی در گیاهان"},
    "c6h12o6": {"name": "فروکتوز", "formula": "C6H12O6", "type": "Sugar", "pH": 7.0, "molarity": 0.1, "heat": 13.0,
                "color": "#FFFFFF", "desc": "قند میوه، شیرین‌ترین قند طبیعی"},
    "c6h12o6-gal": {"name": "گالاکتوز", "formula": "C6H12O6", "type": "Sugar", "pH": 7.0, "molarity": 0.1, "heat": 12.0,
                    "color": "#FFFFFF", "desc": "قند موجود در محصولات لبنی"},
    "c12h22o11-lac": {"name": "لاکتوز", "formula": "C12H22O11", "type": "Sugar", "pH": 7.0, "molarity": 0.1,
                      "heat": 10.0, "color": "#FFFFFF", "desc": "قند شیر، تشکیل شده از گلوکز و گالاکتوز"},
    "c12h22o11-mal": {"name": "مالتوز", "formula": "C12H22O11", "type": "Sugar", "pH": 7.0, "molarity": 0.1,
                      "heat": 9.0, "color": "#FFFFFF", "desc": "قند جوانه جو، محصول هضم نشاسته"},
    "c6h14o6": {"name": "سوربیتول", "formula": "C6H14O6", "type": "Sugar Alcohol", "pH": 7.0, "molarity": 0.1,
                "heat": 18.0, "color": "#FFFFFF", "desc": "شیرین‌کننده رژیمی و ملین"},
    "c3h8o3": {"name": "گلیسرول", "formula": "C3H8O3", "type": "Alcohol", "pH": 7.0, "molarity": 0.1, "heat": -5.5,
               "color": "#FFFFFF", "desc": "پایه چربی‌ها، استفاده در صنایع آرایشی و دارویی"},
    "c2h4(oh)2": {"name": "اتیلن گلیکول", "formula": "C2H6O2", "type": "Alcohol", "pH": 7.0, "molarity": 0.1,
                  "heat": -6.0, "color": "#FFFFFF", "desc": "ضدیخ و ماده اولیه پلی‌استر"},
    "c3h6(oh)2": {"name": "پروپیلن گلیکول", "formula": "C3H8O2", "type": "Alcohol", "pH": 7.0, "molarity": 0.1,
                  "heat": -8.0, "color": "#FFFFFF", "desc": "حامل دارو و جایگزین غیرسمی ضدیخ"},
    "c6h5ch=ch2": {"name": "استایرن", "formula": "C8H8", "type": "Monomer", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
                   "color": "#FFFFFF", "desc": "ماده اولیه تولید یونولیت و پلاستیک‌های شفاف"},
    "c2h3no": {"name": "آکریل‌آمید", "formula": "C3H5NO", "type": "Monomer", "pH": 7.0, "molarity": 0.1, "heat": -15.0,
               "color": "#FFFFFF", "desc": "تشکیل شده در غذاهای سرخ شده، سمی برای اعصاب"},
    "c3h3n": {"name": "آکریلونیتریل", "formula": "C3H3N", "type": "Monomer", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
              "color": "#FFFFFF", "desc": "ماده اولیه تولید الیاف آکریلیک و پلاستیک ABS"},
    "ch3cooch=ch2": {"name": "وینیل استات", "formula": "C4H6O2", "type": "Monomer", "pH": 7.0, "molarity": 0.1,
                     "heat": 0.0, "color": "#FFFFFF", "desc": "ماده اصلی چسب چوب سفید"},
    "c5h8o2": {"name": "متیل متاکریلات", "formula": "C5H8O2", "type": "Monomer", "pH": 7.0, "molarity": 0.1,
               "heat": 0.0, "color": "#FFFFFF", "desc": "ماده اولیه تولید شیشه اکریلیک یا پلکسی‌گلاس"},
    "c2h5nh2": {"name": "اتیل آمین", "formula": "C2H7N", "type": "Weak Base", "pH": 11.8, "molarity": 0.1,
                "heat": -25.0, "color": "#FFFFFF", "desc": "گاز با بوی آمونیاک، استفاده در تولید علف‌کش‌ها"},
    "ch3nh2": {"name": "متیل آمین", "formula": "CH5N", "type": "Weak Base", "pH": 11.9, "molarity": 0.1, "heat": -23.0,
               "color": "#FFFFFF", "desc": "واسطه شیمیایی در سنتز داروها مانند آدرنالین"},
    "(ch3)2nh": {"name": "دی‌متیل آمین", "formula": "C2H7N", "type": "Weak Base", "pH": 11.7, "molarity": 0.1,
                 "heat": -20.0, "color": "#FFFFFF", "desc": "استفاده در شتاب‌دهنده‌های لاستیک‌سازی"},
    "(ch3)3n": {"name": "تری‌متیل آمین", "formula": "C3H9N", "type": "Weak Base", "pH": 11.3, "molarity": 0.1,
                "heat": -18.0, "color": "#FFFFFF", "desc": "عامل بوی ماهی گندیده، استفاده در تولید مواد ضدعفونی"},
    "c2h4(nh2)2": {"name": "اتیلن دی‌آمین", "formula": "C2H8N2", "type": "Base", "pH": 11.5, "molarity": 0.1,
                   "heat": -30.0, "color": "#F0F8FF", "desc": "عامل کی‌لیت‌کننده برای جذب فلزات سنگین"},
    "c10h16n2o8": {"name": "EDTA", "formula": "C10H16N2O8", "type": "Chelating Agent", "pH": 2.5, "molarity": 0.1,
                   "heat": 0.0, "color": "#FFFFFF", "desc": "حذف‌کننده سختی آب و درمان مسمومیت سربی"},
    "na2edta": {"name": "سدیم ادتا", "formula": "C10H14N2Na2O8", "type": "Salt", "pH": 4.5, "molarity": 0.1,
                "heat": 5.0, "color": "#FFFFFF", "desc": "نگهدارنده در محصولات آرایشی و خونی"},
    "c6h12n4": {"name": "هگزامین", "formula": "C6H12N4", "type": "Salt", "pH": 8.5, "molarity": 0.1, "heat": 20.0,
                "color": "#FFFFFF", "desc": "قرص سوخت الکلی و داروی عفونت مجاری ادرار"},
    "cnh3": {"name": "سیانامید", "formula": "CH2N2", "type": "Organic Compound", "pH": 7.0, "molarity": 0.1,
             "heat": -10.0, "color": "#FFFFFF", "desc": "استفاده در کشاورزی برای شکستن خواب جوانه‌ها"},
    "h2nnh2": {"name": "هیدرازین", "formula": "H4N2", "type": "Base", "pH": 10.5, "molarity": 0.1, "heat": -18.0,
               "color": "#FFFFFF", "desc": "سوخت موشک و عامل اکسیژن‌زدا در دیگ‌های بخار"},
    "nh2oh": {"name": "هیدروکسیل آمین", "formula": "H3NO", "type": "Weak Base", "pH": 9.0, "molarity": 0.1,
              "heat": -5.0, "color": "#FFFFFF", "desc": "عامل کاهنده در سنتز نایلون و داروسازی"},
    "nano3": {"name": "سدیم نیترات", "formula": "NaNO3", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 20.5,
              "color": "#FFFFFF", "desc": "شوره شیلی، کود و نگهدارنده گوشت"},
    "k2s": {"name": "پتاسیم سولفید", "formula": "K2S", "type": "Base", "pH": 12.5, "molarity": 0.1, "heat": -50.0,
            "color": "#FFE4B5", "desc": "استفاده در رنگرزی و تولید کاغذ"},
    "na2s2o8": {"name": "سدیم پرسولفات", "formula": "Na2S2O8", "type": "Oxidizer", "pH": 4.0, "molarity": 0.1,
                "heat": 15.0, "color": "#FFFFFF", "desc": "حکاکی روی برد مدار چاپی (PCB)"},
    "(nh4)2s2o8": {"name": "آمونیوم پرسولفات", "formula": "(NH4)2S2O8", "type": "Oxidizer", "pH": 3.5, "molarity": 0.1,
                   "heat": 28.0, "color": "#FFFFFF", "desc": "سفیدکننده آرد و کاتالیزور پلیمریزاسیون"},
    "k2s2o5": {"name": "پتاسیم متابی‌سولفیت", "formula": "K2S2O5", "type": "Salt", "pH": 4.0, "molarity": 0.1,
               "heat": 10.0, "color": "#FFFFFF", "desc": "آنتی‌اکسیدان در آبمیوه‌ها و شراب‌سازی"},
    "na2s2o5": {"name": "سدیم متابی‌سولفیت", "formula": "Na2S2O5", "type": "Salt", "pH": 4.3, "molarity": 0.1,
                "heat": 12.0, "color": "#FFFFFF", "desc": "سفیدکننده مواد غذایی مانند میوه خشک"},
    "mg3n2": {"name": "منیزیم نیترید", "formula": "Mg3N2", "type": "Nitride", "pH": 12.0, "molarity": 0.1,
              "heat": -150.0, "color": "#F5F5DC", "desc": "محصول سوختن منیزیم در هوا"},
    "aln": {"name": "آلومینیوم نیترید", "formula": "AlN", "type": "Nitride", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
            "color": "#F0F0F0", "desc": "نیمه‌هادی با رسانایی گرمایی فوق‌العاده بالا"},
    "casi2": {"name": "کلسیم سیلیسید", "formula": "CaSi2", "type": "Silicide", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
              "color": "#C0C0C0", "desc": "استفاده در تولید فولاد و مواد آتش‌بازی"},
    "sic": {"name": "سیلیسیم کاربید", "formula": "SiC", "type": "Carbide", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
            "color": "#000000", "desc": "سمباده الماسه، بسیار سخت و مقاوم به حرارت"},
    "cac2": {"name": "کلسیم کاربید", "formula": "CaC2", "type": "Carbide", "pH": 12.5, "molarity": 0.1, "heat": -120.0,
             "color": "#808080", "desc": "سنگ کاربیت، تولید گاز استیلن با آب"},
    "al4c3": {"name": "آلومینیوم کاربید", "formula": "Al4C3", "type": "Carbide", "pH": 12.0, "molarity": 0.1,
              "heat": -180.0, "color": "#FFFF00", "desc": "تولید گاز متان در واکنش با آب"},
    "b4c": {"name": "بور کاربید", "formula": "B4C", "type": "Carbide", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
            "color": "#000000", "desc": "جلیقه ضد گلوله و میله‌های کنترل هسته‌ای"},
    "w c": {"name": "تنگستن کاربید", "formula": "WC", "type": "Carbide", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
            "color": "#696969", "desc": "ساخت مته‌ها و ابزارهای تراشکاری فوق سخت"},
    "li3n": {"name": "لیتیوم نیترید", "formula": "Li3N", "type": "Nitride", "pH": 13.0, "molarity": 0.1, "heat": -160.0,
             "color": "#8B0000", "desc": "تنها نیترید فلز قلیایی پایدار"},
    "knh2": {"name": "پتاسیم آمید", "formula": "KNH2", "type": "Strong Base", "pH": 14.0, "molarity": 0.1,
             "heat": -80.0, "color": "#FFFFFF", "desc": "باز بسیار قوی در شیمی آلی"},
    "nanh2": {"name": "سدیم آمید", "formula": "NaNH2", "type": "Strong Base", "pH": 14.0, "molarity": 0.1,
              "heat": -75.0, "color": "#FFFFFF", "desc": "سودآمید، استفاده در سنتز نیل (ایندیگو)"},
    "li h": {"name": "لیتیوم هیدرید", "formula": "LiH", "type": "Hydride", "pH": 13.0, "molarity": 0.1, "heat": -180.0,
             "color": "#FFFFFF", "desc": "ذخیره‌ساز هیدروژن و سوخت هسته‌ای"},
    "na h": {"name": "سدیم هیدرید", "formula": "NaH", "type": "Hydride", "pH": 13.5, "molarity": 0.1, "heat": -110.0,
             "color": "#F5F5F5", "desc": "پایه قوی و عامل کاهنده در شیمی آلی"},
    "ca h2": {"name": "کلسیم هیدرید", "formula": "CaH2", "type": "Hydride", "pH": 12.5, "molarity": 0.1, "heat": -190.0,
              "color": "#D3D3D3", "desc": "خشک‌کننده حلال‌های آلی"},
    "li alh4": {"name": "لیتیوم آلومینیوم هیدرید", "formula": "LiAlH4", "type": "Reducing Agent", "pH": 13.0,
                "molarity": 0.1, "heat": -15.0, "color": "#FFFFFF", "desc": "LAH، کاهنده بسیار قدرتمند در آزمایشگاه"},
    "na bh4": {"name": "سدیم بوروهیدرید", "formula": "NaBH4", "type": "Reducing Agent", "pH": 10.5, "molarity": 0.1,
               "heat": -10.0, "color": "#FFFFFF", "desc": "کاهنده ملایم و اختصاصی آلدهیدها"},
    "k b r o3": {"name": "پتاسیم برومات", "formula": "KBrO3", "type": "Oxidizer", "pH": 7.0, "molarity": 0.1,
                 "heat": 45.0, "color": "#FFFFFF", "desc": "بهبوددهنده آرد نان (در بسیاری کشورها ممنوع است)"},
    "na b r o3": {"name": "سدیم برومات", "formula": "NaBrO3", "type": "Oxidizer", "pH": 7.0, "molarity": 0.1,
                  "heat": 30.0, "color": "#FFFFFF", "desc": "استفاده در استخراج طلا و محلول‌های فر دائم مو"},
    "li cl o4": {"name": "لیتیوم پرکلرات", "formula": "LiClO4", "type": "Oxidizer", "pH": 7.0, "molarity": 0.1,
                 "heat": -26.0, "color": "#FFFFFF", "desc": "الکترولیت در باتری‌های لیتیومی و منبع اکسیژن"},
    "ba(cl o3)2": {"name": "باریم کلرات", "formula": "Ba(ClO3)2", "type": "Oxidizer", "pH": 7.0, "molarity": 0.1,
                   "heat": 25.0, "color": "#FFFFFF", "desc": "ایجاد رنگ سبز در آتش‌بازی"},
    "ag2 o": {"name": "نقره(I) اکسید", "formula": "Ag2O", "type": "Oxide", "pH": 9.0, "molarity": 0.1, "heat": -31.0,
              "color": "#2F4F4F", "desc": "استفاده در باتری‌های ساعت و کاتالیزور"},
    "hg o": {"name": "جیوه(II) اکسید", "formula": "HgO", "type": "Oxide", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
             "color": "#FF4500", "desc": "اکسید قرمز جیوه، استفاده در باتری‌های جیوه‌ای قدیمی"},

    "c9h8o4": {"name": "آسپرین", "formula": "C9H8O4", "type": "Medicine", "pH": 3.5, "molarity": 0.01, "heat": 0.0,
               "color": "#FFFFFF", "desc": "استیل‌سالیسیلیک اسید، مسکن و رقیق‌کننده خون"},
    "c8h9no2": {"name": "استامینوفن", "formula": "C8H9NO2", "type": "Medicine", "pH": 6.0, "molarity": 0.01,
                "heat": 0.0, "color": "#FFFFFF", "desc": "پاراستامول، تب‌بر و مسکن رایج"},
    "c14h11cl2no2": {"name": "دیکلوفناک", "formula": "C14H11Cl2NO2", "type": "Medicine", "pH": 4.0, "molarity": 0.01,
                     "heat": 0.0, "color": "#FFFFFF", "desc": "ضد التهاب غیر استروئیدی قوی"},
    "c13h18o2": {"name": "ایبوپروفن", "formula": "C13H18O2", "type": "Medicine", "pH": 4.5, "molarity": 0.01,
                 "heat": 0.0, "color": "#FFFFFF", "desc": "مسکن و ضد التهاب برای دردهای مفصلی"},
    "c6h6o2": {"name": "هیدروکینون", "formula": "C6H6O2", "type": "Organic Compound", "pH": 4.5, "molarity": 0.1,
               "heat": 18.0, "color": "#FFFFFF", "desc": "روشن‌کننده پوست و داروی ظهور عکس"},
    "c6h4(oh)2": {"name": "کاتکول", "formula": "C6H6O2", "type": "Organic Compound", "pH": 5.0, "molarity": 0.1,
                  "heat": 15.0, "color": "#F5F5F5", "desc": "ماده اولیه در تولید آدرنالین و حشره‌کش‌ها"},
    "c6h4(oh)2-res": {"name": "رزورسینول", "formula": "C6H6O2", "type": "Organic Compound", "pH": 5.2, "molarity": 0.1,
                      "heat": 16.0, "color": "#FFFFFF", "desc": "استفاده در درمان آکنه و چسب‌های تایر"},
    "c10h14o": {"name": "تیمول", "formula": "C10H14O", "type": "Phenol", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
                "color": "#FFFFFF", "desc": "اسانس گیاه آویشن، ضدعفونی‌کننده قوی"},
    "c10h12o2": {"name": "اوژنول", "formula": "C10H12O2", "type": "Phenol", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
                 "color": "#FFFFF0", "desc": "اسانس میخک، مسکن درد دندان"},
    "c10h20o": {"name": "منتول", "formula": "C10H20O", "type": "Alcohol", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
                "color": "#FFFFFF", "desc": "اسانس نعنا، ایجاد احساس خنکی در پوست"},
    "c10h16o": {"name": "کافور", "formula": "C10H16O", "type": "Ketone", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
                "color": "#FFFFFF", "desc": "ماده ضد بید و مسکن موضعی"},
    "c6h5oh-na": {"name": "سدیم فنولات", "formula": "C6H5ONa", "type": "Salt", "pH": 11.5, "molarity": 0.1,
                  "heat": -15.0, "color": "#FFFFFF", "desc": "واسطه در تولید آسپرین و ضدعفونی‌کننده‌ها"},
    "c6h2(no2)3oh": {"name": "پیکریک اسید", "formula": "C6H3N3O7", "type": "Strong Acid", "pH": 1.3, "molarity": 0.1,
                     "heat": 0.0, "color": "#FFFF00", "desc": "ماده منفجره زرد رنگ و رنگ‌آمیزی بافت"},
    "c7h5(no2)3": {"name": "TNT", "formula": "C7H5N3O6", "type": "Explosive", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
                   "color": "#F5F5DC", "desc": "ترینیتروتولوئن، ماده منفجره نظامی استاندارد"},
    "c3h5(no3)3": {"name": "نیتروگلیسیرین", "formula": "C3H5N3O9", "type": "Explosive", "pH": 7.0, "molarity": 0.1,
                   "heat": 0.0, "color": "#FFFFFF", "desc": "ماده اصلی دینامیت و داروی قلبی"},
    "c6h7(no3)5": {"name": "نیتروسلولوز", "formula": "C6H7N5O15", "type": "Explosive", "pH": 7.0, "molarity": 0.1,
                   "heat": 0.0, "color": "#FFFFFF", "desc": "پنبه باروتی، پایه فیلم‌های قدیمی و لاک"},
    "c2h6os": {"name": "DMSO", "formula": "C2H6OS", "type": "Solvent", "pH": 7.0, "molarity": 0.1, "heat": -18.0,
               "color": "#FFFFFF", "desc": "دی‌متیل سولفوکسید، حلال نفوذپذیر به پوست"},
    "ch3cn": {"name": "استونیتریل", "formula": "C2H3N", "type": "Solvent", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
              "color": "#FFFFFF", "desc": "حلال مهم در آنالیز HPLC"},
    "hcon(ch3)2": {"name": "DMF", "formula": "C3H7NO", "type": "Solvent", "pH": 7.0, "molarity": 0.1, "heat": -12.0,
                   "color": "#FFFFFF", "desc": "دی‌متیل فرمامید، حلال صنعتی برای الیاف مصنوعی"},
    "c4h9li": {"name": "ان-بوتیل لیتیوم", "formula": "C4H9Li", "type": "Organometallic", "pH": 14.0, "molarity": 0.1,
               "heat": -150.0, "color": "#FFFFFF", "desc": "واکنش‌گر بسیار فعال، آتش‌گیر در مجاورت هوا"},
    "(c2h5)2zn": {"name": "دی‌اتیل روی", "formula": "C4H10Zn", "type": "Organometallic", "pH": 7.0, "molarity": 0.1,
                  "heat": 0.0, "color": "#FFFFFF", "desc": "اولین ترکیب آلی فلزی ساخته شده، خودآتشگیر"},
    "pb(c2h5)4": {"name": "تترااتیل سرب", "formula": "C8H20Pb", "type": "Organometallic", "pH": 7.0, "molarity": 0.1,
                  "heat": 0.0, "color": "#FFFFFF", "desc": "افزودنی ضد کوبش بنزین‌های قدیمی (ممنوع شده)"},
    "na n h 2": {"name": "سدیم آمید", "formula": "NaNH2", "type": "Base", "pH": 14.0, "molarity": 0.1, "heat": -80.0,
                 "color": "#FFFFFF", "desc": "باز بسیار قوی برای سنتز استیلن‌ها"},
    "liclo4": {"name": "لیتیوم پرکلرات", "formula": "LiClO4", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": -26.0,
               "color": "#FFFFFF", "desc": "منبع اکسیژن در شاتل‌های فضایی"},
    "ag2cr o4": {"name": "نقره کرومات", "formula": "Ag2CrO4", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
                 "color": "#8B0000", "desc": "رسوب قرمز آجری در تیتراسیون مور"},
    "ba cr o4": {"name": "باریم کرومات", "formula": "BaCrO4", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
                 "color": "#FFFF00", "desc": "زرد باریم، رنگدانه ضد خوردگی"},
    "pb cr o4": {"name": "سرب کرومات", "formula": "PbCrO4", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
                 "color": "#FFD700", "desc": "زرد کروم، رنگدانه مورد استفاده در خط‌کشی جاده"},
    "cu(ch3coo)2": {"name": "استات مس(II)", "formula": "C4H6CuO4", "type": "Salt", "pH": 5.5, "molarity": 0.1,
                    "heat": -15.0, "color": "#008080", "desc": "سبز تیره، استفاده در حشره‌کش‌ها و کاتالیزور"},
    "pb(ch3coo)2": {"name": "استات سرب(II)", "formula": "C4H6O4Pb", "type": "Salt", "pH": 6.0, "molarity": 0.1,
                    "heat": -16.0, "color": "#FFFFFF", "desc": "شکر سرب، سمی با طعم شیرین"},
    "al(ch3coo)3": {"name": "استات آلومینیوم", "formula": "C6H9AlO6", "type": "Salt", "pH": 4.5, "molarity": 0.1,
                    "heat": 0.0, "color": "#FFFFFF", "desc": "محلول بورو، قابض پوست در پزشکی"},
    "ch3coo k": {"name": "پتاسیم استات", "formula": "C2H3KO2", "type": "Salt", "pH": 8.5, "molarity": 0.1,
                 "heat": -15.0, "color": "#FFFFFF", "desc": "یخ‌زدای باندهای فرودگاه و نگهدارنده غذا"},
    "ch3coo na": {"name": "سدیم استات", "formula": "C2H3NaO2", "type": "Salt", "pH": 8.9, "molarity": 0.1,
                  "heat": -17.0, "color": "#FFFFFF", "desc": "یخ خشک شیمیایی در کیسه‌های گرم‌کن دست"},
    "nh4 ch3coo": {"name": "آمونیوم استات", "formula": "C2H7NO2", "type": "Salt", "pH": 7.0, "molarity": 0.1,
                   "heat": 2.0, "color": "#FFFFFF", "desc": "بافر در آنالیزهای شیمیایی و تولید پروتئین"},
    "c6h5coo k": {"name": "پتاسیم بنزوات", "formula": "C7H5KO2", "type": "Salt", "pH": 8.0, "molarity": 0.1,
                  "heat": 7.0, "color": "#FFFFFF", "desc": "نگهدارنده در غذاهای اسیدی و آتش‌بازی"},
    "c2h5coo na": {"name": "سدیم پروپیونات", "formula": "C3H5NaO2", "type": "Salt", "pH": 8.5, "molarity": 0.1,
                   "heat": 0.0, "color": "#FFFFFF", "desc": "ضد کپک در نان‌های صنعتی"},
    "ca(c3h5o2)2": {"name": "کلسیم پروپیونات", "formula": "C6H10CaO4", "type": "Salt", "pH": 8.0, "molarity": 0.1,
                    "heat": 0.0, "color": "#FFFFFF", "desc": "متداول‌ترین نگهدارنده نان و فرآورده‌های گوشتی"},
    "na2 c2o4": {"name": "سدیم اگزالات", "formula": "Na2C2O4", "type": "Salt", "pH": 8.0, "molarity": 0.1, "heat": 15.0,
                 "color": "#FFFFFF", "desc": "استاندارد اولیه در پرمنگناتومتری"},
    "k h c2o4": {"name": "پتاسیم هیدروژن اگزالات", "formula": "KHC2O4", "type": "Salt", "pH": 3.5, "molarity": 0.1,
                 "heat": 20.0, "color": "#FFFFFF", "desc": "نمک ترشک، پاک‌کننده لکه جوهر و زنگار"},
    "k2 c2o4": {"name": "پتاسیم اگزالات", "formula": "K2C2O4", "type": "Salt", "pH": 8.0, "molarity": 0.1, "heat": 18.0,
                "color": "#FFFFFF", "desc": "ضد انعقاد خون در لوله‌های آزمایشگاهی"},
    "fe2(c2o4)3": {"name": "اگزالات آهن(III)", "formula": "C6Fe2O12", "type": "Salt", "pH": 3.0, "molarity": 0.1,
                   "heat": 0.0, "color": "#FFFFE0", "desc": "حساس به نور، استفاده در نقشه‌کشی بلوپرینت"},
    "k3[fe(cn)6]": {"name": "پتاسیم فریک‌سیانید", "formula": "K3FeN6C6", "type": "Complex", "pH": 7.0, "molarity": 0.1,
                    "heat": 45.0, "color": "#FF4500", "desc": "قرمز خون، استفاده در عکاسی و سخت‌کاری فولاد"},
    "k4[fe(cn)6]": {"name": "پتاسیم فروسیانید", "formula": "K4FeN6C6", "type": "Complex", "pH": 7.0, "molarity": 0.1,
                    "heat": 55.0, "color": "#FFFF00", "desc": "زرد قلیا، افزودنی نمک برای جلوگیری از کلوخه شدن"},
    "fe4[fe(cn)6]3": {"name": "آبی پروس", "formula": "C18Fe7N18", "type": "Complex", "pH": 7.0, "molarity": 0.1,
                      "heat": 0.0, "color": "#000080", "desc": "اولین رنگدانه مصنوعی، درمان مسمومیت تالیوم"},
    "na2[fe(cn)5no]": {"name": "سدیم نیتروپروساید", "formula": "C5FeN6Na2O", "type": "Medicine", "pH": 7.0,
                       "molarity": 0.1, "heat": 0.0, "color": "#8B0000", "desc": "کاهنده سریع فشار خون در اورژانس"},
    "ni(cn)2": {"name": "نیکل سیانید", "formula": "C2N2Ni", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
                "color": "#90EE90", "desc": "استفاده در متالورژی و آبکاری"},
    "cu(cn)": {"name": "مس(I) سیانید", "formula": "CuCN", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
               "color": "#FFFFFF", "desc": "کاتالیزور در واکنش‌های جفت‌شدن آلی"},
    "ag cn": {"name": "نقره سیانید", "formula": "AgCN", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
              "color": "#FFFFFF", "desc": "استفاده در آبکاری نقره با کیفیت بالا"},
    "au cn": {"name": "طلا(I) سیانید", "formula": "AuCN", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
              "color": "#FFFF00", "desc": "ماده واسطه در استخراج طلا و آبکاری طلا"},
    "hg(cn)2": {"name": "جیوه(II) سیانید", "formula": "C2HgN2", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
                "color": "#FFFFFF", "desc": "تنها سیانید فلزی محلول در آب که یونیزه نمی‌شود"},
    "pb(scn)2": {"name": "سرب(II) تیوسیانات", "formula": "C2N2PbS2", "type": "Salt", "pH": 7.0, "molarity": 0.1,
                 "heat": 0.0, "color": "#FFFFFF", "desc": "استفاده در چاشنی‌های انفجاری و مسابقات تیراندازی"},
    "k scn": {"name": "پتاسیم تیوسیانات", "formula": "KSCN", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 24.0,
              "color": "#FFFFFF", "desc": "معرف شناسایی آهن(III) با ایجاد رنگ قرمز خونی"},
    "nh4 scn": {"name": "آمونیوم تیوسیانات", "formula": "CH4N2S", "type": "Salt", "pH": 5.0, "molarity": 0.1,
                "heat": 22.0, "color": "#FFFFFF", "desc": "تولید علف‌کش‌ها و مواد عکاسی"},
    "hg(scn)2": {"name": "جیوه(II) تیوسیانات", "formula": "C2HgN2S2", "type": "Salt", "pH": 7.0, "molarity": 0.1,
                 "heat": 0.0, "color": "#FFFFFF", "desc": "مار فرعون، در اثر حرارت به شدت متورم می‌شود"},
    "nh4 h2 po4": {"name": "مونوآمونیوم فسفات", "formula": "H6NO4P", "type": "Salt", "pH": 4.5, "molarity": 0.1,
                   "heat": 16.0, "color": "#FFFFFF", "desc": "کود شیمیایی MAP و کپسول آتش‌نشانی پودری"},
    "(nh4)2 h po4": {"name": "دی‌آمونیوم فسفات", "formula": "H9N2O4P", "type": "Salt", "pH": 8.0, "molarity": 0.1,
                     "heat": 14.0, "color": "#FFFFFF", "desc": "کود فسفره DAP و تاخیرانداز شعله"},
    "ca(h2 po4)2": {"name": "مونوکلسیم فسفات", "formula": "C4H12CaO8P2", "type": "Salt", "pH": 3.0, "molarity": 0.1,
                    "heat": 0.0, "color": "#FFFFFF", "desc": "بکینگ پودر و مکمل کلسیم دام"},
    "ca h po4": {"name": "دی‌کلسیم فسفات", "formula": "CaHPO4", "type": "Salt", "pH": 7.2, "molarity": 0.1, "heat": 0.0,
                 "color": "#FFFFFF", "desc": "استفاده در خمیردندان و غنی‌سازی غلات"},
    "ca3 (po4)2": {"name": "تری‌کلسیم فسفات", "formula": "Ca3O8P2", "type": "Salt", "pH": 7.5, "molarity": 0.1,
                   "heat": 0.0, "color": "#FFFFFF", "desc": "خاکستر استخوان، ماده اولیه تولید فسفر"},
    "ag3 po4": {"name": "نقره فسفات", "formula": "Ag3PO4", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
                "color": "#FFFF00", "desc": "رسوب زرد رنگ، استفاده در رنگ‌آمیزی بیولوژیک"},
    "zn3 (po4)2": {"name": "روی فسفات", "formula": "O8P2Zn3", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
                   "color": "#FFFFFF", "desc": "سیمان دندانپزشکی و پوشش ضد زنگ فلزات"},
    "na5 p3 o10": {"name": "سدیم تری‌پلی‌فسفات", "formula": "Na5P3O10", "type": "Salt", "pH": 9.7, "molarity": 0.1,
                   "heat": -50.0, "color": "#FFFFFF", "desc": "سخت‌گیر آب در پودرهای شوینده"},
    "h4 p2 o7": {"name": "پیروفسفریک اسید", "formula": "H4P2O7", "type": "Acid", "pH": 1.1, "molarity": 0.1,
                 "heat": 0.0, "color": "#FFFFFF", "desc": "عامل فسفریله کردن در بیوشیمی"},
    "h po3": {"name": "متافسفریک اسید", "formula": "HPO3", "type": "Acid", "pH": 1.5, "molarity": 0.1, "heat": 0.0,
              "color": "#FFFFFF", "desc": "فرم شیشه‌ای اسید فسفریک"},
    "h3 po2": {"name": "هیپوفسفرو اسید", "formula": "H3PO2", "type": "Acid", "pH": 1.2, "molarity": 0.1, "heat": 0.0,
               "color": "#FFFFFF", "desc": "عامل کاهنده قوی برای آبکاری الکترولس"},
    "ph3": {"name": "فسفین", "formula": "PH3", "type": "Gas", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
            "color": "#FFFFFF", "desc": "گاز فوق‌العاده سمی با بوی ماهی گنده، آفت‌کش غلات"},
    "pcl3": {"name": "فسفر تریکلرید", "formula": "PCl3", "type": "Salt", "pH": 1.0, "molarity": 0.1, "heat": -280.0,
             "color": "#FFFFFF", "desc": "مایع خورنده، واسطه در تولید آفت‌کش‌ها"},
    "pcl5": {"name": "فسفر پنتاکلرید", "formula": "PCl5", "type": "Salt", "pH": 1.0, "molarity": 0.1, "heat": -350.0,
             "color": "#FDF5E6", "desc": "عامل کلردار کننده قوی در شیمی آلی"},
    "pocl3": {"name": "فسفریل کلرید", "formula": "POCl3", "type": "Salt", "pH": 1.0, "molarity": 0.1, "heat": -250.0,
              "color": "#FFFFFF", "desc": "تولید استرهای فسفات و پلاستیک‌سازها"},
    "pscl3": {"name": "تیوفسفریل کلرید", "formula": "PSCl3", "type": "Salt", "pH": 1.0, "molarity": 0.1, "heat": 0.0,
              "color": "#FFFFFF", "desc": "واسطه ساخت حشره‌کش‌های فسفره سمی"},
    "na h s o3": {"name": "سدیم بی‌سولفیت", "formula": "NaHSO3", "type": "Salt", "pH": 4.5, "molarity": 0.1,
                  "heat": 0.0, "color": "#FFFFFF", "desc": "حذف کلر اضافی از آب تصفیه شده"},
    "na2 s2 o4": {"name": "سدیم دی‌تیونیت", "formula": "Na2S2O4", "type": "Salt", "pH": 7.0, "molarity": 0.1,
                  "heat": -80.0, "color": "#FFFFFF", "desc": "پودر کاهنده، رنگ‌بری از پارچه و خمیر کاغذ"},
    "na2 s o3": {"name": "سدیم سولفیت", "formula": "Na2SO3", "type": "Salt", "pH": 9.5, "molarity": 0.1, "heat": -11.0,
                 "color": "#FFFFFF", "desc": "جلوگیری از اکسایش در میوه‌های خشک"},
    "na2 s o4 . 10h2o": {"name": "نمک گلوبر", "formula": "H20Na2O14S", "type": "Salt", "pH": 7.0, "molarity": 0.1,
                         "heat": 78.0, "color": "#FFFFFF", "desc": "ملین قوی و استفاده در رنگرزی پنبه"},
    "mg so4 . 7h2o": {"name": "نمک اپسوم", "formula": "H14MgO11S", "type": "Salt", "pH": 6.0, "molarity": 0.1,
                      "heat": 16.0, "color": "#FFFFFF", "desc": "نمک حمام، تسکین‌دهنده دردهای عضلانی"},
    "cu so4 . 5h2o": {"name": "کات‌کبود", "formula": "H10CuO9S", "type": "Salt", "pH": 4.0, "molarity": 0.1,
                      "heat": 11.0, "color": "#0000FF", "desc": "ضد جلبک و باکتری در کشاورزی"},
    "fe so4 . 7h2o": {"name": "زاج سبز", "formula": "H14FeO11S", "type": "Salt", "pH": 3.5, "molarity": 0.1,
                      "heat": 14.0, "color": "#90EE90", "desc": "تأمین آهن خاک و تولید مرکب سیاه"},
    "zn so4 . 7h2o": {"name": "زاج سفید روی", "formula": "H14O11SZn", "type": "Salt", "pH": 4.5, "molarity": 0.1,
                      "heat": 13.0, "color": "#FFFFFF", "desc": "پیشگیری از خزه بستن و مکمل غذایی روی"},
    "k al(so4)2 . 12h2o": {"name": "زاج عطار", "formula": "H24AlKO20S2", "type": "Salt", "pH": 3.3, "molarity": 0.1,
                           "heat": 0.0, "color": "#FFFFFF", "desc": "منعقدکننده خون (قلم اصلاح) و تصفیه آب"},
    "nh4 al(so4)2 . 12h2o": {"name": "زاج آمونیوم", "formula": "H28AlNO20S2", "type": "Salt", "pH": 3.5,
                             "molarity": 0.1, "heat": 0.0, "color": "#FFFFFF",
                             "desc": "استفاده در پودر پخت و تصفیه فاضلاب"},
    "k fe(so4)2 . 12h2o": {"name": "زاج آهن", "formula": "H24FeKO20S2", "type": "Salt", "pH": 2.0, "molarity": 0.1,
                           "heat": 0.0, "color": "#E6E6FA", "desc": "رنگرزی و دباغی چرم"},
    "h2 se o3": {"name": "سلنو اسید", "formula": "H2SeO3", "type": "Acid", "pH": 2.5, "molarity": 0.1, "heat": 0.0,
                 "color": "#FFFFFF", "desc": "رنگ‌آمیزی فولاد و مس به رنگ سیاه"},
    "h2 se o4": {"name": "سلنیک اسید", "formula": "H2SeO4", "type": "Strong Acid", "pH": 1.0, "molarity": 0.1,
                 "heat": 0.0, "color": "#FFFFFF", "desc": "تنها اسیدی که می‌تواند طلا را در خود حل کند"},
    "se o2": {"name": "سلنیم دی‌اکسید", "formula": "SeO2", "type": "Oxide", "pH": 2.5, "molarity": 0.1, "heat": 0.0,
              "color": "#FFFFFF", "desc": "اکسیدکننده در سنتز آلی و قرمزکننده شیشه"},
    "na2 se o3": {"name": "سدیم سلنیت", "formula": "Na2SeO3", "type": "Salt", "pH": 9.0, "molarity": 0.1, "heat": 0.0,
                  "color": "#FFFFFF", "desc": "تأمین سلنیم در مکمل‌های غذایی و خوراک دام"},
    "te o2": {"name": "تلوریم دی‌اکسید", "formula": "TeO2", "type": "Oxide", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
              "color": "#FFFFFF", "desc": "ماده تشکیل‌دهنده شیشه‌های اپتیکال خاص"},
    "h6 te o6": {"name": "تلوریک اسید", "formula": "H6TeO6", "type": "Weak Acid", "pH": 5.0, "molarity": 0.1,
                 "heat": 0.0, "color": "#FFFFFF", "desc": "تشکیل تلورات‌ها و اکسیدکننده"},
    "h f": {"name": "هیدروفلوئوریک اسید", "formula": "HF", "type": "Weak Acid", "pH": 2.1, "molarity": 0.1,
            "heat": -13.0, "color": "#FFFFFF", "desc": "بسیار خورنده، تنها اسید حل‌کننده شیشه"},
    "h i": {"name": "هیدرویدیک اسید", "formula": "HI", "type": "Strong Acid", "pH": 1.0, "molarity": 0.1, "heat": -82.0,
            "color": "#FFFFFF", "desc": "قوی‌ترین اسید هالوژن‌دار معدنی، عامل کاهنده"},
    "h f s b f5": {"name": "فلوروسنتیمونیک اسید", "formula": "H2SbF6", "type": "Superacid", "pH": -12.0,
                   "molarity": 1.0, "heat": 0.0, "color": "#FFFFFF",
                   "desc": "قوی‌ترین ابر اسید جهان، نگهداری در تفلون"},
    "f2": {"name": "فلوئور", "formula": "F2", "type": "Gas", "pH": 1.0, "molarity": 0.1, "heat": 0.0,
           "color": "#FFFFE0", "desc": "واکنش‌پذیرترین عنصر جهان، اکسیدکننده فوق‌العاده"},
    "cl2": {"name": "کلر", "formula": "Cl2", "type": "Gas", "pH": 3.0, "molarity": 0.1, "heat": -25.0,
            "color": "#ADFF2F", "desc": "گاز زرد مایل به سبز، ضدعفونی آب و سلاح شیمیایی"},
    "br2": {"name": "بروم", "formula": "Br2", "type": "Liquid", "pH": 3.5, "molarity": 0.1, "heat": -5.0,
            "color": "#A52A2A", "desc": "تنها نافلز مایع در دمای اتاق، بسیار فرار و بدبو"},
    "i2": {"name": "ید", "formula": "I2", "type": "Solid", "pH": 5.0, "molarity": 0.1, "heat": 20.0, "color": "#4B0082",
           "desc": "جامد خاکستری براق، ضدعفونی‌کننده و مورد نیاز تیروئید"},
    "i cl": {"name": "ید مونوکلرید", "formula": "ICl", "type": "Interhalogen", "pH": 2.0, "molarity": 0.1, "heat": 0.0,
             "color": "#8B0000", "desc": "معرف ویس برای اندازه‌گیری عدد یدی چربی‌ها"},
    "i f5": {"name": "ید پنتافلورید", "formula": "IF5", "type": "Interhalogen", "pH": 1.0, "molarity": 0.1, "heat": 0.0,
             "color": "#FFFFFF", "desc": "مایع بی‌رنگ، عامل فلوئوردار کننده قوی"},
    "cl f3": {"name": "کلر تری‌فلورید", "formula": "ClF3", "type": "Interhalogen", "pH": 0.0, "molarity": 1.0,
              "heat": 0.0, "color": "#FFFFFF", "desc": "بسیار خطرناک، می‌تواند آجر و بتن را به آتش بکشد"},
    "na b f4": {"name": "سدیم تترافلوروبورات", "formula": "NaBF4", "type": "Salt", "pH": 4.0, "molarity": 0.1,
                "heat": 0.0, "color": "#FFFFFF", "desc": "الکترولیت در باتری‌ها و کاتالیزور"},
    "h b f4": {"name": "فلوروبوریک اسید", "formula": "HBF4", "type": "Strong Acid", "pH": 1.0, "molarity": 0.1,
               "heat": 0.0, "color": "#FFFFFF", "desc": "استفاده در آبکاری و تولید نمک‌های دیازونیوم"},
    "k p f6": {"name": "پتاسیم هگزافلوروفسفات", "formula": "KPF6", "type": "Salt", "pH": 7.0, "molarity": 0.1,
               "heat": 0.0, "color": "#FFFFFF", "desc": "منبع یون هگزافلوروفسفات برای الکترولیت‌ها"},
    "sf6": {"name": "گوگرد هگزافلورید", "formula": "SF6", "type": "Gas", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
            "color": "#FFFFFF", "desc": "عایق الکتریکی در پست‌های برق فشار قوی"},

    "u3o8": {"name": "کیک زرد", "formula": "U3O8", "type": "Radioactive", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
             "color": "#FFFF00", "desc": "اکسید تغلیظ شده اورانیوم، ماده اولیه سوخت هسته‌ای"},
    "uf6": {"name": "اورانیوم هگزافلورید", "formula": "UF6", "type": "Radioactive", "pH": 1.0, "molarity": 0.1,
            "heat": 0.0, "color": "#F8F8FF", "desc": "ترکیب گازی مورد استفاده در سانتریفیوژ برای غنی‌سازی"},
    "puo2": {"name": "پلوتونیوم دی‌اکسید", "formula": "PuO2", "type": "Radioactive", "pH": 7.0, "molarity": 0.1,
             "heat": 0.0, "color": "#FFFFF0", "desc": "سوخت مولدهای گرما-الکتریکی در کاوشگرهای فضایی"},
    "c60": {"name": "فولرن (باکی‌بال)", "formula": "C60", "type": "Nanomaterial", "pH": 7.0, "molarity": 0.1,
            "heat": 0.0, "color": "#000000", "desc": "قفس کربنی نانومتری، استفاده در دارورسانی و روان‌کارها"},
    "cnt": {"name": "نانولوله کربنی", "formula": "C", "type": "Nanomaterial", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
            "color": "#000000", "desc": "استوانه‌های کربنی با مقاومت کششی فوق‌العاده بالا"},
    "gra": {"name": "گرافن", "formula": "C", "type": "Nanomaterial", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
            "color": "#000000", "desc": "تک‌لایه اتمی کربن، رساناترین ماده جهان"},
    "n2h4": {"name": "هیدرازین سوخت", "formula": "N2H4", "type": "Rocket Fuel", "pH": 10.5, "molarity": 1.0,
             "heat": -18.0, "color": "#FFFFFF", "desc": "سوخت موتورهای پیشران فضاپیماها و ماهواره‌ها"},
    "clo3f": {"name": "پرکلریل فلورید", "formula": "ClO3F", "type": "Oxidizer", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
              "color": "#FFFFFF", "desc": "اکسیدکننده بسیار قدرتمند در سوخت موشک"},
    "h2o2-htp": {"name": "پراکسید هیدروژن ۹۸٪", "formula": "H2O2", "type": "Propellant", "pH": 3.0, "molarity": 1.0,
                 "heat": -98.0, "color": "#F0F8FF", "desc": "غلظت بالا (HTP) برای پیشرانه‌های تک‌سوز"},
    "tio2-nano": {"name": "نانو دی‌اکسید تیتانیوم", "formula": "TiO2", "type": "Photocatalyst", "pH": 7.0,
                  "molarity": 0.1, "heat": 0.0, "color": "#FFFFFF",
                  "desc": "استفاده در شیشه‌های خودتمیزشونده و تصفیه هوا"},
    "ag-nano": {"name": "نانو نقره", "formula": "Ag", "type": "Antimicrobial", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
                "color": "#FFFFE0", "desc": "ذرات نانومتری با خاصیت آنتی‌باکتریال بسیار قوی"},
    "au-nano": {"name": "نانو طلا", "formula": "Au", "type": "Medical", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
                "color": "#800000", "desc": "استفاده در تشخیص سرطان و درمان‌های هدفمند"},
    "linimno": {"name": "NMC", "formula": "LiNiMnCoO2", "type": "Battery Material", "pH": 8.0, "molarity": 0.1,
                "heat": 0.0, "color": "#000000", "desc": "ترکیب اصلی کاتد در باتری‌های خودروهای الکتریکی"},
    "lifepo4": {"name": "LFP", "formula": "LiFePO4", "type": "Battery Material", "pH": 7.5, "molarity": 0.1,
                "heat": 0.0, "color": "#696969", "desc": "کاتد باتری‌های لیتیومی با ایمنی و طول عمر بالا"},
    "gaas": {"name": "گالیم آرسنید", "formula": "GaAs", "type": "Semiconductor", "pH": 7.0, "molarity": 0.1,
             "heat": 0.0, "color": "#808080", "desc": "ماده اصلی سلول‌های خورشیدی فضایی و رادارهای سرعت بالا"},
    "gan": {"name": "گالیم نیترید", "formula": "GaN", "type": "Semiconductor", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
            "color": "#FFFFF0", "desc": "تکنولوژی مدرن شارژرهای سریع و LEDهای آبی"},
    "cdte": {"name": "کادمیوم تلورید", "formula": "CdTe", "type": "Photovoltaic", "pH": 7.0, "molarity": 0.1,
             "heat": 0.0, "color": "#000000", "desc": "لایه نازک در پنل‌های خورشیدی ارزان‌قیمت"},
    "ito": {"name": "اکسید قلع-ایندیوم", "formula": "In2O3/SnO2", "type": "Conductor", "pH": 7.0, "molarity": 0.1,
            "heat": 0.0, "color": "#FFFFFF", "desc": "لایه شفاف و رسانا در صفحات لمسی موبایل"},
    "ybcq": {"name": "YBCO", "formula": "YBa2Cu3O7", "type": "Superconductor", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
             "color": "#000000", "desc": "ابررسانای دمای بالا (بالاتر از دمای نیتروژن مایع)"},
    "nb-ti": {"name": "نیوبیوم-تیتانیوم", "formula": "NbTi", "type": "Superconductor", "pH": 7.0, "molarity": 0.1,
              "heat": 0.0, "color": "#C0C0C0", "desc": "آلیاژ مورد استفاده در آهنرباهای قدرتمند MRI"},
    "tho2": {"name": "توریم دی‌اکسید", "formula": "ThO2", "type": "Ceramic", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
             "color": "#FFFFFF", "desc": "مقاوم‌ترین سرامیک در برابر حرارت (نقطه ذوب ۳۳۰۰ درجه)"},
    "zrc": {"name": "زیرکونیوم کاربید", "formula": "ZrC", "type": "Refractory", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
            "color": "#808080", "desc": "پوشش نازل موشک و سوخت راکتورهای اتمی نسل جدید"},
    "hf-ta-c": {"name": "هافنیم تانتالوم کاربید", "formula": "Hf-Ta-C", "type": "Refractory", "pH": 7.0,
                "molarity": 0.1, "heat": 0.0, "color": "#2F4F4F",
                "desc": "دیرگدازترین ترکیب شناخته شده با نقطه ذوب حدود ۴۰۰۰ درجه"},
    "re": {"name": "رنیوم خالص", "formula": "Re", "type": "Metal", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
           "color": "#C0C0C0", "desc": "فلز کمیاب برای ساخت موتورهای جت هواپیما"},
    "os": {"name": "اسمیوم", "formula": "Os", "type": "Metal", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
           "color": "#B0C4DE", "desc": "چگال‌ترین عنصر طبیعی (دو برابر سرب)"},
    "ir": {"name": "ایریدیوم", "formula": "Ir", "type": "Metal", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
           "color": "#FFFFFF", "desc": "مقاوم‌ترین فلز در برابر خوردگی و اسیدها"},
    "tc-99m": {"name": "تکنسیم-۹۹", "formula": "Tc", "type": "Radioisotope", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
               "color": "#C0C0C0", "desc": "پرکاربردترین رادیودارو برای تصویربرداری پزشکی"},
    "i-131": {"name": "ید-۱۳۱", "formula": "I", "type": "Radioisotope", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
              "color": "#4B0082", "desc": "درمان سرطان تیروئید و پرکاری آن"},
    "co-60": {"name": "کبالت-۶۰", "formula": "Co", "type": "Radioisotope", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
              "color": "#FFFFFF", "desc": "منبع پرتو گاما برای استریل کردن تجهیزات و درمان تومور"},
    "h3": {"name": "تریتیم", "formula": "H3", "type": "Radioactive Gas", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
           "color": "#FFFFFF", "desc": "ایزوتوپ سنگین هیدروژن، سوخت همجوشی هسته‌ای"},
    "he3": {"name": "هلیوم-۳", "formula": "He3", "type": "Stable Isotope", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
            "color": "#FFFFFF", "desc": "ایزوتوپ کمیاب، سوخت ایده‌آل همجوشی بدون پسماند رادیواکتیو"},
    "u-235": {"name": "اورانیوم-۲۳۵", "formula": "U", "type": "Radioactive", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
              "color": "#C0C0C0", "desc": "ایزوتوپ شکافت‌پذیر مورد استفاده در بمب اتم و راکتور"},
    "d2o": {"name": "آب سنگین", "formula": "D2O", "type": "Moderator", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
            "color": "#FFFFFF", "desc": "کندکننده نوترون در نیروگاه‌های هسته‌ای اراک-نوع"},
    "bef2": {"name": "بریلیوم فلورید", "formula": "BeF2", "type": "Molten Salt", "pH": 7.0, "molarity": 0.1,
             "heat": 0.0, "color": "#FFFFFF", "desc": "جزء اصلی نمک‌های مذاب در راکتورهای پیشرفته"},
    "lin03-nan": {"name": "نیترات لیتیوم-سدیم", "formula": "LiNO3/NaNO3", "type": "Thermal Storage", "pH": 8.0,
                  "molarity": 0.1, "heat": 0.0, "color": "#FFFFFF",
                  "desc": "ذخیره‌ساز انرژی گرمایی در نیروگاه‌های خورشیدی متمرکز"},
    "c4-pfoa": {"name": "PFOA", "formula": "C8HF15O2", "type": "Forever Chemical", "pH": 2.5, "molarity": 0.1,
                "heat": 0.0, "color": "#FFFFFF", "desc": "پوشش تابه تفلون، بسیار پایدار و مضر برای محیط زیست"},
    "ptfe": {"name": "تفلون", "formula": "(C2F4)n", "type": "Polymer", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
             "color": "#FFFFFF", "desc": "پلی‌تترافلوئورواتیلن، مقاوم‌ترین پلاستیک به مواد شیمیایی"},
    "kev": {"name": "کولار", "formula": "(C14H10N2O2)n", "type": "Polymer", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
            "color": "#FFFF00", "desc": "الیاف بسیار مقاوم برای جلیقه ضد گلوله"},
    "nomex": {"name": "نومکس", "formula": "(C14H10N2O2)n", "type": "Polymer", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
              "color": "#FFFFFF", "desc": "الیاف ضد حریق برای لباس آتش‌نشانان و رانندگان F1"},
    "peek": {"name": "پیک", "formula": "(C19H12O3)n", "type": "Polymer", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
             "color": "#F5DEB3", "desc": "پلیمر مهندسی فوق‌مقاوم برای قطعات هواپیما و ایمپلنت"},
    "v-gas": {"name": "گاز وی-ایکس (VX)", "formula": "C11H26NO2PS", "type": "Nerve Agent", "pH": 7.0, "molarity": 1.0,
              "heat": 0.0, "color": "#FFFFE0", "desc": "مرگبارترین سلاح شیمیایی عصبی ساخته شده"},
    "sar-gas": {"name": "گاز سارین", "formula": "C4H10FO2P", "type": "Nerve Agent", "pH": 7.0, "molarity": 1.0,
                "heat": 0.0, "color": "#FFFFFF", "desc": "عامل عصبی بی‌بو و فرار، سلاح کشتار جمعی"},
    "mus-gas": {"name": "گاز خردل", "formula": "C4H8Cl2S", "type": "Blister Agent", "pH": 7.0, "molarity": 1.0,
                "heat": 0.0, "color": "#F5F5DC", "desc": "عامل تاول‌زا، استفاده شده در جنگ جهانی اول"},
    "phos": {"name": "فسژن", "formula": "COCl2", "type": "Choking Agent", "pH": 3.0, "molarity": 0.1, "heat": 0.0,
             "color": "#FFFFFF", "desc": "گاز خفه‌کننده با بوی علف تازه، بسیار سمی"},
    "ricin": {"name": "ریسین", "formula": "Protein", "type": "Toxin", "pH": 7.0, "molarity": 0.01, "heat": 0.0,
              "color": "#FFFFFF", "desc": "سم استخراج شده از کرچک، ۶۰۰۰ برابر سمی‌تر از سیانور"},
    "botox": {"name": "سم بوتولینوم", "formula": "Protein", "type": "Toxin", "pH": 7.0, "molarity": 0.0001, "heat": 0.0,
              "color": "#FFFFFF", "desc": "سمی‌ترین ماده شناخته شده جهان، مورد استفاده در زیبایی (بوتاکس)"},
    "tetrox": {"name": "تترودوتوکسین", "formula": "C11H17N3O8", "type": "Neurotoxin", "pH": 7.0, "molarity": 0.01,
               "heat": 0.0, "color": "#FFFFFF", "desc": "سم موجود در ماهی بادکنکی (فوگو)"},
    "batra": {"name": "باتراکوتوکسین", "formula": "C31H42N2O6", "type": "Neurotoxin", "pH": 7.0, "molarity": 0.01,
              "heat": 0.0, "color": "#FFFFFF", "desc": "سم موجود در پوست قورباغه‌های نیزه‌ای سمی"},
    "c12h4cl4o2": {"name": "دی‌اکسین (TCDD)", "formula": "C12H4Cl4O2", "type": "Pollutant", "pH": 7.0, "molarity": 0.1,
                   "heat": 0.0, "color": "#FFFFFF", "desc": "سمی‌ترین آلاینده زیست‌محیطی، عامل سرطان"},
    "pcb-126": {"name": "PCB", "formula": "C12H5Cl5", "type": "Pollutant", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
                "color": "#FDF5E6", "desc": "ترکیبات کلردار عایق برق، بسیار سمی و پایدار"},
    "ddt": {"name": "DDT", "formula": "C14H9Cl5", "type": "Pesticide", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
            "color": "#FFFFFF", "desc": "حشره‌کش معروف که به دلیل اثرات زیست‌محیطی ممنوع شد"},
    "glyph": {"name": "گلیفوزیت", "formula": "C3H8NO5P", "type": "Herbicide", "pH": 2.5, "molarity": 0.1, "heat": 0.0,
              "color": "#FFFFFF", "desc": "رایج‌ترین علف‌کش جهان (راندآپ)"},
    "paraq": {"name": "پاراکوات", "formula": "C12H14N2", "type": "Herbicide", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
              "color": "#F0FFFF", "desc": "علف‌کش بسیار سمی که در صورت بلع درمان ندارد"},
    "h6-rdx": {"name": "RDX", "formula": "C3H6N6O6", "type": "Explosive", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
               "color": "#FFFFFF", "desc": "ماده منفجره با قدرت تخریب بالا، جزء اصلی C4"},
    "hmx": {"name": "HMX", "formula": "C4H8N8O8", "type": "Explosive", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
            "color": "#FFFFFF", "desc": "قوی‌ترین ماده منفجره غیر اتمی نظامی"},
    "petn": {"name": "PETN", "formula": "C5H8N4O12", "type": "Explosive", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
             "color": "#FFFFFF", "desc": "ماده منفجره حساس، مورد استفاده در فیوزهای انفجاری"},
    "cl-20": {"name": "CL-20", "formula": "C6H6N12O12", "type": "Explosive", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
              "color": "#FFFFFF", "desc": "متراکم‌ترین و قدرتمندترین ماده منفجره غیر اتمی مدرن"},
    "cu-azide": {"name": "آزید مس(II)", "formula": "Cu(N3)2", "type": "Primary Explosive", "pH": 7.0, "molarity": 0.1,
                 "heat": 0.0, "color": "#008080", "desc": "چاشنی بسیار حساس و خطرناک"},
    "pb-azide": {"name": "آزید سرب", "formula": "Pb(N3)2", "type": "Primary Explosive", "pH": 7.0, "molarity": 0.1,
                 "heat": 0.0, "color": "#FFFFFF", "desc": "چاشنی استاندارد در کلاهک‌های موشک و نارنجک"},
    "ag-fulm": {"name": "فولمینات نقره", "formula": "AgCNO", "type": "Explosive", "pH": 7.0, "molarity": 0.1,
                "heat": 0.0, "color": "#FFFFFF", "desc": "بسیار حساس، استفاده در فشفشه‌های تقه‌ای (ترقه پیازی)"},
    "hg-fulm": {"name": "فولمینات جیوه", "formula": "Hg(CNO)2", "type": "Explosive", "pH": 7.0, "molarity": 0.1,
                "heat": 0.0, "color": "#808080", "desc": "اولین چاشنی ساخته شده برای گلوله اسلحه"},
    "ni-cad": {"name": "نیکل-کادمیوم", "formula": "NiOOH/Cd", "type": "Battery Material", "pH": 11.0, "molarity": 0.1,
               "heat": 0.0, "color": "#FFFFFF", "desc": "باتری‌های قابل شارژ قدیمی با اثر حافظه"},
    "li-cob": {"name": "لیتیوم کبالت اکسید", "formula": "LiCoO2", "type": "Battery Material", "pH": 7.0,
               "molarity": 0.1, "heat": 0.0, "color": "#000000",
               "desc": "کاتد استاندارد در اکثر باتری‌های لپ‌تاپ و گوشی"},
    "graph": {"name": "گرافیت", "formula": "C", "type": "Lubricant", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
              "color": "#000000", "desc": "نرم‌کننده، مغز مداد و الکترودهای کوره قوس"},
    "diam": {"name": "الماس", "formula": "C", "type": "Abrasive", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
             "color": "#FFFFFF", "desc": "سخت‌ترین کانی طبیعی، رسانای گرمایی عالی"},
    "mos2": {"name": "مولیبدن دی‌سولفید", "formula": "MoS2", "type": "Lubricant", "pH": 7.0, "molarity": 0.1,
             "heat": 0.0, "color": "#2F4F4F", "desc": "روان‌کار خشک برای استفاده در خلاء و فضا"},
    "ws2": {"name": "تنگستن دی‌سولفید", "formula": "WS2", "type": "Lubricant", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
            "color": "#808080", "desc": "ضریب اصطکاک بسیار پایین، مقاوم به دمای بالا"},
    "bn": {"name": "نیترید بور", "formula": "BN", "type": "Lubricant", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
           "color": "#FFFFFF", "desc": "گرافیت سفید، روان‌کار در دمای بسیار بالا"},
    "c-bn": {"name": "بورازون (c-BN)", "formula": "BN", "type": "Abrasive", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
             "color": "#FFFFFF", "desc": "سخت‌ترین ماده جهان بعد از الماس"},
    "pd-cat": {"name": "پالادیوم روی کربن", "formula": "Pd/C", "type": "Catalyst", "pH": 7.0, "molarity": 0.1,
               "heat": 0.0, "color": "#000000", "desc": "کاتالیزور اصلی برای هیدروژنه کردن در داروسازی"},
    "pt-cat": {"name": "پلاتین سیاه", "formula": "Pt", "type": "Catalyst", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
               "color": "#000000", "desc": "کاتالیزور اگزوز خودرو و پیل‌های سوختی"},
    "rh-cat": {"name": "رودیوم", "formula": "Rh", "type": "Catalyst", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
               "color": "#C0C0C0", "desc": "گران‌ترین فلز گروه پلاتین، کاهش گازهای سمی اگزوز"},
    "ru-cat": {"name": "روتنیوم", "formula": "Ru", "type": "Catalyst", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
               "color": "#C0C0C0", "desc": "کاتالیزور تولید آمونیاک به روش نوین"},
    "ti-cl3": {"name": "کاتالیزور زیگلر-ناتا", "formula": "TiCl3", "type": "Catalyst", "pH": 2.0, "molarity": 0.1,
               "heat": 0.0, "color": "#4B0082", "desc": "انقلاب در تولید پلاستیک پلی‌اتیلن و پلی‌پروپیلن"},
    "v-o-c": {"name": "ترکیبات آلی فرار", "formula": "VOCs", "type": "Pollutant", "pH": 7.0, "molarity": 0.1,
              "heat": 0.0, "color": "#FFFFFF", "desc": "بخارات سمی ناشی از رنگ و بنزین، آلاینده شهرها"},
    "p-m-25": {"name": "ذرات معلق ۲.۵", "formula": "PM2.5", "type": "Pollutant", "pH": 7.0, "molarity": 0.1,
               "heat": 0.0, "color": "#808080", "desc": "ریزترین ذرات آلودگی هوا که وارد خون می‌شوند"},
    "so-x": {"name": "اکسیدهای گوگرد", "formula": "SOx", "type": "Pollutant", "pH": 2.0, "molarity": 0.1, "heat": 0.0,
             "color": "#FFFFFF", "desc": "عامل اصلی تولید مه دود و تخریب بناهای تاریخی"},
    "no-x": {"name": "اکسیدهای نیتروژن", "formula": "NOx", "type": "Pollutant", "pH": 3.0, "molarity": 0.1, "heat": 0.0,
             "color": "#A52A2A", "desc": "گازهای خروجی از موتورهای دیزلی، عامل باران اسیدی"},
    "cfc-11": {"name": "فریون-۱۱", "formula": "CCl3F", "type": "Ozone Depleting", "pH": 7.0, "molarity": 0.1,
               "heat": 0.0, "color": "#FFFFFF", "desc": "گاز یخچال قدیمی، عامل سوراخ شدن لایه ازن"},
    "hfc-134a": {"name": "فریون-۱۳۴", "formula": "CH2FCF3", "type": "Refrigerant", "pH": 7.0, "molarity": 0.1,
                 "heat": 0.0, "color": "#FFFFFF", "desc": "گاز کولر خودرو مدرن، بی‌خطر برای لایه ازن"},
    "sf6-gas": {"name": "گوگرد هگزافلورید", "formula": "SF6", "type": "Insulator", "pH": 7.0, "molarity": 0.1,
                "heat": 0.0, "color": "#FFFFFF", "desc": "قوی‌ترین گاز گلخانه‌ای (۲۴۰۰۰ برابر CO2)"},
    "li-h": {"name": "لیتیوم هیدرید", "formula": "LiH", "type": "Shielding", "pH": 13.0, "molarity": 0.1,
             "heat": -180.0, "color": "#FFFFFF", "desc": "سپر حفاظتی نوترون در فضاپیماهای هسته‌ای"},
    "pb-te": {"name": "سرب تلورید", "formula": "PbTe", "type": "Thermoelectric", "pH": 7.0, "molarity": 0.1,
              "heat": 0.0, "color": "#696969", "desc": "تبدیل مستقیم گرما به برق در کاوشگرهای فضایی"},
    "bi2te3": {"name": "بیسموت تلورید", "formula": "Bi2Te3", "type": "Thermoelectric", "pH": 7.0, "molarity": 0.1,
               "heat": 0.0, "color": "#C0C0C0", "desc": "سردکننده پلتیر، ایجاد سرما با جریان برق"},
    "y2o3": {"name": "ایتریا", "formula": "Y2O3", "type": "Ceramic", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
             "color": "#FFFFFF", "desc": "افزودنی در شیشه‌های دوربین و لیزرهای صنعتی"},
    "nd-yag": {"name": "نئودیمیم:یاگ", "formula": "Nd:Y3Al5O12", "type": "Laser", "pH": 7.0, "molarity": 0.1,
               "heat": 0.0, "color": "#EE82EE", "desc": "بلور مورد استفاده در لیزرهای جراحی و نظامی"},
    "nd-fe-b": {"name": "آهنربای نئودیمیم", "formula": "Nd2Fe14B", "type": "Magnet", "pH": 7.0, "molarity": 0.1,
                "heat": 0.0, "color": "#C0C0C0", "desc": "قوی‌ترین آهنربای دائم جهان"},
    "sm-co": {"name": "ساماریوم-کبالت", "formula": "SmCo5", "type": "Magnet", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
              "color": "#C0C0C0", "desc": "آهنربای دائم مقاوم به دمای بسیار بالا"},
    "gd-dtpa": {"name": "گادولینیوم (MRI)", "formula": "Gd-DTPA", "type": "Contrast Agent", "pH": 7.0, "molarity": 0.1,
                "heat": 0.0, "color": "#FFFFFF", "desc": "ماده حاجب برای شفاف‌سازی تصاویر MRI"},
    "eu-ox": {"name": "اکسید اروپیوم", "formula": "Eu2O3", "type": "Phosphor", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
              "color": "#FFC0CB", "desc": "ایجاد رنگ قرمز در صفحات نمایش و مانیتورها"},
    "er-glass": {"name": "شیشه اربیوم", "formula": "Er:Glass", "type": "Fiber Optic", "pH": 7.0, "molarity": 0.1,
                 "heat": 0.0, "color": "#FFB6C1", "desc": "تقویت‌کننده سیگنال در کابل‌های نوری اینترنت"},
    "lu-ag": {"name": "لوتیتیم آلومینیوم گارنت", "formula": "LuAG", "type": "Scintillator", "pH": 7.0, "molarity": 0.1,
              "heat": 0.0, "color": "#FFFFFF", "desc": "آشکارساز پرتوهای پرانرژی در اسکنرهای PET"},
    "zr-o2-y": {"name": "زیرکونیای تثبیت شده", "formula": "YSZ", "type": "Electrolyte", "pH": 7.0, "molarity": 0.1,
                "heat": 0.0, "color": "#FFFFFF", "desc": "الکترولیت در سنسور اکسیژن خودرو"},
    "nb2o5": {"name": "اکسید نیوبیوم", "formula": "Nb2O5", "type": "Optical", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
              "color": "#FFFFFF", "desc": "پوشش لنزهای دوربین با شکست نور بالا"},
    "ta2o5": {"name": "اکسید تانتالوم", "formula": "Ta2O5", "type": "Dielectric", "pH": 7.0, "molarity": 0.1,
              "heat": 0.0, "color": "#FFFFFF", "desc": "ماده اصلی در خازن‌های بسیار کوچک موبایل"},
    "re-ox": {"name": "اکسید رنیوم", "formula": "Re2O7", "type": "Catalyst", "pH": 1.0, "molarity": 0.1, "heat": 0.0,
              "color": "#FFFF00", "desc": "کاتالیزور تولید بنزین با عدد اوکتان بالا"},
    "ir-cl4": {"name": "ایریدیوم کلرید", "formula": "IrCl4", "type": "Catalyst", "pH": 2.0, "molarity": 0.1,
               "heat": 0.0, "color": "#000000", "desc": "تولید کاتالیزورهای پیل سوختی هیدروژنی"},
    "os-o4": {"name": "اسمیوم تترااکسید", "formula": "OsO4", "type": "Fixative", "pH": 7.0, "molarity": 0.1,
              "heat": 0.0, "color": "#FDF5E6", "desc": "بسیار سمی، تثبیت‌کننده چربی‌ها برای میکروسکوپ الکترونی"},
    "ru-o4": {"name": "روتنیوم تترااکسید", "formula": "RuO4", "type": "Oxidizer", "pH": 1.0, "molarity": 0.1,
              "heat": 0.0, "color": "#FFFF00", "desc": "اکسیدکننده فوق‌العاده قوی و ناپایدار"},
    "rh-cl3": {"name": "رودیوم کلرید", "formula": "RhCl3", "type": "Catalyst", "pH": 2.0, "molarity": 0.1, "heat": 0.0,
               "color": "#8B0000", "desc": "ماده اولیه برای تولید کاتالیزور ویلکینسن"},
    "au-cl3": {"name": "طلای تریکلرید", "formula": "AuCl3", "type": "Salt", "pH": 1.5, "molarity": 0.1, "heat": 0.0,
               "color": "#FFD700", "desc": "تیزاب سلطانی، مورد استفاده در آبکاری و پزشکی"},
    "pd-cl2": {"name": "پالادیوم کلرید", "formula": "PdCl2", "type": "Salt", "pH": 2.5, "molarity": 0.1, "heat": 0.0,
               "color": "#A52A2A", "desc": "سنسور تشخیص نشت گاز مونوکسید کربن"},
    "pt-cl4": {"name": "پلاتین کلرید", "formula": "PtCl4", "type": "Salt", "pH": 2.0, "molarity": 0.1, "heat": 0.0,
               "color": "#8B4513", "desc": "تهیه کاتالیزورهای ضد سرطان مانند سیس‌پلاتین"},
    "li-pf6": {"name": "لیتیوم هگزافلوروفسفات", "formula": "LiPF6", "type": "Electrolyte", "pH": 7.0, "molarity": 1.0,
               "heat": 0.0, "color": "#FFFFFF", "desc": "رایج‌ترین الکترولیت در باتری‌های لیتیوم-یون"},
    "li-bf4": {"name": "لیتیوم تترافلوروبورات", "formula": "LiBF4", "type": "Electrolyte", "pH": 4.0, "molarity": 1.0,
               "heat": 0.0, "color": "#FFFFFF", "desc": "الکترولیت باتری در دماهای بسیار پایین (تا -۴۰ درجه)"},
    "li-clo4-bat": {"name": "لیتیوم پرکلرات (باتری)", "formula": "LiClO4", "type": "Electrolyte", "pH": 7.0,
                    "molarity": 1.0, "heat": 0.0, "color": "#FFFFFF",
                    "desc": "رسانایی عالی اما خطر انفجار در صورت ضربه"},
    "lin03-bat": {"name": "نیترات لیتیوم (باتری)", "formula": "LiNO3", "type": "Additive", "pH": 7.0, "molarity": 0.1,
                  "heat": 0.0, "color": "#FFFFFF", "desc": "افزودنی برای جلوگیری از رشد دندریت در باتری لیتیوم-گوگرد"},
    "na-s": {"name": "سدیم-گوگرد", "formula": "Na2Sx", "type": "Battery Material", "pH": 12.0, "molarity": 0.1,
             "heat": 0.0, "color": "#FFFF00", "desc": "باتری‌های دما بالا برای ذخیره برق شبکه نیروگاهی"},
    "v-redox": {"name": "وانادیوم ردوکس", "formula": "V2+/V5+", "type": "Flow Battery", "pH": 1.0, "molarity": 2.0,
                "heat": 0.0, "color": "#4B0082", "desc": "باتری‌های جریانی غول‌پیکر برای ذخیره انرژی خورشیدی"},
    "zn-air": {"name": "روی-هوا", "formula": "ZnO", "type": "Battery Material", "pH": 13.0, "molarity": 0.1,
               "heat": 0.0, "color": "#FFFFFF", "desc": "باتری سمعک، با استفاده از اکسیژن هوا کار می‌کند"},
    "ni-mh": {"name": "نیکل-متال هیدرید", "formula": "NiMH", "type": "Battery Material", "pH": 11.0, "molarity": 0.1,
              "heat": 0.0, "color": "#FFFFFF", "desc": "باتری خودروهای هیبریدی مانند تویوتا پریوس"},
    "f-12": {"name": "فریون-۱۲", "formula": "CCl2F2", "type": "Ozone Depleting", "pH": 7.0, "molarity": 0.1,
             "heat": 0.0, "color": "#FFFFFF", "desc": "گاز قدیمی یخچال، تخریب‌کننده شدید لایه ازن"},
    "f-22": {"name": "فریون-۲۲", "formula": "CHClF2", "type": "Refrigerant", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
             "color": "#FFFFFF", "desc": "گاز کولر گازی‌های قدیمی، در حال حذف تدریجی"},
    "nh3-ref": {"name": "آمونیاک سردساز", "formula": "NH3", "type": "Refrigerant", "pH": 11.6, "molarity": 1.0,
                "heat": -33.0, "color": "#FFFFFF", "desc": "سردکننده سیستم‌های صنعتی بزرگ و سردخانه‌ها"},
    "co2-ref": {"name": "دی‌اکسید کربن (R744)", "formula": "CO2", "type": "Refrigerant", "pH": 5.5, "molarity": 0.1,
                "heat": -78.0, "color": "#FFFFFF", "desc": "سردکننده طبیعی و سازگار با محیط زیست"},
    "ch4-ref": {"name": "ایزوبوتان (R600a)", "formula": "C4H10", "type": "Refrigerant", "pH": 7.0, "molarity": 0.1,
                "heat": -11.0, "color": "#FFFFFF", "desc": "گاز یخچال‌های جدید خانگی"},
    "p-f-c": {"name": "پرفلوروکربن‌ها", "formula": "CF4", "type": "Greenhouse Gas", "pH": 7.0, "molarity": 0.1,
              "heat": 0.0, "color": "#FFFFFF", "desc": "گازهای صنعتی با ماندگاری ۵۰۰۰۰ سال در جو"},
    "nf3": {"name": "نیتروژن تری‌فلورید", "formula": "NF3", "type": "Etchant", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
            "color": "#FFFFFF", "desc": "تمیزکننده اتاق‌های تمیز ساخت نیمه‌هادی"},
    "wf6": {"name": "تنگستن هگزافلورید", "formula": "WF6", "type": "Precursor", "pH": 1.0, "molarity": 0.1, "heat": 0.0,
            "color": "#FFFFFF", "desc": "چگال‌ترین گاز جهان، لایه‌نشانی فلز در تراشه‌ها"},
    "sih4": {"name": "سیلان", "formula": "SiH4", "type": "Precursor", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
             "color": "#FFFFFF", "desc": "گاز مورد استفاده برای تولید سیلیکون خالص خورشیدی"},
    "b2h6": {"name": "دی‌بوران", "formula": "B2H6", "type": "Dopant", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
             "color": "#FFFFFF", "desc": "گاز سمی برای نیمه‌هادی‌ها و سوخت موشک"},
    "ph3-semi": {"name": "فسفین (نیمه‌هادی)", "formula": "PH3", "type": "Dopant", "pH": 7.0, "molarity": 0.1,
                 "heat": 0.0, "color": "#FFFFFF", "desc": "تزریق فسفر به سیلیکون برای تولید نیمه‌هادی نوع n"},
    "ash3": {"name": "آرسین", "formula": "AsH3", "type": "Dopant", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
             "color": "#FFFFFF", "desc": "فوق‌العاده سمی، استفاده در صنعت میکروالکترونیک"},
    "geh4": {"name": "ژرمان", "formula": "GeH4", "type": "Precursor", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
             "color": "#FFFFFF", "desc": "تولید فیلم‌های نازک ژرمانیوم در اپتیک"},
    "un-un-en": {"name": "اوگانسون", "formula": "Og", "type": "Superheavy", "pH": 7.0, "molarity": 0.0, "heat": 0.0,
                 "color": "#808080", "desc": "سنگین‌ترین عنصر جدول تناوبی (ساخته شده در آزمایشگاه)"},
    "am-241": {"name": "امریسیوم-۲۴۱", "formula": "Am", "type": "Radioactive", "pH": 7.0, "molarity": 0.1, "heat": 0.0,
               "color": "#C0C0C0", "desc": "منبع یونیزاسیون در سنسورهای دود خانگی"},
    "cf-252": {"name": "کالیفرنیوم-۲۵۲", "formula": "Cf", "type": "Radioactive", "pH": 7.0, "molarity": 0.1,
               "heat": 0.0, "color": "#C0C0C0", "desc": "منبع قدرتمند نوترون برای شروع راکتورهای هسته‌ای"},
    "h-f-sub": {"name": "آنتیموان پنتافلورید", "formula": "SbF5", "type": "Superacid Base", "pH": -1.0, "molarity": 1.0,
                "heat": 0.0, "color": "#FFFFFF", "desc": "جزء اصلی در تولید قوی‌ترین اسیدهای جهان"},
"h2": {"name": "هیدروژن", "formula": "H2", "type": "Gas", "pH": 7.0, "molarity": 0.01, "heat": 0.0, "color": "#FFFFFF", "desc": "سبک‌ترین گاز، سوخت پاک و واکنش‌پذیر"},
"n2": {"name": "نیتروژن", "formula": "N2", "type": "Gas", "pH": 7.0, "molarity": 0.01, "heat": 0.0, "color": "#FFFFFF", "desc": "۷۸٪ هوا، گاز بی‌اثر و ماده اولیه آمونیاک"},
"co2": {"name": "دی‌اکسید کربن", "formula": "CO2", "type": "Gas", "pH": 5.5, "molarity": 0.01, "heat": 0.0, "color": "#FFFFFF", "desc": "گاز گلخانه‌ای، محصول احتراق و تنفس"},
"co": {"name": "مونوکسید کربن", "formula": "CO", "type": "Gas", "pH": 7.0, "molarity": 0.01, "heat": 0.0, "color": "#FFFFFF", "desc": "گاز سمی بی‌بو، عامل مسمومیت"},
"cl2": {"name": "کلر", "formula": "Cl2", "type": "Gas", "pH": 7.0, "molarity": 0.01, "heat": 0.0, "color": "#FFFF00", "desc": "گاز سبز زرد سمی، ضدعفونی‌کننده آب"},
"mg": {"name": "منیزیم", "formula": "Mg", "type": "Metal", "pH": 7.0, "molarity": 1.0, "heat": 0.0, "color": "#C0C0C0", "desc": "فلز سبک، سوختن با نور سفید شدید"},
"zn": {"name": "روی", "formula": "Zn", "type": "Metal", "pH": 7.0, "molarity": 1.0, "heat": 0.0, "color": "#808080", "desc": "فلز ضد زنگ، تولید گاز هیدروژن با اسید"},
"al": {"name": "آلومینیوم", "formula": "Al", "type": "Metal", "pH": 7.0, "molarity": 1.0, "heat": 0.0, "color": "#C0C0C0", "desc": "فلز سبک و مقاوم، تولید هیدروژن با باز"},
"ca": {"name": "کلسیم", "formula": "Ca", "type": "Metal", "pH": 7.0, "molarity": 1.0, "heat": 0.0, "color": "#FFFFFF", "desc": "فلز قلیایی خاکی، واکنش شدید با آب"},
"na": {"name": "سدیم", "formula": "Na", "type": "Metal", "pH": 7.0, "molarity": 1.0, "heat": 0.0, "color": "#C0C0C0", "desc": "فلز قلیایی نرم، واکنش انفجاری با آب"},
"p4": {"name": "فسفر سفید", "formula": "P4", "type": "Element", "pH": 7.0, "molarity": 1.0, "heat": 0.0, "color": "#FFFF00", "desc": "بسیار واکنش‌پذیر، خوداشتعال در هوا و سمی"},
"so3": {"name": "تری‌اکسید گوگرد", "formula": "SO3", "type": "Oxide", "pH": 1.0, "molarity": 0.1, "heat": -100.0, "color": "#FFFFFF", "desc": "ماده اولیه تولید اسید سولفوریک، واکنش گرمازا با آب"},
"(nh4)2cr2o7": {"name": "آمونیوم دی‌کرومات", "formula": "(NH4)2Cr2O7", "type": "Salt", "pH": 4.0, "molarity": 0.1, "heat": 75.0, "color": "#FF8C00", "desc": "تجزیه گرمایی به شکل آتشفشان سبز آزمایشگاهی"},
"k2cro4": {"name": "پتاسیم کرومات", "formula": "K2CrO4", "type": "Salt", "pH": 8.5, "molarity": 0.1, "heat": 14.5, "color": "#FFFF00", "desc": "رسوب زرد، اکسیدکننده و نشانگر تیتراسیون"},
"nan3": {"name": "سدیم آزید", "formula": "NaN3", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 0.0, "color": "#FFFFFF", "desc": "تولید گاز نیتروژن سریع برای ایربگ خودرو"},
"cac2": {"name": "کلسیم کاربید", "formula": "CaC2", "type": "Salt", "pH": 7.0, "molarity": 1.0, "heat": 0.0, "color": "#808080", "desc": "تولید گاز استیلن با آب، چراغ کاربید قدیمی"},
"c3h8": {"name": "پروپان", "formula": "C3H8", "type": "Gas", "pH": 7.0, "molarity": 0.01, "heat": 0.0, "color": "#FFFFFF", "desc": "گاز کپسول آشپزخانه و سوخت BBQ"},
"c4h10": {"name": "بوتان", "formula": "C4H10", "type": "Gas", "pH": 7.0, "molarity": 0.01, "heat": 0.0, "color": "#FFFFFF", "desc": "گاز فندک و کپسول کوچک"},
"c5h12": {"name": "پنتان", "formula": "C5H12", "type": "Hydrocarbon", "pH": 7.0, "molarity": 0.1, "heat": 0.0, "color": "#FFFFFF", "desc": "جزء بنزین، مایع فرار"},
"c6h14": {"name": "هگزان", "formula": "C6H14", "type": "Hydrocarbon", "pH": 7.0, "molarity": 0.1, "heat": 0.0, "color": "#FFFFFF", "desc": "حلال آلی و جزء بنزین"},
"c7h16": {"name": "هپتان", "formula": "C7H16", "type": "Hydrocarbon", "pH": 7.0, "molarity": 0.1, "heat": 0.0, "color": "#FFFFFF", "desc": "جزء سوخت دیزل"},
"c8h18": {"name": "اکتان", "formula": "C8H18", "type": "Hydrocarbon", "pH": 7.0, "molarity": 0.1, "heat": 0.0, "color": "#FFFFFF", "desc": "جزء اصلی بنزین، معیار عدد اکتان"},
"c10h8": {"name": "نفتالین", "formula": "C10H8", "type": "Hydrocarbon", "pH": 7.0, "molarity": 0.1, "heat": 0.0, "color": "#FFFFFF", "desc": "توپ ضد بید، احتراق دودزا"},
"c2h4": {"name": "اتیلن", "formula": "C2H4", "type": "Gas", "pH": 7.0, "molarity": 0.01, "heat": 0.0, "color": "#FFFFFF", "desc": "هورمون رسیدن میوه، ماده اولیه پلی‌اتیلن"},
"c3h6": {"name": "پروپیلن", "formula": "C3H6", "type": "Gas", "pH": 7.0, "molarity": 0.01, "heat": 0.0, "color": "#FFFFFF", "desc": "ماده اولیه پلی‌پروپیلن و پلاستیک"},
"c2h2": {"name": "استیلن", "formula": "C2H2", "type": "Gas", "pH": 7.0, "molarity": 0.01, "heat": -22.0, "color": "#FFFFFF", "desc": "گاز جوشکاری، بوی سیر"},
"kscn": {"name": "پتاسیم تیوسیانات", "formula": "KSCN", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 0.0, "color": "#FFFFFF", "desc": "تست آهن(III) با رنگ قرمز خون"},
"na2c2o4": {"name": "سدیم اگزالات", "formula": "Na2C2O4", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 0.0, "color": "#FFFFFF", "desc": "تشکیل رسوب اکسالات کلسیم (سنگ کلیه)"},
"h2s": {"name": "هیدروژن سولفید", "formula": "H2S", "type": "Gas", "pH": 4.1, "molarity": 0.1, "heat": -19.7, "color": "#F5F5F5", "desc": "گاز با بوی تخم‌مرغ گندیده، بسیار سمی"},
"so2": {"name": "دی‌اکسید گوگرد", "formula": "SO2", "type": "Gas", "pH": 2.0, "molarity": 0.01, "heat": 0.0, "color": "#FFFFFF", "desc": "گاز سمی از سوختن گوگرد، عامل باران اسیدی"},
"no": {"name": "نیتریک اکسید", "formula": "NO", "type": "Gas", "pH": 7.0, "molarity": 0.01, "heat": 0.0, "color": "#FFFFFF", "desc": "گاز بی‌رنگ، تبدیل به قهوه‌ای در هوا"},
"no2": {"name": "دی‌اکسید نیتروژن", "formula": "NO2", "type": "Gas", "pH": 3.0, "molarity": 0.01, "heat": 0.0, "color": "#A52A2A", "desc": "گاز قهوه‌ای سمی، عامل آلودگی هوا"},
"n2o": {"name": "نیتروس اکسید", "formula": "N2O", "type": "Gas", "pH": 7.0, "molarity": 0.01, "heat": 0.0, "color": "#FFFFFF", "desc": "گاز خنده، بیهوش‌کننده دندانپزشکی"},
"nh4no2": {"name": "آمونیوم نیتریت", "formula": "NH4NO2", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 0.0, "color": "#FFFFFF", "desc": "تجزیه به نیتروژن و آب"},
"kclo3": {"name": "پتاسیم کلرات", "formula": "KClO3", "type": "Salt", "pH": 7.0, "molarity": 0.1, "heat": 0.0, "color": "#FFFFFF", "desc": "اکسیدکننده قوی، تولید اکسیژن"},
"na2so3": {"name": "سدیم سولفیت", "formula": "Na2SO3", "type": "Salt", "pH": 9.0, "molarity": 0.1, "heat": -12.0, "color": "#FFFFFF", "desc": "نگهدارنده و اکسایش‌پذیر"},
"ch3cho": {"name": "استالدئید", "formula": "CH3CHO", "type": "Aldehyde", "pH": 7.0, "molarity": 0.1, "heat": 0.0, "color": "#FFFFFF", "desc": "اکسایش اتانول، بوی میوه"},
"fe(oh)3": {"name": "هیدروکسید آهن(III)", "formula": "Fe(OH)3", "type": "Precipitate", "pH": 3.0, "molarity": 0.01, "heat": 0.0, "color": "#8B4513", "desc": "رسوب قهوه‌ای ژله‌ای"},
"cu(oh)2": {"name": "هیدروکسید مس(II)", "formula": "Cu(OH)2", "type": "Precipitate", "pH": 8.0, "molarity": 0.01, "heat": 0.0, "color": "#00FFFF", "desc": "رسوب آبی روشن"},
"ni(oh)2": {"name": "هیدروکسید نیکل(II)", "formula": "Ni(OH)2", "type": "Precipitate", "pH": 9.0, "molarity": 0.01, "heat": 0.0, "color": "#90EE90", "desc": "رسوب سبز روشن"},
"cr(oh)3": {"name": "هیدروکسید کروم(III)", "formula": "Cr(OH)3", "type": "Precipitate", "pH": 8.0, "molarity": 0.01, "heat": 0.0, "color": "#808080", "desc": "رسوب سبز خاکستری آمفوتر"},
"pbso4": {"name": "سولفات سرب", "formula": "PbSO4", "type": "Precipitate", "pH": 7.0, "molarity": 0.01, "heat": 0.0, "color": "#FFFFFF", "desc": "رسوب سفید سنگین"},
"agi": {"name": "یدید نقره", "formula": "AgI", "type": "Precipitate", "pH": 7.0, "molarity": 0.01, "heat": 0.0, "color": "#FFFFE0", "desc": "رسوب زرد کم‌رنگ، حساس به نور"},
"agbr": {"name": "برمید نقره", "formula": "AgBr", "type": "Precipitate", "pH": 7.0, "molarity": 0.01, "heat": 0.0, "color": "#F0E68C", "desc": "رسوب کرمی، استفاده در عکاسی"},
"pbi2": {"name": "یدید سرب", "formula": "PbI2", "type": "Precipitate", "pH": 7.0, "molarity": 0.01, "heat": 0.0, "color": "#FFD700", "desc": "رسوب زرد طلایی (باران طلایی)"},
"pbcr o4": {"name": "کرومات سرب", "formula": "PbCrO4", "type": "Precipitate", "pH": 7.0, "molarity": 0.01, "heat": 0.0, "color": "#FFFF00", "desc": "رسوب زرد کروم"},
"srso4": {"name": "سولفات استرانسیم", "formula": "SrSO4", "type": "Precipitate", "pH": 7.0, "molarity": 0.01, "heat": 0.0, "color": "#FFFFFF", "desc": "رسوب سفید"},
"znco3": {"name": "کربنات روی", "formula": "ZnCO3", "type": "Precipitate", "pH": 7.0, "molarity": 0.01, "heat": 0.0, "color": "#FFFFFF", "desc": "رسوب سفید پایه"},
"fes": {"name": "سولفید آهن(II)", "formula": "FeS", "type": "Precipitate", "pH": 7.0, "molarity": 0.01, "heat": 0.0, "color": "#000000", "desc": "رسوب سیاه"},
"zns": {"name": "سولفید روی", "formula": "ZnS", "type": "Precipitate", "pH": 7.0, "molarity": 0.01, "heat": 0.0, "color": "#FFFFFF", "desc": "رسوب سفید، فسفرسانس"},
"cds": {"name": "سولفید کادمیم", "formula": "CdS", "type": "Precipitate", "pH": 7.0, "molarity": 0.01, "heat": 0.0, "color": "#FFFF00", "desc": "رسوب زرد روشن"},
"mns": {"name": "سولفید منگنز", "formula": "MnS", "type": "Precipitate", "pH": 7.0, "molarity": 0.01, "heat": 0.0, "color": "#FFB6C1", "desc": "رسوب صورتی گوشتی"},
"cos": {"name": "سولفید کبالت", "formula": "CoS", "type": "Precipitate", "pH": 7.0, "molarity": 0.01, "heat": 0.0, "color": "#000000", "desc": "رسوب سیاه"},
"sb2s3": {"name": "سولفید آنتیموان(III)", "formula": "Sb2S3", "type": "Precipitate", "pH": 7.0, "molarity": 0.01, "heat": 0.0, "color": "#FFA500", "desc": "رسوب نارنجی"},
"sns": {"name": "سولفید قلع(II)", "formula": "SnS", "type": "Precipitate", "pH": 7.0, "molarity": 0.01, "heat": 0.0, "color": "#8B4513", "desc": "رسوب قهوه‌ای"},
"hexamethylenediamine": {"name": "هگزامتیلن دی‌آمین", "formula": "C6H16N2", "type": "Organic", "pH": 12.0, "molarity": 0.1, "heat": 0.0, "color": "#FFFFFF", "desc": "ماده اولیه تولید نایلون ۶۶"},
"adipoyl chloride": {"name": "آدیپویل کلرید", "formula": "C6H8Cl2O2", "type": "Organic", "pH": 1.0, "molarity": 0.1, "heat": 0.0, "color": "#FFFFFF", "desc": "ماده اولیه تولید نایلون در مرز دو فاز"},
"c8h8": {"name": "استایرن", "formula": "C8H8", "type": "Monomer", "pH": 7.0, "molarity": 0.1, "heat": 0.0, "color": "#FFFFFF", "desc": "ماده اولیه پلی‌استایرن و فوم"},
"c3h5n": {"name": "آکریلونیتریل", "formula": "C3H3N", "type": "Monomer", "pH": 7.0, "molarity": 0.1, "heat": 0.0, "color": "#FFFFFF", "desc": "ماده اولیه الیاف مصنوعی و پلاستیک ABS"},
"br2": {"name": "برم", "formula": "Br2", "type": "Halogen", "pH": 7.0, "molarity": 0.1, "heat": 0.0, "color": "#8B0000", "desc": "مایع قرمز قهوه‌ای سمی، اکسیدکننده قوی"},
"i2": {"name": "ید", "formula": "I2", "type": "Halogen", "pH": 7.0, "molarity": 0.1, "heat": 0.0, "color": "#4B0082", "desc": "جامد بنفش، تصعید شونده و ضدعفونی‌کننده"},
"f2": {"name": "فلوئور", "formula": "F2", "type": "Halogen", "pH": 7.0, "molarity": 0.01, "heat": 0.0, "color": "#FFFF00", "desc": "گاز زرد کم‌رنگ، واکنش‌پذیرترین عنصر"},
"o3": {"name": "ازون", "formula": "O3", "type": "Gas", "pH": 7.0, "molarity": 0.01, "heat": 0.0, "color": "#0000FF", "desc": "گاز آبی رنگ، اکسیدکننده قوی و بوی تند"},
"he": {"name": "هلیوم", "formula": "He", "type": "Gas", "pH": 7.0, "molarity": 0.01, "heat": 0.0, "color": "#FFFFFF", "desc": "گاز بی‌اثر سبک، پرکننده بالن"},
"ar": {"name": "آرگون", "formula": "Ar", "type": "Gas", "pH": 7.0, "molarity": 0.01, "heat": 0.0, "color": "#FFFFFF", "desc": "گاز بی‌اثر، استفاده در لامپ و جوشکاری"},
"kr": {"name": "کریپتون", "formula": "Kr", "type": "Gas", "pH": 7.0, "molarity": 0.01, "heat": 0.0, "color": "#FFFFFF", "desc": "گاز نجیب، نور سفید در لامپ‌های فلورسنت"},
"xe": {"name": "گزنون", "formula": "Xe", "type": "Gas", "pH": 7.0, "molarity": 0.01, "heat": 0.0, "color": "#FFFFFF", "desc": "گاز نجیب سنگین، نور آبی در چراغ خودرو"},
"ne": {"name": "نئون", "formula": "Ne", "type": "Gas", "pH": 7.0, "molarity": 0.01, "heat": 0.0, "color": "#FFFFFF", "desc": "گاز نجیب، نور قرمز در تابلوهای تبلیغاتی"},
"cu": {"name": "مس", "formula": "Cu", "type": "Metal", "pH": 7.0, "molarity": 1.0, "heat": 0.0, "color": "#B87333", "desc": "فلز قرمز رنگ، رسانای عالی برق"},
"ag": {"name": "نقره", "formula": "Ag", "type": "Metal", "pH": 7.0, "molarity": 1.0, "heat": 0.0, "color": "#C0C0C0", "desc": "فلز سفید براق، بهترین رسانای برق"},
"au": {"name": "طلا", "formula": "Au", "type": "Metal", "pH": 7.0, "molarity": 1.0, "heat": 0.0, "color": "#FFD700", "desc": "فلز زرد مقاوم به خوردگی"},
"pt": {"name": "پلاتین", "formula": "Pt", "type": "Metal", "pH": 7.0, "molarity": 1.0, "heat": 0.0, "color": "#E5E4E2", "desc": "فلز گران‌بها، کاتالیزور اگزوز خودرو"},
"pb": {"name": "سرب", "formula": "Pb", "type": "Metal", "pH": 7.0, "molarity": 1.0, "heat": 0.0, "color": "#808080", "desc": "فلز سنگین نرم، سپر پرتو ایکس"},
"sn": {"name": "قلع", "formula": "Sn", "type": "Metal", "pH": 7.0, "molarity": 1.0, "heat": 0.0, "color": "#C0C0C0", "desc": "فلز سفید نرم، پوشش قوطی کنسرو"},
"ni": {"name": "نیکل", "formula": "Ni", "type": "Metal", "pH": 7.0, "molarity": 1.0, "heat": 0.0, "color": "#A0A0A0", "desc": "فلز مقاوم به خوردگی، سکه و آبکاری"},
"co": {"name": "کبالت", "formula": "Co", "type": "Metal", "pH": 7.0, "molarity": 1.0, "heat": 0.0, "color": "#808080", "desc": "فلز مغناطیسی، رنگ آبی در شیشه"},
"cr": {"name": "کروم", "formula": "Cr", "type": "Metal", "pH": 7.0, "molarity": 1.0, "heat": 0.0, "color": "#C0C0C0", "desc": "فلز براق، آبکاری ضد زنگ"},
"mn": {"name": "منگنز", "formula": "Mn", "type": "Metal", "pH": 7.0, "molarity": 1.0, "heat": 0.0, "color": "#808080", "desc": "فلز سخت، آلیاژ فولاد"},
"ti": {"name": "تیتانیوم", "formula": "Ti", "type": "Metal", "pH": 7.0, "molarity": 1.0, "heat": 0.0, "color": "#C0C0C0", "desc": "فلز سبک و قوی، ایمپلنت پزشکی"},
"v": {"name": "وانادیوم", "formula": "V", "type": "Metal", "pH": 7.0, "molarity": 1.0, "heat": 0.0, "color": "#C0C0C0", "desc": "آلیاژ فولاد قوی"},
"ba": {"name": "باریم", "formula": "Ba", "type": "Metal", "pH": 7.0, "molarity": 1.0, "heat": 0.0, "color": "#FFFFFF", "desc": "فلز قلیایی خاکی، رنگ سبز در آتش‌بازی"},
"sr": {"name": "استرانسیم", "formula": "Sr", "type": "Metal", "pH": 7.0, "molarity": 1.0, "heat": 0.0, "color": "#FFFFFF", "desc": "فلز قلیایی خاکی، رنگ قرمز در آتش‌بازی"},
"k": {"name": "پتاسیم", "formula": "K", "type": "Metal", "pH": 7.0, "molarity": 1.0, "heat": 0.0, "color": "#C0C0C0", "desc": "فلز قلیایی نرم، واکنش شدید با آب"},
"li": {"name": "لیتیوم", "formula": "Li", "type": "Metal", "pH": 7.0, "molarity": 1.0, "heat": 0.0, "color": "#C0C0C0", "desc": "سبک‌ترین فلز، باتری لیتیومی"},
"cs": {"name": "سزیم", "formula": "Cs", "type": "Metal", "pH": 7.0, "molarity": 1.0, "heat": 0.0, "color": "#FFD700", "desc": "واکنش‌پذیرترین فلز قلیایی"},
"rb": {"name": "روبیدیم", "formula": "Rb", "type": "Metal", "pH": 7.0, "molarity": 1.0, "heat": 0.0, "color": "#C0C0C0", "desc": "فلز قلیایی نرم و واکنش‌پذیر"},
"be": {"name": "بریلیوم", "formula": "Be", "type": "Metal", "pH": 7.0, "molarity": 1.0, "heat": 0.0, "color": "#C0C0C0", "desc": "فلز سبک و سمی، آلیاژ سخت"},
"sc": {"name": "اسکاندیم", "formula": "Sc", "type": "Metal", "pH": 7.0, "molarity": 1.0, "heat": 0.0, "color": "#C0C0C0", "desc": "عنصر کمیاب، آلیاژ آلومینیوم"},
"y": {"name": "یتریم", "formula": "Y", "type": "Metal", "pH": 7.0, "molarity": 1.0, "heat": 0.0, "color": "#C0C0C0", "desc": "عنصر خاکی کمیاب، سرامیک دما بالا"},
"zr": {"name": "زیرکونیم", "formula": "Zr", "type": "Metal", "pH": 7.0, "molarity": 1.0, "heat": 0.0, "color": "#C0C0C0", "desc": "مقاوم به خوردگی، روکش راکتور هسته‌ای"},
"hf": {"name": "هافنیم", "formula": "Hf", "type": "Metal", "pH": 7.0, "molarity": 1.0, "heat": 0.0, "color": "#C0C0C0", "desc": "جذب نوترون بالا، میله کنترل راکتور"},
"nb": {"name": "نیوبیوم", "formula": "Nb", "type": "Metal", "pH": 7.0, "molarity": 1.0, "heat": 0.0, "color": "#C0C0C0", "desc": "ابررسانا، آلیاژ جت"},
"ta": {"name": "تانتالم", "formula": "Ta", "type": "Metal", "pH": 7.0, "molarity": 1.0, "heat": 0.0, "color": "#C0C0C0", "desc": "خازن‌های کوچک الکترونیک"},
"mo": {"name": "مولیبدن", "formula": "Mo", "type": "Metal", "pH": 7.0, "molarity": 1.0, "heat": 0.0, "color": "#C0C0C0", "desc": "آلیاژ فولاد سخت"},
"w": {"name": "تنگستن", "formula": "W", "type": "Metal", "pH": 7.0, "molarity": 1.0, "heat": 0.0, "color": "#C0C0C0", "desc": "نقطه ذوب بالا، لامپ رشته‌ای"},
"fe2o3": {"name": "اکسید آهن(III)", "formula": "Fe2O3", "type": "Oxide", "pH": 7.0, "molarity": 0.1, "heat": 0.0, "color": "#8B4513", "desc": "زنگ آهن، رنگدانه قرمز"},
"cuo": {"name": "اکسید مس(II)", "formula": "CuO", "type": "Oxide", "pH": 7.0, "molarity": 0.1, "heat": 0.0, "color": "#000000", "desc": "پودر سیاه، کاتالیزور"},
"zno": {"name": "اکسید روی", "formula": "ZnO", "type": "Oxide", "pH": 7.0, "molarity": 0.1, "heat": 0.0, "color": "#FFFFFF", "desc": "کرم ضد آفتاب و رنگ سفید"},
"al2o3": {"name": "اکسید آلومینیوم", "formula": "Al2O3", "type": "Oxide", "pH": 7.0, "molarity": 0.1, "heat": 0.0, "color": "#FFFFFF", "desc": "کوراندوم، ساینده سخت"},
"tio2": {"name": "دی‌اکسید تیتانیوم", "formula": "TiO2", "type": "Oxide", "pH": 7.0, "molarity": 0.1, "heat": 0.0, "color": "#FFFFFF", "desc": "رنگ سفید مات و فتوکاتالیست"},
"sio2": {"name": "دی‌اکسید سیلیسیم", "formula": "SiO2", "type": "Oxide", "pH": 7.0, "molarity": 0.1, "heat": 0.0, "color": "#FFFFFF", "desc": "شن و ماسه، شیشه"},
"p4o10": {"name": "پنتااکسید فسفر", "formula": "P4O10", "type": "Oxide", "pH": 1.0, "molarity": 0.1, "heat": -100.0, "color": "#FFFFFF", "desc": "جذب‌کننده رطوبت قوی"},
"na2o": {"name": "اکسید سدیم", "formula": "Na2O", "type": "Oxide", "pH": 13.0, "molarity": 0.1, "heat": -50.0, "color": "#FFFFFF", "desc": "باز قوی، واکنش گرمازا با آب"},
"cao": {"name": "اکسید کلسیم", "formula": "CaO", "type": "Oxide", "pH": 12.0, "molarity": 0.1, "heat": -60.0, "color": "#FFFFFF", "desc": "آهک زنده، خشک‌کننده"},
"k2o": {"name": "اکسید پتاسیم", "formula": "K2O", "type": "Oxide", "pH": 13.0, "molarity": 0.1, "heat": -70.0, "color": "#FFFFFF", "desc": "باز بسیار قوی"},
"cr2o3": {"name": "اکسید کروم(III)", "formula": "Cr2O3", "type": "Oxide", "pH": 7.0, "molarity": 0.1, "heat": 0.0, "color": "#008000", "desc": "رنگ سبز، مقاوم به حرارت"},
"fe3o4": {"name": "مگنتیت", "formula": "Fe3O4", "type": "Oxide", "pH": 7.0, "molarity": 0.1, "heat": 0.0, "color": "#000000", "desc": "اکسید مغناطیسی طبیعی"},
"mn o2": {"name": "دی‌اکسید منگنز", "formula": "MnO2", "type": "Oxide", "pH": 7.0, "molarity": 0.1, "heat": 0.0, "color": "#2F4F4F", "desc": "کاتالیزور تجزیه پراکسید"},
"v2o5": {"name": "پنتااکسید وانادیوم", "formula": "V2O5", "type": "Oxide", "pH": 2.0, "molarity": 0.1, "heat": 0.0, "color": "#FFA500", "desc": "کاتالیزور تولید اسید سولفوریک"},
"pb o2": {"name": "دی‌اکسید سرب", "formula": "PbO2", "type": "Oxide", "pH": 7.0, "molarity": 0.1, "heat": 0.0, "color": "#8B4513", "desc": "اکسیدکننده قوی در باتری"},
"ag2o": {"name": "اکسید نقره", "formula": "Ag2O", "type": "Oxide", "pH": 10.0, "molarity": 0.1, "heat": 0.0, "color": "#8B4513", "desc": "ضدعفونی‌کننده و اکسیدکننده"},
"hg o": {"name": "اکسید جیوه(II)", "formula": "HgO", "type": "Oxide", "pH": 7.0, "molarity": 0.1, "heat": 0.0, "color": "#FF0000", "desc": "پودر قرمز یا زرد، تجزیه به جیوه و اکسیژن"},
"sb2o3": {"name": "تری‌اکسید آنتیموان", "formula": "Sb2O3", "type": "Oxide", "pH": 7.0, "molarity": 0.1, "heat": 0.0, "color": "#FFFFFF", "desc": "بازدارنده شعله در پلاستیک"},
"bi2o3": {"name": "تری‌اکسید بیسموت", "formula": "Bi2O3", "type": "Oxide", "pH": 7.0, "molarity": 0.1, "heat": 0.0, "color": "#FFFF00", "desc": "رنگ زرد در سرامیک"},
"as2o3": {"name": "تری‌اکسید آرسنیک", "formula": "As2O3", "type": "Oxide", "pH": 7.0, "molarity": 0.1, "heat": 0.0, "color": "#FFFFFF", "desc": "سم قوی تاریخی (آرسنیک سفید)"},
"se o2": {"name": "دی‌اکسید سلنیم", "formula": "SeO2", "type": "Oxide", "pH": 2.0, "molarity": 0.1, "heat": 0.0, "color": "#FFFFFF", "desc": "اکسیدکننده در سنتز آلی"},
"te o2": {"name": "دی‌اکسید تلوریم", "formula": "TeO2", "type": "Oxide", "pH": 7.0, "molarity": 0.1, "heat": 0.0, "color": "#FFFFFF", "desc": "ماده اولیه شیشه‌های خاص"},
"na clo": {"name": "هیپوکلریت سدیم", "formula": "NaClO", "type": "Oxidizer", "pH": 11.0, "molarity": 0.1, "heat": 0.0, "color": "#F0FFFF", "desc": "وایتکس، سفیدکننده و ضدعفونی‌کننده"},
"k clo4": {"name": "پرکلرات پتاسیم", "formula": "KClO4", "type": "Oxidizer", "pH": 7.0, "molarity": 0.1, "heat": 0.0, "color": "#FFFFFF", "desc": "اکسیدکننده قوی در مواد آتش‌زا"},
"nh4 clo4": {"name": "آمونیوم پرکلرات", "formula": "NH4ClO4", "type": "Oxidizer", "pH": 7.0, "molarity": 0.1, "heat": 0.0, "color": "#FFFFFF", "desc": "سوخت جامد موشک فضایی"},
"ba clo4": {"name": "پرکلرات باریم", "formula": "Ba(ClO4)2", "type": "Oxidizer", "pH": 7.0, "molarity": 0.1, "heat": 0.0, "color": "#FFFFFF", "desc": "رنگ سبز در آتش‌بازی"},
"na2 o2": {"name": "پراکسید سدیم", "formula": "Na2O2", "type": "Oxidizer", "pH": 12.0, "molarity": 0.1, "heat": -50.0, "color": "#FFFFE0", "desc": "تولید اکسیژن و سفیدکننده"},
"ba o2": {"name": "پراکسید باریم", "formula": "BaO2", "type": "Oxidizer", "pH": 12.0, "molarity": 0.1, "heat": 0.0, "color": "#FFFFFF", "desc": "روش قدیمی تولید پراکسید هیدروژن"},
"li2 o2": {"name": "پراکسید لیتیوم", "formula": "Li2O2", "type": "Oxidizer", "pH": 12.0, "molarity": 0.1, "heat": 0.0, "color": "#FFFFFF", "desc": "جاذب CO2 در فضاپیما"},
"cs2": {"name": "دی‌سولفید کربن", "formula": "CS2", "type": "Solvent", "pH": 7.0, "molarity": 0.1, "heat": 0.0, "color": "#FFFFFF", "desc": "حلال ویسکوز و لاستیک"},
"ch2cl2": {"name": "دی‌کلرومتان", "formula": "CH2Cl2", "type": "Solvent", "pH": 7.0, "molarity": 0.1, "heat": 0.0, "color": "#FFFFFF", "desc": "حلال رنگ‌بر و کافئین‌زدایی"},
"c6h5ch3": {"name": "تولوئن", "formula": "C6H5CH3", "type": "Solvent", "pH": 7.0, "molarity": 0.1, "heat": 0.0, "color": "#FFFFFF", "desc": "حلال رنگ و ماده اولیه TNT"},
"c6h5cl": {"name": "کلروبنزن", "formula": "C6H5Cl", "type": "Solvent", "pH": 7.0, "molarity": 0.1, "heat": 0.0, "color": "#FFFFFF", "desc": "حلال و ماده اولیه فنل"},
"dmso": {"name": "دی‌متیل سولفوکسید", "formula": "(CH3)2SO", "type": "Solvent", "pH": 7.0, "molarity": 0.1, "heat": 0.0, "color": "#FFFFFF", "desc": "حلال قطبی آپروتیک، نفوذ در پوست"},
"thf": {"name": "تتراهیدروفوران", "formula": "C4H8O", "type": "Solvent", "pH": 7.0, "molarity": 0.1, "heat": 0.0, "color": "#FFFFFF", "desc": "حلال واکنش‌های گرینیارد"},
"ch3cn": {"name": "استونیتریل", "formula": "CH3CN", "type": "Solvent", "pH": 7.0, "molarity": 0.1, "heat": 0.0, "color": "#FFFFFF", "desc": "حلال قطبی در HPLC"},
"hf": {"name": "هیدروفلوئوریک اسید", "formula": "HF", "type": "Weak Acid", "pH": 3.2, "molarity": 0.1, "heat": -50.0, "color": "#FFFFFF", "desc": "خوردگی شیشه، بسیار خطرناک"},
"hi": {"name": "هیدرویدیک اسید", "formula": "HI", "type": "Strong Acid", "pH": 1.0, "molarity": 0.1, "heat": -80.0, "color": "#FFFFFF", "desc": "کاهنده قوی، تولید ید"},
"hcn": {"name": "هیدروسیانیک اسید", "formula": "HCN", "type": "Weak Acid", "pH": 9.2, "molarity": 0.1, "heat": 0.0, "color": "#FFFFFF", "desc": "گاز سمی با بوی بادام (سیانید)"},
"h2co3": {"name": "کربنیک اسید", "formula": "H2CO3", "type": "Weak Acid", "pH": 6.3, "molarity": 0.1, "heat": 0.0, "color": "#FFFFFF", "desc": "در نوشابه‌های گازدار"},
"h2so3": {"name": "سولفوروس اسید", "formula": "H2SO3", "type": "Weak Acid", "pH": 1.9, "molarity": 0.1, "heat": 0.0, "color": "#FFFFFF", "desc": "نگهدارنده در شراب"},
"hno2": {"name": "نیتریک اسید", "formula": "HNO2", "type": "Weak Acid", "pH": 3.3, "molarity": 0.1, "heat": 0.0, "color": "#FFFFFF", "desc": "عامل دیازوتاسیون"},
"h3po3": {"name": "فسفروس اسید", "formula": "H3PO3", "type": "Weak Acid", "pH": 1.8, "molarity": 0.1, "heat": 0.0, "color": "#FFFFFF", "desc": "کاهنده در آبکاری"},
"hclo": {"name": "هیپوکلروس اسید", "formula": "HClO", "type": "Weak Acid", "pH": 7.5, "molarity": 0.1, "heat": 0.0, "color": "#FFFFFF", "desc": "عامل ضدعفونی در استخر"},
"hbro": {"name": "هیپوبرومیک اسید", "formula": "HBrO", "type": "Weak Acid", "pH": 8.7, "molarity": 0.1, "heat": 0.0, "color": "#FFFFFF", "desc": "اکسیدکننده ضعیف"},
"hio": {"name": "هیپوئیدیک اسید", "formula": "HIO", "type": "Weak Acid", "pH": 10.0, "molarity": 0.1, "heat": 0.0, "color": "#FFFFFF", "desc": "ضعیف‌ترین هیپوهالواسید"},
"nh4oh": {"name": "آمونیوم هیدروکسید", "formula": "NH4OH", "type": "Weak Base", "pH": 11.6, "molarity": 0.1, "heat": -35.0, "color": "#F0F8FF", "desc": "محلول آمونیاک، پاک‌کننده"},
}


# ترجمه انواع مواد به فارسی برای نمایش در دانشنامه
TYPE_MAP = {
    "Strong Acid": "مایع (اسید قوی)",
    "Weak Acid": "مایع (اسید ضعیف)",
    "Strong Base": "مایع (باز قوی)",
    "Weak Base": "مایع (باز ضعیف)",
    "Acid": "مایع (اسید)",
    "Base": "مایع (باز)",
    "Salt": "جامد (نمک)",
    "Gas": "گاز",
    "Liquid": "مایع",
    "Solid": "جامد",
    "Metal": "جامد (فلز)",
    "Oxide": "جامد (اکسید)",
    "Solvent": "مایع (حلال)",
    "Element": "جامد (عنصر)",
    "Alcohol": "مایع (الکل)",
    "Precipitate": "جامد (رسوب)",
    "Halogen": "گاز/مایع",
    "Organic Compound": "آلی",
    "Complex": "محلول کمپلکس"
}


def get_persian_type(eng_type):
    return TYPE_MAP.get(eng_type, eng_type)  # اگر پیدا نشد همان انگلیسی را برگردان


class ChemicalCalculator:
    SUBSCRIPTS = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")

    @staticmethod
    def to_subscript(text):
        if not text: return ""
        return text.translate(ChemicalCalculator.SUBSCRIPTS)

    @staticmethod
    def parse_formula(formula):
        if formula == "Mix" or formula == "-" or formula is None: return {}
        elements = re.findall(r'([A-Z][a-z]*)(\d*)', formula)
        composition = Counter()
        for el, count in elements:
            count = int(count) if count else 1
            composition[el] += count
        return composition

    @staticmethod
    def format_gross_formula(atom_counts, simplify=True, empirical=False):
        if not atom_counts: return "ماده‌ای وجود ندارد"
        atom_counts = atom_counts.copy()
        sorted_elements = []
        keys = list(atom_counts.keys())
        if 'C' in keys: sorted_elements.append('C'); keys.remove('C')
        if 'H' in keys: sorted_elements.append('H'); keys.remove('H')
        sorted_elements.extend(sorted(keys))

        if empirical:
            vals = [atom_counts[el] for el in sorted_elements if atom_counts[el] > 0]
            if not vals: return ""
            min_val = min(vals)
            for el in sorted_elements:
                if atom_counts[el] > 0: atom_counts[el] /= min_val
            for el in sorted_elements: atom_counts[el] = round(atom_counts[el])

        formula_str = ""
        for el in sorted_elements:
            count = atom_counts[el]
            if count > 0:
                formula_str += f"{el}{int(count) if count > 1 else ''}"
        return ChemicalCalculator.to_subscript(formula_str)


# ----------------- بشر واقعی‌تر (PyQt5) -----------------
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
        # محدود کردن ارتفاع برای جلوگیری از سرریز گرافیکی
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

        # حاشیه‌های امن برای رسم
        margin_x = 30
        margin_y = 20
        beaker_w = w - 2 * margin_x
        beaker_h = h - 2 * margin_y
        ellipse_h = 20  # ارتفاع بیضی برای حالت سه بعدی

        beaker_rect = QRectF(margin_x, margin_y, beaker_w, beaker_h)

        # 1. رسم مایع
        if self._fluid_height > 0:
            fluid_h_px = (self._fluid_height / 100.0) * (beaker_h - ellipse_h)
            fluid_top_y = beaker_rect.bottom() - ellipse_h / 2 - fluid_h_px

            path_fluid = QPainterPath()
            # بیضی پایین مایع
            path_fluid.addEllipse(margin_x + 2, beaker_rect.bottom() - ellipse_h - 2, beaker_w - 4, ellipse_h)
            # مستطیل بدنه مایع
            path_fluid.addRect(margin_x + 2, fluid_top_y + ellipse_h / 2, beaker_w - 4, fluid_h_px - ellipse_h / 2)

            painter.setPen(Qt.NoPen)
            fluid_grad = QLinearGradient(margin_x, 0, w - margin_x, 0)
            c = self._fluid_color
            fluid_grad.setColorAt(0, c.darker(120))
            fluid_grad.setColorAt(0.3, c.lighter(110))
            fluid_grad.setColorAt(0.8, c)
            fluid_grad.setColorAt(1, c.darker(120))
            painter.setBrush(fluid_grad)
            painter.drawPath(path_fluid)

            # سطح مایع (بیضی بالا)
            painter.setBrush(c.lighter(115))
            painter.drawEllipse(QRectF(margin_x + 2, fluid_top_y, beaker_w - 4, ellipse_h))

        # 2. رسم شیشه بشر
        glass_pen = QPen(QColor(220, 230, 255, 150), 2)
        painter.setPen(glass_pen)
        painter.setBrush(QColor(255, 255, 255, 20))  # شفافیت شیشه

        # بدنه بشر
        path_glass = QPainterPath()
        path_glass.moveTo(margin_x, margin_y + ellipse_h / 2)
        path_glass.lineTo(margin_x, beaker_rect.bottom() - ellipse_h / 2)
        # خمیدگی پایین (بیضی کامل پایین)
        path_glass.arcTo(margin_x, beaker_rect.bottom() - ellipse_h, beaker_w, ellipse_h, 180, -180)
        path_glass.lineTo(beaker_rect.right(), margin_y + ellipse_h / 2)
        # بیضی دهانه بالا
        path_glass.addEllipse(QRectF(margin_x, margin_y, beaker_w, ellipse_h))

        painter.drawPath(path_glass)

        # 3. درجه‌بندی (Graduation marks)
        painter.setPen(QPen(QColor(255, 255, 255, 180), 1))
        for i in range(1, 10):
            y_pos = beaker_rect.bottom() - ellipse_h / 2 - (i * 0.1 * (beaker_h - ellipse_h))
            width_mark = 10 if i % 5 != 0 else 20
            painter.drawLine(int(margin_x + 10), int(y_pos), int(margin_x + 10 + width_mark), int(y_pos))
            if i % 2 == 0:
                painter.drawText(int(margin_x + 35), int(y_pos + 5), f"{i * 100}")

        # 4. فلش (انیمیشن واکنش)
        if self._flash_opacity > 0.01:
            fc = QColor(255, 255, 255, int(self._flash_opacity * 200))
            painter.setBrush(fc)
            painter.setPen(Qt.NoPen)
            painter.drawRect(self.rect())


# ----------------- موتور آزمایشگاه -----------------
class LabEngine:
    def __init__(self):
        self.score = 0
        self.level = 1
        self.discovered = set()
        self.load_data()
        self.reset()
        self.builder_parts = []

    def reset(self):
        self.total_volume = 0.0
        self.moles_h = 0.0
        self.moles_oh = 0.0
        self.temp_c = 25.0
        self.contents = {}
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
        if key not in CHEMICAL_DB: return "خطا در یافتن ماده"

        data = CHEMICAL_DB[key]
        added_moles = data["molarity"] * (vol / 1000.0)
        self.total_volume += vol

        self.contents[key] = self.contents.get(key, 0) + added_moles
        self.composition_log[key] = self.composition_log.get(key, 0) + vol

        if self.total_volume > 0:
            heat_effect = data["heat"] * (vol / self.total_volume)
            self.temp_c += heat_effect

        # محاسبه مول‌های H+ و OH-
        if data["pH"] < 7:
            # اسید
            self.moles_h += added_moles * (1 if data["pH"] < 2 else 0.1)
        elif data["pH"] > 7:
            # باز
            self.moles_oh += added_moles * (1 if data["pH"] > 12 else 0.1)
        # نکته: برای pH 7 تغییری در excess moles نمی‌دهیم

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
                        return (name, 0, "old")
        return None

    def get_ph(self):
        if self.total_volume == 0: return 7.0
        vol_l = self.total_volume / 1000.0
        h = self.moles_h / vol_l if vol_l else 0
        oh = self.moles_oh / vol_l if vol_l else 0

        # رفع مشکل pH 0 برای مواد خنثی
        # اگر تفاوت غلظت H+ و OH- بسیار ناچیز باشد، محلول خنثی است
        if abs(h - oh) < 1e-9:
            return 7.0

        if h > oh:
            net_h = h - oh
            val = -math.log10(net_h + 1e-14)
            return max(0, min(14, val))
        else:
            net_oh = oh - h
            poh = -math.log10(net_oh + 1e-14)
            val = 14.0 - poh
            return max(0, min(14, val))

    def calculate_mixed_color(self):
        if self.total_volume == 0: return "#E0FFFF"
        r_total, g_total, b_total = 0, 0, 0
        total_weight = 0
        base_color = QColor("#E0FFFF")
        base_weight = 0.1 * self.total_volume
        r_total += base_color.red() * base_weight
        g_total += base_color.green() * base_weight
        b_total += base_color.blue() * base_weight
        total_weight += base_weight
        vol_l = self.total_volume / 1000.0
        for k, moles in self.contents.items():
            if moles > 1e-5:
                conc = moles / vol_l
                data = CHEMICAL_DB.get(k)
                if data:
                    c = QColor(data["color"])
                    weight = conc * 100
                    r_total += c.red() * weight
                    g_total += c.green() * weight
                    b_total += c.blue() * weight
                    total_weight += weight
        if total_weight == 0: return "#E0FFFF"
        return QColor(
            int(min(255, r_total / total_weight)),
            int(min(255, g_total / total_weight)),
            int(min(255, b_total / total_weight))
        ).name()

    def update_color(self):
        self.dominant_color = self.calculate_mixed_color()

    def calculate_mixture_stats(self):
        total_atoms = Counter()
        for k, v in self.composition_log.items():
            form = CHEMICAL_DB[k]["formula"]
            atoms = ChemicalCalculator.parse_formula(form)
            for a, c in atoms.items(): total_atoms[a] += c * v
        return ChemicalCalculator.format_gross_formula(total_atoms, simplify=True, empirical=True), total_atoms


# ----------------- رابط کاربری (PyQt5) -----------------
class ModernLabWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("آزمایشگاه شیمی پیشرفته")
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

        # پنل کنترل
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
        self.progress_xp.setTextVisible(False)
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
        btn_heat = QPushButton("🔥 گرما (+)")
        btn_heat.setStyleSheet("background-color: #f38ba8; color: #1e1e2e;")
        btn_heat.clicked.connect(lambda: self.engine.change_temperature(10))
        btn_cool = QPushButton("🧊 سرما (-)")
        btn_cool.setStyleSheet("background-color: #89b4fa; color: #1e1e2e;")
        btn_cool.clicked.connect(lambda: self.engine.change_temperature(-10))
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

        # دکمه‌های کنترلی
        btn_wash = QPushButton("شست و شوی بشر")
        btn_wash.setStyleSheet("background-color: #89dceb; color: #1e1e2e; font-weight: bold; margin-top: 5px;")
        btn_wash.clicked.connect(self.action_wash)
        vbox.addWidget(btn_wash)

        btn_reset = QPushButton("خالی کردن محتویات")
        btn_reset.setStyleSheet("background-color: #fab387; color: #1e1e2e;")
        btn_reset.clicked.connect(self.action_reset)
        vbox.addWidget(btn_reset)

        btn_hard_reset = QPushButton("شروع مجدد بازی (New Game)")
        btn_hard_reset.setStyleSheet("background-color: #ff5555; color: white; font-weight: bold; margin-top: 10px;")
        btn_hard_reset.clicked.connect(self.action_hard_reset)
        vbox.addWidget(btn_hard_reset)

        # پنل وسط
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

        # پنل تب‌ها
        tabs = QTabWidget()
        tabs.addTab(self.create_discoveries_tab(), "🏆 کشف‌ها")
        tabs.addTab(self.create_wiki_tab(), "📖 دانشنامه واکنش‌ها")
        tabs.addTab(self.create_builder_tab(), "🧩 سازنده مولکول")
        tabs.addTab(self.create_graph_tab(), "📈 نمودارها")
        tabs.addTab(self.create_contents_tab(), "🧪 محتویات")
        tabs.addTab(self.create_datasheet_tab(), "📚 لیست مواد")

        split = QSplitter(Qt.Horizontal)
        split.addWidget(panel_ctrl)
        split.addWidget(panel_vis)
        split.addWidget(tabs)
        split.setSizes([350, 400, 600])
        layout.addWidget(split)

    # ----------------- توابع کمکی دانشنامه -----------------
    def get_state_color_text(self, formula):
        """بازگرداندن اطلاعات فرمت شده برای نمایش در جدول (نوع + رنگ)"""
        norm_key = normalize_key(formula)
        data = CHEMICAL_DB.get(norm_key)

        # اگر ماده در دیتابیس نبود
        if not data:
            return formula

        name = data.get('name', formula)
        chem_type = data.get('type', '')
        color_hex = data.get('color', '#FFFFFF')

        persian_type = get_persian_type(chem_type)

        # ساخت HTML برای نمایش رنگ و متن
        # از کاراکتر مربع پر (■) برای نمایش رنگ استفاده می‌کنیم
        html_text = f"{name} <span style='color:{color_hex}; font-size:16px;'>■</span> <small>({persian_type})</small>"
        return html_text

    def create_wiki_tab(self):
        """ساخت تب دانشنامه با جزئیات کامل (رنگ و حالت)"""
        w = QWidget()
        layout = QVBoxLayout(w)

        self.table_wiki = QTableWidget()
        self.table_wiki.setColumnCount(6)
        self.table_wiki.setHorizontalHeaderLabels(
            ["نام واکنش", "مواد اولیه (رنگ/حالت)", "محصولات (رنگ/حالت)", "دما (C)", "XP", "توضیحات"])
        self.table_wiki.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table_wiki.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)

        layout.addWidget(self.table_wiki)
        self.update_wiki_table()
        return w

    def update_wiki_table(self):
        """به‌روزرسانی جدول دانشنامه با جزئیات جدید"""
        discovered_items = {k: v for k, v in CUSTOM_REACTIONS.items() if k in self.engine.discovered}

        self.table_wiki.setRowCount(len(discovered_items))

        for i, (name, data) in enumerate(discovered_items.items()):
            # 1. نام واکنش
            self.table_wiki.setItem(i, 0, QTableWidgetItem(name))

            # 2. مواد اولیه با جزئیات
            reactants_str = ""
            for r in data.get("reactants", []):
                # نرمال‌سازی برای پیدا کردن در دیتابیس
                # فرض بر این است که نام‌های در لیست reactants کلید دیتابیس یا فرمول هستند
                # ما از تابع کمکی استفاده می‌کنیم که HTML برمی‌گرداند
                # اما QTableWidgetItem مستقیماً HTML نمی‌گیرد، باید از QLabel استفاده کرد
                pass

                # روش جایگزین: استفاده از ویجت QLabel داخل سلول برای رندر HTML

            # ساخت متن مواد اولیه
            r_labels = []
            for r in data.get("reactants", []):
                r_labels.append(self.get_state_color_text(r))
            r_final_html = " + ".join(r_labels)

            lbl_r = QLabel(r_final_html)
            lbl_r.setWordWrap(True)
            self.table_wiki.setCellWidget(i, 1, lbl_r)

            # 3. محصولات با جزئیات
            p_labels = []
            for p in data.get("products", []):
                p_labels.append(self.get_state_color_text(p))
            p_final_html = " + ".join(p_labels)

            lbl_p = QLabel(p_final_html)
            lbl_p.setWordWrap(True)
            self.table_wiki.setCellWidget(i, 2, lbl_p)

            # 4. دما
            temp_min = data.get("temp_min", "N/A")
            self.table_wiki.setItem(i, 3, QTableWidgetItem(str(temp_min)))

            # 5. امتیاز
            xp = data.get("xp", 0)
            self.table_wiki.setItem(i, 4, QTableWidgetItem(str(xp)))

            # 6. توضیحات
            desc = data.get("desc", "")
            self.table_wiki.setItem(i, 5, QTableWidgetItem(desc))

        self.table_wiki.resizeRowsToContents()

    def create_discoveries_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        self.table_disc = QTableWidget()
        self.table_disc.setColumnCount(3)
        self.table_disc.setHorizontalHeaderLabels(["واکنش", "مواد لازم", "XP"])
        self.table_disc.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        l.addWidget(self.table_disc)
        self.update_discoveries_table()
        return w

    def create_builder_tab(self):
        w = QWidget()
        l = QHBoxLayout(w)
        p_in = QFrame();
        p_in.setFixedWidth(250)
        vl = QVBoxLayout(p_in)
        self.combo_b = QComboBox()
        for s, n in sorted(PERIODIC_TABLE.items()): self.combo_b.addItem(f"{s} - {n}", s)
        self.spin_b = QSpinBox();
        self.spin_b.setRange(1, 100)
        btn_add_b = QPushButton("افزودن جزء")
        btn_add_b.clicked.connect(self.action_builder_add)
        self.list_b = QListWidget()
        btn_calc_b = QPushButton("محاسبه ترکیب")
        btn_calc_b.clicked.connect(self.action_builder_calc)
        btn_clr_b = QPushButton("پاک کردن")
        btn_clr_b.clicked.connect(
            lambda: [self.engine.builder_parts.clear(), self.list_b.clear(), self.lbl_b_res.setText("?")])
        vl.addWidget(QLabel("عنصر:"));
        vl.addWidget(self.combo_b)
        vl.addWidget(QLabel("تعداد:"));
        vl.addWidget(self.spin_b)
        vl.addWidget(btn_add_b);
        vl.addWidget(self.list_b)
        vl.addWidget(btn_calc_b);
        vl.addWidget(btn_clr_b);
        vl.addStretch()
        p_res = QFrame()
        vlr = QVBoxLayout(p_res)
        self.lbl_b_res = QLabel("?")
        self.lbl_b_res.setStyleSheet("font-size: 32px; color: #fab387; border: 2px dashed #45475a; padding: 20px;")
        self.lbl_b_desc = QLabel("اجزا را اضافه کنید...")
        self.lbl_b_desc.setWordWrap(True)
        vlr.addStretch();
        vlr.addWidget(self.lbl_b_res, 0, Qt.AlignCenter)
        vlr.addWidget(self.lbl_b_desc);
        vlr.addStretch()
        l.addWidget(p_in);
        l.addWidget(p_res)
        return w

    def create_graph_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        self.figure = Figure(figsize=(5, 6), facecolor='#1e1e2e')
        self.canvas = FigureCanvas(self.figure)
        self.ax_ph = self.figure.add_subplot(211)
        self.ax_ph.set_facecolor('#1e1e2e')
        self.ax_ph.set_ylabel('pH', color='#cdd6f4')
        self.ax_ph.tick_params(colors='#cdd6f4')
        self.ax_ph.grid(True, color='#45475a', alpha=0.5)
        self.ax_temp = self.figure.add_subplot(212)
        self.ax_temp.set_facecolor('#1e1e2e')
        self.ax_temp.set_ylabel('Temp', color='#cdd6f4')
        self.ax_temp.tick_params(colors='#cdd6f4')
        self.ax_temp.grid(True, color='#45475a', alpha=0.5)
        self.line_ph, = self.ax_ph.plot([], [], color='#fab387', lw=2)
        self.line_temp, = self.ax_temp.plot([], [], color='#f38ba8', lw=2)
        l.addWidget(self.canvas)
        return w

    def create_contents_tab(self):
        w = QWidget();
        l = QVBoxLayout(w)
        self.table_cont = QTableWidget()
        self.table_cont.setColumnCount(3)
        self.table_cont.setHorizontalHeaderLabels(["ماده", "فرمول", "مقدار"])
        self.table_cont.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        l.addWidget(self.table_cont)
        self.lbl_mix = QLabel("فرمول تجربی: -")
        l.addWidget(self.lbl_mix)
        return w

    def create_datasheet_tab(self):
        w = QWidget();
        l = QVBoxLayout(w)
        t = QTableWidget()
        t.setColumnCount(4)
        t.setHorizontalHeaderLabels(["نام", "فرمول", "نوع", "pH"])
        t.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        t.setRowCount(len(CHEMICAL_DB))
        for i, (k, v) in enumerate(sorted(CHEMICAL_DB.items(), key=lambda x: x[1]['name'])):
            t.setItem(i, 0, QTableWidgetItem(v['name']))
            t.setItem(i, 1, QTableWidgetItem(ChemicalCalculator.to_subscript(v['formula'])))
            t.setItem(i, 2, QTableWidgetItem(get_persian_type(v['type'])))
            t.setItem(i, 3, QTableWidgetItem(str(v['pH'])))
        l.addWidget(t)
        return w

    def create_details_group(self):
        gb = QGroupBox("مشخصات")
        gl = QGridLayout()
        self.lbl_d_name = QLabel("-")
        self.lbl_d_form = QLabel("-")
        self.lbl_d_type = QLabel("-")
        gl.addWidget(QLabel("نام:"), 0, 0);
        gl.addWidget(self.lbl_d_name, 0, 1)
        gl.addWidget(QLabel("فرمول:"), 1, 0);
        gl.addWidget(self.lbl_d_form, 1, 1)
        gl.addWidget(QLabel("نوع:"), 2, 0);
        gl.addWidget(self.lbl_d_type, 2, 1)
        gb.setLayout(gl)
        return gb

    def populate_chemicals(self):
        self.combo_chem.clear()
        for k, v in sorted(CHEMICAL_DB.items(), key=lambda x: x[1]['name']):
            self.combo_chem.addItem(f"{v['name']} ({v['formula']})", k)
        if self.combo_chem.count() > 0:
            self.combo_chem.setCurrentIndex(0)

    def filter_chemicals(self, text):
        self.combo_chem.blockSignals(True)
        self.combo_chem.clear()
        t = text.lower()
        for k, v in sorted(CHEMICAL_DB.items(), key=lambda x: x[1]['name']):
            if t in v['name'].lower() or t in v['formula'].lower() or t in k:
                self.combo_chem.addItem(f"{v['name']} ({v['formula']})", k)
        self.combo_chem.blockSignals(False)
        if self.combo_chem.count() > 0:
            self.combo_chem.setCurrentIndex(0)
            self.update_chem_details()

    def update_chem_details(self):
        k = self.combo_chem.currentData()
        if k:
            d = CHEMICAL_DB[k]
            self.lbl_d_name.setText(d['name'])
            self.lbl_d_form.setText(ChemicalCalculator.to_subscript(d['formula']))
            self.lbl_d_type.setText(get_persian_type(d['type']))

    def handle_reaction_result(self, disc):
        if not disc: return

        name, xp, status = disc
        if status == "new":
            self.timer.stop()
            self.txt_log.append(f"✨ <b style='color:#a6e3a1'>واکنش کشف شد: {name} (+{xp} XP)</b>")
            self.beaker.trigger_reaction_animation()
            self.update_player_stats()
            self.update_discoveries_table()
            self.update_wiki_table()
            QMessageBox.information(self, "کشف جدید", f"تبریک!\nواکنش: {name}\nامتیاز: {xp}")
            self.timer.start(50)
        elif status == "old":
            last_line = self.txt_log.toPlainText().split('\n')[-1]
            if f"تکراری: {name}" not in last_line:
                self.txt_log.append(f"⚠️ واکنش تکراری: {name}")

    def action_add(self):
        k = self.combo_chem.currentData()
        if not k:
            self.txt_log.append("❌ خطا: لطفاً یک ماده را از لیست انتخاب کنید.")
            return

        msg = self.engine.add_chemical(k, self.spin_vol.value())
        self.txt_log.append(f"🔹 {msg}")
        self.beaker.set_target_state(self.engine.total_volume, self.engine.dominant_color)
        self.update_contents_ui()
        disc = self.engine.check_reactions()
        self.handle_reaction_result(disc)

    def action_builder_add(self):
        k = self.combo_b.currentData()
        c = self.spin_b.value()
        self.engine.builder_parts.append((k, c))
        self.list_b.addItem(f"{c} × {PERIODIC_TABLE[k]}")

    def action_builder_calc(self):
        atoms = Counter()
        for k, c in self.engine.builder_parts: atoms[k] += c
        form = ChemicalCalculator.format_gross_formula(atoms, simplify=False, empirical=False)
        self.lbl_b_res.setText(form)
        form_emp = ChemicalCalculator.format_gross_formula(atoms, simplify=True, empirical=True)
        plain_f_emp = form_emp.translate(str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789"))
        found = None
        for v in CHEMICAL_DB.values():
            db_atoms = ChemicalCalculator.parse_formula(v['formula'])
            db_emp = ChemicalCalculator.format_gross_formula(db_atoms, simplify=True, empirical=True)
            plain_db_emp = db_emp.translate(str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789"))
            if plain_f_emp == plain_db_emp:
                found = v['name']
                break
        if found:
            self.lbl_b_desc.setText(f"✅ این فرمول متعلق به «{found}» است.")
        else:
            self.lbl_b_desc.setText("🧪 یک ترکیب جدید یا ناشناخته.")

    def action_wash(self):
        self.engine.reset()
        self.beaker.set_target_state(0, "#E0FFFF")
        self.update_contents_ui()
        self.txt_log.append("🚿 بشر شسته شد (محتویات خالی شد).")

    def action_reset(self):
        self.engine.reset()
        self.beaker.set_target_state(0, "#E0FFFF")
        self.data_time.clear();
        self.data_ph.clear();
        self.data_temp.clear()
        self.line_ph.set_data([], []);
        self.line_temp.set_data([], [])
        self.canvas.draw()
        self.update_contents_ui()
        self.txt_log.clear()

    def action_hard_reset(self):
        reply = QMessageBox.question(self, 'شروع مجدد بازی',
                                     "آیا مطمئن هستید؟\nتمام امتیازات و لول شما پاک شده و بازی از اول شروع می‌شود.",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.engine.hard_reset()
            self.beaker.set_target_state(0, "#E0FFFF")
            self.update_player_stats()
            self.update_contents_ui()
            self.update_discoveries_table()
            self.update_wiki_table()
            self.txt_log.clear()
            self.txt_log.append("🔄 بازی ریست شد. موفق باشید!")

    def update_player_stats(self):
        self.lbl_level.setText(f"سطح: {self.engine.level}")
        self.lbl_score.setText(f"امتیاز: {self.engine.score}")
        self.progress_xp.setValue(self.engine.score % 100)

    def update_discoveries_table(self):
        self.table_disc.setRowCount(len(CUSTOM_REACTIONS))
        for i, (n, d) in enumerate(CUSTOM_REACTIONS.items()):
            if n in self.engine.discovered:
                self.table_disc.setItem(i, 0, QTableWidgetItem(f"✅ {n}"))
                self.table_disc.item(i, 0).setForeground(QBrush(QColor("#a6e3a1")))
                ings = ", ".join([CHEMICAL_DB.get(normalize_key(x), {'name': x})['name'] for x in d['reactants']])
                self.table_disc.setItem(i, 1, QTableWidgetItem(ings))
            else:
                self.table_disc.setItem(i, 0, QTableWidgetItem("؟؟؟"))
                self.table_disc.item(i, 0).setForeground(QBrush(QColor("#6c7086")))
                self.table_disc.setItem(i, 1, QTableWidgetItem(f"ترکیب {len(d['reactants'])} ماده"))
            self.table_disc.setItem(i, 2, QTableWidgetItem(str(d['xp'])))

    def update_contents_ui(self):
        self.table_cont.setRowCount(0)
        r = 0
        for k, v in self.engine.contents.items():
            if v > 0.0001:
                self.table_cont.insertRow(r)
                self.table_cont.setItem(r, 0, QTableWidgetItem(CHEMICAL_DB[k]['name']))
                self.table_cont.setItem(r, 1,
                                        QTableWidgetItem(ChemicalCalculator.to_subscript(CHEMICAL_DB[k]['formula'])))
                self.table_cont.setItem(r, 2, QTableWidgetItem(f"{v:.4f} mol"))
                r += 1
        f, _ = self.engine.calculate_mixture_stats()
        self.lbl_mix.setText(f"فرمول تجربی: {f}")

    def game_loop(self):
        self.engine.update_physics()
        if not hasattr(self, 'start_time'): self.start_time = time.time()
        t = time.time() - self.start_time
        ph, temp = self.engine.get_ph(), self.engine.temp_c
        self.lbl_ph_display.setText(f"pH: {ph:.2f}")
        self.lbl_temp_display.setText(f"{temp:.1f} °C")
        disc = self.engine.check_reactions()
        self.handle_reaction_result(disc)
        self.data_time.append(t)
        self.data_ph.append(ph)
        self.data_temp.append(temp)
        max_points = 200
        if len(self.data_time) > max_points:
            self.data_time = self.data_time[-max_points:]
            self.data_ph = self.data_ph[-max_points:]
            self.data_temp = self.data_temp[-max_points:]
        self.line_ph.set_data(self.data_time, self.data_ph)
        self.line_temp.set_data(self.data_time, self.data_temp)
        if self.data_time:
            self.ax_ph.set_xlim(min(self.data_time), max(self.data_time) + 1)
            self.ax_ph.set_ylim(0, 14)
            self.ax_temp.set_xlim(min(self.data_time), max(self.data_time) + 1)
            self.ax_temp.set_ylim(min(self.data_temp) - 5, max(self.data_temp) + 5)
        self.canvas.draw()


if __name__ == '__main__':
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setFont(QFont(FONT_NAME, 10))
    app.setStyleSheet(APP_STYLE)
    w = ModernLabWindow()
    w.show()
    sys.exit(app.exec())
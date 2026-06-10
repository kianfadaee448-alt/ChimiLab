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
        QListWidget, QSpinBox, QProgressBar, QScrollArea, QDialog, QToolTip
    )
    from PyQt5.QtCore import Qt, QTimer, QRectF, QPropertyAnimation, pyqtProperty, QEasingCurve, QPoint
    from PyQt5.QtGui import QFont, QColor, QPainter, QPen, QLinearGradient, QPainterPath, QBrush, QCursor, QFontMetrics
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
except ImportError as e:
    print(f"Error: {e}")
    print("Please install required libraries: pip install PyQt5 matplotlib")
    sys.exit(1)

# =============================================================================
# دیتابیس داخلی برنامه
# =============================================================================

CHEMILAB_DB = {
    "naoh": {"name": "سدیم هیدروکسید", "formula": "NaOH", "type": "Strong Base", "pH": 13.0, "molarity": 0.1,
             "heat": -44.5, "color": "#FFFFFF"},
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
    "(nh4)2cr2o7": {"name": "آمونیوم دی‌کرومات", "formula": "(NH4)2Cr2O7", "type": "Salt", "pH": 4.0, "molarity": 0.1,
                    "heat": 75.0, "color": "#FF8C00"},
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

CUSTOM_REACTIONS = {

    "تشکیل اکسید آهن (زنگ آهن)": {"reactants": ["Fe", "O2"], "products": ["Fe2O3"],
                                  "desc": "آهن در حضور اکسیژن و رطوبت زنگ می‌زند.", "xp": 50},
    "ترکیب هیدروژن و اکسیژن": {"reactants": ["H2", "O2"], "products": ["H2O"], "desc": "انفجار شدید تولید آب.",
                               "xp": 80},
    "سوختن متان": {"reactants": ["CH4", "O2"], "products": ["CO2", "H2O"], "desc": "احتراق گاز طبیعی.", "xp": 40},
    "خنثی‌سازی اسید و باز": {"reactants": ["HCl", "NaOH"], "products": ["NaCl", "H2O"], "desc": "تولید نمک و آب.",
                             "xp": 75},
    "تشکیل آمونیاک (هابر)": {"reactants": ["N2", "H2"], "products": ["NH3"], "desc": "سنتز صنعتی آمونیاک.", "xp": 120},
    "تجزیه آب (الکترولیز)": {"reactants": ["H2O"], "products": ["H2", "O2"], "desc": "تجزیه الکتریکی آب.", "xp": 90},
    "رسوب نقره کلرید": {"reactants": ["AgNO3", "NaCl"], "products": ["AgCl", "NaNO3"], "desc": "رسوب سفید شیرمانند.",
                        "xp": 60},
    "باران طلایی (یدید سرب)": {"reactants": ["Pb(NO3)2", "KI"], "products": ["PbI2"], "desc": "رسوب زرد طلایی زیبا.",
                               "xp": 100},
    "دود سفید نشادر": {"reactants": ["NH3", "HCl"], "products": ["NH4Cl"], "desc": "تشکیل دود سفید آمونیوم کلرید.",
                       "xp": 65},
    "سوختن منیزیم": {"reactants": ["Mg", "O2"], "products": ["MgO"], "desc": "نور شدید سفید.", "xp": 70},
    "تولید دی‌اکسید کربن": {"reactants": ["CaCO3", "HCl"], "products": ["CaCl2", "CO2", "H2O"],
                            "desc": "حباب گاز از سنگ آهک.", "xp": 45},
    "محلول آبی سولفات مس": {"reactants": ["CuSO4", "H2O"], "products": ["CuSO4(aq)"], "desc": "رنگ آبی شفاف.",
                            "xp": 20},
    "اکسایش گلوکز": {"reactants": ["C6H12O6", "O2"], "products": ["CO2", "H2O"], "desc": "تنفس سلولی.", "xp": 110},
    "ترکیب سدیم و کلر": {"reactants": ["Na", "Cl2"], "products": ["NaCl"], "desc": "واکنش انفجاری نمک طعام.", "xp": 95},
    "رسوب هیدروکسید آهن": {"reactants": ["FeCl3", "NaOH"], "products": ["Fe(OH)3"], "desc": "رسوب قهوه‌ای ژله‌ای.",
                           "xp": 55},
    "تولید گاز هیدروژن": {"reactants": ["Zn", "HCl"], "products": ["ZnCl2", "H2"], "desc": "حباب گاز هیدروژن.",
                          "xp": 50},
    "سوختن اتانول": {"reactants": ["C2H5OH", "O2"], "products": ["CO2", "H2O"], "desc": "احتراق الکل.", "xp": 60},
    "تشکیل اسید سولفوریک": {"reactants": ["SO3", "H2O"], "products": ["H2SO4"], "desc": "واکنش گرمازا شدید.", "xp": 85},
    "رسوب باریم سولفات": {"reactants": ["BaCl2", "Na2SO4"], "products": ["BaSO4"], "desc": "رسوب سفید سنگین.",
                          "xp": 40},
    # دمای بالا نیاز دارد
    "آتشفشان آمونیوم دی‌کرومات": {"reactants": ["(NH4)2Cr2O7"], "products": ["Cr2O3", "N2", "H2O"],
                                  "desc": "تجزیه به شکل کوه آتشفشان.", "xp": 200, "temp_min": 150},
    "تولید اکسیژن (پراکسید)": {"reactants": ["H2O2"], "products": ["H2O", "O2"],
                               "desc": "تجزیه کاتالیزی پراکسید هیدروژن.", "xp": 70},
    "رسوب کرومات سرب": {"reactants": ["Pb(NO3)2", "K2CrO4"], "products": ["PbCrO4"], "desc": "رسوب زرد کروم.",
                        "xp": 80},
    "خنثی‌سازی با بی‌کربنات": {"reactants": ["HCl", "NaHCO3"], "products": ["NaCl", "CO2", "H2O"],
                               "desc": "حباب دی‌اکسید کربن.", "xp": 55},
    "سوختن پروپان": {"reactants": ["C3H8", "O2"], "products": ["CO2", "H2O"], "desc": "احتراق گاز آشپزخانه.", "xp": 45},
    "تشکیل نیترات آمونیوم": {"reactants": ["NH3", "HNO3"], "products": ["NH4NO3"], "desc": "واکنش خنثی‌سازی کود.",
                             "xp": 65},
    "رسوب فسفات کلسیم": {"reactants": ["CaCl2", "Na3PO4"], "products": ["Ca3(PO4)2"], "desc": "رسوب سفید استخوان.",
                         "xp": 50},
    "تولید گاز آمونیاک": {"reactants": ["NH4Cl", "NaOH"], "products": ["NH3", "NaCl", "H2O"],
                          "desc": "بوی تند آمونیاک.", "xp": 60},
    "اکسایش الکل به آلدهید": {"reactants": ["C2H5OH", "O2"], "products": ["CH3CHO", "H2O"], "desc": "با کاتالیزور مس.",
                              "xp": 90},
    "رسوب ید": {"reactants": ["KI", "Pb(NO3)2"], "products": ["PbI2"], "desc": "رسوب زرد یدید سرب.", "xp": 70},
    "سوختن گوگرد": {"reactants": ["S", "O2"], "products": ["SO2"], "desc": "بوی تند دی‌اکسید گوگرد.", "xp": 55},
    "ترکیب آهن و گوگرد": {"reactants": ["Fe", "S"], "products": ["FeS"], "desc": "واکنش گرمازا سولفید آهن.", "xp": 80},
    "تجزیه کلرات پتاسیم": {"reactants": ["KClO3"], "products": ["KCl", "O2"], "desc": "تولید اکسیژن.", "xp": 75,
                           "temp_min": 100},
    "رسوب هیدروکسید آلومینیوم": {"reactants": ["AlCl3", "NaOH"], "products": ["Al(OH)3"], "desc": "رسوب سفید ژله‌ای.",
                                 "xp": 60},
    "تولید گاز نیتروژن": {"reactants": ["NH4NO2"], "products": ["N2", "H2O"], "desc": "تجزیه نیترات آمونیوم.", "xp": 85,
                          "temp_min": 100},
    "سوختن فسفر سفید": {"reactants": ["P4", "O2"], "products": ["P4O10"], "desc": "نور شدید و دود.", "xp": 100},
    "تشکیل اسید نیتریک": {"reactants": ["NO2", "H2O", "O2"], "products": ["HNO3"], "desc": "اکسایش دی‌اکسید نیتروژن.",
                          "xp": 110},
    "رسوب سیانید نقره": {"reactants": ["AgNO3", "KCN"], "products": ["AgCN"], "desc": "رسوب سفید (خطرناک).", "xp": 70},
    "خنثی‌سازی سرکه و جوش شیرین": {"reactants": ["CH3COOH", "NaHCO3"], "products": ["CH3COONa", "CO2", "H2O"],
                                   "desc": "حباب برای آتشفشان خانگی.", "xp": 40},
    "تولید هیدروکسید مس": {"reactants": ["CuSO4", "NaOH"], "products": ["Cu(OH)2"], "desc": "رسوب آبی روشن.", "xp": 55},
    "سوختن هیدروژن": {"reactants": ["H2", "O2"], "products": ["H2O"], "desc": "انفجار با صدای پوپ.", "xp": 65},
    "ترکیب کلسیم و آب": {"reactants": ["Ca", "H2O"], "products": ["Ca(OH)2", "H2"], "desc": "تولید گاز هیدروژن.",
                         "xp": 70},
    "رسوب کربنات کلسیم": {"reactants": ["CaCl2", "Na2CO3"], "products": ["CaCO3"], "desc": "رسوب سفید سنگ آهک.",
                          "xp": 45},
    "تجزیه پرمنگنات پتاسیم": {"reactants": ["KMnO4"], "products": ["K2MnO4", "MnO2", "O2"],
                              "desc": "تولید اکسیژن بنفش.", "xp": 95, "temp_min": 120},
    "اکسایش یدید به ید": {"reactants": ["KI", "H2O2"], "products": ["I2"], "desc": "رنگ قهوه‌ای ید آزاد.", "xp": 80},
    "سوختن استیلن": {"reactants": ["C2H2", "O2"], "products": ["CO2", "H2O"], "desc": "شعله داغ جوشکاری.", "xp": 75},
    "تشکیل کلرید آهن(III)": {"reactants": ["Fe", "Cl2"], "products": ["FeCl3"], "desc": "واکنش گرمازا کلر.", "xp": 90},
    "رسوب سولفید روی": {"reactants": ["ZnSO4", "H2S"], "products": ["ZnS"], "desc": "رسوب سفید سولفید.", "xp": 60},
    "تولید گاز استیلن": {"reactants": ["CaC2", "H2O"], "products": ["C2H2"], "desc": "بوی سیر استیلن.", "xp": 70},
    "خنثی‌سازی اسید سیتریک": {"reactants": ["C6H8O7", "NaOH"], "products": ["Na3C6H5O7", "H2O"],
                              "desc": "واکنش آب لیمو و باز.", "xp": 50},
    "سوختن بوتان": {"reactants": ["C4H10", "O2"], "products": ["CO2", "H2O"], "desc": "احتراق فندک.", "xp": 40},
    "رسوب اکسالات کلسیم": {"reactants": ["CaCl2", "Na2C2O4"], "products": ["CaC2O4"], "desc": "رسوب سفید سنگ کلیه.",
                           "xp": 65},
    "تجزیه نیترات سرب": {"reactants": ["Pb(NO3)2"], "products": ["PbO", "NO2", "O2"], "desc": "گاز قهوه‌ای سمی.",
                         "xp": 85, "temp_min": 180},
    "اکسایش مس با نیتریک اسید": {"reactants": ["Cu", "HNO3"], "products": ["Cu(NO3)2", "NO2"],
                                 "desc": "گاز قهوه‌ای و محلول آبی.", "xp": 95},
    "سوختن نفتالن": {"reactants": ["C10H8", "O2"], "products": ["CO2", "H2O"], "desc": "شعله دودزا.", "xp": 55},
    "تشکیل پلیمر نایلون": {"reactants": ["Hexamethylenediamine", "Adipoyl chloride"], "products": ["Nylon"],
                           "desc": "رشته نایلون در مرز دو فاز.", "xp": 120},
    "رسوب برمید نقره": {"reactants": ["AgNO3", "NaBr"], "products": ["AgBr"], "desc": "رسوب کرمی رنگ.", "xp": 50},
    "تولید گاز فسفین": {"reactants": ["Ca3P2", "H2O"], "products": ["PH3"], "desc": "گاز سمی خوداشتعال.", "xp": 100},
    "خنثی‌سازی با کربنات": {"reactants": ["H2SO4", "Na2CO3"], "products": ["Na2SO4", "CO2", "H2O"],
                            "desc": "حباب شدید.", "xp": 45},
    "سوختن پنتاان": {"reactants": ["C5H12", "O2"], "products": ["CO2", "H2O"], "desc": "احتراق بنزین.", "xp": 40},
    "رسوب هیدروکسید نیکل": {"reactants": ["NiSO4", "NaOH"], "products": ["Ni(OH)2"], "desc": "رسوب سبز روشن.",
                            "xp": 60},
    "تجزیه آزید سدیم": {"reactants": ["NaN3"], "products": ["Na", "N2"], "desc": "تولید گاز ایربگ.", "xp": 90,
                        "temp_min": 100},
    "اکسایش سولفیت": {"reactants": ["Na2SO3", "O2"], "products": ["Na2SO4"], "desc": "اکسایش هوا به سولفات.", "xp": 70},
    "سوختن هگزان": {"reactants": ["C6H14", "O2"], "products": ["CO2", "H2O"], "desc": "احتراق سوخت.", "xp": 40},
    "تشکیل سولفید هیدروژن": {"reactants": ["FeS", "HCl"], "products": ["H2S"], "desc": "بوی تخم‌گندیده.", "xp": 65},
    "رسوب فلورید کلسیم": {"reactants": ["CaCl2", "NaF"], "products": ["CaF2"], "desc": "رسوب سفید دندان.", "xp": 50},
    "تولید کلر (الکترولیز نمک)": {"reactants": ["NaCl", "H2O"], "products": ["Cl2", "H2", "NaOH"],
                                  "desc": "الکترولیز آب نمک.", "xp": 100},
    "خنثی‌سازی فسفریک اسید": {"reactants": ["H3PO4", "NaOH"], "products": ["Na3PO4", "H2O"], "desc": "تولید فسفات.",
                              "xp": 55},
    "سوختن اکتان": {"reactants": ["C8H18", "O2"], "products": ["CO2", "H2O"], "desc": "احتراق بنزین اصلی.", "xp": 45},
    "رسوب تیوسیانات آهن": {"reactants": ["FeCl3", "KSCN"], "products": ["Fe(SCN)3"], "desc": "رنگ قرمز خون.", "xp": 85},
    "تجزیه هیدروژن پراکسید با کاتالیزور": {"reactants": ["H2O2", "MnO2"], "products": ["H2O", "O2"],
                                           "desc": "حباب شدید اکسیژن.", "xp": 60},
    "اکسایش منگنز(II)": {"reactants": ["MnSO4", "H2O2"], "products": ["MnO2"], "desc": "رسوب قهوه‌ای دی‌اکسید منگنز.",
                         "xp": 70},
    "سوختن بنزن": {"reactants": ["C6H6", "O2"], "products": ["CO2", "H2O"], "desc": "شعله دودزا سیاه.", "xp": 55},
    "تشکیل سیلیکات ژل": {"reactants": ["Na2SiO3", "HCl"], "products": ["SiO2 gel"], "desc": "ژل سیلیکا باغبانی.",
                         "xp": 75},
    "رسوب کبالت سولفید": {"reactants": ["CoCl2", "H2S"], "products": ["CoS"], "desc": "رسوب سیاه.", "xp": 60},
    "تولید گاز نیتریک اکسید": {"reactants": ["Cu", "HNO3"], "products": ["Cu(NO3)2", "NO"],
                               "desc": "گاز بی‌رنگ به قهوه‌ای.", "xp": 80},
    "خنثی‌سازی بوریک اسید": {"reactants": ["H3BO3", "NaOH"], "products": ["Na3BO3", "H2O"], "desc": "واکنش ضعیف.",
                             "xp": 50},
    "سوختن تولوئن": {"reactants": ["C7H8", "O2"], "products": ["CO2", "H2O"], "desc": "احتراق دودزا.", "xp": 45},
    "رسوب کروم هیدروکسید": {"reactants": ["CrCl3", "NaOH"], "products": ["Cr(OH)3"], "desc": "رسوب سبز خاکستری.",
                            "xp": 65},
    "تجزیه آمونیوم نیترات": {"reactants": ["NH4NO3"], "products": ["N2O", "H2O"], "desc": "گاز خنده (گرم).", "xp": 90,
                             "temp_min": 120},
    "اکسایش برمید": {"reactants": ["NaBr", "Cl2"], "products": ["Br2"], "desc": "رنگ نارنجی برم آزاد.", "xp": 75},
    "سوختن زایلن": {"reactants": ["C8H10", "O2"], "products": ["CO2", "H2O"], "desc": "احتراق آروماتیک.", "xp": 50},
    "تشکیل کمپلکس آبی مس": {"reactants": ["CuSO4", "NH3"], "products": ["[Cu(NH3)4]SO4"], "desc": "رنگ آبی تیره.",
                            "xp": 80},
    "رسوب منگنز سولفید": {"reactants": ["MnSO4", "H2S"], "products": ["MnS"], "desc": "رسوب صورتی گوشتی.", "xp": 60},
    "تولید دی‌نیتروژن اکسید": {"reactants": ["NH4NO3"], "products": ["N2O", "H2O"], "desc": "گاز خنده.", "xp": 70,
                               "temp_min": 80},
    "خنثی‌سازی استیک اسید": {"reactants": ["CH3COOH", "KOH"], "products": ["CH3COOK", "H2O"],
                             "desc": "تولید استات پتاسیم.", "xp": 45},
    "سوختن استایرن": {"reactants": ["C8H8", "O2"], "products": ["CO2", "H2O"], "desc": "احتراق پلی‌استایرن.", "xp": 50},
    "رسوب کادمیم سولفید": {"reactants": ["CdSO4", "H2S"], "products": ["CdS"], "desc": "رسوب زرد روشن.", "xp": 65},
    "تجزیه پتاسیم کلرات با کاتالیزور": {"reactants": ["KClO3", "MnO2"], "products": ["KCl", "O2"],
                                        "desc": "تولید سریع اکسیژن.", "xp": 75},
    "اکسایش آرسنیک": {"reactants": ["As", "O2"], "products": ["As2O3"], "desc": "سمی سفید.", "xp": 80},
    "سوختن فنل": {"reactants": ["C6H5OH", "O2"], "products": ["CO2", "H2O"], "desc": "احتراق فنولی.", "xp": 55},
    "تشکیل کمپلکس آهن تیوسیانات": {"reactants": ["Fe3+", "SCN-"], "products": ["[FeSCN]2+"], "desc": "رنگ قرمز شدید.",
                                   "xp": 85},
    "رسوب استرانسیم سولفات": {"reactants": ["SrCl2", "Na2SO4"], "products": ["SrSO4"], "desc": "رسوب سفید.", "xp": 40},
    "تولید گاز متان": {"reactants": ["CH3I", "Mg"], "products": ["CH4"], "desc": "تولید متان ساده.", "xp": 90},
    "خنثی‌سازی لاکتیک اسید": {"reactants": ["C3H6O3", "NaOH"], "products": ["NaC3H5O3", "H2O"], "desc": "اسید شیر.",
                              "xp": 50},
    "سوختن انیلین": {"reactants": ["C6H5NH2", "O2"], "products": ["CO2", "H2O", "N2"], "desc": "احتراق آمینی.",
                     "xp": 60},
    "رسوب باریم کربنات": {"reactants": ["BaCl2", "Na2CO3"], "products": ["BaCO3"], "desc": "رسوب سفید سنگین.",
                          "xp": 45},
    # دمای بالا
    "تجزیه سدیم بی‌کربنات": {"reactants": ["NaHCO3"], "products": ["Na2CO3", "CO2", "H2O"], "desc": "جوش شیرین در پخت.",
                             "xp": 55, "temp_min": 60},
    "اکسایش قلع": {"reactants": ["Sn", "HNO3"], "products": ["SnO2"], "desc": "تشکیل متااستانیک اسید.", "xp": 70},
    "سوختن پیریدین": {"reactants": ["C5H5N", "O2"], "products": ["CO2", "H2O", "NO2"], "desc": "احتراق نیتروژنی.",
                      "xp": 65},
    "تشکیل اسید استیک": {"reactants": ["C2H5OH", "KMnO4"], "products": ["CH3COOH"], "desc": "سرکه از الکل.", "xp": 80},
    "رسوب روی کربنات": {"reactants": ["ZnSO4", "Na2CO3"], "products": ["ZnCO3"], "desc": "رسوب سفید پایه.", "xp": 50},
    "تولید گاز کربنیل کلرید": {"reactants": ["CO", "Cl2"], "products": ["COCl2"], "desc": "گاز سمی (فقط تئوری).",
                               "xp": 120},
    "خنثی‌سازی تارتاریک اسید": {"reactants": ["C4H6O6", "NaOH"], "products": ["Na2C4H4O6", "H2O"],
                                "desc": "اسید ترتار.", "xp": 55},
    "سوختن نفتالین": {"reactants": ["C10H8", "O2"], "products": ["CO2", "H2O"], "desc": "دود سیاه ضدبید.", "xp": 60},
    "تولید گاز اکسیژن از گیاهان": {"reactants": ["CO2", "H2O"], "products": ["C6H12O6", "O2"],
                                   "desc": "فتوسنتز در گیاهان سبز.", "xp": 100},
    "اکسایش آهن(II) به آهن(III)": {"reactants": ["FeSO4", "O2"], "products": ["Fe2(SO4)3"], "desc": "اکسایش در هوا.",
                                   "xp": 60},
    "رسوب هیدروکسید منیزیم": {"reactants": ["MgCl2", "NaOH"], "products": ["Mg(OH)2"], "desc": "رسوب سفید شیر آهک.",
                              "xp": 50},
    "سوختن متیل الکل": {"reactants": ["CH3OH", "O2"], "products": ["CO2", "H2O"], "desc": "احتراق متانول.", "xp": 45},
    "تشکیل اسید کلریدریک": {"reactants": ["H2", "Cl2"], "products": ["HCl"], "desc": "ترکیب مستقیم هالوژن.", "xp": 80},
    "تجزیه کربنات سدیم": {"reactants": ["Na2CO3"], "products": ["Na2O", "CO2"], "desc": "تجزیه گرمایی.", "xp": 55,
                          "temp_min": 100},
    "رسوب سولفید مس": {"reactants": ["CuSO4", "H2S"], "products": ["CuS"], "desc": "رسوب سیاه.", "xp": 65},
    "تولید سدیم هیدروکسید": {"reactants": ["NaCl", "H2O"], "products": ["NaOH", "Cl2", "H2"],
                             "desc": "فرایند کلر-آلکالی.", "xp": 110},
    "اکسایش سدیم سولفیت": {"reactants": ["Na2SO3", "H2O2"], "products": ["Na2SO4"], "desc": "اکسایش ملایم.", "xp": 60},
    "سوختن اتیلن": {"reactants": ["C2H4", "O2"], "products": ["CO2", "H2O"], "desc": "احتراق الفین.", "xp": 50},
    "تشکیل کمپلکس کبالت": {"reactants": ["CoCl2", "NH3"], "products": ["[Co(NH3)6]Cl3"],
                           "desc": "رنگ تغییر از صورتی به زرد.", "xp": 90},
    "رسوب فسفات نقره": {"reactants": ["AgNO3", "Na3PO4"], "products": ["Ag3PO4"], "desc": "رسوب زرد.", "xp": 70},
    "تولید گاز دی‌اکسید گوگرد": {"reactants": ["Cu", "H2SO4"], "products": ["CuSO4", "SO2"],
                                 "desc": "واکنش مس با اسید سولفوریک.", "xp": 75},
    "خنثی‌سازی اسید فرمیک": {"reactants": ["HCOOH", "NaOH"], "products": ["HCOONa", "H2O"], "desc": "اسید مورچه.",
                             "xp": 50},
    "سوختن پروپیلن": {"reactants": ["C3H6", "O2"], "products": ["CO2", "H2O"], "desc": "احتراق گاز پالایشگاهی.",
                      "xp": 45},
    "رسوب یدید نقره": {"reactants": ["AgNO3", "KI"], "products": ["AgI"], "desc": "رسوب زرد کم‌رنگ.", "xp": 60},
    "تجزیه پتاسیم پرمنگنات": {"reactants": ["KMnO4"], "products": ["K2MnO4", "MnO2", "O2"], "desc": "رنگ بنفش ناپدید.",
                              "xp": 85, "temp_min": 130},
    "اکسایش اتانول به استیک اسید": {"reactants": ["C2H5OH", "O2"], "products": ["CH3COOH"], "desc": "تولید سرکه.",
                                    "xp": 95},
    "سوختن بوتن": {"reactants": ["C4H8", "O2"], "products": ["CO2", "H2O"], "desc": "احتراق بوتادین بخشی.", "xp": 50},
    "تشکیل هیدرازین": {"reactants": ["NH3", "NaOCl"], "products": ["N2H4"], "desc": "واکنش راشینگ (ساده).", "xp": 100},
    "رسوب اکسید قلع": {"reactants": ["SnCl2", "NaOH"], "products": ["Sn(OH)2"], "desc": "رسوب سفید آمفوتر.", "xp": 65},
    "تولید گاز هیدروژن از آلومینیوم": {"reactants": ["Al", "NaOH"], "products": ["NaAlO2", "H2"], "desc": "حباب شدید.",
                                       "xp": 70},
    "خنثی‌سازی اسید اگزالیک": {"reactants": ["H2C2O4", "NaOH"], "products": ["Na2C2O4", "H2O"], "desc": "اسید اگزالات.",
                               "xp": 55},
    "سوختن ایزوپروپیل الکل": {"reactants": ["C3H7OH", "O2"], "products": ["CO2", "H2O"],
                              "desc": "احتراق ضدعفونی‌کننده.", "xp": 45},
    "رسوب سولفات سرب": {"reactants": ["Pb(NO3)2", "H2SO4"], "products": ["PbSO4"], "desc": "رسوب سفید سنگین.",
                        "xp": 60},
    "تجزیه هیدرازین": {"reactants": ["N2H4"], "products": ["N2", "H2"], "desc": "تجزیه سوخت موشک.", "xp": 90},
    "اکسایش سولفید به سولفات": {"reactants": ["Na2S", "O2"], "products": ["Na2SO4"], "desc": "اکسایش هوا.", "xp": 65},
    "سوختن پنتیل الکل": {"reactants": ["C5H11OH", "O2"], "products": ["CO2", "H2O"], "desc": "احتراق الکل بالاتر.",
                         "xp": 50},
    "تشکیل کمپلکس نیکل": {"reactants": ["NiSO4", "NH3"], "products": ["[Ni(NH3)6]SO4"], "desc": "رنگ آبی به سبز.",
                          "xp": 80},
    "رسوب کربنات نقره": {"reactants": ["AgNO3", "Na2CO3"], "products": ["Ag2CO3"], "desc": "رسوب زرد کم‌رنگ.",
                         "xp": 60},
    "تولید گاز نیتروژن دی‌اکسید": {"reactants": ["Cu", "HNO3"], "products": ["Cu(NO2)2", "NO2"],
                                   "desc": "گاز قهوه‌ای سمی.", "xp": 85},
    "خنثی‌سازی اسید مالئیک": {"reactants": ["C4H4O4", "NaOH"], "products": ["Na2C4H2O4", "H2O"], "desc": "اسید سیس.",
                              "xp": 55},
    "سوختن هپتان": {"reactants": ["C7H16", "O2"], "products": ["CO2", "H2O"], "desc": "احتراق سوخت دیزل.", "xp": 45},
    "رسوب فلورید باریم": {"reactants": ["BaCl2", "NaF"], "products": ["BaF2"], "desc": "رسوب سفید.", "xp": 50},
    "تجزیه آمونیوم بی‌کرومات": {"reactants": ["(NH4)2Cr2O7"], "products": ["Cr2O3", "N2", "H2O"],
                                "desc": "آتشفشان سبز.", "xp": 120, "temp_min": 150},
    "اکسایش فسفیت": {"reactants": ["Na3PO3", "I2"], "products": ["Na3PO4"], "desc": "اکسایش ید.", "xp": 70},
    "سوختن دکان": {"reactants": ["C10H22", "O2"], "products": ["CO2", "H2O"], "desc": "احتراق نفت سفید.", "xp": 50},
    "تشکیل اسید هیپوکلروس": {"reactants": ["Cl2", "H2O"], "products": ["HClO", "HCl"], "desc": "آب ژاول.", "xp": 75},
    "رسوب سولفید کادمیم": {"reactants": ["Cd(NO3)2", "Na2S"], "products": ["CdS"], "desc": "رسوب زرد.", "xp": 65},
    "تولید هیدروژن پراکسید": {"reactants": ["BaO2", "H2SO4"], "products": ["BaSO4", "H2O2"], "desc": "روش قدیمی.",
                              "xp": 80},
    "خنثی‌سازی اسید ساکسینیک": {"reactants": ["C4H6O4", "KOH"], "products": ["K2C4H4O4", "H2O"],
                                "desc": "اسید کهربایی.", "xp": 55},
    "سوختن سیکلوهگزان": {"reactants": ["C6H12", "O2"], "products": ["CO2", "H2O"], "desc": "احتراق حلقوی.", "xp": 50},
    "رسوب کرومات باریم": {"reactants": ["BaCl2", "K2CrO4"], "products": ["BaCrO4"], "desc": "رسوب زرد.", "xp": 60},
    "تجزیه پتاسیم نیترات": {"reactants": ["KNO3"], "products": ["KNO2", "O2"], "desc": "تولید اکسیژن.", "xp": 70,
                            "temp_min": 100},
    "اکسایش تیو سولفات": {"reactants": ["Na2S2O3", "I2"], "products": ["Na2S4O6"], "desc": "واکنش ساعت ید.", "xp": 85},
    "سوختن تولوئن با اکسیژن ناکافی": {"reactants": ["C7H8", "O2"], "products": ["C", "CO", "H2O"], "desc": "دود سیاه.",
                                      "xp": 55},
    "تشکیل کمپلکس آهن(II)": {"reactants": ["FeSO4", "KCN"], "products": ["K4[Fe(CN)6]"], "desc": "فروسیانید.",
                             "xp": 90},
    "رسوب سولفات استرانسیم": {"reactants": ["Sr(NO3)2", "H2SO4"], "products": ["SrSO4"], "desc": "رسوب سفید.",
                              "xp": 50},
    "تولید گاز آرگون": {"reactants": ["air"], "products": ["Ar", "N2", "O2"], "desc": "تقطیر جزء به جزء.", "xp": 100},
    "خنثی‌سازی اسید بنزوییک": {"reactants": ["C6H5COOH", "NaOH"], "products": ["C6H5COONa", "H2O"],
                               "desc": "بنزن کربوکسیلیک.", "xp": 60},
    "سوختن استون": {"reactants": ["CH3COCH3", "O2"], "products": ["CO2", "H2O"], "desc": "احتراق کتون.", "xp": 45},
    "رسوب فسفات باریم": {"reactants": ["BaCl2", "Na3PO4"], "products": ["Ba3(PO4)2"], "desc": "رسوب سفید.", "xp": 55},
    "تجزیه سدیم آزید": {"reactants": ["NaN3"], "products": ["Na", "N2"], "desc": "ایربگ خودرو.", "xp": 85,
                        "temp_min": 100},
    "اکسایش هیدرازین": {"reactants": ["N2H4", "O2"], "products": ["N2", "H2O"], "desc": "احتراق سوخت موشک.", "xp": 95},
    "سوختن فرمالدئید": {"reactants": ["HCHO", "O2"], "products": ["CO2", "H2O"], "desc": "احتراق آلدهید.", "xp": 50},
    "تشکیل پلی‌اتیلن": {"reactants": ["C2H4"], "products": ["(C2H4)n"], "desc": "پلیمریزاسیون.", "xp": 110},
    "رسوب کلرید باریم": {"reactants": ["Ba(NO3)2", "HCl"], "products": ["BaCl2"],
                         "desc": "محلول باقی می‌ماند (قابل حل).", "xp": 40},
    "تولید کلسیم کاربید": {"reactants": ["CaO", "C"], "products": ["CaC2"], "desc": "در کوره الکتریکی.", "xp": 90,
                           "temp_min": 300},
    "خنثی‌سازی اسید سالیسیلیک": {"reactants": ["C6H4(OH)COOH", "NaOH"], "products": ["C6H4(OH)COONa", "H2O"],
                                 "desc": "آسپیرین پایه.", "xp": 60},
    "سوختن گلوکز": {"reactants": ["C6H12O6", "O2"], "products": ["CO2", "H2O"], "desc": "احتراق قند.", "xp": 55},
    "رسوب سولفید آهن(II)": {"reactants": ["FeSO4", "Na2S"], "products": ["FeS"], "desc": "رسوب سیاه.", "xp": 60},
    "تجزیه باریم پراکسید": {"reactants": ["BaO2"], "products": ["BaO", "O2"], "desc": "تولید اکسیژن قدیمی.", "xp": 75,
                            "temp_min": 200},
    "اکسایش منیزیم با دی‌اکسید کربن": {"reactants": ["Mg", "CO2"], "products": ["MgO", "C"], "desc": "سوختن در CO2.",
                                       "xp": 80},
    "سوختن پارافین": {"reactants": ["C20H42", "O2"], "products": ["CO2", "H2O"], "desc": "احتراق شمع.", "xp": 50},
    "تشکیل اسید فسفریک": {"reactants": ["P4O10", "H2O"], "products": ["H3PO4"], "desc": "واکنش گرمازا.", "xp": 70},
    "رسوب کربنات استرانسیم": {"reactants": ["SrCl2", "Na2CO3"], "products": ["SrCO3"], "desc": "رسوب سفید.", "xp": 55},
    "تولید گاز سیلان": {"reactants": ["Mg2Si", "HCl"], "products": ["SiH4"], "desc": "گاز خوداشتعال.", "xp": 100},
    "خنثی‌سازی اسید پالمیتیک": {"reactants": ["C16H32O2", "NaOH"], "products": ["C16H31O2Na", "H2O"],
                                "desc": "صابون‌سازی.", "xp": 65},
    "سوختن دی‌متیل اتر": {"reactants": ["C2H6O", "O2"], "products": ["CO2", "H2O"], "desc": "احتراق اتر.", "xp": 50},
    "رسوب هیدروکسید کروم": {"reactants": ["Cr2(SO4)3", "NH3"], "products": ["Cr(OH)3"], "desc": "رسوب آمفوتر.",
                            "xp": 70},
    "تجزیه کلسیم هیپوکلریت": {"reactants": ["Ca(OCl)2"], "products": ["CaCl2", "O2"], "desc": "پودر سفیدکننده.",
                              "xp": 75},
    "اکسایش گزانتات": {"reactants": ["xanthate", "O2"], "products": ["dixanthogen"], "desc": "در فلوتاسیون.", "xp": 85},
    "سوختن کربوهیدرات": {"reactants": ["starch", "O2"], "products": ["CO2", "H2O"], "desc": "احتراق نشاسته.", "xp": 55},
    "تشکیل پلی‌پروپیلن": {"reactants": ["C3H6"], "products": ["(C3H6)n"], "desc": "پلیمریزاسیون استریو.", "xp": 110},
    "رسوب سولفید قلع": {"reactants": ["SnCl2", "H2S"], "products": ["SnS"], "desc": "رسوب قهوه‌ای.", "xp": 65},
    "تولید آلومینیوم (الکترولیز)": {"reactants": ["Al2O3", "O2"], "products": ["Al", "O2"], "desc": "فرایند هال-هرولت.",
                                    "xp": 120},
    "خنثی‌سازی اسید استئاریک": {"reactants": ["C18H36O2", "KOH"], "products": ["C18H35O2K", "H2O"],
                                "desc": "صابون پتاسیم.", "xp": 60},
    "سوختن فرئون": {"reactants": ["CCl2F2"], "products": ["CO2", "HF", "Cl2"], "desc": "تجزیه مضر.", "xp": 70},
    "رسوب اکسالات نقره": {"reactants": ["AgNO3", "H2C2O4"], "products": ["Ag2C2O4"], "desc": "رسوب سفید.", "xp": 55},
    "تجزیه پتاسیم یدات": {"reactants": ["KIO3"], "products": ["KI", "O2"], "desc": "تولید اکسیژن.", "xp": 75,
                          "temp_min": 100},
    "اکسایش تولوئن به بنزالدئید": {"reactants": ["C6H5CH3", "KMnO4"], "products": ["C6H5CHO"], "desc": "اکسایش جانبی.",
                                   "xp": 90},
    "سوختن لیپید": {"reactants": ["fat", "O2"], "products": ["CO2", "H2O"], "desc": "متابولیسم چربی.", "xp": 60},
    "تشکیل پلی‌وینیل کلرید": {"reactants": ["C2H3Cl"], "products": ["(C2H3Cl)n"], "desc": "PVC.", "xp": 100},
    "رسوب سولفید آنتیموان": {"reactants": ["SbCl3", "H2S"], "products": ["Sb2S3"], "desc": "رسوب نارنجی.", "xp": 70},
    "تولید مس (از سنگ معدن)": {"reactants": ["Cu2S", "O2"], "products": ["Cu", "SO2"], "desc": "روستینگ و ذوب.",
                               "xp": 95},
    "خنثی‌سازی اسید اولئیک": {"reactants": ["C18H34O2", "NaOH"], "products": ["C18H33O2Na", "H2O"],
                              "desc": "صابون مایع.", "xp": 65},
    "سوختن متانول با شعله آبی": {"reactants": ["CH3OH", "O2"], "products": ["CO2", "H2O"], "desc": "احتراق پاک.",
                                 "xp": 50},
    "رسوب هیدروکسید روی": {"reactants": ["ZnCl2", "NH3"], "products": ["[Zn(NH3)4](OH)2"], "desc": "حل شدن آمفوتر.",
                           "xp": 75},
    "تجزیه آمونیوم پرسولفات": {"reactants": ["(NH4)2S2O8"], "products": ["N2", "H2SO4"], "desc": "اکسیدکننده قوی.",
                               "xp": 85, "temp_min": 100},
    "اکسایش بنزن به فنل": {"reactants": ["C6H6", "O2"], "products": ["C6H5OH"], "desc": "فرایند کمیل.", "xp": 100},
    "سوختن پروتئین": {"reactants": ["protein", "O2"], "products": ["CO2", "H2O", "NOx"], "desc": "احتراق بوی مو.",
                      "xp": 60},
    "تشکیل پلی‌استایرن": {"reactants": ["C8H8"], "products": ["(C8H8)n"], "desc": "فوم یا سخت.", "xp": 95},
    "رسوب فسفات منیزیم": {"reactants": ["MgSO4", "Na2HPO4"], "products": ["MgHPO4"], "desc": "در تست کلیه.", "xp": 65},
    "تولید تیتانیوم (کرول)": {"reactants": ["TiCl4", "Mg"], "products": ["Ti", "MgCl2"], "desc": "کاهش فلز.",
                              "xp": 110},
    "خنثی‌سازی اسید لینولئیک": {"reactants": ["C18H32O2", "NaOH"], "products": ["C18H31O2Na", "H2O"],
                                "desc": "اسید چرب غیراشباع.", "xp": 60},
    "سوختن دی‌اکسید کربن (با منیزیم)": {"reactants": ["CO2", "Mg"], "products": ["MgO", "C"], "desc": "کربن آزاد.",
                                        "xp": 70},
    "رسوب کرومات نقره": {"reactants": ["AgNO3", "K2CrO4"], "products": ["Ag2CrO4"], "desc": "رسوب قرمز.", "xp": 65},
    "تجزیه سدیم پراکسید": {"reactants": ["Na2O2", "H2O"], "products": ["NaOH", "O2"], "desc": "تولید اکسیژن.",
                           "xp": 75},
    "اکسایش انیلین": {"reactants": ["C6H5NH2", "KMnO4"], "products": ["quinone"], "desc": "رنگ سیاه.", "xp": 85},
    "سوختن سلولز": {"reactants": ["(C6H10O5)n", "O2"], "products": ["CO2", "H2O"], "desc": "احتراق کاغذ.", "xp": 55},
    "تشکیل نمک طعام صنعتی": {"reactants": ["NaOH", "HCl"], "products": ["NaCl", "H2O"],
                             "desc": "خنثی‌سازی صنعتی برای تولید نمک.", "xp": 50},
    "اکسایش جیوه": {"reactants": ["Hg", "O2"], "products": ["HgO"], "desc": "تشکیل اکسید قرمز یا زرد.", "xp": 60},
    "رسوب هیدروکسید کادمیم": {"reactants": ["CdSO4", "NaOH"], "products": ["Cd(OH)2"], "desc": "رسوب سفید.", "xp": 55},
    "سوختن پروپانول": {"reactants": ["C3H7OH", "O2"], "products": ["CO2", "H2O"], "desc": "احتراق الکل پروپیلیک.",
                       "xp": 45},
    "تشکیل اسید هیدروبرومیک": {"reactants": ["H2", "Br2"], "products": ["HBr"], "desc": "ترکیب مستقیم برم.", "xp": 80},
    "تجزیه کربنات پتاسیم": {"reactants": ["K2CO3"], "products": ["K2O", "CO2"], "desc": "تجزیه گرمایی قلیایی.",
                            "xp": 60, "temp_min": 100},
    "رسوب سولفید سرب": {"reactants": ["Pb(NO3)2", "H2S"], "products": ["PbS"], "desc": "رسوب سیاه گالن.", "xp": 65},
    "تولید پتاسیم هیدروکسید": {"reactants": ["KCl"], "products": ["KOH", "Cl2", "H2"],
                               "desc": "الکترولیز سلول جیوه‌ای.", "xp": 110},
    "اکسایش پتاسیم سولفیت": {"reactants": ["K2SO3", "H2O2"], "products": ["K2SO4"], "desc": "اکسایش به سولفات.",
                             "xp": 60},
    "سوختن بوتادین": {"reactants": ["C4H6", "O2"], "products": ["CO2", "H2O"], "desc": "احتراق لاستیک مصنوعی.",
                      "xp": 55},
    "تشکیل کمپلکس آهن(III)": {"reactants": ["FeCl3", "KSCN"], "products": ["Fe(SCN)3"],
                              "desc": "رنگ قرمز خون (تست آهن).", "xp": 85},
    "رسوب فسفات باریم": {"reactants": ["Ba(NO3)2", "H3PO4"], "products": ["Ba3(PO4)2"], "desc": "رسوب سفید فسفات.",
                         "xp": 60},
    "تولید گاز دی‌اکسید نیتروژن": {"reactants": ["Pb(NO3)2"], "products": ["PbO", "NO2", "O2"],
                                   "desc": "گاز قهوه‌ای از نیترات.", "xp": 75, "temp_min": 100},
    "خنثی‌سازی اسید پروپیونیک": {"reactants": ["C2H5COOH", "NaOH"], "products": ["C2H5COONa", "H2O"],
                                 "desc": "اسید پروپیونیک.", "xp": 50},
    "سوختن ایزوبوتن": {"reactants": ["C4H8", "O2"], "products": ["CO2", "H2O"], "desc": "احتراق شاخه‌دار.", "xp": 45},
    "رسوب برمید سرب": {"reactants": ["Pb(NO3)2", "KBr"], "products": ["PbBr2"], "desc": "رسوب سفید کم‌رنگ.", "xp": 55},
    "تجزیه سدیم پرمنگنات": {"reactants": ["NaMnO4"], "products": ["Na2MnO4", "MnO2", "O2"],
                            "desc": "تجزیه مشابه پتاسیم.", "xp": 80, "temp_min": 120},
    "اکسایش پروپانول به پروپانال": {"reactants": ["C3H7OH", "PCC"], "products": ["C3H6O"], "desc": "اکسایش انتخابی.",
                                    "xp": 90},
    "سوختن پنتادین": {"reactants": ["C5H8", "O2"], "products": ["CO2", "H2O"], "desc": "احتراق دی‌ان.", "xp": 55},
    "تشکیل دی‌نیتروژن تری‌اکسید": {"reactants": ["NO", "O2"], "products": ["N2O3"], "desc": "گاز آبی در سرما.",
                                   "xp": 95},
    "رسوب هیدروکسید قلع(II)": {"reactants": ["SnCl2", "NH3"], "products": ["Sn(OH)2"], "desc": "رسوب سفید آمفوتر.",
                               "xp": 65},
    "تولید گاز هیدروژن از منیزیم": {"reactants": ["Mg", "H2O"], "products": ["MgO", "H2"], "desc": "واکنش با بخار.",
                                    "xp": 70},
    "خنثی‌سازی اسید بوتریک": {"reactants": ["C3H7COOH", "KOH"], "products": ["C3H7COOK", "H2O"],
                              "desc": "بوی کره فاسد.", "xp": 55},
    "سوختن ترپنتین": {"reactants": ["C10H16", "O2"], "products": ["CO2", "H2O"], "desc": "احتراق روغن درخت کاج.",
                      "xp": 50},
    "رسوب سولفات کلسیم": {"reactants": ["CaCl2", "H2SO4"], "products": ["CaSO4"], "desc": "رسوب گچ.", "xp": 50},
    "تجزیه هیدروژن پراکسید با خون": {"reactants": ["H2O2", "catalase"], "products": ["H2O", "O2"],
                                     "desc": "حباب در زخم.", "xp": 75},
    "اکسایش سدیم تیوسولفات": {"reactants": ["Na2S2O3", "Cl2"], "products": ["Na2SO4"], "desc": "در سفیدکننده.",
                              "xp": 70},
    "سوختن هگزانول": {"reactants": ["C6H13OH", "O2"], "products": ["CO2", "H2O"], "desc": "احتراق الکل سنگین.",
                      "xp": 50},
    "تشکیل کمپلکس مس(II)": {"reactants": ["CuSO4", "EDTA"], "products": ["Cu-EDTA"], "desc": "کمپلکس پایدار.",
                            "xp": 85},
    "رسوب کربنات باریم": {"reactants": ["BaCl2", "KHCO3"], "products": ["BaCO3"], "desc": "رسوب سنگین.", "xp": 55},
    "تولید گاز نیتریک اکسید": {"reactants": ["NaNO2", "HCl"], "products": ["NO"], "desc": "گاز بی‌رنگ.", "xp": 80},
    "خنثی‌سازی اسید والریک": {"reactants": ["C4H9COOH", "NaOH"], "products": ["C4H9COONa", "H2O"], "desc": "اسید چرب.",
                              "xp": 55},
    "سوختن نونان": {"reactants": ["C9H20", "O2"], "products": ["CO2", "H2O"], "desc": "احتراق گازوئیل.", "xp": 45},
    "رسوب فلورید استرانسیم": {"reactants": ["SrCl2", "HF"], "products": ["SrF2"], "desc": "رسوب دندان.", "xp": 50},
    "اکسایش آرسنیک(III)": {"reactants": ["As2O3", "HNO3"], "products": ["H3AsO4"], "desc": "به اسید آرسنیک.", "xp": 75},
    "سوختن دودکان": {"reactants": ["C12H26", "O2"], "products": ["CO2", "H2O"], "desc": "احتراق نفت.", "xp": 50},
    "تشکیل اسید هیپوبرومیک": {"reactants": ["Br2", "H2O"], "products": ["HBrO", "HBr"], "desc": "ضعیف‌تر از کلر.",
                              "xp": 70},
    "رسوب سولفید بیسموت": {"reactants": ["Bi(NO3)3", "H2S"], "products": ["Bi2S3"], "desc": "رسوب سیاه.", "xp": 65},
    "تولید پراکسید سدیم": {"reactants": ["Na", "O2"], "products": ["Na2O2"], "desc": "پراکسید زرد.", "xp": 85},
    "خنثی‌سازی اسید کاپروئیک": {"reactants": ["C5H11COOH", "NaOH"], "products": ["C5H11COONa", "H2O"],
                                "desc": "بوی بز.", "xp": 55},
    "سوختن سیکلوپنتان": {"reactants": ["C5H10", "O2"], "products": ["CO2", "H2O"], "desc": "احتراق حلقوی کوچک.",
                         "xp": 50},
    "رسوب کرومات استرانسیم": {"reactants": ["SrCl2", "K2Cr2O7"], "products": ["SrCrO4"], "desc": "رسوب زرد.", "xp": 60},
    "تجزیه کلسیم نیترات": {"reactants": ["Ca(NO3)2"], "products": ["CaO", "NO2", "O2"], "desc": "نیترات کلسیم.",
                           "xp": 70, "temp_min": 150},
    "اکسایش هیپوفسفیت": {"reactants": ["NaH2PO2", "HgCl2"], "products": ["Na2HPO4"], "desc": "کاهش جیوه.", "xp": 80},
    "سوختن نفتالن با کاتالیزور": {"reactants": ["C10H8", "O2"], "products": ["phthalic anhydride"],
                                  "desc": "اکسایش صنعتی.", "xp": 95},
    "تشکیل کمپلکس روی": {"reactants": ["ZnSO4", "NH3"], "products": ["[Zn(NH3)4]SO4"], "desc": "کمپلکس آمینی.",
                         "xp": 75},
    "رسوب سولفات باریم (تست)": {"reactants": ["BaCl2", "SO4^2-"], "products": ["BaSO4"], "desc": "تست سولفات.",
                                "xp": 50},
    "تولید گاز هلیوم (رادیواکتیو)": {"reactants": ["U-238"], "products": ["He", "Pb"], "desc": "پوسیدگی آلفا.",
                                     "xp": 100},
    "خنثی‌سازی اسید هپتانوئیک": {"reactants": ["C6H13COOH", "KOH"], "products": ["C6H13COOK", "H2O"],
                                 "desc": "اسید چرب.", "xp": 55},
    "سوختن فرمالین": {"reactants": ["HCHO", "O2"], "products": ["CO2", "H2O"], "desc": "احتراق محلول.", "xp": 45},
    "رسوب فسفات استرانسیم": {"reactants": ["Sr(NO3)2", "Na3PO4"], "products": ["Sr3(PO4)2"], "desc": "رسوب سفید.",
                             "xp": 55},
    "تجزیه پتاسیم پراکسید": {"reactants": ["K2O2", "H2O"], "products": ["KOH", "O2"], "desc": "پراکسید پتاسیم.",
                             "xp": 80},
    "اکسایش فسفر قرمز": {"reactants": ["P", "O2"], "products": ["P4O10"], "desc": "اکسایش آرام.", "xp": 70},
    "سوختن استالدئید": {"reactants": ["CH3CHO", "O2"], "products": ["CO2", "H2O"], "desc": "احتراق تند.", "xp": 50},
    "تشکیل پلی‌متاکریلات": {"reactants": ["methyl methacrylate"], "products": ["PMMA"], "desc": "پلکسی‌گلاس.",
                            "xp": 100},
    "رسوب کلرید سرب": {"reactants": ["Pb(NO3)2", "NaCl"], "products": ["PbCl2"], "desc": "رسوب سفید گرم‌حل.", "xp": 55},
    "تولید آهن (کاهش)": {"reactants": ["Fe2O3", "CO"], "products": ["Fe", "CO2"], "desc": "کوره بلند.", "xp": 110},
    "خنثی‌سازی اسید کاپریلیک": {"reactants": ["C7H15COOH", "NaOH"], "products": ["C7H15COONa", "H2O"],
                                "desc": "در نارگیل.", "xp": 60},
    "سوختن اتیل استات": {"reactants": ["C4H8O2", "O2"], "products": ["CO2", "H2O"], "desc": "احتراق استر.", "xp": 50},
    "رسوب هیدروکسید باریم": {"reactants": ["BaCl2", "NH3"], "products": ["Ba(OH)2"], "desc": "محلول قوی.", "xp": 50},
    "تجزیه باریم آزید": {"reactants": ["Ba(N3)2"], "products": ["Ba", "N2"], "desc": "انفجاری.", "xp": 90,
                         "temp_min": 120},
    "اکسایش منگنز به پرمنگنات": {"reactants": ["MnSO4", "PbO2", "HNO3"], "products": ["HMnO4"],
                                 "desc": "سنتز پرمنگنات.", "xp": 95},
    "سوختن پروپیونیتریل": {"reactants": ["C3H5N", "O2"], "products": ["CO2", "H2O", "NO2"], "desc": "احتراق نیتریل.",
                           "xp": 60},
    "تشکیل پلی‌تترافلورواتیلن": {"reactants": ["C2F4"], "products": ["Teflon"], "desc": "PTFE ضدچسب.", "xp": 110},
    "رسوب سولفید آرسنیک": {"reactants": ["As2O3", "H2S"], "products": ["As2S3"], "desc": "رسوب زرد.", "xp": 70},
    "تولید طلا (کاهش)": {"reactants": ["AuCl3", "SO2"], "products": ["Au"], "desc": "رسوب طلا.", "xp": 100},
    "خنثی‌سازی اسید لوریک": {"reactants": ["C11H23COOH", "NaOH"], "products": ["C11H23COONa", "H2O"],
                             "desc": "در صابون.", "xp": 60},
    "سوختن دی‌اتیل اتر": {"reactants": ["C4H10O", "O2"], "products": ["CO2", "H2O"], "desc": "انفجاری.", "xp": 55},
    "رسوب هیدروکسید استرانسیم": {"reactants": ["SrCl2", "NaOH"], "products": ["Sr(OH)2"], "desc": "باز قوی.", "xp": 50},
    "تجزیه سدیم هیپوکلریت": {"reactants": ["NaOCl"], "products": ["NaCl", "O"], "desc": "تجزیه سفیدکننده.", "xp": 70},
    "اکسایش کروم(III) به کرومات": {"reactants": ["Cr2(SO4)3", "H2O2"], "products": ["CrO4^2-"], "desc": "رنگ زرد.",
                                   "xp": 85},
    "سوختن گلیسرول": {"reactants": ["C3H8O3", "O2"], "products": ["CO2", "H2O"], "desc": "احتراق چسبناک.", "xp": 50},
    "تشکیل پلی‌اکریلونیتریل": {"reactants": ["C3H3N"], "products": ["PAN"], "desc": "الیاف مصنوعی.", "xp": 100},
    "رسوب سولفید آنتیموان(V)": {"reactants": ["SbCl5", "H2S"], "products": ["Sb2S5"], "desc": "رسوب نارنجی.", "xp": 70},
    "تولید نقره (از فیلم)": {"reactants": ["AgBr"], "products": ["Ag"], "desc": "عکاسی قدیمی.", "xp": 90},
    "خنثی‌سازی اسید میریستیک": {"reactants": ["C13H27COOH", "KOH"], "products": ["C13H27COOK", "H2O"],
                                "desc": "در جوز هندی.", "xp": 60},
    "سوختن بنزالدئید": {"reactants": ["C6H5CHO", "O2"], "products": ["CO2", "H2O"], "desc": "بوی بادام.", "xp": 55},
    "رسوب اکسالات باریم": {"reactants": ["BaCl2", "H2C2O4"], "products": ["BaC2O4"], "desc": "رسوب سفید.", "xp": 55},
    "تجزیه پتاسیم پرسولفات": {"reactants": ["K2S2O8"], "products": ["K2SO4", "O2"], "desc": "اکسیدکننده.", "xp": 80,
                              "temp_min": 90},
    "اکسایش وانادیوم": {"reactants": ["V2O5"], "products": ["color change"], "desc": "تغییر رنگ چندگانه.", "xp": 90},
    "سوختن ساکارز": {"reactants": ["C12H22O11", "O2"], "products": ["CO2", "H2O"], "desc": "کارامل به سیاه.", "xp": 50},
    "تشکیل پلی‌بوتادین": {"reactants": ["C4H6"], "products": ["rubber"], "desc": "لاستیک مصنوعی.", "xp": 105},
    "رسوب فسفومولیبدات": {"reactants": ["PO4^3-", "molybdate", "HNO3"], "products": ["(NH4)3PMo12O40"],
                          "desc": "رسوب زرد تست فسفات.", "xp": 75},
    "تولید کروم (کاهش)": {"reactants": ["Cr2O3", "Al"], "products": ["Cr", "Al2O3"], "desc": "ترمیت کروم.", "xp": 110,
                          "temp_min": 250},
    "خنثی‌سازی اسید پالمیتوئولئیک": {"reactants": ["C16H30O2", "NaOH"], "products": ["soap"], "desc": "صابون غیراشباع.",
                                     "xp": 60},
    "سوختن فنیل‌اتانول": {"reactants": ["C6H5CH2CH2OH", "O2"], "products": ["CO2", "H2O"], "desc": "بوی گل رز.",
                          "xp": 55},
    "رسوب کبالت هیدروکسید": {"reactants": ["CoSO4", "KOH"], "products": ["Co(OH)2"], "desc": "آبی به صورتی.", "xp": 60},
    "اکسایش تیتانیوم": {"reactants": ["Ti", "O2"], "products": ["TiO2"], "desc": "پوشش سفید.", "xp": 70},
    "سوختن فروکتوز": {"reactants": ["C6H12O6", "O2"], "products": ["CO2", "H2O"], "desc": "قند میوه.", "xp": 50},
    "تشکیل پلی‌کربنات": {"reactants": ["bisphenol A", "phosgene"], "products": ["PC"], "desc": "پلاستیک مقاوم.",
                         "xp": 110},
    "رسوب نیکل دی‌متیل‌گلیوکسیم": {"reactants": ["Ni2+", "DMG"], "products": ["Ni(DMG)2"],
                                   "desc": "رسوب قرمز تست نیکل.", "xp": 80},
    "تولید زیرکونیم": {"reactants": ["ZrCl4", "Mg"], "products": ["Zr"], "desc": "فرایند کرول مشابه.", "xp": 115},
    "خنثی‌سازی اسید آراشیدونیک": {"reactants": ["C20H32O2", "NaOH"], "products": ["soap"], "desc": "اسید ضروری.",
                                  "xp": 65},
    "سوختن کومن": {"reactants": ["C9H12", "O2"], "products": ["CO2", "H2O"], "desc": "احتراق ایزوپروپیل‌بنزن.",
                   "xp": 55},
    "رسوب منیزیم آمونیوم فسفات": {"reactants": ["Mg2+", "NH4+", "PO4"], "products": ["MgNH4PO4"], "desc": "تست منیزیم.",
                                  "xp": 70},
    "تجزیه اورانیوم (شکافت)": {"reactants": ["U-235", "neutron"], "products": ["fission products", "energy"],
                               "desc": "انرژی هسته‌ای.", "xp": 150},
    "تشکیل اکسید آهن (زنگ آهن)": {
        "reactants": ["Fe", "O2"],
        "products": ["Fe2O3"],
        "desc": "آهن در حضور اکسیژن و رطوبت زنگ می‌زند.",
        "xp": 50
    },
    "ترکیب هیدروژن و اکسیژن": {
        "reactants": ["H2", "O2"],
        "products": ["H2O"],
        "desc": "انفجار شدید تولید آب.",
        "xp": 80
    },
    "سوختن متان": {
        "reactants": ["CH4", "O2"],
        "products": ["CO2", "H2O"],
        "desc": "احتراق گاز طبیعی.",
        "xp": 40
    },
    "خنثی‌سازی اسید و باز": {
        "reactants": ["HCl", "NaOH"],
        "products": ["NaCl", "H2O"],
        "desc": "تولید نمک و آب.",
        "xp": 75
    },
    "تشکیل آمونیاک (هابر)": {
        "reactants": ["N2", "H2"],
        "products": ["NH3"],
        "desc": "سنتز صنعتی آمونیاک.",
        "xp": 120
    },
    "تجزیه آب (الکترولیز)": {
        "reactants": ["H2O"],
        "products": ["H2", "O2"],
        "desc": "تجزیه الکتریکی آب.",
        "xp": 90
    },
    "رسوب نقره کلرید": {
        "reactants": ["AgNO3", "NaCl"],
        "products": ["AgCl", "NaNO3"],
        "desc": "رسوب سفید شیرمانند.",
        "xp": 60
    },
    "باران طلایی (یدید سرب)": {
        "reactants": ["Pb(NO3)2", "KI"],
        "products": ["PbI2"],
        "desc": "رسوب زرد طلایی زیبا.",
        "xp": 100
    },
    "دود سفید نشادر": {
        "reactants": ["NH3", "HCl"],
        "products": ["NH4Cl"],
        "desc": "تشکیل دود سفید آمونیوم کلرید.",
        "xp": 65
    },
    "سوختن منیزیم": {
        "reactants": ["Mg", "O2"],
        "products": ["MgO"],
        "desc": "نور شدید سفید.",
        "xp": 70
    },
    "تولید دی‌اکسید کربن": {
        "reactants": ["CaCO3", "HCl"],
        "products": ["CaCl2", "CO2", "H2O"],
        "desc": "حباب گاز از سنگ آهک.",
        "xp": 45
    },
    "محلول آبی سولفات مس": {
        "reactants": ["CuSO4", "H2O"],
        "products": ["CuSO4(aq)"],
        "desc": "رنگ آبی شفاف.",
        "xp": 20
    },
    "اکسایش گلوکز": {
        "reactants": ["C6H12O6", "O2"],
        "products": ["CO2", "H2O"],
        "desc": "تنفس سلولی.",
        "xp": 110
    },
    "ترکیب سدیم و کلر": {
        "reactants": ["Na", "Cl2"],
        "products": ["NaCl"],
        "desc": "واکنش انفجاری نمک طعام.",
        "xp": 95
    },
    "رسوب هیدروکسید آهن": {
        "reactants": ["FeCl3", "NaOH"],
        "products": ["Fe(OH)3"],
        "desc": "رسوب قهوه‌ای ژله‌ای.",
        "xp": 55
    },
    "تولید گاز هیدروژن": {
        "reactants": ["Zn", "HCl"],
        "products": ["ZnCl2", "H2"],
        "desc": "حباب گاز هیدروژن.",
        "xp": 50
    },
    "سوختن اتانول": {
        "reactants": ["C2H5OH", "O2"],
        "products": ["CO2", "H2O"],
        "desc": "احتراق الکل.",
        "xp": 60
    },
    "تشکیل اسید سولفوریک": {
        "reactants": ["SO3", "H2O"],
        "products": ["H2SO4"],
        "desc": "واکنش گرمازا شدید.",
        "xp": 85
    },
    "رسوب باریم سولفات": {
        "reactants": ["BaCl2", "Na2SO4"],
        "products": ["BaSO4"],
        "desc": "رسوب سفید سنگین.",
        "xp": 40
    },
    "آتشفشان آمونیوم دی‌کرومات": {
        "reactants": ["(NH4)2Cr2O7"],
        "products": ["Cr2O3", "N2", "H2O"],
        "desc": "تجزیه به شکل کوه آتشفشان.",
        "xp": 200
    },
    "تولید اکسیژن (پراکسید)": {
        "reactants": ["H2O2"],
        "products": ["H2O", "O2"],
        "desc": "تجزیه کاتالیزی پراکسید هیدروژن.",
        "xp": 70
    },
    "رسوب کرومات سرب": {
        "reactants": ["Pb(NO3)2", "K2CrO4"],
        "products": ["PbCrO4"],
        "desc": "رسوب زرد کروم.",
        "xp": 80
    },
    "خنثی‌سازی با بی‌کربنات": {
        "reactants": ["HCl", "NaHCO3"],
        "products": ["NaCl", "CO2", "H2O"],
        "desc": "حباب دی‌اکسید کربن.",
        "xp": 55
    },
    "سوختن پروپان": {
        "reactants": ["C3H8", "O2"],
        "products": ["CO2", "H2O"],
        "desc": "احتراق گاز آشپزخانه.",
        "xp": 45
    },
    "تشکیل نیترات آمونیوم": {
        "reactants": ["NH3", "HNO3"],
        "products": ["NH4NO3"],
        "desc": "واکنش خنثی‌سازی کود.",
        "xp": 65
    },
    "رسوب فسفات کلسیم": {
        "reactants": ["CaCl2", "Na3PO4"],
        "products": ["Ca3(PO4)2"],
        "desc": "رسوب سفید استخوان.",
        "xp": 50
    },
    "تولید گاز آمونیاک": {
        "reactants": ["NH4Cl", "NaOH"],
        "products": ["NH3", "NaCl", "H2O"],
        "desc": "بوی تند آمونیاک.",
        "xp": 60
    },
    "اکسایش الکل به آلدهید": {
        "reactants": ["C2H5OH", "O2"],
        "products": ["CH3CHO", "H2O"],
        "desc": "با کاتالیزور مس.",
        "xp": 90
    },
    "رسوب ید": {
        "reactants": ["KI", "Pb(NO3)2"],
        "products": ["PbI2"],
        "desc": "رسوب زرد یدید سرب.",
        "xp": 70
    },
    "سوختن گوگرد": {
        "reactants": ["S", "O2"],
        "products": ["SO2"],
        "desc": "بوی تند دی‌اکسید گوگرد.",
        "xp": 55
    },
    "ترکیب آهن و گوگرد": {
        "reactants": ["Fe", "S"],
        "products": ["FeS"],
        "desc": "واکنش گرمازا سولفید آهن.",
        "xp": 80
    },
    "تجزیه کلرات پتاسیم": {
        "reactants": ["KClO3"],
        "products": ["KCl", "O2"],
        "desc": "تولید اکسیژن.",
        "xp": 75
    },
    "رسوب هیدروکسید آلومینیوم": {
        "reactants": ["AlCl3", "NaOH"],
        "products": ["Al(OH)3"],
        "desc": "رسوب سفید ژله‌ای.",
        "xp": 60
    },
    "تولید گاز نیتروژن": {
        "reactants": ["NH4NO2"],
        "products": ["N2", "H2O"],
        "desc": "تجزیه نیترات آمونیوم.",
        "xp": 85
    },
    "سوختن فسفر سفید": {
        "reactants": ["P4", "O2"],
        "products": ["P4O10"],
        "desc": "نور شدید و دود.",
        "xp": 100
    },
    "تشکیل اسید نیتریک": {
        "reactants": ["NO2", "H2O", "O2"],
        "products": ["HNO3"],
        "desc": "اکسایش دی‌اکسید نیتروژن.",
        "xp": 110
    },
    "رسوب سیانید نقره": {
        "reactants": ["AgNO3", "KCN"],
        "products": ["AgCN"],
        "desc": "رسوب سفید (خطرناک).",
        "xp": 70
    },
    "خنثی‌سازی سرکه و جوش شیرین": {
        "reactants": ["CH3COOH", "NaHCO3"],
        "products": ["CH3COONa", "CO2", "H2O"],
        "desc": "حباب برای آتشفشان خانگی.",
        "xp": 40
    },
    "تولید هیدروکسید مس": {
        "reactants": ["CuSO4", "NaOH"],
        "products": ["Cu(OH)2"],
        "desc": "رسوب آبی روشن.",
        "xp": 55
    },
    "سوختن هیدروژن": {
        "reactants": ["H2", "O2"],
        "products": ["H2O"],
        "desc": "انفجار با صدای پوپ.",
        "xp": 65
    },
    "ترکیب کلسیم و آب": {
        "reactants": ["Ca", "H2O"],
        "products": ["Ca(OH)2", "H2"],
        "desc": "تولید گاز هیدروژن.",
        "xp": 70
    },
    "رسوب کربنات کلسیم": {
        "reactants": ["CaCl2", "Na2CO3"],
        "products": ["CaCO3"],
        "desc": "رسوب سفید سنگ آهک.",
        "xp": 45
    },
    "تجزیه پرمنگنات پتاسیم": {
        "reactants": ["KMnO4"],
        "products": ["K2MnO4", "MnO2", "O2"],
        "desc": "تولید اکسیژن بنفش.",
        "xp": 95
    },
    "اکسایش یدید به ید": {
        "reactants": ["KI", "H2O2"],
        "products": ["I2"],
        "desc": "رنگ قهوه‌ای ید آزاد.",
        "xp": 80
    },
    "سوختن استیلن": {
        "reactants": ["C2H2", "O2"],
        "products": ["CO2", "H2O"],
        "desc": "شعله داغ جوشکاری.",
        "xp": 75
    },
    "تشکیل کلرید آهن(III)": {
        "reactants": ["Fe", "Cl2"],
        "products": ["FeCl3"],
        "desc": "واکنش گرمازا کلر.",
        "xp": 90
    },
    "رسوب سولفید روی": {
        "reactants": ["ZnSO4", "H2S"],
        "products": ["ZnS"],
        "desc": "رسوب سفید سولفید.",
        "xp": 60
    },
    "تولید گاز استیلن": {
        "reactants": ["CaC2", "H2O"],
        "products": ["C2H2"],
        "desc": "بوی سیر استیلن.",
        "xp": 70
    },
    "خنثی‌سازی اسید سیتریک": {
        "reactants": ["C6H8O7", "NaOH"],
        "products": ["Na3C6H5O7", "H2O"],
        "desc": "واکنش آب لیمو و باز.",
        "xp": 50
    },
    "سوختن بوتان": {
        "reactants": ["C4H10", "O2"],
        "products": ["CO2", "H2O"],
        "desc": "احتراق فندک.",
        "xp": 40
    },
    "رسوب اکسالات کلسیم": {
        "reactants": ["CaCl2", "Na2C2O4"],
        "products": ["CaC2O4"],
        "desc": "رسوب سفید سنگ کلیه.",
        "xp": 65
    },
    "تجزیه نیترات سرب": {
        "reactants": ["Pb(NO3)2"],
        "products": ["PbO", "NO2", "O2"],
        "desc": "گاز قهوه‌ای سمی.",
        "xp": 85
    },
    "اکسایش مس با نیتریک اسید": {
        "reactants": ["Cu", "HNO3"],
        "products": ["Cu(NO3)2", "NO2"],
        "desc": "گاز قهوه‌ای و محلول آبی.",
        "xp": 95
    },
    "سوختن نفتالن": {
        "reactants": ["C10H8", "O2"],
        "products": ["CO2", "H2O"],
        "desc": "شعله دودزا.",
        "xp": 55
    },
    "تشکیل پلیمر نایلون": {
        "reactants": ["Hexamethylenediamine", "Adipoyl chloride"],
        "products": ["Nylon"],
        "desc": "رشته نایلون در مرز دو فاز.",
        "xp": 120
    },
    "رسوب برمید نقره": {
        "reactants": ["AgNO3", "NaBr"],
        "products": ["AgBr"],
        "desc": "رسوب کرمی رنگ.",
        "xp": 50
    },
    "تولید گاز فسفین": {
        "reactants": ["Ca3P2", "H2O"],
        "products": ["PH3"],
        "desc": "گاز سمی خوداشتعال.",
        "xp": 100
    },
    "خنثی‌سازی با کربنات": {
        "reactants": ["H2SO4", "Na2CO3"],
        "products": ["Na2SO4", "CO2", "H2O"],
        "desc": "حباب شدید.",
        "xp": 45
    },
    "سوختن پنتاان": {
        "reactants": ["C5H12", "O2"],
        "products": ["CO2", "H2O"],
        "desc": "احتراق بنزین.",
        "xp": 40
    },
    "رسوب هیدروکسید نیکل": {
        "reactants": ["NiSO4", "NaOH"],
        "products": ["Ni(OH)2"],
        "desc": "رسوب سبز روشن.",
        "xp": 60
    },
    "تجزیه آزید سدیم": {
        "reactants": ["NaN3"],
        "products": ["Na", "N2"],
        "desc": "تولید گاز ایربگ.",
        "xp": 90
    },
    "اکسایش سولفیت": {
        "reactants": ["Na2SO3", "O2"],
        "products": ["Na2SO4"],
        "desc": "اکسایش هوا به سولفات.",
        "xp": 70
    },
    "سوختن هگزان": {
        "reactants": ["C6H14", "O2"],
        "products": ["CO2", "H2O"],
        "desc": "احتراق سوخت.",
        "xp": 40
    },
    "تشکیل سولفید هیدروژن": {
        "reactants": ["FeS", "HCl"],
        "products": ["H2S"],
        "desc": "بوی تخم‌گندیده.",
        "xp": 65
    },
    "رسوب فلورید کلسیم": {
        "reactants": ["CaCl2", "NaF"],
        "products": ["CaF2"],
        "desc": "رسوب سفید دندان.",
        "xp": 50
    },
    "تولید کلر (الکترولیز نمک)": {
        "reactants": ["NaCl(aq)"],
        "products": ["Cl2", "H2", "NaOH"],
        "desc": "الکترولیز آب نمک.",
        "xp": 100
    },
    "خنثی‌سازی فسفریک اسید": {
        "reactants": ["H3PO4", "NaOH"],
        "products": ["Na3PO4", "H2O"],
        "desc": "تولید فسفات.",
        "xp": 55
    },
    "سوختن اکتان": {
        "reactants": ["C8H18", "O2"],
        "products": ["CO2", "H2O"],
        "desc": "احتراق بنزین اصلی.",
        "xp": 45
    },
    "رسوب تیوسیانات آهن": {
        "reactants": ["FeCl3", "KSCN"],
        "products": ["Fe(SCN)3"],
        "desc": "رنگ قرمز خون.",
        "xp": 85
    },
    "تجزیه هیدروژن پراکسید با کاتالیزور": {
        "reactants": ["H2O2", "MnO2"],
        "products": ["H2O", "O2"],
        "desc": "حباب شدید اکسیژن.",
        "xp": 60
    },
    "اکسایش منگنز(II)": {
        "reactants": ["MnSO4", "H2O2"],
        "products": ["MnO2"],
        "desc": "رسوب قهوه‌ای دی‌اکسید منگنز.",
        "xp": 70
    },
    "سوختن بنزن": {
        "reactants": ["C6H6", "O2"],
        "products": ["CO2", "H2O"],
        "desc": "شعله دودزا سیاه.",
        "xp": 55
    },
    "تشکیل سیلیکات ژل": {
        "reactants": ["Na2SiO3", "HCl"],
        "products": ["SiO2 gel"],
        "desc": "ژل سیلیکا باغبانی.",
        "xp": 75
    },
    "رسوب کبالت سولفید": {
        "reactants": ["CoCl2", "H2S"],
        "products": ["CoS"],
        "desc": "رسوب سیاه.",
        "xp": 60
    },
    "تولید گاز نیتریک اکسید": {
        "reactants": ["Cu", "HNO3 dilute"],
        "products": ["Cu(NO3)2", "NO"],
        "desc": "گاز بی‌رنگ به قهوه‌ای.",
        "xp": 80
    },
    "خنثی‌سازی بوریک اسید": {
        "reactants": ["H3BO3", "NaOH"],
        "products": ["Na3BO3", "H2O"],
        "desc": "واکنش ضعیف.",
        "xp": 50
    },
    "سوختن تولوئن": {
        "reactants": ["C7H8", "O2"],
        "products": ["CO2", "H2O"],
        "desc": "احتراق دودزا.",
        "xp": 45
    },
    "رسوب کروم هیدروکسید": {
        "reactants": ["CrCl3", "NaOH"],
        "products": ["Cr(OH)3"],
        "desc": "رسوب سبز خاکستری.",
        "xp": 65
    },
    "تجزیه آمونیوم نیترات": {
        "reactants": ["Na2SO4"],
        "products": ["N2O", "H2O"],
        "desc": "گاز خنده (گرم).",
        "xp": 90
    },
    "اکسایش برمید": {
        "reactants": ["NaBr", "Cl2"],
        "products": ["Br2"],
        "desc": "رنگ نارنجی برم آزاد.",
        "xp": 75
    },
    "سوختن زایلن": {
        "reactants": ["C8H10", "O2"],
        "products": ["CO2", "H2O"],
        "desc": "احتراق آروماتیک.",
        "xp": 50
    },
    "تشکیل کمپلکس آبی مس": {
        "reactants": ["CuSO4", "NH3"],
        "products": ["[Cu(NH3)4]SO4"],
        "desc": "رنگ آبی تیره.",
        "xp": 80
    },
    "رسوب منگنز سولفید": {
        "reactants": ["MnSO4", "H2S"],
        "products": ["MnS"],
        "desc": "رسوب صورتی گوشتی.",
        "xp": 60
    },
    "تولید دی‌نیتروژن اکسید": {
        "reactants": ["NH4NO3 heat"],
        "products": ["N2O", "H2O"],
        "desc": "گاز خنده.",
        "xp": 70
    },
    "خنثی‌سازی استیک اسید": {
        "reactants": ["CH3COOH", "KOH"],
        "products": ["CH3COOK", "H2O"],
        "desc": "تولید استات پتاسیم.",
        "xp": 45
    },
    "سوختن استایرن": {
        "reactants": ["C8H8", "O2"],
        "products": ["CO2", "H2O"],
        "desc": "احتراق پلی‌استایرن.",
        "xp": 50
    },
    "رسوب کادمیم سولفید": {
        "reactants": ["CdSO4", "H2S"],
        "products": ["CdS"],
        "desc": "رسوب زرد روشن.",
        "xp": 65
    },
    "تجزیه پتاسیم کلرات با کاتالیزور": {
        "reactants": ["KClO3", "MnO2"],
        "products": ["KCl", "O2"],
        "desc": "تولید سریع اکسیژن.",
        "xp": 75
    },
    "اکسایش آرسنیک": {
        "reactants": ["As", "O2"],
        "products": ["As2O3"],
        "desc": "سمی سفید.",
        "xp": 80
    },
    "سوختن فنل": {
        "reactants": ["C6H5OH", "O2"],
        "products": ["CO2", "H2O"],
        "desc": "احتراق فنولی.",
        "xp": 55
    },
    "تشکیل کمپلکس آهن تیوسیانات": {
        "reactants": ["Fe3", "SCN"],
        "products": ["[FeSCN]2+"],
        "desc": "رنگ قرمز شدید.",
        "xp": 85
    },
    "رسوب استرانسیم سولفات": {
        "reactants": ["SrCl2", "Na2SO4"],
        "products": ["SrSO4"],
        "desc": "رسوب سفید.",
        "xp": 40
    },
    "تولید گاز متان (واکنش گرینیارد شبیه)": {
        "reactants": ["CH3I", "Mg"],
        "products": ["CH4 after hydrolysis"],
        "desc": "تولید متان ساده.",
        "xp": 90
    },
    "خنثی‌سازی لاکتیک اسید": {
        "reactants": ["C3H6O3", "NaOH"],
        "products": ["NaC3H5O3", "H2O"],
        "desc": "اسید شیر.",
        "xp": 50
    },
    "سوختن انیلین": {
        "reactants": ["C6H5NH2", "O2"],
        "products": ["CO2", "H2O", "N2"],
        "desc": "احتراق آمینی.",
        "xp": 60
    },
    "رسوب باریم کربنات": {
        "reactants": ["BaCl2", "Na2CO3"],
        "products": ["BaCO3"],
        "desc": "رسوب سفید سنگین.",
        "xp": 45
    },
    "تجزیه سدیم بی‌کربنات": {
        "reactants": ["NaHCO3 heat"],
        "products": ["Na2CO3", "CO2", "H2O"],
        "desc": "جوش شیرین در پخت.",
        "xp": 55
    },
    "اکسایش قلع": {
        "reactants": ["Sn", "HNO3"],
        "products": ["SnO2"],
        "desc": "تشکیل متااستانیک اسید.",
        "xp": 70
    },
    "سوختن پیریدین": {
        "reactants": ["C5H5N", "O2"],
        "products": ["CO2", "H2O", "NO2"],
        "desc": "احتراق نیتروژنی.",
        "xp": 65
    },
    "تشکیل اسید استیک (اکسایش اتانول)": {
        "reactants": ["C2H5OH", "KMnO4"],
        "products": ["CH3COOH"],
        "desc": "سرکه از الکل.",
        "xp": 80
    },
    "رسوب روی کربنات": {
        "reactants": ["ZnSO4", "Na2CO3"],
        "products": ["ZnCO3"],
        "desc": "رسوب سفید پایه.",
        "xp": 50
    },
    "تولید گاز کربنیل کلرید (فوسژن خطرناک)": {
        "reactants": ["CO", "Cl2"],
        "products": ["COCl2"],
        "desc": "گاز سمی (فقط تئوری).",
        "xp": 120
    },
    "خنثی‌سازی تارتاریک اسید": {
        "reactants": ["C4H6O6", "NaOH"],
        "products": ["Na2C4H4O6", "H2O"],
        "desc": "اسید ترتار.",
        "xp": 55
    },
    "سوختن نفتالین": {
        "reactants": ["C10H8", "O2"],
        "products": ["CO2", "H2O"],
        "desc": "دود سیاه ضدبید.",
        "xp": 60
    },
    "تولید گاز اکسیژن از گیاهان": {
        "reactants": ["CO2", "H2O", "light"],
        "products": ["C6H12O6", "O2"],
        "desc": "فتوسنتز در گیاهان سبز.",
        "xp": 100
    },
    "اکسایش آهن(II) به آهن(III)": {
        "reactants": ["FeSO4", "O2"],
        "products": ["Fe2(SO4)3"],
        "desc": "اکسایش در هوا.",
        "xp": 60
    },
    "رسوب هیدروکسید منیزیم": {
        "reactants": ["MgCl2", "NaOH"],
        "products": ["Mg(OH)2"],
        "desc": "رسوب سفید شیر آهک.",
        "xp": 50
    },
    "سوختن متیل الکل": {
        "reactants": ["CH3OH", "O2"],
        "products": ["CO2", "H2O"],
        "desc": "احتراق متانول.",
        "xp": 45
    },
    "تشکیل اسید کلریدریک": {
        "reactants": ["H2", "Cl2"],
        "products": ["HCl"],
        "desc": "ترکیب مستقیم هالوژن.",
        "xp": 80
    },
    "تجزیه کربنات سدیم": {
        "reactants": ["Na2CO3 heat"],
        "products": ["Na2O", "CO2"],
        "desc": "تجزیه گرمایی.",
        "xp": 55
    },
    "رسوب سولفید مس": {
        "reactants": ["CuSO4", "H2S"],
        "products": ["CuS"],
        "desc": "رسوب سیاه.",
        "xp": 65
    },
    "تولید سدیم هیدروکسید (الکترولیز)": {
        "reactants": ["NaCl(aq)"],
        "products": ["NaOH", "Cl2", "H2"],
        "desc": "فرایند کلر-آلکالی.",
        "xp": 110
    },
    "اکسایش سدیم سولفیت": {
        "reactants": ["Na2SO3", "H2O2"],
        "products": ["Na2SO4"],
        "desc": "اکسایش ملایم.",
        "xp": 60
    },
    "سوختن اتیلن": {
        "reactants": ["C2H4", "O2"],
        "products": ["CO2", "H2O"],
        "desc": "احتراق الفین.",
        "xp": 50
    },
    "تشکیل کمپلکس کبالت": {
        "reactants": ["CoCl2", "NH3"],
        "products": ["[Co(NH3)6]Cl3"],
        "desc": "رنگ تغییر از صورتی به زرد.",
        "xp": 90
    },
    "رسوب فسفات نقره": {
        "reactants": ["AgNO3", "Na3PO4"],
        "products": ["Ag3PO4"],
        "desc": "رسوب زرد.",
        "xp": 70
    },
    "تولید گاز دی‌اکسید گوگرد": {
        "reactants": ["Cu", "H2SO4 conc"],
        "products": ["CuSO4", "SO2"],
        "desc": "واکنش مس با اسید سولفوریک.",
        "xp": 75
    },
    "خنثی‌سازی اسید فرمیک": {
        "reactants": ["HCOOH", "NaOH"],
        "products": ["HCOONa", "H2O"],
        "desc": "اسید مورچه.",
        "xp": 50
    },
    "سوختن پروپیلن": {
        "reactants": ["C3H6", "O2"],
        "products": ["CO2", "H2O"],
        "desc": "احتراق گاز پالایشگاهی.",
        "xp": 45
    },
    "رسوب یدید نقره": {
        "reactants": ["AgNO3", "KI"],
        "products": ["AgI"],
        "desc": "رسوب زرد کم‌رنگ.",
        "xp": 60
    },
    "تجزیه پتاسیم پرمنگنات با حرارت": {
        "reactants": ["KMnO4 heat"],
        "products": ["K2MnO4", "MnO2", "O2"],
        "desc": "رنگ بنفش ناپدید.",
        "xp": 85
    },
    "اکسایش اتانول به استیک اسید": {
        "reactants": ["C2H5OH", "O2", "catalyst"],
        "products": ["CH3COOH"],
        "desc": "تولید سرکه.",
        "xp": 95
    },
    "سوختن بوتن": {
        "reactants": ["C4H8", "O2"],
        "products": ["CO2", "H2O"],
        "desc": "احتراق بوتادین بخشی.",
        "xp": 50
    },
    "تشکیل هیدرازین": {
        "reactants": ["NH3", "NaOCl"],
        "products": ["N2H4"],
        "desc": "واکنش راشینگ (ساده).",
        "xp": 100
    },
    "رسوب اکسید قلع": {
        "reactants": ["SnCl2", "NaOH"],
        "products": ["Sn(OH)2"],
        "desc": "رسوب سفید آمفوتر.",
        "xp": 65
    },
    "تولید گاز هیدروژن از آلومینیوم": {
        "reactants": ["Al", "NaOH"],
        "products": ["NaAlO2", "H2"],
        "desc": "حباب شدید.",
        "xp": 70
    },
    "خنثی‌سازی اسید اگزالیک": {
        "reactants": ["H2C2O4", "NaOH"],
        "products": ["Na2C2O4", "H2O"],
        "desc": "اسید اگزالات.",
        "xp": 55
    },
    "سوختن ایزوپروپیل الکل": {
        "reactants": ["C3H7OH", "O2"],
        "products": ["CO2", "H2O"],
        "desc": "احتراق ضدعفونی‌کننده.",
        "xp": 45
    },
    "رسوب سولفات سرب": {
        "reactants": ["Pb(NO3)2", "H2SO4"],
        "products": ["PbSO4"],
        "desc": "رسوب سفید سنگین.",
        "xp": 60
    },
    "تجزیه هیدرازین": {
        "reactants": ["N2H4"],
        "products": ["N2", "H2"],
        "desc": "تجزیه سوخت موشک.",
        "xp": 90
    },
    "اکسایش سولفید به سولفات": {
        "reactants": ["Na2S", "O2"],
        "products": ["Na2SO4"],
        "desc": "اکسایش هوا.",
        "xp": 65
    },
    "سوختن پنتیل الکل": {
        "reactants": ["C5H11OH", "O2"],
        "products": ["CO2", "H2O"],
        "desc": "احتراق الکل بالاتر.",
        "xp": 50
    },
    "تشکیل کمپلکس نیکل": {
        "reactants": ["NiSO4", "NH3"],
        "products": ["[Ni(NH3)6]SO4"],
        "desc": "رنگ آبی به سبز.",
        "xp": 80
    },
    "رسوب کربنات نقره": {
        "reactants": ["AgNO3", "Na2CO3"],
        "products": ["Ag2CO3"],
        "desc": "رسوب زرد کم‌رنگ.",
        "xp": 60
    },
    "تولید گاز نیتروژن دی‌اکسید": {
        "reactants": ["Cu", "HNO3 conc"],
        "products": ["Cu(NO2)2", "NO2"],
        "desc": "گاز قهوه‌ای سمی.",
        "xp": 85
    },
    "خنثی‌سازی اسید مالئیک": {
        "reactants": ["C4H4O4", "NaOH"],
        "products": ["Na2C4H2O4", "H2O"],
        "desc": "اسید سیس.",
        "xp": 55
    },
    "سوختن هپتان": {
        "reactants": ["C7H16", "O2"],
        "products": ["CO2", "H2O"],
        "desc": "احتراق سوخت دیزل.",
        "xp": 45
    },
    "رسوب فلورید باریم": {
        "reactants": ["BaCl2", "NaF"],
        "products": ["BaF2"],
        "desc": "رسوب سفید.",
        "xp": 50
    },
    "تجزیه آمونیوم بی‌کرومات": {
        "reactants": ["(NH4)2Cr2O7 heat"],
        "products": ["Cr2O3", "N2", "H2O"],
        "desc": "آتشفشان سبز.",
        "xp": 120
    },
    "اکسایش فسفیت": {
        "reactants": ["Na3PO3", "I2"],
        "products": ["Na3PO4"],
        "desc": "اکسایش ید.",
        "xp": 70
    },
    "سوختن دکان": {
        "reactants": ["C10H22", "O2"],
        "products": ["CO2", "H2O"],
        "desc": "احتراق نفت سفید.",
        "xp": 50
    },
    "تشکیل اسید هیپوکلروس": {
        "reactants": ["Cl2", "H2O"],
        "products": ["HClO", "HCl"],
        "desc": "آب ژاول.",
        "xp": 75
    },
    "رسوب سولفید کادمیم": {
        "reactants": ["Cd(NO3)2", "Na2S"],
        "products": ["CdS"],
        "desc": "رسوب زرد.",
        "xp": 65
    },
    "تولید هیدروژن پراکسید": {
        "reactants": ["BaO2", "H2SO4"],
        "products": ["BaSO4", "H2O2"],
        "desc": "روش قدیمی.",
        "xp": 80
    },
    "خنثی‌سازی اسید ساکسینیک": {
        "reactants": ["C4H6O4", "KOH"],
        "products": ["K2C4H4O4", "H2O"],
        "desc": "اسید کهربایی.",
        "xp": 55
    },
    "سوختن سیکلوهگزان": {
        "reactants": ["C6H12", "O2"],
        "products": ["CO2", "H2O"],
        "desc": "احتراق حلقوی.",
        "xp": 50
    },
    "رسوب کرومات باریم": {
        "reactants": ["BaCl2", "K2CrO4"],
        "products": ["BaCrO4"],
        "desc": "رسوب زرد.",
        "xp": 60
    },
    "تجزیه پتاسیم نیترات": {
        "reactants": ["KNO3 heat"],
        "products": ["KNO2", "O2"],
        "desc": "تولید اکسیژن.",
        "xp": 70
    },
    "اکسایش تیو سولفات": {
        "reactants": ["Na2S2O3", "I2"],
        "products": ["Na2S4O6"],
        "desc": "واکنش ساعت ید.",
        "xp": 85
    },
    "سوختن تولوئن با اکسیژن ناکافی": {
        "reactants": ["C7H8", "O2 limited"],
        "products": ["C", "CO", "H2O"],
        "desc": "دود سیاه.",
        "xp": 55
    },
    "تشکیل کمپلکس آهن(II)": {
        "reactants": ["FeSO4", "KCN"],
        "products": ["K4[Fe(CN)6]"],
        "desc": "فروسیانید.",
        "xp": 90
    },
    "رسوب سولفات استرانسیم": {
        "reactants": ["Sr(NO3)2", "H2SO4"],
        "products": ["SrSO4"],
        "desc": "رسوب سفید.",
        "xp": 50
    },
    "تولید گاز آرگون (جدا سازی هوا)": {
        "reactants": ["air"],
        "products": ["Ar", "N2", "O2"],
        "desc": "تقطیر جزء به جزء.",
        "xp": 100
    },
    "خنثی‌سازی اسید بنزوییک": {
        "reactants": ["C6H5COOH", "NaOH"],
        "products": ["C6H5COONa", "H2O"],
        "desc": "بنزن کربوکسیلیک.",
        "xp": 60
    },
    "سوختن استون": {
        "reactants": ["CH3COCH3", "O2"],
        "products": ["CO2", "H2O"],
        "desc": "احتراق کتون.",
        "xp": 45
    },
    "رسوب فسفات باریم": {
        "reactants": ["BaCl2", "Na3PO4"],
        "products": ["Ba3(PO4)2"],
        "desc": "رسوب سفید.",
        "xp": 55
    },
    "تجزیه سدیم آزید": {
        "reactants": ["NaN3 heat"],
        "products": ["Na", "N2"],
        "desc": "ایربگ خودرو.",
        "xp": 85
    },
    "اکسایش هیدرازین": {
        "reactants": ["N2H4", "O2"],
        "products": ["N2", "H2O"],
        "desc": "احتراق سوخت موشک.",
        "xp": 95
    },
    "سوختن فرمالدئید": {
        "reactants": ["HCHO", "O2"],
        "products": ["CO2", "H2O"],
        "desc": "احتراق آلدهید.",
        "xp": 50
    },
    "تشکیل پلی‌اتیلن": {
        "reactants": ["C2H4", "catalyst"],
        "products": ["(C2H4)n"],
        "desc": "پلیمریزاسیون.",
        "xp": 110
    },
    "رسوب کلرید باریم": {
        "reactants": ["Ba(NO3)2", "HCl"],
        "products": ["BaCl2"],
        "desc": "محلول باقی می‌ماند (قابل حل).",
        "xp": 40
    },
    "تولید کلسیم کاربید": {
        "reactants": ["CaO", "C"],
        "products": ["CaC2"],
        "desc": "در کوره الکتریکی.",
        "xp": 90
    },
    "خنثی‌سازی اسید سالیسیلیک": {
        "reactants": ["C6H4(OH)COOH", "NaOH"],
        "products": ["C6H4(OH)COONa", "H2O"],
        "desc": "آسپیرین پایه.",
        "xp": 60
    },
    "سوختن گلوکز": {
        "reactants": ["C6H12O6", "O2"],
        "products": ["CO2", "H2O"],
        "desc": "احتراق قند.",
        "xp": 55
    },
    "رسوب سولفید آهن(II)": {
        "reactants": ["FeSO4", "Na2S"],
        "products": ["FeS"],
        "desc": "رسوب سیاه.",
        "xp": 60
    },
    "تجزیه باریم پراکسید": {
        "reactants": ["BaO2 heat"],
        "products": ["BaO", "O2"],
        "desc": "تولید اکسیژن قدیمی.",
        "xp": 75
    },
    "اکسایش منیزیم با دی‌اکسید کربن": {
        "reactants": ["Mg", "CO2"],
        "products": ["MgO", "C"],
        "desc": "سوختن در CO2.",
        "xp": 80
    },
    "سوختن پارافین": {
        "reactants": ["C20H42", "O2"],
        "products": ["CO2", "H2O"],
        "desc": "احتراق شمع.",
        "xp": 50
    },
    "تشکیل اسید فسفریک": {
        "reactants": ["P4O10", "H2O"],
        "products": ["H3PO4"],
        "desc": "واکنش گرمازا.",
        "xp": 70
    },
    "رسوب کربنات استرانسیم": {
        "reactants": ["SrCl2", "Na2CO3"],
        "products": ["SrCO3"],
        "desc": "رسوب سفید.",
        "xp": 55
    },
    "تولید گاز سیلان": {
        "reactants": ["Mg2Si", "HCl"],
        "products": ["SiH4"],
        "desc": "گاز خوداشتعال.",
        "xp": 100
    },
    "خنثی‌سازی اسید پالمیتیک": {
        "reactants": ["C16H32O2", "NaOH"],
        "products": ["C16H31O2Na", "H2O"],
        "desc": "صابون‌سازی.",
        "xp": 65
    },
    "سوختن دی‌متیل اتر": {
        "reactants": ["C2H6O", "O2"],
        "products": ["CO2", "H2O"],
        "desc": "احتراق اتر.",
        "xp": 50
    },
    "رسوب هیدروکسید کروم": {
        "reactants": ["Cr2(SO4)3", "NH3"],
        "products": ["Cr(OH)3"],
        "desc": "رسوب آمفوتر.",
        "xp": 70
    },
    "تجزیه کلسیم هیپوکلریت": {
        "reactants": ["Ca(OCl)2"],
        "products": ["CaCl2", "O2"],
        "desc": "پودر سفیدکننده.",
        "xp": 75
    },
    "اکسایش گزانتات": {
        "reactants": ["xanthate", "O2"],
        "products": ["dixanthogen"],
        "desc": "در فلوتاسیون.",
        "xp": 85
    },
    "سوختن کربوهیدرات": {
        "reactants": ["starch", "O2"],
        "products": ["CO2", "H2O"],
        "desc": "احتراق نشاسته.",
        "xp": 55
    },
    "تشکیل پلی‌پروپیلن": {
        "reactants": ["C3H6", "Ziegler catalyst"],
        "products": ["(C3H6)n"],
        "desc": "پلیمریزاسیون استریو.",
        "xp": 110
    },
    "رسوب سولفید قلع": {
        "reactants": ["SnCl2", "H2S"],
        "products": ["SnS"],
        "desc": "رسوب قهوه‌ای.",
        "xp": 65
    },
    "تولید آلومینیوم (الکترولیز)": {
        "reactants": ["Al2O3 dissolved"],
        "products": ["Al", "O2"],
        "desc": "فرایند هال-هرولت.",
        "xp": 120
    },
    "خنثی‌سازی اسید استئاریک": {
        "reactants": ["C18H36O2", "KOH"],
        "products": ["C18H35O2K", "H2O"],
        "desc": "صابون پتاسیم.",
        "xp": 60
    },
    "سوختن فرئون (تخریب)": {
        "reactants": ["CCl2F2", "heat"],
        "products": ["CO2", "HF", "Cl2"],
        "desc": "تجزیه مضر.",
        "xp": 70
    },
    "رسوب اکسالات نقره": {
        "reactants": ["AgNO3", "H2C2O4"],
        "products": ["Ag2C2O4"],
        "desc": "رسوب سفید.",
        "xp": 55
    },
    "تجزیه پتاسیم یدات": {
        "reactants": ["KIO3 heat"],
        "products": ["KI", "O2"],
        "desc": "تولید اکسیژن.",
        "xp": 75
    },
    "اکسایش تولوئن به بنزالدئید": {
        "reactants": ["C6H5CH3", "KMnO4"],
        "products": ["C6H5CHO"],
        "desc": "اکسایش جانبی.",
        "xp": 90
    },
    "سوختن لیپید": {
        "reactants": ["fat", "O2"],
        "products": ["CO2", "H2O"],
        "desc": "متابولیسم چربی.",
        "xp": 60
    },
    "تشکیل پلی‌وینیل کلرید": {
        "reactants": ["C2H3Cl", "initiator"],
        "products": ["(C2H3Cl)n"],
        "desc": "PVC.",
        "xp": 100
    },
    "رسوب سولفید آنتیموان": {
        "reactants": ["SbCl3", "H2S"],
        "products": ["Sb2S3"],
        "desc": "رسوب نارنجی.",
        "xp": 70
    },
    "تولید مس (از سنگ معدن)": {
        "reactants": ["Cu2S", "O2"],
        "products": ["Cu", "SO2"],
        "desc": "روستینگ و ذوب.",
        "xp": 95
    },
    "خنثی‌سازی اسید اولئیک": {
        "reactants": ["C18H34O2", "NaOH"],
        "products": ["C18H33O2Na", "H2O"],
        "desc": "صابون مایع.",
        "xp": 65
    },
    "سوختن متانول با شعله آبی": {
        "reactants": ["CH3OH", "O2 complete"],
        "products": ["CO2", "H2O"],
        "desc": "احتراق پاک.",
        "xp": 50
    },
    "رسوب هیدروکسید روی": {
        "reactants": ["ZnCl2", "NH3 excess"],
        "products": ["[Zn(NH3)4](OH)2"],
        "desc": "حل شدن آمفوتر.",
        "xp": 75
    },
    "تجزیه آمونیوم پرسولفات": {
        "reactants": ["(NH4)2S2O8"],
        "products": ["N2", "H2SO4"],
        "desc": "اکسیدکننده قوی.",
        "xp": 85
    },
    "اکسایش بنزن به فنل": {
        "reactants": ["C6H6", "O2", "catalyst"],
        "products": ["C6H5OH"],
        "desc": "فرایند کمیل.",
        "xp": 100
    },
    "سوختن پروتئین": {
        "reactants": ["protein", "O2"],
        "products": ["CO2", "H2O", "NOx"],
        "desc": "احتراق بوی مو.",
        "xp": 60
    },
    "تشکیل پلی‌استایرن": {
        "reactants": ["C8H8", "initiator"],
        "products": ["(C8H8)n"],
        "desc": "فوم یا سخت.",
        "xp": 95
    },
    "رسوب فسفات منیزیم": {
        "reactants": ["MgSO4", "Na2HPO4"],
        "products": ["MgHPO4"],
        "desc": "در تست کلیه.",
        "xp": 65
    },
    "تولید تیتانیوم (کرول)": {
        "reactants": ["TiCl4", "Mg"],
        "products": ["Ti", "MgCl2"],
        "desc": "کاهش فلز.",
        "xp": 110
    },
    "خنثی‌سازی اسید لینولئیک": {
        "reactants": ["C18H32O2", "NaOH"],
        "products": ["C18H31O2Na", "H2O"],
        "desc": "اسید چرب غیراشباع.",
        "xp": 60
    },
    "سوختن دی‌اکسید کربن (با منیزیم)": {
        "reactants": ["CO2", "Mg hot"],
        "products": ["MgO", "C"],
        "desc": "کربن آزاد.",
        "xp": 70
    },
    "رسوب کرومات نقره": {
        "reactants": ["AgNO3", "K2CrO4"],
        "products": ["Ag2CrO4"],
        "desc": "رسوب قرمز.",
        "xp": 65
    },
    "تجزیه سدیم پراکسید": {
        "reactants": ["Na2O2", "H2O"],
        "products": ["NaOH", "O2"],
        "desc": "تولید اکسیژن.",
        "xp": 75
    },
    "اکسایش انیلین": {
        "reactants": ["C6H5NH2", "KMnO4"],
        "products": ["quinone"],
        "desc": "رنگ سیاه.",
        "xp": 85
    },
    "سوختن سلولز": {
        "reactants": ["(C6H10O5)n", "O2"],
        "products": ["CO2", "H2O"],
        "desc": "احتراق کاغذ.",
        "xp": 55
    },
    "تشکیل نمک طعام صنعتی": {
        "reactants": ["NaOH", "HCl"],
        "products": ["NaCl", "H2O"],
        "desc": "خنثی‌سازی صنعتی برای تولید نمک.",
        "xp": 50
    },
    "اکسایش جیوه": {
        "reactants": ["Hg", "O2"],
        "products": ["HgO"],
        "desc": "تشکیل اکسید قرمز یا زرد.",
        "xp": 60
    },
    "رسوب هیدروکسید کادمیم": {
        "reactants": ["CdSO4", "NaOH"],
        "products": ["Cd(OH)2"],
        "desc": "رسوب سفید.",
        "xp": 55
    },
    "سوختن پروپانول": {
        "reactants": ["C3H7OH", "O2"],
        "products": ["CO2", "H2O"],
        "desc": "احتراق الکل پروپیلیک.",
        "xp": 45
    },
    "تشکیل اسید هیدروبرومیک": {
        "reactants": ["H2", "Br2"],
        "products": ["HBr"],
        "desc": "ترکیب مستقیم برم.",
        "xp": 80
    },
    "تجزیه کربنات پتاسیم": {
        "reactants": ["K2CO3 heat"],
        "products": ["K2O", "CO2"],
        "desc": "تجزیه گرمایی قلیایی.",
        "xp": 60
    },
    "رسوب سولفید سرب": {
        "reactants": ["Pb(NO3)2", "H2S"],
        "products": ["PbS"],
        "desc": "رسوب سیاه گالن.",
        "xp": 65
    },
    "تولید پتاسیم هیدروکسید": {
        "reactants": ["KCl(aq)"],
        "products": ["KOH", "Cl2", "H2"],
        "desc": "الکترولیز سلول جیوه‌ای.",
        "xp": 110
    },
    "اکسایش پتاسیم سولفیت": {
        "reactants": ["K2SO3", "H2O2"],
        "products": ["K2SO4"],
        "desc": "اکسایش به سولفات.",
        "xp": 60
    },
    "سوختن بوتادین": {
        "reactants": ["C4H6", "O2"],
        "products": ["CO2", "H2O"],
        "desc": "احتراق لاستیک مصنوعی.",
        "xp": 55
    },
    "تشکیل کمپلکس آهن(III)": {
        "reactants": ["FeCl3", "KSCN"],
        "products": ["Fe(SCN)3"],
        "desc": "رنگ قرمز خون (تست آهن).",
        "xp": 85
    },
    "تولید گاز دی‌اکسید نیتروژن": {
        "reactants": ["Pb(NO3)2 heat"],
        "products": ["PbO", "NO2", "O2"],
        "desc": "گاز قهوه‌ای از نیترات.",
        "xp": 75
    },
    "خنثی‌سازی اسید پروپیونیک": {
        "reactants": ["C2H5COOH", "NaOH"],
        "products": ["C2H5COONa", "H2O"],
        "desc": "اسید پروپیونیک.",
        "xp": 50
    },
    "سوختن ایزوبوتن": {
        "reactants": ["C4H8 iso", "O2"],
        "products": ["CO2", "H2O"],
        "desc": "احتراق شاخه‌دار.",
        "xp": 45
    },
    "رسوب برمید سرب": {
        "reactants": ["Pb(NO3)2", "KBr"],
        "products": ["PbBr2"],
        "desc": "رسوب سفید کم‌رنگ.",
        "xp": 55
    },
    "تجزیه سدیم پرمنگنات": {
        "reactants": ["NaMnO4 heat"],
        "products": ["Na2MnO4", "MnO2", "O2"],
        "desc": "تجزیه مشابه پتاسیم.",
        "xp": 80
    },
    "اکسایش پروپانول به پروپانال": {
        "reactants": ["C3H7OH", "PCC"],
        "products": ["C3H6O"],
        "desc": "اکسایش انتخابی.",
        "xp": 90
    },
    "سوختن پنتادین": {
        "reactants": ["C5H8", "O2"],
        "products": ["CO2", "H2O"],
        "desc": "احتراق دی‌ان.",
        "xp": 55
    },
    "تشکیل دی‌نیتروژن تری‌اکسید": {
        "reactants": ["NO", "O2 cold"],
        "products": ["N2O3"],
        "desc": "گاز آبی در سرما.",
        "xp": 95
    },
    "رسوب هیدروکسید قلع(II)": {
        "reactants": ["SnCl2", "NH3"],
        "products": ["Sn(OH)2"],
        "desc": "رسوب سفید آمفوتر.",
        "xp": 65
    },
    "تولید گاز هیدروژن از منیزیم": {
        "reactants": ["Mg", "H2O steam"],
        "products": ["MgO", "H2"],
        "desc": "واکنش با بخار.",
        "xp": 70
    },
    "خنثی‌سازی اسید بوتریک": {
        "reactants": ["C3H7COOH", "KOH"],
        "products": ["C3H7COOK", "H2O"],
        "desc": "بوی کره فاسد.",
        "xp": 55
    },
    "سوختن ترپنتین": {
        "reactants": ["C10H16", "O2"],
        "products": ["CO2", "H2O"],
        "desc": "احتراق روغن درخت کاج.",
        "xp": 50
    },
    "رسوب سولفات کلسیم": {
        "reactants": ["CaCl2", "H2SO4"],
        "products": ["CaSO4"],
        "desc": "رسوب گچ.",
        "xp": 50
    },
    "تجزیه هیدروژن پراکسید با خون": {
        "reactants": ["H2O2", "catalase"],
        "products": ["H2O", "O2"],
        "desc": "حباب در زخم.",
        "xp": 75
    },
    "اکسایش سدیم تیوسولفات": {
        "reactants": ["Na2S2O3", "Cl2"],
        "products": ["Na2SO4"],
        "desc": "در سفیدکننده.",
        "xp": 70
    },
    "سوختن هگزانول": {
        "reactants": ["C6H13OH", "O2"],
        "products": ["CO2", "H2O"],
        "desc": "احتراق الکل سنگین.",
        "xp": 50
    },
    "تشکیل کمپلکس مس(II)": {
        "reactants": ["CuSO4", "EDTA"],
        "products": ["Cu-EDTA"],
        "desc": "کمپلکس پایدار.",
        "xp": 85
    },
    "رسوب کربنات باریم": {
        "reactants": ["BaCl2", "KHCO3"],
        "products": ["BaCO3"],
        "desc": "رسوب سنگین.",
        "xp": 55
    },
    "تولید گاز نیتریک اکسید": {
        "reactants": ["NaNO2", "HCl"],
        "products": ["NO"],
        "desc": "گاز بی‌رنگ.",
        "xp": 80
    },
    "خنثی‌سازی اسید والریک": {
        "reactants": ["C4H9COOH", "NaOH"],
        "products": ["C4H9COONa", "H2O"],
        "desc": "اسید چرب.",
        "xp": 55
    },
    "سوختن نونان": {
        "reactants": ["C9H20", "O2"],
        "products": ["CO2", "H2O"],
        "desc": "احتراق گازوئیل.",
        "xp": 45
    },
    "رسوب فلورید استرانسیم": {
        "reactants": ["SrCl2", "HF"],
        "products": ["SrF2"],
        "desc": "رسوب دندان.",
        "xp": 50
    },
    "اکسایش آرسنیک(III)": {
        "reactants": ["As2O3", "HNO3"],
        "products": ["H3AsO4"],
        "desc": "به اسید آرسنیک.",
        "xp": 75
    },
    "سوختن دودکان": {
        "reactants": ["C12H26", "O2"],
        "products": ["CO2", "H2O"],
        "desc": "احتراق نفت.",
        "xp": 50
    },
    "تشکیل اسید هیپوبرومیک": {
        "reactants": ["Br2", "H2O"],
        "products": ["HBrO", "HBr"],
        "desc": "ضعیف‌تر از کلر.",
        "xp": 70
    },
    "رسوب سولفید بیسموت": {
        "reactants": ["Bi(NO3)3", "H2S"],
        "products": ["Bi2S3"],
        "desc": "رسوب سیاه.",
        "xp": 65
    },
    "تولید پراکسید سدیم": {
        "reactants": ["Na", "O2"],
        "products": ["Na2O2"],
        "desc": "پراکسید زرد.",
        "xp": 85
    },
    "خنثی‌سازی اسید کاپروئیک": {
        "reactants": ["C5H11COOH", "NaOH"],
        "products": ["C5H11COONa", "H2O"],
        "desc": "بوی بز.",
        "xp": 55
    },
    "سوختن سیکلوپنتان": {
        "reactants": ["C5H10", "O2"],
        "products": ["CO2", "H2O"],
        "desc": "احتراق حلقوی کوچک.",
        "xp": 50
    },
    "رسوب کرومات استرانسیم": {
        "reactants": ["SrCl2", "K2Cr2O7"],
        "products": ["SrCrO4"],
        "desc": "رسوب زرد.",
        "xp": 60
    },
    "تجزیه کلسیم نیترات": {
        "reactants": ["Ca(NO3)2 heat"],
        "products": ["CaO", "NO2", "O2"],
        "desc": "نیترات کلسیم.",
        "xp": 70
    },
    "اکسایش هیپوفسفیت": {
        "reactants": ["NaH2PO2", "HgCl2"],
        "products": ["Na2HPO4"],
        "desc": "کاهش جیوه.",
        "xp": 80
    },
    "سوختن نفتالن با کاتالیزور": {
        "reactants": ["C10H8", "O2 cat"],
        "products": ["phthalic anhydride"],
        "desc": "اکسایش صنعتی.",
        "xp": 95
    },
    "تشکیل کمپلکس روی": {
        "reactants": ["ZnSO4", "NH3"],
        "products": ["[Zn(NH3)4]SO4"],
        "desc": "کمپلکس آمینی.",
        "xp": 75
    },
    "رسوب سولفات باریم (تست)": {
        "reactants": ["BaCl2", "SO4^2-"],
        "products": ["BaSO4"],
        "desc": "تست سولفات.",
        "xp": 50
    },
    "تولید گاز هلیوم (رادیواکتیو)": {
        "reactants": ["U-238 decay"],
        "products": ["He", "Pb"],
        "desc": "پوسیدگی آلفا.",
        "xp": 100
    },
    "خنثی‌سازی اسید هپتانوئیک": {
        "reactants": ["C6H13COOH", "KOH"],
        "products": ["C6H13COOK", "H2O"],
        "desc": "اسید چرب.",
        "xp": 55
    },
    "سوختن فرمالین": {
        "reactants": ["HCHO aq", "O2"],
        "products": ["CO2", "H2O"],
        "desc": "احتراق محلول.",
        "xp": 45
    },
    "رسوب فسفات استرانسیم": {
        "reactants": ["Sr(NO3)2", "Na3PO4"],
        "products": ["Sr3(PO4)2"],
        "desc": "رسوب سفید.",
        "xp": 55
    },
    "تجزیه پتاسیم پراکسید": {
        "reactants": ["K2O2", "H2O"],
        "products": ["KOH", "O2"],
        "desc": "پراکسید پتاسیم.",
        "xp": 80
    },
    "اکسایش فسفر قرمز": {
        "reactants": ["P red", "O2 slow"],
        "products": ["P4O10"],
        "desc": "اکسایش آرام.",
        "xp": 70
    },
    "سوختن استالدئید": {
        "reactants": ["CH3CHO", "O2"],
        "products": ["CO2", "H2O"],
        "desc": "احتراق تند.",
        "xp": 50
    },
    "تشکیل پلی‌متاکریلات": {
        "reactants": ["methyl methacrylate", "initiator"],
        "products": ["PMMA"],
        "desc": "پلکسی‌گلاس.",
        "xp": 100
    },
    "رسوب کلرید سرب": {
        "reactants": ["Pb(NO3)2", "NaCl"],
        "products": ["PbCl2"],
        "desc": "رسوب سفید گرم‌حل.",
        "xp": 55
    },
    "تولید آهن (کاهش)": {
        "reactants": ["Fe2O3", "CO"],
        "products": ["Fe", "CO2"],
        "desc": "کوره بلند.",
        "xp": 110
    },
    "خنثی‌سازی اسید کاپریلیک": {
        "reactants": ["C7H15COOH", "NaOH"],
        "products": ["C7H15COONa", "H2O"],
        "desc": "در نارگیل.",
        "xp": 60
    },
    "سوختن اتیل استات": {
        "reactants": ["C4H8O2", "O2"],
        "products": ["CO2", "H2O"],
        "desc": "احتراق استر.",
        "xp": 50
    },
    "رسوب هیدروکسید باریم": {
        "reactants": ["BaCl2", "NH3"],
        "products": ["Ba(OH)2"],
        "desc": "محلول قوی.",
        "xp": 50
    },
    "تجزیه باریم آزید": {
        "reactants": ["Ba(N3)2 heat"],
        "products": ["Ba", "N2"],
        "desc": "انفجاری.",
        "xp": 90
    },
    "اکسایش منگنز به پرمنگنات": {
        "reactants": ["MnSO4", "PbO2", "HNO3"],
        "products": ["HMnO4"],
        "desc": "سنتز پرمنگنات.",
        "xp": 95
    },
    "سوختن پروپیونیتریل": {
        "reactants": ["C3H5N", "O2"],
        "products": ["CO2", "H2O", "NO2"],
        "desc": "احتراق نیتریل.",
        "xp": 60
    },
    "تشکیل پلی‌تترافلورواتیلن": {
        "reactants": ["C2F4", "catalyst"],
        "products": ["Teflon"],
        "desc": "PTFE ضدچسب.",
        "xp": 110
    },
    "رسوب سولفید آرسنیک": {
        "reactants": ["As2O3", "H2S"],
        "products": ["As2S3"],
        "desc": "رسوب زرد.",
        "xp": 70
    },
    "تولید طلا (کاهش)": {
        "reactants": ["AuCl3", "SO2"],
        "products": ["Au"],
        "desc": "رسوب طلا.",
        "xp": 100
    },
    "خنثی‌سازی اسید لوریک": {
        "reactants": ["C11H23COOH", "NaOH"],
        "products": ["C11H23COONa", "H2O"],
        "desc": "در صابون.",
        "xp": 60
    },
    "سوختن دی‌اتیل اتر": {
        "reactants": ["C4H10O", "O2"],
        "products": ["CO2", "H2O"],
        "desc": "انفجاری.",
        "xp": 55
    },
    "رسوب هیدروکسید استرانسیم": {
        "reactants": ["SrCl2", "NaOH"],
        "products": ["Sr(OH)2"],
        "desc": "باز قوی.",
        "xp": 50
    },
    "تجزیه سدیم هیپوکلریت": {
        "reactants": ["NaOCl"],
        "products": ["NaCl", "O"],
        "desc": "تجزیه سفیدکننده.",
        "xp": 70
    },
    "اکسایش کروم(III) به کرومات": {
        "reactants": ["Cr2(SO4)3", "H2O2", "base"],
        "products": ["CrO4^2-"],
        "desc": "رنگ زرد.",
        "xp": 85
    },
    "سوختن گلیسرول": {
        "reactants": ["C3H8O3", "O2"],
        "products": ["CO2", "H2O"],
        "desc": "احتراق چسبناک.",
        "xp": 50
    },
    "تشکیل پلی‌اکریلونیتریل": {
        "reactants": ["C3H3N", "catalyst"],
        "products": ["PAN"],
        "desc": "الیاف مصنوعی.",
        "xp": 100
    },
    "رسوب سولفید آنتیموان(V)": {
        "reactants": ["SbCl5", "H2S"],
        "products": ["Sb2S5"],
        "desc": "رسوب نارنجی.",
        "xp": 70
    },
    "تولید نقره (از فیلم)": {
        "reactants": ["AgBr", "developer"],
        "products": ["Ag"],
        "desc": "عکاسی قدیمی.",
        "xp": 90
    },
    "خنثی‌سازی اسید میریستیک": {
        "reactants": ["C13H27COOH", "KOH"],
        "products": ["C13H27COOK", "H2O"],
        "desc": "در جوز هندی.",
        "xp": 60
    },
    "سوختن بنزالدئید": {
        "reactants": ["C6H5CHO", "O2"],
        "products": ["CO2", "H2O"],
        "desc": "بوی بادام.",
        "xp": 55
    },
    "رسوب اکسالات باریم": {
        "reactants": ["BaCl2", "H2C2O4"],
        "products": ["BaC2O4"],
        "desc": "رسوب سفید.",
        "xp": 55
    },
    "تجزیه پتاسیم پرسولفات": {
        "reactants": ["K2S2O8"],
        "products": ["K2SO4", "O2"],
        "desc": "اکسیدکننده.",
        "xp": 80
    },
    "اکسایش وانادیوم": {
        "reactants": ["V2O5", "change"],
        "products": ["color change"],
        "desc": "تغییر رنگ چندگانه.",
        "xp": 90
    },
    "سوختن ساکارز": {
        "reactants": ["C12H22O11", "O2"],
        "products": ["CO2", "H2O"],
        "desc": "کارامل به سیاه.",
        "xp": 50
    },
    "تشکیل پلی‌بوتادین": {
        "reactants": ["C4H6", "Ziegler"],
        "products": ["rubber"],
        "desc": "لاستیک مصنوعی.",
        "xp": 105
    },
    "رسوب فسفومولیبدات": {
        "reactants": ["PO4^3-", "molybdate", "HNO3"],
        "products": ["(NH4)3PMo12O40"],
        "desc": "رسوب زرد تست فسفات.",
        "xp": 75
    },
    "تولید کروم (کاهش)": {
        "reactants": ["Cr2O3", "Al"],
        "products": ["Cr", "Al2O3"],
        "desc": "ترمیت کروم.",
        "xp": 110
    },
    "خنثی‌سازی اسید پالمیتوئولئیک": {
        "reactants": ["C16H30O2", "NaOH"],
        "products": ["soap"],
        "desc": "صابون غیراشباع.",
        "xp": 60
    },
    "سوختن فنیل‌اتانول": {
        "reactants": ["C6H5CH2CH2OH", "O2"],
        "products": ["CO2", "H2O"],
        "desc": "بوی گل رز.",
        "xp": 55
    },
    "رسوب کبالت هیدروکسید": {
        "reactants": ["CoSO4", "KOH"],
        "products": ["Co(OH)2"],
        "desc": "آبی به صورتی.",
        "xp": 60
    },
    "تجزیه آمونیوم دی‌کرومات با حرارت": {
        "reactants": ["(NH4)2Cr2O7 heat"],
        "products": ["Cr2O3 green"],
        "desc": "آتشفشان آزمایشگاهی.",
        "xp": 120
    },
    "اکسایش تیتانیوم": {
        "reactants": ["Ti", "O2"],
        "products": ["TiO2"],
        "desc": "پوشش سفید.",
        "xp": 70
    },
    "سوختن فروکتوز": {
        "reactants": ["C6H12O6", "O2"],
        "products": ["CO2", "H2O"],
        "desc": "قند میوه.",
        "xp": 50
    },
    "تشکیل پلی‌کربنات": {
        "reactants": ["bisphenol A", "phosgene"],
        "products": ["PC"],
        "desc": "پلاستیک مقاوم.",
        "xp": 110
    },
    "رسوب نیکل دی‌متیل‌گلیوکسیم": {
        "reactants": ["Ni2+", "DMG"],
        "products": ["Ni(DMG)2"],
        "desc": "رسوب قرمز تست نیکل.",
        "xp": 80
    },
    "تولید زیرکونیم": {
        "reactants": ["ZrCl4", "Mg"],
        "products": ["Zr"],
        "desc": "فرایند کرول مشابه.",
        "xp": 115
    },
    "خنثی‌سازی اسید آراشیدونیک": {
        "reactants": ["C20H32O2", "NaOH"],
        "products": ["soap"],
        "desc": "اسید ضروری.",
        "xp": 65
    },
    "سوختن کومن": {
        "reactants": ["C9H12", "O2"],
        "products": ["CO2", "H2O"],
        "desc": "احتراق ایزوپروپیل‌بنزن.",
        "xp": 55
    },
    "رسوب منیزیم آمونیوم فسفات": {
        "reactants": ["Mg2+", "NH4+", "PO4"],
        "products": ["MgNH4PO4"],
        "desc": "تست منیزیم.",
        "xp": 70
    },
    "تجزیه اورانیوم (شکافت)": {
        "reactants": ["U-235", "neutron"],
        "products": ["fission products", "energy"],
        "desc": "انرژی هسته‌ای.",
        "xp": 150},
"تجزیه کلسیم کربنات": {"reactants": ["CaCO3"], "products": ["CaO", "CO2"], "desc": "تولید آهک زنده از سنگ آهک در کوره.", "xp": 80, "temp_min": 825},
"تجزیه آمونیوم دی‌کرومات": {"reactants": ["(NH4)2Cr2O7"], "products": ["Cr2O3", "N2", "H2O"], "desc": "آتشفشان نارنجی که خاکستر سبز تولید می‌کند.", "xp": 150, "temp_min": 180},
"تجزیه پتاسیم کلرات": {"reactants": ["KClO3"], "products": ["KCl", "O2"], "desc": "روش آزمایشگاهی برای تولید اکسیژن خالص.", "xp": 110, "temp_min": 400},
"تجزیه جوش شیرین": {"reactants": ["NaHCO3"], "products": ["Na2CO3", "CO2", "H2O"], "desc": "آزاد شدن گاز برای پف کردن کیک و نان.", "xp": 50, "temp_min": 70},
"تجزیه نیتروگلیسیرین": {"reactants": ["C3H5N3O9"], "products": ["CO2", "N2", "H2O", "O2"], "desc": "انفجار فوق‌العاده سریع و خطرناک.", "xp": 250, "temp_min": 170},
"تجزیه جیوه (II) اکسید": {"reactants": ["HgO"], "products": ["Hg", "O2"], "desc": "واکنش تاریخی پریستلی برای کشف اکسیژن.", "xp": 130, "temp_min": 500},
"تجزیه کلسیم سولفات": {"reactants": ["CaSO4.2H2O"], "products": ["CaSO4", "H2O"], "desc": "تولید گچ ساختمانی از سنگ گچ.", "xp": 45, "temp_min": 150},
"تجزیه مس (II) کربنات": {"reactants": ["CuCO3"], "products": ["CuO", "CO2"], "desc": "تغییر رنگ پودر سبز به سیاه اکسید مس.", "xp": 75, "temp_min": 290},
"تجزیه سدیم آزید": {"reactants": ["NaN3"], "products": ["Na", "N2"], "desc": "واکنش اصلی باز شدن کیسه هوای خودرو.", "xp": 160, "temp_min": 300},
"تجزیه نیترات آمونیوم": {"reactants": ["NH4NO3"], "products": ["N2O", "H2O"], "desc": "تولید گاز خنده‌آور (نیتروس اکسید).", "xp": 140, "temp_min": 210},
"تجزیه باریم پراکسید": {"reactants": ["BaO2"], "products": ["BaO", "O2"], "desc": "تولید اکسیژن در دمای بالا.", "xp": 90, "temp_min": 700},
"تجزیه مس (II) نیترات": {"reactants": ["Cu(NO3)2"], "products": ["CuO", "NO2", "O2"], "desc": "آزاد شدن گاز قهوه‌ای سمی دی‌اکسید نیتروژن.", "xp": 120, "temp_min": 170},
"تجزیه سرب (II) نیترات": {"reactants": ["Pb(NO3)2"], "products": ["PbO", "NO2", "O2"], "desc": "تولید پودر زرد رنگ اکسید سرب.", "xp": 115, "temp_min": 470},
"تجزیه نقره اکسید": {"reactants": ["Ag2O"], "products": ["Ag", "O2"], "desc": "استخراج نقره خالص با حرارت مستقیم.", "xp": 180, "temp_min": 280},
"تجزیه آهن (III) هیدروکسید": {"reactants": ["Fe(OH)3"], "products": ["Fe2O3", "H2O"], "desc": "تبدیل رسوب زنگ‌زده به اکسید آهن خشک.", "xp": 65, "temp_min": 200},
"تجزیه هیدروژن پراکسید": {"reactants": ["H2O2"], "products": ["H2O", "O2"], "desc": "تجزیه خودبه‌خودی آب اکسیژنه در گرما.", "xp": 70, "temp_min": 80},
"تجزیه پتاسیم پرمنگنات": {"reactants": ["KMnO4"], "products": ["K2MnO4", "MnO2", "O2"], "desc": "تجزیه بلورهای بنفش به پودر سیاه.", "xp": 145, "temp_min": 240},
"تجزیه لیتیوم کربنات": {"reactants": ["Li2CO3"], "products": ["Li2O", "CO2"], "desc": "تجزیه سخت‌ترین کربنات قلیایی.", "xp": 100, "temp_min": 1300},
"تجزیه مگنتیت": {"reactants": ["Fe3O4"], "products": ["FeO", "O2"], "desc": "کاهش اکسید مغناطیسی آهن.", "xp": 135, "temp_min": 1500},
"تجزیه اسید اگزالیک": {"reactants": ["H2C2O4"], "products": ["CO2", "CO", "H2O"], "desc": "تولید همزمان دو اکسید کربن.", "xp": 95, "temp_min": 105},
"تجزیه دی‌نیتروژن مونوکسید": {"reactants": ["N2O"], "products": ["N2", "O2"], "desc": "شکستن گاز خنده در دمای بسیار بالا.", "xp": 155, "temp_min": 600},
"تجزیه آلومینیوم هیدروکسید": {"reactants": ["Al(OH)3"], "products": ["Al2O3", "H2O"], "desc": "تولید پودر آلومینا برای ذوب فلز.", "xp": 85, "temp_min": 570},
"تجزیه آمونیوم کلرید": {"reactants": ["NH4Cl"], "products": ["NH3", "HCl"], "desc": "تصعید و تجزیه همزمان نشادر.", "xp": 60, "temp_min": 340},
"تجزیه تیتانیوم هیدرید": {"reactants": ["TiH2"], "products": ["Ti", "H2"], "desc": "تولید پودر فلز تیتانیوم خالص.", "xp": 190, "temp_min": 400},
"تجزیه سدیم پرسولفات": {"reactants": ["Na2S2O8"], "products": ["Na2SO4", "SO3"], "desc": "آزاد شدن گاز تند تری‌اکسید گوگرد.", "xp": 125, "temp_min": 180},
"تجزیه روی کربنات": {"reactants": ["ZnCO3"], "products": ["ZnO", "CO2"], "desc": "تولید اکسید روی (سفیداب).", "xp": 70, "temp_min": 300},
"تجزیه سرب (IV) اکسید": {"reactants": ["PbO2"], "products": ["PbO", "O2"], "desc": "کاهش عدد اکسایش سرب در گرما.", "xp": 105, "temp_min": 290},
"تجزیه کلسیم اگزالات": {"reactants": ["CaC2O4"], "products": ["CaCO3", "CO"], "desc": "مرحله اول تجزیه نمک اگزالات.", "xp": 110, "temp_min": 400},
"تجزیه آهن (II) سولفات": {"reactants": ["FeSO4"], "products": ["Fe2O3", "SO2", "SO3"], "desc": "تجزیه پیچیده زاج سبز.", "xp": 165, "temp_min": 680},
"تجزیه آمونیوم کربنات": {"reactants": ["(NH4)2CO3"], "products": ["NH3", "CO2", "H2O"], "desc": "نمک بویا که کاملاً تبخیر می‌شود.", "xp": 55, "temp_min": 58},
"تجزیه منیزیم هیدروکسید": {"reactants": ["Mg(OH)2"], "products": ["MgO", "H2O"], "desc": "استخراج منیزیا از هیدروکسید منیزیم.", "xp": 80, "temp_min": 350},
"تجزیه برلیوم کربنات": {"reactants": ["BeCO3"], "products": ["BeO", "CO2"], "desc": "ناپایدارترین کربنات گروه دوم.", "xp": 140, "temp_min": 100},
"تجزیه استرانسیوم نیترات": {"reactants": ["Sr(NO3)2"], "products": ["SrO", "NO2", "O2"], "desc": "تجزیه نمک عامل شعله قرمز.", "xp": 130, "temp_min": 570},
"تجزیه مولیبدن تری‌اکسید": {"reactants": ["MoO3"], "products": ["Mo", "O2"], "desc": "تجزیه حرارتی اکسید مولیبدن.", "xp": 210, "temp_min": 1100},
"تجزیه نیکل (II) کربنات": {"reactants": ["NiCO3"], "products": ["NiO", "CO2"], "desc": "تولید اکسید سبز رنگ نیکل.", "xp": 90, "temp_min": 350},
"تجزیه باریم هیدروکسید": {"reactants": ["Ba(OH)2"], "products": ["BaO", "H2O"], "desc": "تبدیل باریم هیدروکسید به اکسید.", "xp": 115, "temp_min": 800},
"تجزیه آنتیموان تری‌سولفید": {"reactants": ["Sb2S3"], "products": ["Sb", "S"], "desc": "جداسازی عنصر آنتیموان از کانه.", "xp": 175, "temp_min": 550},
"تجزیه اوره": {"reactants": ["CH4N2O"], "products": ["NH3", "HNCO"], "desc": "تولید آمونیاک و اسید ایزوسیانیک.", "xp": 85, "temp_min": 135},
"تجزیه فسفر پنتاکلرید": {"reactants": ["PCl5"], "products": ["PCl3", "Cl2"], "desc": "واکنش تعادلی مشهور در شیمی.", "xp": 100, "temp_min": 160},
"تجزیه کبالت (II) کلرید": {"reactants": ["CoCl2.6H2O"], "products": ["CoCl2", "H2O"], "desc": "تغییر رنگ صورتی به آبی (خشک شدن).", "xp": 40, "temp_min": 120},
"تجزیه سدیم نیترات": {"reactants": ["NaNO3"], "products": ["NaNO2", "O2"], "desc": "تولید سدیم نیتریت.", "xp": 95, "temp_min": 380},
"تجزیه طلا (III) کلرید": {"reactants": ["AuCl3"], "products": ["AuCl", "Cl2"], "desc": "مرحله اول بازیابی طلا.", "xp": 200, "temp_min": 160},
"تجزیه یدیک اسید": {"reactants": ["HIO3"], "products": ["I2O5", "H2O"], "desc": "تولید پنتا اکسید ید.", "xp": 110, "temp_min": 170},
"تجزیه هیدرازین": {"reactants": ["N2H4"], "products": ["NH3", "N2"], "desc": "واکنش کاتالیزوری سوخت موشک.", "xp": 180, "temp_min": 250},
"تجزیه منیزیم سیلیکات": {"reactants": ["Mg2SiO4"], "products": ["MgO", "SiO2"], "desc": "تجزیه کانی الیوین در حرارت بالا.", "xp": 150, "temp_min": 1400},
"تجزیه نقره کربنات": {"reactants": ["Ag2CO3"], "products": ["Ag2O", "CO2"], "desc": "تغییر رنگ زرد به قهوه‌ای.", "xp": 120, "temp_min": 210},
"تجزیه مس (I) اکسید": {"reactants": ["Cu2O"], "products": ["Cu", "O2"], "desc": "کاهش حرارتی مس قرمز.", "xp": 160, "temp_min": 1235},
"تجزیه دی‌اکسید منگنز": {"reactants": ["MnO2"], "products": ["Mn2O3", "O2"], "desc": "کاهش اکسید منگنز در کوره.", "xp": 110, "temp_min": 535},
"تجزیه آمونیوم سولفات": {"reactants": ["(NH4)2SO4"], "products": ["NH4HSO4", "NH3"], "desc": "تجزیه کود شیمیایی.", "xp": 65, "temp_min": 235},
"تجزیه تالیم (I) کربنات": {"reactants": ["Tl2CO3"], "products": ["Tl2O", "CO2"], "desc": "تجزیه نمک سمی تالیم.", "xp": 140, "temp_min": 270},
"تجزیه بیسموت نیترات": {"reactants": ["Bi(NO3)3"], "products": ["Bi2O3", "NO2", "O2"], "desc": "تولید اکسید زرد بیسموت.", "xp": 130, "temp_min": 450},
"تجزیه کلسیم هیدرید": {"reactants": ["CaH2"], "products": ["Ca", "H2"], "desc": "آزاد سازی گاز هیدروژن از جامد.", "xp": 145, "temp_min": 600},
"تجزیه بوریک اسید": {"reactants": ["H3BO3"], "products": ["HBO2", "H2O"], "desc": "تولید اسید متابوریک.", "xp": 50, "temp_min": 170},
"تجزیه آلومینیوم نیترات": {"reactants": ["Al(NO3)3"], "products": ["Al2O3", "NO2", "O2"], "desc": "تولید پودر آلومینا با خلوص بالا.", "xp": 110, "temp_min": 150},
"تجزیه سدیم هیپوکلریت": {"reactants": ["NaClO"], "products": ["NaCl", "O2"], "desc": "تجزیه وایتکس در مقابل نور و گرما.", "xp": 45, "temp_min": 40},
"تجزیه روی هیدروکسید": {"reactants": ["Zn(OH)2"], "products": ["ZnO", "H2O"], "desc": "تبدیل رسوب سفید به پودر اکسید.", "xp": 75, "temp_min": 125},
"تجزیه کادمیم کربنات": {"reactants": ["CdCO3"], "products": ["CdO", "CO2"], "desc": "تجزیه نمک سمی کادمیم.", "xp": 135, "temp_min": 350},
"تجزیه لانتان نیترات": {"reactants": ["La(NO3)3"], "products": ["La2O3", "NO2", "O2"], "desc": "تجزیه نمک خاکی کمیاب.", "xp": 220, "temp_min": 600},
"تجزیه قلع (II) هیدروکسید": {"reactants": ["Sn(OH)2"], "products": ["SnO", "H2O"], "desc": "تولید اکسید سیاه قلع.", "xp": 95, "temp_min": 150},
"تجزیه پتاسیم بی‌کربنات": {"reactants": ["KHCO3"], "products": ["K2CO3", "CO2", "H2O"], "desc": "تجزیه حرارتی پتاسیم بی‌کربنات.", "xp": 60, "temp_min": 120}
}

# =============================================================================

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
"""

TYPE_MAP = {
    "Strong Acid": "مایع (اسید قوی)", "Weak Acid": "مایع (اسید ضعیف)", "Strong Base": "مایع (باز قوی)",
    "Weak Base": "مایع (باز ضعیف)", "Acid": "مایع (اسید)", "Base": "مایع (باز)", "Superacid": "ابر اسید",
    "Gas": "گاز", "Liquid": "مایع", "Solid": "جامد", "Metal": "جامد (فلز)", "Oxide": "جامد (اکسید)",
    "Salt": "جامد (نمک)", "Element": "جامد (عنصر)", "Halogen": "هالوژن", "Ion": "یون", "Complex": "کمپلکس",
    "Precipitate": "جامد (رسوب)", "Organic Compound": "ترکیب آلی", "Alcohol": "مایع (الکل)", "Sugar": "قند",
    "Solvent": "مایع (حلال)", "Explosive": "ماده منفجره", "Radioactive": "رادیواکتیو"
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
        if formula == "Mix" or formula == "-" or formula is None: return Counter()
        temp_formula = formula
        # Expand parenthesis e.g. (OH)2 -> OHOH (simplified)
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
        """
        محاسبه فرمول تجربی کلی برای کل محتویات ظرف.
        دیگر محدودیت 'مخلوط پیچیده' وجود ندارد و همه اتم‌ها محاسبه می‌شوند.
        """
        if not atom_moles_counter:
            return "ماده‌ای وجود ندارد"

        # فیلتر کردن مقادیر بسیار ناچیز
        filtered_atoms = {k: v for k, v in atom_moles_counter.items() if v > 1e-9}
        if not filtered_atoms:
            return "-"

        # پیدا کردن کوچکترین مقدار مول برای نرمال‌سازی نسبت‌ها
        min_mole = min(filtered_atoms.values())
        if min_mole < 1e-12:  # جلوگیری از تقسیم بر صفر
            return "ناچیز"

        ratios = {k: v / min_mole for k, v in filtered_atoms.items()}

        # تلاش برای پیدا کردن ضریب صحیح (1 تا 20)
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

            # اگر خطا خیلی کم بود، همین را قبول کن
            if current_error < 0.1:
                break

        # مرتب‌سازی عناصر: کربن، هیدروژن، سپس الفبایی
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
        self._flash_opacity = value;
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
            lbl_r.setWordWrap(True);
            self.table_wiki.setCellWidget(i, 1, lbl_r)
            lbl_p = QLabel(" + ".join([self.get_state_color_text(p) for p in d['products']]))
            lbl_p.setWordWrap(True);
            self.table_wiki.setCellWidget(i, 2, lbl_p)
            self.table_wiki.setItem(i, 3, QTableWidgetItem(str(d.get('temp_min', '-'))))
            self.table_wiki.setItem(i, 4, QTableWidgetItem(str(d.get('xp', 0))))
        self.table_wiki.resizeRowsToContents()

    def create_discoveries_tab(self):
        w = QWidget();
        l = QVBoxLayout(w)
        self.table_disc = QTableWidget();
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
        w = QWidget();
        l = QVBoxLayout(w)
        t = QTableWidget();
        t.setColumnCount(7);
        t.setHorizontalHeaderLabels(["نام", "فرمول", "نوع", "رنگ", "مولاریته (M)", "pH", "گرما (Heat)"])
        t.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        t.setRowCount(len(CHEMILAB_DB))
        for i, (k, v) in enumerate(sorted(CHEMILAB_DB.items(), key=lambda x: x[1]['name'])):
            t.setItem(i, 0, QTableWidgetItem(v.get('name', '')))
            t.setItem(i, 1, QTableWidgetItem(ChemicalCalculator.to_subscript(v.get('formula', ''))))
            t.setItem(i, 2, QTableWidgetItem(get_persian_type(v.get('type', ''))))
            color_cell = QTableWidgetItem("");
            color_cell.setBackground(QColor(v.get('color', '#FFFFFF')));
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
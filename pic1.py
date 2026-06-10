import sys
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QLabel
)
from PyQt5.QtCore import Qt
import pyqtgraph.opengl as gl
from rdkit import Chem
from rdkit.Chem import AllChem


class MoleculeViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("3D Molecule Viewer - PyQt5")
        self.setGeometry(200, 200, 1000, 700)
        self.init_ui()

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        layout = QVBoxLayout()
        main_widget.setLayout(layout)

        title = QLabel("3D Molecule Viewer")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)

        input_layout = QHBoxLayout()

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Enter SMILES (e.g. O=S(=O)(O)O)")
        input_layout.addWidget(self.input_field)

        self.button = QPushButton("Generate 3D")
        self.button.clicked.connect(self.generate_molecule)
        input_layout.addWidget(self.button)

        layout.addLayout(input_layout)

        self.gl_view = gl.GLViewWidget()
        self.gl_view.setBackgroundColor('w')
        self.gl_view.opts['distance'] = 20
        layout.addWidget(self.gl_view)

    def clear_scene(self):
        self.gl_view.clear()

    def generate_molecule(self):
        smiles = self.input_field.text().strip()
        self.clear_scene()

        try:
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                print("Invalid SMILES")
                return

            mol = Chem.AddHs(mol)
            AllChem.EmbedMolecule(mol, AllChem.ETKDG())
            AllChem.UFFOptimizeMolecule(mol)

            conf = mol.GetConformer()

            atom_positions = []
            atom_colors = []

            color_map = {
                "C": (0.2, 0.2, 0.2, 1),
                "H": (1, 1, 1, 1),
                "O": (1, 0, 0, 1),
                "N": (0, 0, 1, 1),
                "S": (1, 1, 0, 1),
            }

            for atom in mol.GetAtoms():
                pos = conf.GetAtomPosition(atom.GetIdx())
                atom_positions.append([pos.x, pos.y, pos.z])

                symbol = atom.GetSymbol()
                atom_colors.append(color_map.get(symbol, (0.5, 0.5, 0.5, 1)))

            atom_positions = np.array(atom_positions)

            scatter = gl.GLScatterPlotItem(
                pos=atom_positions,
                size=0.6,
                color=atom_colors,
                pxMode=False
            )
            self.gl_view.addItem(scatter)

            for bond in mol.GetBonds():
                start = bond.GetBeginAtomIdx()
                end = bond.GetEndAtomIdx()

                pos = np.array([
                    atom_positions[start],
                    atom_positions[end]
                ])

                line = gl.GLLinePlotItem(
                    pos=pos,
                    color=(0, 0, 0, 1),
                    width=2,
                    antialias=True
                )
                self.gl_view.addItem(line)

        except Exception as e:
            print("Error:", e)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MoleculeViewer()
    window.show()
    sys.exit(app.exec())

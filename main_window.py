from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QApplication,
)
from torqeedo_programmer import TorqeedoProgrammer


class MainWindow(QMainWindow):
    def __init__(self, torqeedo_programmer):
        super().__init__()
        self.torqeedo_programmer: TorqeedoProgrammer = torqeedo_programmer
        self.setWindowTitle("Torqeedo Programmer")
        self.setGeometry(100, 100, 800, 600)  # Taille initiale de la fenêtre
        self.initUI()

    def initUI(self):
        # Widget central qui contiendra tout le layout
        centralWidget = QWidget()
        self.setCentralWidget(centralWidget)

        # Layout principal horizontal
        mainLayout = QHBoxLayout()

        # Section de gauche pour la sélection du tracker
        leftLayout = QVBoxLayout()
        leftLayout.addWidget(QLabel("Sélection du Tracker"))
        # Ajoutez ici vos éléments de sélection du tracker...

        # Section centrale pour les réglages
        centerLayout = QVBoxLayout()
        centerLayout.addWidget(QLabel("Réglages"))
        # Ajoutez ici vos éléments de réglage...

        # Section de droite pour les résultats
        rightLayout = QVBoxLayout()
        rightLayout.addWidget(QLabel("Résultats"))
        # Ajoutez ici vos éléments pour afficher les résultats...

        # Ajout des layouts sectionnels au layout principal
        mainLayout.addLayout(leftLayout)
        mainLayout.addLayout(centerLayout)
        mainLayout.addLayout(rightLayout)

        # Assignation du layout principal au widget central
        centralWidget.setLayout(mainLayout)

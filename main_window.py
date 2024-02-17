from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
)
from compilation_result_widget import CompilationResultWidget
from controller_selection_widget import ControllerSelectionWidget
from download_firmware_widget import DownloadFirmwareWidget
from serial_device_selection_widget import SerialDeviceSelectionWidget
from torqeedo_programmer import TorqeedoProgrammer


class MainWindow(QMainWindow):
    def __init__(self, torqeedo_programmer):
        super().__init__()
        self.torqeedo_programmer: TorqeedoProgrammer = torqeedo_programmer
        self.setWindowTitle("Torqeedo Programmer")
        self.setGeometry(100, 100, 1400, 800)  # Taille initiale de la fenêtre
        self.initUI(torqeedo_programmer)

    def initUI(self, torqeedo_programmer: TorqeedoProgrammer):
        print("Initialisation de l'interface utilisateur principale...")
        # Widget central qui contiendra tout le layout
        centralWidget = QWidget()
        self.setCentralWidget(centralWidget)

        # Layout principal horizontal
        mainLayout = QHBoxLayout()

        # Section de gauche pour la sélection du tracker
        leftLayout = QVBoxLayout()
        leftLayout.addWidget(QLabel("Sélection du Tracker"))
        # Utiliser le widget de sélection dans la colonne de gauche
        controller_device_selection_widget = ControllerSelectionWidget(
            torqeedo_programmer
        )
        leftLayout.addWidget(controller_device_selection_widget)

        serial_device_selection_widget = SerialDeviceSelectionWidget(
            torqeedo_programmer
        )
        leftLayout.addWidget(serial_device_selection_widget)

        # Section centrale pour les réglages
        centerLayout = QVBoxLayout()
        centerLayout.addWidget(QLabel("Réglages"))

        download_firmware_widget = DownloadFirmwareWidget(torqeedo_programmer)
        centerLayout.addWidget(download_firmware_widget)

        # Section de droite pour les résultats
        rightLayout = QVBoxLayout()
        rightLayout.addWidget(QLabel("Résultats"))

        compilation_result_widget = CompilationResultWidget(
            torqeedo_programmer
        )
        rightLayout.addWidget(compilation_result_widget)

        # Ajout des layouts sectionnels au layout principal
        mainLayout.addLayout(leftLayout)
        mainLayout.addLayout(centerLayout)
        mainLayout.addLayout(rightLayout)

        # Assignation du layout principal au widget central
        centralWidget.setLayout(mainLayout)

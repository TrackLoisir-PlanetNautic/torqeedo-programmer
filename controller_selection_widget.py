from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QComboBox,
    QCheckBox,
    QLineEdit,
    QPushButton,
)
from new.torqeedo_programmer import TorqeedoProgrammer

class ControllerSelectionWidget(QWidget):
    def __init__(self, torqeedo_programmer: TorqeedoProgrammer, parent=None):
        super().__init__(parent)
        self.torqeedo_programmer = torqeedo_programmer
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)

        # Checkbox pour filtrer par lastPing
        self.lastPingCheckBox = QCheckBox("Nouveaux boitiers uniquement")
        self.lastPingCheckBox.stateChanged.connect(self.onFilterChange)
        layout.addWidget(self.lastPingCheckBox)

        # QLineEdit pour la recherche
        self.searchLineEdit = QLineEdit()
        self.searchLineEdit.setPlaceholderText("Recherchez par kingwoId...")
        self.searchLineEdit.textChanged.connect(self.onFilterChange)
        layout.addWidget(self.searchLineEdit)

        # Liste déroulante pour les kingwoIds
        self.controllerComboBox = QComboBox()
        layout.addWidget(self.controllerComboBox)

        # Bouton de rafraîchissement
        self.refreshButton = QPushButton("Rafraîchir la liste")
        self.refreshButton.clicked.connect(self.refreshControllerList)
        layout.addWidget(self.refreshButton)

        # Peuplement initial
        self.onFilterChange()

    def onFilterChange(self):
        # Méthode appelée lorsque le filtre change
        self.updateControllerList()
        self.selectFirstControllerAndUpdate()

    def updateControllerList(self):
        self.controllerComboBox.clear()

        filteredControllers = [
            controller for controller in self.torqeedo_programmer.torqeedo_controllers
            if (not self.lastPingCheckBox.isChecked() or controller.lastPing == 0)
            and (self.searchLineEdit.text().lower() in controller.kingwoId.lower())
        ]

        for controller in filteredControllers:
            self.controllerComboBox.addItem(controller.kingwoId, controller)

    def refreshControllerList(self):
        # Appel à l'API pour obtenir la liste mise à jour des contrôleurs
        try:
            self.torqeedo_programmer.torqeedo_controllers = self.torqeedo_programmer.api.getTorqeedoControllersList()
            self.updateControllerList()
            self.selectFirstControllerAndUpdate()
            print("Liste des contrôleurs mise à jour avec succès.")
        except Exception as e:
            print(f"Erreur lors de la mise à jour des contrôleurs : {e}")

    def selectFirstControllerAndUpdate(self):
        # Sélectionne le premier contrôleur de la liste et met à jour selected_controller
        if self.controllerComboBox.count() > 0:
            self.controllerComboBox.setCurrentIndex(0)
            selectedController = self.controllerComboBox.currentData()
            self.torqeedo_programmer.selected_controller = selectedController
            print(f"Contrôleur sélectionné : {self.torqeedo_programmer.selected_controller.kingwoId}")
        else:
            self.torqeedo_programmer.selected_controller = None
            print("Aucun contrôleur sélectionné.")

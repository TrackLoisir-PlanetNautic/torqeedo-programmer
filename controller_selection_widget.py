from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QComboBox,
    QCheckBox,
    QLineEdit,
    QPushButton,
)


class ControllerSelectionWidget(QWidget):
    def __init__(self, torqeedo_programmer, parent=None):
        super().__init__(parent)
        self.torqeedo_programmer = torqeedo_programmer
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)

        # Checkbox pour filtrer par lastPing
        self.lastPingCheckBox = QCheckBox("Nouveaux boitiers uniquement")
        self.lastPingCheckBox.stateChanged.connect(self.updateControllerList)
        layout.addWidget(self.lastPingCheckBox)

        # QLineEdit pour la recherche
        self.searchLineEdit = QLineEdit()
        self.searchLineEdit.setPlaceholderText("Recherchez par kingwoId...")
        self.searchLineEdit.textChanged.connect(self.updateControllerList)
        layout.addWidget(self.searchLineEdit)

        # Liste déroulante pour les kingwoIds
        self.controllerComboBox = QComboBox()
        layout.addWidget(self.controllerComboBox)

        # Bouton de rafraîchissement
        self.refreshButton = QPushButton("Rafraîchir la liste")
        self.refreshButton.clicked.connect(self.refreshControllerList)
        layout.addWidget(self.refreshButton)

        # Peuplement initial
        self.updateControllerList()

    def updateControllerList(self):
        self.controllerComboBox.clear()

        for controller in self.torqeedo_programmer.torqeedo_controllers:
            if (
                not self.lastPingCheckBox.isChecked()
                or controller.lastPing == 0
            ) and (
                self.searchLineEdit.text().lower()
                in controller.kingwoId.lower()
            ):
                self.controllerComboBox.addItem(controller.kingwoId)

    def refreshControllerList(self):
        # Appel à l'API pour obtenir la liste mise à jour des contrôleurs
        try:
            self.torqeedo_programmer.torqeedo_controllers = (
                self.torqeedo_programmer.api.getTorqeedoControllersList()
            )
            self.updateControllerList()  # Mise à jour de la liste des contrôleurs dans l'interface utilisateur
            print("Liste des contrôleurs mise à jour avec succès.")
        except Exception as e:
            print(f"Erreur lors de la mise à jour des contrôleurs : {e}")

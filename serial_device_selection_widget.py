from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QComboBox,
    QPushButton,
)
from new.torqeedo_programmer import TorqeedoProgrammer
import serial
import serial.tools.list_ports


class SerialDeviceSelectionWidget(QWidget):
    def __init__(self, torqeedo_programmer: TorqeedoProgrammer, parent=None):
        super().__init__(parent)
        self.torqeedo_programmer = torqeedo_programmer
        self.initUI()

    def click_refreshSerialList(self):
        self.serialPortsComboBox.clear()
        self.SerialPortsReady = []
        myports = [tuple(p) for p in list(serial.tools.list_ports.comports())]
        for port in myports:
            if port[1].__contains__("CP2102"):
                print("a port seems usable for programming : " + port[0])
                self.serialPortsComboBox.addItems([port[0]])
                self.SerialPortsReady.append(port[0])
        if len(myports) == 0:
            print(
                "No port ready for programming, please check port connection"
            )

    def click_connectProgrammer(self):
        if self.serialPortsComboBox.currentIndex() < 0:
            self.torqeedo_programmer.selected_serial_port = None
            print("Selected Serial port : None")
            return
        self.torqeedo_programmer.selected_serial_port = self.SerialPortsReady[
            self.serialPortsComboBox.currentIndex()
        ]
        print("debug victor")
        print(self.serialPortsComboBox.currentIndex())
        print(self.SerialPortsReady)

        print(
            "Selected Serial port : "
            + str(self.torqeedo_programmer.selected_serial_port)
        )
        # self.activate()

    def initUI(self):
        layout = QVBoxLayout(self)

        self.refreshBtn = QPushButton()
        self.refreshBtn.setText("Refresh Serial Ports")
        self.refreshBtn.clicked.connect(self.click_refreshSerialList)

        self.SerialPortsList = ["Select"]
        self.serialPortsComboBox = QComboBox()
        self.serialPortsComboBox.addItems(self.SerialPortsList)
        self.serialPortsComboBox.setEditable(True)

        self.connectProgrammer = QPushButton()
        self.connectProgrammer.setText("Connect to programmer")
        self.connectProgrammer.clicked.connect(self.click_connectProgrammer)

        layout.addWidget(self.refreshBtn)
        layout.addWidget(self.serialPortsComboBox)
        layout.addWidget(self.connectProgrammer)

        self.click_refreshSerialList()

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

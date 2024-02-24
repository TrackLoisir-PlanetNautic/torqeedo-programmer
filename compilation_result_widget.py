from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
)
from pydantic import BaseModel
from typing import List
from new.torqeedo_programmer import TorqeedoProgrammer


# Widget pour afficher CompilationResult
class CompilationResultWidget(QWidget):
    def __init__(self, torqeedo_programmer: TorqeedoProgrammer, parent=None):
        super().__init__(parent)
        self.torqeedo_programmer = torqeedo_programmer
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)

        if self.torqeedo_programmer.compilation_result is None:
            # Affichage si aucune compilation n'a été effectuée
            layout.addWidget(QLabel("Click on Restart ESP32 for a result"))
        else:
            layout.addWidget(QLabel("Click on Restart ESP32 for a result"))
            # Affichage des résultats de compilation

            def checkPartTableArray(self, partArray):
                if partArray == [
                    ["0", "nvs", "WiFi", "data", "01", "02", "00018000"],
                    ["1", "otadata", "OTA", "data", "01", "00", "0001e000"],
                    ["2", "app0", "OTA", "app", "00", "10", "00020000"],
                    ["3", "app1", "OTA", "app", "00", "11", "00200000"],
                    ["4", "spiffs", "Unknown", "data", "01", "82", "003f0000"],
                ]:
                    return True
                return False

            attributes = [
                "secureBootV2EnabledBootloader",
                "secureBootV2CheckOKBootloader",
                "secureBootV2EnabledBootloaderStage2",
                "secureBootV2CheckOKFirmware",
                "projectName",
                "AES128_KEY",
                "VERSION_NUMBER",
                "TRACKER_GPS_ID",
                "WIFI_BACKUP_SSID",
                "MODE",
                "REAL_COMPILATION_TIME",
                "DEBUG",
                "partTableDesc",
                "error",
            ]

            for attr in attributes:
                if attr == "partTableDesc":
                    value = checkPartTableArray(
                        self,
                        self.torqeedo_programmer.compilation_result.partTableDesc,
                    )
                else:
                    value = getattr(
                        self.torqeedo_programmer.compilation_result,
                        attr,
                        "Non défini",
                    )
                if isinstance(value, list):
                    value = ", ".join(value)
                elif isinstance(value, bool):
                    value = "Oui" if value else "Non"
                layout.addWidget(
                    QLabel(f"{attr.replace('_', ' ').capitalize()}: {value}")
                )

        self.setLayout(layout)

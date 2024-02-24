import asyncio
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QComboBox,
    QPushButton,
    QProgressBar,
    QLabel
)
from new.torqeedo_programmer import TorqeedoProgrammer
import serial
import serial.tools.list_ports


class DownloadFirmwareWidget(QWidget):
    def __init__(self, torqeedo_programmer: TorqeedoProgrammer, parent=None):
        super().__init__(parent)
        self.torqeedo_programmer = torqeedo_programmer
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)

        self.downloadContentBtn = QPushButton()
        self.downloadContentBtn.setText("Download content")
        self.downloadContentBtn.clicked.connect(self.start_download_firmware)

        self.downloadProgress = QProgressBar()

        self.labelDownloadContent = QLabel("Not downloaded")

        layout.addWidget(self.downloadContentBtn)
        layout.addWidget(self.downloadProgress)

    def start_download_firmware(self):
        asyncio.create_task(
            self.torqeedo_programmer.api.download_firmware(
                str(self.torqeedo_programmer.selected_controller.torqCtrlId)
            )
        )

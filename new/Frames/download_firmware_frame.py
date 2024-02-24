from tkinter.ttk import (
    Label,
    Button,
    Frame,
    Combobox,
)
from torqeedo_programmer import TorqeedoProgrammer
import serial
import serial.tools.list_ports


def refresh_serial_ports(combo: Combobox):
    combo["values"] = []  # Effacer la liste actuelle
    ports = serial.tools.list_ports.comports()
    usable_ports = [
        port.device for port in ports if "CP2102" in port.description
    ]
    combo["values"] = usable_ports
    if usable_ports:
        combo.current(0)  # Sélectionner le premier port trouvé
    else:
        combo.set("Aucun connecteur trouvé")


# Fonction pour connecter le programmeur
def download_firmware(
    torqeedo_programmer: TorqeedoProgrammer
):
    print("download_firmware")


def render_download_firmware_frame(
    middle_column_frame: Frame, torqeedo_programmer: TorqeedoProgrammer
):
    middle_column_frame.pack(side="left", expand=True, fill="both")
    # Widget pour la sélection du port série
    serial_ports_label = Label(middle_column_frame, text="Download")
    serial_ports_label.pack(padx=10, pady=5)
    # Bouton pour connecter au programmeur
    download_button = Button(
        middle_column_frame,
        text="Télécharger le firmware",
        command=lambda: download_firmware(torqeedo_programmer),
    )
    download_button.pack(padx=10, pady=10)

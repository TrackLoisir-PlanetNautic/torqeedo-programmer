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
def connect_programmer(
    combo: Combobox, torqeedo_programmer: TorqeedoProgrammer
):
    selected_port = combo.get()
    if selected_port:
        torqeedo_programmer.selected_serial_port = selected_port
        print(f"Selected Serial port : {selected_port}")
    else:
        print("No port selected")


def render_select_serial_device_frame(
    first_column_frame: Frame, torqeedo_programmer: TorqeedoProgrammer
):
    first_column_frame.pack(
        side="left", expand=True, fill="both"
    )
    # Widget pour la sélection du port série
    serial_ports_label = Label(first_column_frame, text="Sélection du port")
    serial_ports_label.pack(padx=10, pady=5)
    serial_ports_combo = Combobox(first_column_frame)
    serial_ports_combo.pack(padx=10, pady=5)
    refresh_button = Button(
        first_column_frame,
        text="Rafraîchir la liste",
        command=lambda: refresh_serial_ports(serial_ports_combo),
    )
    refresh_button.pack(padx=10, pady=5)

    # Bouton pour connecter au programmeur
    connect_button = Button(
        first_column_frame,
        text="Connection au programmeur",
        command=lambda: connect_programmer(
            serial_ports_combo, torqeedo_programmer
        ),
    )
    connect_button.pack(padx=10, pady=10)

    # Initialiser la liste des ports séries au démarrage
    refresh_serial_ports(serial_ports_combo)

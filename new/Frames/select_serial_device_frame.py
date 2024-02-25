from tkinter.ttk import (
    Label,
    Button,
    Frame,
    Combobox,
)
from torqeedo_programmer import TorqeedoProgrammer
import serial
import serial.tools.list_ports


def refresh_serial_ports(
    combo: Combobox, torqeedo_programmer: TorqeedoProgrammer
):
    combo["values"] = []  # Effacer la liste actuelle
    ports = serial.tools.list_ports.comports()
    usable_ports = [
        port.device for port in ports if "CP2102" in port.description
    ]
    combo["values"] = usable_ports
    if usable_ports:
        torqeedo_programmer.selected_serial_port = usable_ports[0]
        combo.current(0)
        print(
            f"Selected Serial port : {torqeedo_programmer.selected_serial_port}"
        )
    else:
        combo.set("Aucun connecteur trouvé")


def on_combobox_input(
    combo: Combobox, torqeedo_programmer: TorqeedoProgrammer
):
    selected = combo.get()
    if selected != "Aucun connecteur trouvé":
        torqeedo_programmer.selected_serial_port = combo.get()
        print(
            f"Selected Serial port : {torqeedo_programmer.selected_serial_port}"
        )


def render_select_serial_device_frame(
    first_column_frame: Frame, torqeedo_programmer: TorqeedoProgrammer
):
    first_column_frame.pack(side="left", expand=True, fill="both")
    # Widget pour la sélection du port série
    serial_ports_label = Label(first_column_frame, text="Sélection du port")
    serial_ports_label.pack(padx=10, pady=5)
    serial_ports_combo = Combobox(
        first_column_frame,
        postcommand=lambda: on_combobox_input(
            serial_ports_combo, torqeedo_programmer
        ),
    )
    serial_ports_combo.pack(padx=10, pady=5)
    refresh_button = Button(
        first_column_frame,
        text="Rafraîchir la liste",
        command=lambda: refresh_serial_ports(
            serial_ports_combo, torqeedo_programmer
        ),
    )
    refresh_button.pack(padx=10, pady=5)

    # Initialiser la liste des ports séries au démarrage
    refresh_serial_ports(serial_ports_combo, torqeedo_programmer)

import asyncio
from tkinter.ttk import Label, Button, Frame, Combobox, Progressbar
from torqeedo_programmer import TorqeedoProgrammer
import serial
import serial.tools.list_ports
from tkinter import IntVar


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
def download_firmware_clicked(
    torqeedo_programmer: TorqeedoProgrammer,
    update_dowload_firm_progress_bar: callable,
    progress_var: IntVar,
    download_status_label: Label,
):
    torqeedo_programmer.firmware_download_status = "in_progress"
    print("download_firmware")
    progress_var.set(0)
    asyncio.ensure_future(
        torqeedo_programmer.api.download_firmware(
            torqeedo_programmer.selected_controller,
            update_dowload_firm_progress_bar,
            download_status_label,
            torqeedo_programmer.firmware_download_status,
        )
    )


def render_download_firmware_frame(
    middle_column_frame: Frame, torqeedo_programmer: TorqeedoProgrammer
):
    progress_var = IntVar()
    progress_var.set(0)
    current_step = IntVar()
    current_step.set(0)

    def update_dowload_firm_progress_bar(chunk_size, total_length, step):
        current = progress_var.get()
        if step != current_step.get():
            current_step.set(step)
            current += 25
        progress_var.set(current + chunk_size / total_length * 100)

    download_firmware_label = Label(middle_column_frame, text="Download")
    download_firmware_label.pack(padx=10, pady=5)
    # Bouton pour connecter au programmeur
    download_button = Button(
        middle_column_frame,
        text="Télécharger le firmware",
        command=lambda: download_firmware_clicked(
            torqeedo_programmer,
            update_dowload_firm_progress_bar,
            progress_var,
            download_status_label,
        ),
    )
    download_button.pack(padx=10, pady=10)
    progress_bar = Progressbar(
        middle_column_frame,
        orient="horizontal",
        length=200,
        mode="determinate",
        variable=progress_var,
    )
    progress_bar.pack(padx=10, pady=5)

    download_status_label = Label(
        middle_column_frame,
        text="Veuillez sélectionner un identifiant de contrôleur",
    )
    download_status_label.pack(padx=10, pady=5)

    def check_controller_selected():
        if torqeedo_programmer.selected_controller is None:
            progress_var.set(0)
            current_step.set(0)
            download_button["state"] = "disabled"
            download_status_label.config(
                text="Veuillez sélectionner un identifiant de contrôleur"
            )
        else:
            download_button["state"] = "normal"
            if torqeedo_programmer.firmware_download_status == "no":
                download_status_label.config(text="Firmware non téléchargé")
                progress_var.set(0)
                current_step.set(0)
        middle_column_frame.after(
            100, check_controller_selected
        )  # Check every 100ms

    check_controller_selected()

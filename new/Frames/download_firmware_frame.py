import asyncio
from tkinter.ttk import Label, Button, Frame, Progressbar
from torqeedo_programmer import TorqeedoProgrammer
from torqeedo_controller import TorqeedoController, DownloadFirmwareStatus
from tkinter import IntVar, DoubleVar


# Fonction pour connecter le programmeur
def download_firmware_clicked(
    torqeedo_programmer: TorqeedoProgrammer,
    update_dowload_firm_progress_bar: callable,
    progress_var: DoubleVar,
    download_status_label: Label,
):
    torqeedo_programmer.selected_controller.firmware_download_status = (
        DownloadFirmwareStatus.IN_PROGRESS
    )
    print("download_firmware")
    progress_var.set(0)
    asyncio.ensure_future(
        torqeedo_programmer.api.download_firmware(
            torqeedo_programmer.selected_controller,
            update_dowload_firm_progress_bar,
            download_status_label,
        )
    )


def render_download_firmware_frame(
    middle_column_frame: Frame, torqeedo_programmer: TorqeedoProgrammer
):
    progress_var = DoubleVar()
    progress_var.set(0)
    current_step = IntVar()
    current_step.set(0)
    step_progress = DoubleVar()
    step_progress.set(0)

    def update_dowload_firm_progress_bar(chunk_size, total_length, step):
        if step != current_step.get():
            current_step.set(step)
            step_progress.set(0)
        current_chunck = step_progress.get()
        step_progress.set((current_chunck + chunk_size * 100 / total_length))
        progress_var.set(current_step.get() * 25 + step_progress.get() / 4)

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

            if (
                torqeedo_programmer.selected_controller.firmware_download_status
                == DownloadFirmwareStatus.NOT_STARTED
            ):
                download_status_label.config(text="Firmware non téléchargé")
                progress_var.set(0)
                current_step.set(0)
        middle_column_frame.after(
            100, check_controller_selected
        )  # Check every 100ms

    check_controller_selected()

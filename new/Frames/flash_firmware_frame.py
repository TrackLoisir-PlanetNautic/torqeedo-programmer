import asyncio
from tkinter.ttk import Label, Button, Frame, Progressbar
from status import (
    BootloaderFlashedStatus,
    FirmwareFlashedStatus,
    BurnHashKeyStatus,
)
from torqeedo_programmer import TorqeedoProgrammer
from tkinter import IntVar, messagebox
import threading
import queue


class Dict2Class(object):

    def __init__(self, my_dict):

        for key in my_dict:
            setattr(self, key, my_dict[key])


async def flash_firmware(
    torqeedo_programmer: TorqeedoProgrammer, progress_queue: queue.Queue
):
    print("flash_firmware_clicked")

    firmware = open("./downloads/firmware_tmp", "rb")

    # Namespace(chip='auto', port=None, baud=460800, before='default_reset', after='hard_reset', no_stub=False, trace=False, override_vddsdio=None, connect_attempts=7, operation='write_flash', addr_filename=[(131072, <_io.BufferedReader name='firmware_tmp'>)], erase_all=False,
    # flash_freq='80m', flash_mode='dio', flash_size='4MB', spi_connection=None, no_progress=False, verify=False, encrypt=False, encrypt_files=None, ignore_flash_encryption_efuse_setting=False, force=False, compress=None, no_compress=False)
    args = {
        "baud": 1000000,  # VICTOR
        "compress": True,  # VICTOR
        "flash_size": "16MB",  # VICTOR 4MB -> 16MB
        "flash_mode": "dio",
        "flash_freq": "80m",
        "no_compress": False,
        "force": False,
        "addr_filename": [(131072, firmware)],
        "encrypt": None,
        "encrypt_files": None,
        "ignore_flash_encryption_efuse_setting": None,
        "erase_all": False,
        "no_stub": False,
        "verify": None,
    }
    args = Dict2Class(args)
    print(args)
    print(torqeedo_programmer.selected_controller.esp_rom)
    if not torqeedo_programmer.selected_controller.esp_rom.esp.IS_STUB:
        torqeedo_programmer.selected_controller.esp_rom.esp = (
            torqeedo_programmer.selected_controller.esp_rom.esp.run_stub()
        )

    # Ensuring the ESP tool runs in a non-blocking way
    def run_write_flash(progress_queue):
        def update_progress(value):
            if value == -1:
                torqeedo_programmer.selected_controller.esp_rom = None
                torqeedo_programmer.selected_controller.burn_hash_key_status = (
                    BurnHashKeyStatus.NOT_SCANNED
                )
                torqeedo_programmer.selected_controller.bootloader_flashed_status = (
                    BootloaderFlashedStatus.NOT_FLASHED
                )
                torqeedo_programmer.selected_controller.firmware_flashed_status = (
                    FirmwareFlashedStatus.NOT_FLASHED
                )
                torqeedo_programmer.selected_controller.esp_rom = None
                torqeedo_programmer.selected_controller.compilation_result = (
                    None
                )
                progress_queue.put(("error", "Firmware flashing failed."))
                progress_queue.put(("progress", 0))
            else:
                progress_queue.put(("progress", value))

        torqeedo_programmer.selected_controller.esp_rom.write_flash(
            args, update_progress
        )

    # Run the blocking operation in a separate thread
    thread = threading.Thread(target=run_write_flash, args=(progress_queue,))
    thread.start()
    while thread.is_alive():
        await asyncio.sleep(0.1)
    torqeedo_programmer.selected_controller.firmware_flashed_status = (
        FirmwareFlashedStatus.FLASHED
    )


def flash_firmware_clicked(
    torqeedo_programmer: TorqeedoProgrammer,
    progress_queue: queue.Queue,
    progress_var: IntVar,
):
    progress_var.set(0)

    torqeedo_programmer.selected_controller.firmware_flashed_status = (
        FirmwareFlashedStatus.IN_PROGRESS
    )
    asyncio.ensure_future(flash_firmware(torqeedo_programmer, progress_queue))


def render_flash_firmware_frame(
    middle_column_frame: Frame,
    torqeedo_programmer: TorqeedoProgrammer,
):
    progress_var = IntVar()
    progress_var.set(0)

    flash_firmware_label = Label(middle_column_frame, text="Flash firmware")
    flash_firmware_label.pack(padx=10, pady=5)
    # Bouton pour connecter au programmeur
    progress_queue = queue.Queue()

    flash_firmware_button = Button(
        middle_column_frame,
        text="Flash firmware",
        command=lambda: flash_firmware_clicked(
            torqeedo_programmer,
            progress_queue,
            progress_var,
        ),
    )
    flash_firmware_button.pack(padx=10, pady=10)
    progress_bar = Progressbar(
        middle_column_frame,
        orient="horizontal",
        length=200,
        mode="determinate",
        variable=progress_var,
    )
    progress_bar.pack(padx=10, pady=5)

    flash_firmware_status_label = Label(
        middle_column_frame, text="Not flashed"
    )
    flash_firmware_status_label.pack(padx=10, pady=5)

    def check_flash_firmware_status():
        try:
            message, value = progress_queue.get_nowait()
            if message == "error":
                messagebox.showerror(
                    "Erreur",
                    "Erreur lors du flash du firmware, la carte a été déconnectée. Veuillez la reconnecter et réessayer.",
                )
            elif message == "progress":
                progress_var.set(value)
        except queue.Empty:
            pass  # Do nothing if the queue is empty
        if torqeedo_programmer.selected_controller is None:
            progress_var.set(0)
            flash_firmware_button["state"] = "disabled"
            flash_firmware_status_label.config(
                text="Veuillez sélectionner un identifiant de contrôleur"
            )
        elif torqeedo_programmer.selected_controller.esp_rom is None:
            progress_var.set(0)
            flash_firmware_button["state"] = "disabled"
            flash_firmware_status_label.config(
                text="Non connecté à la carte electronique"
            )
        elif (
            torqeedo_programmer.selected_controller.bootloader_flashed_status
            != (BootloaderFlashedStatus.FLASHED)
        ):
            progress_var.set(0)
            flash_firmware_button["state"] = "disabled"
            flash_firmware_status_label.config(
                text="Veuillez flasher le bootloader avant"
            )
        elif (
            torqeedo_programmer.selected_controller.firmware_flashed_status
            == FirmwareFlashedStatus.NOT_FLASHED
        ):
            progress_var.set(0)
            flash_firmware_button["state"] = "normal"
            flash_firmware_status_label.config(text="Not flashed")
        elif (
            torqeedo_programmer.selected_controller.firmware_flashed_status
            == FirmwareFlashedStatus.IN_PROGRESS
        ):
            flash_firmware_button["state"] = "disabled"
            flash_firmware_status_label.config(
                text="En cours (Temps estimé 1min30)"
            )
        elif (
            torqeedo_programmer.selected_controller.firmware_flashed_status
            == FirmwareFlashedStatus.FLASHED
        ):
            flash_firmware_button["state"] = "disabled"
            flash_firmware_status_label.config(text="Firmware flashed")

        middle_column_frame.after(
            100, check_flash_firmware_status
        )  # Check every 100ms

    check_flash_firmware_status()

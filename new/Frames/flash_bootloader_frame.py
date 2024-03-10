import asyncio
from tkinter.ttk import Label, Button, Frame, Progressbar
from torqeedo_programmer import TorqeedoProgrammer
from tkinter import IntVar, messagebox
from torqeedo_controller import (
    BootloaderFlashedStatus,
    FirmwareFlashedStatus,
    BurnHashKeyStatus,
    ConnectToPcbStatus,
)
import threading
import queue


class Dict2Class(object):

    def __init__(self, my_dict):

        for key in my_dict:
            setattr(self, key, my_dict[key])


async def flash_bootload(
    torqeedo_programmer: TorqeedoProgrammer, progress_queue: queue.Queue
):
    print("flash_bootloader_clicked")

    part_table = open("./downloads/part_table_tmp", "rb")
    bootloader = open("./downloads/bootloader_tmp", "rb")

    # Namespace(chip='auto', port=None, baud=460800, before='default_reset', after='hard_reset', no_stub=False, trace=False, override_vddsdio=None, connect_attempts=7, operation='write_flash', addr_filename=[(131072, <_io.BufferedReader name='firmware_tmp'>)], erase_all=False,
    # flash_freq='80m', flash_mode='dio', flash_size='4MB', spi_connection=None, no_progress=False, verify=False, encrypt=False, encrypt_files=None, ignore_flash_encryption_efuse_setting=False, force=False, compress=None, no_compress=False)
    args = {
        "chip": "esp32",
        "compress": None,
        "flash_mode": "dio",
        "flash_freq": "80m",
        "no_compress": False,
        "force": True,
        "addr_filename": [(94208, part_table), (4096, bootloader)],
        "encrypt": None,
        "encrypt_files": None,
        "ignore_flash_encryption_efuse_setting": None,
        "flash_size": "4MB",
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
                torqeedo_programmer.selected_controller.connect_to_pcb_status = (
                    ConnectToPcbStatus.NOT_CONNECTED
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
    torqeedo_programmer.selected_controller.bootloader_flashed_status = (
        BootloaderFlashedStatus.FLASHED
    )


def flash_bootloader_clicked(
    torqeedo_programmer: TorqeedoProgrammer,
    progress_queue: queue.Queue,
    progress_var: IntVar,
):
    progress_var.set(0)

    torqeedo_programmer.selected_controller.bootloader_flashed_status = (
        BootloaderFlashedStatus.IN_PROGRESS
    )
    asyncio.ensure_future(flash_bootload(torqeedo_programmer, progress_queue))


def render_flash_bootloader_frame(
    middle_column_frame: Frame,
    torqeedo_programmer: TorqeedoProgrammer,
):
    progress_var = IntVar()
    progress_var.set(0)

    flash_bootloader_label = Label(
        middle_column_frame, text="Flash bootloader and part table"
    )
    flash_bootloader_label.pack(padx=10, pady=5)
    # Bouton pour connecter au programmeur
    progress_queue = queue.Queue()

    flash_bootloader_button = Button(
        middle_column_frame,
        text="Flash bootloader and part table",
        command=lambda: flash_bootloader_clicked(
            torqeedo_programmer,
            progress_queue,
            progress_var,
        ),
    )
    flash_bootloader_button.pack(padx=10, pady=10)
    progress_bar = Progressbar(
        middle_column_frame,
        orient="horizontal",
        length=200,
        mode="determinate",
        variable=progress_var,
    )
    progress_bar.pack(padx=10, pady=5)

    flash_bootloader_status_label = Label(
        middle_column_frame, text="Not flashed"
    )
    flash_bootloader_status_label.pack(padx=10, pady=5)

    def check_flash_bootloader_status():
        try:
            message, value = progress_queue.get_nowait()
            if message == "error":
                messagebox.showerror(
                    "Erreur",
                    "Erreur lors du flashage du bootloader, la carte a été déconnectée. Veuillez la reconnecter et réessayer.",
                )
            elif message == "progress":
                progress_var.set(value)
        except queue.Empty:
            pass  # Do nothing if the queue is empty
        if torqeedo_programmer.selected_controller is None:
            progress_var.set(0)
            flash_bootloader_button["state"] = "disabled"
            flash_bootloader_status_label.config(
                text="Veuillez sélectionner un identifiant de contrôleur"
            )
        elif torqeedo_programmer.selected_controller.esp_rom is None:
            progress_var.set(0)
            flash_bootloader_button["state"] = "disabled"
            flash_bootloader_status_label.config(
                text="Non connecté à la carte electronique"
            )
        elif (
            torqeedo_programmer.selected_controller.bootloader_flashed_status
            == BootloaderFlashedStatus.NOT_FLASHED
        ):
            progress_var.set(0)
            flash_bootloader_button["state"] = "normal"
            flash_bootloader_status_label.config(text="Not flashed")
        elif (
            torqeedo_programmer.selected_controller.bootloader_flashed_status
            == BootloaderFlashedStatus.IN_PROGRESS
        ):
            flash_bootloader_button["state"] = "disabled"
            flash_bootloader_status_label.config(text="In progress")
        elif (
            torqeedo_programmer.selected_controller.bootloader_flashed_status
            == BootloaderFlashedStatus.FLASHED
        ):
            flash_bootloader_button["state"] = "disabled"
            flash_bootloader_status_label.config(
                text="Bootloader and part table flashed"
            )

        middle_column_frame.after(
            100, check_flash_bootloader_status
        )  # Check every 100ms

    check_flash_bootloader_status()

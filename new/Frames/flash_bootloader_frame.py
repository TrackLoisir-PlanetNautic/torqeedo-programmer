import asyncio
from tkinter.ttk import Label, Button, Frame, Progressbar
from torqeedo_programmer import TorqeedoProgrammer
from tkinter import IntVar


class Dict2Class(object):

    def __init__(self, my_dict):

        for key in my_dict:
            setattr(self, key, my_dict[key])


def flash_bootloader_clicked(
    torqeedo_programmer: TorqeedoProgrammer,
    update_flash_bootloader_form_progress_bar: callable,
    progress_var: IntVar,
    flash_bootloader_status_label: Label,
):

    flash_bootloader_status_label.config(
        text="Flashing bootloader and part table"
    )
    print("flash_bootloader_clicked")
    progress_var.set(0)
    print("part table and bootloader flash")

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
    torqeedo_programmer.selected_controller.esp_rom.write_flash(
        args, update_flash_bootloader_form_progress_bar
    )

    flash_bootloader_status_label.config(text="Flashed")


def render_flash_bootloader_frame(
    middle_column_frame: Frame,
    torqeedo_programmer: TorqeedoProgrammer,
):
    progress_var = IntVar()
    progress_var.set(0)

    def update_flash_bootloader_form_progress_bar(value):
        progress_var.set(value)

    flash_bootloader_label = Label(
        middle_column_frame, text="Flash bootloader and part table"
    )
    flash_bootloader_label.pack(padx=10, pady=5)
    # Bouton pour connecter au programmeur
    flash_bootloader_button = Button(
        middle_column_frame,
        text="Flash bootloader and part table",
        command=lambda: flash_bootloader_clicked(
            torqeedo_programmer,
            update_flash_bootloader_form_progress_bar,
            progress_var,
            flash_bootloader_status_label,
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

        middle_column_frame.after(
            100, check_flash_bootloader_status
        )  # Check every 100ms

    check_flash_bootloader_status()
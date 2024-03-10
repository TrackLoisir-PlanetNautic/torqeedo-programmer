from tkinter.ttk import Frame
from tkinter import Toplevel
from torqeedo_programmer import TorqeedoProgrammer
from Frames.select_controller_frame import render_select_controller_frame
from Frames.select_serial_device_frame import render_select_serial_device_frame
from Frames.download_firmware_frame import render_download_firmware_frame
from Frames.test_serial_connection_frame import (
    render_test_serial_connection_frame,
)
from Frames.burn_hash_key_frame import render_burn_hash_key_frame
from Frames.flash_bootloader_frame import render_flash_bootloader_frame
from Frames.flash_firmware_frame import render_flash_firmware_frame


def open_main_frame(
    root_window: Toplevel, torqeedo_programmer: TorqeedoProgrammer
):
    print("Opening main frame")

    # Création du frame principal qui contient tout
    main_frame = Frame(root_window)
    main_frame.pack(padx=20, pady=20, expand=True, fill="both")
    first_column_frame = Frame(main_frame, borderwidth=2, relief="groove")

    render_select_controller_frame(first_column_frame, torqeedo_programmer)
    render_select_serial_device_frame(first_column_frame, torqeedo_programmer)

    middle_column_frame = Frame(main_frame, borderwidth=2, relief="groove")
    middle_column_frame.pack(side="left", expand=True, fill="both")

    render_download_firmware_frame(middle_column_frame, torqeedo_programmer)
    burn_hash_key_text = "Burn Sign hash key"
    render_test_serial_connection_frame(
        middle_column_frame, torqeedo_programmer, burn_hash_key_text
    )

    render_burn_hash_key_frame(
        middle_column_frame, torqeedo_programmer, burn_hash_key_text
    )

    render_flash_bootloader_frame(middle_column_frame, torqeedo_programmer)

    render_flash_firmware_frame(middle_column_frame, torqeedo_programmer)

import asyncio
from tkinter.ttk import Label, Button, Frame, Progressbar
from torqeedo_programmer import TorqeedoProgrammer
from tkinter import IntVar


def flash_bootloader_clicked(
    torqeedo_programmer: TorqeedoProgrammer,
    update_flash_bootloader_form_progress_bar: callable,
    progress_var: IntVar,
):
    print("flash_bootloader_clicked")
    progress_var.set(0)
    asyncio.ensure_future(
        torqeedo_programmer.selected_controller.esp.burn_sign_hask_key(
            progress_var,
            update_flash_bootloader_form_progress_bar,
        )
    )


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

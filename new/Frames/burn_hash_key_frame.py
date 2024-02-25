import asyncio
from tkinter.ttk import Label, Button, Frame, Progressbar
from torqeedo_programmer import TorqeedoProgrammer
from tkinter import IntVar


def burn_hash_key_firmware_clicked(
    torqeedo_programmer: TorqeedoProgrammer,
    update_burn_hash_key_progress_bar: callable,
    progress_var: IntVar,
    burn_hash_key_status_label: Label,
):
    print("burn_hash_key")
    progress_var.set(0)
    asyncio.ensure_future(
        torqeedo_programmer.selected_controller.esp.burn_sign_hask_key(
            progress_var,
            update_burn_hash_key_progress_bar,
            burn_hash_key_status_label,
        )
    )


def render_burn_hash_key_frame(
    middle_column_frame: Frame, torqeedo_programmer: TorqeedoProgrammer
):
    progress_var = IntVar()
    progress_var.set(0)

    def update_burn_hash_key_firm_progress_bar(value):
        progress_var.set(value)

    burn_hash_key_firmware_label = Label(
        middle_column_frame, text="Burn Sign hash key"
    )
    burn_hash_key_firmware_label.pack(padx=10, pady=5)
    # Bouton pour connecter au programmeur
    burn_hash_key_button = Button(
        middle_column_frame,
        text="Burn sign hash key",
        command=lambda: burn_hash_key_firmware_clicked(
            torqeedo_programmer,
            update_burn_hash_key_firm_progress_bar,
            progress_var,
            burn_hash_key_status_label,
        ),
    )
    burn_hash_key_button.pack(padx=10, pady=10)
    progress_bar = Progressbar(
        middle_column_frame,
        orient="horizontal",
        length=200,
        mode="determinate",
        variable=progress_var,
    )
    progress_bar.pack(padx=10, pady=5)

    burn_hash_key_status_label = Label(
        middle_column_frame,
        text=torqeedo_programmer.burn_hash_key_status_label,
    )
    burn_hash_key_status_label.pack(padx=10, pady=5)

    def check_test_connexion_triggered():
        if (
            torqeedo_programmer.burn_hash_key_status_label
            != burn_hash_key_status_label.cget("text")
        ):
            burn_hash_key_status_label.config(
                text=torqeedo_programmer.burn_hash_key_status_label
            )
        # esp is defined in torqeedo_programmer.selected_controller
        if (
            torqeedo_programmer.selected_controller is not None
            and torqeedo_programmer.selected_controller.esp is not None
        ):
            progress_var.set(0)
            burn_hash_key_button["state"] = "disabled"
            burn_hash_key_status_label.config(text="No burn")
        else:
            burn_hash_key_button["state"] = "normal"
            # if torqeedo_programmer.firmware_burn_hash_key_status == "no":
            #    burn_hash_key_status_label.config(
            #        text="Firmware non téléchargé"
            #    )
            #    progress_var.set(0)
            #    current_step.set(0)
        middle_column_frame.after(
            100, check_test_connexion_triggered
        )  # Check every 100ms

    check_test_connexion_triggered()

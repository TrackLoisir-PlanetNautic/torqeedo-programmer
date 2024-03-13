import asyncio
from tkinter.ttk import Label, Button, Frame, Progressbar
from torqeedo_programmer import TorqeedoProgrammer
from status import BurnHashKeyStatus
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
        torqeedo_programmer.selected_controller.esp_rom.burn_sign_hask_key(
            torqeedo_programmer,
            update_burn_hash_key_progress_bar,
            burn_hash_key_status_label,
        )
    )


def render_burn_hash_key_frame(
    middle_column_frame: Frame,
    torqeedo_programmer: TorqeedoProgrammer,
    burn_hash_key_text: str,
):
    progress_var = IntVar()
    progress_var.set(0)

    def update_burn_hash_key_form_progress_bar(value):
        progress_var.set(value)

    # Bouton pour connecter au programmeur
    burn_hash_key_button = Button(
        middle_column_frame,
        text="Burn sign hash key",
        command=lambda: burn_hash_key_firmware_clicked(
            torqeedo_programmer,
            update_burn_hash_key_form_progress_bar,
            progress_var,
            burn_hash_key_status_label,
        ),
    )
    burn_hash_key_button.grid(row=7, column=0, padx=10, pady=10, sticky="W")

    burn_hash_key_status_label = Label(
        middle_column_frame,
        text=burn_hash_key_text,
    )
    burn_hash_key_status_label.grid(
        row=7, column=1, padx=10, pady=10, sticky="E"
    )

    progress_bar = Progressbar(
        middle_column_frame,
        orient="horizontal",
        length=300,
        mode="determinate",
        variable=progress_var,
    )
    progress_bar.grid(row=8, column=0, columnspan=2, padx=10, pady=5)

    kingwo_id_of_hash_key: str = None

    def check_burn_hash_key_status(kingwo_id_of_hash_key: str):
        if torqeedo_programmer.selected_controller is None:
            burn_hash_key_button["state"] = "disabled"
            burn_hash_key_status_label.config(
                text="Veuillez lancer la connection à une carte électronique"
            )
            progress_var.set(0)
        elif (
            torqeedo_programmer.selected_controller.burn_hash_key_status
            == BurnHashKeyStatus.BURNED_SAME
        ):
            burn_hash_key_button["state"] = "disabled"
            burn_hash_key_status_label.config(text="HashKey : Burned same")
            progress_var.set(100)
        elif (
            torqeedo_programmer.selected_controller.burn_hash_key_status
            == BurnHashKeyStatus.BURNED_NOT_SAME
        ):
            burn_hash_key_button["state"] = "disabled"
            if kingwo_id_of_hash_key is None:
                kingwo_id_of_hash_key = ""
                asyncio.ensure_future(
                    torqeedo_programmer.api.getKingwoIdFromHashkey(
                        torqeedo_programmer.selected_controller.hashkey_b64,
                        kingwo_id_of_hash_key,
                    )
                )
            burn_hash_key_status_label.config(
                text="HashKey : Burned not same" + kingwo_id_of_hash_key
            )
            progress_var.set(100)
        elif (
            torqeedo_programmer.selected_controller.burn_hash_key_status
            == BurnHashKeyStatus.ERROR
        ):
            burn_hash_key_button["state"] = "disabled"
            burn_hash_key_status_label.config(
                text="HashKey : Erreur, veuillez télécharger le firmware et réessayer"
            )
            progress_var.set(0)
        elif (
            torqeedo_programmer.selected_controller.burn_hash_key_status
            == BurnHashKeyStatus.NOT_BURNED
        ):
            burn_hash_key_button["state"] = "normal"
            burn_hash_key_status_label.config(text="HashKey : Not burned")
            progress_var.set(0)
        elif (
            torqeedo_programmer.selected_controller.burn_hash_key_status
            == BurnHashKeyStatus.NOT_SCANNED
        ):
            burn_hash_key_button["state"] = "disabled"
            kingwo_id_of_hash_key = None
            burn_hash_key_status_label.config(
                text="HashKey : Veuillez lancer la connection à une carte électronique"
            )
            progress_var.set(0)

        middle_column_frame.after(
            100, check_burn_hash_key_status, kingwo_id_of_hash_key
        )  # Check every 100ms

    check_burn_hash_key_status(kingwo_id_of_hash_key)

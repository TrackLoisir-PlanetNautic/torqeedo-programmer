import asyncio
from tkinter.ttk import Button, Frame
from torqeedo_programmer import TorqeedoProgrammer


def restart_esp_and_get_infos_clicked(
    torqeedo_programmer: TorqeedoProgrammer,
):
    torqeedo_programmer.selected_controller.esp_rom.restart()


def render_restart_esp_and_get_infos_frame(
    middle_column_frame: Frame,
    torqeedo_programmer: TorqeedoProgrammer,
):

    restart_esp_and_get_infos_button = Button(
        middle_column_frame,
        text="Restart ESP and get infos",
        command=lambda: restart_esp_and_get_infos_clicked(
            torqeedo_programmer,
        ),
    )
    restart_esp_and_get_infos_button.pack(padx=10, pady=10)

    def restart_esp_and_get_infos_status():
        if (
            torqeedo_programmer.selected_controller is None
            or torqeedo_programmer.selected_controller.esp_rom is None
        ):
            restart_esp_and_get_infos_button["state"] = "disabled"
        else:
            restart_esp_and_get_infos_button["state"] = "normal"

        middle_column_frame.after(
            100, restart_esp_and_get_infos_status
        )  # Check every 100ms

    restart_esp_and_get_infos_status()

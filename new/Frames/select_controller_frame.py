from tkinter.ttk import (
    Label,
    Button,
    Frame,
    Combobox,
    Checkbutton,
)
from tkinter import IntVar, StringVar
import asyncio
from torqeedo_programmer import TorqeedoProgrammer
from status import (
    DownloadFirmwareStatus,
    BootloaderFlashedStatus,
    BurnHashKeyStatus,
    FirmwareFlashedStatus,
)


async def get_torqeedo_controllers_async(
    torqeedo_programmer: TorqeedoProgrammer,
):
    print("get_torqeedo_controllers_async")
    try:
        torqeedo_programmer.torqeedo_controllers = (
            await torqeedo_programmer.api.getTorqeedoControllersList()
        )
    except Exception as e:
        print(e)
        return


def get_torqeedo_controllers(torqeedo_programmer: TorqeedoProgrammer):
    asyncio.ensure_future(get_torqeedo_controllers_async(torqeedo_programmer))


def refresh_controller_list(
    torqeedo_programmer: TorqeedoProgrammer,
    combo: Combobox,
    filter_last_ping: IntVar,
    filter_kingwoId: StringVar,
):
    async def refresh_and_update():
        await get_torqeedo_controllers_async(torqeedo_programmer)
        update_combobox_values(
            torqeedo_programmer, combo, filter_last_ping, filter_kingwoId
        )

    asyncio.ensure_future(refresh_and_update())


def update_combobox_values(
    torqeedo_programmer: TorqeedoProgrammer,
    kingwoId_combobox: Combobox,
    filter_last_ping: IntVar,
    filter_kingwoId: StringVar,
):
    if filter_last_ping.get() == 1:
        torqeedo_programmer.filtered_controllers = [
            c
            for c in torqeedo_programmer.torqeedo_controllers
            if c.lastPing == 0
        ]
    else:
        torqeedo_programmer.filtered_controllers = (
            torqeedo_programmer.torqeedo_controllers
        )
    if filter_kingwoId.get() != "":
        data = []
        for item in torqeedo_programmer.filtered_controllers:
            if filter_kingwoId.get().lower() in item.kingwoId.lower():
                data.append(item)
        torqeedo_programmer.filtered_controllers = data
    kingwoIds = [c.kingwoId for c in torqeedo_programmer.filtered_controllers]
    kingwoId_combobox["values"] = kingwoIds


def render_select_controller_frame(
    left_column_frame: Frame, torqeedo_programmer: TorqeedoProgrammer
):
    first_column_label = Label(
        left_column_frame, text="Selection du contrôleur"
    )
    first_column_label.pack(padx=10, pady=5)
    left_column_frame.pack(
        side="left", expand=True, fill="both", padx=10, pady=10
    )

    filter_kingwoId = StringVar()
    filter_last_ping = IntVar()
    filter_last_ping.set(1)

    # Création de la Combobox pour sélectionner kingwoId
    kingwoId_combobox = Combobox(
        left_column_frame,
        postcommand=lambda: update_combobox_values(
            torqeedo_programmer,
            kingwoId_combobox,
            filter_last_ping,
            filter_kingwoId,
        ),
    )

    def on_combobox_input(event):
        val = event.widget.get()
        filter_kingwoId.set(val)

    def on_combobox_select(event):
        selected_kingwoId = kingwoId_combobox.get()
        torqeedo_programmer.selected_controller = next(
            c
            for c in torqeedo_programmer.filtered_controllers
            if c.kingwoId == selected_kingwoId
        )
        torqeedo_programmer.selected_controller.firmware_download_status = (
            DownloadFirmwareStatus.NOT_STARTED
        )
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
        torqeedo_programmer.selected_controller.hashkey_b64 = None
        torqeedo_programmer.selected_controller.compilation_result = None

    kingwoId_combobox.bind("<KeyRelease>", on_combobox_input)
    kingwoId_combobox.bind(
        "<<ComboboxSelected>>", on_combobox_select
    )  # Bind selection event
    kingwoId_combobox.pack(padx=10, pady=5)

    # Création du bouton de rafraîchissement
    refresh_button = Button(
        left_column_frame,
        text="Rafraîchir la liste",
        command=lambda: refresh_controller_list(
            torqeedo_programmer,
            kingwoId_combobox,
            filter_last_ping,
            filter_kingwoId,
        ),
    )

    refresh_button.pack(pady=5)

    # CheckBox pour filtrer lastPing = 0
    filter_checkbox = Checkbutton(
        left_column_frame,
        text="Filtrer par lastPing = 0",
        variable=filter_last_ping,
        command=lambda: update_combobox_values(
            torqeedo_programmer,
            kingwoId_combobox,
            filter_last_ping,
            filter_kingwoId,
        ),
    )
    filter_checkbox.pack()
    filter_checkbox.pack(padx=10, pady=5)

    # Initialisation de la liste des contrôleurs
    refresh_controller_list(
        torqeedo_programmer,
        kingwoId_combobox,
        filter_last_ping,
        filter_kingwoId,
    )

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
    main_frame: Frame, torqeedo_programmer: TorqeedoProgrammer
):
    first_column_frame = Frame(main_frame, borderwidth=2, relief="groove")
    first_column_label = Label(
        first_column_frame, text="Selection du contrôleur"
    )
    filter_kingwoId = StringVar()
    filter_last_ping = IntVar()

    # Création de la Combobox pour sélectionner kingwoId
    kingwoId_combobox = Combobox(
        first_column_frame,
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
        print(torqeedo_programmer.selected_controller)

    kingwoId_combobox.bind("<KeyRelease>", on_combobox_input)
    kingwoId_combobox.bind(
        "<<ComboboxSelected>>", on_combobox_select
    )  # Bind selection event
    kingwoId_combobox.pack(padx=10, pady=10)

    # Création du bouton de rafraîchissement
    refresh_button = Button(
        first_column_frame,
        text="Rafraîchir",
        command=lambda: refresh_controller_list(
            torqeedo_programmer,
            kingwoId_combobox,
            filter_last_ping,
            filter_kingwoId,
        ),
    )
    refresh_button.pack(pady=10)

    # CheckBox pour filtrer lastPing = 0
    filter_checkbox = Checkbutton(
        first_column_frame,
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

    first_column_label.pack(padx=10, pady=10)
    first_column_frame.pack(
        side="left", expand=True, fill="both", padx=10, pady=10
    )

    # Initialisation de la liste des contrôleurs
    refresh_controller_list(
        torqeedo_programmer,
        kingwoId_combobox,
        filter_last_ping,
        filter_kingwoId,
    )

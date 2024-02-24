from tkinter.ttk import Label, Entry, Button, Frame, Style
from tkinter import Toplevel, DISABLED, NORMAL
import asyncio
from torqeedo_programmer import TorqeedoProgrammer


async def get_torqeedo_controllers_async(
    torqeedo_programmer: TorqeedoProgrammer,
):
    try:
        torqeedo_programmer.torqeedo_controllers = (
            await torqeedo_programmer.api.getTorqeedoControllersList()
        )
        print(torqeedo_programmer.torqeedo_controllers)
    except Exception as e:
        print(e)
        return


def get_torqeedo_controllers(torqeedo_programmer: TorqeedoProgrammer):
    asyncio.ensure_future(get_torqeedo_controllers_async(torqeedo_programmer))


def open_select_controller_frame(
    main_frame: Frame, torqeedo_programmer: TorqeedoProgrammer
):

    # Première colonne (Frame)
    first_column_frame = Frame(main_frame, borderwidth=2, relief="groove")
    first_column_label = Label(first_column_frame, text="Première Colonne")
    first_column_label.pack(padx=10, pady=10)
    first_column_frame.pack(
        side="left", expand=True, fill="both", padx=10, pady=10
    )
    get_torqeedo_controllers(torqeedo_programmer)

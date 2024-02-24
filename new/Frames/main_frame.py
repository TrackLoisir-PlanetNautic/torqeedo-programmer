from tkinter.ttk import Frame
from tkinter import Toplevel
from torqeedo_programmer import TorqeedoProgrammer
from Frames.select_controller_frame import open_select_controller_frame


def open_main_frame(
    root_window: Toplevel, torqeedo_programmer: TorqeedoProgrammer
):
    print("Opening main frame")

    # Création du frame principal qui contient tout
    main_frame = Frame(root_window)
    main_frame.pack(padx=20, pady=20, expand=True, fill="both")

    open_select_controller_frame(main_frame, torqeedo_programmer)
from tkinter.ttk import Frame
from tkinter import Toplevel
from torqeedo_programmer import TorqeedoProgrammer
from Frames.select_controller_frame import render_select_controller_frame
from Frames.select_serial_device_frame import render_select_serial_device_frame


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

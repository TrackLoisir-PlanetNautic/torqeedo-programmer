from tkinter.ttk import Label, Entry, Button, Frame, Style
from tkinter import Toplevel, DISABLED, NORMAL
import asyncio
from api import API


def open_select_controller_frame(main_frame: Frame, api: API):

    # Première colonne (Frame)
    first_column_frame = Frame(main_frame, borderwidth=2, relief="groove")
    first_column_label = Label(first_column_frame, text="Première Colonne")
    first_column_label.pack(padx=10, pady=10)
    first_column_frame.pack(
        side="left", expand=True, fill="both", padx=10, pady=10
    )

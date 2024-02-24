from tkinter.ttk import Label, Entry, Button, Frame, Style
from tkinter import Toplevel, DISABLED, NORMAL
import asyncio
from api import API
from config_manager import ConfigManager
from PIL import Image, ImageTk


def open_main_frame(root_window: Toplevel, api: API):
    print("Opening main frame")

    # Création du frame principal qui contient tout
    main_frame = Frame(root_window)
    main_frame.pack(padx=20, pady=20, expand=True, fill="both")

    # Première colonne (Frame)
    first_column_frame = Frame(main_frame, borderwidth=2, relief="groove")
    first_column_label = Label(first_column_frame, text="Première Colonne")
    first_column_label.pack(padx=10, pady=10)
    first_column_frame.pack(
        side="left", expand=True, fill="both", padx=10, pady=10
    )

    # Deuxième colonne (Frame)
    second_column_frame = Frame(main_frame, borderwidth=2, relief="groove")
    second_column_label = Label(second_column_frame, text="Deuxième Colonne")
    second_column_label.pack(padx=10, pady=10)
    second_column_frame.pack(
        side="left", expand=True, fill="both", padx=10, pady=10
    )

    # Troisième colonne (Frame)
    third_column_frame = Frame(main_frame, borderwidth=2, relief="groove")
    third_column_label = Label(third_column_frame, text="Troisième Colonne")
    third_column_label.pack(padx=10, pady=10)
    third_column_frame.pack(
        side="left", expand=True, fill="both", padx=10, pady=10
    )

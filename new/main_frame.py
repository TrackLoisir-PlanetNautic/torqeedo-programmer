from tkinter.ttk import Label, Entry, Button, Frame, Style
from tkinter import Toplevel, DISABLED, NORMAL
import asyncio
from api import API
from config_manager import ConfigManager
from PIL import Image, ImageTk


def open_main_frame(root_window: Toplevel):
    print("Opening main frame")

    main_frame = Frame(root_window)
    test = Label(main_frame, text="Bienvenue")
    test.pack()
    main_frame.pack(padx=20, pady=20)

from tkinter.ttk import Label, Entry, Button, Frame, Style
from tkinter import Toplevel, DISABLED, NORMAL
import asyncio
from api import API
from config_manager import ConfigManager
from PIL import Image, ImageTk
from Frames.main_frame import open_main_frame
from torqeedo_programmer import TorqeedoProgrammer


# Fonction asynchrone pour gérer la connexion
# et l'ouverture d'une nouvelle fenêtre
async def login_and_open_login_frame(
    root_window: Toplevel,
    login_frame: Frame,
    torqeedo_programmer: TorqeedoProgrammer,
    email: str,
    password: str,
    login_button: Button,
    status_label: Label,
):
    try:
        await torqeedo_programmer.api.connectToWebsite(email, password)
    except Exception as e:
        status_label.config(text=str(e))
        login_button.config(state=NORMAL)
        return

    login_frame.pack_forget()
    login_frame.destroy()
    open_main_frame(root_window, torqeedo_programmer)


# Fonction appelée lorsque l'utilisateur clique sur le bouton de connexion
def on_login_clicked(
    root_window: Toplevel,
    login_frame: Frame,
    torqeedo_programmer: TorqeedoProgrammer,
    email_entry: Entry,
    password_entry: Entry,
    login_button: Button,
    status_label: Label,
):
    email = email_entry.get()
    password = password_entry.get()
    ConfigManager().set_email(email)
    login_button.config(state=DISABLED)
    status_label.config(text="Connexion en cours...")
    asyncio.ensure_future(
        login_and_open_login_frame(
            root_window,
            login_frame,
            torqeedo_programmer,
            email,
            password,
            login_button,
            status_label,
        )
    )


def init_login_frame(root_window: Toplevel):
    # Adjust the style for a modern look
    style = Style()
    style.configure("TLabel", font=("Arial", 14), background="white")
    style.configure(
        "TEntry", font=("Arial", 14), width=40
    )  # Increase width here
    style.configure("TButton", font=("Arial", 12), borderwidth=1)
    style.configure("TFrame", background="white")

    root_window.title("Trackloisirs")
    root_window.configure(background="white")

    login_frame = Frame(root_window, style="TFrame")
    # Increase padx here for a wider frame effect
    login_frame.pack(padx=40, pady=20, expand=True)

    # Load and resize the logo proportionally
    original_image = Image.open("Ressources/Full_logo_black.png")
    target_width = 150
    original_width, original_height = original_image.size
    ratio = target_width / original_width
    new_height = int(original_height * ratio)
    resized_image = original_image.resize(
        (target_width, new_height), Image.Resampling.LANCZOS
    )

    logo_image = ImageTk.PhotoImage(resized_image)

    logo_label = Label(login_frame, image=logo_image, background="white")
    logo_label.image = (
        logo_image  # Keep a reference to avoid garbage collection
    )
    logo_label.pack(pady=(10, 40))

    email_label = Label(
        login_frame,
        text="Adresse mail:",
        font=("Arial", 14),
        background="white",
    )
    email_label.pack(pady=(0, 10))
    email_entry = Entry(login_frame, font=("Arial", 14))
    email_entry.insert(0, ConfigManager().get_email())
    email_entry.pack(pady=(0, 20))

    password_label = Label(
        login_frame,
        text="Mot de passe:",
        font=("Arial", 14),
        background="white",
    )
    password_label.pack(pady=(0, 10))
    password_entry = Entry(login_frame, show="*", font=("Arial", 14))
    password_entry.pack(pady=(0, 10))

    status_label = Label(login_frame, text="", style="TLabel")
    status_label.pack(pady=(0, 10))

    api_instance = API(base_url="https://app.trackloisirs.com/api")
    torqeedo_programmer = TorqeedoProgrammer(api=api_instance)

    login_button = Button(
        login_frame,
        text="Connexion",
        style="TButton",
        command=lambda: on_login_clicked(
            root_window,
            login_frame,
            torqeedo_programmer,
            email_entry,
            password_entry,
            login_button,
            status_label,
        ),
    )
    login_button.pack()

    # Function to handle the Enter key press
    def handle_enter(event):
        on_login_clicked(
            root_window,
            login_frame,
            torqeedo_programmer,
            email_entry,
            password_entry,
            login_button,
            status_label,
        )

    # Bind the Enter key to the login action
    root_window.bind("<Return>", handle_enter)

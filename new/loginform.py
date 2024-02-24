from tkinter.ttk import Label, Entry, Button, Frame
from tkinter import Toplevel, DISABLED, NORMAL
import asyncio
from api import API
from config_manager import ConfigManager


# Close login frame and open main frame
def open_login_frame(root_window: Toplevel, login_frame: Frame):
    login_frame.pack_forget()
    login_frame.destroy()

    main_frame = Frame(root_window)
    test = Label(main_frame, text="Bienvenue")
    test.pack()
    main_frame.pack(padx=20, pady=20)


# Fonction asynchrone pour gérer la connexion
# et l'ouverture d'une nouvelle fenêtre
async def login_and_open_login_frame(
    root_window: Toplevel,
    login_frame: Frame,
    api: API,
    email: str,
    password: str,
    login_button: Button,
    status_label: Label,
):
    try:
        await api.connectToWebsite(email, password)
    except Exception as e:
        status_label.config(text=str(e))
        login_button.config(state=NORMAL)
        return

    open_login_frame(root_window, login_frame)


# Fonction appelée lorsque l'utilisateur clique sur le bouton de connexion
def on_login_clicked(
    root_window: Toplevel,
    login_frame: Frame,
    api: API,
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
            api,
            email,
            password,
            login_button,
            status_label,
        )
    )


def init_login_frame(root_window: Toplevel):

    default_email = ConfigManager().get_email()

    login_frame = Frame(root_window)
    login_frame.pack(padx=20, pady=20)
    email_label = Label(login_frame, text="Adresse mail:")
    email_label.pack(
        pady=(0, 10)
    )  # Ajoute de l'espace en dessous du label de l'email
    email_entry = Entry(login_frame)
    email_entry.insert(0, default_email)
    email_entry.pack(pady=(0, 20))

    password_label = Label(login_frame, text="Mot de passe:")
    password_label.pack(pady=(0, 10))
    password_entry = Entry(login_frame, show="*")
    password_entry.pack(pady=(0, 20))

    status_label = Label(login_frame, text="")
    status_label.pack(pady=(0, 10))

    api = API(base_url="https://app.trackloisirs.com/api")
    login_button = Button(
        login_frame,
        text="Connexion",
        command=lambda: on_login_clicked(
            root_window,
            login_frame,
            api,
            email_entry,
            password_entry,
            login_button,
            status_label,
        ),
    )
    login_button.pack()

    # Fonction pour gérer l'appui sur la touche Entrée
    def handle_enter(event):
        on_login_clicked(
            root_window,
            login_frame,
            api,
            email_entry,
            password_entry,
            login_button,
            status_label,
        )

    # Associer l'appui sur la touche Entrée à la tentative de connexion
    root_window.bind("<Return>", handle_enter)

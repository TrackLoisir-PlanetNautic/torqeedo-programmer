from tkinter import Label, Entry, Button, Toplevel, DISABLED, NORMAL
import asyncio
from api import API
from config_manager import ConfigManager


# Fonction pour ouvrir une nouvelle fenêtre après une connexion réussie
def open_main_window(login_window: Toplevel):
    login_window.destroy()
    main_window = Toplevel()
    main_window.title("Nouvelle Fenêtre")
    Label(main_window, text="Connexion réussie!").pack()


# Fonction asynchrone pour gérer la connexion
# et l'ouverture d'une nouvelle fenêtre
async def login_and_open_main_window(
    login_window: Toplevel,
    api: API,
    email: str,
    password: str,
    login_button: Button,
    status_label: Label,
):
    try:
        await api.connectToWebsite(email, password)
        open_main_window(login_window)
    except Exception as e:
        status_label.config(text=e)
    finally:
        login_button.config(state=NORMAL)


# Fonction appelée lorsque l'utilisateur clique sur le bouton de connexion
def on_login_clicked(
    login_window: Toplevel,
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
        login_and_open_main_window(
            login_window, api, email, password, login_button, status_label
        )
    )


def init_login_window(login_window: Toplevel):
    login_window.title("Fenêtre de Connexion")
    default_email = ConfigManager().get_email()
    email_label = Label(login_window, text="Adresse mail:")
    email_label.pack()
    email_entry = Entry(login_window)
    email_entry.insert(0, default_email)
    email_entry.pack()

    password_label = Label(login_window, text="Mot de passe:")
    password_label.pack()
    password_entry = Entry(login_window, show="*")
    password_entry.pack()

    status_label = Label(login_window, text="")
    status_label.pack()

    api = API(base_url="https://app.trackloisirs.com/api")
    login_button = Button(
        login_window,
        text="Connexion",
        command=lambda: on_login_clicked(
            login_window,
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
            login_window,
            api,
            email_entry,
            password_entry,
            login_button,
            status_label,
        )

    # Associer l'appui sur la touche Entrée à la tentative de connexion
    login_window.bind("<Return>", handle_enter)

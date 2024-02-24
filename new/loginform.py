from tkinter import Label, Entry, Button, Toplevel, DISABLED, NORMAL
from tkinter import messagebox
import asyncio
from api import API
from config_manager import ConfigManager


# Fonction pour ouvrir une nouvelle fenêtre après une connexion réussie
def open_new_window():
    new_window = Toplevel()
    new_window.title("Nouvelle Fenêtre")
    Label(new_window, text="Connexion réussie!").pack()


# Fonction asynchrone pour gérer la connexion et l'ouverture d'une nouvelle fenêtre
async def login_and_open_new_window(
    api: API,
    email: str,
    password: str,
    login_button: Button,
    status_label: Label,
):
    try:
        login_success = await api.connectToWebsite(email, password)
        if login_success:
            open_new_window()  # Ouverture d'une nouvelle fenêtre
        else:
            status_label.config(text="Erreur de connexion")
    except Exception as e:
        messagebox.showerror("Erreur", str(e))
        status_label.config(text="Erreur de connexion")
    finally:
        login_button.config(state=NORMAL)


# Fonction appelée lorsque l'utilisateur clique sur le bouton de connexion
def on_login_clicked(
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
        login_and_open_new_window(
            api, email, password, login_button, status_label
        )
    )


def init_login_window(root: Toplevel):
    root.title("Fenêtre de Connexion")
    default_email = ConfigManager().get_email()
    email_label = Label(root, text="Adresse mail:")
    email_label.pack()
    email_entry = Entry(root)
    email_entry.insert(0, default_email)
    email_entry.pack()

    password_label = Label(root, text="Mot de passe:")
    password_label.pack()
    password_entry = Entry(root, show="*")
    password_entry.pack()

    status_label = Label(root, text="")
    status_label.pack()

    api = API(base_url="https://app.trackloisirs.com/api")
    login_button = Button(
        root,
        text="Connexion",
        command=lambda: on_login_clicked(
            api, email_entry, password_entry, login_button, status_label
        ),
    )
    login_button.pack()

import asyncio
import aiotkinter
from Frames.login_form import init_login_frame
from ttkthemes import ThemedTk


async def close_program(loop):
    loop.stop()


if __name__ == "__main__":
    asyncio.set_event_loop_policy(aiotkinter.TkinterEventLoopPolicy())
    loop = asyncio.get_event_loop()

    root_window = ThemedTk(theme="arc")
    root_window.geometry("1200x800")
    root_window.title("Trackloisirs")

    # Initialisation de la fenêtre de connexion
    init_login_frame(root_window)

    # Définir une fonction de fermeture qui arrête la boucle d'événements
    def on_close():
        asyncio.create_task(close_program(loop))
        root_window.destroy()

    # Lier l'événement de fermeture de la fenêtre à la fonction on_close
    root_window.protocol("WM_DELETE_WINDOW", on_close)

    try:
        loop.run_forever()
    finally:
        loop.close()

import sys
import asyncio
from PyQt6.QtWidgets import QApplication, QMainWindow, QDialog
from login_window import LoginWindow
from qasync import QEventLoop

from torqeedo_programmer import TorqeedoProgrammer
from main_window import MainWindow


async def main():
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    login_window = LoginWindow("https://app.trackloisirs.com/api")
    if login_window.exec() == QDialog.DialogCode.Accepted:
        # Logique post-connexion
        api_instance = (
            login_window.api
        )  # Récupère l'instance API de la fenêtre de connexion

        try:
            # Supposons que vous ayez une méthode pour récupérer la liste des contrôleurs
            controllers = api_instance.getTorqeedoControllersList()

            # Instanciez TorqeedoProgrammer avec l'API et la liste des contrôleurs
            torqeedo_programmer = TorqeedoProgrammer(
                api=api_instance, torqeedo_controllers=controllers
            )
            main_window = MainWindow(torqeedo_programmer)
            main_window.show()

        except Exception as e:
            print(
                f"Erreur lors de la récupération des contrôleurs Torqeedo : {e}"
            )
            # Gérez l'erreur (par exemple, affichez un message à l'utilisateur)

    with loop:
        loop.run_forever()


if __name__ == "__main__":
    asyncio.run(main())

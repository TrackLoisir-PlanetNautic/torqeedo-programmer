from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
)
from login_window import LoginWindow
from torqeedo_programmer import TorqeedoProgrammer
from main_window import MainWindow


def main():
    app = QApplication([])
    api_url = "https://app.trackloisirs.com/api"
    login_window = LoginWindow(api_url)

    if login_window.exec() == QDialog.DialogCode.Accepted:
        # À ce stade, login_window.api contient une instance API configurée et connectée
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
            app.exec()

        except Exception as e:
            print(
                f"Erreur lors de la récupération des contrôleurs Torqeedo : {e}"
            )
            # Gérez l'erreur (par exemple, affichez un message à l'utilisateur)
    


if __name__ == "__main__":
    main()

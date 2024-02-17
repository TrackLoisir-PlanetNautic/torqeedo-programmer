import asyncio
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
)
from PyQt6.QtCore import Qt, QCoreApplication, QEvent
from api import API
from config_manager import ConfigManager


class LoginWindow(QDialog):
    def __init__(self, api_url):
        super().__init__()
        self.config_manager = ConfigManager()
        self.api_url = api_url
        self.api = None
        self.setupUi()
        self.emailLineEdit.setText(self.config_manager.get_email())

    def setupUi(self):
        self.setWindowTitle("Connexion")
        self.setGeometry(
            300, 100, 350, 250
        )  # Ajustement pour s'adapter au nouveau contenu

        layout = QVBoxLayout()

        # Email
        self.emailLabel = QLabel("Email:")
        self.emailLineEdit = QLineEdit()
        layout.addWidget(self.emailLabel)
        layout.addWidget(self.emailLineEdit)

        # Password
        self.passwordLabel = QLabel("Mot de passe:")
        self.passwordLineEdit = QLineEdit()
        self.passwordLineEdit.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.passwordLabel)
        layout.addWidget(self.passwordLineEdit)

        # Bouton de connexion
        self.loginButton = QPushButton("Connexion")
        self.loginButton.clicked.connect(self.attempt_login)
        layout.addWidget(self.loginButton)

        # Zone d'affichage des erreurs
        self.errorLabel = QLabel("")
        self.errorLabel.setStyleSheet("color: red;")
        self.errorLabel.setWordWrap(True)
        self.errorLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.errorLabel)

        self.setLayout(layout)

    def attempt_login(self):
        QCoreApplication.instance().postEvent(self, QEvent(QEvent.Type.User))
        email = self.emailLineEdit.text()
        password = self.passwordLineEdit.text()
        self.config_manager.set_email(email)
        self.loginButton.setText("Chargement...")

        asyncio.create_task(self.async_attempt_login(email, password))

    async def async_attempt_login(self, email, password):
        self.api = API(base_url=self.api_url, email=email, password=password)
        try:
            await self.api.connectToWebsite()
            has_rights = await self.api.check_user_rights_for_requests()
            print(has_rights)
            if has_rights:
                print("accept")
                self.accept()  # Ferme la fenêtre de dialogue avec un résultat positif
            else:
                self.display_error("Vous n'avez pas les droits nécessaires.")
        except Exception as e:
            self.display_error(str(e))
        finally:
            print("Connexion terminée")
            print(self.loginButton)

    def display_error(self, message):
        # Affiche le message d'erreur dans la zone prévue à cet effet
        self.errorLabel.setText(message)

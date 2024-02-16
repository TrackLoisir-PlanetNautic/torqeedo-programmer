from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
)
from PyQt6.QtCore import Qt
from api import API


class LoginWindow(QDialog):
    def __init__(self, api_url):
        super().__init__()
        self.api_url = api_url
        self.api = None
        self.setupUi()

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
        email = self.emailLineEdit.text()
        password = self.passwordLineEdit.text()

        self.api = API(base_url=self.api_url, email=email, password=password)
        try:
            self.api.connectToWebsite()
            has_rights = self.api.check_user_rights_for_requests()
            if has_rights:
                self.accept()  # Ferme la fenêtre de dialogue avec un résultat positif
            else:
                self.display_error("Vous n'avez pas les droits nécessaires.")
        except Exception as e:
            self.display_error(str(e))

    def display_error(self, message):
        # Affiche le message d'erreur dans la zone prévue à cet effet
        self.errorLabel.setText(message)

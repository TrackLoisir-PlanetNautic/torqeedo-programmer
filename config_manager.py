import json
import os
from pathlib import Path


class ConfigManager:
    def __init__(self, filepath="config.json"):
        # Déterminer le dossier de support de l'application
        if os.path.exists("Ressources"):
            self.filepath = "Ressources/" + filepath
        else:
            app_support_dir = (
                Path.home()
                / "Library"
                / "Application Support"
                / "ToreedoProgrammer"
            )
            app_support_dir.mkdir(parents=True, exist_ok=True)

            # Chemin complet du fichier de configuration
            self.filepath = app_support_dir / filepath

        # Vérifier l'existence du fichier de configuration, le créer si nécessaire
        if not os.path.exists(self.filepath):
            with open(self.filepath, "w") as f:
                f.write("{}")

        self.config = {}
        self.load_config()

    def load_config(self):
        if os.path.exists(self.filepath):
            with open(self.filepath, "r") as f:
                self.config = json.load(f)
        else:
            self.config = {}

    def save_config(self):
        with open(self.filepath, "w") as f:
            json.dump(self.config, f)

    def get_email(self):
        return self.config.get("email", "")

    def set_email(self, email):
        self.config["email"] = email
        self.save_config()

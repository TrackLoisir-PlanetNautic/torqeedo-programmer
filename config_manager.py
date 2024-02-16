import json
import os


class ConfigManager:
    def __init__(self, filepath="config.json"):
        self.filepath = filepath
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

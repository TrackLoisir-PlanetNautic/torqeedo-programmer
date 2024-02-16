from pydantic import BaseModel
from typing import Optional, List
import requests
from torqeedo_controller import TorqeedoController


class API(BaseModel):
    base_url: str
    email: str
    password: str
    accessToken: str = None

    def connectToWebsite(self):
        url = self.base_url + "/frontend/account/login"
        params = {
            "email": self.email,
            "password": self.password,
            "remember": "true",
        }

        try:
            res = requests.post(url, json=params)
            res.raise_for_status()  # Cela va lever une exception si le code de statut HTTP n'est pas 200
            data = res.json()

            if data["status"] == 200:
                self.accessToken = data[
                    "accessToken"
                ]  # Sauvegarde du token d'authentification
                print("Connexion réussie, token récupéré.")
            else:
                print(data)
                raise Exception(
                    f"Echec de la connexion : {data.get('message', 'Aucune erreur retournée')}"
                )
        except requests.RequestException as e:
            raise Exception(f"Echec de la connexion: {e}")

    def check_user_rights_for_requests(self) -> bool:
        url = (
            self.base_url
            + "/backend/pythonProgrammer/getTorqeedoControllersList"
        )
        headers = {"authorization": "Bearer " + self.accessToken}
        res = requests.get(url, headers=headers, timeout=5)
        return res.json()

    def getTorqeedoControllersList(self) -> List[TorqeedoController]:
        url = (
            self.base_url
            + "/backend/pythonProgrammer/getTorqeedoControllersList"
        )
        headers = {"Authorization": "Bearer " + self.accessToken}
        try:
            res = requests.get(url, headers=headers, timeout=5)
            res.raise_for_status()  # This will raise an exception for HTTP errors
            data = res.json()

            if data["status"] == 200:
                controllers_list = [
                    TorqeedoController(**controller)
                    for controller in data["data"]
                ]
                return controllers_list
            else:
                raise Exception(
                    f"Failed to fetch controllers: {data.get('message', 'No error message')}"
                )
        except requests.RequestException as e:
            raise Exception(f"Request failed: {e}")

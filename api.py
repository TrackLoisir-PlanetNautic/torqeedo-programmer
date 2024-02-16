import base64
from pydantic import BaseModel
from typing import List
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

    async def download_firmware(self, torqCtrlId: int):
        if self.current_in_download:
            return
        self.current_in_download = True
        url = self.base_url + "/backend/pythonProgrammer/getHashSigningKey"
        headers = {
            "authorization": "Bearer " + self.accessToken,
            "torqctrlid": str(torqCtrlId),
        }

        try:
            res = requests.get(url, headers=headers, timeout=5)
            res = res.json()
            print(res)
            if res["status"] != 200:
                self.download_msg = res["message"]
                self.current_in_download = False
                return

            self.signHashKey = base64.b64decode(res["hashkey_b64"])

            st_bootloader = self.download_and_store(
                "/backend/pythonProgrammer/getBootloader", "./bootloader_tmp"
            )
            if not st_bootloader:
                self.current_in_download = False
                return
            self.signedBootloaderReady = True

            st_parttable = self.download_and_store(
                "/backend/pythonProgrammer/getPartTable", "./part_table_tmp"
            )
            if not st_parttable:
                self.current_in_download = False
                return
            self.partTableReady = True

            st_signedfirmware = self.download_and_store(
                "/backend/pythonProgrammer/getSignedFirmware", "./firmware_tmp"
            )
            if not st_signedfirmware:
                self.current_in_download = False
                return
            self.signedFirmwareReady = True

        except Exception:
            self.signedFirmwareReady = False
            self.download_msg = "Download failed !"

        self.current_in_download = False
        self.download_msg = "Download finished successfully!"

    def download_and_store(self, endpoint, store_path):
        url = self.base_url + endpoint
        headers = {
            "authorization": "Bearer " + self.accessToken,
            "torqctrlid": str(self.trackerSelected["torqCtrlId"]),
        }
        res = requests.get(url, headers=headers, timeout=5, stream=True)
        print(res)
        if res.status_code != 200:
            self.download_msg = res.reason
            return 0

        path = store_path
        with open(path, "wb") as f:
            total_length = int(res.headers.get("content-length"))
            chunk_size = 1024
            total_chunk = int(total_length / chunk_size)
            current_chunk = 0
            for chunk in res.iter_content(chunk_size=chunk_size):
                if chunk:
                    current_chunk = current_chunk + 1
                    f.write(chunk)
                    f.flush()
        return 200

import base64
from pydantic import BaseModel
from typing import Any, List
import requests
from torqeedo_controller import TorqeedoController
import aiohttp


class API(BaseModel):
    base_url: str
    email: str
    password: str
    accessToken: str = None
    firmware_currently_downloading: bool = False
    dl_signed_bootloader: bool = False
    dl_part_table: bool = False
    dl_signed_firmware: bool = False
    download_msg: str = ""
    signed_hash_key: bytes = None

    async def connectToWebsite(self):
        async with aiohttp.ClientSession() as session:
            url = self.base_url + "/frontend/account/login"
            params = {
                "email": self.email,
                "password": self.password,
                "remember": "true",
            }

            try:
                async with session.post(url, json=params) as res:
                    res.raise_for_status()  # Cela va lever une exception si le code de statut HTTP n'est pas 200
                    data = await res.json()

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

        async def check_user_rights_for_requests(self) -> bool:
            async with aiohttp.ClientSession() as session:
                url = (
                    self.base_url
                    + "/backend/pythonProgrammer/getTorqeedoControllersList"
                )
                headers = {"authorization": "Bearer " + self.accessToken}
                async with session.get(url, headers=headers) as res:
                    data = await res.json()
                    return data

    async def getTorqeedoControllersList(self) -> List[TorqeedoController]:
        url = (
            self.base_url
            + "/backend/pythonProgrammer/getTorqeedoControllersList"
        )
        headers = {"Authorization": "Bearer " + self.accessToken}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as res:
                    res.raise_for_status()
                    data = await res.json()

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

    async def download_firmware(self, torqCtrlId: str):
        print("Downloading firmware")
        if self.firmware_currently_downloading:
            return
        self.firmware_currently_downloading = True
        url = self.base_url + "/backend/pythonProgrammer/getHashSigningKey"
        headers = {
            "authorization": "Bearer " + self.accessToken,
            "torqctrlid": torqCtrlId,
        }

        try:
            res = requests.get(url, headers=headers, timeout=5)
            res = res.json()
            print(res)
            if res["status"] != 200:
                self.download_msg = res["message"]
                self.firmware_currently_downloading = False
                return

            self.signed_hash_key = base64.b64decode(res["hashkey_b64"])
            print(self.signed_hash_key)

            st_bootloader = self.download_and_store(
                "/backend/pythonProgrammer/getBootloader",
                "./bootloader_tmp",
                torqCtrlId,
            )
            if not st_bootloader:
                self.firmware_currently_downloading = False
                return
            self.dl_signed_bootloader = True
            print(self.dl_signed_bootloader)
            st_parttable = self.download_and_store(
                "/backend/pythonProgrammer/getPartTable",
                "./part_table_tmp",
                torqCtrlId,
            )
            if not st_parttable:
                self.firmware_currently_downloading = False
                return
            self.dl_part_table = True

            st_signedfirmware = self.download_and_store(
                "/backend/pythonProgrammer/getSignedFirmware",
                "./firmware_tmp",
                torqCtrlId,
            )
            if not st_signedfirmware:
                self.firmware_currently_downloading = False
                return
            self.dl_signed_firmware = True

        except Exception as e:
            print(f"Error while downloading firmware: {e}")
            self.dl_signed_firmware = False
            self.download_msg = "Download failed !"

        self.firmware_currently_downloading = False
        self.download_msg = "Download finished successfully!"

    def download_and_store(
        self, endpoint: str, store_path: str, torqCtrlId: str
    ):
        url = self.base_url + endpoint
        headers = {
            "authorization": "Bearer " + self.accessToken,
            "torqctrlid": torqCtrlId,
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

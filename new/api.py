from pydantic import BaseModel
from typing import List
import aiohttp
from torqeedo_controller import TorqeedoController


# Nouvelle définition de la classe API utilisant aiohttp pour
# des appels asynchrones
class API(BaseModel):
    base_url: str
    accessToken: str = None
    firmware_currently_downloading: bool = False
    dl_signed_bootloader: bool = False
    dl_part_table: bool = False
    dl_signed_firmware: bool = False
    download_msg: str = ""
    signed_hash_key: bytes = None

    async def connectToWebsite(self, email, password):
        async with aiohttp.ClientSession() as session:
            url = self.base_url + "/frontend/account/login"
            params = {
                "email": email,
                "password": password,
                "remember": "true",
            }

            async with session.post(url, json=params) as res:
                res.raise_for_status()
                # Cela va lever une exception si
                # le code de statut HTTP n'est pas 200
                data = await res.json()

                if data["status"] == 200:
                    self.accessToken = data["accessToken"]
                    return True  # Indique la réussite de la connexion
                else:
                    raise Exception(
                        f"Échec de la connexion: {data.get('message', 'Aucune erreur retournée')}"
                    )

    async def getTorqeedoControllersList(self) -> List[TorqeedoController]:
        url = (
            self.base_url
            + "/backend/pythonProgrammer/getTorqeedoControllersList"
        )
        headers = {"Authorization": "Bearer " + self.accessToken}
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

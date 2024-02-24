from pydantic import BaseModel
from typing import List
import aiohttp
from torqeedo_controller import TorqeedoController
import base64


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

    async def download_and_store(
        self, endpoint: str, store_path: str, torqCtrlId: str
    ):
        url = self.base_url + endpoint
        print(url)
        headers = {
            "authorization": "Bearer " + self.accessToken,
            "torqctrlid": str(torqCtrlId),
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as res:
                if res.status != 200:
                    print("Failed to download:", res.reason)
                    return 0

                total_length = res.headers.get("content-length")
                if total_length is None:  # no content length header
                    print("No content-length header")
                    return 0
                else:
                    total_length = int(total_length)

                chunk_size = 1024
                with open(store_path, "wb") as f:
                    async for chunk in res.content.iter_chunked(chunk_size):
                        if chunk:
                            f.write(chunk)
                            f.flush()
                return 200

    async def download_firmware(self, torqCtrlId: str):
        try:
            print("Downloading start firmware")

            url = self.base_url + "/backend/pythonProgrammer/getHashSigningKey"
            headers = {
                "authorization": "Bearer " + self.accessToken,
                "torqctrlid": str(torqCtrlId),
            }
            print("Downloading hashkey")
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as res:
                    res.raise_for_status()
                    data = await res.json()
                    if data["status"] != 200:
                        print(data["message"])
                        raise Exception(
                            f"Failed to download firmware: {data['message']}"
                        )
                    print("hashkey_b64 retrieved")
                    # print(base64.b64decode(data["hashkey_b64"]))

                print("Downloading st_bootloader")
                st_bootloader = await self.download_and_store(
                    "/backend/pythonProgrammer/getBootloader",
                    "./downloads/bootloader_tmp",
                    torqCtrlId,
                )
                if not st_bootloader:
                    print("Failed to download bootloader")
                    return

                print("Downloading st_parttable")
                st_parttable = await self.download_and_store(
                    "/backend/pythonProgrammer/getPartTable",
                    "./downloads/part_table_tmp",
                    torqCtrlId,
                )
                if not st_parttable:
                    print("Failed to download part table")
                    return

                print("Downloading st_signedfirmware")
                st_signedfirmware = await self.download_and_store(
                    "/backend/pythonProgrammer/getSignedFirmware",
                    "./downloads/firmware_tmp",
                    torqCtrlId,
                )
                if not st_signedfirmware:
                    print("Failed to download signed firmware")
                    return
                print("Download completed")
        except Exception as e:
            print(e)
            return

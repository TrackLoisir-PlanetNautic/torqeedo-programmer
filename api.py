from pydantic import BaseModel
from typing import List
import aiohttp
from torqeedo_controller import TorqeedoController, DownloadFirmwareStatus
import base64
from tkinter.ttk import Label
import ssl

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

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
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_context)) as session:
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
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_context)) as session:
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
        self,
        endpoint: str,
        store_path: str,
        torqeedo_controller: TorqeedoController,
        update_dowload_firm_progress_bar: callable,
        step: int,
    ):
        url = self.base_url + endpoint
        headers = {
            "authorization": "Bearer " + self.accessToken,
            "torqctrlid": str(torqeedo_controller.torqCtrlId),
        }
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_context)) as session:
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
                            update_dowload_firm_progress_bar(
                                len(chunk), total_length, step
                            )
                return 200

    async def download_firmware(
        self,
        torqeedo_controller: TorqeedoController,
        update_dowload_firm_progress_bar: callable,
        status_label: Label,
    ):
        try:
            print("Downloading start firmware")

            url = self.base_url + "/backend/pythonProgrammer/getHashSigningKey"
            headers = {
                "authorization": "Bearer " + self.accessToken,
                "torqctrlid": str(torqeedo_controller.torqCtrlId),
            }
            print("Downloading hashkey")
            status_label.config(text="Downloading hashkey")
            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_context)) as session:
                async with session.get(url, headers=headers) as res:
                    res.raise_for_status()
                    data = await res.json()
                    if data["status"] != 200:
                        print(data["message"])
                        status_label.config(
                            text=f"Failed to download firmware: {data['message']}"
                        )
                        torqeedo_controller.firmware_download_status = (
                            DownloadFirmwareStatus.ERROR
                        )
                        return
                    torqeedo_controller.hashkey_b64 = base64.b64decode(
                        data["hashkey_b64"]
                    )
                    update_dowload_firm_progress_bar(1, 1, 0)
                    print("Hashkey downloaded")
                    status_label.config(text="Hashkey downloaded")

                print("Downloading st_bootloader")
                status_label.config(text="Downloading bootloader")
                st_bootloader = await self.download_and_store(
                    "/backend/pythonProgrammer/getBootloader",
                    "./downloads/bootloader_tmp",
                    torqeedo_controller,
                    update_dowload_firm_progress_bar,
                    1,
                )
                if not st_bootloader:
                    print("Failed to download bootloader")
                    status_label.config(text="Failed to download bootloader")
                    torqeedo_controller.firmware_download_status = (
                        DownloadFirmwareStatus.ERROR
                    )
                    return

                print("Downloading st_parttable")
                st_parttable = await self.download_and_store(
                    "/backend/pythonProgrammer/getPartTable",
                    "./downloads/part_table_tmp",
                    torqeedo_controller,
                    update_dowload_firm_progress_bar,
                    2,
                )
                if not st_parttable:
                    print("Failed to download part table")
                    status_label.config(text="Failed to download part table")
                    torqeedo_controller.firmware_download_status = (
                        DownloadFirmwareStatus.ERROR
                    )
                    return

                print("Downloading st_signedfirmware")
                status_label.config(text="Downloading signed firmware")
                st_signedfirmware = await self.download_and_store(
                    "/backend/pythonProgrammer/getSignedFirmware",
                    "./downloads/firmware_tmp",
                    torqeedo_controller,
                    update_dowload_firm_progress_bar,
                    3,
                )
                if not st_signedfirmware:
                    print("Failed to download signed firmware")
                    status_label.config(
                        text="Failed to download signed firmware"
                    )
                    torqeedo_controller.firmware_download_status = (
                        DownloadFirmwareStatus.ERROR
                    )
                    return
            print("Download completed successfully")
            status_label.config(text="Download completed successfully")
            torqeedo_controller.firmware_download_status = (
                DownloadFirmwareStatus.SUCCESS
            )
        except Exception as e:
            print(e)
            torqeedo_controller.firmware_download_status = (
                DownloadFirmwareStatus.ERROR
            )
            status_label.config(
                text="Impossible de télécharger. Vérifiez votre connexion internet."
            )

    async def getKingwoIdFromHashkey(
        self, hashkey_b64: bytes, kingwo_id_of_hash_key: str
    ):
        url = (
            self.base_url + "/backend/pythonProgrammer/getKingwoIdFromHashkey"
        )
        headers = {"Authorization": "Bearer " + self.accessToken}
        data = {"hashkey_b64": base64.b64encode(hashkey_b64).decode("utf-8")}
        try:
            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_context)) as session:
                async with session.post(
                    url, headers=headers, json=data
                ) as res:
                    res.raise_for_status()
                    data = await res.json()
                    if data["status"] == 200:
                        kingwo_id_of_hash_key = f"KingwoId: {data['kingwoId']}"
                    else:
                        kingwo_id_of_hash_key = f"Failed to get KingwoId: {data.get('message', 'No error message')}"
        except Exception as e:
            print(e)
            kingwo_id_of_hash_key = f"Failed to get KingwoId: {e}"

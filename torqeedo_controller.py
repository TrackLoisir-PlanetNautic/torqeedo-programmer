from pydantic import BaseModel
from typing import Optional
from typing import Dict
from esp_rom import EspRom
from status import (
    DownloadFirmwareStatus,
    BurnHashKeyStatus,
    BootloaderFlashedStatus,
    FirmwareFlashedStatus,
    ConnectToPcbStatus
)
from compilation_result import CompilationResult


class TorqeedoController(BaseModel):
    torqCtrlId: int
    lastPing: int
    testCheckList: Optional[Dict] = None
    aesKey: Optional[str] = None
    workPlaceId: int
    kingwoId: str
    softType: str
    softVersion: int
    lastCheckOTA: int
    lastUpdateOTA: int
    statusId: int
    hashkey_b64: bytes = None
    esp_rom: EspRom = None
    connect_to_pcb_status: ConnectToPcbStatus = (
        ConnectToPcbStatus.NOT_CONNECTED
    )
    firmware_download_status: DownloadFirmwareStatus = (
        DownloadFirmwareStatus.NOT_STARTED
    )
    burn_hash_key_status: BurnHashKeyStatus = BurnHashKeyStatus.NOT_SCANNED
    bootloader_flashed_status: BootloaderFlashedStatus = (
        BootloaderFlashedStatus.NOT_FLASHED
    )
    firmware_flashed_status: FirmwareFlashedStatus = (
        FirmwareFlashedStatus.NOT_FLASHED
    )
    compilation_result: CompilationResult = None

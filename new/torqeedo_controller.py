from pydantic import BaseModel
from typing import Optional
from typing import Dict
from esp_rom import EspRom
from enum import Enum


class DownloadFirmwareStatus(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    ERROR = "error"
    SUCCESS = "success"


class BurnHashKeyStatus(Enum):
    NOT_SCANNED = "not_scanned"
    NOT_BURNED = "not_burned"
    BURNED_NOT_SAME = "burned_not_same"
    BURNED_SAME = "burned_same"
    ERROR = "error"


class BootloaderFlashedStatus(Enum):
    NOT_FLASHED = "not_flashed"
    IN_PROGRESS = "in_progress"
    FLASHED = "flashed"


class FirmwareFlashedStatus(Enum):
    NOT_FLASHED = "not_flashed"
    IN_PROGRESS = "in_progress"
    FLASHED = "flashed"


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
    firmware_download_status: DownloadFirmwareStatus = (
        DownloadFirmwareStatus.NOT_STARTED
    )
    burn_hash_key_status: BurnHashKeyStatus = BurnHashKeyStatus.NOT_SCANNED
    bootloader_flashed: BootloaderFlashedStatus = (
        BootloaderFlashedStatus.NOT_FLASHED
    )
    firmware_flashed: FirmwareFlashedStatus = FirmwareFlashedStatus.NOT_FLASHED

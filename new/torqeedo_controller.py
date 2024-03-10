from pydantic import BaseModel
from typing import Optional
from typing import Dict
from esp_rom import EspRom


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
    esp: EspRom = None

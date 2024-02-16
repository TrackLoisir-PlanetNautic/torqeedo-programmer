from pydantic import BaseModel
from typing import Optional, List, Dict


class CompilationResult(BaseModel):
    secureBootV2EnabledBootloader: Optional[str] = None
    secureBootV2CheckOKBootloader: Optional[str] = None
    secureBootV2EnabledBootloaderStage2: Optional[str] = None
    secureBootV2CheckOKFirmware: Optional[str] = None
    projectName: Optional[str] = None
    AES128_KEY: Optional[str] = None
    VERSION_NUMBER: Optional[str] = None
    TRACKER_GPS_ID: Optional[str] = None
    WIFI_BACKUP_SSID: Optional[str] = None
    MODE: Optional[str] = None
    REAL_COMPILATION_TIME: Optional[str] = None
    DEBUG: Optional[List[str]] = None
    partTableDesc: Optional[bool] = None
    error: Optional[str] = None

    # Ajoutez d'autres champs ici au besoin

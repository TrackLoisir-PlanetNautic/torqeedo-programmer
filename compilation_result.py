from pydantic import BaseModel
from typing import Optional, List


class CompilationResult(BaseModel):
    VERSION_NUMBER: Optional[str] = None
    AES128_KEY: Optional[str] = None
    DEBUG: Optional[List[str]] = None
    REAL_COMPILATION_TIME: Optional[str] = None
    WIFI_BACKUP_SSID: Optional[str] = None
    TRACKER_GPS_ID: Optional[str] = None
    MODE: Optional[str] = None
    SECURE_BOOT_V2_ENABLED_BOOTLOADER: Optional[bool] = None
    SECURE_BOOT_V2_VERIFIED: Optional[bool] = None
    COMPILATION_TIME: Optional[str] = None
    PROJECT_NAME: Optional[str] = None
    APP_VERSION: Optional[str] = None
    SECURE_BOOT_V2_ENABLED_BOOTLOADER_STAGE2: Optional[bool] = None
    SECURE_BOOT_V2_CHECK_OK_BOOTLOADER: Optional[bool] = None
    PART_TABLE: Optional[List[bool]] = []
    ERROR: Optional[str] = None
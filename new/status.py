from enum import Enum


class DownloadFirmwareStatus(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    ERROR = "error"
    SUCCESS = "success"


class BurnHashKeyStatus(Enum):
    IN_PROGRESS = "in_progress"
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

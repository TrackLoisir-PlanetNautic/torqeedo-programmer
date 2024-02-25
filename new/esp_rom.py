from pydantic import BaseModel
from typing import Any, Optional

import esptool

from esptool.targets.esp32 import ESP32ROM
from esptool.targets.esp32c2 import ESP32C2ROM
from esptool.targets.esp32c3 import ESP32C3ROM
from esptool.targets.esp32c6 import ESP32C6ROM
from esptool.targets.esp32c6beta import ESP32C6BETAROM
from esptool.targets.esp32h2 import ESP32H2ROM
from esptool.targets.esp32h2beta1 import ESP32H2BETA1ROM
from esptool.targets.esp32h2beta2 import ESP32H2BETA2ROM
from esptool.targets.esp32s2 import ESP32S2ROM
from esptool.targets.esp32s3 import ESP32S3ROM
from esptool.targets.esp32s3beta2 import ESP32S3BETA2ROM
from esptool.targets.esp8266 import ESP8266ROM


import espefuse.efuse.esp32 as esp32_efuse
import espefuse.efuse.esp32c2 as esp32c2_efuse
import espefuse.efuse.esp32c3 as esp32c3_efuse
import espefuse.efuse.esp32c6 as esp32c6_efuse
import espefuse.efuse.esp32h2 as esp32h2_efuse
import espefuse.efuse.esp32h2beta1 as esp32h2beta1_efuse
import espefuse.efuse.esp32s2 as esp32s2_efuse
import espefuse.efuse.esp32s3 as esp32s3_efuse
import espefuse.efuse.esp32s3beta2 as esp32s3beta2_efuse

from collections import namedtuple

from esptool.util import (
    hexify,
)

CHIP_DEFS = {
    "esp8266": ESP8266ROM,
    "esp32": ESP32ROM,
    "esp32s2": ESP32S2ROM,
    "esp32s3beta2": ESP32S3BETA2ROM,
    "esp32s3": ESP32S3ROM,
    "esp32c3": ESP32C3ROM,
    "esp32c6beta": ESP32C6BETAROM,
    "esp32h2beta1": ESP32H2BETA1ROM,
    "esp32h2beta2": ESP32H2BETA2ROM,
    "esp32c2": ESP32C2ROM,
    "esp32c6": ESP32C6ROM,
    "esp32h2": ESP32H2ROM,
}

DETECTED_FLASH_SIZES = {
    0x12: "256KB",
    0x13: "512KB",
    0x14: "1MB",
    0x15: "2MB",
    0x16: "4MB",
    0x17: "8MB",
    0x18: "16MB",
    0x19: "32MB",
    0x1A: "64MB",
    0x1B: "128MB",
    0x1C: "256MB",
    0x20: "64MB",
    0x21: "128MB",
    0x22: "256MB",
    0x32: "256KB",
    0x33: "512KB",
    0x34: "1MB",
    0x35: "2MB",
    0x36: "4MB",
    0x37: "8MB",
    0x38: "16MB",
    0x39: "32MB",
    0x3A: "64MB",
}
FLASH_MODES = {"qio": 0, "qout": 1, "dio": 2, "dout": 3}

DefChip = namedtuple("DefChip", ["chip_name", "efuse_lib", "chip_class"])

SUPPORTED_CHIPS = {
    "esp32": DefChip("ESP32", esp32_efuse, esptool.targets.ESP32ROM),
    "esp32c2": DefChip("ESP32-C2", esp32c2_efuse, esptool.targets.ESP32C2ROM),
    "esp32c3": DefChip("ESP32-C3", esp32c3_efuse, esptool.targets.ESP32C3ROM),
    "esp32c6": DefChip("ESP32-C6", esp32c6_efuse, esptool.targets.ESP32C6ROM),
    "esp32h2": DefChip("ESP32-H2", esp32h2_efuse, esptool.targets.ESP32H2ROM),
    "esp32h2beta1": DefChip(
        "ESP32-H2(beta1)", esp32h2beta1_efuse, esptool.targets.ESP32H2BETA1ROM
    ),
    "esp32s2": DefChip("ESP32-S2", esp32s2_efuse, esptool.targets.ESP32S2ROM),
    "esp32s3": DefChip("ESP32-S3", esp32s3_efuse, esptool.targets.ESP32S3ROM),
    "esp32s3beta2": DefChip(
        "ESP32-S3(beta2)", esp32s3beta2_efuse, esptool.targets.ESP32S3BETA2ROM
    ),
}


class EspRom(BaseModel):
    esp: Any
    mac_address: Optional[str] = None
    description: Optional[str] = None
    flash_infos: Optional[dict | None] = None
    major_rev: Optional[int] = None
    efuses: Optional[tuple] = None
    already_burned_same: bool = False
    compare_hash_key: bool = False

    def get_flash_id(self):
        """
        (manufacturer, device, flash_size, flash_type)
        """
        val = {}
        try:
            flash_id = self.esp.flash_id()
            val["manufacturer"] = flash_id & 0xFF
            flid_lowbyte = (flash_id >> 16) & 0xFF
            val["device"] = ((flash_id >> 8) & 0xFF, flid_lowbyte)
            val["flash_size"] = DETECTED_FLASH_SIZES.get(
                flid_lowbyte, "Unknown"
            )
            return val
        except (esptool.FatalError, OSError) as err:
            print(err)

    def is_abs_done_fuse_ok(self):
        for efu in self.efuses[0].efuses:
            if efu.name == "ABS_DONE_1":
                print(efu.name)
                print(efu.get())
                return efu.get()
        return False

    def get_efuses(
        self,
        skip_connect=False,
        debug_mode=False,
        do_not_confirm=False,
    ) -> tuple:
        for name in SUPPORTED_CHIPS:
            print(self.esp.CHIP_NAME)
            if SUPPORTED_CHIPS[name].chip_name == self.esp.CHIP_NAME:
                efuse = SUPPORTED_CHIPS[name].efuse_lib
                return (
                    efuse.EspEfuses(
                        self.esp, skip_connect, debug_mode, do_not_confirm
                    ),
                    efuse.operations,
                )
        else:
            raise esptool.FatalError(
                "get_efuses: Unsupported chip (%s)" % self.esp.CHIP_NAME
            )

    def is_the_same_block2(self, hashkey_b64: bytes):
        if hashkey_b64 is None or self.efuse is None:
            return -2

        print("------")
        print(str(self.efuse[0].blocks[2].bitarray)[2:])
        returnedNewBitString = ""
        for i in range(0, int(len(hexify(self.signHashKey))), 2):
            returnedNewBitString += str(hexify(self.signHashKey))[i + 1]
            returnedNewBitString += str(hexify(self.signHashKey))[i]
        print(returnedNewBitString[::-1])
        print("------")

        if (
            str(str(self.efuse[0].blocks[2].bitarray)[2:])
            == "0000000000000000000000000000000000000000000000000000000000000000"
        ):
            return -1

        if str(str(self.efuse[0].blocks[2].bitarray)[2:]) == str(
            returnedNewBitString[::-1]
        ):
            return 1
        return 0

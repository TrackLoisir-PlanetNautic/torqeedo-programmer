from pydantic import BaseModel
from typing import Any, Optional
import time
from tkinter.ttk import Label

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
    already_burned: bool = False
    is_same_hash_key: bool = False

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

    def burn_sign_hask_key(
        self,
        hashkey_b64: bytes,
        update_burn_hash_key_progress_bar: callable,
        burn_hash_key_status_label: Label,
    ):
        if not self.already_burned:
            try:
                print("burn hash key")
                update_burn_hash_key_progress_bar(0)
                self.burn_efuse(self.esp, self.efuse[0], "ABS_DONE_1", 1, None)
                update_burn_hash_key_progress_bar(50)
                time.sleep(0.25)
                self.burn_key(
                    self.esp,
                    self.efuses[0],
                    "secure_boot_v2",
                    hashkey_b64,
                    True,
                    None,
                )
                self.burnProgress.setValue(100)
                burn_hash_key_status_label.config(text="Burned !")
                time.sleep(0.25)
                self.efuse = self.get_efuses(self.esp)
                self.absDoneStatus.setText(
                    "secure boot ok: " + str(self.is_abs_done_fuse_ok())
                )
                if self.is_the_same_block2() != 1:
                    burn_hash_key_status_label.config(
                        text="Burn key failed !!"
                    )
            except:
                print("ERROR : can't burn now !")
        else:
            print("compare keys")

    def burn_efuse(self, esp, efuses, efuse_name, value, args):
        def print_attention(blocked_efuses_after_burn):
            if len(blocked_efuses_after_burn):
                print(
                    "    ATTENTION! This BLOCK uses NOT the NONE coding scheme "
                    "and after 'BURN', these efuses can not be burned in the feature:"
                )
                for i in range(0, len(blocked_efuses_after_burn), 5):
                    print(
                        "              ",
                        "".join(
                            "{}".format(blocked_efuses_after_burn[i : i + 5 :])
                        ),
                    )

        efuse_name_list = [efuse_name]
        burn_efuses_list = [efuses[name] for name in efuse_name_list]
        old_value_list = [efuses[name].get_raw() for name in efuse_name_list]
        new_value_list = [value]

        attention = ""
        print("The efuses to burn:")
        for block in efuses.blocks:
            burn_list_a_block = [
                e for e in burn_efuses_list if e.block == block.id
            ]
            if len(burn_list_a_block):
                print("  from BLOCK%d" % (block.id))
                for field in burn_list_a_block:
                    print("     - %s" % (field.name))
                    if (
                        efuses.blocks[field.block].get_coding_scheme()
                        != efuses.REGS.CODING_SCHEME_NONE
                    ):
                        using_the_same_block_names = [
                            e.name for e in efuses if e.block == field.block
                        ]
                        wr_names = [e.name for e in burn_list_a_block]
                        blocked_efuses_after_burn = [
                            name
                            for name in using_the_same_block_names
                            if name not in wr_names
                        ]
                        attention = " (see 'ATTENTION!' above)"
                if attention:
                    print_attention(blocked_efuses_after_burn)

        print("\nBurning efuses{}:".format(attention))
        for efuse, new_value in zip(burn_efuses_list, new_value_list):
            print(
                "\n    - '{}' ({}) {} -> {}".format(
                    efuse.name,
                    efuse.description,
                    efuse.get_bitstring(),
                    efuse.convert_to_bitstring(new_value),
                )
            )
            efuse.save(new_value)

        print()
        if "ENABLE_SECURITY_DOWNLOAD" in efuse_name_list:
            print(
                "ENABLE_SECURITY_DOWNLOAD -> 1: eFuses will not be read back "
                "for confirmation because this mode disables "
                "any SRAM and register operations."
            )
            print("                               espefuse will not work.")
            print(
                "                               esptool can read/write only flash."
            )

        if "DIS_DOWNLOAD_MODE" in efuse_name_list:
            print(
                "DIS_DOWNLOAD_MODE -> 1: eFuses will not be read back for "
                "confirmation because this mode disables any communication with the chip."
            )
            print(
                "                        espefuse/esptool will not work because "
                "they will not be able to connect to the chip."
            )

        if (
            esp.CHIP_NAME == "ESP32"
            and esp.get_chip_revision() >= 300
            and "UART_DOWNLOAD_DIS" in efuse_name_list
        ):
            print(
                "UART_DOWNLOAD_DIS -> 1: eFuses will be read for confirmation, "
                "but after that connection to the chip will become impossible."
            )
            print("                        espefuse/esptool will not work.")

        if not efuses.burn_all(check_batch_mode=True):
            return

        print("Checking efuses...")
        raise_error = False
        for efuse, old_value, new_value in zip(
            burn_efuses_list, old_value_list, new_value_list
        ):
            if not efuse.is_readable():
                print(
                    "Efuse %s is read-protected. Read back the burn value is not possible."
                    % efuse.name
                )
            else:
                new_value = efuse.convert_to_bitstring(new_value)
                burned_value = efuse.get_bitstring()
                if burned_value != new_value:
                    print(
                        burned_value,
                        "->",
                        new_value,
                        "Efuse %s failed to burn. Protected?" % efuse.name,
                    )
                    raise_error = True
        if raise_error:
            raise esptool.FatalError("The burn was not successful.")
        else:
            print("Successful")

    def burn_key(self, esp, efuses, blk, key: bytes, no_protect_key, args):
        block_name = blk
        # efuses.force_write_always = False

        print("Burn keys to blocks:")
        efuse = None
        for block in efuses.blocks:
            if block_name == block.name or block_name in block.alias:
                efuse = efuses[block.name]
        if efuse is None:
            raise esptool.FatalError("Unknown block name - %s" % (block_name))
        num_bytes = efuse.bit_len // 8
        data = key
        revers_msg = None
        if block_name in ("flash_encryption", "secure_boot_v1"):
            revers_msg = "\tReversing the byte order"
            data = data[::-1]
        print(" - %s -> [%s]" % (efuse.name, hexify(data, " ")))
        if revers_msg:
            print(revers_msg)
        if len(data) != num_bytes:
            raise esptool.FatalError(
                "Incorrect key file size %d. "
                "Key file must be %d bytes (%d bits) of raw binary key data."
                % (len(data), num_bytes, num_bytes * 8)
            )

        efuse.save(data)

        if block_name in ("flash_encryption", "secure_boot_v1"):
            if not no_protect_key:
                print("\tDisabling read to key block")
                efuse.disable_read()

        if not no_protect_key:
            print("\tDisabling write to key block")
            efuse.disable_write()
        print("")

        if no_protect_key:
            print("Key is left unprotected as per --no-protect-key argument.")

        msg = "Burn keys in efuse blocks.\n"
        if no_protect_key:
            msg += "The key block will left readable and writeable (due to --no-protect-key)"
        else:
            msg += "The key block will be read and write protected "
            "(no further changes or readback)"
        print(msg, "\n")
        if not efuses.burn_all(check_batch_mode=True):
            return
        print("Successful")

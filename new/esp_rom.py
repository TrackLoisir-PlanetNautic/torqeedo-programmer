from pydantic import BaseModel
from typing import Any, Optional
import time
import os
from tkinter.ttk import Label

import esptool
import struct
import io
import hashlib
import zlib
import sys

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
    flash_size_bytes,
    div_roundup,
    pad_to,
    print_overwrite,
)

from esptool.cmds import erase_flash, verify_flash

from esptool.bin_image import LoadFirmwareImage

from esptool.loader import (
    DEFAULT_TIMEOUT,
    ERASE_WRITE_TIMEOUT_PER_MB,
    timeout_per_mb,
    ESPLoader,
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
        print(
            "Getting esp flash infos : manufacturer, device, flash_size, flash_type"
        )
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
                # print(efu.name)
                # print(efu.get())
                return efu.get()
        return False

    def get_efuses(
        self,
        skip_connect=False,
        debug_mode=False,
        do_not_confirm=False,
    ) -> tuple:
        print("Getting efuses")
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
        if hashkey_b64 is None or self.efuses is None:
            return -2
        print("Comparing hash key")
        print("------")
        print(str(self.efuses[0].blocks[2].bitarray)[2:])
        returnedNewBitString = ""
        for i in range(0, int(len(hexify(hashkey_b64))), 2):
            returnedNewBitString += str(hexify(hashkey_b64))[i + 1]
            returnedNewBitString += str(hexify(hashkey_b64))[i]
        print(returnedNewBitString[::-1])
        print("------")

        if (
            str(str(self.efuses[0].blocks[2].bitarray)[2:])
            == "0000000000000000000000000000000000000000000000000000000000000000"
        ):
            return -1

        if str(str(self.efuses[0].blocks[2].bitarray)[2:]) == str(
            returnedNewBitString[::-1]
        ):
            return 1
        return 0

    async def burn_sign_hask_key(
        self,
        hashkey_b64: bytes,
        update_burn_hash_key_progress_bar: callable,
        burn_hash_key_status_label: Label,
    ):
        print("Start burning hash key")
        if not self.already_burned:
            try:
                update_burn_hash_key_progress_bar(0)
                self._burn_efuse(
                    self.esp, self.efuses[0], "ABS_DONE_1", 1, None
                )
                update_burn_hash_key_progress_bar(50)
                time.sleep(0.25)
                self._burn_key(
                    self.esp,
                    self.efuses[0],
                    "secure_boot_v2",
                    hashkey_b64,
                    True,
                    None,
                )
                update_burn_hash_key_progress_bar(100)
                burn_hash_key_status_label.config(text="Burned !")
                time.sleep(0.25)
                self.efuses = self.get_efuses(self.esp)
                if self.is_the_same_block2() != 1:
                    burn_hash_key_status_label.config(
                        text="Burn key failed !!"
                    )
            except Exception:
                print("ERROR : can't burn now !")
        else:
            print("Key already burned")

    def _burn_efuse(self, esp, efuses, efuse_name, value, args):
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

    def _burn_key(self, esp, efuses, blk, key: bytes, no_protect_key, args):
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

    def _update_image_flash_params(self, address, args, image):
        """
        Modify the flash mode & size bytes if this looks like an executable bootloader image
        """
        if len(image) < 8:
            return image  # not long enough to be a bootloader image

        # unpack the (potential) image header
        magic, _, flash_mode, flash_size_freq = struct.unpack(
            "BBBB", image[:4]
        )
        if address != self.esp.BOOTLOADER_FLASH_OFFSET:
            return (
                image  # not flashing bootloader offset, so don't modify this
            )

        if (args.flash_mode, args.flash_freq, args.flash_size) == (
            "keep",
        ) * 3:
            return image  # all settings are 'keep', not modifying anything

        # easy check if this is an image: does it start with a magic byte?
        if magic != self.esp.ESP_IMAGE_MAGIC:
            print(
                "Warning: Image file at 0x%x doesn't look like an image file, "
                "so not changing any flash settings." % address
            )
            return image

        # make sure this really is an image, and not just data that
        # starts with esp.ESP_IMAGE_MAGIC (mostly a problem for encrypted
        # images that happen to start with a magic byte
        try:
            test_image = self.esp.BOOTLOADER_IMAGE(io.BytesIO(image))
            test_image.verify()
        except Exception:
            print(
                "Warning: Image file at 0x%x is not a valid %s image, "
                "so not changing any flash settings."
                % (address, self.esp.CHIP_NAME)
            )
            return image

        # After the 8-byte header comes the extended header for chips others than ESP8266.
        # The 15th byte of the extended header indicates if the image is protected by
        # a SHA256 checksum. In that case we should not modify the header because
        # the checksum check would fail.
        sha_implies_keep = args.chip != "esp8266" and image[8 + 15] == 1

        def print_keep_warning(arg_to_keep, arg_used):
            print(
                "Warning: Image file at {addr} is protected with a hash checksum, "
                "so not changing the flash {arg} setting. "
                "Use the --flash_{arg}=keep option instead of --flash_{arg}={arg_orig} "
                "in order to remove this warning, or use the --dont-append-digest option "
                "for the elf2image command in order to generate an image file "
                "without a hash checksum".format(
                    addr=hex(address), arg=arg_to_keep, arg_orig=arg_used
                )
            )

        if args.flash_mode != "keep":
            new_flash_mode = FLASH_MODES[args.flash_mode]
            if flash_mode != new_flash_mode and sha_implies_keep:
                print_keep_warning("mode", args.flash_mode)
            else:
                flash_mode = new_flash_mode

        flash_freq = flash_size_freq & 0x0F
        if args.flash_freq != "keep":
            new_flash_freq = self.esp.parse_flash_freq_arg(args.flash_freq)
            if flash_freq != new_flash_freq and sha_implies_keep:
                print_keep_warning("frequency", args.flash_freq)
            else:
                flash_freq = new_flash_freq

        flash_size = flash_size_freq & 0xF0
        if args.flash_size != "keep":
            new_flash_size = self.esp.parse_flash_size_arg(args.flash_size)
            if flash_size != new_flash_size and sha_implies_keep:
                print_keep_warning("size", args.flash_size)
            else:
                flash_size = new_flash_size

        flash_params = struct.pack(b"BB", flash_mode, flash_size + flash_freq)
        if flash_params != image[2:4]:
            print(
                "Flash params set to 0x%04x"
                % struct.unpack(">H", flash_params)
            )
            image = image[0:2] + flash_params + image[4:]
        return image

    def write_flash(
        self, args, update_flash_bootloader_form_progress_bar: callable
    ):
        # set args.compress based on default behaviour:
        # -> if either --compress or --no-compress is set, honour that
        # -> otherwise, set --compress unless --no-stub is set
        if args.compress is None and not args.no_compress:
            args.compress = not args.no_stub

        if (
            not args.force
            and self.esp.CHIP_NAME != "ESP8266"
            and not self.esp.secure_download_mode
        ):
            # Check if secure boot is active
            if self.esp.get_secure_boot_enabled():
                for address, _ in args.addr_filename:
                    if address < 0x8000:
                        raise esptool.FatalError(
                            "Secure Boot detected, writing to flash regions < 0x8000 "
                            "is disabled to protect the bootloader. "
                            "Use --force to override, "
                            "please use with caution, otherwise it may brick your device!"
                        )
            # Check if chip_id and min_rev in image are valid for the target in use
            for _, argfile in args.addr_filename:
                try:
                    image = LoadFirmwareImage(self.esp.CHIP_NAME, argfile)
                except (esptool.FatalError, struct.error, RuntimeError):
                    continue
                finally:
                    argfile.seek(
                        0
                    )  # LoadFirmwareImage changes the file handle position
                if image.chip_id != self.esp.IMAGE_CHIP_ID:
                    raise esptool.FatalError(
                        f"{argfile.name} is not an {self.esp.CHIP_NAME} image."
                        "Use --force to flash anyway."
                    )

                # this logic below decides which min_rev to use, min_rev or min/max_rev_full
                if (
                    image.max_rev_full == 0
                ):  # image does not have max/min_rev_full fields
                    use_rev_full_fields = False
                elif (
                    image.max_rev_full == 65535
                ):  # image has default value of max_rev_full
                    if (
                        image.min_rev_full == 0 and image.min_rev != 0
                    ):  # min_rev_full is not set, min_rev is used
                        use_rev_full_fields = False
                    use_rev_full_fields = True
                else:  # max_rev_full set to a version
                    use_rev_full_fields = True

                if use_rev_full_fields:
                    rev = self.esp.get_chip_revision()
                    if rev < image.min_rev_full or rev > image.max_rev_full:
                        error_str = (
                            f"{argfile.name} requires chip revision in range "
                        )
                        error_str += f"[v{image.min_rev_full // 100}.{image.min_rev_full % 100} - "
                        if image.max_rev_full == 65535:
                            error_str += "max rev not set] "
                        else:
                            error_str += f"v{image.max_rev_full // 100}.{image.max_rev_full % 100}] "
                        error_str += f"(this chip is revision v{rev // 100}.{rev % 100})"
                        raise esptool.FatalError(
                            f"{error_str}. Use --force to flash anyway."
                        )
                else:
                    # In IDF, image.min_rev is set based on Kconfig option.
                    # For C3 chip, image.min_rev is the Minor revision
                    # while for the rest chips it is the Major revision.
                    if self.esp.CHIP_NAME == "ESP32-C3":
                        rev = self.esp.get_minor_chip_version()
                    else:
                        rev = self.esp.get_major_chip_version()
                    if rev < image.min_rev:
                        raise esptool.FatalError(
                            f"{argfile.name} requires chip revision "
                            f"{image.min_rev} or higher (this chip is revision {rev}). "
                            "Use --force to flash anyway."
                        )

        # In case we have encrypted files to write,
        # we first do few sanity checks before actual flash
        if args.encrypt or args.encrypt_files is not None:
            do_write = True

            if not self.esp.secure_download_mode:
                if self.esp.get_encrypted_download_disabled():
                    raise esptool.FatalError(
                        "This chip has encrypt functionality "
                        "in UART download mode disabled. "
                        "This is the Flash Encryption configuration for Production mode "
                        "instead of Development mode."
                    )

                crypt_cfg_efuse = self.esp.get_flash_crypt_config()

                if crypt_cfg_efuse is not None and crypt_cfg_efuse != 0xF:
                    print(
                        "Unexpected FLASH_CRYPT_CONFIG value: 0x%x"
                        % (crypt_cfg_efuse)
                    )
                    do_write = False

                enc_key_valid = self.esp.is_flash_encryption_key_valid()

                if not enc_key_valid:
                    print("Flash encryption key is not programmed")
                    do_write = False

            # Determine which files list contain the ones to encrypt
            files_to_encrypt = (
                args.addr_filename if args.encrypt else args.encrypt_files
            )

            for address, argfile in files_to_encrypt:
                if address % self.esp.FLASH_ENCRYPTED_WRITE_ALIGN:
                    print(
                        "File %s address 0x%x is not %d byte aligned, can't flash encrypted"
                        % (
                            argfile.name,
                            address,
                            self.esp.FLASH_ENCRYPTED_WRITE_ALIGN,
                        )
                    )
                    do_write = False

            if not do_write and not args.ignore_flash_encryption_efuse_setting:
                raise esptool.FatalError(
                    "Can't perform encrypted flash write, "
                    "consult Flash Encryption documentation for more information"
                )

        # verify file sizes fit in flash
        if args.flash_size != "keep":  # TODO: check this even with 'keep'
            flash_end = flash_size_bytes(args.flash_size)
            for address, argfile in args.addr_filename:
                argfile.seek(0, os.SEEK_END)
                if address + argfile.tell() > flash_end:
                    raise esptool.FatalError(
                        "File %s (length %d) at offset %d "
                        "will not fit in %d bytes of flash. "
                        "Use --flash_size argument, or change flashing address."
                        % (argfile.name, argfile.tell(), address, flash_end)
                    )
                argfile.seek(0)

        if args.erase_all:
            erase_flash(self.esp, args)
        else:
            for address, argfile in args.addr_filename:
                argfile.seek(0, os.SEEK_END)
                write_end = address + argfile.tell()
                argfile.seek(0)
                bytes_over = address % self.esp.FLASH_SECTOR_SIZE
                if bytes_over != 0:
                    print(
                        "WARNING: Flash address {:#010x} is not aligned "
                        "to a {:#x} byte flash sector. "
                        "{:#x} bytes before this address will be erased.".format(
                            address, self.esp.FLASH_SECTOR_SIZE, bytes_over
                        )
                    )
                # Print the address range of to-be-erased flash memory region
                print(
                    "Flash will be erased from {:#010x} to {:#010x}...".format(
                        address - bytes_over,
                        div_roundup(write_end, self.esp.FLASH_SECTOR_SIZE)
                        * self.esp.FLASH_SECTOR_SIZE
                        - 1,
                    )
                )

        """ Create a list describing all the files we have to flash.
        Each entry holds an "encrypt" flag marking whether the file needs encryption or not.
        This list needs to be sorted.

        First, append to each entry of our addr_filename list the flag args.encrypt
        E.g., if addr_filename is [(0x1000, "partition.bin"), (0x8000, "bootloader")],
        all_files will be [
            (0x1000, "partition.bin", args.encrypt),
            (0x8000, "bootloader", args.encrypt)
            ],
        where, of course, args.encrypt is either True or False
        """
        all_files = [
            (offs, filename, args.encrypt)
            for (offs, filename) in args.addr_filename
        ]
        """
        Now do the same with encrypt_files list, if defined.
        In this case, the flag is True
        """
        if args.encrypt_files is not None:
            encrypted_files_flag = [
                (offs, filename, True)
                for (offs, filename) in args.encrypt_files
            ]

            # Concatenate both lists and sort them.
            # As both list are already sorted, we could simply do a merge instead,
            # but for the sake of simplicity and because the lists are very small,
            # let's use sorted.
            all_files = sorted(
                all_files + encrypted_files_flag, key=lambda x: x[0]
            )

        for address, argfile, encrypted in all_files:
            compress = args.compress

            # Check whether we can compress the current file before flashing
            if compress and encrypted:
                print(
                    "\nWARNING: - compress and encrypt options are mutually exclusive "
                )
                print("Will flash %s uncompressed" % argfile.name)
                compress = False

            if args.no_stub:
                print("Erasing flash...")
            image = pad_to(
                argfile.read(),
                self.esp.FLASH_ENCRYPTED_WRITE_ALIGN if encrypted else 4,
            )
            if len(image) == 0:
                print("WARNING: File %s is empty" % argfile.name)
                continue
            image = self._update_image_flash_params(address, args, image)
            calcmd5 = hashlib.md5(image).hexdigest()
            uncsize = len(image)
            if compress:
                uncimage = image
                image = zlib.compress(uncimage, 9)
                # Decompress the compressed binary a block at a time,
                # to dynamically calculate the timeout based on the real write size
                decompress = zlib.decompressobj()
                blocks = self.esp.flash_defl_begin(
                    uncsize, len(image), address
                )
            else:
                blocks = self.esp.flash_begin(
                    uncsize, address, begin_rom_encrypted=encrypted
                )
            argfile.seek(0)  # in case we need it again
            seq = 0
            bytes_sent = 0  # bytes sent on wire
            bytes_written = 0  # bytes written to flash
            t = time.time()

            timeout = DEFAULT_TIMEOUT

            while len(image) > 0:
                update_flash_bootloader_form_progress_bar(
                    100 * (seq + 1) // blocks
                )
                # progressBar.setValue(100 * (seq + 1) // blocks)
                print(100 * (seq + 1) // blocks)
                print_overwrite(
                    "Writing at 0x%08x... (%d %%)"
                    % (address + bytes_written, 100 * (seq + 1) // blocks)
                )
                sys.stdout.flush()
                block = image[0 : self.esp.FLASH_WRITE_SIZE]
                if compress:
                    # feeding each compressed block into the decompressor lets us
                    # see block-by-block how much will be written
                    block_uncompressed = len(decompress.decompress(block))
                    bytes_written += block_uncompressed
                    block_timeout = max(
                        DEFAULT_TIMEOUT,
                        timeout_per_mb(
                            ERASE_WRITE_TIMEOUT_PER_MB, block_uncompressed
                        ),
                    )
                    if not self.esp.IS_STUB:
                        timeout = block_timeout  # ROM code writes block to flash before ACKing
                    self.esp.flash_defl_block(block, seq, timeout=timeout)
                    if self.esp.IS_STUB:
                        # Stub ACKs when block is received,
                        # then writes to flash while receiving the block after it
                        timeout = block_timeout
                else:
                    # Pad the last block
                    block = block + b"\xff" * (
                        self.esp.FLASH_WRITE_SIZE - len(block)
                    )
                    if encrypted:
                        self.esp.flash_encrypt_block(block, seq)
                    else:
                        self.esp.flash_block(block, seq)
                    bytes_written += len(block)
                bytes_sent += len(block)
                image = image[self.esp.FLASH_WRITE_SIZE :]
                seq += 1

            if self.esp.IS_STUB:
                # Stub only writes each block to flash after 'ack'ing the receive,
                # so do a final dummy operation which will not be 'ack'ed
                # until the last block has actually been written out to flash
                self.esp.read_reg(
                    ESPLoader.CHIP_DETECT_MAGIC_REG_ADDR, timeout=timeout
                )

            t = time.time() - t
            speed_msg = ""
            if compress:
                if t > 0.0:
                    speed_msg = " (effective %.1f kbit/s)" % (
                        uncsize / t * 8 / 1000
                    )
                print_overwrite(
                    "Wrote %d bytes (%d compressed) at 0x%08x in %.1f seconds%s..."
                    % (uncsize, bytes_sent, address, t, speed_msg),
                    last_line=True,
                )
            else:
                if t > 0.0:
                    speed_msg = " (%.1f kbit/s)" % (
                        bytes_written / t * 8 / 1000
                    )
                print_overwrite(
                    "Wrote %d bytes at 0x%08x in %.1f seconds%s..."
                    % (bytes_written, address, t, speed_msg),
                    last_line=True,
                )

            if not encrypted and not self.esp.secure_download_mode:
                try:
                    res = self.esp.flash_md5sum(address, uncsize)
                    if res != calcmd5:
                        print("File  md5: %s" % calcmd5)
                        print("Flash md5: %s" % res)
                        print(
                            "MD5 of 0xFF is %s"
                            % (hashlib.md5(b"\xFF" * uncsize).hexdigest())
                        )
                        raise esptool.FatalError(
                            "MD5 of file does not match data in flash!"
                        )
                    else:
                        print("Hash of data verified.")
                except esptool.NotImplementedInROMError:
                    pass

        print("\nLeaving...")

        if self.esp.IS_STUB:
            # skip sending flash_finish to ROM loader here,
            # as it causes the loader to exit and run user code
            self.esp.flash_begin(0, 0)

            # Get the "encrypted" flag for the last file flashed
            # Note: all_files list contains triplets like:
            # (address: Integer, filename: String, encrypted: Boolean)
            last_file_encrypted = all_files[-1][2]

            # Check whether the last file flashed was compressed or not
            if args.compress and not last_file_encrypted:
                self.esp.flash_defl_finish(False)
            else:
                self.esp.flash_finish(False)

        if args.verify:
            print("Verifying just-written flash...")
            print(
                "(This option is deprecated, "
                "flash contents are now always read back after flashing.)"
            )
            # If some encrypted files have been flashed,
            # print a warning saying that we won't check them
            if args.encrypt or args.encrypt_files is not None:
                print(
                    "WARNING: - cannot verify encrypted files, they will be ignored"
                )
            # Call verify_flash function only if there is at least
            # one non-encrypted file flashed
            if not args.encrypt:
                verify_flash(self.esp, args)

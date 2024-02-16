# importing libraries
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QPalette, QColor
from PyQt6 import QtGui
import sys
import requests
import json
import time
import threading
import serial
import serial.tools.list_ports
import base64
import os
import struct
import zlib
import hashlib
import io


import espefuse
import esptool
from esptool.loader import (
    DEFAULT_CONNECT_ATTEMPTS,
    DEFAULT_TIMEOUT,
    ERASE_WRITE_TIMEOUT_PER_MB,
    ESPLoader,
    timeout_per_mb,
)
from esptool.bin_image import ELFFile, ImageSegment, LoadFirmwareImage
from esptool.util import (
    div_roundup,
    flash_size_bytes,
    hexify,
    pad_to,
    print_overwrite,
)
from esptool.loader import ESPLoader, list_ports
from esptool.cmds import (
    chip_id,
    detect_chip,
    detect_flash_size,
    dump_mem,
    elf2image,
    erase_flash,
    erase_region,
    flash_id,
    get_security_info,
    image_info,
    load_ram,
    make_image,
    merge_bin,
    read_flash,
    read_flash_status,
    read_mac,
    read_mem,
    run,
    verify_flash,
    version,
    write_flash,
    write_flash_status,
    write_mem,
)


from collections import namedtuple

DefChip = namedtuple("DefChip", ["chip_name", "efuse_lib", "chip_class"])
base_url = "https://app.trackloisirs.com/api"

import espefuse.efuse.esp32 as esp32_efuse
import espefuse.efuse.esp32c2 as esp32c2_efuse
import espefuse.efuse.esp32c3 as esp32c3_efuse
import espefuse.efuse.esp32c6 as esp32c6_efuse
import espefuse.efuse.esp32h2 as esp32h2_efuse
import espefuse.efuse.esp32h2beta1 as esp32h2beta1_efuse
import espefuse.efuse.esp32s2 as esp32s2_efuse
import espefuse.efuse.esp32s3 as esp32s3_efuse
import espefuse.efuse.esp32s3beta2 as esp32s3beta2_efuse

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

CHIP_LIST = list(CHIP_DEFS.keys())
ROM_LIST = list(CHIP_DEFS.values())


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


def _update_image_flash_params(esp, address, args, image):
    """
    Modify the flash mode & size bytes if this looks like an executable bootloader image
    """
    if len(image) < 8:
        return image  # not long enough to be a bootloader image

    # unpack the (potential) image header
    magic, _, flash_mode, flash_size_freq = struct.unpack("BBBB", image[:4])
    if address != esp.BOOTLOADER_FLASH_OFFSET:
        return image  # not flashing bootloader offset, so don't modify this

    if (args.flash_mode, args.flash_freq, args.flash_size) == ("keep",) * 3:
        return image  # all settings are 'keep', not modifying anything

    # easy check if this is an image: does it start with a magic byte?
    if magic != esp.ESP_IMAGE_MAGIC:
        print(
            "Warning: Image file at 0x%x doesn't look like an image file, "
            "so not changing any flash settings." % address
        )
        return image

    # make sure this really is an image, and not just data that
    # starts with esp.ESP_IMAGE_MAGIC (mostly a problem for encrypted
    # images that happen to start with a magic byte
    try:
        test_image = esp.BOOTLOADER_IMAGE(io.BytesIO(image))
        test_image.verify()
    except Exception:
        print(
            "Warning: Image file at 0x%x is not a valid %s image, "
            "so not changing any flash settings." % (address, esp.CHIP_NAME)
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
        new_flash_freq = esp.parse_flash_freq_arg(args.flash_freq)
        if flash_freq != new_flash_freq and sha_implies_keep:
            print_keep_warning("frequency", args.flash_freq)
        else:
            flash_freq = new_flash_freq

    flash_size = flash_size_freq & 0xF0
    if args.flash_size != "keep":
        new_flash_size = esp.parse_flash_size_arg(args.flash_size)
        if flash_size != new_flash_size and sha_implies_keep:
            print_keep_warning("size", args.flash_size)
        else:
            flash_size = new_flash_size

    flash_params = struct.pack(b"BB", flash_mode, flash_size + flash_freq)
    if flash_params != image[2:4]:
        print("Flash params set to 0x%04x" % struct.unpack(">H", flash_params))
        image = image[0:2] + flash_params + image[4:]
    return image


class Dict2Class(object):

    def __init__(self, my_dict):

        for key in my_dict:
            setattr(self, key, my_dict[key])


class Color(QWidget):

    def __init__(self, color):
        super(Color, self).__init__()
        self.setAutoFillBackground(True)

        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(color))
        self.setPalette(palette)


class SelectTrackerLayout(QVBoxLayout):
    def __init__(self, accessToken, SerialManager):
        super(SelectTrackerLayout, self).__init__()
        self.accessToken = accessToken
        self.SerialManager = SerialManager
        self.filteredTorqeedoTrackersList = []

        self.checkBoxNewtrackeronlyState = 0
        self.trackerFilterText = ""

        # Initialisation de QLineEdit pour la recherche
        self.searchLineEdit = QLineEdit()
        self.searchLineEdit.setPlaceholderText("Type to filter...")
        self.searchLineEdit.textChanged.connect(self.filterTrackers)
        # Connexion du signal de changement de texte

        # Checkbox checkBoxNewtrackeronly
        self.checkBoxNewtrackeronly = QCheckBox("No ping only")
        self.checkBoxNewtrackeronly.stateChanged.connect(self.checkboxChanged)

        # Configuration existante du QComboBox
        self.torqeedoIdComboBox = QComboBox()
        self.torqeedoIdComboBox.setEditable(True)
        self.torqeedoIdComboBox.currentIndexChanged.connect(
            self.select_tracker
        )

        self.refreshBtn = QPushButton()
        self.refreshBtn.setText("Refresh list")
        self.refreshBtn.clicked.connect(self.click_refresh)

        # Ajout de QLineEdit et QComboBox au layout
        self.addWidget(self.searchLineEdit)
        self.addWidget(self.checkBoxNewtrackeronly)
        self.addWidget(self.torqeedoIdComboBox)
        self.addWidget(self.refreshBtn)
        self.click_refresh()  # Appel initial pour remplir la liste

    def click_refresh(self):
        print("Refresh list")
        # request to get the torqeedo id list
        url = base_url + "/backend/pythonProgrammer/getTorqeedoControllersList"
        headers = {"authorization": "Bearer " + self.accessToken}
        res = requests.get(url, headers=headers, timeout=5)
        res = res.json()

        if res["status"] == 200:
            self.torqeedoIdList = res["data"]
            self.torqeedoIdComboBox.clear()
            print(self.torqeedoIdList)
            self.torqeedoIdComboBox.addItems(
                [item["kingwoId"] for item in self.torqeedoIdList]
            )
            self.filter(
                self.checkBoxNewtrackeronlyState, self.trackerFilterText
            )
        else:
            if hasattr(self, "getTorqeedoIdError"):
                self.getTorqeedoIdError.setText(res["message"])
            else:
                self.getTorqeedoIdError = QLabel(res["message"])
                # self.selectTorqeedoIdLayout.addRow(self.getTorqeedoIdError)

    def select_tracker(self, id):
        if id > 0:
            print("Selected tracker :")
            print(id)
            print(self.filteredTorqeedoTrackersList)
            print(self.filteredTorqeedoTrackersList[id])
            self.SerialManager.setSelectedTracker(
                self.filteredTorqeedoTrackersList[id]
            )

    def checkboxChanged(self, state):
        print("Checkbox changed")
        print(state)
        self.checkBoxNewtrackeronlyState = state
        self.filter(self.checkBoxNewtrackeronlyState, self.trackerFilterText)

    def filterTrackers(self, text):
        self.trackerFilterText = text
        self.filter(self.checkBoxNewtrackeronlyState, self.trackerFilterText)

    def filter(self, state, text):
        # Filtrage des trackers basé sur le texte saisi
        kingwoIdFilteredList = []
        if text == "":
            kingwoIdFilteredList = self.torqeedoIdList
        else:
            for item in self.torqeedoIdList:
                if text.lower() in item["kingwoId"].lower():
                    kingwoIdFilteredList.append(item)
        finalFilteredList = []
        # Filtrage des trackers basé sur l'état de la case à cocher
        if state == 2:
            print("Filtering only new tracker")
            for i in kingwoIdFilteredList:
                if (
                    i["lastPing"] is None
                    or i["lastPing"] == "null"
                    or i["lastPing"] == ""
                    or i["lastPing"] == 0
                ):
                    finalFilteredList.append(i)
        else:
            finalFilteredList = kingwoIdFilteredList
        self.filteredTorqeedoTrackersList = finalFilteredList
        self.torqeedoIdComboBox.clear()
        filtered_id_list = [i["kingwoId"] for i in finalFilteredList]
        self.torqeedoIdComboBox.addItems(filtered_id_list)


def hexify(bitstring, separator=""):
    as_bytes = tuple(b for b in bitstring)
    return separator.join(("%02x" % b) for b in as_bytes)


class ResultTestLayout(QVBoxLayout):

    def __init__(self):
        super(ResultTestLayout, self).__init__()

        self.serialConnected = False
        self.selectedSerialPort = None

        self.SerialLayout = QVBoxLayout()

        self.addLayout(self.SerialLayout)

        self.resetESP32ForAResult = QLabel(
            "Click on Restart ESP32 for a result"
        )
        self.SerialLayout.addWidget(self.resetESP32ForAResult)

    def checkPartTableArray(self, partArray):
        if partArray == [
            ["0", "nvs", "WiFi", "data", "01", "02", "00018000"],
            ["1", "otadata", "OTA", "data", "01", "00", "0001e000"],
            ["2", "app0", "OTA", "app", "00", "10", "00020000"],
            ["3", "app1", "OTA", "app", "00", "11", "00200000"],
            ["4", "spiffs", "Unknown", "data", "01", "82", "003f0000"],
        ]:
            return True
        return False

    def resetLayout(self):
        try:
            self.resetESP32ForAResult.deleteLater()
        except:
            pass

        try:
            self.esp32CommError.deleteLater()
        except:
            pass

        try:
            self.secureBootV2Enabled.deleteLater()
            self.secureBootV2CheckOK.deleteLater()
            self.appCompileTime.deleteLater()
            self.projectName.deleteLater()
            self.appVersion.deleteLater()
            self.partTableDesc.deleteLater()
            self.secureBootV2EnabledBootloaderStage2.deleteLater()
            self.secureBootV2CheckOKBootloader.deleteLater()

        except:
            pass

        self.resetESP32ForAResult = QLabel("Click on Reset ESP32 for a result")
        self.SerialLayout.addWidget(self.resetESP32ForAResult)

    def setInfosText(self, infoArray):
        print(infoArray)
        """
        infosAboutTracker["DEBUG"] = []
        
        """

        # self.resetESP32ForAResult.destroy()
        try:
            self.resetESP32ForAResult.deleteLater()
        except:
            pass

        try:
            self.esp32CommError.deleteLater()
        except:
            pass

        try:
            self.secureBootV2EnabledBootloader.deleteLater()
            self.secureBootV2CheckOK.deleteLater()
            self.projectName.deleteLater()
            self.partTableDesc.deleteLater()
            self.secureBootV2CheckOKBootloader.deleteLater()
            self.secureBootV2EnabledBootloaderStage2.deleteLater()
            self.aes128Key.deleteLater()
            self.versionNumber.deleteLater()
            self.trackerGpsId.deleteLater()
            self.wifiBackupSsid.deleteLater()
            self.mode.deleteLater()
            self.debug.deleteLater()
            self.realCompilationTime.deleteLater()
        except:
            pass

        if "error" in infoArray:
            self.secureBootV2Enabled = QLabel(infoArray["error"])
            self.SerialLayout.addWidget(self.secureBootV2Enabled)
            return

        self.secureBootV2EnabledBootloader = QLabel(
            'Secure boot v2 enabled in first bootloader: <font color="blue">%s</font>'
            % str(infoArray["secureBootV2EnabledBootloader"])
        )
        self.SerialLayout.addWidget(self.secureBootV2EnabledBootloader)
        self.secureBootV2CheckOKBootloader = QLabel(
            'Signed second bootloader check ok : <font color="blue">%s</font>'
            % str(infoArray["secureBootV2CheckOKBootloader"])
        )
        self.SerialLayout.addWidget(self.secureBootV2CheckOKBootloader)
        self.secureBootV2EnabledBootloaderStage2 = QLabel(
            'Secure boot v2 enabled in second bootloader : <font color="blue">%s</font>'
            % str(infoArray["secureBootV2EnabledBootloaderStage2"])
        )
        self.SerialLayout.addWidget(self.secureBootV2EnabledBootloaderStage2)
        self.secureBootV2CheckOK = QLabel(
            'Signed firmware check ok : <font color="blue">%s</font>'
            % str(infoArray["secureBootV2CheckOKFirmware"])
        )
        self.SerialLayout.addWidget(self.secureBootV2CheckOK)

        self.projectName = QLabel(
            'Firmware project name : <font color="blue">%s</font>'
            % str(infoArray["projectName"])
        )
        self.SerialLayout.addWidget(self.projectName)
        self.aes128Key = QLabel(
            '4 first char of aes key: <font color="blue">%s</font>'
            % str(infoArray["AES128_KEY"])
        )
        self.SerialLayout.addWidget(self.aes128Key)
        self.versionNumber = QLabel(
            'Firmware Version Number: <font color="blue">%s</font>'
            % str(infoArray["VERSION_NUMBER"])
        )
        self.SerialLayout.addWidget(self.versionNumber)
        self.trackerGpsId = QLabel(
            'Tracker kingwo id: <font color="blue">%s</font>'
            % str(infoArray["TRACKER_GPS_ID"])
        )
        self.SerialLayout.addWidget(self.trackerGpsId)
        self.wifiBackupSsid = QLabel(
            'Wifi backup SSID: <font color="blue">%s</font>'
            % str(infoArray["WIFI_BACKUP_SSID"])
        )
        self.SerialLayout.addWidget(self.wifiBackupSsid)
        self.mode = QLabel(
            'MODE: <font color="blue">%s</font>' % str(infoArray["MODE"])
        )
        self.SerialLayout.addWidget(self.mode)
        self.realCompilationTime = QLabel(
            'Compilation time: <font color="blue">%s</font>'
            % str(infoArray["REAL_COMPILATION_TIME"])
        )
        self.SerialLayout.addWidget(self.realCompilationTime)

        if len(infoArray["DEBUG"]) == 0:
            debugsList = "No debug"
        else:
            debugsList = ""
            for deb in infoArray["DEBUG"]:
                debugsList = debugsList + deb + " "

        self.realCompilationTime = QLabel(
            'Debug activés : <font color="blue">%s</font>' % str(debugsList)
        )
        self.SerialLayout.addWidget(self.realCompilationTime)

        partTableCheckOk = self.checkPartTableArray(infoArray["partTableDesc"])

        self.partTableDesc = QLabel(
            'PartTable check : <font color="blue">%s</font>'
            % str(partTableCheckOk)
        )
        self.SerialLayout.addWidget(self.partTableDesc)


class ManageSerialLayout(QVBoxLayout):

    def get_default_connected_device(
        self,
        serial_list,
        port,
        connect_attempts,
        initial_baud,
        chip="auto",
        trace=False,
        before="default_reset",
    ):
        _esp = None
        for each_port in reversed(serial_list):
            print("Serial port %s" % each_port)
            try:
                if chip == "auto":
                    _esp = detect_chip(
                        each_port,
                        initial_baud,
                        before,
                        trace,
                        connect_attempts,
                    )
                    self.labelTestSerial.setText("ESP connected")
                else:
                    chip_class = CHIP_DEFS[chip]
                    _esp = chip_class(each_port, initial_baud, trace)
                    _esp.connect(before, connect_attempts)
                    self.labelTestSerial.setText("ESP connected")
                break
            except (esptool.FatalError, OSError) as err:
                self.labelTestSerial.setText("Can't connect")
                self.labelMacAddr.setText("MAC Addr: ")
                print("handle")
                if str(
                    "Failed to connect to Espressif device: No serial data received."
                ) in str(err):
                    print("no serial data")
                    self.labelTestSerial.setText("ESP not connected (no data)")
                if str(
                    "Failed to connect to ESP32: Invalid head of packet (0x01): Possible serial noise or corruption."
                ) in str(err):
                    print("connected but corrupted data")
                    self.labelTestSerial.setText(
                        "ESP not connected (maybe already connected to another software, please kill it)"
                    )

                print("%s failed to connect: %s" % (each_port, err))
                if _esp and _esp._port:
                    _esp._port.close()
                _esp = None
        return _esp

    def is_abs_done_fuse_ok(self):
        for efu in self.efuse[0].efuses:
            if efu.name == "ABS_DONE_1":
                print(efu.name)
                print(efu.get())
                return efu.get()
        return False

    def is_the_same_block2(self):
        if not (self.signHashKeyReady == True and self.efuse != None):
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

    def get_efuses(
        self, esp, skip_connect=False, debug_mode=True, do_not_confirm=False
    ):
        for name in SUPPORTED_CHIPS:
            print(esp.CHIP_NAME)
            if SUPPORTED_CHIPS[name].chip_name == esp.CHIP_NAME:
                efuse = SUPPORTED_CHIPS[name].efuse_lib
                return (
                    efuse.EspEfuses(
                        esp, skip_connect, debug_mode, do_not_confirm
                    ),
                    efuse.operations,
                )
        else:
            raise esptool.FatalError(
                "get_efuses: Unsupported chip (%s)" % esp.CHIP_NAME
            )

    def reset_run_esp(self, esp):
        esp.hard_reset()

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

    def burn_key(self, esp, efuses, blk, key, no_protect_key, args):
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

    def flash_id(self, esp):
        """
        (manufacturer, device, flash_size, flash_type)
        """
        val = {}
        try:
            flash_id = esp.flash_id()
            val["manufacturer"] = flash_id & 0xFF
            flid_lowbyte = (flash_id >> 16) & 0xFF
            val["device"] = ((flash_id >> 8) & 0xFF, flid_lowbyte)
            val["flash_size"] = DETECTED_FLASH_SIZES.get(
                flid_lowbyte, "Unknown"
            )
            return val
        except (esptool.FatalError, OSError) as err:
            print(err)

    def write_flash(self, esp, args, progressBar):
        # set args.compress based on default behaviour:
        # -> if either --compress or --no-compress is set, honour that
        # -> otherwise, set --compress unless --no-stub is set
        if args.compress is None and not args.no_compress:
            args.compress = not args.no_stub

        if (
            not args.force
            and esp.CHIP_NAME != "ESP8266"
            and not esp.secure_download_mode
        ):
            # Check if secure boot is active
            if esp.get_secure_boot_enabled():
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
                    image = LoadFirmwareImage(esp.CHIP_NAME, argfile)
                except (esptool.FatalError, struct.error, RuntimeError):
                    continue
                finally:
                    argfile.seek(
                        0
                    )  # LoadFirmwareImage changes the file handle position
                if image.chip_id != esp.IMAGE_CHIP_ID:
                    raise esptool.FatalError(
                        f"{argfile.name} is not an {esp.CHIP_NAME} image. "
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
                    rev = esp.get_chip_revision()
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
                        raise FatalError(
                            f"{error_str}. Use --force to flash anyway."
                        )
                else:
                    # In IDF, image.min_rev is set based on Kconfig option.
                    # For C3 chip, image.min_rev is the Minor revision
                    # while for the rest chips it is the Major revision.
                    if esp.CHIP_NAME == "ESP32-C3":
                        rev = esp.get_minor_chip_version()
                    else:
                        rev = esp.get_major_chip_version()
                    if rev < image.min_rev:
                        raise FatalError(
                            f"{argfile.name} requires chip revision "
                            f"{image.min_rev} or higher (this chip is revision {rev}). "
                            "Use --force to flash anyway."
                        )

        # In case we have encrypted files to write,
        # we first do few sanity checks before actual flash
        if args.encrypt or args.encrypt_files is not None:
            do_write = True

            if not esp.secure_download_mode:
                if esp.get_encrypted_download_disabled():
                    raise FatalError(
                        "This chip has encrypt functionality "
                        "in UART download mode disabled. "
                        "This is the Flash Encryption configuration for Production mode "
                        "instead of Development mode."
                    )

                crypt_cfg_efuse = esp.get_flash_crypt_config()

                if crypt_cfg_efuse is not None and crypt_cfg_efuse != 0xF:
                    print(
                        "Unexpected FLASH_CRYPT_CONFIG value: 0x%x"
                        % (crypt_cfg_efuse)
                    )
                    do_write = False

                enc_key_valid = esp.is_flash_encryption_key_valid()

                if not enc_key_valid:
                    print("Flash encryption key is not programmed")
                    do_write = False

            # Determine which files list contain the ones to encrypt
            files_to_encrypt = (
                args.addr_filename if args.encrypt else args.encrypt_files
            )

            for address, argfile in files_to_encrypt:
                if address % esp.FLASH_ENCRYPTED_WRITE_ALIGN:
                    print(
                        "File %s address 0x%x is not %d byte aligned, can't flash encrypted"
                        % (
                            argfile.name,
                            address,
                            esp.FLASH_ENCRYPTED_WRITE_ALIGN,
                        )
                    )
                    do_write = False

            if not do_write and not args.ignore_flash_encryption_efuse_setting:
                raise FatalError(
                    "Can't perform encrypted flash write, "
                    "consult Flash Encryption documentation for more information"
                )

        # verify file sizes fit in flash
        if args.flash_size != "keep":  # TODO: check this even with 'keep'
            flash_end = flash_size_bytes(args.flash_size)
            for address, argfile in args.addr_filename:
                argfile.seek(0, os.SEEK_END)
                if address + argfile.tell() > flash_end:
                    raise FatalError(
                        "File %s (length %d) at offset %d "
                        "will not fit in %d bytes of flash. "
                        "Use --flash_size argument, or change flashing address."
                        % (argfile.name, argfile.tell(), address, flash_end)
                    )
                argfile.seek(0)

        if args.erase_all:
            erase_flash(esp, args)
        else:
            for address, argfile in args.addr_filename:
                argfile.seek(0, os.SEEK_END)
                write_end = address + argfile.tell()
                argfile.seek(0)
                bytes_over = address % esp.FLASH_SECTOR_SIZE
                if bytes_over != 0:
                    print(
                        "WARNING: Flash address {:#010x} is not aligned "
                        "to a {:#x} byte flash sector. "
                        "{:#x} bytes before this address will be erased.".format(
                            address, esp.FLASH_SECTOR_SIZE, bytes_over
                        )
                    )
                # Print the address range of to-be-erased flash memory region
                print(
                    "Flash will be erased from {:#010x} to {:#010x}...".format(
                        address - bytes_over,
                        div_roundup(write_end, esp.FLASH_SECTOR_SIZE)
                        * esp.FLASH_SECTOR_SIZE
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
                esp.FLASH_ENCRYPTED_WRITE_ALIGN if encrypted else 4,
            )
            if len(image) == 0:
                print("WARNING: File %s is empty" % argfile.name)
                continue
            image = _update_image_flash_params(esp, address, args, image)
            calcmd5 = hashlib.md5(image).hexdigest()
            uncsize = len(image)
            if compress:
                uncimage = image
                image = zlib.compress(uncimage, 9)
                # Decompress the compressed binary a block at a time,
                # to dynamically calculate the timeout based on the real write size
                decompress = zlib.decompressobj()
                blocks = esp.flash_defl_begin(uncsize, len(image), address)
            else:
                blocks = esp.flash_begin(
                    uncsize, address, begin_rom_encrypted=encrypted
                )
            argfile.seek(0)  # in case we need it again
            seq = 0
            bytes_sent = 0  # bytes sent on wire
            bytes_written = 0  # bytes written to flash
            t = time.time()

            timeout = DEFAULT_TIMEOUT

            while len(image) > 0:
                progressBar.setValue(100 * (seq + 1) // blocks)
                print(100 * (seq + 1) // blocks)
                print_overwrite(
                    "Writing at 0x%08x... (%d %%)"
                    % (address + bytes_written, 100 * (seq + 1) // blocks)
                )
                sys.stdout.flush()
                block = image[0 : esp.FLASH_WRITE_SIZE]
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
                    if not esp.IS_STUB:
                        timeout = block_timeout  # ROM code writes block to flash before ACKing
                    esp.flash_defl_block(block, seq, timeout=timeout)
                    if esp.IS_STUB:
                        # Stub ACKs when block is received,
                        # then writes to flash while receiving the block after it
                        timeout = block_timeout
                else:
                    # Pad the last block
                    block = block + b"\xff" * (
                        esp.FLASH_WRITE_SIZE - len(block)
                    )
                    if encrypted:
                        esp.flash_encrypt_block(block, seq)
                    else:
                        esp.flash_block(block, seq)
                    bytes_written += len(block)
                bytes_sent += len(block)
                image = image[esp.FLASH_WRITE_SIZE :]
                seq += 1

            if esp.IS_STUB:
                # Stub only writes each block to flash after 'ack'ing the receive,
                # so do a final dummy operation which will not be 'ack'ed
                # until the last block has actually been written out to flash
                esp.read_reg(
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

            if not encrypted and not esp.secure_download_mode:
                try:
                    res = esp.flash_md5sum(address, uncsize)
                    if res != calcmd5:
                        print("File  md5: %s" % calcmd5)
                        print("Flash md5: %s" % res)
                        print(
                            "MD5 of 0xFF is %s"
                            % (hashlib.md5(b"\xFF" * uncsize).hexdigest())
                        )
                        raise FatalError(
                            "MD5 of file does not match data in flash!"
                        )
                    else:
                        print("Hash of data verified.")
                except NotImplementedInROMError:
                    pass

        print("\nLeaving...")

        if esp.IS_STUB:
            # skip sending flash_finish to ROM loader here,
            # as it causes the loader to exit and run user code
            esp.flash_begin(0, 0)

            # Get the "encrypted" flag for the last file flashed
            # Note: all_files list contains triplets like:
            # (address: Integer, filename: String, encrypted: Boolean)
            last_file_encrypted = all_files[-1][2]

            # Check whether the last file flashed was compressed or not
            if args.compress and not last_file_encrypted:
                esp.flash_defl_finish(False)
            else:
                esp.flash_finish(False)

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
                verify_flash(esp, args)

    def download_and_store(self, endpoint, store_path):
        url = base_url + endpoint
        headers = {
            "authorization": "Bearer " + self.accessToken,
            "torqctrlid": str(self.trackerSelected["torqCtrlId"]),
        }
        res = requests.get(url, headers=headers, timeout=5, stream=True)
        print(res)
        if res.status_code != 200:
            self.labelDownloadContent.setText(res.reason)
            return 0

        path = store_path
        with open(path, "wb") as f:
            total_length = int(res.headers.get("content-length"))
            chunk_size = 1024
            total_chunk = int(total_length / chunk_size)
            current_chunk = 0
            for chunk in res.iter_content(chunk_size=chunk_size):
                if chunk:
                    current_chunk = current_chunk + 1
                    f.write(chunk)
                    f.flush()
        return 200

    def download_thread(self):
        print(self.accessToken)
        # self.downloadProgress.setValue(0)
        url = base_url + "/backend/pythonProgrammer/getHashSigningKey"
        headers = {
            "authorization": "Bearer " + self.accessToken,
            "torqctrlid": str(self.trackerSelected["torqCtrlId"]),
        }

        self.downloadProgress.setValue(0)
        self.labelDownloadContent.setText("In progress ..")

        self.notCurrentlyInDownload = False
        self.activate()

        try:
            res = requests.get(url, headers=headers, timeout=5)
            res = res.json()
            print(res)
            if res["status"] != 200:
                self.labelDownloadContent.setText(res["message"])
                return

            self.signHashKey = base64.b64decode(res["hashkey_b64"])
            self.signHashKeyReady = True
            self.activate()
            # self.downloadProgress.setValue(10)

            st_bootloader = self.download_and_store(
                "/backend/pythonProgrammer/getBootloader", "./bootloader_tmp"
            )
            if not st_bootloader:
                return
            self.signedBootloaderReady = True
            self.downloadProgress.setValue(20)
            self.activate()
            st_parttable = self.download_and_store(
                "/backend/pythonProgrammer/getPartTable", "./part_table_tmp"
            )
            if not st_parttable:
                return
            self.partTableReady = True
            self.downloadProgress.setValue(40)
            self.activate()
            st_signedfirmware = self.download_and_store(
                "/backend/pythonProgrammer/getSignedFirmware", "./firmware_tmp"
            )
            if not st_signedfirmware:
                return
            self.signedFirmwareReady = True
            self.downloadProgress.setValue(100)
            self.labelDownloadContent.setText("Content Downloaded !")

        except:
            self.signedFirmwareReady = False
            self.labelDownloadContent.setText("Download failed !")

        self.notCurrentlyInDownload = True
        self.activate()

    def click_downloadContent(self):
        print("Download Content")

        x = threading.Thread(target=self.download_thread)
        x.start()

    def click_testSerialConnection(self):
        print("test serial")

        self.serialConnected = True
        self.activate()
        self.esp = self.get_default_connected_device(
            [self.selectedSerialPort],
            port=self.selectedSerialPort,
            connect_attempts=1,
            initial_baud=115200,
            chip="esp32",
            trace=False,
            before="default_reset",
        )
        if self.esp is not None:
            mac = self.esp.read_mac()
            desc = self.esp.get_chip_description()
            flash_infos = self.flash_id(self.esp)
            major_rev = self.esp.get_major_chip_version()
            print(mac)
            self.labelMacAddr.setText("MAC Addr: " + str(mac))
            self.efuse = self.get_efuses(self.esp)
            self.absDoneStatus.setText(
                "secure boot ok: " + str(self.is_abs_done_fuse_ok())
            )
            print(self.efuse)
            if self.is_the_same_block2() == 1:
                self.burnHashKeyStatusLabel.setText("Already Burned (same)")
                self.alreadyBurnSame = True
                self.activate()
            elif self.is_the_same_block2() == 0:
                self.burnHashKeyStatusLabel.setText(
                    "Already Burned (not the same)"
                )
                self.compareBurnKeys = True
                self.activate()
            elif self.is_the_same_block2() == -2:
                self.burnHashKeyStatusLabel.setText(
                    "Error, try download content button"
                )
            else:
                self.burnHashKeyStatusLabel.setText("Not burned")

            print(str(self.efuse[0].blocks[2].id))
            print(dir(self.efuse[0].blocks[2]))
            print((self.efuse[0].blocks[2].bitarray))

    def click_burnSignHashKey(self):
        if not self.compareBurnKeys:
            try:
                print("burn hash key")
                self.burnProgress.setValue(0)
                self.burn_efuse(self.esp, self.efuse[0], "ABS_DONE_1", 1, None)
                self.burnProgress.setValue(50)
                time.sleep(0.25)
                self.burn_key(
                    self.esp,
                    self.efuse[0],
                    "secure_boot_v2",
                    self.signHashKey,
                    True,
                    None,
                )
                self.burnProgress.setValue(100)
                self.burnHashKeyStatusLabel.setText("Burned !")
                time.sleep(0.25)
                self.efuse = self.get_efuses(self.esp)
                self.absDoneStatus.setText(
                    "secure boot ok: " + str(self.is_abs_done_fuse_ok())
                )
                if self.is_the_same_block2() != 1:
                    self.burnHashKeyStatusLabel.setText("Burn key failed !!")
            except:
                print("ERROR : can't burn now !")
        else:
            print("compare keys")

    def click_partTable_bootloader_flash(self):
        print("part table and bootloader flash")

        part_table = open("./part_table_tmp", "rb")
        bootloader = open("./bootloader_tmp", "rb")
        self.bootloaderPartTableFlashStatusLabel.setText(
            "Flashing in progress"
        )

        # Namespace(chip='auto', port=None, baud=460800, before='default_reset', after='hard_reset', no_stub=False, trace=False, override_vddsdio=None, connect_attempts=7, operation='write_flash', addr_filename=[(131072, <_io.BufferedReader name='firmware_tmp'>)], erase_all=False,
        # flash_freq='80m', flash_mode='dio', flash_size='4MB', spi_connection=None, no_progress=False, verify=False, encrypt=False, encrypt_files=None, ignore_flash_encryption_efuse_setting=False, force=False, compress=None, no_compress=False)
        args = {
            "chip": "esp32",
            "compress": None,
            "flash_mode": "dio",
            "flash_freq": "80m",
            "no_compress": False,
            "force": True,
            "addr_filename": [(94208, part_table), (4096, bootloader)],
            "encrypt": None,
            "encrypt_files": None,
            "ignore_flash_encryption_efuse_setting": None,
            "flash_size": "4MB",
            "erase_all": False,
            "no_stub": False,
            "verify": None,
        }
        args = Dict2Class(args)
        print(args)

        if not self.esp.IS_STUB:
            self.esp = self.esp.run_stub()
        self.write_flash(self.esp, args, self.bootloaderPartTableFlashProgress)

        self.bootloaderPartTableFlashStatusLabel.setText("flashed !")

    def click_resetHard(self):
        try:
            print("Reset Hardware")
            self.reset_run_esp(self.esp)
            infosAboutTracker = {}
            infosAboutTracker["secureBootV2EnabledBootloader"] = False
            infosAboutTracker["secureBootV2CheckOKFirmware"] = False
            infosAboutTracker["secureBootV2EnabledBootloaderStage2"] = False
            infosAboutTracker["secureBootV2CheckOKBootloader"] = False
            infosAboutTracker["appCompileTime"] = None
            infosAboutTracker["projectName"] = None
            infosAboutTracker["appVersion"] = None
            infosAboutTracker["partTableDesc"] = []
            infosAboutTracker["AES128_KEY"] = None
            infosAboutTracker["VERSION_NUMBER"] = None
            infosAboutTracker["TRACKER_GPS_ID"] = None
            infosAboutTracker["WIFI_BACKUP_SSID"] = None
            infosAboutTracker["DEBUG"] = []
            infosAboutTracker["MODE"] = None
            infosAboutTracker["REAL_COMPILATION_TIME"] = None

            inPartTableDesc = False

            with serial.Serial(
                self.selectedSerialPort, 115200, timeout=1
            ) as ser:
                for i in range(73):
                    try:
                        x = ser.readline().decode()
                        print(x)
                        if "VERSION_NUMBER" in x:
                            print("VERSION NUMBER")
                            print(x)

                            infosAboutTracker["VERSION_NUMBER"] = (
                                x.split("VERSION_NUMBER :")[-1].lstrip()
                            ).split("\x1b")[0]
                        if "AES128_KEY" in x:
                            infosAboutTracker["AES128_KEY"] = (
                                x.split("AES128_KEY :")[-1].lstrip()
                            ).split("\x1b")[0]
                        if "DEBUG :" in x:
                            infosAboutTracker["DEBUG"].append(
                                (x.split("DEBUG :")[-1].lstrip()).split(
                                    "\x1b"
                                )[0]
                            )
                        if "REAL_COMPILATION_TIME" in x:
                            infosAboutTracker["REAL_COMPILATION_TIME"] = (
                                x.split("REAL_COMPILATION_TIME :")[-1].lstrip()
                            ).split("\x1b")[0]
                        if "WIFI_BACKUP_SSID" in x:
                            infosAboutTracker["WIFI_BACKUP_SSID"] = (
                                x.split("WIFI_BACKUP_SSID :")[-1].lstrip()
                            ).split("\x1b")[0]
                        if "TRACKER_GPS_ID" in x:
                            infosAboutTracker["TRACKER_GPS_ID"] = (
                                x.split("TRACKER_GPS_ID :")[-1].lstrip()
                            ).split("\x1b")[0]
                        if "MODE" in x:
                            infosAboutTracker["MODE"] = (
                                x.split("MODE :")[-1].lstrip()
                            ).split("\x1b")[0]
                        if "secure boot v2 enabled" in x:
                            infosAboutTracker[
                                "secureBootV2EnabledBootloader"
                            ] = True
                        if "secure boot verification succeeded" in x:
                            infosAboutTracker[
                                "secureBootV2CheckOKBootloader"
                            ] = True
                        if "Compile time:" in x:
                            infosAboutTracker["appCompileTime"] = (
                                x.split("Compile time:")[-1].lstrip()
                            ).split("\x1b")[0]
                        if "Project name:" in x:
                            infosAboutTracker["projectName"] = (
                                x.split("Project name:")[-1].lstrip()
                            ).split("\x1b")[0]
                        if "App version:" in x:
                            infosAboutTracker["appVersion"] = (
                                x.split("App version:")[-1].lstrip()
                            ).split("\x1b")[0]
                        if "secure_boot_v2: Verifying with RSA-PSS" in x:
                            infosAboutTracker[
                                "secureBootV2EnabledBootloaderStage2"
                            ] = True
                        if (
                            "secure_boot_v2: Signature verified successfully!"
                            in x
                        ):
                            infosAboutTracker[
                                "secureBootV2CheckOKFirmware"
                            ] = True
                        if "Partition Table:" in x:
                            inPartTableDesc = True
                        if "End of partition table" in x:
                            inPartTableDesc = False
                        if inPartTableDesc:
                            # ['(74)', 'boot:', '##', 'Label', 'Usage', 'Type', 'ST', 'Offset']
                            #
                            arr = [
                                b
                                for b in x.split(" ")
                                if b != ""
                                and not "\x1b" in b
                                and not "boot:" in b
                                and not "(" in b
                            ]
                            if arr[0].isnumeric():
                                infosAboutTracker["partTableDesc"].append(arr)
                    except:
                        infosAboutTracker["error"] = (
                            "Can't read serial port (maybe already open by another software ?)"
                        )
                        self.resultTestLayout.setInfosText(infosAboutTracker)
                        print(
                            "Can't read serial port (maybe already open by another software ?)"
                        )
            self.resultTestLayout.setInfosText(infosAboutTracker)
        except:
            print("ERROR : error on booting ESP")

    def click_appFlash(self):
        try:
            print("app flash")
            firmware = open("./firmware_tmp", "rb")
            self.appFlashStatusLabel.setText("Flashed")

            # Namespace(chip='auto', port=None, baud=460800, before='default_reset', after='hard_reset', no_stub=False, trace=False, override_vddsdio=None, connect_attempts=7, operation='write_flash', addr_filename=[(131072, <_io.BufferedReader name='firmware_tmp'>)], erase_all=False,
            # flash_freq='80m', flash_mode='dio', flash_size='4MB', spi_connection=None, no_progress=False, verify=False, encrypt=False, encrypt_files=None, ignore_flash_encryption_efuse_setting=False, force=False, compress=None, no_compress=False)
            args = {
                "compress": None,
                "flash_mode": "dio",
                "flash_freq": "80m",
                "no_compress": False,
                "force": False,
                "addr_filename": [(131072, firmware)],
                "encrypt": None,
                "encrypt_files": None,
                "ignore_flash_encryption_efuse_setting": None,
                "flash_size": "4MB",
                "erase_all": False,
                "no_stub": False,
                "verify": None,
            }
            args = Dict2Class(args)
            print(args)

            if not self.esp.IS_STUB:
                self.esp = self.esp.run_stub()

            self.write_flash(self.esp, args, self.appFlashProgress)

            self.appFlashStatusLabel.setText("App flashed !")
        except:
            print("ERROR: app flash failed")

    def specifySelectedPort(self, selectedSerialPort):
        self.selectedSerialPort = selectedSerialPort
        self.activate()

    def activate(self):

        self.downloadContentBtn.setEnabled(
            self.activ and self.notCurrentlyInDownload
        )

        if self.selectedSerialPort == None or self.selectedSerialPort == False:
            isPortSelected = False
        else:
            isPortSelected = True

        self.testSerialBtn.setEnabled(self.activ and isPortSelected)
        self.burnHashSignKeyBtn.setEnabled(
            self.serialConnected
            and self.signHashKeyReady
            and isPortSelected
            and not self.alreadyBurnSame
        )
        self.appFlashBtn.setEnabled(
            self.serialConnected
            and self.signedFirmwareReady
            and isPortSelected
        )
        self.bootloaderPartTableFlashBtn.setEnabled(
            self.serialConnected
            and self.signedBootloaderReady
            and self.partTableReady
            and isPortSelected
        )
        self.resetHardBtn.setEnabled(self.serialConnected and isPortSelected)

        if self.compareBurnKeys:
            self.burnHashSignKeyBtn.setEnabled(True)
            self.burnHashSignKeyBtn.setText("Compare keys")

    def resetAll(self):
        self.appFlashProgress.setValue(0)
        self.downloadProgress.setValue(0)
        self.burnProgress.setValue(0)
        self.bootloaderPartTableFlashProgress.setValue(0)
        self.labelDownloadContent.setText("Not downloaded")
        self.labelTestSerial.setText("Not connected")
        self.absDoneStatus.setText("secure boot ok: Not checked")
        self.burnHashKeyStatusLabel.setText("Not burned")
        self.appFlashStatusLabel.setText("No app flashed")
        self.bootloaderPartTableFlashStatusLabel = QLabel("Not flashed")

        self.signedFirmwareReady = False
        self.signHashKeyReady = False
        self.alreadyBurnSame = False
        self.compareBurnKeys = False
        self.serialConnected = False
        self.signedBootloaderReady = False
        self.partTableReady = False
        self.notCurrentlyInDownload = True

        self.resultTestLayout.resetLayout()
        self.activate()

    def setSelectedTracker(self, tracker):
        self.resetAll()
        self.serialConnected = False
        self.trackerSelected = tracker
        if self.trackerSelected is None:
            self.activ = False
            self.activate()
            return
        self.activ = True
        self.activate()

    def __init__(self, accessToken, resultTestLayout):
        super(ManageSerialLayout, self).__init__()

        self.resultTestLayout = resultTestLayout
        self.accessToken = accessToken
        self.signedFirmwareReady = False
        self.signHashKeyReady = False
        self.selectedSerialPort = False
        self.alreadyBurnSame = False
        self.compareBurnKeys = False
        self.activ = False
        self.serialConnected = False
        self.signedBootloaderReady = False
        self.partTableReady = False
        self.notCurrentlyInDownload = True

        SerialLayout = QVBoxLayout()

        ###### DOWNLOAD CONTENT ######
        DownloadContentVLayout = QVBoxLayout()

        DownloadContentLayout = QHBoxLayout()

        self.downloadContentBtn = QPushButton()
        self.downloadContentBtn.setText("Download content")
        self.downloadContentBtn.clicked.connect(self.click_downloadContent)

        self.downloadProgress = QProgressBar()

        self.labelDownloadContent = QLabel("Not downloaded")

        DownloadContentLayout.addWidget(self.downloadContentBtn)
        DownloadContentLayout.addWidget(self.labelDownloadContent)
        DownloadContentVLayout.addLayout(DownloadContentLayout)
        DownloadContentVLayout.addWidget(self.downloadProgress)
        SerialLayout.addLayout(DownloadContentVLayout)

        ###### TEST SERIAL CONNECTION ######
        SerialTestLayout = QHBoxLayout()
        SerialTestVLayout = QVBoxLayout()

        self.testSerialBtn = QPushButton()
        self.testSerialBtn.setText("Test Serial Connection")
        # testSerialBtn.move(64,32)
        self.testSerialBtn.clicked.connect(self.click_testSerialConnection)

        self.labelTestSerial = QLabel("Not connected")

        self.absDoneStatus = QLabel("secure boot ok: Not checked")
        self.labelMacAddr = QLabel("MAC Addr: ")

        SerialTestLayout.addWidget(self.testSerialBtn)
        SerialTestLayout.addWidget(self.labelTestSerial)
        SerialTestVLayout.addLayout(SerialTestLayout)
        SerialTestVLayout.addWidget(self.absDoneStatus)
        SerialTestVLayout.addWidget(self.labelMacAddr)

        SerialLayout.addLayout(SerialTestVLayout)

        ###### EFUSE SIGN KEY ######
        SerialBurnKeyVLayout = QVBoxLayout()

        SerialBurnKeyLayout = QHBoxLayout()

        self.burnHashSignKeyBtn = QPushButton()
        self.burnHashSignKeyBtn.setText("Burn Sign Hash Key")
        # testSerialBtn.move(64,32)
        self.burnHashSignKeyBtn.clicked.connect(self.click_burnSignHashKey)

        self.burnProgress = QProgressBar()

        self.burnHashKeyStatusLabel = QLabel("Not burned")

        SerialBurnKeyLayout.addWidget(self.burnHashSignKeyBtn)
        SerialBurnKeyLayout.addWidget(self.burnHashKeyStatusLabel)
        SerialBurnKeyVLayout.addLayout(SerialBurnKeyLayout)
        SerialBurnKeyVLayout.addWidget(self.burnProgress)

        SerialLayout.addLayout(SerialBurnKeyVLayout)

        ###### Bootloader and part table ######
        SerialBootloaderPartTableFlashVLayout = QVBoxLayout()

        SerialBootloaderPartTableFlashLayout = QHBoxLayout()

        self.bootloaderPartTableFlashBtn = QPushButton()
        self.bootloaderPartTableFlashBtn.setText(
            "Flash Bootloader and part table"
        )
        # testSerialBtn.move(64,32)
        self.bootloaderPartTableFlashBtn.clicked.connect(
            self.click_partTable_bootloader_flash
        )

        self.bootloaderPartTableFlashProgress = QProgressBar()

        self.bootloaderPartTableFlashStatusLabel = QLabel("Not flashed")

        SerialBootloaderPartTableFlashLayout.addWidget(
            self.bootloaderPartTableFlashBtn
        )
        SerialBootloaderPartTableFlashLayout.addWidget(
            self.bootloaderPartTableFlashStatusLabel
        )
        SerialBootloaderPartTableFlashVLayout.addLayout(
            SerialBootloaderPartTableFlashLayout
        )
        SerialBootloaderPartTableFlashVLayout.addWidget(
            self.bootloaderPartTableFlashProgress
        )

        SerialLayout.addLayout(SerialBootloaderPartTableFlashVLayout)

        ###### Flash App ######
        SerialAppFlashVLayout = QVBoxLayout()

        SerialAppFlashLayout = QHBoxLayout()

        self.appFlashBtn = QPushButton()
        self.appFlashBtn.setText("Flash App")
        # testSerialBtn.move(64,32)
        self.appFlashBtn.clicked.connect(self.click_appFlash)

        self.appFlashProgress = QProgressBar()

        self.appFlashStatusLabel = QLabel("No app flashed")

        SerialAppFlashLayout.addWidget(self.appFlashBtn)
        SerialAppFlashLayout.addWidget(self.appFlashStatusLabel)
        SerialAppFlashVLayout.addLayout(SerialAppFlashLayout)
        SerialAppFlashVLayout.addWidget(self.appFlashProgress)

        SerialLayout.addLayout(SerialAppFlashVLayout)

        ###### Reset ESP ######
        SerialResetHardLayout = QHBoxLayout()

        self.resetHardBtn = QPushButton()
        self.resetHardBtn.setText("Restart ESP32 and obtain boot info")
        # testSerialBtn.move(64,32)
        self.resetHardBtn.clicked.connect(self.click_resetHard)

        SerialResetHardLayout.addWidget(self.resetHardBtn)
        SerialLayout.addLayout(SerialResetHardLayout)

        self.addLayout(SerialLayout)
        self.setSelectedTracker(None)


class SerialCP2102Layout(QVBoxLayout):

    def getSelectedSerialPort(self):
        return self.SelectedSerialPort

    def click_refreshSerialList(self):
        print("refresh serial ports")
        self.serialPortsComboBox.clear()
        self.SerialPortsReady = []
        myports = [tuple(p) for p in list(serial.tools.list_ports.comports())]
        for port in myports:
            if port[1].__contains__("CP2102"):
                print("a port seems usable for programming : " + port[0])
                self.serialPortsComboBox.addItems([port[0]])
                self.SerialPortsReady.append(port[0])
        if len(myports) == 0:
            print(
                "No port ready for programming, please check port connection"
            )

    def click_connectProgrammer(self):
        if self.serialPortsComboBox.currentIndex() < 0:
            self.SelectedSerialPort = None
            print("Selected Serial port : None")
            return
        self.SelectedSerialPort = self.SerialPortsReady[
            self.serialPortsComboBox.currentIndex()
        ]
        print("debug victor")
        print(self.serialPortsComboBox.currentIndex())
        print(self.SerialPortsReady)

        print("Selected Serial port : " + str(self.SelectedSerialPort))
        self.SerialLayout.specifySelectedPort(self.SelectedSerialPort)

    def __init__(self, serialLayout):
        super(SerialCP2102Layout, self).__init__()
        self.SerialLayout = serialLayout

        serialCP2102Layout = QVBoxLayout()
        self.SelectedSerialPort = None

        self.refreshBtn = QPushButton()
        self.refreshBtn.setText("Refresh Serial Ports")
        self.refreshBtn.clicked.connect(self.click_refreshSerialList)

        self.SerialPortsList = ["Select"]
        self.serialPortsComboBox = QComboBox()
        self.serialPortsComboBox.addItems(self.SerialPortsList)
        self.serialPortsComboBox.setEditable(True)

        self.connectProgrammer = QPushButton()
        self.connectProgrammer.setText("Connect to programmer")
        self.connectProgrammer.clicked.connect(self.click_connectProgrammer)

        serialCP2102Layout.addWidget(self.refreshBtn)
        serialCP2102Layout.addWidget(self.serialPortsComboBox)
        serialCP2102Layout.addWidget(self.connectProgrammer)

        self.addLayout(serialCP2102Layout)
        self.click_refreshSerialList()


class MainWindow(QDialog):

    def __init__(self, accessToken):
        super(MainWindow, self).__init__()

        self.accessToken = accessToken

        self.setWindowTitle("TorqeedoProgrammer")

        # setting geometry to the window
        self.setGeometry(100, 100, 900, 500)

        outerLayout = QHBoxLayout()
        selectTrackerLayout = QVBoxLayout()

        manageSerialLayout = QVBoxLayout()

        frame3 = QFrame()
        frame3.setFrameShape(QFrame.Shape.StyledPanel)
        frame3.setLineWidth(3)

        frame4 = QFrame()
        frame4.setFrameShape(QFrame.Shape.StyledPanel)
        frame4.setLineWidth(3)

        resultTestLayout = ResultTestLayout()
        SerialLayout = ManageSerialLayout(self.accessToken, resultTestLayout)

        serialCP2102Layout = SerialCP2102Layout(SerialLayout)
        TrackerLayout = SelectTrackerLayout(self.accessToken, SerialLayout)

        frame3.setLayout(TrackerLayout)
        frame4.setLayout(serialCP2102Layout)

        selectTrackerLayout.addWidget(frame3)
        selectTrackerLayout.addWidget(frame4)

        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        frame.setLineWidth(3)

        frame.setLayout(SerialLayout)

        manageSerialLayout.addWidget(frame)

        outerLayout.addLayout(selectTrackerLayout)
        outerLayout.addWidget(QLabel("=>"))
        outerLayout.addLayout(manageSerialLayout)
        outerLayout.addWidget(QLabel("=>"))
        outerLayout.addLayout(resultTestLayout)

        self.setLayout(outerLayout)


class ConnectWindow(QDialog):

    # constructor
    def __init__(self):
        super(ConnectWindow, self).__init__()

        # setting window title
        self.setWindowTitle("TorqeedoProgrammer")

        # setting geometry to the window
        self.setGeometry(100, 100, 500, 300)

        # calling the method that create the form
        self.createConnexionForm()

    def createConnexionForm(self):

        # creating a group box
        self.connexionGroupBox = QGroupBox("Connexion")

        # creating a line edit for email connexion
        self.emailLineEdit = QLineEdit()
        self.emailLineEdit.setText("victor.chevillotte@gmail.com")
        # self.emailLineEdit.setFixedSize(350,40)

        # creating a line edit for password connexion
        self.passwordLineEdit = QLineEdit()
        self.passwordLineEdit.setEchoMode(QLineEdit.EchoMode.Password)
        # self.passwordLineEdit.setFixedSize(350,40)

        # creating a form layout
        self.loginLayout = QFormLayout()

        # adding rows
        # for email and adding input text
        self.loginLayout.addRow(QLabel("Email"), self.emailLineEdit)

        # for password and adding input text
        self.loginLayout.addRow(QLabel("Password"), self.passwordLineEdit)

        # setting layout
        self.connexionGroupBox.setLayout(self.loginLayout)

        # creating a dialog button for ok and cancel
        self.connexionButtonBox = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
        )

        # adding action when form is accepted
        self.connexionButtonBox.accepted.connect(self.connectToWebsite)

        # adding action when form is rejected
        self.connexionButtonBox.rejected.connect(self.reject)

        # creating a vertical layout
        self.mainLayout = QVBoxLayout()

        # adding form group box to the layout
        self.mainLayout.addWidget(self.connexionGroupBox)

        # adding button box to the layout
        self.mainLayout.addWidget(self.connexionButtonBox)

        # setting lay out
        self.setLayout(self.mainLayout)

    def checkUserRightToUsePogrammer(self):
        url = base_url + "/backend/pythonProgrammer/getTorqeedoControllersList"
        headers = {"authorization": "Bearer " + self.accessToken}
        res = requests.get(url, headers=headers, timeout=5)
        return res.json()

    def connectToWebsite(self):
        # method to connect to the website
        url = base_url + "/frontend/account/login"
        params = {
            "email": self.emailLineEdit.text(),
            "password": self.passwordLineEdit.text(),
            "remember": "true",
        }

        try:
            res = requests.post(url, json=params)
            if res.status_code != 200:
                if hasattr(self, "connexionError"):
                    self.connexionError.setText(
                        "Echec de la requête avec le serveur (status!=200)"
                    )
                else:
                    self.connexionError = QLabel(
                        "Echec de la requête avec le serveur (status!=200)"
                    )
                    self.loginLayout.addRow(self.connexionError)
                return
            res = res.json()

            if res["status"] == 200:
                self.user = res["user"]
                self.accessToken = res["accessToken"]
                print("res")

                print(res)

                resCheck = self.checkUserRightToUsePogrammer()
                print(resCheck)
                if resCheck["status"] != 200:
                    if hasattr(self, "connexionError"):
                        self.connexionError.setText(resCheck["message"])
                    else:
                        self.connexionError = QLabel(resCheck["message"])
                        self.loginLayout.addRow(self.connexionError)
                    return

                self.mainWindow = MainWindow(self.accessToken)
                self.mainWindow.show()

                self.close()
            else:
                if hasattr(self, "connexionError"):
                    self.connexionError.setText(res["message"])
                else:
                    self.connexionError = QLabel(res["message"])
                    self.loginLayout.addRow(self.connexionError)
        except Exception as e:
            print(e)

            print("can't connect to web server.")
            if hasattr(self, "connexionError"):
                self.connexionError.setText(
                    "Connexion au site internet impossible, verifier connexion internet"
                )
            else:
                self.connexionError = QLabel(
                    "Connexion au site internet impossible, verifier connexion internet"
                )
                self.loginLayout.addRow(self.connexionError)


import subprocess
import sys


# esptool.main(["write_flash", "--flash_mode", "dio" ,"--flash_freq", "80m", "--flash_size", "4MB", "0x20000", "firmware_tmp"])

# main method
if __name__ == "__main__":

    app = QApplication(sys.argv)
    app.setStyleSheet("QWidget{font-size:20px;}")

    connectWindow = ConnectWindow()
    connectWindow.show()

    sys.exit(app.exec())

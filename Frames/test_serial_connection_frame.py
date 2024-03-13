from tkinter.ttk import Label, Button, Frame
from status import (
    BurnHashKeyStatus,
    FirmwareFlashedStatus,
    BootloaderFlashedStatus,
    ConnectToPcbStatus,
)
from torqeedo_programmer import TorqeedoProgrammer
from esp_rom import EspRom
import esptool
from esptool.cmds import detect_chip


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


def get_default_connected_device(
    serial_list: list[str],
    connect_attempts: int,
    initial_baud: int,
    serial_connection_status_label: Label,
    chip="auto",
    trace=False,
    before="default_reset",
) -> esptool.ESP32ROM:
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
                serial_connection_status_label.config(
                    text="Carte électronique connectée"
                )
            else:
                chip_class = CHIP_DEFS[chip]
                _esp = chip_class(each_port, initial_baud, trace)
                _esp.connect(before, connect_attempts)
                serial_connection_status_label.config(
                    text="Carte électronique connectée"
                )
            break
        except (esptool.FatalError, OSError) as err:
            if str(
                "Failed to connect to Espressif device: No serial data received."
            ) in str(err):
                serial_connection_status_label.config(
                    text="Erreur de connexion à la carte électronique (no serial data)"
                )
            elif str(
                "Failed to connect to ESP32: Invalid head of packet (0x01): Possible serial noise or corruption."
            ) in str(err):
                print("connected but corrupted data")
                serial_connection_status_label.config(
                    text="Erreur de connexion à la carte électronique (Vous êtes peut-être déjà connecté à la carte avec un autre logiciel)"
                )
            else:
                serial_connection_status_label.config(
                    text="Erreur de connexion à la carte électronique (erreur indéfinie)"
                )

            print("%s failed to connect: %s" % (each_port, err))
            if _esp and _esp._port:
                _esp._port.close()
            _esp = None
    return _esp


def click_test_serial_connection(
    torqeedo_programmer: TorqeedoProgrammer,
    serial_connection_status_label: Label,
    mac_address_label: Label,
    burn_hash_key_text: str,
):
    print("Test serial connection")
    torqeedo_programmer.selected_controller.connect_to_pcb_status = (
        ConnectToPcbStatus.IN_PROGRESS
    )
    connected_esp = get_default_connected_device(
        [torqeedo_programmer.selected_serial_port],
        connect_attempts=1,
        initial_baud=115200,
        chip="esp32",
        trace=False,
        before="default_reset",
        serial_connection_status_label=serial_connection_status_label,
    )
    if connected_esp is not None:
        esp_rom = EspRom(esp=connected_esp)
        torqeedo_programmer.selected_controller.esp_rom = esp_rom

        esp_rom.mac_address = str(connected_esp.read_mac())
        esp_rom.description = connected_esp.get_chip_description()
        esp_rom.flash_infos = esp_rom.get_flash_id()
        esp_rom.major_rev = connected_esp.get_major_chip_version()
        mac_address_label.config(text="MAC Address: " + esp_rom.mac_address)

        esp_rom.efuses = esp_rom.get_efuses()

        is_the_same_block2 = esp_rom.is_the_same_block2(
            torqeedo_programmer.selected_controller.hashkey_b64
        )

        if is_the_same_block2 == 1:
            torqeedo_programmer.selected_controller.burn_hash_key_status = (
                BurnHashKeyStatus.BURNED_SAME
            )
            esp_rom.already_burned = True
            esp_rom.is_same_hash_key = True
        elif is_the_same_block2 == 0:
            torqeedo_programmer.selected_controller.burn_hash_key_status = (
                BurnHashKeyStatus.BURNED_NOT_SAME
            )
            esp_rom.already_burned = True
            esp_rom.is_same_hash_key = False
        elif is_the_same_block2 == -2:
            torqeedo_programmer.selected_controller.burn_hash_key_status = (
                BurnHashKeyStatus.ERROR
            )
            esp_rom.already_burned = False
            esp_rom.is_same_hash_key = False
        else:
            torqeedo_programmer.selected_controller.burn_hash_key_status = (
                BurnHashKeyStatus.NOT_BURNED
            )
            esp_rom.already_burned = False
            esp_rom.is_same_hash_key = False
        print(burn_hash_key_text)
        torqeedo_programmer.selected_controller.connect_to_pcb_status = (
            ConnectToPcbStatus.CONNECTED
        )
        # print(str(esp_rom.efuses[0].blocks[2].id))
        # print(dir(esp_rom.efuses[0].blocks[2]))
        # print((esp_rom.efuses[0].blocks[2].bitarray))
    else:
        print("No esp connected")
        torqeedo_programmer.selected_controller.connect_to_pcb_status = (
            ConnectToPcbStatus.ERROR
        )
        serial_connection_status_label.config(
            text="Erreur de connexion, vérifiez le branchement"
        )
        torqeedo_programmer.selected_controller.esp_rom = None
        torqeedo_programmer.selected_controller.hashkey_b64 = None
        torqeedo_programmer.selected_controller.burn_hash_key_status = (
            BurnHashKeyStatus.NOT_SCANNED
        )


def render_test_serial_connection_frame(
    middle_column_frame: Frame,
    torqeedo_programmer: TorqeedoProgrammer,
    burn_hash_key_text: str,
):

    test_serial_connection_button = Button(
        middle_column_frame,
        text="Test serial connection",
        command=lambda: click_test_serial_connection(
            torqeedo_programmer,
            serial_connection_status_label,
            mac_address_label,
            burn_hash_key_text,
        ),
    )
    test_serial_connection_button.grid(
        row=3, column=0, columnspan=2, padx=10, pady=5
    )

    serial_connection_status_label = Label(
        middle_column_frame, text="Aucune carte électronique connectée"
    )
    serial_connection_status_label.grid(
        row=4, column=0, columnspan=2, padx=10, pady=5
    )

    secure_boot_status_label = Label(
        middle_column_frame, text="Secure boot status"
    )
    secure_boot_status_label.grid(
        row=5, column=0, columnspan=2, padx=10, pady=5
    )

    mac_address_label = Label(middle_column_frame, text="MAC Address")
    mac_address_label.grid(row=6, column=0, columnspan=2, padx=10, pady=5)

    def check_controller_selected():
        if (
            torqeedo_programmer.selected_controller is None
            or torqeedo_programmer.selected_serial_port is None
        ):
            test_serial_connection_button["state"] = "disabled"
            secure_boot_status_label.config(text="Secure boot status")
            mac_address_label.config(text="MAC Address")
            if torqeedo_programmer.selected_controller is None:
                serial_connection_status_label.config(
                    text="Selectionnez un identifiant"
                )
            else:
                serial_connection_status_label.config(
                    text="Selectionnez un port série"
                )
        else:
            if (
                torqeedo_programmer.selected_controller.bootloader_flashed_status
                == (BootloaderFlashedStatus.IN_PROGRESS)
                or torqeedo_programmer.selected_controller.firmware_flashed_status
                == (FirmwareFlashedStatus.IN_PROGRESS)
                or torqeedo_programmer.selected_controller.connect_to_pcb_status
                == (ConnectToPcbStatus.IN_PROGRESS)
            ):
                test_serial_connection_button["state"] = "disabled"
            else:
                test_serial_connection_button["state"] = "normal"
            if (
                torqeedo_programmer.selected_controller.connect_to_pcb_status
                == ConnectToPcbStatus.IN_PROGRESS
            ):
                serial_connection_status_label.config(
                    text="Connexion en cours"
                )
            elif (
                torqeedo_programmer.selected_controller.esp_rom is None
                and torqeedo_programmer.selected_controller.connect_to_pcb_status
                == ConnectToPcbStatus.NOT_CONNECTED
            ):
                serial_connection_status_label.config(
                    text="Carte électronique non connectée"
                )
                secure_boot_status_label.config(text="Secure boot status")
                mac_address_label.config(text="MAC Address")
                torqeedo_programmer.selected_controller.esp_rom = None
                # torqeedo_programmer.selected_controller.hashkey_b64 = None
        if (
            torqeedo_programmer.selected_controller is not None
            and torqeedo_programmer.selected_controller.esp_rom is not None
        ):
            secure_boot_status_text = "Secure boot ok : " + str(
                torqeedo_programmer.selected_controller.esp_rom.is_abs_done_fuse_ok()
            )
            secure_boot_status_label.config(text=secure_boot_status_text)

        middle_column_frame.after(
            100, check_controller_selected
        )  # Check every 100ms

    check_controller_selected()

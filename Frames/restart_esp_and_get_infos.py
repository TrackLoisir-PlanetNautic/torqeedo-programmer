import asyncio
from tkinter.ttk import Button, Frame
from torqeedo_programmer import TorqeedoProgrammer
import serial
import serial.tools.list_ports
from compilation_result import CompilationResult


async def restart_esp_and_readline(torqeedo_programmer: TorqeedoProgrammer):
    print("restart_esp_and_readline")
    try:
        torqeedo_programmer.selected_controller.esp_rom.restart()
        compilation_result: CompilationResult = CompilationResult()
        inPartTableDesc = False

        with serial.Serial(
            torqeedo_programmer.selected_serial_port, 115200, timeout=1
        ) as ser:
            for i in range(300):
                try:
                    x = ser.readline().decode()
                    print(x)
                    if ("just started" in x):
                        break
                    if "VERSION_NUMBER" in x:
                        compilation_result.VERSION_NUMBER = (
                            x.split("VERSION_NUMBER :")[-1].lstrip()
                        ).split("\x1b")[0]
                    if "AES128_KEY" in x:
                        compilation_result.AES128_KEY = (
                            x.split("AES128_KEY :")[-1].lstrip()
                        ).split("\x1b")[0]
                    if "DEBUG :" in x:
                        compilation_result.DEBUG.append(
                            (x.split("DEBUG :")[-1].lstrip()).split("\x1b")[0]
                        )
                    if "REAL_COMPILATION_TIME" in x:
                        compilation_result.REAL_COMPILATION_TIME = (
                            x.split("REAL_COMPILATION_TIME :")[-1].lstrip()
                        ).split("\x1b")[0]
                    if "WIFI_BACKUP_SSID" in x:
                        compilation_result.WIFI_BACKUP_SSID = (
                            x.split("WIFI_BACKUP_SSID :")[-1].lstrip()
                        ).split("\x1b")[0]
                    if "TRACKER_GPS_ID" in x:
                        compilation_result.TRACKER_GPS_ID = (
                            x.split("TRACKER_GPS_ID :")[-1].lstrip()
                        ).split("\x1b")[0]
                    if "MODE" in x:
                        compilation_result.MODE = (
                            x.split("MODE :")[-1].lstrip()
                        ).split("\x1b")[0]
                    if "secure boot v2 enabled" in x:
                        compilation_result.SECURE_BOOT_V2_ENABLED_BOOTLOADER = (
                            True
                        )
                    if "secure boot verification succeeded" in x:
                        compilation_result.SECURE_BOOT_V2_VERIFIED = True
                    if "Compile time:" in x:
                        compilation_result.COMPILATION_TIME = (
                            x.split("Compile time:")[-1].lstrip()
                        ).split("\x1b")[0]
                    if "Project name:" in x:
                        compilation_result.PROJECT_NAME = (
                            x.split("Project name:")[-1].lstrip()
                        ).split("\x1b")[0]
                    if "App version:" in x:
                        compilation_result.APP_VERSION = (
                            x.split("App version:")[-1].lstrip()
                        ).split("\x1b")[0]
                    if "secure_boot_v2: Verifying with RSA-PSS" in x:
                        compilation_result.SECURE_BOOT_V2_ENABLED_BOOTLOADER_STAGE2 = (
                            True
                        )
                    if "secure_boot_v2: Signature verified successfully!" in x:
                        compilation_result.SECURE_BOOT_V2_CHECK_OK_BOOTLOADER = (
                            True
                        )
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
                            compilation_result.PART_TABLE.append(arr)
                except Exception as e:
                    print(e)
                    compilation_result.ERROR = "Can't read serial port (maybe already open by another software ?)"
                    print(
                        "Can't read serial port (maybe already open by another software ?)"
                    )
        print(compilation_result)
    except Exception as e:
        print(e)
        return


def restart_esp_and_get_infos_clicked(
    torqeedo_programmer: TorqeedoProgrammer,
):
    asyncio.ensure_future(restart_esp_and_readline(torqeedo_programmer))


def render_restart_esp_and_get_infos_frame(
    middle_column_frame: Frame,
    torqeedo_programmer: TorqeedoProgrammer,
):

    restart_esp_and_get_infos_button = Button(
        middle_column_frame,
        text="Restart ESP and get infos",
        command=lambda: restart_esp_and_get_infos_clicked(
            torqeedo_programmer,
        ),
    )
    restart_esp_and_get_infos_button.grid(row=13, column=0, columnspan=2, padx=10, pady=5)

    def restart_esp_and_get_infos_status():
        if (
            torqeedo_programmer.selected_controller is None
            or torqeedo_programmer.selected_controller.esp_rom is None
        ):
            restart_esp_and_get_infos_button["state"] = "disabled"
        else:
            restart_esp_and_get_infos_button["state"] = "normal"

        middle_column_frame.after(
            100, restart_esp_and_get_infos_status
        )  # Check every 100ms

    restart_esp_and_get_infos_status()

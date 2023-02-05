


import espefuse
import esptool
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
import serial.tools.list_ports

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

def check_and_return_serial_ports():
    myports = [tuple(p) for p in list(serial.tools.list_ports.comports())]
    for port in myports:
        if (port[1].__contains__("CP2102")):
            print("a port seems usable for programming : "+ port[0])
            return port[0]
    print("No port ready for programming, please check port connection")
            


check_and_return_serial_ports()

commands = ["--after", "no_reset", "read_mac"]
#print(serial)
#esptool.main(commands)

def get_default_connected_device(
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
                    each_port, initial_baud, before, trace, connect_attempts
                )
            else:
                chip_class = CHIP_DEFS[chip]
                _esp = chip_class(each_port, initial_baud, trace)
                _esp.connect(before, connect_attempts)
            break
        except (FatalError, OSError) as err:
            if port is not None:
                raise
            print("%s failed to connect: %s" % (each_port, err))
            if _esp and _esp._port:
                _esp._port.close()
            _esp = None
    return _esp


def get_port_list():
    if list_ports is None:
        raise FatalError(
            "Listing all serial ports is currently not available. "
            "Please try to specify the port when running esptool.py or update "
            "the pyserial package to the latest version"
        )
    return sorted(ports.device for ports in list_ports.comports())

def flash_id(esp):
    """ 
        (manufacturer, device, flash_size, flash_type)
    """
    val = {}
    flash_id = esp.flash_id()
    val["manufacturer"] = (flash_id & 0xFF)
    flid_lowbyte = (flash_id >> 16) & 0xFF
    val["device"] = ((flash_id >> 8) & 0xFF, flid_lowbyte)
    val["flash_size"] = (DETECTED_FLASH_SIZES.get(flid_lowbyte, "Unknown"))
    return val


    
ser_list = get_port_list()
esp = get_default_connected_device(
            ser_list,
            port=None,
            connect_attempts=1,
            initial_baud=115200,
            chip="auto",
            trace=False,
            before="default_reset",
        )
mac = esp.read_mac()
desc = esp.get_chip_description()
flash_infos = flash_id(esp)
major_rev = esp.get_major_chip_version()


from collections import namedtuple
DefChip = namedtuple("DefChip", ["chip_name", "efuse_lib", "chip_class"])


import espefuse.efuse.esp32 as esp32_efuse
import espefuse.efuse.esp32c2 as esp32c2_efuse
import espefuse.efuse.esp32c3 as esp32c3_efuse
import espefuse.efuse.esp32c6 as esp32c6_efuse
import espefuse.efuse.esp32h2 as esp32h2_efuse
import espefuse.efuse.esp32h2beta1 as esp32h2beta1_efuse
import espefuse.efuse.esp32s2 as esp32s2_efuse
import espefuse.efuse.esp32s3 as esp32s3_efuse
import espefuse.efuse.esp32s3beta2 as esp32s3beta2_efuse

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




def dump(esp, efuses):
    for block in efuses.blocks:
        print(str(block.id))
        print(block.get_bitstring())
        """
            file_dump_name = (
                file_dump_name[:place_for_index]
                + str(block.id)
                + file_dump_name[place_for_index:]
            )
            print(file_dump_name)
            with open(file_dump_name, "wb") as f:
                block.get_bitstring().byteswap()
                block.get_bitstring().tofile(f)
        """

def get_efuses(esp, skip_connect=False, debug_mode=True, do_not_confirm=False):
    for name in SUPPORTED_CHIPS:
        print(esp.CHIP_NAME)

        if SUPPORTED_CHIPS[name].chip_name == esp.CHIP_NAME:
            efuse = SUPPORTED_CHIPS[name].efuse_lib
            return (
                efuse.EspEfuses(esp, skip_connect, debug_mode, do_not_confirm),
                efuse.operations,
            )
    else:
        raise esptool.FatalError("get_efuses: Unsupported chip (%s)" % esp.CHIP_NAME)

#espefuse.main()

def hexify(bitstring, separator=""):
    as_bytes = tuple(b for b in bitstring)
    return separator.join(("%02x" % b) for b in as_bytes)

def burn_key(esp, efuses, blk, key, no_protect_key, args):
    block_name = blk
    #efuses.force_write_always = False


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
        msg += (
            "The key block will left readable and writeable (due to --no-protect-key)"
        )
    else:
        msg += "The key block will be read and write protected "
        "(no further changes or readback)"
    print(msg, "\n")
    if not efuses.burn_all(check_batch_mode=True):
        return
    print("Successful")


print(mac)
print(desc)
print("major rev : "+str(major_rev))
print(flash_infos)

efuse = get_efuses(esp)
print(dir(efuse[0]))
print(efuse[0])
dump(esp, efuse[0])

datafile = open("hash_key_test", "rb")
val_key = datafile.read()
val_key = val_key[0:-1]
print(val_key)
print(len(val_key))
burn_key(esp, efuse[0], "secure_boot_v2", val_key, True, None)



#curl localhost:8080/api/backend/pythonProgrammer/getHashSigningKey -H "Authorization: Bearer eyU2zEi4" -H "torqCtrlId:2"
#curl localhost:8080/api/backend/pythonProgrammer/getSignedFirmware -H "Authorization: Bearer eyJhbc" -H "torqCtrlId:2"
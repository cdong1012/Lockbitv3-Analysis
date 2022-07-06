import idaapi
import idc
import idautils
import json
from aplib import decompress


def decrypt_config(encrypted_string, length):
    v3 = int(length / 0xFF)  # should be 0xA
    v4 = length % 0xFF
    offset = 0
    if v3 != 0:
        v5 = int(length / 0xFF)
        while v5 != 0:
            encrypted_string = decrypt_string(encrypted_string, 255, offset)
            offset += 255
            v5 -= 1
    if v4 != 0:
        encrypted_string = decrypt_string(encrypted_string, v4, offset)

    return encrypted_string


def decrypt_string(encrypted_string, length, offset):
    BUFFER_OFFSET_COUNTER = 0
    BUFFER1_COUNTER = 0
    BUFFER1 = []
    for i in KEY_BUFFER:
        BUFFER1.append(i)
    v2 = 0
    v4 = 0
    curr_index = 0
    v6 = 0

    while length != 0:
        v4 = (BUFFER1[1 + v2] + v4) & 0xFF
        v6 = BUFFER1[1 + v2] & 0xFF
        v7 = BUFFER1[v4] & 0xFF
        BUFFER1[v4] = v6
        BUFFER1[1 + v2] = v7
        v6 = (v7 + v6) & 0xFF
        v2 += 1
        encrypted_string[curr_index + offset] ^= BUFFER1[v6]
        curr_index += 1
        length -= 1
    return encrypted_string


def init_resolve_buffer(key1, key2, length):
    global KEY_BUFFER
    v3 = 240
    v4 = key1[0]
    v5 = key1[1]
    v6 = key1[2]
    v7 = key1[3]

    def _copy_bytes(integer, BUFFER, offset):
        for i in range(0, 4):
            BUFFER[offset + i] = integer & 0xff
            integer >>= 8
        return BUFFER

    while v3 >= 0:
        KEY_BUFFER = _copy_bytes(v4, KEY_BUFFER, v3 + 12)
        KEY_BUFFER = _copy_bytes(v7, KEY_BUFFER, v3 + 8)
        KEY_BUFFER = _copy_bytes(v5, KEY_BUFFER, v3 + 4)
        KEY_BUFFER = _copy_bytes(v6, KEY_BUFFER, v3)
        v4 -= 0x10101010
        v7 -= 0x10101010
        v5 -= 0x10101010
        v6 -= 0x10101010
        v3 -= 16

    lo_v8 = 0
    v9 = 0
    v10 = 0

    while True:
        while True:
            lo_result = KEY_BUFFER[v9] & 0xff
            lo_v8 = (lo_result + ((key2[v10] + lo_v8) & 0xff)) & 0xff
            hi_result = KEY_BUFFER[lo_v8]

            v10 += 1
            KEY_BUFFER[lo_v8] = lo_result
            KEY_BUFFER[v9] = hi_result
            if v10 >= length:
                break
            v9 += 1
            v9 &= 0xff
            if v9 == 0:
                return

        v10 = 0
        v9 += 1
        v9 &= 0xff
        if v9 == 0:
            break


def get_KEY_BUFFER(init_resolve_func_ea):
    global KEY_BUFFER

    if init_resolve_func_ea is None:
        print('get_KEY_BUFFER fails...')
        return None

    ref_ea = None
    for ref in idautils.CodeRefsTo(init_resolve_func_ea, 1):
        # only 1 ref
        ref_ea = ref
        break

    arg_list = [0, 0, 0]

    curr_ea = ref_ea
    for i in range(0, 3):
        while True:
            prev_instruction_ea = idc.prev_head(curr_ea)
            if idc.print_insn_mnem(prev_instruction_ea) == 'push':
                arg_list[i] = idc.get_operand_value(prev_instruction_ea, 0)
                curr_ea = prev_instruction_ea
                break

    key1 = []
    key1_ea = arg_list[0]
    length = arg_list[2]

    while key1_ea < arg_list[0] + length:
        key1.append(int.from_bytes(idaapi.get_bytes(key1_ea, 4), 'little'))

        key1_ea += 4

    key2 = []
    key2_ea = arg_list[1]

    while key2_ea < arg_list[1] + length:
        key2.append(int.from_bytes(idaapi.get_bytes(key2_ea, 1), 'little'))
        key2_ea += 1

    init_resolve_buffer(key1, key2, length)


def translate_ea(offset):
    for s in idautils.Segments():
        if idc.get_segm_name(s) == ".text":
            return offset + s

    print('translate_ea fails..')
    return None


def translate_ea_to_offset(ea):
    for s in idautils.Segments():
        if idc.get_segm_name(s) == ".text":
            return ea - s

    print('translate_ea_to_offset fails...')
    return None


def get_FULL_CONFIG():
    global config_extract_ea, FULL_CONFIG

    # get FULL_CONFIG size
    curr_ea = config_extract_ea
    stop_bytes = 0  # this should be 0xDEADBEEF
    FULL_CONFIG_ea = 0

    while True:
        next_instruction_ea = idc.next_head(curr_ea)
        if idc.print_insn_mnem(next_instruction_ea) == 'cmp':
            stop_bytes = idc.get_operand_value(next_instruction_ea, 1)
            break
        elif idc.print_insn_mnem(next_instruction_ea) == 'lea':
            FULL_CONFIG_ea = idc.get_operand_value(next_instruction_ea, 1)
        curr_ea = next_instruction_ea

    config_length = 0

    while True:
        if int.from_bytes(idaapi.get_bytes(FULL_CONFIG_ea + config_length, 4), 'little') == stop_bytes:
            break
        config_length += 1

    FULL_CONFIG = [each_byte for each_byte in idaapi.get_bytes(
        FULL_CONFIG_ea, config_length)]
    FULL_CONFIG = decrypt_config(FULL_CONFIG, config_length)


def decompress_config():
    global FULL_CONFIG, DECOMPRESSED_CONFIG

    DECOMPRESSED_CONFIG = FULL_CONFIG[0x104:]  # extract compressed config

    DECOMPRESSED_CONFIG = decompress(bytearray(DECOMPRESSED_CONFIG))


# 0x189b, 0x1bfc, 0x472
def parse_config(resolve_config_start_offset, resolve_config_end_offset, memcpy_offset):
    global RAWCONFIG, CONFIG_ORDER

    start_ea = translate_ea(resolve_config_start_offset)
    end_ea = translate_ea(resolve_config_end_offset)
    memcpy_ea = translate_ea(memcpy_offset)

    if start_ea is None or end_ea is None or memcpy_ea is None:
        print('Parse config fails...')
        return

    config_offset_list = []
    skipped = True
    for ref in idautils.CodeRefsTo(memcpy_ea, 1):
        # only 1 ref
        if ref >= start_ea and ref <= end_ea:
            if skipped:  # skip the first memcpy cause it's not config-related
                skipped = False
                continue
            else:
                curr_ea = ref
                while True:
                    prev_instruction_ea = idc.prev_head(curr_ea)
                    if idc.print_insn_mnem(prev_instruction_ea) == 'lea':
                        if "+" not in idc.GetDisasm(prev_instruction_ea):
                            config_offset_list.append(0)
                        else:
                            if idc.get_operand_value(prev_instruction_ea, 1) == 0x20:
                                for i in range(0x20, 0x20 + 24):
                                    config_offset_list.append(i)
                            else:
                                config_offset_list.append(
                                    idc.get_operand_value(prev_instruction_ea, 1))
                        break
                    curr_ea = prev_instruction_ea

    for i in range(0, len(CONFIG_ORDER)):
        print(f"{config_offset_list[i]}: {CONFIG_ORDER[i]}")

    assert(len(config_offset_list) == len(CONFIG_ORDER))

    def extract_config_data(offset, is_string, is_ID):
        global DECOMPRESSED_CONFIG

        if is_string:
            end_offset = offset
            while True:
                temp_buffer = DECOMPRESSED_CONFIG[end_offset:end_offset + 4]
                if temp_buffer[0] == 0 and temp_buffer[1] == 0 and temp_buffer[2] == 0 and temp_buffer[3] == 0:
                    break
                end_offset += 1

            temp_offset = offset
            config_string = ''
            while temp_offset < end_offset:
                temp_buffer = DECOMPRESSED_CONFIG[temp_offset:temp_offset + 3]
                if temp_buffer[0] == 0 and temp_buffer[1] == 0 and temp_buffer[2] == 0:
                    config_string += ', '
                    temp_offset += 3
                elif DECOMPRESSED_CONFIG[temp_offset] != 0:
                    config_string += chr(DECOMPRESSED_CONFIG[temp_offset])
                    temp_offset += 1
                else:
                    temp_offset += 1

            return config_string
        elif is_ID:
            config_string = ''
            for i in range(offset, offset + 32):
                config_string += hex(DECOMPRESSED_CONFIG[i])
                config_string += ', '
            config_string = '[' + config_string[:-2] + ']'
            return config_string
        else:
            config_string = ''
            for i in range(offset, offset + 24):
                config_string += hex(DECOMPRESSED_CONFIG[i])
                config_string += ', '
            config_string = '[' + config_string[:-2] + ']'
            return config_string

    for i in range(0, len(config_offset_list)):
        if i == 0:
            RAWCONFIG[CONFIG_ORDER[i]] = extract_config_data(
                config_offset_list[i], False, True)
        elif i == 1:
            if DECOMPRESSED_CONFIG[config_offset_list[i]] == 1:
                RAWCONFIG[CONFIG_ORDER[i]] = "Full"
            elif DECOMPRESSED_CONFIG[config_offset_list[i]] == 2:
                RAWCONFIG[CONFIG_ORDER[i]] = "Fast"
            else:
                RAWCONFIG[CONFIG_ORDER[i]] = "Auto"
        elif i > 1 and i <= 24:
            RAWCONFIG[CONFIG_ORDER[i]
                      ] = DECOMPRESSED_CONFIG[config_offset_list[i]] == 1
        else:
            RAWCONFIG[CONFIG_ORDER[i]] = extract_config_data(
                config_offset_list[i], True, False)

    return


def decrypt_all_strings(decrypt_string_func_ea):
    global STRING_DICTIONARY
    for ref in idautils.CodeRefsTo(decrypt_string_func_ea, 1):
        # this function can be better. I hate it rn but oh well

        prev_instruction_ea = 0x472DAC if ref == translate_ea(
            0x1db3) else idc.prev_head(ref)

        if idc.print_insn_mnem(prev_instruction_ea) == 'push' or idc.print_insn_mnem(prev_instruction_ea) == 'lea':
            encrypted_blob_ea = idc.get_operand_value(prev_instruction_ea, 1) if ref == translate_ea(
                0x1db3) else idc.get_operand_value(prev_instruction_ea, 0)
            length = int.from_bytes(idaapi.get_bytes(
                encrypted_blob_ea - 4, 4), 'little')
            #print(hex(prev_instruction_ea) + " and " + hex(encrypted_blob_ea) + " and " + hex(length))
            encrypted_blob = [x for x in idaapi.get_bytes(
                encrypted_blob_ea, length)]
            encrypted_blob = decrypt_config(encrypted_blob, length)
            string = ''
            for each in encrypted_blob:
                if each != 0:
                    string += chr(each)
            STRING_DICTIONARY[translate_ea_to_offset(
                encrypted_blob_ea)] = string
            print(string)
    return

BUFFER1 = []
KEY_BUFFER = []
BUFFER1_COUNTER = 0
BUFFER_OFFSET_COUNTER = 0

# CONFIG
config_extract_ea = translate_ea(0x189b)
FULL_CONFIG = []
DECOMPRESSED_CONFIG = []
RAWCONFIG = {}
CONFIG_ORDER = ["VICTIM_ID", "ENCRYPTION_MODE", "AVOID_PROCESS_FLAG",
                "ENCRYPT_ALL_DRIVES_FLAG", "ENCRYPT_NET_SHARED_RESOURCE_FLAG",
                "CHECK_RUSSIAN_COMP_FLAG", "DELETE_SHADOW_COPIES_FLAG",
                "WIPE_RECYCLE_BIN_FLAG", "SELF_DELETE_FLAG", "UAC_ELEVATION_FLAG",
                "AdjustTokenPrivileges_FLAG", "LOGGING_FLAG",
                "DIRECTORY_TO_AVOID_FLAG", "FILE_TO_AVOID_FLAG",
                "FILE_EXTENSION_FLAG", "DIR_TO_REMOVE_FLAG",
                "SQL_SQL_LITE_FLAG", "PROCESS_TO_KILL_FLAG",
                "SERVICE_TO_KILL_FLAG", "THREAT_WALLPAPER_FLAG",
                "RANSOM_NOTE_FLAG", "CHANGE_ICON_FLAG",
                "BUILD_MUTEX_FLAG", "THREAD_OBJECT_FLAG",
                "C2_URL_FLAG",
                "DIRECTORY_TO_AVOID", "FILE_TO_AVOID", "FILE_EXTENSION_TO_AVOID",
                "DIR_TO_REMOVE", "SQL_STRING", "PROCESS_TO_AVOID", "PROCESS_TO_KILL", "SERVICE_TO_KILL", "C2_URL",
                "THREAT_STRING", "RANSOM_NOTE"
                ]


# string decrypt
STRING_DICTIONARY = {}


def main():
    global BUFFER1, KEY_BUFFER, FULL_CONFIG, DECOMPRESSED_CONFIG, RAWCONFIG

    for i in range(0, 256):
        BUFFER1.append(0)
        KEY_BUFFER.append(0)

    get_KEY_BUFFER(0x40173C)

    decrypt_all_strings(translate_ea(0x408C9C))

    # get_FULL_CONFIG()
    # decompress_config()

    # parse_config(0x189b, 0x1bfc, 0x472)

    # print(RAWCONFIG)
    # with open("C:\\Users\\cdong49\\Desktop\\temp\\test.JSON", 'w') as outfile:
    #     json.dump(RAWCONFIG, outfile)


if __name__ == "__main__":
    main()

import json
import idaapi
import idc
import idautils

def ror(n,rotations,width):
    return (2**width-1)&(n>>rotations|n<<(width-rotations))

def hashing(name):
    dll_name, API_name = name.split(':')
    dll_hash = hash_dll(dll_name, 0)
    api_hash = hash_API(API_name, dll_hash)
    return api_hash
    
def hash_dll(dll_name, start):
    result = start
    dll_name = [ord(each) for each in dll_name]
    dll_name.append(0)
    for each in dll_name:
        temp = each
        if temp >= 0x41 and temp <= 0x5a: # to lower
            temp |= 0x20
        result = temp + ror(result, 13, 32)
    return result

def hash_API(API_name, start):
    result = start
    API_name = [ord(each) for each in API_name]
    API_name.append(0)
    for each in API_name:
        result = each + ror(result, 13, 32)
    return result

def setup(json_file):
    global export_hashes
    exports_json = json.loads(open(json_file, 'rb').read())
    exports_list = exports_json['exports']
    for export in exports_list:
        api_hash = hashing(export)
        export_hashes[api_hash] = export.split(':')[1]


def resolve_all_APIs(resolve_ea):
    global export_hashes
    if resolve_ea is None:
        print('resolve fails..')
        return

    for ref in idautils.CodeRefsTo(resolve_ea, 1):
        # only 1 ref
        curr_ea = ref
        API_addresses_ea = 0
        API_hashes_ea = 0
        
        while True:
            prev_instruction_ea = idc.prev_head(curr_ea)
            if idc.print_insn_mnem(prev_instruction_ea) == 'push':
                if API_addresses_ea == 0:
                    API_addresses_ea = idc.get_operand_value(prev_instruction_ea, 0)
                else:
                    API_hashes_ea = idc.get_operand_value(prev_instruction_ea, 0)
                    break
            curr_ea = prev_instruction_ea
            
        API_addresses_ea += 4
        API_hashes_ea += 4

        index = 0
        while True:
            API_hash = int.from_bytes(idc.get_bytes(API_hashes_ea + 4 * index, 4), 'little')
            if API_hash == 0xCCCCCCCC:
                break
            API_hash = API_hash ^ 0x1803FFF7
            if API_hash in export_hashes:
                print(export_hashes[API_hash])
                idc.set_name(API_addresses_ea + 4 * index, export_hashes[API_hash],idaapi.SN_FORCE)
            else:
                print(hex(API_addresses_ea), 'NOTFOUND')
            index += 1
export_hashes = {} 
setup('C:\\Users\\chuon\\Desktop\\ReverseEngineering\\blackmatterv3\\Blackmatter\\exports.json')

# change the address in the parameter to the address of the function resolving the API
resolve_all_APIs(0x407B9C)

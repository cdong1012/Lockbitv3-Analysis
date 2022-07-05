import json
import idaapi
import idc
import idautils
from fnvhash import fnv1a_32

# task 1: set up json
def setup(json_file):
    global export_hashes
    exports_json = json.loads(open(json_file, 'rb').read())
    exports_list = exports_json['exports']
    for export in exports_list:
        api_hash = hashing(export)
        export_hashes[api_hash] = export
    
def hashing(API_name):
    return fnv1a_32(API_name.lower().encode())

# task 2: locate all importing functions
def populate_func_hash_dict():
    global func_hash_dict, export_hashes
    
    for segment_ea in idautils.Segments():
        for func_ea in idautils.Functions(segment_ea, idc.get_segm_end(segment_ea)):
            functionName = idc.get_func_name(func_ea)
            for (start_ea, end_ea) in idautils.Chunks(func_ea):
                curr_ea = start_ea
                API_hash = 0
                while curr_ea <= end_ea:
                    curr_ea = idc.next_head(curr_ea)
                    if idc.print_insn_mnem(curr_ea) == 'imul' and idc.get_operand_value(curr_ea, 2) == 0x1000193:
                        break
                if curr_ea > end_ea:
                    continue
                while curr_ea <= end_ea:
                    curr_ea = idc.next_head(curr_ea)
                    if idc.print_insn_mnem(curr_ea) == 'cmp' and idc.get_operand_value(curr_ea, 1) != -1 and idc.get_operand_value(curr_ea, 1) >=0x1000:
                        API_hash = idc.get_operand_value(curr_ea, 1)
                        break
                if API_hash == 0:
                    continue
                
                func_hash_dict[func_ea] = export_hashes[API_hash] if API_hash in export_hashes else "UNKNOWN " + hex(API_hash)
                
                # weird shits start to happen if the func size is > 200
                # requires manual parsing
                # annoying, I know
                if '.dll' in func_hash_dict[func_ea] and end_ea - start_ea >= 200:
                    del func_hash_dict[func_ea]

export_hashes = {}
setup('C:\\Users\\chuon\\Desktop\\ReverseEngineering\\lockbitv2\\IDAPython-Malware-Scripts\\Lockbit\\exports.json')

# dictionary{key = func_ea, value = API name}
func_hash_dict = {}
populate_func_hash_dict()

def resolve_API_funcs():
    for func_ea in func_hash_dict:
        if "UNK" not in func_hash_dict[func_ea]:
            idc.set_name(func_ea, "get_" + func_hash_dict[func_ea], idaapi.SN_FORCE)

# resolve_API_funcs()

# task 3: put a comment to resolve all hashes without changing func name

def add_resolved_hash_comment():
    global export_hashes
    
    for segment_ea in idautils.Segments():
        for func_ea in idautils.Functions(segment_ea, idc.get_segm_end(segment_ea)):
            functionName = idc.get_func_name(func_ea)
            for (start_ea, end_ea) in idautils.Chunks(func_ea):
                curr_ea = start_ea
                while curr_ea <= end_ea:
                    API_hash = 0
                    while curr_ea <= end_ea:
                        curr_ea = idc.next_head(curr_ea)
                        if idc.print_insn_mnem(curr_ea) == 'imul' and idc.get_operand_value(curr_ea, 2) == 0x1000193:
                            break
                    if curr_ea > end_ea:
                        continue
                    while curr_ea <= end_ea:
                        curr_ea = idc.next_head(curr_ea)
                        if idc.print_insn_mnem(curr_ea) == 'cmp' and idc.get_operand_value(curr_ea, 1) != -1 and idc.get_operand_value(curr_ea, 1) >=0x1000:
                            API_hash = idc.get_operand_value(curr_ea, 1)
                            if API_hash in export_hashes:
                                idc.set_cmt(curr_ea, export_hashes[API_hash], 0)
                                
add_resolved_hash_comment()

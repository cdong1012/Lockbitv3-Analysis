def ror(n,rotations,width):
    return (2**width-1)&(n>>rotations|n<<(width-rotations))
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

def bruteforce(target_hash):
    string = '-'
    
    for first in range(ord('a'), ord('z') + 1):
        for second in range(ord('a'), ord('z') + 1):
            for third in range(ord('a'), ord('z') + 1):
                for fourth in range(ord('a'), ord('z') + 1):
                    temp_string = '-' + chr(first) + chr(second) + chr(third) + chr(fourth)
                    #print(temp_string)
                    if hash_dll(temp_string, 0) == target_hash:
                        return temp_string
print(bruteforce(0xEB9F5C34))
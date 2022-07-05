import base64

hash_dict = {0x4c4b25d4 : "tor browser", 0xd3801b00 : "hlp", 0xdd081c00 : "mpa", 0xab086595 : "program files (x86)", 0xae018eae : "system volume information", 0xf1c01c00 : "wpx", 0x8cf281cd : "config.msi", 0xc7701a40 : "bin", 0xc7a01840 : "bat", 0x64e29771 : "diagpkg", 0x52cb0b38 : "google", 0x26687e35 : "$windows.~ws", 0xdd201bc0 : "mod", 0x6b66f975 : "intel", 0xdb581b80 : "lnk", 0x4cca7837 : "nomedia", 0xd5c01900 : "idx", 0xe3301c80 : "prf", 0xdb301900 : "ldf", 0x2e75e394 : "programdata", 0x45678b17 : "-wall", 0x45471d17 : "-path", 0xf00cae96 : "bootfont.bin", 0xe3426cd7 : "windows", 0xd59818c0 : "ics", 0xc9901d40 : "cur", 0xdd481cc0 : "msi", 0xd3081d00 : "hta", 0xcd281e00 : "exe", 0x85aa57e4 : "ntuser.dat.log", 0xfcc8ab56 : "bootsect.bak", 0xaf16c593 : "themepack", 0xe1a63bc0 : "boot", 0x4aba94f1 : "diagcab", 0xe7801d00 : "rtp", 0xd9c81940 : "key", 0xdf981b00 : "nls", 0xe9601c00 : "spl", 0x7f07935 : "windows.old", 0xb7e02438 : "svchost.exe", 0xe7681bc0 : "rom", 0xe99018c0 : "scr", 0xc5481b80 : "ani", 0x67b00e00 : "386", 0xdd181cc0 : "msc", 0x3907099b : "boot.ini", 0xe9981a00 : "shs", 0xc9101840 : "cab", 0xe9981e40 : "sys", 0x82d2a252 : "desktop.ini", 0xcbb01c80 : "drv", 0xa1fccbfe : "deskthemepack", 0xcb601b00 : "dll", 0x5cde3a7b : "public", 0x267078f5 : "$windows.~bt", 0xe15ed8c0 : "lock", 0xd56018c0 : "icl", 0x30a212d : "$recycle.bin", 0xdd801cc0 : "msp", 0x36004e4e : "program files", 0xc6ce6958 : "appdata", 0xc9201b40 : "cmd", 0xdda81cc0 : "msu", 0x5366e694 : "perflogs", 0xba22623b : "all users", 0xc8cef7d1 : "thumbs.db", 0x452f4997 : "-safe", 0xc99eab80 : "icns", 0xc9681bc0 : "com", 0xdb975937 : "ntldr", 0xc5b01900 : "adv", 0xc23aa6f5 : "ntuser.dat", 0xb7ea3892 : "msocache", 0x86ccaa15 : "autorun.inf", 0x4a6bb7db : "msstyles", 0x4ae29631 : "diagcfg", 0x846bec00 : "iconcache.db", 0xcd2e9b7a : "theme", 0xe1c018c0 : "ocx", 0xdccab8dd : "mozilla", 0xef3a37b3 : "default", 0xa6f2d1a7 : "application data", 0xe3101900 : "pdb", 0xd57818c0 : "ico", 0xc9601c00 : "cpl", 0x3eb272e6 : "explorer.exe", 0xe1881cc0 : "ps1", 0xcbe2aa35 : "ntuser.ini"}

file = open('C:\\Users\\IEUser\\Desktop\\blackmatter2\\decompressed_config.bin', 'rb')

buffer = file.read()

file.close()

buffer = [each for each in buffer[0xd5:]]

base64_strings_buffer = []

curr_string = ''
i = 0
for each in buffer:
    if each == 0:
        print('I is: ' + hex(i) + ' ' + curr_string)
        base64_strings_buffer.append(curr_string)
        curr_string = ''
        i = 0
    else:
        curr_string += chr(each)
        i += 1

for i in range(0,3):
    base64_string_bytes = base64_strings_buffer[i].encode('utf-8')
    decoded_bytes = base64.decodebytes(base64_string_bytes)
    hash_list = []
    for j in range(0, len(decoded_bytes) - 4, 4):
        hash_list.append(int.from_bytes(decoded_bytes[j:j+4], 'little'))
    for j in range(len(hash_list)):
        if hash_list[j] in hash_dict:
            hash_list[j] = hash_dict[hash_list[j]]
        else:
            print("CANT FIND")
    print(hash_list)
    print('------------------------------')

base64_string = base64_strings_buffer[3]
base64_string_bytes = base64_string.encode('utf-8')
decoded_bytes = base64.decodebytes(base64_string_bytes).replace(b'\x00\x00', b' ')
decoded_bytes = ''.join([chr(each) for each in decoded_bytes if each != 0 ])
# print(base64_strings_buffer)
import os
import pefile
import json
# shout-out to OALabs https://gist.github.com/OALabs/94ff4fc02bf02d55a8161068cafd11c0
INTERESTING_DLLS = [
    'kernel32.dll', 'comctl32.dll', 'advapi32.dll', 'comdlg32.dll',
    'gdi32.dll',    'msvcrt.dll',   'netapi32.dll', 'ntdll.dll',
    'ntoskrnl.exe', 'oleaut32.dll', 'psapi.dll',    'shell32.dll',
    'shlwapi.dll',  'srsvc.dll',    'urlmon.dll',   'user32.dll',
    'winhttp.dll',  'wininet.dll',  'ws2_32.dll',   'wship6.dll',
    'advpack.dll',
    'wow64cpu.dll',
    'KERNELBASE.dll',
    'ucrtbase.dll',
    'rstrtmgr.dll',
    'sechost.dll',
    'shcore.dll',
    'combase.dll',
    'iphlpapi.dll',
    'ole32.dll',
    'wtsapi32.dll',
    'activeds.dll',
    'winspool.drv'
]


exports_list = []

for filename in os.listdir("C:\\Windows\\System32"):
    if filename.lower() in INTERESTING_DLLS:
        pe = pefile.PE("C:\\Windows\\System32\\" + filename)
        for exp in pe.DIRECTORY_ENTRY_EXPORT.symbols:
            try:
                exports_list.append(filename.lower() + ':' + exp.name.decode('utf-8'))
            except:
                continue

exports_json = {'exports': exports_list}
open('exports.json', 'w').write(json.dumps(exports_json))
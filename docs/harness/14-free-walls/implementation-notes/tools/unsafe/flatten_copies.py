"""Find every copy of given 32-byte segments (4 doubles: x0, y0, x1, y1) in the game's private writable memory and make each copy
zero length (x1, y1 := x0, y0). flatten_copies.py <segments.json> <backup.json>   (segments.json: list of hex strings)
restore: flatten_copies.py restore <backup.json>
UNSAFE: writes game memory. Refused unless HARNESS_ALLOW_UNSAFE=1 (checked in obstacles_mem.open_game_rw). Test games only."""
import ctypes
import importlib.util
import json
import pathlib
import struct
import sys
import time
from ctypes import wintypes

TOOLS_DIR = pathlib.Path(__file__).resolve().parent.parent
spec_om = importlib.util.spec_from_file_location("om", TOOLS_DIR / "obstacles_mem.py")
om = importlib.util.module_from_spec(spec_om)
spec_om.loader.exec_module(om)


class MBI(ctypes.Structure):
    _fields_ = [("BaseAddress", ctypes.c_void_p), ("AllocationBase", ctypes.c_void_p), ("AllocationProtect", wintypes.DWORD),
                ("PartitionId", wintypes.WORD), ("RegionSize", ctypes.c_size_t), ("State", wintypes.DWORD),
                ("Protect", wintypes.DWORD), ("Type", wintypes.DWORD)]


om.kernel32.VirtualQueryEx.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.POINTER(MBI), ctypes.c_size_t]
om.kernel32.VirtualQueryEx.restype = ctypes.c_size_t
WRITABLE = {0x04, 0x08, 0x40, 0x80}

if sys.argv[1] == "restore":
    handle = om.open_game_rw()
    rows = json.load(open(sys.argv[2]))
    for row in rows:
        om.write(handle, int(row["addr"], 16), bytes.fromhex(row["bytes"]))
    print("restored", len(rows))
    raise SystemExit

segments = [bytes.fromhex(s) for s in json.load(open(sys.argv[1]))]
handle = om.open_game_rw()
found = []
address, start = 0, time.time()
mbi = MBI()
CHUNK = 64 * 1024 * 1024
while om.kernel32.VirtualQueryEx(handle, ctypes.c_void_p(address), ctypes.byref(mbi), ctypes.sizeof(mbi)):
    base, size = mbi.BaseAddress or 0, mbi.RegionSize
    if mbi.State == 0x1000 and mbi.Type == 0x20000 and (mbi.Protect & 0xff) in WRITABLE:
        offset = 0
        while offset < size:
            n = min(CHUNK, size - offset)
            buf = ctypes.create_string_buffer(n)
            done = ctypes.c_size_t()
            if om.kernel32.ReadProcessMemory(handle, ctypes.c_void_p(base + offset), buf, n, ctypes.byref(done)):
                data = buf.raw[:done.value]
                for seg in segments:
                    pos = data.find(seg)
                    while pos != -1:
                        found.append((base + offset + pos, seg))
                        pos = data.find(seg, pos + 8)
            offset += n
    address = base + size
    if address >= 0x7FFFFFFFFFFF:
        break
backup = []
for addr, seg in found:
    x0, y0, _x1, _y1 = struct.unpack("<4d", seg)
    backup.append({"addr": hex(addr), "bytes": seg.hex()})
    om.write(handle, addr, struct.pack("<4d", x0, y0, x0, y0))
json.dump(backup, open(sys.argv[2], "w"))
per_segment = {}
for _addr, seg in found:
    per_segment[seg.hex()[:16]] = per_segment.get(seg.hex()[:16], 0) + 1
print(json.dumps({"segments": len(segments), "copies_flattened": len(found), "seconds": round(time.time() - start),
                  "copies_per_segment_min": min(per_segment.values(), default=0), "max": max(per_segment.values(), default=0),
                  "segments_found": len(per_segment)}))

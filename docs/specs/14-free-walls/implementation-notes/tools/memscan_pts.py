"""Scan the game's private writable memory for byte patterns. memscan_pts.py <patterns.json> <out.json>
patterns.json: {"name": "hex", ...}. Prints every hit address per pattern (at most 50 each)."""
import ctypes
import importlib.util
import json
import sys
import time
from ctypes import wintypes

spec = importlib.util.spec_from_file_location("om", __file__.replace("memscan_pts.py", "obstacles_mem.py"))
om = importlib.util.module_from_spec(spec)
spec.loader.exec_module(om)


class MBI(ctypes.Structure):
    _fields_ = [("BaseAddress", ctypes.c_void_p), ("AllocationBase", ctypes.c_void_p), ("AllocationProtect", wintypes.DWORD),
                ("PartitionId", wintypes.WORD), ("RegionSize", ctypes.c_size_t), ("State", wintypes.DWORD),
                ("Protect", wintypes.DWORD), ("Type", wintypes.DWORD)]


MEM_COMMIT, MEM_PRIVATE = 0x1000, 0x20000
WRITABLE = {0x04, 0x08, 0x40, 0x80}  # PAGE_READWRITE, WRITECOPY, EXECUTE_READWRITE, EXECUTE_WRITECOPY
om.kernel32.VirtualQueryEx.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.POINTER(MBI), ctypes.c_size_t]
om.kernel32.VirtualQueryEx.restype = ctypes.c_size_t

patterns = {k: bytes.fromhex(v) for k, v in json.load(open(sys.argv[1])).items()}
handle = om.open_game()
hits = {k: [] for k in patterns}
address, scanned, start = 0, 0, time.time()
mbi = MBI()
CHUNK = 64 * 1024 * 1024
while om.kernel32.VirtualQueryEx(handle, ctypes.c_void_p(address), ctypes.byref(mbi), ctypes.sizeof(mbi)):
    base, size = mbi.BaseAddress or 0, mbi.RegionSize
    if mbi.State == MEM_COMMIT and mbi.Type == MEM_PRIVATE and (mbi.Protect & 0xff) in WRITABLE:
        offset = 0
        while offset < size:
            n = min(CHUNK, size - offset)
            buf = ctypes.create_string_buffer(n)
            done = ctypes.c_size_t()
            if om.kernel32.ReadProcessMemory(handle, ctypes.c_void_p(base + offset), buf, n, ctypes.byref(done)):
                data = buf.raw[:done.value]
                scanned += done.value
                for name, pat in patterns.items():
                    pos = data.find(pat)
                    while pos != -1 and len(hits[name]) < 50:
                        hits[name].append(hex(base + offset + pos))
                        pos = data.find(pat, pos + 1)
            offset += n
    address = base + size
    if address >= 0x7FFFFFFFFFFF:
        break
json.dump(hits, open(sys.argv[2], "w"), indent=1)
print(json.dumps({"scanned_mb": scanned // (1024 * 1024), "seconds": round(time.time() - start), "hits": {k: len(v) for k, v in hits.items()}}))

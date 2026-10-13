"""Read the raw Obstacle2D entries of RTSMultiEngineCPP.SpatialComponent.Obstacles from game memory (Windows ReadProcessMemory).
obstacles_mem.py dump <out.json>          write every entry as 128 raw bytes (hex) plus decoded doubles, floats and int32s
Layout facts from the jmap: Obstacles is a TArray at offset 656 of SpatialComponent; one Obstacle2D is 128 bytes."""
import ctypes
import json
import os
import struct
import sys
from ctypes import wintypes

sys.path.insert(0, r"C:\Users\garre\development\manor-lords-mod\mcp")
sys.path.insert(0, r"C:\Users\garre\development\manor-lords-mod\harness")
os.environ["UE4SS_BRIDGE_GAME_DIR"] = r"C:\Program Files (x86)\Steam\steamapps\common\Manor Lords\ManorLords\Binaries\Win64"
# The run name comes from RUN, or from current_run.txt next to this script (for commands that cannot set RUN).
RUN_NAME = os.environ.get("RUN") or open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "current_run.txt")).read().strip()
os.environ["UE4SS_BRIDGE_DATA_DIR"] = r"C:\Users\garre\development\manor-lords-mod\runs\\" + RUN_NAME + r"\bridge"
from ue4ss_bridge import server
from runlib.game import find_game_processes

OBSTACLES_OFFSET = 656
ENTRY_SIZE = 128
PROCESS_VM_READ = 0x0010
PROCESS_QUERY_INFORMATION = 0x0400

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
kernel32.OpenProcess.restype = wintypes.HANDLE
kernel32.ReadProcessMemory.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]


def one(*a, **k):
    value = server.one(*a, **k)
    return value["result"] if isinstance(value, dict) and "result" in value else value


def open_game():
    pids = [p.pid for p in find_game_processes()]
    if len(pids) != 1:
        raise SystemExit(f"expected one game process, found {pids}")
    handle = kernel32.OpenProcess(PROCESS_VM_READ | PROCESS_QUERY_INFORMATION, False, pids[0])
    if not handle:
        raise SystemExit(f"OpenProcess failed: {ctypes.get_last_error()}")
    return handle


def read(handle, address, size):
    buffer = ctypes.create_string_buffer(size)
    done = ctypes.c_size_t()
    if not kernel32.ReadProcessMemory(handle, ctypes.c_void_p(address), buffer, size, ctypes.byref(done)) or done.value != size:
        raise SystemExit(f"ReadProcessMemory failed at {hex(address)}: {ctypes.get_last_error()}")
    return buffer.raw


def spatial_address():
    value = server.one("get", ref="first:RTSMultiEngineCPP", name="SpatialComponent")
    value = value.get("result", value)
    return int(value["address"])


def dump(path):
    handle = open_game()
    base = spatial_address()
    data_ptr, num, cap = struct.unpack("<QiI", read(handle, base + OBSTACLES_OFFSET, 16))
    raw = read(handle, data_ptr, num * ENTRY_SIZE) if num > 0 else b""
    entries = []
    for i in range(num):
        chunk = raw[i * ENTRY_SIZE:(i + 1) * ENTRY_SIZE]
        entries.append({"i": i, "hex": chunk.hex(),
                        "d": [round(v, 3) for v in struct.unpack("<16d", chunk)],
                        "f": [round(v, 3) for v in struct.unpack("<32f", chunk)],
                        "i32": list(struct.unpack("<32i", chunk))})
    json.dump({"spatial": hex(base), "data": hex(data_ptr), "num": num, "max": cap, "entries": entries}, open(path, "w"))
    print(json.dumps({"spatial": hex(base), "data": hex(data_ptr), "num": num, "max": cap}))


if __name__ == "__main__":
    if sys.argv[1] == "dump":
        dump(sys.argv[2])


PROCESS_VM_WRITE = 0x0020
PROCESS_VM_OPERATION = 0x0008
kernel32.WriteProcessMemory.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]


UNSAFE_ENV = "HARNESS_ALLOW_UNSAFE"


def open_game_rw():
    """Open the game for memory writes. Refused unless HARNESS_ALLOW_UNSAFE=1: a write can crash the game (test games only)."""
    if os.environ.get(UNSAFE_ENV) != "1":
        raise SystemExit(f"memory writes are unsafe: set {UNSAFE_ENV}=1 to allow them (test games only, never a user save)")
    pids = [p.pid for p in find_game_processes()]
    if len(pids) != 1:
        raise SystemExit(f"expected one game process, found {pids}")
    handle = kernel32.OpenProcess(PROCESS_VM_READ | PROCESS_VM_WRITE | PROCESS_VM_OPERATION | PROCESS_QUERY_INFORMATION, False, pids[0])
    if not handle:
        raise SystemExit(f"OpenProcess (write) failed: {ctypes.get_last_error()}")
    return handle


def write(handle, address, data):
    done = ctypes.c_size_t()
    if not kernel32.WriteProcessMemory(handle, ctypes.c_void_p(address), data, len(data), ctypes.byref(done)) or done.value != len(data):
        raise SystemExit(f"WriteProcessMemory failed at {hex(address)}: {ctypes.get_last_error()}")


def entries_live(handle):
    """Yield (index, entry_address, points_ptr, num_points, points) for the live list."""
    base = spatial_address()
    data_ptr, num, _ = struct.unpack("<QiI", read(handle, base + OBSTACLES_OFFSET, 16))
    for i in range(num):
        address = data_ptr + i * ENTRY_SIZE
        ptr, n, _cap = struct.unpack("<QiI", read(handle, address + 80, 16))
        points = []
        if ptr and 0 < n <= 512:
            raw = read(handle, ptr, n * 16)
            points = [struct.unpack("<2d", raw[k * 16:(k + 1) * 16]) for k in range(n)]
        yield i, address, ptr, n, points

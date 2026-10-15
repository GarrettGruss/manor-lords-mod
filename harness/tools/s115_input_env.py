"""Print facts about the Windows input setup (spike #115). Read-only."""
import ctypes

user32 = ctypes.windll.user32
METRICS = {
    "SM_MOUSEPRESENT": 19,
    "SM_CMOUSEBUTTONS": 43,
    "SM_MOUSEWHEELPRESENT": 75,
    "SM_CMONITORS": 80,
    "SM_DIGITIZER": 94,
    "SM_MAXIMUMTOUCHES": 95,
    "SM_REMOTESESSION": 0x1000,
}
for name, index in METRICS.items():
    print(name, user32.GetSystemMetrics(index))

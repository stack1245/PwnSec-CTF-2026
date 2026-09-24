import ctypes
import sys
import time
from ctypes import wintypes


WM_GETTEXTLENGTH = 0x000E
EM_SETSEL = 0x00B1
EM_REPLACESEL = 0x00C2
BM_CLICK = 0x00F5
user32 = ctypes.windll.user32
user32.SendMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.SendMessageW.restype = wintypes.LPARAM
pid = int(sys.argv[1])
value = sys.argv[2]
top_windows = []


@ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
def enum_window(hwnd, _):
    process_id = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id))
    if process_id.value == pid and user32.GetDlgItem(hwnd, 1005):
        top_windows.append(hwnd)
    return True


user32.EnumWindows(enum_window, 0)
if len(top_windows) != 1:
    raise SystemExit(f"expected one visible top window, got {top_windows!r}")

top = top_windows[0]
edit = user32.GetDlgItem(top, 1004)
run = user32.GetDlgItem(top, 1005)
if not edit or not run:
    raise SystemExit("missing edit or run control")

if value:
    length = user32.SendMessageW(edit, WM_GETTEXTLENGTH, 0, 0)
    user32.SendMessageW(edit, EM_SETSEL, length, length)
    buffer = ctypes.create_unicode_buffer(value)
    user32.SendMessageW(edit, EM_REPLACESEL, 0, ctypes.cast(buffer, ctypes.c_void_p).value)
user32.SendMessageW(run, BM_CLICK, 0, 0)
time.sleep(0.5)
print(f"submitted {value!r}")

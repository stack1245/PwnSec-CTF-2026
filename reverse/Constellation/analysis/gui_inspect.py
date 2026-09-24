import ctypes
import sys
from ctypes import wintypes


user32 = ctypes.windll.user32
user32.SendMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.SendMessageW.restype = wintypes.LPARAM
pid = int(sys.argv[1])
windows = []


@ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
def enum_window(hwnd, _):
    process_id = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id))
    if process_id.value == pid:
        windows.append(hwnd)
    return True


user32.EnumWindows(enum_window, 0)
print("top", [(hex(hwnd), bool(user32.IsWindowVisible(hwnd))) for hwnd in windows])

for top in windows:
    children = []

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def enum_child(hwnd, _):
        children.append(hwnd)
        return True

    user32.EnumChildWindows(top, enum_child, 0)
    for hwnd in children:
        class_name = ctypes.create_unicode_buffer(256)
        text = ctypes.create_unicode_buffer(1024)
        user32.GetClassNameW(hwnd, class_name, len(class_name))
        user32.GetWindowTextW(hwnd, text, len(text))
        text_length = user32.SendMessageW(hwnd, 0x000E, 0, 0)
        message_text = ctypes.create_unicode_buffer(max(1, text_length + 1))
        user32.SendMessageW(
            hwnd,
            0x000D,
            len(message_text),
            ctypes.cast(message_text, ctypes.c_void_p).value,
        )
        print(
            hex(top),
            hex(hwnd),
            "id",
            user32.GetDlgCtrlID(hwnd),
            "visible",
            bool(user32.IsWindowVisible(hwnd)),
            "enabled",
            bool(user32.IsWindowEnabled(hwnd)),
            "class",
            repr(class_name.value),
            "text",
            repr(text.value),
            "message_text",
            repr(message_text.value),
        )

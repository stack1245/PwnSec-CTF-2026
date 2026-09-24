import ctypes
import json
import pathlib
import struct
import sys
from ctypes import wintypes


PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010
MEM_COMMIT = 0x1000
MEM_PRIVATE = 0x20000
PAGE_GUARD = 0x100
PAGE_NOACCESS = 0x01
CHUNK = 16 * 1024 * 1024


class MEMORY_BASIC_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BaseAddress", ctypes.c_void_p),
        ("AllocationBase", ctypes.c_void_p),
        ("AllocationProtect", wintypes.DWORD),
        ("PartitionId", wintypes.WORD),
        ("RegionSize", ctypes.c_size_t),
        ("State", wintypes.DWORD),
        ("Protect", wintypes.DWORD),
        ("Type", wintypes.DWORD),
    ]


kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
kernel32.OpenProcess.restype = wintypes.HANDLE
kernel32.ReadProcessMemory.argtypes = [
    wintypes.HANDLE,
    ctypes.c_void_p,
    ctypes.c_void_p,
    ctypes.c_size_t,
    ctypes.POINTER(ctypes.c_size_t),
]
kernel32.VirtualQueryEx.argtypes = [
    wintypes.HANDLE,
    ctypes.c_void_p,
    ctypes.POINTER(MEMORY_BASIC_INFORMATION),
    ctypes.c_size_t,
]
kernel32.VirtualQueryEx.restype = ctypes.c_size_t


pid = int(sys.argv[1])
fast = "--fast" in sys.argv[2:]
serialized = "--serialized" in sys.argv[2:]
handle = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
if not handle:
    raise ctypes.WinError(ctypes.get_last_error())


def read(address, size):
    buffer = ctypes.create_string_buffer(size)
    got = ctypes.c_size_t()
    if not kernel32.ReadProcessMemory(handle, address, buffer, size, ctypes.byref(got)):
        return None
    return buffer.raw[: got.value]


signature = struct.pack("<I", 0xF1A68D63) if serialized else struct.pack("<3I", 192, 224, 32)
candidates = []
address = 0
mbi = MEMORY_BASIC_INFORMATION()

while kernel32.VirtualQueryEx(handle, address, ctypes.byref(mbi), ctypes.sizeof(mbi)):
    base = int(mbi.BaseAddress or 0)
    size = int(mbi.RegionSize)
    eligible = mbi.State == MEM_COMMIT and not (mbi.Protect & (PAGE_GUARD | PAGE_NOACCESS))
    if fast:
        eligible = eligible and mbi.Type == MEM_PRIVATE and size <= 8 * 1024 * 1024
    if eligible:
        offset = 0
        overlap = b""
        while offset < size:
            piece = read(base + offset, min(CHUNK, size - offset))
            if piece:
                blob = overlap + piece
                start = 0
                while True:
                    hit = blob.find(signature, start)
                    if hit < 0:
                        break
                    candidates.append(base + offset - len(overlap) + hit)
                    start = hit + 1
                overlap = blob[-(len(signature) - 1):] if len(signature) > 1 else b""
            offset += min(CHUNK, size - offset)
    next_address = base + size
    if next_address <= address:
        break
    address = next_address

out_dir = pathlib.Path(__file__).parent
verbose = "--verbose" in sys.argv[2:]
if verbose:
    print("candidates", [hex(x) for x in candidates])
for candidate in candidates:
    if serialized:
        header = read(candidate, 20)
        if not header or len(header) != 20:
            continue
        magic, width, data_shards, parity_shards, blocks = struct.unpack("<5I", header)
        if (magic, width, data_shards, parity_shards) != (0xF1A68D63, 192, 224, 32):
            continue
        field = read(candidate + 20, 255)
        matrix = read(candidate + 20 + 255, data_shards * parity_shards)
        order = read(candidate + 20 + 255 + data_shards * parity_shards, blocks * 256 * 4)
        if not all((field, matrix, order)):
            continue
        order_values = struct.unpack(f"<{len(order) // 4}I", order)
        first_required_orders = [order_values[i * 256 : (i + 1) * 256] for i in range(min(4, blocks))]
        if len(set(field)) != 255 or not all(matrix) or any(len(set(values)) != 256 for values in first_required_orders):
            continue
        for name, data in (("field", field), ("matrix", matrix), ("order", order)):
            (out_dir / f"plan_{name}.bin").write_bytes(data)
        meta = {"width": width, "data_shards": data_shards, "parity_shards": parity_shards, "blocks": blocks}
        (out_dir / "plan_meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
        print("matched serialized", hex(candidate), meta)
        break
    raw = read(candidate, 88)
    if not raw or len(raw) != 88:
        continue
    values = struct.unpack_from("<4I", raw)
    spans = [struct.unpack_from("<QQ", raw, off) for off in (16, 40, 64)]
    sizes = [end - begin for begin, end in spans]
    blocks = values[3]
    if verbose:
        print("inspect", hex(candidate), values, [(hex(a), hex(b)) for a, b in spans], sizes)
    if not 1 <= blocks <= 4096 or sizes != [255, 224 * 32, blocks * 256 * 4]:
        continue
    names = ("field", "matrix", "order")
    for name, (begin, end) in zip(names, spans):
        data = read(begin, end - begin)
        if data is None or len(data) != end - begin:
            raise RuntimeError(f"failed reading {name}")
        (out_dir / f"plan_{name}.bin").write_bytes(data)
    meta = dict(zip(("width", "data_shards", "parity_shards", "blocks"), values))
    (out_dir / "plan_meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print("matched", hex(candidate), meta, sizes)
    break
else:
    raise SystemExit("parsed plan object not found")

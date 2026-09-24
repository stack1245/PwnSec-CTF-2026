#!/usr/bin/env python3
"""Reach the ROM reward screen by pinning the lives counter."""

from pathlib import Path

from pyboy import PyBoy


ROOT = Path(__file__).resolve().parent
ROM = ROOT / "AURA.gb"
CAPTURES = ROOT / "cheat-captures"
LIVES = 0xC0FC
GIFT_GATE = 0xC109


def main() -> None:
    CAPTURES.mkdir(exist_ok=True)
    pyboy = PyBoy(str(ROM), window="null", sound_emulated=False)
    pyboy.set_emulation_speed(0)
    try:
        pyboy.tick(120)
        pyboy.button("start")
        pyboy.tick(120)
        previous = bytes(pyboy.memory[address] for address in range(0xC0F0, 0xC110))
        for frame in range(1, 8_001):
            pyboy.memory[LIVES] = 3
            pyboy.memory[GIFT_GATE] = 0
            pyboy.tick(1, frame % 60 == 0)
            pyboy.memory[LIVES] = 3
            pyboy.memory[GIFT_GATE] = 0
            current = bytes(pyboy.memory[address] for address in range(0xC0F0, 0xC110))
            if current != previous:
                watched = {0xC0FB, 0xC0FC, 0xC0FD, 0xC107, 0xC108, 0xC109}
                changes = [f"{0xC0F0 + i:04x}:{old:02x}->{new:02x}" for i, (old, new) in enumerate(zip(previous, current)) if old != new and 0xC0F0 + i in watched]
                if changes:
                    print(frame, " ".join(changes))
                previous = current
            if frame % 300 == 0 or (4_100 <= frame <= 4_500 and frame % 30 == 0):
                pyboy.screen.image.save(CAPTURES / f"frame-{frame:05d}.png")
    finally:
        pyboy.stop(save=False)


if __name__ == "__main__":
    main()

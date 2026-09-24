#!/usr/bin/env python3
"""Find WRAM bytes that track lives and timer during an intentional loss."""

from pathlib import Path

from pyboy import PyBoy


rom = Path(__file__).resolve().parent / "AURA.gb"
pyboy = PyBoy(str(rom), window="null", sound_emulated=False)
pyboy.set_emulation_speed(0)
try:
    pyboy.tick(120)
    pyboy.button("start")
    pyboy.tick(120)
    initial = {address: pyboy.memory[address] for address in range(0xC000, 0xE000)}
    candidates = {address for address, value in initial.items() if value in (3, 15)}
    previous = dict(initial)
    for frame in range(1, 3_601):
        pyboy.tick()
        if frame % 10:
            continue
        changes = []
        for address in list(candidates):
            value = pyboy.memory[address]
            if value != previous[address]:
                changes.append((address, previous[address], value))
                previous[address] = value
        if changes:
            print(frame, " ".join(f"{address:04x}:{old:02x}->{new:02x}" for address, old, new in changes))
finally:
    pyboy.stop(save=False)

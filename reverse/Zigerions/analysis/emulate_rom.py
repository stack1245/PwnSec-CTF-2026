#!/usr/bin/env python3
"""Run the extracted Game Boy ROM headlessly and capture checkpoints."""

from pathlib import Path

from pyboy import PyBoy


ROOT = Path(__file__).resolve().parent
ROM = ROOT / "AURA.gb"
CAPTURES = ROOT / "captures"


def save(pyboy: PyBoy, name: str) -> None:
    CAPTURES.mkdir(exist_ok=True)
    pyboy.screen.image.save(CAPTURES / f"{name}.png")
    print(name, "frame", pyboy.frame_count)


def main() -> None:
    pyboy = PyBoy(str(ROM), window="null", sound_emulated=False)
    pyboy.set_emulation_speed(0)
    try:
        pyboy.tick(120, True)
        save(pyboy, "boot")
        pyboy.button("start")
        pyboy.tick(60, True)
        save(pyboy, "after-start")
        for seconds in (5, 15, 30, 60):
            pyboy.tick(seconds * 60, True)
            save(pyboy, f"play-{seconds:02d}s")
    finally:
        pyboy.stop(save=False)


if __name__ == "__main__":
    main()

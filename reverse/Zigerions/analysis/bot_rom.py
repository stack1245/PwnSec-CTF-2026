#!/usr/bin/env python3
"""Headless horizontal dodge bot for the extracted Game Boy stage."""

from pathlib import Path

from pyboy import PyBoy


ROOT = Path(__file__).resolve().parent
ROM = ROOT / "AURA.gb"
CAPTURES = ROOT / "bot-captures"


def choose_target(player_x: int, hazards: list[tuple[int, int]]) -> int:
    candidates = range(16, 145, 2)
    threatening = [(x, y) for x, y in hazards if 70 <= y <= 150]
    if not threatening:
        return 80

    def score(candidate: int) -> float:
        minimum = min(abs(candidate - x) + max(0, 118 - y) * 0.08 for x, y in threatening)
        return minimum - abs(candidate - player_x) * 0.015 - abs(candidate - 80) * 0.002

    return max(candidates, key=score)


def main() -> None:
    CAPTURES.mkdir(exist_ok=True)
    pyboy = PyBoy(str(ROM), window="null", sound_emulated=False)
    pyboy.set_emulation_speed(0)
    held: str | None = None
    try:
        pyboy.tick(120)
        pyboy.button("start")
        pyboy.tick(120)
        for frame in range(1, 12_001):
            player = pyboy.get_sprite(0)
            hazards = [pyboy.get_sprite(i) for i in range(1, 40)]
            visible_hazards = [(sprite.x, sprite.y) for sprite in hazards if sprite.on_screen and sprite.tile_identifier == 3]
            desired: str | None = None
            if player.on_screen and player.tile_identifier == 2:
                target = choose_target(player.x, visible_hazards)
                if target < player.x - 2:
                    desired = "left"
                elif target > player.x + 2:
                    desired = "right"
            if desired != held:
                if held is not None:
                    pyboy.button_release(held)
                if desired is not None:
                    pyboy.button_press(desired)
                held = desired
            pyboy.tick(1, frame % 60 == 0)
            if frame % 300 == 0:
                pyboy.screen.image.save(CAPTURES / f"frame-{frame:05d}.png")
                print(frame, "player", (player.x, player.y, player.tile_identifier, player.on_screen), "hazards", visible_hazards)
    finally:
        if held is not None:
            pyboy.button_release(held)
        pyboy.stop(save=False)


if __name__ == "__main__":
    main()

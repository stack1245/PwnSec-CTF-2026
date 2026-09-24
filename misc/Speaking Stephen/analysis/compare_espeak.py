from pathlib import Path
import wave

import numpy as np


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT.parent / "output" / "flag-audio.wav"


def load(path: Path) -> np.ndarray:
    with wave.open(str(path), "rb") as wav:
        assert wav.getframerate() == 22050
        assert wav.getnchannels() == 1 and wav.getsampwidth() == 2
        return np.frombuffer(wav.readframes(wav.getnframes()), dtype="<i2").astype(
            np.float64
        )


def fftconvolve_valid(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    full_size = len(left) + len(right) - 1
    fft_size = 1 << (full_size - 1).bit_length()
    full = np.fft.irfft(np.fft.rfft(left, fft_size) * np.fft.rfft(right, fft_size))[
        :full_size
    ]
    return full[len(right) - 1 : len(left)]


def compare(candidate_path: Path) -> None:
    output = load(OUTPUT)
    candidate = load(candidate_path)
    candidate -= candidate.mean()

    # Find the candidate's best placement, then report the least-squares residual.
    correlation = fftconvolve_valid(output, candidate[::-1])
    offset = int(np.argmax(correlation))
    window = output[offset : offset + len(candidate)]
    design = np.column_stack((candidate, np.ones_like(candidate)))
    scale, bias = np.linalg.lstsq(design, window, rcond=None)[0]
    residual = window - (scale * candidate + bias)
    normalized_rmse = np.sqrt(np.mean(residual**2)) / np.std(window)
    cosine = np.dot(window - window.mean(), candidate) / (
        np.linalg.norm(window - window.mean()) * np.linalg.norm(candidate)
    )
    print(
        f"{candidate_path.stem}: offset={offset}, cosine={cosine:.9f}, "
        f"normalized_rmse={normalized_rmse:.9f}, scale={scale:.6f}"
    )


for name in ("bb.wav", "dd.wav"):
    compare(ROOT / "espeak" / name)

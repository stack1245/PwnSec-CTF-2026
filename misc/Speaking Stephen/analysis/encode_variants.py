from pathlib import Path

import av


root = Path(__file__).resolve().parent
source = av.open(str(root / "adversarial.wav"))
frames = list(source.decode(audio=0))
source.close()

for bitrate in (64_000, 128_000, 192_000, 256_000, 320_000):
    path = root / f"adversarial-{bitrate // 1000}k.mp3"
    output = av.open(str(path), mode="w")
    stream = output.add_stream("libmp3lame", rate=16_000)
    stream.bit_rate = bitrate
    stream.layout = "mono"
    for frame in frames:
        frame.sample_rate = 16_000
        for packet in stream.encode(frame):
            output.mux(packet)
    for packet in stream.encode(None):
        output.mux(packet)
    output.close()
    print(path.name, path.stat().st_size)

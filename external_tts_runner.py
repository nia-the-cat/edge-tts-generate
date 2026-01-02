import argparse
import asyncio
import sys

import edge_tts


async def synthesize(args: argparse.Namespace) -> bytes:
    with open(args.text_file, "r", encoding="utf-8") as handle:
        text = handle.read()

    tts = edge_tts.Communicate(
        text,
        voice=args.voice,
        pitch=args.pitch,
        rate=args.rate,
        volume=args.volume,
    )

    audio = b""
    async for chunk in tts.stream():
        if chunk["type"] == "audio":
            audio += chunk["data"]
    return audio


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--text-file", required=True)
    parser.add_argument("--voice", required=True)
    parser.add_argument("--pitch", required=True)
    parser.add_argument("--rate", required=True)
    parser.add_argument("--volume", required=True)
    args = parser.parse_args()

    audio_bytes = asyncio.run(synthesize(args))
    sys.stdout.buffer.write(audio_bytes)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

import argparse
import asyncio
import base64
import json
import sys

import edge_tts


async def synthesize_text(text: str, args: argparse.Namespace) -> bytes:
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


async def synthesize(args: argparse.Namespace) -> bytes:
    with open(args.text_file, encoding="utf-8") as handle:
        text = handle.read()
    return await synthesize_text(text, args)


async def synthesize_batch(args: argparse.Namespace) -> list[dict[str, str]]:
    with open(args.batch_file, encoding="utf-8") as handle:
        payload = json.load(handle)

    items = payload.get("items", [])
    identifiers: list[str] = []
    tasks: list[asyncio.Task[bytes]] = []

    for item in items:
        text = item.get("text", "")
        identifiers.append(str(item.get("id", "")))
        tasks.append(asyncio.create_task(synthesize_text(text, args)))

    audio_results = await asyncio.gather(*tasks, return_exceptions=True)

    for result in audio_results:
        if isinstance(result, Exception):
            raise RuntimeError("Failed to synthesize text in batch") from result

    ordered_results = sorted(zip(identifiers, audio_results, strict=True), key=lambda pair: pair[0])
    return [
        {"id": identifier, "audio": base64.b64encode(audio_bytes).decode("ascii")}
        for identifier, audio_bytes in ordered_results
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--text-file")
    input_group.add_argument("--batch-file")
    parser.add_argument("--voice", required=True)
    parser.add_argument("--pitch", required=True)
    parser.add_argument("--rate", required=True)
    parser.add_argument("--volume", required=True)
    args = parser.parse_args()

    if args.batch_file:
        batch_results = asyncio.run(synthesize_batch(args))
        sys.stdout.write(json.dumps(batch_results))
    else:
        audio_bytes = asyncio.run(synthesize(args))
        sys.stdout.buffer.write(audio_bytes)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

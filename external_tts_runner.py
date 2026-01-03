import argparse
import asyncio
import base64
import json
import sys

import edge_tts

BATCH_CONCURRENCY_LIMIT = 5


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
    queued_items: list[tuple[str, asyncio.Task[bytes]]] = []

    semaphore = asyncio.Semaphore(BATCH_CONCURRENCY_LIMIT)

    async def synthesize_with_limit(text: str) -> bytes:
        async with semaphore:
            return await synthesize_text(text, args)

    for item in items:
        text = item.get("text", "")
        identifier = str(item.get("id", ""))
        queued_items.append((identifier, asyncio.create_task(synthesize_with_limit(text))))

    audio_results = await asyncio.gather(
        *(task for _, task in queued_items), return_exceptions=True
    )

    paired_results = sorted(
        zip((identifier for identifier, _ in queued_items), audio_results, strict=True),
        key=lambda pair: pair[0],
    )

    results: list[dict[str, str]] = []

    for identifier, result in paired_results:
        if isinstance(result, Exception):
            results.append({"id": identifier, "error": str(result)})
        else:
            results.append(
                {"id": identifier, "audio": base64.b64encode(result).decode("ascii")}
            )

    return results


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

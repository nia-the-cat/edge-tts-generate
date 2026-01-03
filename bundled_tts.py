"""
Bundled TTS module using vendored edge-tts library.

This module provides TTS functionality using a bundled copy of edge-tts
and its dependencies, eliminating the need for an external Python runtime.
"""

from __future__ import annotations

import asyncio
import base64
import os
import sys
from dataclasses import dataclass
from os.path import dirname, join


# Force pure Python mode for all packages with C extensions
# This must be done BEFORE importing the packages
os.environ["AIOHTTP_NO_EXTENSIONS"] = "1"
os.environ["FROZENLIST_NO_EXTENSIONS"] = "1"
os.environ["MULTIDICT_NO_EXTENSIONS"] = "1"
os.environ["YARL_NO_EXTENSIONS"] = "1"
os.environ["PROPCACHE_NO_EXTENSIONS"] = "1"


def _setup_vendor_path() -> None:
    """Add vendor directory to sys.path if not already present."""
    vendor_dir = join(dirname(__file__), "vendor")
    if vendor_dir not in sys.path:
        sys.path.insert(0, vendor_dir)


# Set up vendor path before importing edge_tts
_setup_vendor_path()

# Now we can import edge_tts from the vendor directory
import edge_tts  # noqa: E402


BATCH_CONCURRENCY_LIMIT = 5
STREAM_TIMEOUT_SECONDS_DEFAULT = 30.0
STREAM_TIMEOUT_RETRIES_DEFAULT = 1


@dataclass
class TTSConfig:
    """Configuration for TTS synthesis."""

    voice: str
    pitch: str
    rate: str
    volume: str
    stream_timeout: float = STREAM_TIMEOUT_SECONDS_DEFAULT
    stream_timeout_retries: int = STREAM_TIMEOUT_RETRIES_DEFAULT


@dataclass
class TTSItem:
    """A single item to synthesize."""

    identifier: str
    text: str
    voice: str | None = None  # Override voice for this item


@dataclass
class TTSResult:
    """Result of TTS synthesis."""

    identifier: str
    audio: bytes | None = None
    error: str | None = None


async def _synthesize_text(text: str, config: TTSConfig) -> bytes:
    """Synthesize text to audio bytes."""

    async def _collect_audio() -> bytes:
        tts = edge_tts.Communicate(
            text,
            voice=config.voice,
            pitch=config.pitch,
            rate=config.rate,
            volume=config.volume,
        )

        audio = b""
        async for chunk in tts.stream():
            if chunk["type"] == "audio":
                audio += chunk["data"]
        return audio

    for attempt in range(config.stream_timeout_retries + 1):
        try:
            return await asyncio.wait_for(_collect_audio(), timeout=config.stream_timeout)
        except TimeoutError as exc:
            if attempt == config.stream_timeout_retries:
                raise RuntimeError(f"Timed out after {config.stream_timeout} seconds while streaming audio") from exc
    # This should never be reached, but satisfy type checker
    raise RuntimeError("Unexpected error in synthesis retry loop")


async def _synthesize_batch_async(items: list[TTSItem], config: TTSConfig) -> list[TTSResult]:
    """Synthesize a batch of items asynchronously."""
    semaphore = asyncio.Semaphore(BATCH_CONCURRENCY_LIMIT)

    async def synthesize_with_limit(item: TTSItem) -> TTSResult:
        async with semaphore:
            item_config = TTSConfig(
                voice=item.voice or config.voice,
                pitch=config.pitch,
                rate=config.rate,
                volume=config.volume,
                stream_timeout=config.stream_timeout,
                stream_timeout_retries=config.stream_timeout_retries,
            )
            try:
                audio = await _synthesize_text(item.text, item_config)
                return TTSResult(identifier=item.identifier, audio=audio)
            except Exception as exc:
                return TTSResult(identifier=item.identifier, error=str(exc))

    tasks = [synthesize_with_limit(item) for item in items]
    results = await asyncio.gather(*tasks)
    return sorted(results, key=lambda r: r.identifier)


def synthesize_batch(items: list[TTSItem], config: TTSConfig) -> list[TTSResult]:
    """
    Synthesize a batch of items synchronously.

    This function runs the async synthesis in a new event loop,
    making it safe to call from synchronous code.
    """
    # Create a new event loop for this synthesis
    # This avoids conflicts with any existing event loops (e.g., Qt's)
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(_synthesize_batch_async(items, config))
    finally:
        loop.close()


def synthesize_single(text: str, config: TTSConfig) -> bytes:
    """
    Synthesize a single text to audio bytes synchronously.

    Raises an exception if synthesis fails.
    """
    items = [TTSItem(identifier="0", text=text)]
    results = synthesize_batch(items, config)
    if results and results[0].error:
        raise RuntimeError(results[0].error)
    if results and results[0].audio:
        return results[0].audio
    raise RuntimeError("No audio returned from synthesis")


def results_to_json_list(results: list[TTSResult]) -> list[dict[str, str]]:
    """Convert TTSResult list to JSON-serializable format (for compatibility)."""
    output = []
    for result in results:
        if result.error:
            output.append({"id": result.identifier, "error": result.error})
        elif result.audio:
            output.append({"id": result.identifier, "audio": base64.b64encode(result.audio).decode("ascii")})
    return output

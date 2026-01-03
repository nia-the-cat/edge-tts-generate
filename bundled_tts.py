"""
Bundled TTS module using vendored edge-tts library.

This module provides TTS functionality using a bundled copy of edge-tts
and its dependencies, eliminating the need for an external Python runtime.
"""

from __future__ import annotations

import asyncio
import base64
import importlib
from dataclasses import dataclass


try:
    from .vendor_setup import ensure_vendor_path
except ImportError:
    from vendor_setup import ensure_vendor_path


# Set up vendor path before importing edge_tts
ensure_vendor_path()
edge_tts = importlib.import_module("edge_tts")


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
        except asyncio.TimeoutError as exc:
            # Note: In Python 3.9-3.10, asyncio.TimeoutError is distinct from builtin TimeoutError.
            # asyncio.wait_for raises asyncio.TimeoutError specifically.
            if attempt == config.stream_timeout_retries:
                raise RuntimeError(f"Timed out after {config.stream_timeout} seconds while streaming audio") from exc
    # This should never be reached, but satisfy type checker
    raise RuntimeError("Unexpected error in synthesis retry loop")


async def _synthesize_batch_async(items: list[TTSItem], config: TTSConfig) -> list[TTSResult]:
    """Synthesize a batch of items asynchronously.

    Results are returned in the same order as the input items.
    """
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
    # asyncio.gather preserves the order of tasks, so results match input order
    return await asyncio.gather(*tasks)


def _shutdown_loop(loop: asyncio.AbstractEventLoop) -> None:
    """
    Gracefully shut down an event loop.

    This function properly cleans up all pending tasks and transports
    before closing the loop to prevent "Event loop is closed" errors
    on Windows when aiohttp transports are garbage collected.

    Note: This add-on requires Python 3.9+ (enforced by Anki's minimum
    supported Python version), so shutdown_default_executor() is available.
    """
    try:
        # Cancel all pending tasks
        pending = asyncio.all_tasks(loop)
        for task in pending:
            task.cancel()

        # Give tasks a chance to finish cancellation
        if pending:
            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))

        # Shut down async generators
        loop.run_until_complete(loop.shutdown_asyncgens())

        # Shut down the default executor (available in Python 3.9+)
        loop.run_until_complete(loop.shutdown_default_executor())

    except Exception:
        # Ignore errors during shutdown - we're closing anyway
        pass
    finally:
        loop.close()


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
        _shutdown_loop(loop)


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

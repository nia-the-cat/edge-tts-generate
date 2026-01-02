"""
Tests for external_tts_runner.py - CLI argument parsing and synthesize function.
Note: These tests mock edge_tts to avoid network calls.
"""

import argparse
import asyncio
import base64
import importlib.util
import json
import os
import sys
import tempfile
from unittest.mock import MagicMock, patch

import pytest


# Import external_tts_runner from the parent directory without adding it to sys.path
_module_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "external_tts_runner.py")


class TestArgumentParsing:
    """Test CLI argument parsing."""

    @staticmethod
    def _build_parser():
        parser = argparse.ArgumentParser()
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument("--text-file")
        group.add_argument("--batch-file")
        parser.add_argument("--voice", required=True)
        parser.add_argument("--pitch", required=True)
        parser.add_argument("--rate", required=True)
        parser.add_argument("--volume", required=True)
        return parser

    def test_parser_requires_text_file(self):
        """Parser should require either --text-file or --batch-file argument."""
        parser = self._build_parser()

        with pytest.raises(SystemExit):
            parser.parse_args([])

    def test_parser_accepts_all_arguments(self):
        """Parser should accept all required arguments for single input."""
        parser = self._build_parser()

        args = parser.parse_args(
            [
                "--text-file",
                "/tmp/test.txt",
                "--voice",
                "ja-JP-NanamiNeural",
                "--pitch",
                "+0Hz",
                "--rate",
                "+0%",
                "--volume",
                "+0%",
            ]
        )

        assert args.text_file == "/tmp/test.txt"
        assert args.voice == "ja-JP-NanamiNeural"
        assert args.pitch == "+0Hz"
        assert args.rate == "+0%"
        assert args.volume == "+0%"

    def test_parser_accepts_batch_arguments(self):
        """Parser should accept batch input arguments."""
        parser = self._build_parser()

        args = parser.parse_args(
            [
                "--batch-file",
                "/tmp/batch.json",
                "--voice",
                "ja-JP-NanamiNeural",
                "--pitch",
                "+0Hz",
                "--rate",
                "+0%",
                "--volume",
                "+0%",
            ]
        )

        assert args.batch_file == "/tmp/batch.json"
        assert args.voice == "ja-JP-NanamiNeural"


def _load_external_tts_runner():
    """Load external_tts_runner module with mocked edge_tts."""
    sys.modules["edge_tts"] = MagicMock()
    spec = importlib.util.spec_from_file_location("external_tts_runner", _module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestSynthesizeFunction:
    """Test the synthesize async function."""

    def test_synthesize_reads_text_file(self):
        """Synthesize should read text from the provided file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write("Hello, world!")
            text_file = f.name

        try:
            # Create mock args
            args = argparse.Namespace(
                text_file=text_file,
                voice="en-US-JennyNeural",
                pitch="+0Hz",
                rate="+0%",
                volume="+0%",
            )

            # Mock edge_tts.Communicate
            mock_tts = MagicMock()

            async def mock_stream():
                yield {"type": "audio", "data": b"audio_data_chunk_1"}
                yield {"type": "audio", "data": b"audio_data_chunk_2"}
                yield {"type": "metadata", "data": "some_metadata"}  # Should be skipped

            mock_tts.stream = mock_stream

            external_tts_runner = _load_external_tts_runner()

            with patch.object(external_tts_runner.edge_tts, "Communicate", return_value=mock_tts):
                result = asyncio.run(external_tts_runner.synthesize(args))

            assert result == b"audio_data_chunk_1audio_data_chunk_2"
        finally:
            os.unlink(text_file)

    def test_synthesize_passes_voice_parameters(self):
        """Synthesize should pass all voice parameters to edge_tts."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write("Test text")
            text_file = f.name

        try:
            args = argparse.Namespace(
                text_file=text_file,
                voice="ja-JP-NanamiNeural",
                pitch="+10Hz",
                rate="-5%",
                volume="+20%",
            )

            mock_tts = MagicMock()

            async def mock_stream():
                yield {"type": "audio", "data": b"data"}

            mock_tts.stream = mock_stream

            external_tts_runner = _load_external_tts_runner()

            with patch.object(external_tts_runner.edge_tts, "Communicate", return_value=mock_tts) as mock_communicate:
                asyncio.run(external_tts_runner.synthesize(args))

                mock_communicate.assert_called_once_with(
                    "Test text",
                    voice="ja-JP-NanamiNeural",
                    pitch="+10Hz",
                    rate="-5%",
                    volume="+20%",
                )
        finally:
            os.unlink(text_file)

    def test_synthesize_handles_empty_file(self):
        """Synthesize should handle empty text file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write("")
            text_file = f.name

        try:
            args = argparse.Namespace(
                text_file=text_file,
                voice="en-US-JennyNeural",
                pitch="+0Hz",
                rate="+0%",
                volume="+0%",
            )

            mock_tts = MagicMock()

            async def mock_stream():
                # Empty async generator - no audio chunks
                if False:  # Never yields, simulating empty response
                    yield {"type": "audio", "data": b""}

            mock_tts.stream = mock_stream

            external_tts_runner = _load_external_tts_runner()

            with patch.object(external_tts_runner.edge_tts, "Communicate", return_value=mock_tts):
                result = asyncio.run(external_tts_runner.synthesize(args))

            assert result == b""
        finally:
            os.unlink(text_file)

    def test_synthesize_handles_unicode_text(self):
        """Synthesize should handle Unicode text properly."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write("こんにちは、世界！")
            text_file = f.name

        try:
            args = argparse.Namespace(
                text_file=text_file,
                voice="ja-JP-NanamiNeural",
                pitch="+0Hz",
                rate="+0%",
                volume="+0%",
            )

            mock_tts = MagicMock()

            async def mock_stream():
                yield {"type": "audio", "data": b"test_audio"}

            mock_tts.stream = mock_stream

            external_tts_runner = _load_external_tts_runner()

            with patch.object(external_tts_runner.edge_tts, "Communicate", return_value=mock_tts) as mock_communicate:
                result = asyncio.run(external_tts_runner.synthesize(args))

                # Verify the text was read correctly
                mock_communicate.assert_called_once()
                call_args = mock_communicate.call_args[0]
                assert call_args[0] == "こんにちは、世界！"

            assert result == b"test_audio"
        finally:
            os.unlink(text_file)

    def test_synthesize_batch_encodes_audio(self):
        """Synthesize batch should return base64-encoded audio per item."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump({"items": [{"id": "1", "text": "Hello"}, {"id": "2", "text": "World"}]}, f)
            batch_file = f.name

        try:
            args = argparse.Namespace(
                batch_file=batch_file,
                voice="en-US-JennyNeural",
                pitch="+0Hz",
                rate="+0%",
                volume="+0%",
            )

            external_tts_runner = _load_external_tts_runner()

            async def fake_synthesize_text(text, _args):
                return f"audio-{text}".encode()

            with patch.object(external_tts_runner, "synthesize_text", side_effect=fake_synthesize_text):
                result = asyncio.run(external_tts_runner.synthesize_batch(args))

            expected = [
                {"id": "1", "audio": base64.b64encode(b"audio-Hello").decode("ascii")},
                {"id": "2", "audio": base64.b64encode(b"audio-World").decode("ascii")},
            ]
            assert result == expected
        finally:
            os.unlink(batch_file)

    def test_synthesize_batch_uses_bounded_concurrency(self):
        """Synthesize batch should not exceed the configured concurrency limit."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump(
                {
                    "items": [
                        {"id": "3", "text": "third"},
                        {"id": "1", "text": "first"},
                        {"id": "2", "text": "second"},
                        {"id": "5", "text": "fifth"},
                        {"id": "4", "text": "fourth"},
                    ]
                },
                f,
            )
            batch_file = f.name

        try:
            args = argparse.Namespace(
                batch_file=batch_file,
                voice="en-US-JennyNeural",
                pitch="+0Hz",
                rate="+0%",
                volume="+0%",
            )

            external_tts_runner = _load_external_tts_runner()
            external_tts_runner.BATCH_CONCURRENCY_LIMIT = 2

            running = 0
            max_running = 0

            async def fake_synthesize_text(text, _args):
                nonlocal running, max_running
                running += 1
                max_running = max(max_running, running)
                await asyncio.sleep(0)
                await asyncio.sleep(0)
                running -= 1
                return f"audio-{text}".encode()

            with patch.object(external_tts_runner, "synthesize_text", side_effect=fake_synthesize_text):
                result = asyncio.run(external_tts_runner.synthesize_batch(args))

            assert max_running <= external_tts_runner.BATCH_CONCURRENCY_LIMIT

            expected = [
                {"id": "1", "audio": base64.b64encode(b"audio-first").decode("ascii")},
                {"id": "2", "audio": base64.b64encode(b"audio-second").decode("ascii")},
                {"id": "3", "audio": base64.b64encode(b"audio-third").decode("ascii")},
                {"id": "4", "audio": base64.b64encode(b"audio-fourth").decode("ascii")},
                {"id": "5", "audio": base64.b64encode(b"audio-fifth").decode("ascii")},
            ]
            assert result == expected
        finally:
            os.unlink(batch_file)


class TestMainFunction:
    """Test the main entry point function."""

    def test_main_returns_zero_on_success(self):
        """Main should return 0 on successful execution."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write("Test")
            text_file = f.name

        try:
            mock_tts = MagicMock()

            async def mock_stream():
                yield {"type": "audio", "data": b"data"}

            mock_tts.stream = mock_stream

            external_tts_runner = _load_external_tts_runner()

            test_args = [
                "external_tts_runner.py",
                "--text-file",
                text_file,
                "--voice",
                "en-US-JennyNeural",
                "--pitch",
                "+0Hz",
                "--rate",
                "+0%",
                "--volume",
                "+0%",
            ]

            with patch("sys.argv", test_args):
                with patch.object(external_tts_runner.edge_tts, "Communicate", return_value=mock_tts):
                    with patch("sys.stdout") as mock_stdout:
                        mock_stdout.buffer = MagicMock()
                        result = external_tts_runner.main()

            assert result == 0
        finally:
            os.unlink(text_file)


class TestVoiceParameters:
    """Test handling of various voice parameter formats."""

    def test_negative_pitch(self):
        """Should handle negative pitch values."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write("Test")
            text_file = f.name

        try:
            args = argparse.Namespace(
                text_file=text_file,
                voice="en-US-JennyNeural",
                pitch="-20Hz",
                rate="+0%",
                volume="+0%",
            )

            mock_tts = MagicMock()

            async def mock_stream():
                yield {"type": "audio", "data": b"data"}

            mock_tts.stream = mock_stream

            external_tts_runner = _load_external_tts_runner()

            with patch.object(external_tts_runner.edge_tts, "Communicate", return_value=mock_tts) as mock_communicate:
                asyncio.run(external_tts_runner.synthesize(args))

                call_kwargs = mock_communicate.call_args[1]
                assert call_kwargs["pitch"] == "-20Hz"
        finally:
            os.unlink(text_file)

    def test_extreme_rate(self):
        """Should handle extreme rate values."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write("Test")
            text_file = f.name

        try:
            args = argparse.Namespace(
                text_file=text_file,
                voice="en-US-JennyNeural",
                pitch="+0Hz",
                rate="-50%",
                volume="+0%",
            )

            mock_tts = MagicMock()

            async def mock_stream():
                yield {"type": "audio", "data": b"data"}

            mock_tts.stream = mock_stream

            external_tts_runner = _load_external_tts_runner()

            with patch.object(external_tts_runner.edge_tts, "Communicate", return_value=mock_tts) as mock_communicate:
                asyncio.run(external_tts_runner.synthesize(args))

                call_kwargs = mock_communicate.call_args[1]
                assert call_kwargs["rate"] == "-50%"
        finally:
            os.unlink(text_file)

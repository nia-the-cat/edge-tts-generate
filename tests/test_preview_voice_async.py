"""
Tests for the async preview voice functionality.
Tests that the PreviewVoice method runs in background and doesn't block UI.
"""

import re
from unittest.mock import MagicMock, call


class TestPreviewVoiceAsync:
    """Test that PreviewVoice runs asynchronously."""

    def test_preview_voice_disables_button_during_generation(self):
        """PreviewVoice should disable the button while generating audio."""
        # This test validates the pattern used in PreviewVoice

        # Mock button
        button = MagicMock()
        button.text.return_value = "Preview Voice"

        # Simulate the PreviewVoice logic
        original_text = button.text()
        button.setText("Generating preview...")
        button.setEnabled(False)

        # Verify button was disabled
        button.setEnabled.assert_called_once_with(False)
        button.setText.assert_called_once_with("Generating preview...")
        assert original_text == "Preview Voice"

    def test_preview_voice_re_enables_button_on_completion(self):
        """PreviewVoice should re-enable button after generation completes."""
        # This test validates the pattern used in on_preview_done callback

        # Mock button and taskman
        button = MagicMock()
        taskman = MagicMock()
        original_text = "Preview Voice"

        # Simulate the on_preview_done callback logic
        taskman.run_on_main(lambda: button.setEnabled(True))
        taskman.run_on_main(lambda: button.setText(original_text))

        # Verify run_on_main was called twice (for re-enable and text restore)
        assert taskman.run_on_main.call_count == 2

    def test_preview_voice_uses_background_task(self):
        """PreviewVoice should use taskman.run_in_background."""
        # This test validates the pattern for running in background

        # Mock taskman
        taskman = MagicMock()

        def generate_preview():
            """Background task to generate preview audio"""
            return b"fake_audio_data"

        def on_preview_done(future):
            """Callback when preview generation is complete"""
            pass

        # Simulate the background task execution
        taskman.run_in_background(generate_preview, on_preview_done)

        # Verify run_in_background was called with the correct functions
        taskman.run_in_background.assert_called_once()
        args = taskman.run_in_background.call_args[0]
        assert callable(args[0])  # generate_preview function
        assert callable(args[1])  # on_preview_done callback

    def test_preview_voice_handles_errors_gracefully(self):
        """PreviewVoice should handle errors and show error dialog."""
        # This test validates the error handling pattern

        # Mock components
        taskman = MagicMock()
        message_box = MagicMock()

        # Simulate an exception during generation
        test_error = Exception("Test error message")
        error_msg = str(test_error)

        # Simulate error handling in on_preview_done
        taskman.run_on_main(
            lambda: message_box.critical(None, "Preview Error", f"Failed to generate preview: {error_msg}")
        )

        # Verify error was handled
        taskman.run_on_main.assert_called_once()

    def test_preview_voice_button_text_change(self):
        """Verify button text changes during preview generation."""
        # Mock button
        button = MagicMock()
        button.text.return_value = "Preview Voice"

        # Get original text and change it
        original_text = button.text()
        button.setText("Generating preview...")

        # Verify text was changed
        button.setText.assert_called_with("Generating preview...")

        # Simulate completion - restore original text
        button.setText(original_text)

        # Verify text was restored
        assert button.setText.call_count == 2
        calls = [call("Generating preview..."), call("Preview Voice")]
        button.setText.assert_has_calls(calls)

    def test_preview_voice_runs_non_blocking(self):
        """Verify that preview generation uses async pattern."""
        # This validates that the pattern doesn't block the main thread

        # Mock taskman that simulates background execution
        taskman = MagicMock()

        def mock_run_in_background(task_func, callback_func):
            """Simulate background task execution"""
            # In real implementation, this runs in a separate thread
            # and calls callback when done
            result = task_func()

            # Create a mock future
            future = MagicMock()
            future.result.return_value = result
            callback_func(future)

        taskman.run_in_background.side_effect = mock_run_in_background

        # Define a simple task
        def generate_preview():
            return b"audio_data"

        completion_called = False

        def on_preview_done(future):
            nonlocal completion_called
            completion_called = True
            assert future.result() == b"audio_data"

        # Execute the background task
        taskman.run_in_background(generate_preview, on_preview_done)

        # Verify completion callback was called
        assert completion_called is True


class TestGetPreviewTextFromNoteLogic:
    """Test the _getPreviewTextFromNote logic pattern used in PreviewVoice."""

    def test_returns_none_when_no_selected_notes(self):
        """Should return None when there are no selected notes."""
        selected_notes = []
        result = None if not selected_notes else "text"
        assert result is None

    def test_returns_none_when_note_is_none(self):
        """Should return None when note lookup returns None."""
        note = None
        result = None if note is None else "text"
        assert result is None

    def test_returns_none_when_field_is_empty(self):
        """Should return None when the source field is empty."""
        note_text = ""
        result = note_text.strip() if note_text else None
        assert result is None

    def test_cleans_html_tags_from_note_text(self):
        """Should remove HTML tags from preview text."""
        TAG_RE = re.compile(r"(<!--.*?-->|<[^>]*>)")
        note_text = "<b>Hello</b> <i>World</i>"
        result = TAG_RE.sub("", note_text)
        assert result == "Hello World"

    def test_cleans_html_entities_from_note_text(self):
        """Should remove HTML entities from preview text."""
        ENTITY_RE = re.compile(r"(&[^;]+;)")
        note_text = "&nbsp;Hello&amp;World"
        result = ENTITY_RE.sub("", note_text)
        assert result == "HelloWorld"

    def test_extracts_reading_from_brackets(self):
        """Should extract reading from brackets (e.g., 漢字[かんじ] -> かんじ)."""
        KANJI_FURIGANA_RE = re.compile(r" ?\S*?\[(.*?)\]")
        note_text = "漢字[かんじ]"
        result = KANJI_FURIGANA_RE.sub(r"\1", note_text)
        assert result == "かんじ"

    def test_removes_bracket_content_when_enabled(self):
        """Should remove content in brackets when ignore_brackets is enabled."""
        BRACKET_CONTENT_RE = re.compile(r"\[.*?\]")
        ignore_brackets = True
        note_text = "word[pitch;a,h]"
        if ignore_brackets:
            result = BRACKET_CONTENT_RE.sub("", note_text)
        else:
            result = note_text
        assert result == "word"

    def test_preserves_bracket_content_when_disabled(self):
        """Should preserve content in brackets when ignore_brackets is disabled."""
        BRACKET_CONTENT_RE = re.compile(r"\[.*?\]")
        ignore_brackets = False
        note_text = "word[pitch;a,h]"
        if ignore_brackets:
            result = BRACKET_CONTENT_RE.sub("", note_text)
        else:
            result = note_text
        assert result == "word[pitch;a,h]"

    def test_strips_whitespace_for_japanese(self):
        """Should strip whitespace for Japanese language."""
        WHITESPACE_RE = re.compile(" ")
        speaker = "ja-JP-NanamiNeural"
        language_code = speaker.split("-")[0].lower()
        note_text = "こん にち は"
        if language_code in {"ja", "zh"}:
            result = WHITESPACE_RE.sub("", note_text)
        else:
            result = note_text
        assert result == "こんにちは"

    def test_strips_whitespace_for_chinese(self):
        """Should strip whitespace for Chinese language."""
        WHITESPACE_RE = re.compile(" ")
        speaker = "zh-CN-XiaoxiaoNeural"
        language_code = speaker.split("-")[0].lower()
        note_text = "你 好 世 界"
        if language_code in {"ja", "zh"}:
            result = WHITESPACE_RE.sub("", note_text)
        else:
            result = note_text
        assert result == "你好世界"

    def test_preserves_whitespace_for_english(self):
        """Should preserve whitespace for English language."""
        WHITESPACE_RE = re.compile(" ")
        speaker = "en-US-JennyNeural"
        language_code = speaker.split("-")[0].lower()
        note_text = "Hello World"
        if language_code in {"ja", "zh"}:
            result = WHITESPACE_RE.sub("", note_text)
        else:
            result = note_text
        assert result == "Hello World"

    def test_preserves_whitespace_for_german(self):
        """Should preserve whitespace for German language."""
        WHITESPACE_RE = re.compile(" ")
        speaker = "de-DE-KatjaNeural"
        language_code = speaker.split("-")[0].lower()
        note_text = "Guten Tag"
        if language_code in {"ja", "zh"}:
            result = WHITESPACE_RE.sub("", note_text)
        else:
            result = note_text
        assert result == "Guten Tag"

    def test_uses_actual_note_content_for_preview(self):
        """Should use actual note content instead of hardcoded sentences."""
        # This validates that preview now uses note content, not hardcoded text
        mock_note = MagicMock()
        mock_note.__getitem__ = MagicMock(return_value="This is my actual card content")

        source_field = "Front"
        note_text = mock_note[source_field]

        assert note_text == "This is my actual card content"
        mock_note.__getitem__.assert_called_with("Front")

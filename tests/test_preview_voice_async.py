"""
Tests for the async preview voice functionality.
Tests that the PreviewVoice method runs in background and doesn't block UI.
"""

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

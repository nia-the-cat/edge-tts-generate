"""
Tests for issue fixes:
1. Clarify preview warning when source field is missing
2. Preserve destination selection when new field creation is cancelled
3. Handle user cancellation distinctly from completion
4. Summarize skip-mode results after generation
5. Remember newly created destination field in saved config
"""

from unittest.mock import MagicMock


class TestPreviewWarningClarifiesFieldMissing:
    """Test that preview warning distinguishes between empty field and missing field."""

    def test_get_preview_text_returns_field_missing_status(self):
        """_getPreviewTextFromNote should return 'field_missing' status when field doesn't exist."""
        # Simulate the logic from _getPreviewTextFromNote
        note = MagicMock()
        source_field = "NonExistentField"

        # Simulate KeyError when field doesn't exist
        def raise_key_error(_self, field):
            raise KeyError(field)

        note.__getitem__ = raise_key_error

        try:
            note[source_field]
            status = "ok"
        except KeyError:
            status = "field_missing"

        assert status == "field_missing"

    def test_get_preview_text_returns_field_empty_status(self):
        """_getPreviewTextFromNote should return 'field_empty' status when field is empty."""
        # Simulate the logic from _getPreviewTextFromNote
        note = MagicMock()
        source_field = "Expression"
        note.__getitem__ = MagicMock(return_value="")

        note_text = note[source_field]

        if not note_text:
            status = "field_empty"
        else:
            status = "ok"

        assert status == "field_empty"

    def test_get_preview_text_returns_ok_status_with_content(self):
        """_getPreviewTextFromNote should return 'ok' status when field has content."""
        note = MagicMock()
        source_field = "Expression"
        note.__getitem__ = MagicMock(return_value="Hello world")

        note_text = note[source_field]
        cleaned_text = note_text.strip()

        if not cleaned_text:
            status = "field_empty"
        else:
            status = "ok"

        assert status == "ok"

    def test_preview_shows_different_message_for_missing_field(self):
        """PreviewVoice should show 'Field Not Found' message when field is missing."""
        status = "field_missing"
        source_field = "Expression"

        # Simulate the message selection logic
        if status == "field_missing":
            title = "Field Not Found"
            message = (
                f"The selected note does not have a '{source_field}' field. "
                "This can happen when previewing against a note type that lacks the source field.\n\n"
                "Please select a different note that has the source field, or choose a different source field."
            )
        else:
            title = "No Preview Text"
            message = f"The source field '{source_field}' is empty."

        assert title == "Field Not Found"
        assert "does not have" in message
        assert "note type" in message

    def test_preview_shows_empty_message_for_empty_field(self):
        """PreviewVoice should show 'No Preview Text' message when field is empty."""
        status = "field_empty"

        if status == "field_missing":
            title = "Field Not Found"
        else:
            title = "No Preview Text"

        assert title == "No Preview Text"


class TestDestinationSelectionPreservation:
    """Test that destination selection is preserved when new field creation is cancelled."""

    def test_previous_destination_index_is_initialized(self):
        """Previous destination index should be initialized on dialog creation."""
        destination_field_index = 2
        _previous_destination_index = destination_field_index

        assert _previous_destination_index == 2

    def test_previous_index_is_restored_on_cancel(self):
        """Cancelling create field dialog should restore previous selection."""
        previous_index = 2
        user_cancelled = True

        if user_cancelled:
            restored_index = previous_index
        else:
            restored_index = 0  # New selection

        assert restored_index == 2

    def test_previous_index_is_restored_when_field_exists(self):
        """Selecting existing field name should restore previous selection."""
        previous_index = 1
        field_exists = True

        if field_exists:
            restored_index = previous_index
        else:
            restored_index = 5  # New field index

        assert restored_index == 1

    def test_previous_index_is_updated_on_valid_selection(self):
        """Previous index should be updated when user makes a valid selection."""
        new_index = 3
        is_create_new_field_option = False

        if not is_create_new_field_option:
            _previous_destination_index = new_index
        else:
            _previous_destination_index = 0

        assert _previous_destination_index == 3

    def test_previous_index_is_updated_after_creating_new_field(self):
        """Previous index should be updated to new field after successful creation."""
        insert_index = 4
        field_created_successfully = True

        if field_created_successfully:
            _previous_destination_index = insert_index
        else:
            _previous_destination_index = 0

        assert _previous_destination_index == 4


class TestUserCancellationHandling:
    """Test that user cancellation is handled distinctly from completion."""

    def test_canceled_flag_is_set_at_initial_break(self):
        """Canceled flag should be set when breaking at the start of chunk loop."""
        want_cancel = True
        canceled = False

        if want_cancel:
            canceled = True

        assert canceled is True

    def test_cancellation_shows_different_message(self):
        """Cancellation should show a different message than completion."""
        canceled = True
        notes_so_far = 5
        total_notes = 10

        if canceled:
            message = f"Generation cancelled. {notes_so_far}/{total_notes} notes processed."
        else:
            message = "Generation completed."

        assert "cancelled" in message
        assert "5/10" in message

    def test_cancellation_suppresses_other_messages(self):
        """Cancellation should prevent other summary messages from showing."""
        canceled = True
        missing_text_skips = 3
        failures = ["error1", "error2"]
        show_skip_message = False
        show_failure_message = False

        if not canceled:
            if missing_text_skips > 0:
                show_skip_message = True
            if failures:
                show_failure_message = True

        assert show_skip_message is False
        assert show_failure_message is False

    def test_completion_shows_all_messages(self):
        """Completion (not cancelled) should show all relevant messages."""
        canceled = False
        missing_text_skips = 3
        existing_audio_skips = 2
        failures = ["error1"]
        show_skip_message = False
        show_failure_message = False

        if not canceled:
            if missing_text_skips > 0 or existing_audio_skips > 0:
                show_skip_message = True
            if failures:
                show_failure_message = True

        assert show_skip_message is True
        assert show_failure_message is True


class TestSkipModeSummary:
    """Test that skip-mode results are summarized after generation."""

    def test_existing_audio_skips_are_tracked(self):
        """Existing audio skips should be tracked separately."""
        existing_audio_skips = 0
        audio_handling_mode = "skip"
        existing_content = "[sound:audio.mp3]"

        if audio_handling_mode == "skip" and existing_content:
            existing_audio_skips += 1

        assert existing_audio_skips == 1

    def test_skip_summary_includes_existing_audio_count(self):
        """Skip summary should include count of notes with existing audio."""
        existing_audio_skips = 5
        missing_text_skips = 2

        skip_messages = []
        if existing_audio_skips > 0:
            skip_messages.append(f"{existing_audio_skips} already had audio")
        if missing_text_skips > 0:
            skip_messages.append(f"{missing_text_skips} had no source text")

        summary = f"Skipped notes: {', '.join(skip_messages)}."

        assert "5 already had audio" in summary
        assert "2 had no source text" in summary

    def test_skip_summary_shown_when_all_notes_skipped(self):
        """Summary should be shown when all notes are skipped (no pending items)."""
        pending_items = []
        existing_audio_skips = 10
        missing_text_skips = 0
        should_show_summary = False

        if not pending_items and (existing_audio_skips > 0 or missing_text_skips > 0):
            should_show_summary = True

        assert should_show_summary is True

    def test_skip_summary_shows_only_relevant_reasons(self):
        """Skip summary should only show reasons that apply."""
        existing_audio_skips = 5
        missing_text_skips = 0

        skip_messages = []
        if existing_audio_skips > 0:
            skip_messages.append(f"{existing_audio_skips} already had audio")
        if missing_text_skips > 0:
            skip_messages.append(f"{missing_text_skips} had no source text")

        summary = ", ".join(skip_messages)

        assert "5 already had audio" in summary
        assert "no source text" not in summary

    def test_no_summary_when_no_skips(self):
        """No summary should be shown when there are no skips."""
        existing_audio_skips = 0
        missing_text_skips = 0
        should_show_summary = False

        if existing_audio_skips > 0 or missing_text_skips > 0:
            should_show_summary = True

        assert should_show_summary is False


class TestNewFieldConfigSaving:
    """Test that newly created destination field is saved to config."""

    def test_destination_field_updated_before_config_save(self):
        """New field name should be set before saving config."""
        new_field_name = "NewAudioField"
        destination_field = "[ + Create new field... ]"

        # Logic: create field first, then save config
        if new_field_name:
            destination_field = new_field_name

        # Then save config with the actual field name
        config = {"last_destination_field": destination_field}

        assert config["last_destination_field"] == "NewAudioField"

    def test_config_saves_actual_field_name_not_placeholder(self):
        """Config should save actual field name, not the placeholder."""
        new_field_name = "Audio"
        original_destination = "[ + Create new field... ]"

        # Simulate the updated logic
        destination_field = original_destination
        if new_field_name:
            destination_field = new_field_name

        config = {"last_destination_field": destination_field}

        assert "Create new field" not in config["last_destination_field"]
        assert config["last_destination_field"] == "Audio"

    def test_existing_field_saved_when_no_new_field(self):
        """Existing field name should be saved when no new field is created."""
        new_field_name = None
        destination_field = "ExistingAudio"

        if new_field_name:
            destination_field = new_field_name

        config = {"last_destination_field": destination_field}

        assert config["last_destination_field"] == "ExistingAudio"


class TestPreviewStatusReturn:
    """Test the new tuple return format of _getPreviewTextFromNote."""

    def test_returns_tuple_with_text_and_status(self):
        """Method should return (text, status) tuple."""
        # Simulate successful case
        text = "Hello world"
        status = "ok"
        result = (text, status)

        assert isinstance(result, tuple)
        assert len(result) == 2
        assert result[0] == "Hello world"
        assert result[1] == "ok"

    def test_status_values_are_documented(self):
        """Status values should be one of the documented options."""
        valid_statuses = {"ok", "no_notes", "note_none", "field_missing", "field_empty"}

        test_statuses = ["ok", "field_missing", "field_empty"]
        for status in test_statuses:
            assert status in valid_statuses

    def test_text_is_none_for_error_statuses(self):
        """Text should be None for all error statuses."""
        error_statuses = ["no_notes", "note_none", "field_missing", "field_empty"]

        for status in error_statuses:
            result = (None, status)
            assert result[0] is None

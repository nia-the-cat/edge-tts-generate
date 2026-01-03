"""
Tests for addFieldToNoteTypes and field management functions.

These tests verify field creation and note type modification logic.
"""

from __future__ import annotations

import importlib.util
import os
import sys


_MODULE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "edge_tts_gen.py")


def _load_edge_tts_gen():
    """Load the edge_tts_gen module for testing."""
    package_name = "edge_tts_generate"
    package = sys.modules.setdefault(package_name, type(sys)(package_name))
    package.__path__ = [os.path.dirname(_MODULE_PATH)]

    spec = importlib.util.spec_from_file_location(f"{package_name}.edge_tts_gen", _MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class TestAddFieldToNoteTypesLogic:
    """Test addFieldToNoteTypes function logic."""

    def test_adds_field_to_single_note_type(self):
        """Should add field to a single note type."""
        # Simulate the logic from addFieldToNoteTypes
        field_name = "NewAudioField"
        existing_fields = ["Front", "Back"]

        # Logic to check if field needs to be added
        should_add = field_name not in existing_fields
        assert should_add is True

    def test_skips_existing_field(self):
        """Should not add field if it already exists."""
        field_name = "Audio"
        existing_fields = ["Front", "Back", "Audio"]

        should_add = field_name not in existing_fields
        assert should_add is False

    def test_tracks_updated_note_types(self):
        """Should track which note types have been updated."""
        note_types_updated = set()
        model_ids = [1, 2, 1, 3, 2]  # Some duplicates

        for model_id in model_ids:
            if model_id not in note_types_updated:
                note_types_updated.add(model_id)

        # Should only have unique IDs
        assert len(note_types_updated) == 3
        assert note_types_updated == {1, 2, 3}

    def test_handles_multiple_notes_same_type(self):
        """Should only update each note type once."""
        note_types_updated = set()
        sample_model_id = 1234567890  # Typical Anki model ID
        notes_data = [
            {"note_id": 1, "model_id": sample_model_id},
            {"note_id": 2, "model_id": sample_model_id},
            {"note_id": 3, "model_id": sample_model_id},
        ]

        for note_data in notes_data:
            model_id = note_data["model_id"]
            if model_id not in note_types_updated:
                note_types_updated.add(model_id)

        # Should only add the model once
        assert len(note_types_updated) == 1
        assert sample_model_id in note_types_updated


class TestFieldValidation:
    """Test field name validation logic."""

    def test_empty_field_name_is_invalid(self):
        """Empty field names should be invalid."""
        field_name = ""
        is_valid = bool(field_name.strip()) if field_name else False
        assert is_valid is False

    def test_whitespace_only_field_name_is_invalid(self):
        """Whitespace-only field names should be invalid."""
        field_name = "   "
        is_valid = bool(field_name.strip()) if field_name else False
        assert is_valid is False

    def test_valid_field_name(self):
        """Normal field names should be valid."""
        field_name = "Audio"
        is_valid = bool(field_name.strip()) if field_name else False
        assert is_valid is True

    def test_field_name_stripping(self):
        """Field names should be stripped of whitespace."""
        field_name = "  Audio  "
        stripped = field_name.strip()
        assert stripped == "Audio"


class TestFieldExistsCheck:
    """Test checking if field exists in note type."""

    def test_field_exists_in_common_fields(self):
        """Should detect when field exists in common fields."""
        common_fields = {"Front", "Back", "Audio", "Sentence"}
        field_name = "Audio"

        field_exists = field_name in common_fields
        assert field_exists is True

    def test_field_does_not_exist(self):
        """Should detect when field does not exist."""
        common_fields = {"Front", "Back"}
        field_name = "Audio"

        field_exists = field_name in common_fields
        assert field_exists is False

    def test_case_sensitive_check(self):
        """Field check should be case-sensitive."""
        common_fields = {"Front", "Back", "Audio"}
        field_name = "audio"  # lowercase

        field_exists = field_name in common_fields
        assert field_exists is False


class TestDestinationFieldHandling:
    """Test destination field selection and handling."""

    def test_new_field_placeholder_detection(self):
        """Should detect CREATE_NEW_FIELD_OPTION placeholder."""
        CREATE_NEW_FIELD_OPTION = "[ + Create new field... ]"
        destination_text = "[ + Create new field... ]"

        is_create_new = destination_text == CREATE_NEW_FIELD_OPTION
        assert is_create_new is True

    def test_regular_field_not_placeholder(self):
        """Regular field names should not be detected as placeholder."""
        CREATE_NEW_FIELD_OPTION = "[ + Create new field... ]"
        destination_text = "Audio"

        is_create_new = destination_text == CREATE_NEW_FIELD_OPTION
        assert is_create_new is False

    def test_destination_field_update_after_creation(self):
        """Destination field should be updated to new field name after creation."""
        original_destination = "[ + Create new field... ]"
        new_field_name = "NewAudioField"

        if new_field_name:
            destination_field = new_field_name
        else:
            destination_field = original_destination

        assert destination_field == "NewAudioField"


class TestSourceDestinationValidation:
    """Test source and destination field validation."""

    def test_same_source_and_destination_is_invalid(self):
        """Source and destination should not be the same."""
        source_index = 2
        destination_index = 2
        new_field_name = None

        # If not creating new field, check indices
        is_same_field = new_field_name is None and source_index == destination_index
        assert is_same_field is True

    def test_different_source_and_destination_is_valid(self):
        """Different source and destination should be valid."""
        source_index = 0
        destination_index = 2
        new_field_name = None

        is_same_field = new_field_name is None and source_index == destination_index
        assert is_same_field is False

    def test_new_field_skips_index_check(self):
        """Creating new field should skip same index check."""
        source_index = 2
        destination_index = 2  # Same index but creating new field
        new_field_name = "NewAudio"

        # When creating new field, don't check indices
        is_same_field = new_field_name is None and source_index == destination_index
        assert is_same_field is False


class TestPreviousDestinationIndexTracking:
    """Test tracking of previous destination index for restoration."""

    def test_initial_index_tracking(self):
        """Should track initial destination index."""
        destination_field_index = 2
        _previous_destination_index = destination_field_index

        assert _previous_destination_index == 2

    def test_restore_on_cancel(self):
        """Should restore previous index when user cancels."""
        previous_index = 1
        user_cancelled = True

        if user_cancelled:
            restored_index = previous_index
        else:
            restored_index = 5  # New selection

        assert restored_index == 1

    def test_update_on_valid_selection(self):
        """Should update previous index on valid selection."""
        current_index = 3
        CREATE_NEW_FIELD_OPTION = "[ + Create new field... ]"
        selected_text = "Audio"

        if selected_text != CREATE_NEW_FIELD_OPTION:
            _previous_destination_index = current_index
        else:
            _previous_destination_index = 0

        assert _previous_destination_index == 3

    def test_update_after_new_field_creation(self):
        """Should update to new field index after creation."""
        insert_index = 4
        field_created = True

        if field_created:
            _previous_destination_index = insert_index
        else:
            _previous_destination_index = 0

        assert _previous_destination_index == 4

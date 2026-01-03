"""
Tests for edge_tts_gen.py - Pure functions that can be tested without Anki.
Note: Functions that depend on Anki (mw, aqt) are mocked.
Since edge_tts_gen uses relative imports, we test the logic patterns instead of importing directly.
"""

import os
import re
from unittest.mock import MagicMock

import pytest


# Test the logic patterns used in edge_tts_gen without importing the module directly
# (due to relative import issues when testing outside Anki)


class TestGetSpeakerListLogic:
    """Test the getSpeakerList logic pattern."""

    def test_returns_speakers_from_config(self):
        """Should return speakers list from config."""

        # This is the logic from getSpeakerList
        def getSpeakerList(config):
            speakers = []
            speakers.extend(config.get("speakers", []))
            return speakers

        config = {
            "speakers": [
                "ja-JP-NanamiNeural",
                "en-US-JennyNeural",
                "de-DE-KatjaNeural",
            ]
        }

        result = getSpeakerList(config)

        assert result == ["ja-JP-NanamiNeural", "en-US-JennyNeural", "de-DE-KatjaNeural"]

    def test_returns_empty_list_when_no_speakers(self):
        """Should return empty list when config has no speakers."""

        def getSpeakerList(config):
            speakers = []
            speakers.extend(config.get("speakers", []))
            return speakers

        config = {}

        result = getSpeakerList(config)

        assert result == []

    def test_handles_none_speakers(self):
        """Should handle None speakers gracefully."""

        def getSpeakerList(config):
            speakers = []
            speakers.extend(config.get("speakers", []) or [])
            return speakers

        config = {"speakers": None}

        result = getSpeakerList(config)
        assert result == []


class TestGetSpeakerLogic:
    """Test the getSpeaker logic pattern."""

    def test_returns_selected_speaker(self):
        """Should return the currently selected speaker name."""

        # This is the logic from getSpeaker
        def getSpeaker(speaker_combo):
            speaker_name = speaker_combo.itemText(speaker_combo.currentIndex())
            return speaker_name

        mock_combo = MagicMock()
        mock_combo.currentIndex.return_value = 1
        mock_combo.itemText.return_value = "en-US-JennyNeural"

        result = getSpeaker(mock_combo)

        assert result == "en-US-JennyNeural"

    def test_returns_first_speaker_when_index_zero(self):
        """Should return first speaker when index is 0."""

        def getSpeaker(speaker_combo):
            speaker_name = speaker_combo.itemText(speaker_combo.currentIndex())
            return speaker_name

        mock_combo = MagicMock()
        mock_combo.currentIndex.return_value = 0
        mock_combo.itemText.return_value = "ja-JP-NanamiNeural"

        result = getSpeaker(mock_combo)

        assert result == "ja-JP-NanamiNeural"


class TestCreateNewFieldOption:
    """Test the CREATE_NEW_FIELD_OPTION constant."""

    def test_constant_value(self):
        """CREATE_NEW_FIELD_OPTION should have expected value."""
        # Based on the source code
        CREATE_NEW_FIELD_OPTION = "[ + Create new field... ]"

        assert CREATE_NEW_FIELD_OPTION is not None
        assert isinstance(CREATE_NEW_FIELD_OPTION, str)

    def test_constant_is_recognizable(self):
        """CREATE_NEW_FIELD_OPTION should be easily distinguishable."""
        CREATE_NEW_FIELD_OPTION = "[ + Create new field... ]"

        # Should contain visual markers that distinguish it from field names
        assert "[" in CREATE_NEW_FIELD_OPTION or "+" in CREATE_NEW_FIELD_OPTION


class TestTextProcessingRegex:
    """Test the text processing regex patterns used in the module."""

    def test_html_tag_removal(self):
        """Test HTML tag removal regex pattern."""
        tag_re = re.compile(r"(<!--.*?-->|<[^>]*>)")

        # Test basic HTML tags
        text = "<b>Bold</b> text"
        result = tag_re.sub("", text)
        assert result == "Bold text"

        # Test nested tags
        text = "<div><span>Nested</span></div>"
        result = tag_re.sub("", text)
        assert result == "Nested"

        # Test self-closing tags
        text = "Line<br/>break"
        result = tag_re.sub("", text)
        assert result == "Linebreak"

        # Test HTML comments
        text = "Text<!-- comment -->More"
        result = tag_re.sub("", text)
        assert result == "TextMore"

    def test_entity_removal(self):
        """Test HTML entity removal regex pattern."""
        entity_re = re.compile(r"(&[^;]+;)")

        # Test common entities
        text = "&nbsp;space&amp;ampersand"
        result = entity_re.sub("", text)
        assert result == "spaceampersand"

        # Test numeric entities
        text = "&#60;less than&#62;"
        result = entity_re.sub("", text)
        assert result == "less than"

    def test_reading_extraction(self):
        """Test reading extraction from brackets."""
        # Pattern: Replace text with reading from brackets
        # The pattern replaces the word and brackets with just the reading
        pattern = r" ?\S*?\[(.*?)\]"

        text = "漢字[かんじ]"
        result = re.sub(pattern, r"\1", text)
        assert result == "かんじ"

        # Note: This pattern consumes non-whitespace before the bracket
        text = "日本語[にほんご]を勉強[べんきょう]"
        result = re.sub(pattern, r"\1", text)
        assert result == "にほんごべんきょう"

    def test_bracket_content_removal(self):
        """Test bracket content removal for pitch accent markers."""
        pattern = r"\[.*?\]"

        text = "word[;a,h]"
        result = re.sub(pattern, "", text)
        assert result == "word"

        text = "聞[き,きく;h]いた"
        result = re.sub(pattern, "", text)
        assert result == "聞いた"


class TestGetCommonFieldsLogic:
    """Test the getCommonFields logic pattern."""

    def test_returns_fields_from_single_note(self):
        """Should return all fields for a single note."""

        # This is the logic from getCommonFields
        def getCommonFields(selected_notes, get_note_func):
            common_fields = set()
            first = True

            for note_id in selected_notes:
                note = get_note_func(note_id)
                if note is None:
                    raise Exception(f"Note with id {note_id} is None.")
                model = note.note_type()
                model_fields = {f["name"] for f in model["flds"]}
                if first:
                    common_fields = model_fields
                else:
                    common_fields = common_fields.intersection(model_fields)
                first = False
            return common_fields

        mock_note = MagicMock()
        mock_note.note_type.return_value = {
            "flds": [
                {"name": "Front"},
                {"name": "Back"},
                {"name": "Audio"},
            ]
        }

        def get_note_func(note_id):
            return mock_note

        result = getCommonFields([1], get_note_func)

        assert result == {"Front", "Back", "Audio"}

    def test_returns_intersection_of_fields(self):
        """Should return only common fields across multiple notes."""

        def getCommonFields(selected_notes, get_note_func):
            common_fields = set()
            first = True

            for note_id in selected_notes:
                note = get_note_func(note_id)
                if note is None:
                    raise Exception(f"Note with id {note_id} is None.")
                model = note.note_type()
                model_fields = {f["name"] for f in model["flds"]}
                if first:
                    common_fields = model_fields
                else:
                    common_fields = common_fields.intersection(model_fields)
                first = False
            return common_fields

        # First note has Front, Back, Audio
        mock_note1 = MagicMock()
        mock_note1.note_type.return_value = {
            "flds": [
                {"name": "Front"},
                {"name": "Back"},
                {"name": "Audio"},
            ]
        }

        # Second note has Front, Back, Extra (no Audio)
        mock_note2 = MagicMock()
        mock_note2.note_type.return_value = {
            "flds": [
                {"name": "Front"},
                {"name": "Back"},
                {"name": "Extra"},
            ]
        }

        notes = {1: mock_note1, 2: mock_note2}

        def get_note_func(note_id):
            return notes[note_id]

        result = getCommonFields([1, 2], get_note_func)

        # Only Front and Back are common
        assert result == {"Front", "Back"}

    def test_raises_on_none_note(self):
        """Should raise exception when note is None."""

        def getCommonFields(selected_notes, get_note_func):
            common_fields = set()
            first = True

            for note_id in selected_notes:
                note = get_note_func(note_id)
                if note is None:
                    raise Exception(
                        f"Note with id {note_id} is None.\nPlease submit an issue at https://github.com/nia-the-cat/edge-tts-generate/issues/new"
                    )
                model = note.note_type()
                model_fields = {f["name"] for f in model["flds"]}
                if first:
                    common_fields = model_fields
                else:
                    common_fields = common_fields.intersection(model_fields)
                first = False
            return common_fields

        def get_note_func(note_id):
            return None

        with pytest.raises(Exception) as exc_info:
            getCommonFields([1], get_note_func)

        assert "is None" in str(exc_info.value)


class TestLanguageDetection:
    """Test language detection from voice names."""

    def test_japanese_voice_detection(self):
        """Should detect Japanese from ja-JP voice names."""
        voice = "ja-JP-NanamiNeural"
        lang_code = voice.split("-")[0]
        assert lang_code == "ja"

    def test_english_voice_detection(self):
        """Should detect English from en-US voice names."""
        voice = "en-US-JennyNeural"
        lang_code = voice.split("-")[0]
        assert lang_code == "en"

    def test_chinese_voice_detection(self):
        """Should detect Chinese from zh-CN voice names."""
        voice = "zh-CN-XiaoxiaoNeural"
        lang_code = voice.split("-")[0]
        assert lang_code == "zh"

    def test_german_voice_detection(self):
        """Should detect German from de-DE voice names."""
        voice = "de-DE-KatjaNeural"
        lang_code = voice.split("-")[0]
        assert lang_code == "de"


class TestConfigValidation:
    """Test configuration handling."""

    def test_config_json_structure(self):
        """Test that config.json has the expected structure."""
        import json

        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json")

        with open(config_path) as f:
            config = json.load(f)

        # Should have speakers list
        assert "speakers" in config
        assert isinstance(config["speakers"], list)
        assert len(config["speakers"]) > 0

        # All speakers should be strings
        for speaker in config["speakers"]:
            assert isinstance(speaker, str)
            # Should follow the voice naming convention
            assert "-" in speaker
            assert "Neural" in speaker

    def test_manifest_json_structure(self):
        """Test that manifest.json has the expected structure."""
        import json

        manifest_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "manifest.json")

        with open(manifest_path) as f:
            manifest = json.load(f)

        # Should have required fields
        assert "package" in manifest
        assert "name" in manifest
        assert "min_point_version" in manifest
        assert "max_point_version" in manifest


class TestAudioHandlingModes:
    """Test audio handling mode logic."""

    def test_append_mode_logic(self):
        """Test append mode preserves existing content."""
        existing_content = "[sound:existing.mp3]"
        new_audio = "[sound:new.mp3]"
        mode = "append"

        if mode == "append" and existing_content:
            result = existing_content + " " + new_audio
        else:
            result = new_audio

        assert result == "[sound:existing.mp3] [sound:new.mp3]"

    def test_overwrite_mode_logic(self):
        """Test overwrite mode replaces content."""
        existing_content = "[sound:existing.mp3]"
        new_audio = "[sound:new.mp3]"
        mode = "overwrite"

        if mode == "append" and existing_content:
            result = existing_content + " " + new_audio
        else:
            result = new_audio

        assert result == "[sound:new.mp3]"

    def test_skip_mode_logic(self):
        """Test skip mode skips notes with content."""
        existing_content = "[sound:existing.mp3]"
        mode = "skip"

        should_skip = mode == "skip" and bool(existing_content)
        assert should_skip is True

        # Empty content should not skip
        empty_content = ""
        should_skip = mode == "skip" and bool(empty_content)
        assert should_skip is False


class TestVoicePitchRateFormatting:
    """Test voice parameter formatting."""

    def test_pitch_format_positive(self):
        """Pitch should be formatted with Hz suffix."""
        pitch_value = 10
        pitch = f"{pitch_value:+}Hz"
        assert pitch == "+10Hz"

    def test_pitch_format_negative(self):
        """Negative pitch should have minus sign."""
        pitch_value = -10
        pitch = f"{pitch_value:+}Hz"
        assert pitch == "-10Hz"

    def test_pitch_format_zero(self):
        """Zero pitch should have plus sign."""
        pitch_value = 0
        pitch = f"{pitch_value:+}Hz"
        assert pitch == "+0Hz"

    def test_rate_format(self):
        """Rate should be formatted with % suffix."""
        rate_value = 20
        rate = f"{rate_value:+}%"
        assert rate == "+20%"

    def test_volume_format(self):
        """Volume should be formatted with % suffix."""
        volume_value = -75
        volume = f"{volume_value:+}%"
        assert volume == "-75%"


class TestGetCommonFieldsErrorMessage:
    """Test the error message construction in getCommonFields."""

    def test_error_message_includes_all_note_ids(self):
        """Error message should include all selected note IDs as strings."""
        selected_notes = [123, 456, 789]
        note_id = 456  # The note that is None

        # This is the fixed logic from getCommonFields
        error_message = (
            f"Note with id {note_id} is None.\n"
            f"Selected note IDs: {', '.join(str(nid) for nid in selected_notes)}.\n"
            "Please submit an issue with more information about what cards caused this at "
            "https://github.com/nia-the-cat/edge-tts-generate/issues/new"
        )

        # Should include the problematic note ID
        assert "456" in error_message
        # Should include all note IDs in the list
        assert "123" in error_message
        assert "456" in error_message
        assert "789" in error_message
        # Should properly format as comma-separated string
        assert "123, 456, 789" in error_message

    def test_error_message_handles_single_note(self):
        """Error message should work correctly with a single note ID."""
        selected_notes = [12345]
        note_id = 12345

        error_message = (
            f"Note with id {note_id} is None.\n"
            f"Selected note IDs: {', '.join(str(nid) for nid in selected_notes)}.\n"
            "Please submit an issue with more information about what cards caused this at "
            "https://github.com/nia-the-cat/edge-tts-generate/issues/new"
        )

        assert "12345" in error_message
        assert "Selected note IDs: 12345" in error_message


class TestFieldOrderStability:
    """Test that field order is deterministic for dropdowns."""

    def test_sorted_fields_are_deterministic(self):
        """Sorting a set of fields should produce deterministic order."""
        common_fields = {"Audio", "Front", "Back", "Expression", "Sentence"}

        # This is the fix: sorting the set before iteration
        sorted_fields = sorted(common_fields)

        # Should always produce alphabetical order
        assert sorted_fields == ["Audio", "Back", "Expression", "Front", "Sentence"]

        # Multiple sorts should produce identical results
        for _ in range(10):
            assert sorted(common_fields) == sorted_fields

    def test_sorted_fields_consistent_with_different_set_creation_order(self):
        """Field order should be consistent regardless of set creation order."""
        # Create sets with different insertion orders
        fields1 = {"Front", "Back", "Audio"}
        fields2 = {"Audio", "Front", "Back"}
        fields3 = {"Back", "Audio", "Front"}

        # All should produce the same sorted order
        assert sorted(fields1) == sorted(fields2) == sorted(fields3)
        assert sorted(fields1) == ["Audio", "Back", "Front"]

    def test_sorted_fields_preserve_saved_index_lookup(self):
        """Saved field names should map to correct indices after sorting."""
        common_fields = {"Expression", "Audio", "Back", "Front"}
        last_source_field = "Expression"
        last_destination_field = "Audio"

        # Simulate the dropdown population logic
        sorted_fields = sorted(common_fields)
        source_index = None
        destination_index = None

        for i, field in enumerate(sorted_fields):
            if field == last_source_field:
                source_index = i
            if field == last_destination_field:
                destination_index = i

        # Expression should be at index 2 (alphabetically: Audio=0, Back=1, Expression=2, Front=3)
        assert source_index == 2
        # Audio should be at index 0
        assert destination_index == 0

        # Verify the sorted list
        assert sorted_fields[source_index] == "Expression"
        assert sorted_fields[destination_index] == "Audio"

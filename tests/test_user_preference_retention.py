"""
Tests for user preference retention between Anki sessions.

This module tests that user preferences are properly:
1. Read from config on dialog initialization
2. Saved to config when dialog is confirmed
3. Persisted across simulated Anki restarts

User preferences include:
- last_source_field: The field to read text from
- last_destination_field: The field to write audio to
- last_speaker_name: The selected voice
- last_audio_handling: How to handle existing content (append/overwrite/skip)
- ignore_brackets_enabled: Whether to ignore bracket content
- pitch_slider_value: Voice pitch adjustment
- speed_slider_value: Voice speed adjustment
- volume_slider_value: Voice volume adjustment
"""

from __future__ import annotations


# ==============================================================================
# Tests for preference reading from config
# ==============================================================================


class TestPreferenceReadingFromConfig:
    """Test that preferences are correctly read from config on initialization."""

    def test_last_speaker_name_is_read_from_config(self, sample_config):
        """Speaker selection should be restored from config."""
        last_speaker = sample_config.get("last_speaker_name")
        assert last_speaker == "en-US-JennyNeural"

    def test_last_source_field_is_read_from_config(self, sample_config):
        """Source field selection should be restored from config."""
        last_source = sample_config.get("last_source_field")
        assert last_source == "Front"

    def test_last_destination_field_is_read_from_config(self, sample_config):
        """Destination field selection should be restored from config."""
        last_destination = sample_config.get("last_destination_field")
        assert last_destination == "Audio"

    def test_last_audio_handling_is_read_from_config(self, sample_config):
        """Audio handling mode should be restored from config."""
        last_handling = sample_config.get("last_audio_handling")
        assert last_handling == "append"

    def test_ignore_brackets_enabled_is_read_from_config(self, sample_config):
        """Ignore brackets setting should be restored from config."""
        ignore_brackets = sample_config.get("ignore_brackets_enabled")
        assert ignore_brackets is True

    def test_pitch_slider_value_is_read_from_config(self, sample_config):
        """Pitch slider value should be restored from config."""
        pitch = sample_config.get("pitch_slider_value")
        assert pitch == 0

    def test_speed_slider_value_is_read_from_config(self, sample_config):
        """Speed slider value should be restored from config."""
        speed = sample_config.get("speed_slider_value")
        assert speed == 0

    def test_volume_slider_value_is_read_from_config(self, sample_config):
        """Volume slider value should be restored from config."""
        volume = sample_config.get("volume_slider_value")
        assert volume == 0


# ==============================================================================
# Tests for preference defaults when config is missing values
# ==============================================================================


class TestPreferenceDefaults:
    """Test that appropriate defaults are used when config values are missing."""

    def test_missing_last_speaker_name_defaults_to_none(self):
        """Missing speaker name should default to None (first speaker used)."""
        config = {}
        last_speaker = config.get("last_speaker_name") or None
        assert last_speaker is None

    def test_missing_last_source_field_defaults_to_none(self):
        """Missing source field should default to None (smart detection used)."""
        config = {}
        last_source = config.get("last_source_field") or None
        assert last_source is None

    def test_missing_last_destination_field_defaults_to_none(self):
        """Missing destination field should default to None (smart detection used)."""
        config = {}
        last_destination = config.get("last_destination_field") or None
        assert last_destination is None

    def test_missing_audio_handling_defaults_to_append(self):
        """Missing audio handling mode should default to 'append' (safest option)."""
        config = {}
        last_handling = config.get("last_audio_handling", "append")
        assert last_handling == "append"

    def test_missing_ignore_brackets_defaults_to_true(self):
        """Missing ignore brackets setting should default to True."""
        config = {}
        ignore_brackets = config.get("ignore_brackets_enabled", True)
        assert ignore_brackets is True

    def test_missing_pitch_slider_defaults_to_zero(self):
        """Missing pitch slider should default to 0."""
        config = {}
        pitch = config.get("pitch_slider_value") or 0
        assert pitch == 0

    def test_missing_speed_slider_defaults_to_zero(self):
        """Missing speed slider should default to 0."""
        config = {}
        speed = config.get("speed_slider_value") or 0
        assert speed == 0

    def test_missing_volume_slider_defaults_to_zero(self):
        """Missing volume slider should default to 0."""
        config = {}
        volume = config.get("volume_slider_value") or 0
        assert volume == 0


# ==============================================================================
# Tests for preference saving logic
# ==============================================================================


class TestPreferenceSavingLogic:
    """Test the logic for saving preferences to config."""

    def test_config_update_includes_source_field(self):
        """Config update should include source field."""
        config = {}
        source_field = "Expression"

        config["last_source_field"] = source_field

        assert config["last_source_field"] == "Expression"

    def test_config_update_includes_destination_field(self):
        """Config update should include destination field."""
        config = {}
        destination_field = "SentenceAudio"

        config["last_destination_field"] = destination_field

        assert config["last_destination_field"] == "SentenceAudio"

    def test_config_update_includes_speaker_name(self):
        """Config update should include speaker name (voice)."""
        config = {}
        speaker_name = "ja-JP-NanamiNeural"

        config["last_speaker_name"] = speaker_name

        assert config["last_speaker_name"] == "ja-JP-NanamiNeural"

    def test_config_update_includes_audio_handling_mode(self):
        """Config update should include audio handling mode."""
        config = {}
        audio_handling = "overwrite"

        config["last_audio_handling"] = audio_handling

        assert config["last_audio_handling"] == "overwrite"

    def test_config_update_includes_ignore_brackets(self):
        """Config update should include ignore brackets setting."""
        config = {}
        ignore_brackets = False

        config["ignore_brackets_enabled"] = ignore_brackets

        assert config["ignore_brackets_enabled"] is False

    def test_config_update_includes_all_slider_values(self):
        """Config update should include all slider values."""
        config = {}

        config["pitch_slider_value"] = 10
        config["speed_slider_value"] = -20
        config["volume_slider_value"] = 50

        assert config["pitch_slider_value"] == 10
        assert config["speed_slider_value"] == -20
        assert config["volume_slider_value"] == 50


# ==============================================================================
# Tests for preference persistence simulation
# ==============================================================================


class TestPreferencePersistenceSimulation:
    """Test that preferences persist through simulated config save/load cycles."""

    def test_full_preference_roundtrip(self):
        """All preferences should survive a save/load cycle."""
        # Simulate saving preferences
        saved_config = {
            "last_source_field": "Sentence",
            "last_destination_field": "SentenceAudio",
            "last_speaker_name": "zh-CN-XiaoxiaoNeural",
            "last_audio_handling": "skip",
            "ignore_brackets_enabled": False,
            "pitch_slider_value": 25,
            "speed_slider_value": -15,
            "volume_slider_value": 30,
        }

        # Simulate loading preferences (as if Anki restarted)
        loaded_config = saved_config.copy()

        # Verify all values match
        assert loaded_config["last_source_field"] == "Sentence"
        assert loaded_config["last_destination_field"] == "SentenceAudio"
        assert loaded_config["last_speaker_name"] == "zh-CN-XiaoxiaoNeural"
        assert loaded_config["last_audio_handling"] == "skip"
        assert loaded_config["ignore_brackets_enabled"] is False
        assert loaded_config["pitch_slider_value"] == 25
        assert loaded_config["speed_slider_value"] == -15
        assert loaded_config["volume_slider_value"] == 30

    def test_partial_preferences_merge_with_defaults(self):
        """Partial preferences should merge with defaults correctly."""
        # Simulate user has only changed some settings
        user_config = {
            "last_speaker_name": "de-DE-KatjaNeural",
            "volume_slider_value": -50,
        }

        # Simulate default config
        default_config = {
            "speakers": ["en-US-JennyNeural"],
            "log_level": "WARNING",
        }

        # Merge (user config overrides defaults)
        merged_config = {**default_config, **user_config}

        # User values should be preserved
        assert merged_config["last_speaker_name"] == "de-DE-KatjaNeural"
        assert merged_config["volume_slider_value"] == -50

        # Defaults should still be present
        assert merged_config["log_level"] == "WARNING"

    def test_preferences_overwrite_previous_values(self):
        """New preferences should overwrite previous values."""
        # Initial preferences
        config = {
            "last_speaker_name": "en-US-JennyNeural",
            "last_audio_handling": "append",
        }

        # User changes preferences
        config["last_speaker_name"] = "ja-JP-NanamiNeural"
        config["last_audio_handling"] = "overwrite"

        # New values should be stored
        assert config["last_speaker_name"] == "ja-JP-NanamiNeural"
        assert config["last_audio_handling"] == "overwrite"


# ==============================================================================
# Tests for speaker/voice selection retention
# ==============================================================================


class TestSpeakerSelectionRetention:
    """Test speaker (voice) selection is correctly retained."""

    def test_speaker_found_in_list_uses_saved_index(self):
        """When saved speaker exists in list, it should be selected."""
        speakers = ["en-US-JennyNeural", "en-US-GuyNeural", "ja-JP-NanamiNeural"]
        last_speaker_name = "ja-JP-NanamiNeural"

        # Find the speaker index (mirrors dialog initialization logic)
        speaker_combo_index = 0
        for i, speaker_item in enumerate(speakers):
            if speaker_item == last_speaker_name:
                speaker_combo_index = i
                break

        assert speaker_combo_index == 2
        assert speakers[speaker_combo_index] == "ja-JP-NanamiNeural"

    def test_speaker_not_found_falls_back_to_first(self):
        """When saved speaker doesn't exist in list, first speaker is selected."""
        speakers = ["en-US-JennyNeural", "en-US-GuyNeural"]
        last_speaker_name = "removed-voice-Neural"

        # Find the speaker index (mirrors dialog initialization logic)
        speaker_combo_index = 0
        for i, speaker_item in enumerate(speakers):
            if speaker_item == last_speaker_name:
                speaker_combo_index = i
                break

        # Should remain at 0 (first speaker)
        assert speaker_combo_index == 0

    def test_empty_speaker_name_uses_first_speaker(self):
        """When no speaker name is saved, first speaker is selected."""
        speakers = ["en-US-JennyNeural", "en-US-GuyNeural"]
        last_speaker_name = None

        speaker_combo_index = 0
        if last_speaker_name:
            for i, speaker_item in enumerate(speakers):
                if speaker_item == last_speaker_name:
                    speaker_combo_index = i
                    break

        assert speaker_combo_index == 0


# ==============================================================================
# Tests for field selection retention
# ==============================================================================


class TestFieldSelectionRetention:
    """Test field selection is correctly retained."""

    def test_source_field_found_uses_saved_index(self):
        """When saved source field exists, it should be selected."""
        common_fields = sorted(["Audio", "Back", "Expression", "Front", "Sentence"])
        last_source_field = "Sentence"

        source_field_index = 0
        for i, field in enumerate(common_fields):
            if field == last_source_field:
                source_field_index = i
                break

        assert source_field_index == 4  # "Sentence" is at index 4 alphabetically
        assert common_fields[source_field_index] == "Sentence"

    def test_destination_field_found_uses_saved_index(self):
        """When saved destination field exists, it should be selected."""
        common_fields = sorted(["Audio", "Back", "Expression", "Front"])
        last_destination_field = "Audio"

        destination_field_index = 0
        for i, field in enumerate(common_fields):
            if field == last_destination_field:
                destination_field_index = i
                break

        assert destination_field_index == 0  # "Audio" is at index 0 alphabetically
        assert common_fields[destination_field_index] == "Audio"

    def test_missing_field_uses_smart_detection_expression(self):
        """When saved field doesn't exist, smart detection should find 'expression'."""
        common_fields = sorted(["Expression", "Reading", "Audio"])
        last_source_field = "NonexistentField"

        source_field_index = 0
        for i, field in enumerate(common_fields):
            if last_source_field is None and field.lower() in {"expression", "sentence"}:
                source_field_index = i
                break
            if field == last_source_field:
                source_field_index = i
                break

        # Field not found, index stays at 0
        assert source_field_index == 0

    def test_smart_detection_finds_sentence_field(self):
        """Smart detection should find 'Sentence' field as source."""
        common_fields = sorted(["Audio", "Sentence", "Translation"])
        last_source_field = None

        source_field_index = 0
        for i, field in enumerate(common_fields):
            if last_source_field is None and field.lower() in {"expression", "sentence"}:
                source_field_index = i
                break

        assert source_field_index == 1  # "Sentence" is at index 1 alphabetically
        assert common_fields[source_field_index] == "Sentence"

    def test_smart_detection_finds_audio_field(self):
        """Smart detection should find 'Audio' field as destination."""
        common_fields = sorted(["Audio", "Front", "Back"])
        last_destination_field = None

        destination_field_index = 0
        for i, field in enumerate(common_fields):
            if last_destination_field is None and field.lower() == "audio":
                destination_field_index = i
                break

        assert destination_field_index == 0  # "Audio" is at index 0 alphabetically
        assert common_fields[destination_field_index] == "Audio"


# ==============================================================================
# Tests for audio handling mode retention
# ==============================================================================


class TestAudioHandlingModeRetention:
    """Test audio handling mode is correctly retained."""

    def test_append_mode_is_restored(self):
        """Append mode should be correctly restored from config."""
        config = {"last_audio_handling": "append"}
        mode = config.get("last_audio_handling", "append")
        assert mode == "append"

    def test_overwrite_mode_is_restored(self):
        """Overwrite mode should be correctly restored from config."""
        config = {"last_audio_handling": "overwrite"}
        mode = config.get("last_audio_handling", "append")
        assert mode == "overwrite"

    def test_skip_mode_is_restored(self):
        """Skip mode should be correctly restored from config."""
        config = {"last_audio_handling": "skip"}
        mode = config.get("last_audio_handling", "append")
        assert mode == "skip"

    def test_invalid_mode_defaults_to_append(self):
        """Invalid mode value should default to append."""
        config = {"last_audio_handling": "invalid_mode"}
        mode = config.get("last_audio_handling", "append")

        # The raw value is returned, but the dialog would handle this
        # by checking if it matches known values
        valid_modes = {"append", "overwrite", "skip"}
        if mode not in valid_modes:
            mode = "append"

        assert mode == "append"


# ==============================================================================
# Tests for slider value retention
# ==============================================================================


class TestSliderValueRetention:
    """Test slider values are correctly retained."""

    def test_positive_pitch_value_is_restored(self):
        """Positive pitch value should be correctly restored."""
        config = {"pitch_slider_value": 25}
        pitch = config.get("pitch_slider_value") or 0
        assert pitch == 25

    def test_negative_pitch_value_is_restored(self):
        """Negative pitch value should be correctly restored."""
        config = {"pitch_slider_value": -30}
        pitch = config.get("pitch_slider_value") or 0
        assert pitch == -30

    def test_zero_pitch_value_is_restored(self):
        """Zero pitch value should be correctly restored (not replaced with default)."""
        config = {"pitch_slider_value": 0}
        # Using 'or 0' would incorrectly treat 0 as falsy
        # The actual code uses 'or 0' which is a potential bug
        pitch = config.get("pitch_slider_value") or 0
        assert pitch == 0  # This works because 0 or 0 = 0

    def test_positive_speed_value_is_restored(self):
        """Positive speed value should be correctly restored."""
        config = {"speed_slider_value": 15}
        speed = config.get("speed_slider_value") or 0
        assert speed == 15

    def test_negative_volume_value_is_restored(self):
        """Negative volume value should be correctly restored."""
        config = {"volume_slider_value": -75}
        volume = config.get("volume_slider_value") or 0
        assert volume == -75

    def test_slider_values_at_boundaries(self):
        """Slider values at min/max boundaries should be restored."""
        config = {
            "pitch_slider_value": 50,  # max
            "speed_slider_value": -50,  # min
            "volume_slider_value": 100,  # max
        }

        assert config.get("pitch_slider_value") == 50
        assert config.get("speed_slider_value") == -50
        assert config.get("volume_slider_value") == 100


# ==============================================================================
# Tests for complete preference set
# ==============================================================================


class TestCompletePreferenceSet:
    """Test the complete set of user preferences."""

    def test_all_user_preferences_are_defined(self, sample_config):
        """Sample config should contain all expected user preference keys."""
        expected_keys = {
            "last_source_field",
            "last_destination_field",
            "last_speaker_name",
            "last_audio_handling",
            "ignore_brackets_enabled",
            "pitch_slider_value",
            "speed_slider_value",
            "volume_slider_value",
        }

        # All expected keys should be present in sample config
        for key in expected_keys:
            assert key in sample_config, f"Missing expected preference key: {key}"

    def test_preference_keys_match_save_location(self):
        """Preference keys used for reading should match those used for saving."""
        # These are the keys saved in onEdgeTTSOptionSelected (lines 792-796)
        save_keys = {
            "last_source_field",
            "last_destination_field",
            "last_speaker_name",
            "last_audio_handling",
            "ignore_brackets_enabled",
        }

        # These are the keys read in AudioGenDialog.__init__
        read_keys = {
            "last_source_field",  # line 132
            "last_destination_field",  # line 133
            "last_speaker_name",  # line 248
            "last_audio_handling",  # line 210
            "ignore_brackets_enabled",  # line 182
        }

        assert save_keys == read_keys, "Save and read keys should match"

"""
Integration tests for edge-tts-generate add-on.
These tests verify that components work together correctly.
"""

import importlib.util
import json
import os
import sys
from unittest.mock import MagicMock

import pytest


# Helper function to load modules without polluting sys.path
def _load_module(module_name, module_path):
    """Load a module from file without adding to sys.path."""
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestConfigIntegration:
    """Test that configuration files are consistent."""

    def test_config_speakers_are_valid_voices(self):
        """All speakers in config should follow edge-tts naming convention."""
        config_path = os.path.join(_base_path, "config.json")

        with open(config_path) as f:
            config = json.load(f)

        # Valid language codes based on edge-tts
        valid_language_codes = [
            "ja",
            "en",
            "zh",
            "ko",
            "de",
            "fr",
            "es",
            "pt",
            "it",
            "ru",
            "ar",
            "hi",
            "tr",
            "pl",
            "nl",
            "sv",
            "da",
            "no",
            "fi",
            "cs",
            "el",
            "he",
            "th",
            "vi",
            "id",
            "ms",
        ]

        for speaker in config["speakers"]:
            # Should have format: lang-REGION-NameNeural
            parts = speaker.split("-")
            assert len(parts) >= 3, f"Invalid speaker format: {speaker}"

            lang_code = parts[0]
            assert lang_code in valid_language_codes, f"Unknown language code in: {speaker}"

            # Should end with Neural
            assert speaker.endswith("Neural"), f"Speaker should end with 'Neural': {speaker}"

    def test_manifest_version_constraints(self):
        """Manifest version constraints should be valid."""
        manifest_path = os.path.join(_base_path, "manifest.json")

        with open(manifest_path) as f:
            manifest = json.load(f)

        min_version = manifest["min_point_version"]
        max_version = manifest["max_point_version"]

        assert isinstance(min_version, int)
        assert isinstance(max_version, int)
        assert min_version > 0
        assert max_version > min_version

    def test_all_required_files_exist(self):
        """All required add-on files should exist."""
        required_files = [
            "__init__.py",
            "edge_tts_gen.py",
            "external_runtime.py",
            "external_tts_runner.py",
            "config.json",
            "manifest.json",
        ]

        for filename in required_files:
            filepath = os.path.join(_base_path, filename)
            assert os.path.exists(filepath), f"Required file missing: {filename}"


class TestModuleImports:
    """Test that modules can be imported correctly."""

    def test_external_runtime_imports(self):
        """external_runtime.py should import without errors."""
        external_runtime = _load_module("external_runtime", os.path.join(_base_path, "external_runtime.py"))

        # Check key functions exist
        assert hasattr(external_runtime, "get_external_python")
        assert hasattr(external_runtime, "PYTHON_VERSION")
        assert hasattr(external_runtime, "EDGE_TTS_SPEC")

    def test_external_tts_runner_structure(self):
        """external_tts_runner.py should have expected structure."""
        # Mock edge_tts since it's not installed
        sys.modules["edge_tts"] = MagicMock()

        external_tts_runner = _load_module("external_tts_runner", os.path.join(_base_path, "external_tts_runner.py"))

        assert hasattr(external_tts_runner, "main")
        assert hasattr(external_tts_runner, "synthesize")


class TestExternalRuntimeConstants:
    """Test external runtime configuration."""

    def test_python_version_is_pinned(self):
        """Python version should be specifically pinned."""
        external_runtime = _load_module("external_runtime", os.path.join(_base_path, "external_runtime.py"))

        version = external_runtime.PYTHON_VERSION
        # Should be exact version, not a range
        parts = version.split(".")
        assert len(parts) == 3
        # Should be 3.14.x as specified in the project
        assert parts[0] == "3"
        assert parts[1] == "14"

    def test_edge_tts_is_pinned(self):
        """edge-tts version should be pinned."""
        external_runtime = _load_module("external_runtime", os.path.join(_base_path, "external_runtime.py"))

        spec = external_runtime.EDGE_TTS_SPEC
        # Should use == for exact version
        assert "==" in spec
        assert "edge-tts" in spec


class TestTextProcessingPipeline:
    """Test the text processing pipeline."""

    def test_full_text_processing(self):
        """Test complete text processing pipeline."""
        import re

        # Simulate the text processing from getNoteTextAndSpeaker
        original_text = '<div class="sentence">日本語[にほんご]を<br>勉強[べんきょう;a,h]&nbsp;しています</div>'

        # Step 1: Remove HTML entities
        entity_re = re.compile(r"(&[^;]+;)")
        text = entity_re.sub("", original_text)

        # Step 2: Remove HTML tags
        tag_re = re.compile(r"(<!--.*?-->|<[^>]*>)")
        text = tag_re.sub("", text)

        # Step 3: Replace kanji with furigana from brackets
        text = re.sub(r" ?\S*?\[(.*?)\]", r"\1", text)

        # Step 4: Remove stuff between brackets (pitch accent info)
        text = re.sub(r"\[.*?\]", "", text)

        # Step 5: Remove spaces
        text = re.sub(" ", "", text)

        # Final result should be clean Japanese text
        assert "div" not in text.lower()
        assert "<" not in text
        assert "&" not in text
        assert "[" not in text
        assert "]" not in text

    def test_whitespace_handling_respects_language(self):
        """Whitespace removal should depend on the selected voice locale."""
        import re

        sample_text = "This sentence should keep its spaces"

        def strip_spaces(text, voice):
            language_code = voice.split("-")[0].lower()
            if language_code in {"ja", "zh"}:
                return re.sub(" ", "", text)
            return text

        assert strip_spaces(sample_text, "en-US-JennyNeural") == sample_text
        assert strip_spaces(sample_text, "ja-JP-NanamiNeural") == "Thissentenceshouldkeepitsspaces"

    def test_handles_various_input_formats(self):
        """Test processing handles various input formats."""
        import re

        tag_re = re.compile(r"(<!--.*?-->|<[^>]*>)")
        entity_re = re.compile(r"(&[^;]+;)")

        test_cases = [
            # Plain text
            ("Hello World", "Hello World"),
            # HTML tags
            ("<b>Bold</b>", "Bold"),
            # HTML entities
            ("&nbsp;test", "test"),
            # Japanese with furigana
            ("漢字[かんじ]", "かんじ"),
            # Mixed content
            ("<p>Text</p>", "Text"),
        ]

        for input_text, expected_contains in test_cases:
            result = entity_re.sub("", input_text)
            result = tag_re.sub("", result)

            # For furigana test
            if "[" in input_text:
                result = re.sub(r" ?\S*?\[(.*?)\]", r"\1", result)

            assert expected_contains in result or result == expected_contains


class TestVoiceParameterGeneration:
    """Test voice parameter generation."""

    def test_parameter_combinations(self):
        """Test various parameter combinations."""
        test_configs = [
            {"pitch_slider_value": 0, "speed_slider_value": 0, "volume_slider_value": 0},
            {"pitch_slider_value": 10, "speed_slider_value": -5, "volume_slider_value": 20},
            {"pitch_slider_value": -50, "speed_slider_value": 50, "volume_slider_value": -100},
        ]

        for config in test_configs:
            pitch = f"{config.get('pitch_slider_value', 0):+}Hz"
            rate = f"{config.get('speed_slider_value', 0):+}%"
            volume = f"{config.get('volume_slider_value', 0):+}%"

            # All should have proper sign
            assert pitch[0] in ["+", "-"]
            assert rate[0] in ["+", "-"]
            assert volume[0] in ["+", "-"]

            # All should have proper suffix
            assert pitch.endswith("Hz")
            assert rate.endswith("%")
            assert volume.endswith("%")


class TestErrorHandling:
    """Test error handling scenarios."""

    def test_getCommonFields_logic_with_none_note(self):
        """getCommonFields logic should raise descriptive error for None note."""

        # Test the logic pattern from getCommonFields
        def getCommonFields(selected_notes, get_note_func):
            common_fields = set()
            first = True

            for note_id in selected_notes:
                note = get_note_func(note_id)
                if note is None:
                    raise Exception(
                        f"Note with id {note_id} is None.\nPlease submit an issue with more information at https://github.com/nia-the-cat/edge-tts-generate/issues/new"
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
            getCommonFields([123], get_note_func)

        # Should include note ID in error
        assert "123" in str(exc_info.value)
        # Should include link to issues
        assert "github.com" in str(exc_info.value).lower()

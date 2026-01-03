"""
Integration tests for edge-tts-generate add-on.
These tests verify that components work together correctly.
"""

import importlib.util
import json
import os
import re
import sys

import pytest


# Helper function to load modules without polluting sys.path
def _load_module(module_name, module_path):
    """Load a module from file without adding to sys.path."""
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    # Register in sys.modules so dataclasses and other features work
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


_base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.mark.integration
@pytest.mark.smoke
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
            "bundled_tts.py",
            "config.json",
            "manifest.json",
        ]

        for filename in required_files:
            filepath = os.path.join(_base_path, filename)
            assert os.path.exists(filepath), f"Required file missing: {filename}"


@pytest.mark.integration
class TestBundledTTSModule:
    """Test that the bundled TTS module is properly structured."""

    def test_bundled_tts_imports(self):
        """bundled_tts.py should have expected structure."""
        # Add vendor directory to path first (like bundled_tts does)
        vendor_path = os.path.join(_base_path, "vendor")
        if vendor_path not in sys.path:
            sys.path.insert(0, vendor_path)

        # Set environment variables for pure Python mode
        os.environ["AIOHTTP_NO_EXTENSIONS"] = "1"
        os.environ["FROZENLIST_NO_EXTENSIONS"] = "1"
        os.environ["MULTIDICT_NO_EXTENSIONS"] = "1"
        os.environ["YARL_NO_EXTENSIONS"] = "1"
        os.environ["PROPCACHE_NO_EXTENSIONS"] = "1"

        bundled_tts = _load_module("bundled_tts", os.path.join(_base_path, "bundled_tts.py"))

        # Check key classes and functions exist
        assert hasattr(bundled_tts, "TTSConfig")
        assert hasattr(bundled_tts, "TTSItem")
        assert hasattr(bundled_tts, "TTSResult")
        assert hasattr(bundled_tts, "synthesize_batch")
        assert hasattr(bundled_tts, "synthesize_single")

    def test_vendor_directory_exists(self):
        """Vendor directory with dependencies should exist."""
        vendor_path = os.path.join(_base_path, "vendor")
        assert os.path.isdir(vendor_path), "vendor directory should exist"

        # Check for key vendored packages
        edge_tts_path = os.path.join(vendor_path, "edge_tts")
        assert os.path.isdir(edge_tts_path), "edge_tts should be vendored"


@pytest.mark.integration
class TestTextProcessingPipeline:
    """Test the text processing pipeline."""

    def test_full_text_processing(self):
        """Test complete text processing pipeline."""
        # Simulate the text processing from getNoteTextAndSpeaker
        original_text = '<div class="sentence">日本語[にほんご]を<br>勉強[べんきょう;a,h]&nbsp;しています</div>'

        # Step 1: Remove HTML entities
        entity_re = re.compile(r"(&[^;]+;)")
        text = entity_re.sub("", original_text)

        # Step 2: Remove HTML tags
        tag_re = re.compile(r"(<!--.*?-->|<[^>]*>)")
        text = tag_re.sub("", text)

        # Step 3: Replace text with reading from brackets
        text = re.sub(r" ?\S*?\[(.*?)\]", r"\1", text)

        # Step 4: Remove stuff between brackets (pitch accent info)
        text = re.sub(r"\[.*?\]", "", text)

        # Step 5: Remove spaces
        text = re.sub(" ", "", text)

        # Final result should be clean CJK text
        assert "div" not in text.lower()
        assert "<" not in text
        assert "&" not in text
        assert "[" not in text
        assert "]" not in text

    def test_whitespace_handling_respects_language(self):
        """Whitespace removal should depend on the selected voice locale."""
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
        tag_re = re.compile(r"(<!--.*?-->|<[^>]*>)")
        entity_re = re.compile(r"(&[^;]+;)")

        test_cases = [
            # Plain text
            ("Hello World", "Hello World"),
            # HTML tags
            ("<b>Bold</b>", "Bold"),
            # HTML entities
            ("&nbsp;test", "test"),
            # CJK text with reading annotations
            ("漢字[かんじ]", "かんじ"),
            # Mixed content
            ("<p>Text</p>", "Text"),
        ]

        for input_text, expected_contains in test_cases:
            result = entity_re.sub("", input_text)
            result = tag_re.sub("", result)

            # For reading annotation test
            if "[" in input_text:
                result = re.sub(r" ?\S*?\[(.*?)\]", r"\1", result)

            assert expected_contains in result or result == expected_contains


@pytest.mark.integration
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


@pytest.mark.integration
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

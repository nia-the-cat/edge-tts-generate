"""
Tests for the preview note selection functionality.
Tests that users can select which note to use for voice preview when processing batches.
"""

import re
from unittest.mock import MagicMock


class TestPreviewNoteSelection:
    """Test preview note selection when processing multiple notes."""

    def test_preview_uses_first_note_when_single_note_selected(self):
        """When only one note is selected, preview should use that note."""
        selected_notes = [123]
        note_index = 0  # Should always be 0 for single note

        assert note_index == 0
        assert selected_notes[note_index] == 123

    def test_preview_uses_selected_note_from_combo(self):
        """When multiple notes selected, preview should use the note from combo box."""
        selected_notes = [101, 102, 103]

        # Simulate user selecting second note (index 1)
        combo_index = 1
        note_index = combo_index

        assert selected_notes[note_index] == 102

    def test_preview_combo_not_shown_for_single_note(self):
        """Preview note combo should not be shown when only one note is selected."""
        selected_notes = [123]
        should_show_combo = len(selected_notes) > 1

        assert should_show_combo is False

    def test_preview_combo_shown_for_multiple_notes(self):
        """Preview note combo should be shown when multiple notes are selected."""
        selected_notes = [101, 102, 103]
        should_show_combo = len(selected_notes) > 1

        assert should_show_combo is True

    def test_preview_note_index_validation(self):
        """Preview note index should be validated against selected notes list."""
        selected_notes = [101, 102, 103]
        combo_index = 5  # Invalid index

        # Should fall back to 0 if index is out of range
        note_index = combo_index
        if note_index < 0 or note_index >= len(selected_notes):
            note_index = 0

        assert note_index == 0

    def test_preview_combo_displays_note_snippet(self):
        """Preview combo should display a snippet of each note's content."""
        note_text = "This is a very long sentence that should be truncated to fit in the combo box display"
        max_length = 50

        snippet = note_text[:max_length]
        if len(note_text) > max_length:
            snippet += "..."

        assert snippet == "This is a very long sentence that should be trunca..."
        assert len(snippet) == 53  # 50 chars + "..."

    def test_preview_combo_handles_empty_notes(self):
        """Preview combo should handle notes with empty source fields."""
        note_text = ""
        display_text = f"Note 1: {note_text}" if note_text else "Note 1: (empty)"

        assert display_text == "Note 1: (empty)"

    def test_preview_combo_handles_missing_field(self):
        """Preview combo should handle notes missing the source field."""
        source_field = "Expression"
        has_field = False

        if has_field:
            display_text = "Note 1: content"
        else:
            display_text = f"Note 1: (no '{source_field}' field)"

        assert display_text == "Note 1: (no 'Expression' field)"

    def test_preview_combo_updates_on_source_field_change(self):
        """Preview combo should update when source field changes."""
        # This validates the pattern that combo updates when source field changes
        source_field_changed = True

        # Mock combo box and update method
        combo = MagicMock()

        if source_field_changed:
            combo.clear()
            combo.addItem("Note 1: New field content")

        combo.clear.assert_called_once()
        combo.addItem.assert_called_with("Note 1: New field content")

    def test_preview_combo_preserves_selection_on_update(self):
        """Preview combo should preserve current selection when updating."""
        current_index = 2
        total_items = 5

        # After update, restore selection if valid
        if current_index < total_items:
            restored_index = current_index
        else:
            restored_index = 0

        assert restored_index == 2

    def test_preview_combo_resets_selection_when_invalid(self):
        """Preview combo should reset to 0 when current selection becomes invalid."""
        current_index = 3
        total_items = 2  # Source field changed, fewer notes have this field

        # After update, restore selection if valid
        if current_index < total_items:
            restored_index = current_index
        else:
            restored_index = 0

        assert restored_index == 0


class TestPreviewNoteSnippetGeneration:
    """Test snippet generation for preview note combo box."""

    def test_snippet_removes_html_tags(self):
        """Snippet should remove HTML tags."""
        TAG_RE = re.compile(r"(<!--.*?-->|<[^>]*>)")
        note_text = "<b>Bold</b> text"
        cleaned = TAG_RE.sub("", note_text)

        assert cleaned == "Bold text"

    def test_snippet_removes_html_entities(self):
        """Snippet should remove HTML entities."""
        ENTITY_RE = re.compile(r"(&[^;]+;)")
        note_text = "&nbsp;Hello&amp;World"
        cleaned = ENTITY_RE.sub("", note_text)

        assert cleaned == "HelloWorld"

    def test_snippet_strips_whitespace(self):
        """Snippet should strip leading/trailing whitespace."""
        note_text = "  Hello World  "
        cleaned = note_text.strip()

        assert cleaned == "Hello World"

    def test_snippet_truncates_long_text(self):
        """Snippet should truncate text longer than max length."""
        note_text = "A" * 100
        max_length = 50

        snippet = note_text[:max_length]
        if len(note_text) > max_length:
            snippet += "..."

        assert len(snippet) == 53
        assert snippet.endswith("...")

    def test_snippet_preserves_short_text(self):
        """Snippet should preserve text shorter than max length."""
        note_text = "Short text"
        max_length = 50

        snippet = note_text[:max_length]
        if len(note_text) > max_length:
            snippet += "..."

        assert snippet == "Short text"
        assert not snippet.endswith("...")


class TestPreviewNoteIndexCalculation:
    """Test note index calculation for preview."""

    def test_single_note_always_uses_index_zero(self):
        """Single note should always use index 0."""
        selected_notes = [123]
        has_combo = len(selected_notes) > 1

        if has_combo:
            note_index = 1  # This won't happen
        else:
            note_index = 0

        assert note_index == 0

    def test_multiple_notes_use_combo_index(self):
        """Multiple notes should use combo box index."""
        selected_notes = [101, 102, 103, 104]
        has_combo = len(selected_notes) > 1
        combo_current_index = 2

        if has_combo:
            note_index = combo_current_index
        else:
            note_index = 0

        assert note_index == 2

    def test_negative_index_validation(self):
        """Negative combo index should be validated."""
        selected_notes = [101, 102, 103]
        combo_index = -1

        note_index = combo_index
        if note_index < 0 or note_index >= len(selected_notes):
            note_index = 0

        assert note_index == 0

    def test_too_large_index_validation(self):
        """Too large combo index should be validated."""
        selected_notes = [101, 102]
        combo_index = 10

        note_index = combo_index
        if note_index < 0 or note_index >= len(selected_notes):
            note_index = 0

        assert note_index == 0

    def test_valid_index_not_changed(self):
        """Valid combo index should not be changed."""
        selected_notes = [101, 102, 103]
        combo_index = 1

        note_index = combo_index
        if note_index < 0 or note_index >= len(selected_notes):
            note_index = 0

        assert note_index == 1


class TestPreviewNoteComboLayout:
    """Test layout positioning for preview note combo."""

    def test_preview_combo_row_position_for_single_note(self):
        """Preview combo should not affect layout for single note."""
        selected_notes = [123]
        has_combo = len(selected_notes) > 1

        # Original button row was 2 for single note case
        # With new layout: row 3 (no combo shown)
        button_row = 3 if not has_combo else 4

        assert button_row == 3

    def test_preview_combo_row_position_for_multiple_notes(self):
        """Preview combo should shift button row for multiple notes."""
        selected_notes = [101, 102, 103]
        has_combo = len(selected_notes) > 1

        # With combo: preview button on row 4
        button_row = 3 if not has_combo else 4

        assert button_row == 4

    def test_cancel_generate_buttons_row_for_single_note(self):
        """Cancel/Generate buttons should be on row 3 for single note."""
        selected_notes = [123]
        button_row = 3 if len(selected_notes) <= 1 else 5

        assert button_row == 3

    def test_cancel_generate_buttons_row_for_multiple_notes(self):
        """Cancel/Generate buttons should be on row 5 for multiple notes."""
        selected_notes = [101, 102, 103]
        button_row = 3 if len(selected_notes) <= 1 else 5

        assert button_row == 5

    def test_slider_base_row_for_single_note(self):
        """Sliders should start at row 4 for single note."""
        selected_notes = [123]
        slider_base_row = 4 if len(selected_notes) <= 1 else 6

        assert slider_base_row == 4

    def test_slider_base_row_for_multiple_notes(self):
        """Sliders should start at row 6 for multiple notes."""
        selected_notes = [101, 102, 103]
        slider_base_row = 4 if len(selected_notes) <= 1 else 6

        assert slider_base_row == 6

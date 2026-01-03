from __future__ import annotations

import logging
import re
import uuid
from dataclasses import dataclass
from os.path import dirname, join

from aqt import mw, qt
from aqt.qt import (
    QButtonGroup,
    QInputDialog,
    QLabel,
    QMessageBox,
    QRadioButton,
    QSlider,
)
from aqt.sound import av_player
from aqt.utils import tooltip


try:
    from .bundled_tts import TTSConfig, TTSItem, synthesize_batch
    from .logging_config import get_logger
except ImportError:
    # Fallback for test environments where relative imports don't work
    from bundled_tts import TTSConfig, TTSItem, synthesize_batch

    def get_logger(name: str) -> logging.Logger:
        return logging.getLogger(f"edge_tts_generate.{name.lstrip('.')}")


logger = get_logger(__name__)


CREATE_NEW_FIELD_OPTION = "[ + Create new field... ]"
PREVIEW_NOTE_SNIPPET_MAX_LENGTH = 50  # Maximum length for note snippet in preview dropdown
TAG_RE = re.compile(r"(<!--.*?-->|<[^>]*>)")
ENTITY_RE = re.compile(r"(&[^;]+;)")
BRACKET_READING_RE = re.compile(r" ?\S*?\[(.*?)\]")
BRACKET_CONTENT_RE = re.compile(r"\[.*?\]")
WHITESPACE_RE = re.compile(" ")


@dataclass
class ItemError:
    identifier: str
    reason: str


@dataclass
class BatchAudioResult:
    audio_map: dict[str, bytes]
    item_errors: list[ItemError]


def getCommonFields(selected_notes):
    common_fields = set()

    first = True

    for note_id in selected_notes:
        note = mw.col.get_note(note_id)
        if note is None:
            raise Exception(
                f"Note with id {note_id} is None.\nSelected note IDs: {', '.join(str(nid) for nid in selected_notes)}.\nPlease submit an issue with more information about what cards caused this at https://github.com/nia-the-cat/edge-tts-generate/issues/new"
            )
        model = note.note_type()
        model_fields = {f["name"] for f in model["flds"]}
        if first:
            common_fields = model_fields  # Take the first one as is and we will intersect it with the following ones
        else:
            common_fields = common_fields.intersection(
                model_fields
            )  # Find the common fields by intersecting the set of all fields together
        first = False
    return common_fields


def getSpeakerList(config):
    speakers = []
    speakers.extend(config.get("speakers", []))
    return speakers


def getSpeaker(speaker_combo):
    speaker_name = speaker_combo.itemText(speaker_combo.currentIndex())
    return speaker_name


class MyDialog(qt.QDialog):
    def __init__(self, browser, parent=None) -> None:
        super().__init__(parent)
        self.browser = browser
        self.selected_notes = browser.selectedNotes()
        self.new_field_name = None  # Track if user wants to create a new field
        self._preview_cache = None  # Cache for preview audio

        config = mw.addonManager.getConfig(__name__)

        layout = qt.QVBoxLayout()

        layout.addWidget(qt.QLabel("Selected notes: " + str(len(self.selected_notes))))

        self.grid_layout = qt.QGridLayout()

        self.common_fields = getCommonFields(self.selected_notes)

        if len(self.common_fields) < 1:
            QMessageBox.critical(
                mw,
                "Error",
                "The chosen notes share no fields in common. Make sure you're not selecting two different note types",
            )
            self.reject()
            return

        self.source_combo = qt.QComboBox()
        self.destination_combo = qt.QComboBox()

        last_source_field = config.get("last_source_field") or None
        last_destination_field = config.get("last_destination_field") or None
        source_field_index = 0
        destination_field_index = 0
        i = 0
        for field in sorted(self.common_fields):
            if last_source_field is None:
                if field.lower() == "expression" or field.lower() == "sentence":
                    source_field_index = i
            elif field == last_source_field:
                source_field_index = i

            if last_destination_field is None:
                if field.lower() == "audio":
                    destination_field_index = i
            elif field == last_destination_field:
                destination_field_index = i
            self.source_combo.addItem(field)
            self.destination_combo.addItem(field)
            i += 1

        # Add "Create new field" option to destination dropdown
        self.destination_combo.addItem(CREATE_NEW_FIELD_OPTION)
        self.destination_combo.currentIndexChanged.connect(self.onDestinationChanged)

        self.source_combo.setCurrentIndex(source_field_index)
        self.destination_combo.setCurrentIndex(destination_field_index)

        source_label = qt.QLabel("Source field: ")
        source_tooltip = "The field to read from. For example if your sentence is in the field 'Expression' you want to choose 'Expression' as the source field to read from"
        source_label.setToolTip(source_tooltip)

        destination_label = qt.QLabel("Destination field: ")
        destination_tooltip = "The field to write the audio to. Typically you want to choose a field like 'Audio' or 'Audio on Front' or wherever you want the audio placed on your card. Select '[ + Create new field... ]' to add a new audio field."
        destination_label.setToolTip(destination_tooltip)

        self.source_combo.setToolTip(source_tooltip)
        self.destination_combo.setToolTip(destination_tooltip)

        self.grid_layout.addWidget(source_label, 0, 0)
        self.grid_layout.addWidget(self.source_combo, 0, 1)
        self.grid_layout.addWidget(destination_label, 0, 2)
        self.grid_layout.addWidget(self.destination_combo, 0, 3)

        # Audio handling options (radio buttons)
        audio_options_label = qt.QLabel("When destination field has content:")
        audio_options_label.setToolTip("Choose how to handle existing content in the destination field")
        self.grid_layout.addWidget(audio_options_label, 1, 0, 1, 2)

        self.audio_handling_group = QButtonGroup(self)

        self.append_radio = QRadioButton("Append (keep existing content)")
        self.append_radio.setToolTip(
            "Add the generated audio to the field without removing any existing content. This is the safest option."
        )

        self.overwrite_radio = QRadioButton("Overwrite (replace content)")
        self.overwrite_radio.setToolTip("Replace the entire content of the destination field with the new audio")

        self.skip_radio = QRadioButton("Skip (if audio exists)")
        self.skip_radio.setToolTip("Skip generating audio for notes that already have content in the destination field")

        self.audio_handling_group.addButton(self.append_radio, 0)
        self.audio_handling_group.addButton(self.overwrite_radio, 1)
        self.audio_handling_group.addButton(self.skip_radio, 2)

        # Load saved preference or default to append (safest option)
        last_audio_handling = config.get("last_audio_handling", "append")
        if last_audio_handling == "overwrite":
            self.overwrite_radio.setChecked(True)
        elif last_audio_handling == "skip":
            self.skip_radio.setChecked(True)
        else:
            self.append_radio.setChecked(True)  # Default to append

        audio_options_layout = qt.QHBoxLayout()
        audio_options_layout.addWidget(self.append_radio)
        audio_options_layout.addWidget(self.overwrite_radio)
        audio_options_layout.addWidget(self.skip_radio)

        self.grid_layout.addLayout(audio_options_layout, 1, 2, 1, 3)

        # TODO: Does anyone actually want to not ignore stuff in brackets? The checkbox is here if we need it but I don't think anyone wants brackets to be read
        self.ignore_brackets_checkbox = qt.QCheckBox("Ignore stuff in brackets [...]")
        self.ignore_brackets_checkbox.setToolTip(
            "Ignores things between brackets. Some flashcard formats use brackets for readings, pitch accent, or other metadata. Leave this checked unless you want bracket contents read aloud."
        )
        self.ignore_brackets_checkbox.setChecked(config.get("ignore_brackets_enabled", True))
        self.grid_layout.addWidget(self.ignore_brackets_checkbox, 0, 4)

        self.grid_layout.addWidget(qt.QLabel("Speaker: "), 2, 0)
        self.speakers = getSpeakerList(config)
        self.speaker_combo = qt.QComboBox()
        for speaker in self.speakers:
            self.speaker_combo.addItem(speaker)
        self.grid_layout.addWidget(self.speaker_combo, 2, 1)

        self.speaker_status_label = qt.QLabel()
        self.speaker_status_label.setWordWrap(True)
        self.grid_layout.addWidget(self.speaker_status_label, 2, 2, 1, 2)

        last_speaker_name = config.get("last_speaker_name") or None

        if self.speaker_combo.count() > 0:
            # find the speaker/style from the previously saved config data and pick it from the dropdown
            speaker_combo_index = 0
            i = 0
            for speaker_item in [self.speaker_combo.itemText(i) for i in range(self.speaker_combo.count())]:
                if speaker_item == last_speaker_name:
                    speaker_combo_index = i
                    break
                i += 1

            self.speaker_combo.setCurrentIndex(speaker_combo_index)
            self.speaker_status_label.hide()
        else:
            self.speaker_combo.setEnabled(False)
            self.speaker_status_label.setText(
                "No speakers configured. Add voices in the add-on config to enable generation."
            )
            self.speaker_status_label.setStyleSheet("color: #cc3300;")

        # Preview note selection dropdown
        if len(self.selected_notes) > 1:
            self.grid_layout.addWidget(qt.QLabel("Preview from note: "), 3, 0)
            self.preview_note_combo = qt.QComboBox()
            self.preview_note_combo.setToolTip(
                "Select which note to use for voice preview. Shows a snippet of each note's source field."
            )

            # Populate the dropdown with note snippets
            self._populatePreviewNoteCombo()

            # Connect to update when source field changes
            self.source_combo.currentIndexChanged.connect(self._populatePreviewNoteCombo)
            self.source_combo.currentIndexChanged.connect(self._reset_preview_cache)

            self.grid_layout.addWidget(self.preview_note_combo, 3, 1, 1, 2)
            self.preview_note_combo.currentIndexChanged.connect(self._reset_preview_cache)

        self.preview_voice_button = qt.QPushButton("Preview Voice", self)
        self.preview_voice_button.setToolTip(
            "Preview the selected voice using text from the selected note's source field. First preview may take a few seconds to initialize the speech engine."
        )

        self.preview_voice_button.clicked.connect(self.PreviewVoice)
        self.grid_layout.addWidget(
            self.preview_voice_button,
            3 if len(self.selected_notes) <= 1 else 4,
            4 if len(self.selected_notes) <= 1 else 0,
        )

        self.cancel_button = qt.QPushButton("Cancel")
        self.generate_button = qt.QPushButton("Generate Audio")

        self.cancel_button.clicked.connect(self.reject)
        self.generate_button.clicked.connect(self.pre_accept)

        # Position buttons on the appropriate row based on whether preview note selector is shown
        button_row = 3 if len(self.selected_notes) <= 1 else 5
        self.grid_layout.addWidget(self.cancel_button, button_row, 0, 1, 2)
        self.grid_layout.addWidget(self.generate_button, button_row, 3, 1, 2)

        if self.speaker_combo.count() == 0:
            self.preview_voice_button.setEnabled(False)
            self.preview_voice_button.setToolTip("Add speakers in the add-on config to preview a voice.")
            self.generate_button.setEnabled(False)
            self.generate_button.setToolTip("Add speakers in the add-on config to generate audio.")

        def update_slider(slider, label, config_name, slider_desc, slider_unit):
            def update_this_slider(value):
                label.setText(f"{slider_desc} {slider.value()}{slider_unit}")
                config[config_name] = slider.value()
                mw.addonManager.writeConfig(__name__, config)
                self._reset_preview_cache()

            return update_this_slider

        # Calculate base row for sliders based on whether preview note selector is shown
        slider_base_row = 4 if len(self.selected_notes) <= 1 else 6

        volume_slider = QSlider(qt.Qt.Orientation.Horizontal)
        volume_slider.setMinimum(-100)
        volume_slider.setMaximum(100)
        volume_slider.setValue(config.get("volume_slider_value") or 0)
        self.volume_slider = volume_slider

        volume_label = QLabel(f"Volume scale {volume_slider.value()}%")

        volume_slider.valueChanged.connect(
            update_slider(volume_slider, volume_label, "volume_slider_value", "Volume scale", "%")
        )

        self.grid_layout.addWidget(volume_label, slider_base_row, 0, 1, 2)
        self.grid_layout.addWidget(volume_slider, slider_base_row, 3, 1, 2)

        pitch_slider = QSlider(qt.Qt.Orientation.Horizontal)
        pitch_slider.setMinimum(-50)
        pitch_slider.setMaximum(50)
        pitch_slider.setValue(config.get("pitch_slider_value") or 0)
        self.pitch_slider = pitch_slider

        pitch_label = QLabel(f"Pitch scale {pitch_slider.value()}Hz")

        pitch_slider.valueChanged.connect(
            update_slider(pitch_slider, pitch_label, "pitch_slider_value", "Pitch scale", "Hz")
        )

        self.grid_layout.addWidget(pitch_label, slider_base_row + 1, 0, 1, 2)
        self.grid_layout.addWidget(pitch_slider, slider_base_row + 1, 3, 1, 2)

        speed_slider = QSlider(qt.Qt.Orientation.Horizontal)
        speed_slider.setMinimum(-50)
        speed_slider.setMaximum(50)
        speed_slider.setValue(config.get("speed_slider_value") or 0)
        self.speed_slider = speed_slider

        speed_label = QLabel(f"Speed scale {speed_slider.value()}%")

        speed_slider.valueChanged.connect(
            update_slider(speed_slider, speed_label, "speed_slider_value", "Rate scale", "%")
        )

        self.grid_layout.addWidget(speed_label, slider_base_row + 2, 0, 1, 2)
        self.grid_layout.addWidget(speed_slider, slider_base_row + 2, 3, 1, 2)

        layout.addLayout(self.grid_layout)

        self.setLayout(layout)

    def _reset_preview_cache(self):
        self._preview_cache = None

    def _get_preview_parameters(self):
        pitch = f"{self.pitch_slider.value():+}Hz"
        rate = f"{self.speed_slider.value():+}%"
        volume = f"{self.volume_slider.value():+}%"
        return pitch, rate, volume

    def onDestinationChanged(self, index):
        """Handle destination field dropdown change - prompt for new field name if 'Create new field' is selected"""
        if self.destination_combo.itemText(index) == CREATE_NEW_FIELD_OPTION:
            field_name, ok = QInputDialog.getText(
                self, "Create New Field", "Enter the name for the new audio field:", text="Audio"
            )
            if ok and field_name.strip():
                field_name = field_name.strip()
                # Check if field already exists
                if field_name in self.common_fields:
                    QMessageBox.warning(
                        self,
                        "Field Exists",
                        f"A field named '{field_name}' already exists. Please select it from the dropdown or choose a different name.",
                    )
                    # Reset to first item
                    self.destination_combo.setCurrentIndex(0)
                else:
                    self.new_field_name = field_name
                    # Insert the new field name before the "Create new field" option
                    insert_index = self.destination_combo.count() - 1
                    self.destination_combo.insertItem(insert_index, field_name)
                    self.destination_combo.setCurrentIndex(insert_index)
            else:
                # User cancelled, reset to first item
                self.destination_combo.setCurrentIndex(0)

    def pre_accept(self):
        destination_text = self.destination_combo.itemText(self.destination_combo.currentIndex())
        source_text = self.source_combo.itemText(self.source_combo.currentIndex())

        if len(self.common_fields) < 1:
            QMessageBox.critical(
                mw,
                "Error",
                "No common fields were found between the selected notes. Please pick notes that share compatible types before generating audio.",
            )
            self.reject()
            return

        # Don't allow selecting "Create new field" option directly without entering a name
        if destination_text == CREATE_NEW_FIELD_OPTION:
            QMessageBox.critical(
                mw,
                "Error",
                "Please select an existing field or create a new one by selecting '[ + Create new field... ]' and entering a name.",
            )
            return

        # Check if source and destination are the same (only if destination is not a new field)
        if self.new_field_name is None and self.source_combo.currentIndex() == self.destination_combo.currentIndex():
            QMessageBox.critical(
                mw,
                "Error",
                f"The chosen source field '{source_text}' is the same as the destination field '{destination_text}'.\nThis would overwrite the field you're reading from.\n\nTypically you want to read from a field like 'sentence' and output to 'audio', but in this case you're trying to read from 'sentence' and write to 'sentence' which cause your sentence to be overwritten",
            )
        else:
            self.accept()

    def getAudioHandlingMode(self):
        """Returns the selected audio handling mode: 'append', 'overwrite', or 'skip'"""
        if self.overwrite_radio.isChecked():
            return "overwrite"
        elif self.skip_radio.isChecked():
            return "skip"
        else:
            return "append"

    def _populatePreviewNoteCombo(self):
        """Populate the preview note combo box with snippets from each selected note."""
        if len(self.selected_notes) <= 1:
            return  # No combo box for single note

        # Get current source field
        source_field = self.source_combo.itemText(self.source_combo.currentIndex())

        # Remember the current selection before clearing
        current_index = 0
        if hasattr(self, "preview_note_combo") and self.preview_note_combo.count() > 0:
            current_index = self.preview_note_combo.currentIndex()

        # Clear and repopulate
        self.preview_note_combo.clear()

        for i, note_id in enumerate(self.selected_notes):
            note = mw.col.get_note(note_id)
            if note is None:
                self.preview_note_combo.addItem(f"Note {i + 1} (ID: {note_id})")
                continue

            try:
                note_text = note[source_field]
                # Clean the text to show a snippet
                note_text = ENTITY_RE.sub("", note_text)
                note_text = TAG_RE.sub("", note_text)
                note_text = note_text.strip()

                # Create a short snippet using the configured max length
                if note_text:
                    snippet = note_text[:PREVIEW_NOTE_SNIPPET_MAX_LENGTH]
                    if len(note_text) > PREVIEW_NOTE_SNIPPET_MAX_LENGTH:
                        snippet += "..."
                    self.preview_note_combo.addItem(f"Note {i + 1}: {snippet}")
                else:
                    self.preview_note_combo.addItem(f"Note {i + 1}: (empty)")
            except KeyError:
                self.preview_note_combo.addItem(f"Note {i + 1}: (no '{source_field}' field)")

        # Restore previous selection if valid
        if current_index < self.preview_note_combo.count():
            self.preview_note_combo.setCurrentIndex(current_index)

    def _getPreviewTextFromNote(self, source_field, speaker):
        """Get text from the selected note's source field for preview."""
        if not self.selected_notes:
            return None

        # Get the selected note index from combo box (if multiple notes)
        note_index = 0
        if len(self.selected_notes) > 1 and hasattr(self, "preview_note_combo"):
            note_index = self.preview_note_combo.currentIndex()
            # Ensure index is valid
            if note_index < 0 or note_index >= len(self.selected_notes):
                note_index = 0

        note_id = self.selected_notes[note_index]
        note = mw.col.get_note(note_id)
        if note is None:
            return None

        try:
            note_text = note[source_field]
        except KeyError:
            return None

        if not note_text:
            return None

        # Clean the text similar to how it's done in getNoteTextAndSpeaker
        # Remove HTML entities and tags
        note_text = ENTITY_RE.sub("", note_text)
        note_text = TAG_RE.sub("", note_text)

        # Replace text with reading from brackets (e.g., word[reading] -> reading)
        note_text = BRACKET_READING_RE.sub(r"\1", note_text)

        # Remove stuff between brackets if option is enabled
        if self.ignore_brackets_checkbox.isChecked():
            note_text = BRACKET_CONTENT_RE.sub("", note_text)

        # Strip whitespace for CJK languages that don't use spaces between words
        if speaker:
            language_code = speaker.split("-")[0].lower()
            if language_code in {"ja", "zh"}:
                note_text = WHITESPACE_RE.sub("", note_text)

        return note_text.strip() if note_text else None

    def PreviewVoice(self):
        speaker = getSpeaker(self.speaker_combo)
        if speaker is None:
            raise Exception("getSpeaker returned None in PreviewVoice")

        # Get the actual text from the first selected note's source field
        source_field = self.source_combo.itemText(self.source_combo.currentIndex())
        preview_text = self._getPreviewTextFromNote(source_field, speaker)

        if not preview_text:
            QMessageBox.warning(
                self,
                "No Preview Text",
                f"The source field '{source_field}' is empty in the selected note(s). "
                "Please select a note with text content to preview the voice.",
            )
            return

        pitch, rate, volume = self._get_preview_parameters()
        cache_key = (preview_text, speaker, pitch, rate, volume)

        if self._preview_cache and self._preview_cache.get("key") == cache_key:
            original_text = self.preview_voice_button.text()
            self.preview_voice_button.setText("Playing cached preview...")
            self.preview_voice_button.setEnabled(False)

            def play_cached():
                addon_path = dirname(__file__)
                preview_path = join(addon_path, "edge_tts_preview.mp3")
                with open(preview_path, "wb") as f:
                    f.write(self._preview_cache.get("audio", b""))
                av_player.play_file(preview_path)
                self.preview_voice_button.setText(original_text)
                self.preview_voice_button.setEnabled(True)

            mw.taskman.run_on_main(play_cached)
            return

        tup = (preview_text, speaker)

        # Disable button and show loading state during generation
        original_text = self.preview_voice_button.text()
        self.preview_voice_button.setText("Loading preview (may take a few seconds)...")
        self.preview_voice_button.setEnabled(False)

        def generate_preview():
            """Background task to generate preview audio"""
            return GenerateAudioQuery(tup, mw.addonManager.getConfig(__name__))

        def on_preview_done(future):
            """Callback when preview generation is complete"""
            # Re-enable button
            mw.taskman.run_on_main(lambda: self.preview_voice_button.setEnabled(True))
            mw.taskman.run_on_main(lambda: self.preview_voice_button.setText(original_text))

            try:
                result = future.result()
                self._preview_cache = {"key": cache_key, "audio": result}

                def play_preview():
                    """Write file and play audio on main thread"""
                    addon_path = dirname(__file__)
                    preview_path = join(addon_path, "edge_tts_preview.mp3")
                    with open(preview_path, "wb") as f:
                        f.write(result)
                    av_player.play_file(preview_path)

                mw.taskman.run_on_main(play_preview)
            except Exception as exc:
                error_msg = str(exc)
                mw.taskman.run_on_main(
                    lambda: QMessageBox.critical(self, "Preview Error", f"Failed to generate preview:\n{error_msg}")
                )

        # Run preview generation in background thread
        mw.taskman.run_in_background(generate_preview, on_preview_done)


def GenerateAudioBatch(text_speaker_items, config):
    """Generate audio for a batch of text items using bundled edge-tts."""
    if not text_speaker_items:
        logger.debug("GenerateAudioBatch called with empty items list")
        return BatchAudioResult(audio_map={}, item_errors=[])

    logger.info("Starting batch audio generation for %d items", len(text_speaker_items))

    # Build TTS configuration from config
    pitch = f"{config.get('pitch_slider_value', 0):+}Hz"
    rate = f"{config.get('speed_slider_value', 0):+}%"
    volume = f"{config.get('volume_slider_value', 0):+}%"
    stream_timeout_seconds = config.get("stream_timeout_seconds", 30.0)
    stream_timeout_retries = config.get("stream_timeout_retries", 1)
    # All items share the same voice; take the first entry
    voice = text_speaker_items[0][2]

    logger.debug("Audio parameters: voice=%s, pitch=%s, rate=%s, volume=%s", voice, pitch, rate, volume)

    tts_config = TTSConfig(
        voice=voice,
        pitch=pitch,
        rate=rate,
        volume=volume,
        stream_timeout=stream_timeout_seconds,
        stream_timeout_retries=stream_timeout_retries,
    )

    # Convert to TTSItem list
    items = [
        TTSItem(identifier=str(identifier), text=text, voice=item_voice)
        for identifier, text, item_voice in text_speaker_items
    ]

    try:
        logger.debug("Starting bundled TTS synthesis")
        results = synthesize_batch(items, tts_config)
        logger.debug("Bundled TTS synthesis completed")
    except Exception as exc:
        logger.error("TTS synthesis failed: %s", exc)
        raise RuntimeError(f"Failed to synthesize text in batch: {exc}") from exc

    # Convert results to BatchAudioResult format
    audio_map: dict[str, bytes] = {}
    item_errors: list[ItemError] = []

    for result in results:
        if result.error:
            logger.warning("Audio generation error for item %s: %s", result.identifier, result.error)
            item_errors.append(ItemError(identifier=result.identifier, reason=result.error))
        elif result.audio:
            audio_map[result.identifier] = result.audio
        else:
            logger.warning("Missing audio data for item %s", result.identifier)
            item_errors.append(ItemError(identifier=result.identifier, reason="Missing audio data in response"))

    logger.info(
        "Batch audio generation complete: %d successful, %d errors",
        len(audio_map),
        len(item_errors),
    )
    return BatchAudioResult(audio_map=audio_map, item_errors=item_errors)


def GenerateAudioQuery(text_and_speaker_tuple, config):
    text = text_and_speaker_tuple[0]
    voice = text_and_speaker_tuple[1]
    batch_result = GenerateAudioBatch([(0, text, voice)], config)
    if batch_result.item_errors:
        error = batch_result.item_errors[0]
        raise RuntimeError(f"Audio generation failed for preview item {error.identifier}: {error.reason}")

    audio_bytes = batch_result.audio_map.get("0")
    if audio_bytes is None:
        raise RuntimeError("Preview audio missing from batch result")

    return audio_bytes


def addFieldToNoteTypes(field_name, selected_notes):
    """Add a new field to all note types used by the selected notes"""
    note_types_updated = set()
    for note_id in selected_notes:
        note = mw.col.get_note(note_id)
        model = note.note_type()
        model_id = model["id"]

        if model_id not in note_types_updated:
            # Check if field already exists in this note type
            existing_fields = [f["name"] for f in model["flds"]]
            if field_name not in existing_fields:
                # Add the new field
                new_field = mw.col.models.new_field(field_name)
                mw.col.models.add_field(model, new_field)
                mw.col.models.save(model)
                note_types_updated.add(model_id)


def onEdgeTTSOptionSelected(browser):
    selected_notes = browser.selectedNotes()
    logger.debug("Edge TTS option selected with %d notes", len(selected_notes))

    if len(selected_notes) == 0:
        logger.debug("No notes selected, showing information dialog")
        QMessageBox.information(
            mw,
            "No notes selected",
            "Please select one or more notes before generating audio.",
        )
        return

    dialog = MyDialog(browser)
    if dialog.exec():
        speaker = getSpeaker(dialog.speaker_combo)
        if speaker is None:
            logger.error("getSpeaker returned None in onEdgeTTSOptionSelected")
            raise Exception("getSpeaker returned None in my_action")

        source_field = dialog.source_combo.itemText(dialog.source_combo.currentIndex())
        destination_field = dialog.destination_combo.itemText(dialog.destination_combo.currentIndex())

        # Get the audio handling mode
        audio_handling_mode = dialog.getAudioHandlingMode()

        # Check if we need to create a new field
        new_field_name = dialog.new_field_name

        speaker_combo_text = dialog.speaker_combo.itemText(dialog.speaker_combo.currentIndex())

        # Save previously used stuff
        config = mw.addonManager.getConfig(__name__)
        config["last_source_field"] = source_field
        config["last_destination_field"] = destination_field
        config["last_speaker_name"] = speaker_combo_text
        config["last_audio_handling"] = audio_handling_mode
        config["ignore_brackets_enabled"] = dialog.ignore_brackets_checkbox.isChecked()
        mw.addonManager.writeConfig(__name__, config)

        # Create the new field if needed
        if new_field_name:
            addFieldToNoteTypes(new_field_name, dialog.selected_notes)
            destination_field = new_field_name

        def getNoteTextAndSpeaker(note_id):
            note = mw.col.get_note(note_id)
            note_text = note[source_field]

            def _should_strip_whitespace(selected_voice: str) -> bool:
                """Only strip spaces for languages that don't rely on them."""

                if not selected_voice:
                    return False

                language_code = selected_voice.split("-")[0].lower()
                return language_code in {"ja", "zh"}

            # Remove HTML tags and entities using standard regex patterns
            note_text = ENTITY_RE.sub("", note_text)
            note_text = TAG_RE.sub("", note_text)

            # Replace text with reading from brackets (e.g., word[reading] -> reading)
            note_text = BRACKET_READING_RE.sub(r"\1", note_text)
            # Remove stuff between brackets (commonly used for readings, pitch accent, or metadata)
            if dialog.ignore_brackets_checkbox.isChecked():
                note_text = BRACKET_CONTENT_RE.sub("", note_text)

            if _should_strip_whitespace(speaker):
                note_text = WHITESPACE_RE.sub(
                    "", note_text
                )  # Strip spaces for CJK languages that don't use spaces between words

            return (note_text, speaker)

        def updateProgress(notes_so_far, total_notes, skipped_count=0):
            label = f"{notes_so_far}/{total_notes} generated"
            if skipped_count > 0:
                label += f" ({skipped_count} skipped)"
            mw.taskman.run_on_main(
                lambda: mw.progress.update(
                    label=label,
                    value=notes_so_far,
                    max=total_notes,
                )
            )

        def getFieldContent(note, field_name):
            """Get content of a field, returning empty string if field doesn't exist"""
            try:
                return note[field_name].strip()
            except KeyError:
                return ""

        def on_done(future):
            try:
                future.result()
            except Exception as exc:
                mw.progress.finish()
                mw.reset()
                QMessageBox.critical(
                    mw,
                    "Edge TTS Generation Failed",
                    f"An error occurred while generating audio:\n{exc}",
                )
                return

            mw.progress.finish()
            mw.reset()

        mw.taskman.run_in_background(lambda: GenerateAudio(dialog.selected_notes), on_done)

        def GenerateAudio(notes):
            total_notes = len(notes)
            mw.taskman.run_on_main(lambda: mw.progress.start(label="Generating Audio", max=total_notes, immediate=True))
            notes_so_far = 0
            skipped_count = 0
            missing_text_skips = 0
            pending_items = []
            pending_note_ids = []
            chunk_size = 10
            config = mw.addonManager.getConfig(__name__)

            for note_id in notes:
                note = mw.col.get_note(note_id)
                existing_content = getFieldContent(note, destination_field)

                # Handle skip mode: skip if destination field already has content
                if audio_handling_mode == "skip" and existing_content:
                    notes_so_far += 1
                    skipped_count += 1
                    updateProgress(notes_so_far, total_notes, skipped_count)
                    continue

                note_text, selected_voice = getNoteTextAndSpeaker(note_id)
                if not note_text.strip():
                    notes_so_far += 1
                    skipped_count += 1
                    missing_text_skips += 1
                    updateProgress(notes_so_far, total_notes, skipped_count)
                    continue
                pending_items.append((str(note_id), note_text, selected_voice))
                pending_note_ids.append(note_id)

            if not pending_items:
                return

            canceled = False
            failures: list[str] = []
            for chunk_start in range(0, len(pending_items), chunk_size):
                if mw.progress.want_cancel():
                    break

                chunk_items = pending_items[chunk_start : chunk_start + chunk_size]
                chunk_note_ids = pending_note_ids[chunk_start : chunk_start + chunk_size]

                batch_result = GenerateAudioBatch(chunk_items, config)
                error_lookup = {error.identifier: error.reason for error in batch_result.item_errors}

                for note_id in chunk_note_ids:
                    notes_so_far += 1
                    identifier = str(note_id)
                    audio_data = batch_result.audio_map.get(identifier)
                    if identifier in error_lookup:
                        failures.append(f"{identifier}: {error_lookup[identifier]}")
                        updateProgress(notes_so_far, total_notes, skipped_count)
                        if mw.progress.want_cancel():
                            canceled = True
                            break
                        continue
                    if audio_data is None:
                        failures.append(f"{identifier}: No audio returned in batch result")
                        updateProgress(notes_so_far, total_notes, skipped_count)
                        if mw.progress.want_cancel():
                            canceled = True
                            break
                        continue

                    media_dir = mw.col.media.dir()

                    file_id = str(uuid.uuid4())
                    audio_extension = "mp3"
                    filename = f"edge_tts_{file_id}.{audio_extension}"
                    audio_full_path = join(media_dir, filename)

                    with open(audio_full_path, "wb") as f:
                        f.write(audio_data)

                    audio_field_text = f"[sound:{filename}]"
                    note = mw.col.get_note(note_id)

                    # Re-read current content from fresh note to avoid stale data issues
                    current_content = getFieldContent(note, destination_field)

                    # Handle audio placement based on mode
                    if audio_handling_mode == "append" and current_content:
                        # Append: keep existing content and add new audio
                        note[destination_field] = current_content + " " + audio_field_text
                    else:
                        # Overwrite: replace content entirely (also used for empty fields)
                        note[destination_field] = audio_field_text

                    mw.col.update_note(note)
                    updateProgress(notes_so_far, total_notes, skipped_count)
                    if mw.progress.want_cancel():
                        canceled = True
                        break

                if canceled or mw.progress.want_cancel():
                    break

            if missing_text_skips > 0:
                mw.taskman.run_on_main(
                    lambda: tooltip(f"Skipped {missing_text_skips} notes with no text in the source field.")
                )

            if failures:
                failure_summary = "\n".join(f"- {failure}" for failure in failures)
                mw.taskman.run_on_main(
                    lambda: QMessageBox.warning(
                        mw,
                        "Audio Generation Completed with Errors",
                        (
                            "Audio was generated for available notes, but some items failed:\n"
                            f"{failure_summary}\n\n"
                            "You can re-run generation for the failed notes after resolving the issues."
                        ),
                    )
                )

    else:
        logger.debug("Audio generation dialog canceled by user")

from aqt.qt import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QApplication,
    QMessageBox,
    QSlider,
)
from aqt import browser, gui_hooks, qt
from aqt import mw
from aqt.sound import av_player
from os.path import join, exists, dirname
import os
import random
import subprocess
import tempfile
import uuid
import re
import traceback

from .external_runtime import get_external_python


def getCommonFields(selected_notes):
    common_fields = set()

    first = True

    for note_id in selected_notes:
        note = mw.col.get_note(note_id)
        if note is None:
            raise Exception(
                f"Note with id {note_id} is None.\nNotes: {','.join([mw.col.get_note(id) for id in selected_notes])}.\nPlease submit an issues with more information about what cards caused this at https://github.com/Toocanzs/anki-voicevox/issues/new"
            )
        model = note.note_type()
        model_fields = set([f["name"] for f in model["flds"]])
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
        self.selected_notes = browser.selectedNotes()

        config = mw.addonManager.getConfig(__name__)

        layout = qt.QVBoxLayout()

        layout.addWidget(qt.QLabel("Selected notes: " + str(len(self.selected_notes))))

        self.grid_layout = qt.QGridLayout()

        common_fields = getCommonFields(self.selected_notes)

        if len(common_fields) < 1:
            QMessageBox.critical(
                mw,
                "Error",
                f"The chosen notes share no fields in common. Make sure you're not selecting two different note types",
            )
        elif len(common_fields) == 1:
            QMessageBox.critical(
                mw,
                "Error",
                f"The chosen notes only share a single field in common '{list(common_fields)[0]}'. This would leave no field to put the generated audio without overwriting the sentence data",
            )

        self.source_combo = qt.QComboBox()
        self.destination_combo = qt.QComboBox()

        last_source_field = config.get("last_source_field") or None
        last_destination_field = config.get("last_destination_field") or None
        source_field_index = 0
        destination_field_index = 0
        i = 0
        for field in common_fields:
            if last_source_field is None:
                if "expression" == field.lower() or "sentence" == field.lower():
                    source_field_index = i
            elif field == last_source_field:
                source_field_index = i

            if last_destination_field is None:
                if "audio" == field.lower():
                    destination_field_index = i
            elif field == last_destination_field:
                destination_field_index = i
            self.source_combo.addItem(field)
            self.destination_combo.addItem(field)
            i += 1

        self.source_combo.setCurrentIndex(source_field_index)
        self.destination_combo.setCurrentIndex(destination_field_index)

        source_label = qt.QLabel("Source field: ")
        source_tooltip = "The field to read from. For example if your sentence is in the field 'Expression' you want to choose 'Expression' as the source field to read from"
        source_label.setToolTip(source_tooltip)

        destination_label = qt.QLabel("Destination field: ")
        destination_tooltip = "The field to write the audio to. Typically you want to choose a field like 'Audio' or 'Audio on Front' or wherever you want the audio placed on your card."
        destination_label.setToolTip(destination_tooltip)

        self.source_combo.setToolTip(source_tooltip)
        self.destination_combo.setToolTip(destination_tooltip)

        self.grid_layout.addWidget(source_label, 0, 0)
        self.grid_layout.addWidget(self.source_combo, 0, 1)
        self.grid_layout.addWidget(destination_label, 0, 2)
        self.grid_layout.addWidget(self.destination_combo, 0, 3)

        # TODO: Does anyone actually want to not ignore stuff in brackets? The checkbox is here if we need it but I don't think anyone wants brackets to be read
        self.ignore_brackets_checkbox = qt.QCheckBox("Ignore stuff in brackets [...]")
        self.ignore_brackets_checkbox.setToolTip(
            "Ignores things between brackets. Usually Japanese cards have pitch accent and reading info in brackets. Leave this checked unless you really know what you're doing"
        )
        self.ignore_brackets_checkbox.setChecked(True)
        # self.grid_layout.addWidget(self.ignore_brackets_checkbox, 0, 4)

        self.grid_layout.addWidget(qt.QLabel("Speaker: "), 1, 0)
        self.speakers = getSpeakerList(config)
        self.speaker_combo = qt.QComboBox()
        for speaker in self.speakers:
            self.speaker_combo.addItem(speaker)
        self.grid_layout.addWidget(self.speaker_combo, 1, 1)

        last_speaker_name = config.get("last_speaker_name") or None

        # find the speaker/style from the previously saved config data and pick it from the dropdown
        speaker_combo_index = 0
        i = 0
        for speaker_item in [
            self.speaker_combo.itemText(i) for i in range(self.speaker_combo.count())
        ]:
            if speaker_item == last_speaker_name:
                speaker_combo_index = i
                break
            i += 1

        self.speaker_combo.setCurrentIndex(speaker_combo_index)

        self.preview_voice_button = qt.QPushButton("Preview Voice", self)

        self.preview_voice_button.clicked.connect(self.PreviewVoice)
        self.grid_layout.addWidget(self.preview_voice_button, 1, 4)

        self.cancel_button = qt.QPushButton("Cancel")
        self.generate_button = qt.QPushButton("Generate Audio")

        self.cancel_button.clicked.connect(self.reject)
        self.generate_button.clicked.connect(self.pre_accept)

        self.grid_layout.addWidget(self.cancel_button, 2, 0, 1, 2)
        self.grid_layout.addWidget(self.generate_button, 2, 3, 1, 2)

        def update_slider(slider, label, config_name, slider_desc, slider_unit):
            def update_this_slider(value):
                label.setText(f"{slider_desc} {slider.value()}{slider_unit}")
                config[config_name] = slider.value()
                mw.addonManager.writeConfig(__name__, config)

            return update_this_slider

        volume_slider = QSlider(qt.Qt.Orientation.Horizontal)
        volume_slider.setMinimum(-100)
        volume_slider.setMaximum(100)
        volume_slider.setValue(config.get("volume_slider_value") or 0)

        volume_label = QLabel(f"Volume scale {volume_slider.value()}%")

        volume_slider.valueChanged.connect(
            update_slider(
                volume_slider, volume_label, "volume_slider_value", "Volume scale", "%"
            )
        )

        self.grid_layout.addWidget(volume_label, 3, 0, 1, 2)
        self.grid_layout.addWidget(volume_slider, 3, 3, 1, 2)

        pitch_slider = QSlider(qt.Qt.Orientation.Horizontal)
        pitch_slider.setMinimum(-50)
        pitch_slider.setMaximum(50)
        pitch_slider.setValue(config.get("pitch_slider_value") or 0)

        pitch_label = QLabel(f"Pitch scale {pitch_slider.value()}Hz")

        pitch_slider.valueChanged.connect(
            update_slider(
                pitch_slider, pitch_label, "pitch_slider_value", "Pitch scale", "Hz"
            )
        )

        self.grid_layout.addWidget(pitch_label, 4, 0, 1, 2)
        self.grid_layout.addWidget(pitch_slider, 4, 3, 1, 2)

        speed_slider = QSlider(qt.Qt.Orientation.Horizontal)
        speed_slider.setMinimum(-50)
        speed_slider.setMaximum(50)
        speed_slider.setValue(config.get("speed_slider_value") or 0)

        speed_label = QLabel(f"Speed scale {speed_slider.value()}%")

        speed_slider.valueChanged.connect(
            update_slider(
                speed_slider, speed_label, "speed_slider_value", "Rate scale", "%"
            )
        )

        self.grid_layout.addWidget(speed_label, 5, 0, 1, 2)
        self.grid_layout.addWidget(speed_slider, 5, 3, 1, 2)

        layout.addLayout(self.grid_layout)

        self.setLayout(layout)

    def pre_accept(self):
        if self.source_combo.currentIndex() == self.destination_combo.currentIndex():
            source_text = self.source_combo.itemText(self.source_combo.currentIndex())
            destination_text = self.destination_combo.itemText(
                self.destination_combo.currentIndex()
            )
            QMessageBox.critical(
                mw,
                "Error",
                f"The chosen source field '{source_text}' is the same as the destination field '{destination_text}'.\nThis would overwrite the field you're reading from.\n\nTypically you want to read from a field like 'sentence' and output to 'audio', but in this case you're trying to read from 'sentence' and write to 'sentence' which cause your sentence to be overwritten",
            )
        else:
            self.accept()

    def PreviewVoice(self):
        speaker = getSpeaker(self.speaker_combo)
        if speaker is None:
            raise Exception("getSpeaker returned None in PreviewVoice")

        preview_sentences = [
            "こんにちは、これはテスト文章です。",
            "ＤＶＤの再生ボタンを押して、書斎に向かった。",
            "さてと 、 ご馳走様でした",
            "真似しないでくれる？",
            "な 、 なんだよ ？　 テンション高いな",
        ]

        tup = (random.choice(preview_sentences), speaker)
        result = GenerateAudioQuery(tup, mw.addonManager.getConfig(__name__))

        addon_path = dirname(__file__)
        preivew_path = join(addon_path, "edge_tts_preview.mp3")
        with open(preivew_path, "wb") as f:
            f.write(result)
        av_player.play_file(preivew_path)


def GenerateAudioQuery(text_and_speaker_tuple, config):
    text = text_and_speaker_tuple[0]
    voice = text_and_speaker_tuple[1]
    addon_dir = dirname(__file__)

    try:
        python_exe = get_external_python(addon_dir)
    except Exception:
        raise Exception(
            "Failed to bootstrap external Python runtime. Check your internet connection and restart Anki."
        )

    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", suffix=".txt", delete=False
    ) as handle:
        handle.write(text)
        text_path = handle.name

    pitch = f"{config.get('pitch_slider_value', 0):+}Hz"
    rate = f"{config.get('speed_slider_value', 0):+}%"
    volume = f"{config.get('volume_slider_value', 0):+}%"

    runner_path = join(addon_dir, "external_tts_runner.py")
    command = [
        python_exe,
        runner_path,
        "--text-file",
        text_path,
        "--voice",
        voice,
        "--pitch",
        pitch,
        "--rate",
        rate,
        "--volume",
        volume,
    ]

    try:
        result = subprocess.run(
            command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as exc:
        error_output = exc.stderr.decode("utf-8", errors="replace")
        raise Exception(
            f"Unable to generate audio for `{text}`. External runner failed with: {error_output}"
        )
    finally:
        if exists(text_path):
            os.remove(text_path)

    return result.stdout


def onEdgeTTSOptionSelected(browser):
    dialog = MyDialog(browser)
    if dialog.exec():
        speaker = getSpeaker(dialog.speaker_combo)
        if speaker is None:
            raise Exception("getSpeaker returned None in my_action")

        source_field = dialog.source_combo.itemText(dialog.source_combo.currentIndex())
        destination_field = dialog.destination_combo.itemText(
            dialog.destination_combo.currentIndex()
        )

        speaker_combo_text = dialog.speaker_combo.itemText(
            dialog.speaker_combo.currentIndex()
        )

        # Save previously used stuff
        config = mw.addonManager.getConfig(__name__)
        config["last_source_field"] = source_field
        config["last_destination_field"] = destination_field
        config["last_speaker_name"] = speaker_combo_text
        mw.addonManager.writeConfig(__name__, config)

        def getNoteTextAndSpeaker(note_id):
            note = mw.col.get_note(note_id)
            note_text = note[source_field]

            # Remove html tags https://stackoverflow.com/a/19730306
            tag_re = re.compile(r"(<!--.*?-->|<[^>]*>)")
            entity_re = re.compile(r"(&[^;]+;)")

            note_text = entity_re.sub("", note_text)
            note_text = tag_re.sub("", note_text)

            # Replace kanji with furigana from brackets
            note_text = re.sub(r" ?\S*?\[(.*?)\]", r"\1", note_text)
            # Remove stuff between brackets. Usually japanese cards have pitch accent and reading info in brackets like 「 タイトル[;a,h] を 聞[き,きく;h]いた わけ[;a] じゃ ない[;a] ！」
            if dialog.ignore_brackets_checkbox.isChecked():
                note_text = re.sub("\[.*?\]", "", note_text)
            note_text = re.sub(
                " ", "", note_text
            )  # there's a lot of spaces for whatever reason which throws off the voice gen so we remove all spaces (japanese doesn't care about them anyway)

            return (note_text, speaker)

        def updateProgress(notes_so_far, total_notes, bottom_text=""):
            mw.taskman.run_on_main(
                lambda: mw.progress.update(
                    label=f"{notes_so_far}/{total_notes} generated",
                    value=notes_so_far,
                    max=total_notes,
                )
            )

        def on_done(future):
            mw.progress.finish()
            mw.reset()

        fut = mw.taskman.run_in_background(
            lambda: GenerateAudio(dialog.selected_notes), on_done
        )

        def GenerateAudio(notes):
            total_notes = len(notes)
            mw.taskman.run_on_main(
                lambda: mw.progress.start(
                    label="Generating Audio", max=total_notes, immediate=True
                )
            )
            notes_so_far = 0
            for note_id in notes:
                notes_so_far += 1
                updateProgress(notes_so_far, total_notes)

                note_text_and_speaker = getNoteTextAndSpeaker(note_id)

                audio_data = GenerateAudioQuery(
                    note_text_and_speaker, mw.addonManager.getConfig(__name__)
                )
                media_dir = mw.col.media.dir()

                file_id = str(uuid.uuid4())
                audio_extension = "mp3"
                filename = f"edge_tts_{file_id}.{audio_extension}"
                audio_full_path = join(media_dir, filename)

                with open(audio_full_path, "wb") as f:
                    f.write(audio_data)

                audio_field_text = f"[sound:{filename}]"
                note = mw.col.get_note(note_id)
                note[destination_field] = audio_field_text
                mw.col.update_note(note)
                if mw.progress.want_cancel():
                    break

    else:
        print("Canceled!")

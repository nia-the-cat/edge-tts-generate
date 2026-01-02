import os
import random
import re
import subprocess
import tempfile
import uuid
from os.path import dirname, exists, join

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

from .external_runtime import get_external_python

CREATE_NEW_FIELD_OPTION = "[ + Create new field... ]"


def getCommonFields(selected_notes):
    common_fields = set()

    first = True

    for note_id in selected_notes:
        note = mw.col.get_note(note_id)
        if note is None:
            raise Exception(
                f"Note with id {note_id} is None.\nNotes: {','.join([mw.col.get_note(id) for id in selected_notes])}.\nPlease submit an issue with more information about what cards caused this at https://github.com/nia-the-cat/edge-tts-generate/issues/new"
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

        config = mw.addonManager.getConfig(__name__)

        layout = qt.QVBoxLayout()

        layout.addWidget(qt.QLabel("Selected notes: " + str(len(self.selected_notes))))

        self.grid_layout = qt.QGridLayout()

        self.common_fields = getCommonFields(self.selected_notes)

        if len(self.common_fields) < 1:
            QMessageBox.critical(
                mw,
                "Error",
                f"The chosen notes share no fields in common. Make sure you're not selecting two different note types",
            )

        self.source_combo = qt.QComboBox()
        self.destination_combo = qt.QComboBox()

        last_source_field = config.get("last_source_field") or None
        last_destination_field = config.get("last_destination_field") or None
        source_field_index = 0
        destination_field_index = 0
        i = 0
        for field in self.common_fields:
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
        self.append_radio.setToolTip("Add the generated audio to the field without removing any existing content. This is the safest option.")
        
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
            "Ignores things between brackets. Usually Japanese cards have pitch accent and reading info in brackets. Leave this checked unless you really know what you're doing"
        )
        self.ignore_brackets_checkbox.setChecked(True)
        # self.grid_layout.addWidget(self.ignore_brackets_checkbox, 0, 4)

        self.grid_layout.addWidget(qt.QLabel("Speaker: "), 2, 0)
        self.speakers = getSpeakerList(config)
        self.speaker_combo = qt.QComboBox()
        for speaker in self.speakers:
            self.speaker_combo.addItem(speaker)
        self.grid_layout.addWidget(self.speaker_combo, 2, 1)

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
        self.grid_layout.addWidget(self.preview_voice_button, 2, 4)

        self.cancel_button = qt.QPushButton("Cancel")
        self.generate_button = qt.QPushButton("Generate Audio")

        self.cancel_button.clicked.connect(self.reject)
        self.generate_button.clicked.connect(self.pre_accept)

        self.grid_layout.addWidget(self.cancel_button, 3, 0, 1, 2)
        self.grid_layout.addWidget(self.generate_button, 3, 3, 1, 2)

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

        self.grid_layout.addWidget(volume_label, 4, 0, 1, 2)
        self.grid_layout.addWidget(volume_slider, 4, 3, 1, 2)

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

        self.grid_layout.addWidget(pitch_label, 5, 0, 1, 2)
        self.grid_layout.addWidget(pitch_slider, 5, 3, 1, 2)

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

        self.grid_layout.addWidget(speed_label, 6, 0, 1, 2)
        self.grid_layout.addWidget(speed_slider, 6, 3, 1, 2)

        layout.addLayout(self.grid_layout)

        self.setLayout(layout)

    def onDestinationChanged(self, index):
        """Handle destination field dropdown change - prompt for new field name if 'Create new field' is selected"""
        if self.destination_combo.itemText(index) == CREATE_NEW_FIELD_OPTION:
            field_name, ok = QInputDialog.getText(
                self,
                "Create New Field",
                "Enter the name for the new audio field:",
                text="Audio"
            )
            if ok and field_name.strip():
                field_name = field_name.strip()
                # Check if field already exists
                if field_name in self.common_fields:
                    QMessageBox.warning(
                        self,
                        "Field Exists",
                        f"A field named '{field_name}' already exists. Please select it from the dropdown or choose a different name."
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
        destination_text = self.destination_combo.itemText(
            self.destination_combo.currentIndex()
        )
        source_text = self.source_combo.itemText(self.source_combo.currentIndex())
        
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

    def PreviewVoice(self):
        speaker = getSpeaker(self.speaker_combo)
        if speaker is None:
            raise Exception("getSpeaker returned None in PreviewVoice")

        # Language-specific preview sentences
        preview_sentences_by_lang = {
            "ja": [
                "こんにちは、これはテスト文章です。",
                "ＤＶＤの再生ボタンを押して、書斎に向かった。",
                "さてと 、 ご馳走様でした",
                "真似しないでくれる？",
                "な 、 なんだよ ？　 テンション高いな",
            ],
            "en": [
                "Hello, this is a test sentence.",
                "The quick brown fox jumps over the lazy dog.",
                "Thank you for using this add-on.",
                "How are you doing today?",
                "This is a preview of the selected voice.",
            ],
            "de": [
                "Hallo, das ist ein Testsatz.",
                "Wie geht es dir heute?",
                "Vielen Dank für die Nutzung dieses Add-ons.",
                "Der schnelle braune Fuchs springt über den faulen Hund.",
                "Dies ist eine Vorschau der ausgewählten Stimme.",
            ],
            "zh": [
                "你好，这是一个测试句子。",
                "谢谢你使用这个插件。",
                "今天天气怎么样？",
                "快速的棕色狐狸跳过懒狗。",
                "这是所选语音的预览。",
            ],
            "ko": [
                "안녕하세요, 이것은 테스트 문장입니다.",
                "이 애드온을 사용해 주셔서 감사합니다.",
                "오늘 기분이 어떠세요?",
                "빠른 갈색 여우가 게으른 개를 뛰어넘습니다.",
                "선택한 음성의 미리보기입니다.",
            ],
            "fr": [
                "Bonjour, ceci est une phrase de test.",
                "Merci d'utiliser cette extension.",
                "Comment allez-vous aujourd'hui?",
                "Le rapide renard brun saute par-dessus le chien paresseux.",
                "Ceci est un aperçu de la voix sélectionnée.",
            ],
            "es": [
                "Hola, esta es una oración de prueba.",
                "Gracias por usar este complemento.",
                "¿Cómo estás hoy?",
                "El rápido zorro marrón salta sobre el perro perezoso.",
                "Esta es una vista previa de la voz seleccionada.",
            ],
            "pt": [
                "Olá, esta é uma frase de teste.",
                "Obrigado por usar este complemento.",
                "Como você está hoje?",
                "A rápida raposa marrom pula sobre o cão preguiçoso.",
                "Esta é uma prévia da voz selecionada.",
            ],
            "it": [
                "Ciao, questa è una frase di prova.",
                "Grazie per aver utilizzato questo componente aggiuntivo.",
                "Come stai oggi?",
                "La veloce volpe marrone salta sopra il cane pigro.",
                "Questa è un'anteprima della voce selezionata.",
            ],
        }

        # Extract language code from voice name (e.g., "ja-JP-NanamiNeural" -> "ja")
        lang_code = speaker.split("-")[0] if "-" in speaker else "en"
        
        # Get preview sentences for the language, fallback to English if not found
        preview_sentences = preview_sentences_by_lang.get(lang_code, preview_sentences_by_lang["en"])

        tup = (random.choice(preview_sentences), speaker)
        result = GenerateAudioQuery(tup, mw.addonManager.getConfig(__name__))

        addon_path = dirname(__file__)
        preview_path = join(addon_path, "edge_tts_preview.mp3")
        with open(preview_path, "wb") as f:
            f.write(result)
        av_player.play_file(preview_path)


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
    dialog = MyDialog(browser)
    if dialog.exec():
        speaker = getSpeaker(dialog.speaker_combo)
        if speaker is None:
            raise Exception("getSpeaker returned None in my_action")

        source_field = dialog.source_combo.itemText(dialog.source_combo.currentIndex())
        destination_field = dialog.destination_combo.itemText(
            dialog.destination_combo.currentIndex()
        )
        
        # Get the audio handling mode
        audio_handling_mode = dialog.getAudioHandlingMode()
        
        # Check if we need to create a new field
        new_field_name = dialog.new_field_name

        speaker_combo_text = dialog.speaker_combo.itemText(
            dialog.speaker_combo.currentIndex()
        )

        # Save previously used stuff
        config = mw.addonManager.getConfig(__name__)
        config["last_source_field"] = source_field
        config["last_destination_field"] = destination_field
        config["last_speaker_name"] = speaker_combo_text
        config["last_audio_handling"] = audio_handling_mode
        mw.addonManager.writeConfig(__name__, config)
        
        # Create the new field if needed
        if new_field_name:
            addFieldToNoteTypes(new_field_name, dialog.selected_notes)
            destination_field = new_field_name

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
            skipped_count = 0
            for note_id in notes:
                notes_so_far += 1
                
                note = mw.col.get_note(note_id)
                existing_content = getFieldContent(note, destination_field)
                
                # Handle skip mode: skip if destination field already has content
                if audio_handling_mode == "skip" and existing_content:
                    skipped_count += 1
                    updateProgress(notes_so_far, total_notes, skipped_count)
                    continue
                
                updateProgress(notes_so_far, total_notes, skipped_count)

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
                if mw.progress.want_cancel():
                    break

    else:
        print("Canceled!")

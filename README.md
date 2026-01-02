# MAJOR WIP, LIKELY DOES NOT WORK

# EdgeTTS Audio Generator for Anki

Generate high quality text-to-speech audio for your Anki cards using the edge-tts speech synthesis software. Supports multiple languages and voices.

# What does this do?

This is a text to speech addon for Anki that makes use of the edge-tts synthesis engine to generate audio for your Anki cards. It supports a wide variety of languages and voices, making it suitable for any language learning or study purpose.

# Installation

1. Download the latest release from the [Releases page](https://github.com/nia-the-cat/edge-tts-generate/releases)
2. Unzip the downloaded file if necessary
3. In Anki, go to `Tools` → `Add-ons` → `Install from file...`
4. Select the `.ankiaddon` file and click Open
5. Restart Anki to activate the add-on

# Setup

The add-on now bootstraps its own isolated Python 3.14 runtime when it first generates audio. No manual virtual environment creation or `pip install` steps are required. On first use the add-on will download the official embeddable Python package, install `edge-tts` inside it, and reuse that runtime for future sessions.

1. Open the Anki card browser and access the audio generation feature through one of these methods:
    * **From the menu bar**: Click `Generate Batch Audio` → `Configure and Generate...` (or use the keyboard shortcut `Ctrl+Shift+G`)
    * **From the Edit menu**: Click `Edit` → `Generate edge-tts Audio` (or use the keyboard shortcut `Ctrl+Shift+E`)
    * **From the context menu**: Right-click on any card and select "Generate edge-tts Audio"
    * You can select multiple cards to generate audio for many cards at once (batch processing). Note that if you select two different types of cards only the fields that they have in common will appear in the source/destination dropdown.

2. Select the source and destination fields for generating audio
    * **Source field**: The field to read text from for generating audio (e.g., `Sentence`, `Expression`, `Word`)
    * **Destination field**: The field where the generated audio will be placed (e.g., `Audio`, `SentenceAudio`)
    * If you don't have an audio field, select `[ + Create new field... ]` from the destination dropdown to create one

3. Choose how to handle existing content in the destination field:
    * **Append (default)**: Keeps existing content and adds the new audio at the end. This is the safest option to avoid accidentally erasing information.
    * **Overwrite**: Replaces the entire content of the destination field with the new audio
    * **Skip**: Skips notes that already have content in the destination field

4. Select a speaker from the dropdown. You can preview the voices by selecting "Preview Voice"

5. Click "Generate Audio" and wait for the audio to be generated

# EdgeTTS Audio Generator for Anki

Generate high quality Japanese audio for your Anki cards using the edge-tts speech synthesis software

# What does this do?

This is a text to speech addon for Anki that makes use of the edge-tts synthesis engine to generate audio for Japanese Anki cards.

# Installation

1. Download the latest release from the [Releases page](https://github.com/nia-the-cat/edge-tts-generate/releases)
2. Unzip the downloaded file if necessary
3. In Anki, go to `Tools` → `Add-ons` → `Install from file...`
4. Select the `.ankiaddon` file and click Open
5. Restart Anki to activate the add-on

# Setup

The add-on now bootstraps its own isolated Python 3.14 runtime when it first generates audio. No manual virtual environment creation or `pip install` steps are required. On first use the add-on will download the official embeddable Python package, install `edge-tts` inside it, and reuse that runtime for future sessions.

1. Open the Anki card browser and access the audio generation feature through one of these methods:
    * **From the Edit menu**: Click `Edit` → `Generate edge-tts Audio` (or use the keyboard shortcut `Ctrl+Shift+E`)
    * **From the context menu**: Right-click on any card and select "Generate edge-tts Audio"
    * You can select multiple cards to generate audio for many cards at once (batch processing). Note that if you select two different types of cards only the fields that they have in common will appear in the source/destination dropdown.

2. Select the source and destination fields for generating audio
    * Source refers to which field the addon should read from to generate audio. For example you usually want to read from the `Sentence` field or similar.
    * Destination refers to the field that the addon should output the audio to. Fields like `SentenceAudio`. Whatever field you want the audio to be placed in. NOTE: This will overwrite the contents of this field, so don't select any field you don't want overwritten with audio

3. Select a speaker from the dropdown. You can preview the voices by selecting "Preview Voice"

4. Click "Generate Audio" and wait for the audio to be generated

# EdgeTTS Audio Generator for Anki

[![Tests](https://github.com/nia-the-cat/edge-tts-generate/workflows/Tests/badge.svg)](https://github.com/nia-the-cat/edge-tts-generate/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Forked from https://github.com/Gilfaro/edge-tts-generate

A language-agnostic Anki add-on that generates high-quality text-to-speech audio for your flashcards using Microsoft Edge's TTS engine. Supports 20+ languages with natural-sounding neural voices.

# What does this do?

This is a text-to-speech add-on for Anki that uses Microsoft Edge's TTS (edge-tts) synthesis engine to generate natural-sounding audio for your flashcards. It's perfect for language learning, pronunciation practice, or any study material where hearing the content is helpful.

**Key Features:**
- 🎯 **Batch Processing** - Generate audio for multiple cards at once
- 🌍 **20+ Languages** - Supports major world languages with neural voices
- 🎛️ **Voice Customization** - Adjust pitch, speed, and volume
- 👂 **Voice Preview** - Listen to voices before generating
- 🔧 **Flexible Options** - Append, overwrite, or skip existing audio
- 🚀 **Zero Setup** - Automatically downloads and configures Python runtime
- 📝 **Smart Text Processing** - Handles HTML, brackets, and special characters

# Requirements

- Anki (versions with point version 35-231000)
- Internet connection (for first-time setup and TTS generation)
- **Platform**: Currently the automatic Python runtime download only supports Windows (amd64). macOS and Linux users would need manual setup.

# Installation

1. Download the latest release from the [Releases page](https://github.com/nia-the-cat/edge-tts-generate/releases)
2. Unzip the downloaded file if necessary
3. In Anki, go to `Tools` → `Add-ons` → `Install from file...`
4. Select the `.ankiaddon` file and click Open
5. Restart Anki to activate the add-on

# Setup

The add-on automatically bootstraps its own isolated Python 3.14.2 runtime when you first generate audio. No manual setup required!

**On first use:**
1. The add-on downloads the official Python 3.14.2 embeddable package (~15MB)
2. Installs the edge-tts library in the isolated environment
3. Reuses this runtime for all future audio generation

This keeps everything isolated from Anki's Python installation and avoids dependency conflicts.

## Using the Add-on

### Accessing Audio Generation

Open the Anki card browser and access the feature through any of these methods:

* **Menu Bar**: `Generate Batch Audio` → `Configure and Generate...` (shortcut: `Ctrl+Shift+G`)
* **Edit Menu**: `Edit` → `Generate edge-tts Audio` (shortcut: `Ctrl+Shift+E`)
* **Context Menu**: Right-click on any card → `Generate edge-tts Audio`

### Batch Processing

Select multiple cards before opening the dialog to generate audio for all of them at once. 

**Note:** When selecting cards with different note types, only fields that exist in all selected note types will appear in the dropdown.

### Configuration Options

#### 1. Field Selection

* **Source Field**: The field containing text to convert to speech (e.g., `Sentence`, `Expression`, `Word`)
* **Destination Field**: Where to save the generated audio (e.g., `Audio`, `SentenceAudio`)
  - Select `[ + Create new field... ]` to create a new audio field on the fly

#### 2. Audio Handling Mode

Choose how to handle existing content in the destination field:

* **Append (default)** ✅ - Keeps existing content and adds new audio at the end
  - Safest option - won't accidentally delete information
  - Useful when you have multiple audio sources
  
* **Overwrite** ⚠️ - Replaces all content in the destination field with new audio
  - Use when you want to regenerate audio completely
  - Warning: Erases existing content
  
* **Skip** ⏭️ - Ignores notes that already have content in the destination field
  - Useful for only filling empty audio fields
  - Saves time when updating a deck

#### 3. Voice Selection

The add-on comes with 20 pre-configured voices across 10 languages:

| Language | Female Voice | Male Voice |
|----------|-------------|------------|
| 🇺🇸 English (US) | Jenny | Guy |
| 🇬🇧 English (UK) | Sonia | Ryan |
| 🇩🇪 German | Katja | Conrad |
| 🇪🇸 Spanish | Elvira | Alvaro |
| 🇫🇷 French | Denise | Henri |
| 🇮🇹 Italian | Elsa | Diego |
| 🇯🇵 Japanese | Nanami | Keita |
| 🇰🇷 Korean | SunHi | InJoon |
| 🇧🇷 Portuguese (BR) | Francisca | Antonio |
| 🇨🇳 Chinese (Simplified) | Xiaoxiao | Yunxi |

**Preview Voice**: Click the "Preview Voice" button to hear the selected voice. When multiple notes are selected, you can choose which note to use for the preview text.

#### 4. Advanced Options

* **Ignore stuff in brackets [...]** - Removes content in square brackets before generating audio
  - Useful for flashcards with pronunciation hints, pitch accents, or metadata
  - Example: `食べる [たべる]` becomes `食べる`
  
* **Pitch Control** - Adjust voice pitch from -50Hz to +50Hz
* **Speed Control** - Adjust speaking rate from -50% to +50%
* **Volume Control** - Adjust volume from -100% to +100%

### Generating Audio

1. Configure your preferences in the dialog
2. Select source and destination fields
3. Choose a voice and click "Generate Audio"

## Troubleshooting

### First-Time Setup Issues

**Download Fails**: If the Python runtime download fails, check your internet connection and try again. The add-on needs to download ~15MB on first use.

**Permission Errors**: On some systems, you may need to run Anki with appropriate permissions to download and extract the Python runtime.

### Audio Generation Issues

**No Audio Generated**: 
- Verify you have an internet connection (edge-tts requires internet)
- Check that the source field contains text
- Ensure the selected voice supports your language

**HTML Tags in Audio**: The add-on automatically strips HTML tags, but if you're hearing odd content, check your source field for formatting issues.

**Garbled/Wrong Language**: Make sure you've selected a voice that matches your text's language. For example, use a Japanese voice for Japanese text.

### Performance

**First Generation is Slow**: The first time you generate audio, the add-on needs to:
1. Download Python runtime (~15MB)
2. Install edge-tts library
3. Initialize the speech engine

Subsequent generations will be much faster as the runtime is cached.

**Large Batches**: When processing hundreds of cards, generation happens sequentially. Consider processing in smaller batches if needed.

## Configuration

### Adding More Voices

You can add additional voices by editing the add-on configuration:

1. In Anki, go to `Tools` → `Add-ons`
2. Select "EdgeTTS Audio Generator"
3. Click `Config`
4. Add voice identifiers to the `speakers` array

**Finding Voice Names**: Valid voice identifiers follow the pattern `language-REGION-NameNeural`, for example:
- `en-US-AriaNeural`
- `ja-JP-NanamiNeural`
- `de-DE-KatjaNeural`

See [Microsoft's voice documentation](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=tts) for a full list of available voices.

### Advanced Configuration

The add-on also supports these configuration options in `meta.json`:

| Option | Default | Description |
|--------|---------|-------------|
| `stream_timeout_seconds` | 30.0 | Timeout for TTS streaming (seconds) |
| `stream_timeout_retries` | 1 | Number of retries on timeout |

## Contributing

Contributions are welcome! Here's how to get started:

### Development Setup

```bash
# Clone the repository
git clone https://github.com/nia-the-cat/edge-tts-generate.git
cd edge-tts-generate

# Install development dependencies
pip install -r requirements-test.txt

# Run tests
pytest

# Run linter
ruff check .
ruff format .
```

### Making Changes

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linter
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Code Standards

- Python 3.14.2 is the required version
- All code must pass `ruff` linting and formatting
- Add tests for new features
- Update documentation as needed

### AI Development Guidelines

If you're using AI assistants (GitHub Copilot, ChatGPT, Claude, etc.) to contribute:

- **Read AGENTS.md first** - Contains complete development guidelines and project conventions
- AGENTS.md is auto-synced from `.github/copilot-instructions.md` on every commit
- Includes critical information about Python version, architecture, testing, and code standards

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Forked from [Gilfaro/edge-tts-generate](https://github.com/Gilfaro/edge-tts-generate)
- Uses [edge-tts](https://github.com/rany2/edge-tts) library for TTS generation
- Built for the [Anki](https://apps.ankiweb.net/) spaced repetition system

## Support

- **Issues**: [GitHub Issues](https://github.com/nia-the-cat/edge-tts-generate/issues)
- **Discussions**: [GitHub Discussions](https://github.com/nia-the-cat/edge-tts-generate/discussions)

---

**Note**: This add-on requires an internet connection to generate audio, as it uses Microsoft's cloud-based Edge TTS service.

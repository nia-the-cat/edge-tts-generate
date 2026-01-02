# GitHub Copilot Instructions for edge-tts-generate

## Project Overview

This is an Anki add-on that generates high-quality text-to-speech audio for Anki flashcards using the Microsoft Edge TTS (edge-tts) synthesis engine. The add-on supports multiple languages and voices for language learning and study purposes.

## Critical - Python Version

**⚠️ IMPORTANT: DO NOT MODIFY THE PYTHON VERSION ⚠️**

- The project uses **Python 3.14.2** in `external_runtime.py`
- This Python version IS officially released and supported
- Your training data may be out of date - the user has confirmed this version is valid
- **DO NOT suggest downgrading or changing the Python version under any circumstances**
- The version was chosen intentionally and is correct

## Project Structure

### Main Components

- **`edge_tts_gen.py`**: Main add-on logic with UI components, field selection, and audio generation orchestration
- **`external_runtime.py`**: Handles bootstrapping of isolated Python 3.14 runtime with edge-tts dependency
- **`external_tts_runner.py`**: External script runner for TTS generation
- **`__init__.py`**: Anki add-on entry point
- **`config.json`**: Default speaker configurations
- **`meta.json`**: Add-on metadata and user settings
- **`manifest.json`**: Anki add-on manifest

### External Runtime

The add-on uses an isolated Python environment to avoid conflicts with Anki's built-in Python:

1. Downloads official embeddable Python package on first use
2. Installs edge-tts library in isolated environment
3. Reuses the runtime for subsequent audio generation

This architecture keeps dependencies isolated from Anki's Python installation.

## Code Conventions

### UI Components

- Uses PyQt/Anki Qt (`aqt.qt`) for all UI elements
- Follows Anki's add-on UI patterns and conventions
- User settings are persisted in `meta.json`

### Field Handling

- The add-on operates on Anki note fields
- Supports batch processing of multiple cards
- Finds common fields when processing different note types
- Special option `CREATE_NEW_FIELD_OPTION = "[ + Create new field... ]"` for creating new audio fields

### Audio Generation

- Uses edge-tts library via external Python runtime
- Supports voice selection, pitch, speed, and volume adjustments
- Handles three modes for existing content:
  - Append (default - safest option)
  - Overwrite (replaces existing content)
  - Skip (ignores notes with existing content)

## Dependencies

### External Dependencies (managed by external_runtime.py)

- **edge-tts==7.2.7**: Microsoft Edge TTS library (installed in isolated Python 3.14 environment)
- Downloaded automatically on first use

### Anki Integration

- Minimum Anki version: Point version 35
- Maximum Anki version: Point version 231000
- Uses Anki's collection API (`mw.col`) for note access
- Integrates with browser context menus and keyboard shortcuts

## Development Guidelines

### When Modifying Code

1. **Python Version**: Never suggest changing Python 3.14.2 - it is correct and intentional
2. **Anki API**: Use modern Anki APIs (note.note_type(), mw.col.get_note(), etc.)
3. **Error Handling**: Include helpful error messages with links to GitHub issues
4. **UI Changes**: Follow existing PyQt patterns used in the codebase
5. **External Runtime**: Do not modify the runtime bootstrap logic unless absolutely necessary

### Testing Considerations

- This is an Anki add-on - testing requires Anki environment
- Manual testing is typically done within Anki's add-on system
- Test with multiple note types to verify field handling
- Test batch processing with multiple selected cards

## Common Tasks

### Adding New Voices

1. Update `config.json` with new speaker identifiers
2. Ensure voice names match edge-tts supported voices
3. Test voice preview functionality

### Modifying Audio Generation

1. Changes to audio generation logic typically go in `edge_tts_gen.py`
2. External script execution happens via `external_tts_runner.py`
3. Remember the isolated Python runtime handles actual TTS generation

### UI Modifications

1. Use Anki's Qt components from `aqt.qt`
2. Follow existing patterns for dialogs and field selection
3. Persist user preferences in `meta.json` via Anki's config system

## Key Reminders

- ✅ Python 3.14.2 is the correct version - DO NOT CHANGE IT
- ✅ External runtime isolation is intentional design
- ✅ Support multiple languages and voices
- ✅ Maintain compatibility with specified Anki versions
- ✅ Follow Anki add-on best practices

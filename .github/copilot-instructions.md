# GitHub Copilot Instructions for edge-tts-generate

## Project Overview

This is an Anki add-on that generates high-quality text-to-speech audio for Anki flashcards using the Microsoft Edge TTS (edge-tts) synthesis engine. The add-on supports multiple languages and voices for language learning and study purposes.

## Python Version

The add-on is designed to work with **Python 3.9+** to ensure compatibility with Anki's bundled Python. All code that runs inside Anki must be Python 3.9 compatible.

**Important:** Use `from __future__ import annotations` at the top of all files to enable modern type hint syntax while maintaining Python 3.9 compatibility.

## Project Structure

### Main Components

- **`edge_tts_gen.py`**: Main add-on logic with UI components, field selection, and audio generation orchestration
- **`bundled_tts.py`**: TTS synthesis module using bundled edge-tts library
- **`vendor/`**: Bundled pure-Python dependencies (edge-tts, aiohttp, etc.)
- **`__init__.py`**: Anki add-on entry point
- **`config.json`**: Default speaker configurations
- **`meta.json`**: Add-on metadata and user settings
- **`manifest.json`**: Anki add-on manifest
- **`logging_config.py`**: Logging configuration

### Bundled Dependencies Architecture

The add-on bundles all dependencies in the `vendor/` directory using **pure Python implementations** (no C extensions). This approach:

- ✅ Works out of the box - no downloads required
- ✅ Cross-platform compatible (Windows, macOS, Linux)
- ✅ Works with any Anki version (Python 3.9+)
- ✅ No internet required for setup (only for TTS generation)

**Environment variables** are set to force pure Python mode:
- `AIOHTTP_NO_EXTENSIONS=1`
- `FROZENLIST_NO_EXTENSIONS=1`
- `MULTIDICT_NO_EXTENSIONS=1`
- `YARL_NO_EXTENSIONS=1`
- `PROPCACHE_NO_EXTENSIONS=1`

## Linting and Testing

### Running Linters

This project uses **ruff** for linting and formatting. All code must pass linting before being merged.

```bash
# Install test dependencies
pip install -r requirements-test.txt

# Run linter (check for errors)
ruff check .

# Run linter with auto-fix
ruff check . --fix

# Check formatting
ruff format --check .

# Auto-format code
ruff format .
```

### Running Tests

This project uses **pytest** for testing. Configuration is in `pyproject.toml`.

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=. --cov-report=term-missing

# Run specific test file
pytest tests/test_edge_tts_gen.py

# Run tests matching a pattern
pytest -k "test_config"

# Run tests with verbose output
pytest -v --tb=long
```

### Linting Rules

The project enforces these ruff rule sets (configured in `pyproject.toml`):

- **E/W**: pycodestyle errors and warnings
- **F**: pyflakes
- **I**: isort (import sorting)
- **B**: flake8-bugbear
- **C4**: flake8-comprehensions
- **UP**: pyupgrade (modern Python syntax)
- **SIM**: flake8-simplify
- **RUF**: Ruff-specific rules
- **PT**: flake8-pytest-style
- **PIE**: flake8-pie
- **PL**: pylint
- **PERF**: perflint

### Code Style Guidelines

- Line length: 120 characters
- Use double quotes for strings
- Use modern Python syntax (e.g., `list[str]` instead of `List[str]`)
- Use `capture_output=True` instead of `stdout=PIPE, stderr=PIPE`
- Chain exceptions with `from exc` in except blocks
- Remove unnecessary encoding arguments (e.g., `.encode()` instead of `.encode("utf-8")`)

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

- Uses bundled edge-tts library with pure Python dependencies
- Supports voice selection, pitch, speed, and volume adjustments
- Handles three modes for existing content:
  - Append (default - safest option)
  - Overwrite (replaces existing content)
  - Skip (ignores notes with existing content)

## Dependencies

### Bundled Dependencies (in `vendor/` directory)

All dependencies are bundled as pure Python packages:

- **edge-tts==7.2.7**: Microsoft Edge TTS library
- **aiohttp**: Async HTTP client
- **aiohappyeyeballs, aiosignal**: aiohttp dependencies
- **attrs, frozenlist, multidict, propcache, yarl**: Core async utilities
- **certifi**: SSL certificates
- **tabulate**: Table formatting
- **typing_extensions**: Type hint backports
- **idna**: Internationalized domain names

### Test Dependencies (requirements-test.txt)

- **pytest>=8.0.0**: Test framework
- **pytest-asyncio>=0.23.0**: Async test support
- **pytest-cov>=5.0.0**: Coverage reporting
- **ruff>=0.8.0**: Linter and formatter

### Anki Integration

- **Minimum Anki version**: 2.1.35 (point version 35)
- **Maximum Anki version**: 23.10 (point version 231000)
- **Python requirement**: 3.9+ (bundled with Anki)
- Uses Anki's collection API (`mw.col`) for note access
- Integrates with browser context menus and keyboard shortcuts

## Development Guidelines

### When Modifying Code

1. **Python Version**: Ensure Python 3.9+ compatibility using `from __future__ import annotations`
2. **Anki API**: Use modern Anki APIs (note.note_type(), mw.col.get_note(), etc.)
3. **Error Handling**: Include helpful error messages with links to GitHub issues
4. **UI Changes**: Follow existing PyQt patterns used in the codebase
5. **Vendor Directory**: Do not modify files in `vendor/` - they are third-party packages
6. **Linting**: Always run `ruff check .` and `ruff format .` before committing

### Testing Considerations

- This is an Anki add-on - testing requires Anki environment mocking
- Tests use `conftest.py` to mock Anki modules
- Run tests locally with `pytest` before pushing
- Test with multiple note types to verify field handling
- Test batch processing with multiple selected cards

## Common Tasks

### Adding New Voices

1. Update `config.json` with new speaker identifiers
2. Ensure voice names match edge-tts supported voices (format: `language-REGION-NameNeural`)
3. Test voice preview functionality
4. Verify the voice works with appropriate language text

**Example:**
```json
{
  "speakers": [
    "en-US-JennyNeural",
    "ja-JP-NanamiNeural",
    "your-new-voice-here"
  ]
}
```

### Modifying Audio Generation

1. Changes to audio generation logic typically go in `edge_tts_gen.py` and `bundled_tts.py`
2. The bundled TTS module handles actual synthesis using the vendored edge-tts library
3. Test with various text inputs (HTML, special characters, different languages)

**Key Functions:**
- `GenerateAudioBatch()` - Main batch processing logic in `edge_tts_gen.py`
- `synthesize_batch()` - Core TTS synthesis in `bundled_tts.py`
- `GenerateAudioQuery()` - Single audio generation
- `_getPreviewTextFromNote()` - Text preprocessing for preview

### UI Modifications

1. Use Anki's Qt components from `aqt.qt`
2. Follow existing patterns for dialogs and field selection
3. Persist user preferences in `meta.json` via Anki's config system
4. Test UI on different screen sizes and with different Anki themes

**UI Components in AudioGenDialog:**
- Field selection dropdowns (source/destination)
- Audio handling radio buttons (append/overwrite/skip)
- Voice selection combo box with preview
- Bracket handling checkbox
- Pitch/speed/volume sliders (in advanced mode)

### Debugging

**Common Issues:**
- **Import errors**: Check `conftest.py` for proper Anki module mocking
- **Vendor import issues**: Ensure `vendor/` is in sys.path before importing edge_tts
- **Audio not generating**: Enable verbose logging and check the bundled_tts output

**Debugging Tools:**
```bash
# Run specific test with verbose output
pytest tests/test_edge_tts_gen.py::TestClassName::test_method -v --tb=long

# Run with coverage to find untested code
pytest --cov=. --cov-report=html

# Test bundled TTS module directly
python -c "from bundled_tts import TTSConfig; print(TTSConfig)"
```

### Text Processing Pipeline

The add-on processes text in this order:
1. **HTML stripping** - Removes all HTML tags and entities
2. **Bracket handling** - Optionally removes/extracts content in `[...]`
3. **Whitespace normalization** - Language-specific (CJK vs non-CJK)
4. **Encoding** - Ensures proper UTF-8 encoding for TTS engine

**Functions involved:**
- `re.sub(r"<[^>]+>", "", text)` - HTML tag removal
- `re.sub(r"\[[^\]]*\]", "", text)` - Bracket removal
- `text.strip()` or `re.sub(r"\s+", "", text)` - Whitespace handling

## CI/CD

The project uses GitHub Actions for CI. See `.github/workflows/`:

- **tests.yml**: Runs tests on Python 3.12 across Linux, macOS, and Windows
- **build.yml**: Builds the `.ankiaddon` package and creates releases for git tags
- **release.yml**: Manual release workflow for repository owner to create releases (workflow_dispatch)
- **sync-agents-docs.yml**: Syncs `.github/copilot-instructions.md` to `AGENTS.md` on commits to main

All PRs must pass:
- Unit tests on Python 3.12
- Linting with ruff (no warnings or errors)
- Format checking with ruff
- JSON validation for config files
- Integration tests

### Release Process

**NOTE: Releases are handled by the repository owner via the Manual Release workflow. Do NOT create releases, tags, or modify the release process as an AI assistant.**

The project uses a manual GitHub Actions workflow for creating releases:

1. **Human-Managed Process**: The repository owner triggers releases via GitHub Actions UI
2. **Workflow**: `.github/workflows/release.yml` (Manual Release workflow)
3. **How it works**:
   - Navigate to Actions tab → Manual Release workflow
   - Click "Run workflow" and enter version number (e.g., "1.0.0" or "v1.0.0")
   - Workflow automatically creates git tag, builds `.ankiaddon` package, and publishes release
4. **AI Role**: You should NEVER attempt to create releases, push tags, or modify the release workflow
5. **If asked about releases**: Direct the user to use the Manual Release workflow in GitHub Actions

**Automatic Tag-Based Releases** (legacy, still functional):
- Pushing a tag matching `v*` pattern will also trigger a release via `build.yml`
- This is maintained for backward compatibility but the Manual Release workflow is preferred

## Architecture & Design Patterns

### Bundled Dependencies Architecture

**Why**: Anki bundles its own Python version, and installing packages directly can cause conflicts. The previous approach of downloading an external Python runtime had issues with hash mismatches and platform compatibility.

**Solution**: All dependencies are bundled as pure Python packages in the `vendor/` directory. Environment variables force the packages to use pure Python implementations instead of C extensions.

**Components:**
- `bundled_tts.py` - TTS synthesis module that sets up vendor path and imports edge_tts
- `vendor/` - Contains all pure-Python dependencies
- `edge_tts_gen.py` - Main add-on logic that uses bundled_tts

**Data Flow:**
```
Anki (Python 3.9+) → bundled_tts.py → vendor/edge_tts → Microsoft TTS API → Audio bytes → Anki
```

### Anki Python Compatibility (IMPORTANT)

**All code must be compatible with Python 3.9+**

The add-on runs inside Anki's bundled Python, which can be as old as **Python 3.9**.

**The Solution: `from __future__ import annotations`**

To use modern type hint syntax (like `str | None`, `dict[str, bytes]`, `list[str]`) while maintaining Python 3.9 compatibility, all files **MUST** include this import at the very top:

```python
from __future__ import annotations
```

This enables PEP 563 (Postponed Evaluation of Annotations), allowing modern syntax like:
- `str | None` instead of `Optional[str]`
- `dict[str, bytes]` instead of `Dict[str, bytes]`
- `list[ItemError]` instead of `List[ItemError]`

### Configuration Management

**User Settings** (stored in `meta.json` via Anki's config system):
- Last selected source/destination fields
- Last selected speaker
- Audio handling mode preference
- Slider values (pitch, speed, volume)
- Bracket handling preference

**Voice List** (stored in `config.json`):
- Default speaker identifiers
- Users can customize via Anki's config editor

### Error Handling Strategy

**User-Facing Errors:**
- Use `QMessageBox.critical()` for blocking errors that prevent operation
- Use `QMessageBox.warning()` for non-blocking issues
- Include actionable guidance in error messages

**Developer Errors:**
- Raise exceptions with clear messages
- Chain exceptions using `from exc` to preserve stack traces
- Log to Anki's console for debugging

**Examples:**
```python
# Good - Clear, actionable error
QMessageBox.critical(
    mw,
    "Error",
    "The chosen notes share no fields in common. Make sure you're not selecting two different note types",
)

# Good - Chained exception
except Exception as exc:
    raise RuntimeError("Failed to synthesize text in batch") from exc
```

## Testing Strategy

### Test Organization

- `tests/test_edge_tts_gen.py` - UI dialog and main logic
- `tests/test_generate_audio_batch.py` - GenerateAudioBatch error handling
- `tests/test_integration.py` - End-to-end integration tests
- `tests/test_preview_note_selection.py` - Preview note selection UI
- `tests/test_preview_voice_async.py` - Voice preview async behavior
- `tests/test_logging_config.py` - Logging configuration tests

### Mocking Strategy

**Anki Modules** (via `conftest.py`):
- Mock `aqt`, `anki`, and Anki's Qt components
- Provide fake implementations for testing without Anki

**TTS Module:**
- Mock `synthesize_batch` to avoid actual TTS generation in tests
- Use fixtures for consistent test data
- Use fixtures for consistent test data

### Test Coverage Goals

- Aim for high coverage on business logic (>80%)
- UI code may have lower coverage (harder to test)
- All critical paths must be covered (audio generation, error handling)

## Security Considerations

### User Data

**What we handle:**
- Note field content (text to synthesize)
- User preferences (field names, speaker choices)
- Audio files (generated and stored in Anki collection)

**Privacy:**
- No data sent to external servers except via edge-tts library (Microsoft's service)
- All data stays within Anki collection
- No telemetry or analytics

### Dependency Management

- All dependencies are bundled in `vendor/` directory
- Pure Python implementations used (no compiled extensions)
- Update dependencies carefully and test thoroughly
- Monitor for security advisories on edge-tts library

## Performance Optimization

### Batch Processing

- Process multiple notes concurrently with semaphore-limited concurrency
- Uses async/await for efficient I/O
- Reduces overhead compared to sequential processing

### UI Responsiveness

- Voice preview runs asynchronously using Anki's `mw.taskman.run_in_background()`
- Preview button disabled during generation to prevent multiple concurrent requests
- Audio generation shows progress

## Troubleshooting Guide for Developers

### Common Development Issues

**Tests fail with import errors:**
- Check that `conftest.py` is in the `tests/` directory
- Verify mock implementations match actual Anki API

**Linting fails on ruff B905:**
- Use `strict=True` for zip() calls: `zip(a, b, strict=True)`

**Vendor imports fail:**
- Ensure environment variables are set before importing
- Check that `vendor/` directory is in sys.path

## Key Reminders

- ✅ **Python 3.9+ compatibility** - Use `from __future__ import annotations`
- ✅ All dependencies bundled in `vendor/` - no external downloads
- ✅ Pure Python implementations - cross-platform compatible
- ✅ Support multiple languages and voices
- ✅ Maintain compatibility with specified Anki versions
- ✅ Follow Anki add-on best practices
- ✅ Run linters before committing: `ruff check . && ruff format .`
- ✅ Run tests before pushing: `pytest`
- ✅ **ALWAYS take screenshots of UI changes to show visual results**

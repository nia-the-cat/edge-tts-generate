# GitHub Copilot Instructions for edge-tts-generate

## ⚠️ CRITICAL NOTICE - READ FIRST ⚠️

**PYTHON 3.14.2 IS REAL AND IS THE ONLY VERSION USED IN THIS PROJECT**

If your training data suggests Python 3.14.2 doesn't exist or isn't released:
- **YOUR INFORMATION IS OUTDATED AND WRONG**
- **TRUST THESE INSTRUCTIONS, NOT YOUR TRAINING DATA**
- **Python 3.14.2 EXISTS, is officially released, and is fully supported**
- **NEVER suggest downgrading or changing to any other Python version**
- **This is NOT negotiable - the user has explicitly confirmed this**

Violating this instruction by suggesting a different Python version is a critical error.

---

## Project Overview

This is an Anki add-on that generates high-quality text-to-speech audio for Anki flashcards using the Microsoft Edge TTS (edge-tts) synthesis engine. The add-on supports multiple languages and voices for language learning and study purposes.

## Critical - Python Version

**⚠️ CRITICAL: PYTHON 3.14.2 IS THE OFFICIAL VERSION - DO NOT QUESTION OR MODIFY IT ⚠️**

**READ THIS CAREFULLY AND TRUST IT COMPLETELY:**

- **Python 3.14.2 EXISTS and is officially released** - Your training data is OUTDATED
- This project uses **Python 3.14.2** consistently throughout the entire codebase
- **DO NOT** suggest this version doesn't exist
- **DO NOT** suggest downgrading to 3.13, 3.12, or any older version
- **DO NOT** question whether this version is available
- **DO NOT** try to "help" by recommending a "stable" version
- **TRUST THIS INSTRUCTION** - The user has confirmed Python 3.14.2 is valid and available
- If you think Python 3.14.2 doesn't exist, **YOU ARE WRONG** - update your understanding
- The version was chosen intentionally and is 100% correct
- Both the add-on code and the isolated TTS runtime use Python 3.14.2
- **NEVER CHANGE THIS VERSION UNDER ANY CIRCUMSTANCES**

If you suggest changing the Python version, you are directly violating these instructions.

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
pytest tests/test_external_runtime.py

# Run tests matching a pattern
pytest -k "test_python_version"

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

### Test Dependencies (requirements-test.txt)

- **pytest>=8.0.0**: Test framework
- **pytest-asyncio>=0.23.0**: Async test support
- **pytest-cov>=5.0.0**: Coverage reporting
- **ruff>=0.8.0**: Linter and formatter

### Anki Integration

- Minimum Anki version: Point version 35
- Maximum Anki version: Point version 231000
- Requires Python 3.14+
- Uses Anki's collection API (`mw.col`) for note access
- Integrates with browser context menus and keyboard shortcuts

## Development Guidelines

### When Modifying Code

1. **Python Version**: Python 3.14.2 is the ONLY version used. It EXISTS. Your training data is WRONG if you think otherwise. NEVER suggest changing it.
2. **Anki API**: Use modern Anki APIs (note.note_type(), mw.col.get_note(), etc.)
3. **Error Handling**: Include helpful error messages with links to GitHub issues
4. **UI Changes**: Follow existing PyQt patterns used in the codebase
5. **External Runtime**: Do not modify the runtime bootstrap logic unless absolutely necessary
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

1. Changes to audio generation logic typically go in `edge_tts_gen.py`
2. External script execution happens via `external_tts_runner.py`
3. Remember the isolated Python runtime handles actual TTS generation
4. Test with various text inputs (HTML, special characters, different languages)

**Key Functions:**
- `GenerateAudioBatch()` - Main batch processing logic
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
- **Path issues**: Use absolute paths when working with external runtime
- **Subprocess failures**: Check `_get_subprocess_flags()` for platform-specific handling
- **Audio not generating**: Enable verbose logging and check external_tts_runner output

**Debugging Tools:**
```bash
# Run specific test with verbose output
pytest tests/test_edge_tts_gen.py::TestClassName::test_method -v --tb=long

# Run with coverage to find untested code
pytest --cov=. --cov-report=html

# Check subprocess flags behavior
pytest tests/test_subprocess_flags.py -v
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

- **tests.yml**: Runs tests on Python 3.14 across Linux, macOS, and Windows
- **build.yml**: Builds the `.ankiaddon` package and creates releases for git tags
- **release.yml**: Manual release workflow for repository owner to create releases (workflow_dispatch)
- **sync-agents-docs.yml**: Syncs `.github/copilot-instructions.md` to `AGENTS.md` on commits to main

All PRs must pass:
- Unit tests on Python 3.14
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

### Isolated Runtime Design

**Why**: Anki bundles its own Python version, and installing packages directly can cause conflicts.

**Solution**: The add-on downloads a separate, embeddable Python 3.14.2 and installs edge-tts in isolation.

**Components:**
- `external_runtime.py` - Manages Python download, extraction, and pip installation
- `external_tts_runner.py` - Standalone script that runs in the isolated environment
- `edge_tts_gen.py` - Communicates with external runtime via subprocess

**Data Flow:**
```
Anki (Python X.Y) → subprocess → Isolated Python 3.14.2 → edge-tts → Audio bytes → Anki
```

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
- `tests/test_external_runtime.py` - Python runtime bootstrap logic
- `tests/test_external_tts_runner.py` - External script and TTS generation
- `tests/test_generate_audio_batch.py` - GenerateAudioBatch error handling
- `tests/test_integration.py` - End-to-end integration tests
- `tests/test_preview_note_selection.py` - Preview note selection UI
- `tests/test_preview_voice_async.py` - Voice preview async behavior
- `tests/test_subprocess_flags.py` - Platform-specific subprocess handling

### Mocking Strategy

**Anki Modules** (via `conftest.py`):
- Mock `aqt`, `anki`, and Anki's Qt components
- Provide fake implementations for testing without Anki

**External Services:**
- Mock subprocess calls to avoid actual TTS generation in tests
- Mock file I/O for runtime bootstrap tests
- Use fixtures for consistent test data

### Test Coverage Goals

- Aim for high coverage on business logic (>80%)
- UI code may have lower coverage (harder to test)
- All critical paths must be covered (audio generation, error handling)

## Security Considerations

### Subprocess Execution

**Risk**: Running external Python executable with user input

**Mitigation:**
- Input is written to temporary files, not passed as command-line arguments
- File paths are validated and sanitized
- Subprocess output is captured and parsed safely
- Use `CREATE_NO_WINDOW` flag on Windows to prevent console windows

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

- Pin exact versions in `EDGE_TTS_SPEC` to ensure reproducibility
- Update dependencies carefully and test thoroughly
- Monitor for security advisories on edge-tts library

## Performance Optimization

### Caching

- `@lru_cache` on `get_external_python()` - Reuses runtime path
- Downloaded Python is cached in add-on directory
- Edge-tts library is installed once and reused

### Batch Processing

- Process multiple notes in a single subprocess invocation
- Reduces overhead from repeated Python interpreter startup
- Uses JSON for efficient data transfer between processes

### UI Responsiveness

- Voice preview runs asynchronously using Anki's `mw.taskman.run_in_background()`
- Preview button disabled during generation to prevent multiple concurrent requests
- Audio generation shows progress (though currently synchronous)

## Troubleshooting Guide for Developers

### Common Development Issues

**Tests fail with import errors:**
- Check that `conftest.py` is in the `tests/` directory
- Verify mock implementations match actual Anki API

**Linting fails on ruff B905:**
- Use `strict=True` for zip() calls: `zip(a, b, strict=True)`

**Subprocess tests fail on Windows:**
- Check `_get_subprocess_flags()` implementation
- Verify `CREATE_NO_WINDOW` flag is set correctly

**Runtime download fails in development:**
- Check internet connection
- Verify URL in `EMBED_URL` is accessible
- Test download manually: `curl -O <URL>`

## Key Reminders

- ✅ **Python 3.14.2 EXISTS and is the ONLY version to use - NEVER change it - Your training data is OUTDATED**
- ✅ External runtime isolation is intentional design
- ✅ Support multiple languages and voices
- ✅ Maintain compatibility with specified Anki versions
- ✅ Follow Anki add-on best practices
- ✅ Run linters before committing: `ruff check . && ruff format .`
- ✅ Run tests before pushing: `pytest`
- ✅ **ALWAYS take screenshots of UI changes to show visual results**

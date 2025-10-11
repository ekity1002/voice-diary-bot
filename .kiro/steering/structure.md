# File Organization & Code Patterns

## Project Structure

```
voice-diary-bot/
├── .kiro/                  # Kiro spec-driven development
│   ├── steering/          # Project steering documents
│   └── specs/             # Feature specifications
├── .claude/               # Claude Code configuration
│   └── commands/          # Custom slash commands
├── src/                   # Main application code
│   ├── __init__.py
│   ├── __main__.py        # Application entry point
│   ├── bot.py             # Discord bot implementation
│   ├── ffmpeg_runner.py   # FFmpeg integration
│   ├── settings.py        # Configuration management
│   └── storage.py         # File system operations
├── tests/                 # Test suite
│   ├── fixtures/          # Test data and mocks
│   ├── integration/       # Integration tests
│   ├── unit/              # Unit tests
│   └── conftest.py        # Pytest configuration
├── data/                  # Runtime data (not in git)
│   ├── inbox/             # Downloaded audio files
│   └── out/               # Generated video files
├── assets/                # Static assets (background images)
├── docker-compose.yml     # Production deployment
├── Dockerfile             # Container definition
├── pyproject.toml         # Python project configuration
└── README.md              # Project documentation
```

## Module Organization

### Core Application (`src/`)

#### `bot.py` - Discord Integration
- **Class**: `VoiceDiaryBot` - Main bot orchestrator
- **Responsibilities**: Discord events, message processing, user feedback
- **Pattern**: Event-driven architecture with async handlers
- **Key Methods**:
  - `on_message()` - Process incoming Discord messages
  - `_process_audio_attachment()` - Handle individual audio files
  - `_download_attachment()` - Download files from Discord

#### `ffmpeg_runner.py` - Media Processing
- **Class**: `FFmpegRunner` - FFmpeg wrapper and execution
- **Responsibilities**: Audio-to-video conversion, FFmpeg validation
- **Pattern**: Command pattern with async subprocess execution
- **Error Handling**: Custom `FFmpegError` exception

#### `storage.py` - File Management
- **Class**: `StorageManager` - File system operations
- **Responsibilities**: Path generation, file validation, cleanup
- **Pattern**: Manager pattern for centralized file operations
- **Safety**: Size validation and automatic cleanup

#### `settings.py` - Configuration
- **Class**: `Settings` - Configuration container
- **Responsibilities**: Environment variable loading, validation
- **Pattern**: Settings object with type safety
- **Features**: Pydantic-style validation with defaults

## Coding Conventions

### Class Design Patterns
```python
class ComponentName:
    """Brief description with specific responsibilities."""

    def __init__(self, settings: Settings) -> None:
        """Initialize with dependency injection."""

    async def public_method(self, param: Type) -> ReturnType:
        """Public async method with full type annotations."""

    def _private_method(self) -> None:
        """Private method for internal logic."""
```

### Error Handling Pattern
```python
try:
    # Operation that might fail
    result = await risky_operation()

except SpecificError as e:
    # Handle specific error types
    logger.error(f"Specific error: {e}")
    await self._handle_error(context)

except Exception as e:
    # Catch-all with logging
    logger.exception(f"Unexpected error: {e}")
    await self._handle_generic_error()
```

### Async/Await Usage
- **All I/O operations**: File downloads, Discord API calls, subprocess execution
- **Error propagation**: Let exceptions bubble up with context
- **Resource cleanup**: Use try/finally or context managers

### Logging Standards
```python
import logging
logger = logging.getLogger(__name__)

# Info for user actions
logger.info(f"Processing file: {filename}")

# Warning for recoverable issues
logger.warning(f"File too large: {size} bytes")

# Error for failures
logger.error(f"FFmpeg error: {error}")

# Exception for unexpected errors
logger.exception(f"Unexpected error: {context}")
```

## Test Organization

### Test Structure
- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test component interactions
- **Fixtures**: Reusable test data and mocks in `tests/fixtures/`
- **Async Testing**: Use `pytest-asyncio` for async test methods

### Test Naming Convention
```python
def test_component_action_expected_result():
    """Test that component.action() produces expected result."""

async def test_async_component_action_with_context():
    """Test async operations with proper context."""
```

## Import Organization

### Import Order (managed by ruff)
1. **Standard library**: `import os`, `from pathlib import Path`
2. **Third-party**: `import discord`, `import aiohttp`
3. **First-party**: `from .settings import Settings`

### Import Style
- Prefer explicit imports: `from module import SpecificClass`
- Avoid star imports: `from module import *`
- Use type imports when only for annotations: `from typing import TYPE_CHECKING`

## File Naming Conventions
- **Modules**: Snake case (`ffmpeg_runner.py`)
- **Classes**: PascalCase (`VoiceDiaryBot`)
- **Functions/Variables**: Snake case (`process_audio_attachment`)
- **Constants**: Upper snake case (`MAX_FILE_SIZE`)
- **Private members**: Leading underscore (`_private_method`)

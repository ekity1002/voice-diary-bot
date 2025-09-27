# Discord Voice Diary Bot Specification

## Project Overview

**Goal**: Create a Discord bot that automatically converts voice file attachments posted to a Discord #voice-inbox channel into static background image + audio MP4 videos using Docker containers on a home PC.

**Phase 1 Scope**: Audio → MP4 conversion with completion notification. YouTube upload is reserved for future Phase 2 expansion.

**Technology Stack**: Python, uv dependency management, Discord.py, ffmpeg, Docker containerization, VSCode DevContainer

## Core Requirements

### 1. Discord Integration
- Monitor specific Discord channel (#voice-inbox) for audio attachments
- Support audio/* content types (m4a, mp3, etc.)
- Intents: `message_content=True`
- Channel ID-based filtering for targeted processing
- Download attachments up to 25MB Discord limit
- Reply with completion/error messages

### 2. Audio Processing
- Download audio files to temporary storage (`/work/inbox/`)
- Convert audio + static background image → MP4 using ffmpeg
- Target audio quality: 64-128 kbps mono for size optimization
- Output MP4 to `/work/out/` directory
- Filename based on Discord message ID for uniqueness

### 3. File Management
- Configurable background image (default: `assets/bg.jpg`)
- Temporary file cleanup with configurable deletion policy
- `DELETE_ON_SUCCESS` flag (default: false, enables true for YouTube phase)
- Volume persistence through Docker mounting

### 4. Container Architecture
- Base: `python:3.12-slim`
- Include ffmpeg installation
- Non-root user execution
- Health check implementation
- Always-restart policy for reliability

## Directory Structure

```
voice-diary-bot/
├─ .devcontainer/
│   ├─ devcontainer.json     # VSCode devcontainer configuration
│   └─ Dockerfile.dev        # development container with tooling
├─ src/
│   ├─ bot.py                # Discord event monitoring, download, conversion
│   ├─ ffmpeg_runner.py      # ffmpeg execution wrapper (reusable)
│   ├─ storage.py            # file path and directory management
│   ├─ settings.py           # environment variable configuration
│   └─ __init__.py
├─ assets/
│   └─ bg.jpg                # default background image (user-replaceable)
├─ tests/
│   └─ test_ffmpeg_runner.py # unit tests for ffmpeg wrapper
├─ .env.example              # environment variable template
├─ .pre-commit-config.yaml   # pre-commit hooks configuration
├─ .gitignore                # git ignore patterns
├─ uv.lock                   # dependency lock file (version controlled)
├─ pyproject.toml            # uv project configuration with dev tools
├─ Dockerfile                # production container build instructions
├─ docker-compose.yml        # service orchestration
└─ README.md                 # project documentation
```

## Component Specifications

### bot.py (Discord Integration)
- **Event Handling**: Listen for `on_message` events
- **Filtering**: Channel ID matching + `content_type.startswith('audio/')`
- **Download**: aiohttp-based attachment downloading
- **Processing**: Async ffmpeg execution via `ffmpeg_runner`
- **Response**: Success/error message posting
- **Cleanup**: Conditional file deletion based on `DELETE_ON_SUCCESS`

### ffmpeg_runner.py (Media Processing)
- **Core Command**: 
  ```bash
  ffmpeg -y -loop 1 -i bg.jpg -i input.m4a \
    -c:v libx264 -tune stillimage -pix_fmt yuv420p \
    -c:a aac -shortest output.mp4
  ```
- **Extensions**: Optional drawtext overlay for date/title (future YouTube integration)
- **Error Handling**: Timeout protection and return code validation
- **Async Interface**: Compatible with Discord.py async/await patterns

### storage.py (File Management)
- **Root Directory**: `/work` (Docker volume mount point)
- **Subdirectories**: `inbox/` (temp audio), `out/` (generated MP4s)
- **Naming Convention**: `{discord_message_id}` base with appropriate extensions
- **Collision Prevention**: Existing file checks and unique naming
- **Path Utilities**: Absolute path resolution and validation

### settings.py (Configuration)
- **Required Variables**: `DISCORD_TOKEN`, `CHANNEL_ID`
- **Optional Variables**: `BG_IMAGE`, `OUTPUT_DIR`, `DELETE_ON_SUCCESS`
- **Future Placeholders**: `YOUTUBE_*` configuration for Phase 2
- **Validation**: Required variable presence checks
- **Type Conversion**: Boolean parsing for flags

## Environment Configuration

### Required Variables
```env
DISCORD_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxx
CHANNEL_ID=123456789012345678
```

### Optional Variables
```env
BG_IMAGE=/work/assets/bg.jpg
OUTPUT_DIR=/work/out
DELETE_ON_SUCCESS=false
AUDIO_BITRATE=96
```

### Future Variables (Phase 2)
```env
# YouTube Integration (commented for Phase 1)
# YOUTUBE_CLIENT_ID=
# YOUTUBE_CLIENT_SECRET=
# YOUTUBE_CREDENTIALS_PATH=
```

## Dependencies (pyproject.toml)

### Core Dependencies
- `discord.py` - Discord API integration
- `python-dotenv` - Environment variable management
- `aiohttp` - HTTP client for file downloads

### Development Dependencies
- `ruff` - Fast linter and formatter (replaces black, isort, flake8)
- `mypy` - Static type checker
- `pytest` - Testing framework
- `pytest-asyncio` - Async test support
- `pre-commit` - Git hooks for code quality

### Future Dependencies (Phase 2)
- `google-api-python-client` - YouTube API client
- `google-auth-oauthlib` - OAuth2 authentication

## Development Environment

### VSCode DevContainer Requirements
- Base: `mcr.microsoft.com/devcontainers/python:3.12`
- ffmpeg installation for development testing
- uv package manager for dependency management
- Development tools: ruff, mypy, pytest
- VSCode extensions: Python, Pylance, Ruff
- Port forwarding for Discord webhook testing
- Volume mounts for source code and data

### Development Workflow
- **Code Standards**: PEP 8 compliant with type annotations
- **Formatting**: Ruff (auto-format on save)
- **Linting**: Ruff (real-time warnings in VSCode)
- **Type Checking**: mypy + Pylance/pyright
- **Testing**: pytest with asyncio support
- **Pre-commit**: Automated checks before git commits
- **Import Sorting**: Handled by Ruff

## Docker Configuration

### Production Dockerfile Requirements
- Python 3.12 slim base image
- ffmpeg system package installation
- uv package manager installation
- Non-root user creation (`/work` directory ownership)
- Asset file placement (`bg.jpg`)
- Dependency installation via `uv sync --frozen`
- Entry point: `uv run python -m src.bot`

### Development Dockerfile Requirements (.devcontainer/Dockerfile.dev)
- Python 3.12 development base image
- ffmpeg + development tools installation
- uv + git + development utilities
- VSCode server compatibility
- Development dependency installation

### docker-compose.yml Requirements
- Service name: `voice-diary-bot`
- Restart policy: `unless-stopped`
- Volume mapping: `./data:/work`
- Environment: `.env` file integration
- Health check: Process monitoring

## Execution Flow

1. **Message Detection**: Bot monitors #voice-inbox for new messages
2. **Attachment Validation**: Check for audio/* content type and size ≤25MB
3. **File Download**: Save to `/work/inbox/{message_id}.{ext}`
4. **Media Conversion**: Execute ffmpeg to generate `/work/out/{message_id}.mp4`
5. **Response Notification**: Reply with completion message and file path
6. **Cleanup**: Conditional file deletion based on `DELETE_ON_SUCCESS` setting

## Non-Functional Requirements

### Reliability
- **Idempotency**: Duplicate message ID handling (future: `/work/state/processed.jsonl`)
- **Error Recovery**: Graceful failure handling with user notification
- **Stability**: Support for 10+ consecutive file processing without crashes

### Performance
- **Processing Time**: Complete conversion within 1 minute for typical audio files
- **Concurrency**: Handle multiple simultaneous uploads appropriately
- **Resource Management**: Efficient memory and disk space usage

### Security
- **Token Management**: Discord token via environment variables only
- **Permissions**: Bot limited to read + reply permissions
- **Channel Restriction**: Processing limited to configured channel ID only

### Extensibility
- **YouTube Integration**: Architecture prepared for Phase 2 upload functionality
- **ffmpeg Options**: Parameterized command building for future enhancements
- **Configuration**: File-based settings for easy deployment customization

## Acceptance Criteria

### Minimal Viable Product
1. ✅ Audio attachment posted to #voice-inbox generates MP4 within 1 minute
2. ✅ Discord completion notification with local file path
3. ✅ Stable processing of files up to 25MB
4. ✅ 10 consecutive file uploads without system failure
5. ✅ Background image and output directory configurable via `.env` only

### Development Environment
1. ✅ VSCode devcontainer opens successfully with all tools
2. ✅ Ruff formatting and linting works on save
3. ✅ mypy type checking shows no errors
4. ✅ pytest runs all tests successfully
5. ✅ pre-commit hooks prevent commits with code issues

### Quality Assurance
1. ✅ Error messages for unsupported file types
2. ✅ Graceful handling of network interruptions
3. ✅ Proper file cleanup preventing disk space exhaustion
4. ✅ Container restart resilience
5. ✅ All code passes ruff, mypy, and pytest checks

## Future Phase 2 Integration Points

### YouTube Upload Extension
- **New Module**: `src/uploader_youtube.py`
- **Settings Extension**: OAuth2 configuration in `settings.py`
- **Flow Modification**: Convert → Upload → Cleanup → Notify
- **Response Update**: YouTube URL instead of local path
- **Cleanup Activation**: `DELETE_ON_SUCCESS=true` for production

### Enhanced Features
- **Text Overlay**: Date/title rendering via ffmpeg drawtext
- **Audio Processing**: Volume normalization, silence trimming
- **Metadata**: Description and tags for YouTube uploads
- **Batch Processing**: Multiple file handling in single message

## Status: Phase 1 - Requirements Defined
**Next Step**: Design phase approval and technical architecture review
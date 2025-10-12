# Discord Voice Diary Bot

<div align="center">

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg?logo=docker)](https://www.docker.com/)
[![Tests](https://img.shields.io/badge/Tests-28%20Passed-success.svg)]()
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Multi-functional Bot for Automatic Voice Message Processing on Discord

English | [日本語](./README.md)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Setup](#-setup)
- [Usage](#-usage)
- [Configuration](#-configuration)
- [Development](#-development)
- [Testing](#-testing)
- [License](#-license)

---

## 🎯 Overview

Discord Voice Diary Bot automatically processes voice messages posted on Discord in two modes:

1. **Video Generation Mode**: Converts audio files to MP4 videos with background images
2. **Transcription Mode**: Transcribes audio to text using Whisper AI and saves as Obsidian-formatted Markdown files

This bot can be used for various purposes such as managing voice diaries, creating meeting minutes, and archiving voice memos.

---

## ✨ Key Features

### 🎬 Video Generation Mode

- Automatic detection of audio files (M4A, WAV, OGG, etc.)
- Fast video conversion using FFmpeg
- Customizable background images
- Audio quality adjustment (64-128 kbps)
- Automatic file cleanup

### 🎤 Transcription Mode

- **Whisper AI Integration**: High-accuracy transcription using OpenAI Whisper API
- **Obsidian Daily Note Format**: Automatically generates Markdown files by date
- **Front Matter Support**: Tag management with YAML front matter
- **Append Functionality**: Automatically appends same-day audio to the same file
- **Japanese Support**: High-accuracy recognition of Japanese speech

#### Markdown Output Example

```markdown
---
tags:
  - diary
---

[[2025]] / [[2025-Q4|Q4]] / [[2025-10|October]]
❮ [[2025-W40|Week 40]] | Week 41 | [[2025-W42|Week 42]] ❯
[[2025-10-06|06]] - [[2025-10-07|07]] - [[2025-10-08|08]] - ...

## 15:30:45 - voice-message.ogg

This is the transcribed content from the voice message...
```

---

## 🏗 Architecture

### System Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        Discord Server                        │
│                    (#voice-inbox channel)                    │
└───────────────────────────┬─────────────────────────────────┘
                            │ Audio Upload
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  Discord Voice Diary Bot                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                    Bot Controller                     │  │
│  │              (Mode: VIDEO / TRANSCRIPTION)            │  │
│  └────────┬─────────────────────────────┬─────────────────┘  │
│           │                             │                    │
│  ┌────────▼──────────┐       ┌──────────▼──────────────┐   │
│  │   Video Mode      │       │  Transcription Mode     │   │
│  │                   │       │                         │   │
│  │  ┌─────────────┐ │       │  ┌──────────────────┐  │   │
│  │  │   FFmpeg    │ │       │  │  Whisper Server  │  │   │
│  │  │   Runner    │ │       │  │   (GPU-powered)  │  │   │
│  │  └─────────────┘ │       │  └──────────────────┘  │   │
│  │         │         │       │           │            │   │
│  └─────────┼─────────┘       └───────────┼────────────┘   │
│            │                             │                 │
│  ┌─────────▼─────────┐       ┌───────────▼────────────┐   │
│  │   Storage Manager │       │ Markdown Generator     │   │
│  │   (MP4 Videos)    │       │ (Obsidian Format)      │   │
│  └───────────────────┘       └────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
         │                                  │
         ▼                                  ▼
   ./data/output/              ./transcriptions/
   video_YYYYMMDD.mp4          YYYY-MM-DD.md
```

### Components

- **Bot Controller**: Discord event handling and mode routing
- **FFmpeg Runner**: Video conversion processing (async execution, timeout management)
- **Transcription Handler**: Whisper API integration and Markdown generation
- **Storage Manager**: File management and cleanup

---

## 🛠 Tech Stack

### Backend

- **Python 3.12**: Full type hints support
- **discord.py**: Discord API integration
- **aiohttp**: Asynchronous HTTP communication
- **FFmpeg**: Video encoding
- **Whisper AI**: Speech recognition (faster-whisper-server)

### Development Tools

- **uv**: Fast package manager
- **Ruff**: Linter & Formatter
- **mypy**: Static type checker
- **pytest**: Test framework (28 tests)
- **pre-commit**: Code quality management

### Infrastructure

- **Docker & Docker Compose**: Containerization
- **VSCode DevContainer**: Development environment
- **NVIDIA Docker**: GPU support (transcription mode)

---

## 🚀 Setup

### Prerequisites

- Docker & Docker Compose
- Discord Bot Token
- (For transcription mode) NVIDIA GPU & nvidia-docker

> **Note**: Transcription mode is configured to use GPU by default. If you want to use CPU, you need to modify the settings in `docker-compose.transcription.yml`.

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/voice-diary-bot.git
cd voice-diary-bot
```

### 2. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` file:

```bash
# Required settings
DISCORD_TOKEN=your_discord_bot_token_here
CHANNEL_ID=123456789012345678

# Mode selection
BOT_MODE=video  # or transcription

# Transcription mode settings (only for transcription)
WHISPER_API_URL=http://faster-whisper-server:8000
WHISPER_MODEL=Systran/faster-whisper-medium
TRANSCRIPTION_OUTPUT_DIR=/work/transcriptions
```

### 3. Launch

#### Video Generation Mode

```bash
docker-compose up -d
```

#### Transcription Mode

```bash
docker-compose -f docker-compose.transcription.yml up -d
```

> **Note**: If you don't have a GPU environment, comment out the `deploy.resources` section in `docker-compose.transcription.yml`.

### 4. Check Logs

```bash
# Video generation mode
docker-compose logs -f

# Transcription mode
docker-compose -f docker-compose.transcription.yml logs -f
```

---

## 📖 Usage

### Video Generation Mode

1. Upload audio file to designated Discord channel
2. Bot automatically detects and starts processing
3. Completion notification and video file saved to `./data/output/`

```
🎵 Processing audio file: `voice-message.m4a`
↓
✅ Successfully converted `voice-message.m4a` to video!
   Output: `voice-message_20251011.mp4`
```

### Transcription Mode

1. Upload audio file to designated Discord channel
2. Bot automatically transcribes using Whisper AI
3. Completion notification and saved to `./transcriptions/YYYY-MM-DD.md`

```
🎤 Transcribing audio: `voice-message.ogg`
↓
✅ Transcription complete!
   Saved to: `2025-10-11.md`
```

---

## ⚙️ Configuration

### Environment Variables

#### Common Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `DISCORD_TOKEN` | - | Discord Bot Token (required) |
| `CHANNEL_ID` | - | Channel ID to monitor (required) |
| `BOT_MODE` | `video` | Operation mode (`video` / `transcription`) |
| `WORK_DIR` | `/work` | Working directory |
| `MAX_FILE_SIZE` | `26214400` | Maximum file size (bytes) |
| `PROCESSING_TIMEOUT` | `3600` | Processing timeout (seconds) |
| `DELETE_ON_SUCCESS` | `false` | Delete files after processing |

#### Video Generation Mode

| Variable | Default | Description |
|----------|---------|-------------|
| `BACKGROUND_IMAGE` | `/work/assets/bg.jpg` | Background image path |
| `AUDIO_BITRATE` | `96` | Audio bitrate (64-128 kbps) |

#### Transcription Mode

| Variable | Default | Description |
|----------|---------|-------------|
| `WHISPER_API_URL` | `http://localhost:8000` | Whisper API endpoint |
| `WHISPER_MODEL` | `Systran/faster-whisper-medium` | Whisper model to use |
| `TRANSCRIPTION_OUTPUT_DIR` | `/work/transcriptions` | Markdown save location |

---

## 👨‍💻 Development

### Development Environment Setup

This project provides a development environment using **VSCode DevContainer**.

1. **Open VSCode DevContainer**

```bash
code .
# Select "Dev Containers: Reopen in Container" from the Command Palette (Cmd/Ctrl+Shift+P)
```

The DevContainer comes pre-installed with:
- Python 3.12
- uv (fast package manager)
- FFmpeg
- Development tools (Ruff, mypy, pytest)

2. **Install Dependencies**

```bash
uv sync
```

3. **Setup pre-commit**

```bash
pre-commit install
```

### Code Quality Checks

```bash
# Lint
uv run ruff check .

# Format
uv run ruff format .

# Type check
uv run mypy src tests
```

### Project Structure

```
voice-diary-bot/
├── src/
│   ├── __main__.py          # Entry point
│   ├── bot.py               # Bot controller
│   ├── settings.py          # Configuration management
│   ├── ffmpeg_runner.py     # Video conversion
│   ├── transcription.py     # Transcription
│   └── storage.py           # Storage management
├── tests/
│   ├── test_bot.py
│   ├── test_ffmpeg_runner.py
│   ├── test_transcription.py  # 10 tests
│   └── conftest.py
├── .claude/                 # Claude AI configuration
├── docker-compose.yml       # For video mode
├── docker-compose.transcription.yml  # For transcription mode
└── README.md
```

---

## 🧪 Testing

### Running Tests

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_transcription.py

# With coverage
uv run pytest --cov=src --cov-report=html
```

### Test Overview

- **Total**: 28 tests
  - `test_ffmpeg_runner.py`: 18 tests
  - `test_transcription.py`: 10 tests
- **Coverage**: All major features covered

---

## 📄 License

This project is released under the MIT License. See [LICENSE](LICENSE) file for details.

---

<div align="center">

**[⬆ Back to Top](#discord-voice-diary-bot)**

Made with ❤️ by [Your Name]

</div>

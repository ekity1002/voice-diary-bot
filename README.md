# Discord Voice Diary Bot

A Discord bot that automatically converts voice file attachments into MP4 videos with background images using Docker and ffmpeg.

## Features

- Monitors Discord #voice-inbox channel for audio attachments
- Converts audio files to MP4 videos with static background image
- Configurable audio quality (64-128 kbps)
- Docker containerized deployment
- VSCode DevContainer development environment

## Quick Start

### Development Setup

1. Open in VSCode DevContainer
2. Copy `.env.example` to `.env` and configure
3. Run the bot: `uv run python -m src.bot`

### Production Deployment

1. Configure `.env` file
2. Run with Docker Compose: `docker-compose up -d`

## Configuration

Required environment variables:
- `DISCORD_TOKEN` - Discord bot token
- `CHANNEL_ID` - Discord channel ID to monitor

Optional variables:
- `AUDIO_BITRATE=96` - Audio quality (64-128 kbps)
- `DELETE_ON_SUCCESS=false` - Cleanup after processing

## Development

This project uses:
- **Python 3.12** with uv package management
- **Ruff** for formatting and linting
- **mypy** for type checking
- **pytest** for testing
- **pre-commit** for code quality

## Status

🚧 **Under Development** - Implementation in progress
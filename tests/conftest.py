"""Pytest configuration and fixtures for Discord Voice Diary Bot tests."""

import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def mock_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set mock environment variables for testing."""
    monkeypatch.setenv("DISCORD_TOKEN", "test_token_123")
    monkeypatch.setenv("CHANNEL_ID", "123456789")
    monkeypatch.setenv("WORK_DIR", "/tmp/test_work")
    monkeypatch.setenv("BACKGROUND_IMAGE", "/tmp/test_work/assets/bg.jpg")
    monkeypatch.setenv("DELETE_ON_SUCCESS", "false")
    monkeypatch.setenv("AUDIO_BITRATE", "96")
    monkeypatch.setenv("MAX_FILE_SIZE", str(25 * 1024 * 1024))  # 25MB in bytes
    monkeypatch.setenv("PROCESSING_TIMEOUT", "300")


@pytest.fixture
def mock_transcription_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set mock environment variables for transcription mode testing."""
    monkeypatch.setenv("DISCORD_TOKEN", "test_token_123")
    monkeypatch.setenv("CHANNEL_ID", "123456789")
    monkeypatch.setenv("BOT_MODE", "transcription")
    monkeypatch.setenv("WORK_DIR", "/tmp/test_work")
    monkeypatch.setenv("WHISPER_API_URL", "http://localhost:8000")
    monkeypatch.setenv("WHISPER_MODEL", "Systran/faster-whisper-medium")
    monkeypatch.setenv("TRANSCRIPTION_OUTPUT_DIR", "/tmp/test_transcriptions")
    monkeypatch.setenv("MAX_FILE_SIZE", str(25 * 1024 * 1024))
    monkeypatch.setenv("PROCESSING_TIMEOUT", "300")


@pytest.fixture
def sample_audio_content() -> bytes:
    """Return sample audio file content for testing."""
    # This is a minimal valid audio file header for testing
    return b"ID3\x03\x00\x00\x00\x00\x00\x00\x00"


@pytest.fixture
def sample_background_image() -> bytes:
    """Return sample image content for testing."""
    # Minimal JPEG header for testing
    return b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00"


@pytest.fixture
def mock_whisper_response() -> dict[str, str]:
    """Return mock Whisper API response for testing."""
    return {"text": "This is a test transcription result."}

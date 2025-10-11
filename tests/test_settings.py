"""Unit tests for the settings module."""

from pathlib import Path

import pytest

from src.settings import Settings


class TestSettings:
    """Test cases for Settings class."""

    def test_from_env_with_valid_required_vars(self, mock_env_vars):
        """Test Settings.from_env() with valid required environment variables."""
        settings = Settings.from_env()

        assert settings.discord_token == "test_token_123"
        assert settings.channel_id == 123456789
        assert settings.work_dir == Path("/tmp/test_work")
        assert settings.background_image == Path("/tmp/test_work/assets/bg.jpg")
        assert settings.delete_on_success is False
        assert settings.audio_bitrate == 96
        assert settings.max_file_size == 25 * 1024 * 1024
        assert settings.processing_timeout == 300

    def test_from_env_invalid_channel_id(self, monkeypatch):
        """Test Settings.from_env() raises ValueError when CHANNEL_ID is not valid."""
        monkeypatch.setenv("DISCORD_TOKEN", "test_token")
        monkeypatch.setenv("CHANNEL_ID", "not_a_number")

        with pytest.raises(ValueError, match="CHANNEL_ID must be a valid integer"):
            Settings.from_env()

    def test_from_env_default_values(self, monkeypatch):
        """Test Settings.from_env() uses default values when optional vars not set."""
        monkeypatch.setenv("DISCORD_TOKEN", "test_token")
        monkeypatch.setenv("CHANNEL_ID", "123456789")

        settings = Settings.from_env()

        assert settings.work_dir == Path("/work")
        assert settings.background_image == Path("/work/assets/bg.jpg")
        assert settings.delete_on_success is False
        assert settings.audio_bitrate == 128
        assert settings.max_file_size == 25 * 1024 * 1024
        assert settings.processing_timeout == 300

    def test_from_env_custom_optional_values(self, monkeypatch):
        """Test Settings.from_env() with custom optional values."""
        monkeypatch.setenv("DISCORD_TOKEN", "test_token")
        monkeypatch.setenv("CHANNEL_ID", "123456789")
        monkeypatch.setenv("WORK_DIR", "/custom/work")
        monkeypatch.setenv("BACKGROUND_IMAGE", "/custom/bg.png")
        monkeypatch.setenv("DELETE_ON_SUCCESS", "true")
        monkeypatch.setenv("AUDIO_BITRATE", "128")
        monkeypatch.setenv("MAX_FILE_SIZE", "50000000")
        monkeypatch.setenv("PROCESSING_TIMEOUT", "600")

        settings = Settings.from_env()

        assert settings.work_dir == Path("/custom/work")
        assert settings.background_image == Path("/custom/bg.png")
        assert settings.delete_on_success is True
        assert settings.audio_bitrate == 128
        assert settings.max_file_size == 50000000
        assert settings.processing_timeout == 600

    @pytest.mark.parametrize("value", ["true", "1", "yes", "TRUE", "YES"])
    def test_delete_on_success_truthy_values(self, monkeypatch, value):
        """Test that various truthy string values set delete_on_success to True."""
        monkeypatch.setenv("DISCORD_TOKEN", "test_token")
        monkeypatch.setenv("CHANNEL_ID", "123456789")
        monkeypatch.setenv("DELETE_ON_SUCCESS", value)

        settings = Settings.from_env()
        assert settings.delete_on_success is True

    @pytest.mark.parametrize("value", ["false", "0", "no", "FALSE", "NO", ""])
    def test_delete_on_success_falsy_values(self, monkeypatch, value):
        """Test that various falsy string values set delete_on_success to False."""
        monkeypatch.setenv("DISCORD_TOKEN", "test_token")
        monkeypatch.setenv("CHANNEL_ID", "123456789")
        monkeypatch.setenv("DELETE_ON_SUCCESS", value)

        settings = Settings.from_env()
        assert settings.delete_on_success is False

    @pytest.mark.parametrize("bitrate", [63, 129, 0, -1, 200])
    def test_invalid_audio_bitrate_from_env(self, monkeypatch, bitrate):
        """Test that invalid audio bitrate values raise ValueError."""
        monkeypatch.setenv("DISCORD_TOKEN", "test_token")
        monkeypatch.setenv("CHANNEL_ID", "123456789")
        monkeypatch.setenv("AUDIO_BITRATE", str(bitrate))

        with pytest.raises(ValueError, match="AUDIO_BITRATE must be between 64 and 128"):
            Settings.from_env()

    @pytest.mark.parametrize("bitrate", [64, 96, 128])
    def test_valid_audio_bitrate_from_env(self, monkeypatch, bitrate):
        """Test that valid audio bitrate values are accepted."""
        monkeypatch.setenv("DISCORD_TOKEN", "test_token")
        monkeypatch.setenv("CHANNEL_ID", "123456789")
        monkeypatch.setenv("AUDIO_BITRATE", str(bitrate))

        settings = Settings.from_env()
        assert settings.audio_bitrate == bitrate

    def test_post_init_validation_audio_bitrate(self):
        """Test __post_init__ validation for audio bitrate."""
        with pytest.raises(ValueError, match="Audio bitrate must be between 64 and 128"):
            Settings(discord_token="test", channel_id=123, audio_bitrate=50)

    def test_post_init_validation_max_file_size(self):
        """Test __post_init__ validation for max file size."""
        with pytest.raises(ValueError, match="Max file size must be positive"):
            Settings(discord_token="test", channel_id=123, max_file_size=0)

    def test_post_init_validation_processing_timeout(self):
        """Test __post_init__ validation for processing timeout."""
        with pytest.raises(ValueError, match="Processing timeout must be positive"):
            Settings(discord_token="test", channel_id=123, processing_timeout=-1)

    def test_post_init_path_conversion(self):
        """Test that string paths are converted to Path objects in __post_init__."""
        settings = Settings(
            discord_token="test",
            channel_id=123,
            work_dir="/test/work",
            background_image="/test/bg.jpg",
        )

        assert isinstance(settings.work_dir, Path)
        assert isinstance(settings.background_image, Path)
        assert settings.work_dir == Path("/test/work")
        assert settings.background_image == Path("/test/bg.jpg")

    def test_from_env_invalid_max_file_size(self, monkeypatch):
        """Test Settings.from_env() with invalid MAX_FILE_SIZE values."""
        monkeypatch.setenv("DISCORD_TOKEN", "test_token")
        monkeypatch.setenv("CHANNEL_ID", "123456789")
        monkeypatch.setenv("MAX_FILE_SIZE", "not_a_number")

        with pytest.raises(ValueError, match="invalid literal for int()"):
            Settings.from_env()

    def test_from_env_negative_max_file_size(self, monkeypatch):
        """Test Settings.from_env() with negative MAX_FILE_SIZE."""
        monkeypatch.setenv("DISCORD_TOKEN", "test_token")
        monkeypatch.setenv("CHANNEL_ID", "123456789")
        monkeypatch.setenv("MAX_FILE_SIZE", "-1")

        with pytest.raises(ValueError, match="Max file size must be positive"):
            Settings.from_env()

    def test_from_env_invalid_processing_timeout(self, monkeypatch):
        """Test Settings.from_env() with invalid PROCESSING_TIMEOUT values."""
        monkeypatch.setenv("DISCORD_TOKEN", "test_token")
        monkeypatch.setenv("CHANNEL_ID", "123456789")
        monkeypatch.setenv("PROCESSING_TIMEOUT", "not_a_number")

        with pytest.raises(ValueError, match="invalid literal for int()"):
            Settings.from_env()

    def test_from_env_negative_processing_timeout(self, monkeypatch):
        """Test Settings.from_env() with negative PROCESSING_TIMEOUT."""
        monkeypatch.setenv("DISCORD_TOKEN", "test_token")
        monkeypatch.setenv("CHANNEL_ID", "123456789")
        monkeypatch.setenv("PROCESSING_TIMEOUT", "-1")

        with pytest.raises(ValueError, match="Processing timeout must be positive"):
            Settings.from_env()

    def test_from_env_zero_max_file_size(self, monkeypatch):
        """Test Settings.from_env() with zero MAX_FILE_SIZE."""
        monkeypatch.setenv("DISCORD_TOKEN", "test_token")
        monkeypatch.setenv("CHANNEL_ID", "123456789")
        monkeypatch.setenv("MAX_FILE_SIZE", "0")

        with pytest.raises(ValueError, match="Max file size must be positive"):
            Settings.from_env()

    def test_from_env_zero_processing_timeout(self, monkeypatch):
        """Test Settings.from_env() with zero PROCESSING_TIMEOUT."""
        monkeypatch.setenv("DISCORD_TOKEN", "test_token")
        monkeypatch.setenv("CHANNEL_ID", "123456789")
        monkeypatch.setenv("PROCESSING_TIMEOUT", "0")

        with pytest.raises(ValueError, match="Processing timeout must be positive"):
            Settings.from_env()

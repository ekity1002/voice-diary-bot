"""Settings module for Discord Voice Diary Bot.

Provides configuration management with environment variable loading,
validation, and type-safe settings using dataclass.
"""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass
class Settings:
    """Configuration settings for the Discord Voice Diary Bot.

    Loads configuration from environment variables with validation
    and provides sensible defaults where appropriate.
    """

    # Required settings
    discord_token: str
    channel_id: int

    # Optional settings with defaults
    work_dir: Path = Path("/work")
    background_image: Path = Path("/work/assets/bg.jpg")
    delete_on_success: bool = False
    audio_bitrate: int = 96
    max_file_size: int = 25 * 1024 * 1024  # 25MB in bytes
    processing_timeout: int = 300  # 5 minutes in seconds

    @classmethod
    def from_env(cls) -> "Settings":
        """Create Settings instance from environment variables.

        Loads environment variables using python-dotenv and validates
        required parameters. Raises ValueError for missing required
        variables or invalid values.

        Returns:
            Settings: Configured settings instance

        Raises:
            ValueError: If required environment variables are missing
                       or if audio_bitrate is outside valid range
        """
        # Load environment variables from .env file if present
        load_dotenv()

        # Get required settings
        discord_token = os.getenv("DISCORD_TOKEN")
        if not discord_token:
            raise ValueError("DISCORD_TOKEN environment variable is required")

        channel_id_str = os.getenv("CHANNEL_ID")
        if not channel_id_str:
            raise ValueError("CHANNEL_ID environment variable is required")

        try:
            channel_id = int(channel_id_str)
        except ValueError as e:
            raise ValueError(
                f"CHANNEL_ID must be a valid integer: {channel_id_str}"
            ) from e

        # Get optional settings with defaults
        work_dir = Path(os.getenv("WORK_DIR", "/work"))
        background_image = Path(os.getenv("BACKGROUND_IMAGE", "/work/assets/bg.jpg"))

        delete_on_success = os.getenv("DELETE_ON_SUCCESS", "false").lower() in (
            "true",
            "1",
            "yes",
        )

        # Audio bitrate with validation
        audio_bitrate = int(os.getenv("AUDIO_BITRATE", "96"))
        if not 64 <= audio_bitrate <= 128:
            raise ValueError(
                f"AUDIO_BITRATE must be between 64 and 128 kbps, got {audio_bitrate}"
            )

        # File size limit
        max_file_size = int(os.getenv("MAX_FILE_SIZE", str(25 * 1024 * 1024)))

        # Processing timeout
        processing_timeout = int(os.getenv("PROCESSING_TIMEOUT", "300"))

        return cls(
            discord_token=discord_token,
            channel_id=channel_id,
            work_dir=work_dir,
            background_image=background_image,
            delete_on_success=delete_on_success,
            audio_bitrate=audio_bitrate,
            max_file_size=max_file_size,
            processing_timeout=processing_timeout,
        )

    def __post_init__(self) -> None:
        """Validate settings after initialization."""
        # Convert string paths to Path objects if needed
        if isinstance(self.work_dir, str):
            self.work_dir = Path(self.work_dir)
        if isinstance(self.background_image, str):
            self.background_image = Path(self.background_image)

        # Validate audio bitrate range
        if not 64 <= self.audio_bitrate <= 128:
            raise ValueError(
                f"Audio bitrate must be between 64 and 128 kbps, "
                f"got {self.audio_bitrate}"
            )

        # Ensure positive values for limits and timeouts
        if self.max_file_size <= 0:
            raise ValueError("Max file size must be positive")

        if self.processing_timeout <= 0:
            raise ValueError("Processing timeout must be positive")

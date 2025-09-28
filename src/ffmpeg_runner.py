"""FFmpeg runner module for Discord Voice Diary Bot.

Provides async FFmpeg command execution for converting audio files
to MP4 videos with configurable parameters and robust error handling.
"""

import asyncio
import logging
from pathlib import Path

from .settings import Settings

logger = logging.getLogger(__name__)


class FFmpegError(Exception):
    """Exception raised when FFmpeg processing fails."""

    def __init__(
        self,
        message: str,
        return_code: int | None = None,
        stderr: str | None = None,
    ) -> None:
        super().__init__(message)
        self.return_code = return_code
        self.stderr = stderr


class FFmpegRunner:
    """Handles FFmpeg operations for audio to video conversion.

    Executes FFmpeg commands asynchronously with proper timeout handling,
    error reporting, and output validation.
    """

    def __init__(self, settings: Settings) -> None:
        """Initialize FFmpeg runner with settings.

        Args:
            settings: Application settings for configuration
        """
        self.settings = settings
        self.timeout = settings.processing_timeout
        self.audio_bitrate = settings.audio_bitrate
        self.background_image = settings.background_image

    def build_command(self, input_audio: Path, output_video: Path) -> list[str]:
        """Build FFmpeg command for audio to video conversion.

        Args:
            input_audio: Path to input audio file
            output_video: Path to output video file

        Returns:
            list[str]: FFmpeg command as list of arguments
        """
        command = [
            "ffmpeg",
            "-y",  # Overwrite output file
            "-loop",
            "1",
            "-i",
            str(self.background_image),
            "-i",
            str(input_audio),
            "-c:v",
            "libx264",
            "-tune",
            "stillimage",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            f"{self.audio_bitrate}k",
            "-ac",
            "1",  # Mono audio
            "-shortest",  # Stop when shortest input ends
            "-movflags",
            "+faststart",  # Enable fast start for web playback
            str(output_video),
        ]

        return command

    async def convert_audio_to_video(
        self, input_audio: Path, output_video: Path
    ) -> None:
        """Convert audio file to MP4 video with background image.

        Args:
            input_audio: Path to input audio file
            output_video: Path to output video file

        Raises:
            FFmpegError: If FFmpeg command fails or times out
            FileNotFoundError: If input files don't exist
        """
        # Validate input files exist
        if not input_audio.exists():
            raise FileNotFoundError(f"Input audio file not found: {input_audio}")

        if not self.background_image.exists():
            raise FileNotFoundError(
                f"Background image not found: {self.background_image}"
            )

        # Build FFmpeg command
        command = self.build_command(input_audio, output_video)

        logger.info(
            f"Starting FFmpeg conversion: {input_audio.name} -> {output_video.name}"
        )
        logger.debug(f"FFmpeg command: {' '.join(command)}")

        try:
            # Execute FFmpeg command with timeout
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=self.timeout
            )

            # Check if process completed successfully
            if process.returncode != 0:
                stderr_text = stderr.decode("utf-8", errors="replace")
                error_msg = f"FFmpeg failed with return code {process.returncode}"
                logger.error(f"{error_msg}\nStderr: {stderr_text}")
                raise FFmpegError(error_msg, process.returncode, stderr_text)

            # Validate output file was created
            if not output_video.exists():
                raise FFmpegError("FFmpeg completed but output file was not created")

            # Validate output file has content
            if output_video.stat().st_size == 0:
                raise FFmpegError("FFmpeg created empty output file")

            logger.info(
                f"FFmpeg conversion completed successfully: {output_video.name}"
            )

        except TimeoutError as e:
            # Kill the process if it's still running
            if process.returncode is None:
                try:
                    process.kill()
                    await process.wait()
                except Exception as cleanup_error:
                    logger.debug(
                        f"Failed to kill process during cleanup: {cleanup_error}"
                    )

            error_msg = f"FFmpeg conversion timed out after {self.timeout} seconds"
            logger.error(error_msg)
            raise FFmpegError(error_msg) from e

        except FileNotFoundError as e:
            error_msg = (
                "FFmpeg executable not found. Please ensure FFmpeg is installed."
            )
            logger.error(error_msg)
            raise FFmpegError(error_msg) from e

        except Exception as e:
            error_msg = f"Unexpected error during FFmpeg conversion: {str(e)}"
            logger.error(error_msg)
            raise FFmpegError(error_msg) from e

    async def validate_ffmpeg_installation(self) -> bool:
        """Check if FFmpeg is properly installed and accessible.

        Returns:
            bool: True if FFmpeg is available, False otherwise
        """
        try:
            process = await asyncio.create_subprocess_exec(
                "ffmpeg",
                "-version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            await asyncio.wait_for(process.communicate(), timeout=10)
            return process.returncode == 0

        except (TimeoutError, FileNotFoundError):
            return False
        except Exception:
            return False

    def get_estimated_duration(self, input_audio: Path) -> float | None:
        """Get estimated processing duration (placeholder for future implementation).

        Args:
            input_audio: Path to input audio file

        Returns:
            Optional[float]: Estimated duration in seconds, None if unknown
        """
        # This could be implemented using ffprobe in the future
        # For now, return None to indicate unknown duration
        return None

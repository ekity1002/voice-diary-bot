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
        # Check if we can copy audio to avoid re-encoding
        can_copy_audio = self._can_copy_audio(input_audio)

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
            "-preset",
            "veryfast",  # Faster encoding, lower memory usage
            "-profile:v",
            "baseline",  # Lower complexity profile
            "-tune",
            "stillimage",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "copy" if can_copy_audio else "aac",  # Copy audio when possible
        ]

        # Only add bitrate if we're re-encoding audio
        if not can_copy_audio:
            command.extend(["-b:a", f"{self.audio_bitrate}k"])

        command.extend(
            [
                "-ac",
                "1",  # Mono audio
                "-shortest",  # Stop when shortest input ends
                "-movflags",
                "+faststart",  # Enable fast start for web playback
                "-max_muxing_queue_size",
                "1024",  # Limit queue size to reduce memory usage
                str(output_video),
            ]
        )

        return command

    def _can_copy_audio(self, input_audio: Path) -> bool:
        """Check if audio can be copied without re-encoding.

        Args:
            input_audio: Path to input audio file

        Returns:
            bool: True if audio is already AAC and mono
        """
        # For now, assume AAC files can be copied if they're already AAC
        # A more sophisticated implementation would use ffprobe
        return input_audio.suffix.lower() in [".aac", ".m4a"]

    async def _monitor_process_with_timeout(self, process: asyncio.subprocess.Process, input_audio: Path) -> tuple[bytes, bytes]:
        """Monitor FFmpeg process with progress logging and timeout handling.

        Args:
            process: Running FFmpeg subprocess
            input_audio: Input audio file for logging context

        Returns:
            tuple[bytes, bytes]: stdout and stderr from process

        Raises:
            asyncio.TimeoutError: If process exceeds timeout
        """
        start_time = asyncio.get_event_loop().time()
        check_interval = 30  # Check every 30 seconds
        last_check = start_time

        while process.returncode is None:
            try:
                # Wait for process to complete or timeout interval
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=min(check_interval, self.timeout - (asyncio.get_event_loop().time() - start_time))
                )
                return stdout, stderr
            except asyncio.TimeoutError:
                current_time = asyncio.get_event_loop().time()
                elapsed = current_time - start_time

                # Check if we've exceeded the total timeout
                if elapsed >= self.timeout:
                    raise asyncio.TimeoutError(f"FFmpeg conversion timed out after {elapsed:.1f} seconds") from None

                # Log progress every 30 seconds
                if current_time - last_check >= check_interval:
                    logger.info(f"FFmpeg still processing {input_audio.name} - elapsed: {elapsed:.1f}s")
                    last_check = current_time

                # Continue monitoring
                await asyncio.sleep(1)

        # Process completed without timeout
        return await process.communicate()

    async def convert_audio_to_video(self, input_audio: Path, output_video: Path) -> None:
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
            raise FileNotFoundError(f"Background image not found: {self.background_image}")

        # Build FFmpeg command
        command = self.build_command(input_audio, output_video)

        logger.info(f"Starting FFmpeg conversion: {input_audio.name} -> {output_video.name}")
        logger.debug(f"FFmpeg command: {' '.join(command)}")

        try:
            # Execute FFmpeg command with timeout
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            # Monitor process with progress logging
            stdout, stderr = await self._monitor_process_with_timeout(process, input_audio)

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

            logger.info(f"FFmpeg conversion completed successfully: {output_video.name}")

        except asyncio.TimeoutError as e:
            # Kill the process if it's still running
            if process.returncode is None:
                try:
                    process.kill()
                    await process.wait()
                except Exception as cleanup_error:
                    logger.debug(f"Failed to kill process during cleanup: {cleanup_error}")

            error_msg = f"FFmpeg conversion timed out after {self.timeout} seconds"
            logger.error(error_msg)
            raise FFmpegError(error_msg) from e

        except FileNotFoundError as e:
            error_msg = "FFmpeg executable not found. Please ensure FFmpeg is installed."
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

        except (asyncio.TimeoutError, FileNotFoundError):
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

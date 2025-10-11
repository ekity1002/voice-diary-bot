"""Unit tests for the ffmpeg_runner module."""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.ffmpeg_runner import FFmpegError, FFmpegRunner
from src.settings import Settings


class TestFFmpegRunner:
    """Test cases for FFmpegRunner class."""

    @pytest.fixture
    def mock_settings(self, temp_dir):
        """Create mock settings for testing."""
        settings = Mock(spec=Settings)
        settings.processing_timeout = 300
        settings.audio_bitrate = 96
        settings.background_image = temp_dir / "bg.jpg"
        return settings

    @pytest.fixture
    def ffmpeg_runner(self, mock_settings):
        """Create FFmpegRunner instance for testing."""
        return FFmpegRunner(mock_settings)

    @pytest.fixture
    def setup_test_files(self, temp_dir, mock_settings):
        """Set up test input and output files."""
        input_audio = temp_dir / "input.m4a"
        output_video = temp_dir / "output.mp4"
        background_image = mock_settings.background_image

        # Create test files
        input_audio.write_text("fake audio content")
        background_image.write_text("fake image content")

        return input_audio, output_video, background_image

    def test_init(self, ffmpeg_runner, mock_settings):
        """Test FFmpegRunner initialization."""
        assert ffmpeg_runner.settings == mock_settings
        assert ffmpeg_runner.timeout == mock_settings.processing_timeout
        assert ffmpeg_runner.audio_bitrate == mock_settings.audio_bitrate
        assert ffmpeg_runner.background_image == mock_settings.background_image

    def test_build_command_default_settings(self, ffmpeg_runner, temp_dir):
        """Test build_command with default settings."""
        input_audio = temp_dir / "input.m4a"
        output_video = temp_dir / "output.mp4"

        command = ffmpeg_runner.build_command(input_audio, output_video)

        # For .m4a files, audio is copied (no re-encoding, no -b:a flag)
        expected_command = [
            "ffmpeg",
            "-y",
            "-loop",
            "1",
            "-i",
            str(ffmpeg_runner.background_image),
            "-i",
            str(input_audio),
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-profile:v",
            "baseline",
            "-tune",
            "stillimage",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "copy",  # .m4a files use copy instead of aac
            "-ac",
            "1",
            "-shortest",
            "-movflags",
            "+faststart",
            "-max_muxing_queue_size",
            "1024",
            str(output_video),
        ]

        assert command == expected_command

    def test_build_command_custom_bitrate(self, mock_settings, temp_dir):
        """Test build_command with custom audio bitrate."""
        mock_settings.audio_bitrate = 128
        ffmpeg_runner = FFmpegRunner(mock_settings)

        # Use .wav file to force re-encoding (not .m4a which uses copy)
        input_audio = temp_dir / "input.wav"
        output_video = temp_dir / "output.mp4"

        command = ffmpeg_runner.build_command(input_audio, output_video)

        # Check that bitrate is correctly set for re-encoded audio
        bitrate_index = command.index("-b:a")
        assert command[bitrate_index + 1] == "128k"

        # Also verify that aac codec is used (not copy)
        codec_index = command.index("-c:a")
        assert command[codec_index + 1] == "aac"

    @pytest.mark.asyncio
    async def test_convert_audio_to_video_success(self, ffmpeg_runner, setup_test_files):
        """Test successful audio to video conversion."""
        input_audio, output_video, background_image = setup_test_files

        # Mock subprocess execution
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b"stdout", b"stderr"))

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            # Create the output file to simulate successful conversion
            output_video.write_text("fake video content")

            await ffmpeg_runner.convert_audio_to_video(input_audio, output_video)

            # Verify subprocess was called
            mock_process.communicate.assert_called()

    @pytest.mark.asyncio
    async def test_convert_audio_to_video_input_not_found(self, ffmpeg_runner, temp_dir):
        """Test conversion fails when input audio file doesn't exist."""
        input_audio = temp_dir / "nonexistent.m4a"
        output_video = temp_dir / "output.mp4"

        with pytest.raises(FileNotFoundError, match="Input audio file not found"):
            await ffmpeg_runner.convert_audio_to_video(input_audio, output_video)

    @pytest.mark.asyncio
    async def test_convert_audio_to_video_background_not_found(self, ffmpeg_runner, temp_dir):
        """Test conversion fails when background image doesn't exist."""
        input_audio = temp_dir / "input.m4a"
        output_video = temp_dir / "output.mp4"

        # Create input file but not background image
        input_audio.write_text("fake audio")

        with pytest.raises(FileNotFoundError, match="Background image not found"):
            await ffmpeg_runner.convert_audio_to_video(input_audio, output_video)

    @pytest.mark.asyncio
    async def test_convert_audio_to_video_ffmpeg_failure(self, ffmpeg_runner, setup_test_files):
        """Test conversion fails when FFmpeg returns non-zero exit code."""
        input_audio, output_video, background_image = setup_test_files

        # Mock subprocess execution with failure
        mock_process = AsyncMock()
        mock_process.returncode = 1
        mock_process.communicate.return_value = (b"stdout", b"error message")

        with (
            patch("asyncio.create_subprocess_exec", return_value=mock_process),
            patch("asyncio.wait_for", return_value=(b"stdout", b"error message")),
        ):
            with pytest.raises(FFmpegError, match="FFmpeg failed with return code 1"):
                await ffmpeg_runner.convert_audio_to_video(input_audio, output_video)

    @pytest.mark.asyncio
    async def test_convert_audio_to_video_no_output_file(self, ffmpeg_runner, setup_test_files):
        """Test conversion fails when output file is not created."""
        input_audio, output_video, background_image = setup_test_files

        # Mock subprocess execution with success but no output file
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = (b"stdout", b"stderr")

        with (
            patch("asyncio.create_subprocess_exec", return_value=mock_process),
            patch("asyncio.wait_for", return_value=(b"stdout", b"stderr")),
        ):
            # Don't create output file to simulate failure

            with pytest.raises(FFmpegError, match="output file was not created"):
                await ffmpeg_runner.convert_audio_to_video(input_audio, output_video)

    @pytest.mark.asyncio
    async def test_convert_audio_to_video_empty_output_file(self, ffmpeg_runner, setup_test_files):
        """Test conversion fails when output file is empty."""
        input_audio, output_video, background_image = setup_test_files

        # Mock subprocess execution with success
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = (b"stdout", b"stderr")

        with (
            patch("asyncio.create_subprocess_exec", return_value=mock_process),
            patch("asyncio.wait_for", return_value=(b"stdout", b"stderr")),
        ):
            # Create empty output file
            output_video.touch()

            with pytest.raises(FFmpegError, match="empty output file"):
                await ffmpeg_runner.convert_audio_to_video(input_audio, output_video)

    @pytest.mark.asyncio
    async def test_convert_audio_to_video_ffmpeg_not_found(self, ffmpeg_runner, setup_test_files):
        """Test conversion fails when FFmpeg executable is not found."""
        input_audio, output_video, background_image = setup_test_files

        with patch("asyncio.create_subprocess_exec", side_effect=FileNotFoundError()):
            with pytest.raises(FFmpegError, match="FFmpeg executable not found"):
                await ffmpeg_runner.convert_audio_to_video(input_audio, output_video)

    @pytest.mark.asyncio
    async def test_convert_audio_to_video_unexpected_error(self, ffmpeg_runner, setup_test_files):
        """Test conversion handles unexpected errors gracefully."""
        input_audio, output_video, background_image = setup_test_files

        with patch("asyncio.create_subprocess_exec", side_effect=RuntimeError("Unexpected")):
            with pytest.raises(FFmpegError, match="Unexpected error"):
                await ffmpeg_runner.convert_audio_to_video(input_audio, output_video)

    @pytest.mark.asyncio
    async def test_validate_ffmpeg_installation_success(self, ffmpeg_runner):
        """Test FFmpeg installation validation when FFmpeg is available."""
        # Mock subprocess execution with success
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = (b"ffmpeg version", b"")

        with (
            patch("asyncio.create_subprocess_exec", return_value=mock_process),
            patch("asyncio.wait_for", return_value=(b"ffmpeg version", b"")) as mock_wait_for,
        ):
            result = await ffmpeg_runner.validate_ffmpeg_installation()
            assert result is True
            # Verify timeout was set for validation
            mock_wait_for.assert_called_once()
            args, kwargs = mock_wait_for.call_args
            assert kwargs.get("timeout") == 10

    @pytest.mark.asyncio
    async def test_validate_ffmpeg_installation_failure(self, ffmpeg_runner):
        """Test FFmpeg installation validation when FFmpeg is not available."""
        # Mock subprocess execution with failure
        mock_process = AsyncMock()
        mock_process.returncode = 1

        with (
            patch("asyncio.create_subprocess_exec", return_value=mock_process),
            patch("asyncio.wait_for", return_value=(b"", b"error")),
        ):
            result = await ffmpeg_runner.validate_ffmpeg_installation()
            assert result is False

    @pytest.mark.asyncio
    async def test_validate_ffmpeg_installation_not_found(self, ffmpeg_runner):
        """Test FFmpeg installation validation when executable is not found."""
        with patch("asyncio.create_subprocess_exec", side_effect=FileNotFoundError()):
            result = await ffmpeg_runner.validate_ffmpeg_installation()
            assert result is False

    @pytest.mark.asyncio
    async def test_validate_ffmpeg_installation_timeout(self, ffmpeg_runner):
        """Test FFmpeg installation validation with timeout."""
        mock_process = AsyncMock()

        with (
            patch("asyncio.create_subprocess_exec", return_value=mock_process),
            patch("asyncio.wait_for", side_effect=asyncio.TimeoutError()),
        ):
            result = await ffmpeg_runner.validate_ffmpeg_installation()
            assert result is False

    def test_get_estimated_duration(self, ffmpeg_runner, temp_dir):
        """Test get_estimated_duration placeholder implementation."""
        input_audio = temp_dir / "input.m4a"

        # Current implementation returns None
        duration = ffmpeg_runner.get_estimated_duration(input_audio)
        assert duration is None


class TestFFmpegError:
    """Test cases for FFmpegError exception."""

    def test_ffmpeg_error_basic(self):
        """Test basic FFmpegError creation."""
        error = FFmpegError("Test error")
        assert str(error) == "Test error"
        assert error.return_code is None
        assert error.stderr is None

    def test_ffmpeg_error_with_details(self):
        """Test FFmpegError with return code and stderr."""
        error = FFmpegError("Test error", return_code=1, stderr="Error details")
        assert str(error) == "Test error"
        assert error.return_code == 1
        assert error.stderr == "Error details"

"""Integration tests for Discord Voice Diary Bot."""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from src.ffmpeg_runner import FFmpegRunner
from src.settings import Settings
from src.storage import StorageManager


class TestEndToEndWorkflow:
    """Integration tests for complete file processing workflow."""

    @pytest.fixture
    def integration_settings(self, temp_dir):
        """Create settings for integration testing."""
        settings = Settings(
            discord_token="test_token",
            channel_id=123456789,
            work_dir=temp_dir,
            background_image=temp_dir / "assets" / "bg.jpg",
            delete_on_success=False,
            audio_bitrate=96,
            max_file_size=25 * 1024 * 1024,
            processing_timeout=300,
        )
        return settings

    @pytest.fixture
    def setup_integration_env(
        self, integration_settings, sample_audio_content, sample_background_image
    ):
        """Set up complete integration testing environment."""
        storage = StorageManager(integration_settings)
        ffmpeg_runner = FFmpegRunner(integration_settings)

        # Create background image
        background_path = integration_settings.background_image
        background_path.write_bytes(sample_background_image)

        # Create test audio file in inbox
        audio_filename = "test_audio.m4a"
        input_path = storage.get_inbox_path(audio_filename)
        input_path.write_bytes(sample_audio_content)

        output_path = storage.get_output_path(audio_filename)

        return storage, ffmpeg_runner, input_path, output_path

    @pytest.mark.asyncio
    async def test_complete_audio_processing_workflow(self, setup_integration_env):
        """Test the complete workflow from audio input to video output."""
        storage, ffmpeg_runner, input_path, output_path = setup_integration_env

        # Verify setup
        assert input_path.exists()
        assert ffmpeg_runner.background_image.exists()
        assert storage.file_exists(input_path)
        assert storage.validate_file_size(input_path)

        # Mock FFmpeg execution to simulate successful conversion
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = (b"success", b"")

        with patch("asyncio.create_subprocess_exec", return_value=mock_process), patch(
            "asyncio.wait_for", return_value=(b"success", b"")
        ):
            # Simulate FFmpeg creating output file
            output_path.write_text("fake video content")

            # Run the conversion
            await ffmpeg_runner.convert_audio_to_video(input_path, output_path)

            # Verify results
            assert output_path.exists()
            assert storage.file_exists(output_path)
            assert output_path.stat().st_size > 0

            # Test cleanup
            storage.cleanup_inbox_file(input_path)
            assert not input_path.exists()

    @pytest.mark.asyncio
    async def test_workflow_with_cleanup_enabled(self, integration_settings, setup_integration_env):
        """Test workflow with automatic cleanup enabled."""
        # Enable cleanup
        integration_settings.delete_on_success = True

        storage, ffmpeg_runner, input_path, output_path = setup_integration_env

        # Mock successful FFmpeg execution
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = (b"success", b"")

        with patch("asyncio.create_subprocess_exec", return_value=mock_process), patch(
            "asyncio.wait_for", return_value=(b"success", b"")
        ):
            # Simulate FFmpeg creating output file
            output_path.write_text("fake video content")

            # Run conversion
            await ffmpeg_runner.convert_audio_to_video(input_path, output_path)

            # Verify output exists before cleanup
            assert output_path.exists()

            # Test automatic cleanup
            storage.cleanup_output_file(output_path)
            assert not output_path.exists()  # Should be deleted

    @pytest.mark.asyncio
    async def test_workflow_with_file_size_validation(self, integration_settings, temp_dir):
        """Test workflow with file size validation."""
        # Set very small file size limit
        integration_settings.max_file_size = 10

        storage = StorageManager(integration_settings)

        # Create a file that exceeds the limit
        large_audio = storage.get_inbox_path("large_audio.m4a")
        large_audio.write_text("This content exceeds the 10-byte limit")

        # Validation should fail
        assert not storage.validate_file_size(large_audio)

        # Create a file within the limit
        small_audio = storage.get_inbox_path("small_audio.m4a")
        small_audio.write_text("small")

        # Validation should pass
        assert storage.validate_file_size(small_audio)

    @pytest.mark.asyncio
    async def test_workflow_error_handling(self, setup_integration_env):
        """Test error handling in the complete workflow."""
        storage, ffmpeg_runner, input_path, output_path = setup_integration_env

        # Test with FFmpeg failure
        mock_process = AsyncMock()
        mock_process.returncode = 1
        mock_process.communicate.return_value = (b"", b"FFmpeg error")

        with patch("asyncio.create_subprocess_exec", return_value=mock_process), patch(
            "asyncio.wait_for", return_value=(b"", b"FFmpeg error")
        ):
            from src.ffmpeg_runner import FFmpegError

            with pytest.raises(FFmpegError):
                await ffmpeg_runner.convert_audio_to_video(input_path, output_path)

            # Verify original files still exist after error
            assert input_path.exists()
            assert not output_path.exists()

    def test_storage_directory_structure(self, integration_settings):
        """Test that storage manager creates proper directory structure."""
        storage = StorageManager(integration_settings)

        # Verify all directories exist
        assert storage.work_dir.exists()
        assert storage.inbox_dir.exists()
        assert storage.output_dir.exists()
        assert storage.assets_dir.exists()

        # Verify correct paths
        assert storage.inbox_dir == storage.work_dir / "inbox"
        assert storage.output_dir == storage.work_dir / "out"
        assert storage.assets_dir == storage.work_dir / "assets"

    def test_path_generation_consistency(self, integration_settings):
        """Test that path generation is consistent across components."""
        storage = StorageManager(integration_settings)

        test_filename = "test_audio.m4a"

        # Test inbox path
        inbox_path = storage.get_inbox_path(test_filename)
        assert inbox_path.parent == storage.inbox_dir
        assert inbox_path.name == test_filename

        # Test output path
        output_path = storage.get_output_path(test_filename)
        assert output_path.parent == storage.output_dir
        assert output_path.suffix == ".mp4"
        assert output_path.stem == Path(test_filename).stem

    def test_settings_integration_with_components(self, integration_settings):
        """Test that settings are properly integrated across all components."""
        storage = StorageManager(integration_settings)
        ffmpeg_runner = FFmpegRunner(integration_settings)

        # Verify settings propagation
        assert storage.settings == integration_settings
        assert ffmpeg_runner.settings == integration_settings

        # Verify specific setting usage
        assert ffmpeg_runner.audio_bitrate == integration_settings.audio_bitrate
        assert ffmpeg_runner.timeout == integration_settings.processing_timeout
        assert ffmpeg_runner.background_image == integration_settings.background_image

        assert storage.work_dir == integration_settings.work_dir

    @pytest.mark.asyncio
    async def test_multiple_file_processing(self, integration_settings, sample_audio_content):
        """Test processing multiple files in sequence."""
        # Create fresh storage manager without pre-existing files
        storage = StorageManager(integration_settings)
        ffmpeg_runner = FFmpegRunner(integration_settings)

        # Create background image
        background_path = integration_settings.background_image
        background_path.write_bytes(b"fake background image")

        # Create multiple test files
        files = []
        for i in range(3):
            filename = f"audio_{i}.m4a"
            input_path = storage.get_inbox_path(filename)
            output_path = storage.get_output_path(filename)
            input_path.write_bytes(sample_audio_content)
            files.append((input_path, output_path))

        # Mock FFmpeg execution
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = (b"success", b"")

        with patch("asyncio.create_subprocess_exec", return_value=mock_process), patch(
            "asyncio.wait_for", return_value=(b"success", b"")
        ):
            # Process all files
            for input_path, output_path in files:
                # Simulate FFmpeg creating output
                output_path.write_text("fake video content")

                await ffmpeg_runner.convert_audio_to_video(input_path, output_path)

                # Verify each file
                assert output_path.exists()
                assert storage.file_exists(output_path)

        # Verify all files are listed correctly
        inbox_files = storage.list_inbox_files()
        output_files = storage.list_output_files()

        assert len(inbox_files) == 3
        assert len(output_files) == 3

    def test_disk_usage_tracking(
        self, integration_settings, sample_audio_content, sample_background_image
    ):
        """Test disk usage tracking functionality."""
        storage = StorageManager(integration_settings)

        # Create files in different directories
        inbox_file = storage.get_inbox_path("test.m4a")
        inbox_file.write_bytes(sample_audio_content)

        output_file = storage.get_output_path("test.m4a")
        output_file.write_text("fake video content")

        assets_file = storage.assets_dir / "bg.jpg"
        assets_file.write_bytes(sample_background_image)

        # Get usage information
        usage = storage.get_disk_usage()

        # Verify usage tracking
        assert usage["inbox"] > 0
        assert usage["output"] > 0
        assert usage["assets"] > 0
        assert usage["work"] >= usage["inbox"] + usage["output"] + usage["assets"]

    @pytest.mark.asyncio
    async def test_ffmpeg_validation_integration(self, integration_settings):
        """Test FFmpeg validation in integration context."""
        ffmpeg_runner = FFmpegRunner(integration_settings)

        # Mock FFmpeg validation
        mock_process = AsyncMock()
        mock_process.returncode = 0

        with patch("asyncio.create_subprocess_exec", return_value=mock_process), patch(
            "asyncio.wait_for", return_value=(b"ffmpeg version", b"")
        ):
            is_available = await ffmpeg_runner.validate_ffmpeg_installation()
            assert is_available is True

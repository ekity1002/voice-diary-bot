"""Unit tests for the storage module."""

from unittest.mock import Mock

import pytest

from src.settings import Settings
from src.storage import StorageManager


class TestStorageManager:
    """Test cases for StorageManager class."""

    @pytest.fixture
    def mock_settings(self, temp_dir):
        """Create mock settings for testing."""
        settings = Mock(spec=Settings)
        settings.work_dir = temp_dir
        settings.background_image = temp_dir / "assets" / "bg.jpg"
        settings.delete_on_success = False
        settings.max_file_size = 25 * 1024 * 1024  # 25MB
        return settings

    @pytest.fixture
    def storage_manager(self, mock_settings):
        """Create StorageManager instance for testing."""
        return StorageManager(mock_settings)

    def test_init_creates_directories(self, storage_manager, mock_settings):
        """Test that StorageManager.__init__ creates required directories."""
        assert storage_manager.work_dir == mock_settings.work_dir
        assert storage_manager.inbox_dir == mock_settings.work_dir / "inbox"
        assert storage_manager.output_dir == mock_settings.work_dir / "out"
        assert storage_manager.assets_dir == mock_settings.work_dir / "assets"

        # Check directories were created
        assert storage_manager.work_dir.exists()
        assert storage_manager.inbox_dir.exists()
        assert storage_manager.output_dir.exists()
        assert storage_manager.assets_dir.exists()

    def test_get_inbox_path(self, storage_manager):
        """Test get_inbox_path generates correct paths."""
        filename = "test_audio.m4a"
        path = storage_manager.get_inbox_path(filename)

        assert path == storage_manager.inbox_dir / filename
        assert path.name == filename

    def test_get_output_path(self, storage_manager):
        """Test get_output_path generates correct MP4 paths."""
        test_cases = [
            ("audio.m4a", "audio.mp4"),
            ("voice_note.mp3", "voice_note.mp4"),
            ("recording.wav", "recording.mp4"),
            ("file_without_ext", "file_without_ext.mp4"),
        ]

        for input_filename, expected_output in test_cases:
            path = storage_manager.get_output_path(input_filename)
            assert path == storage_manager.output_dir / expected_output
            assert path.suffix == ".mp4"

    def test_get_background_image_path(self, storage_manager, mock_settings):
        """Test get_background_image_path returns correct path."""
        path = storage_manager.get_background_image_path()
        assert path == mock_settings.background_image

    def test_cleanup_inbox_file_existing(self, storage_manager):
        """Test cleanup_inbox_file removes existing file in inbox."""
        # Create a test file in inbox
        test_file = storage_manager.inbox_dir / "test.txt"
        test_file.write_text("test content")
        assert test_file.exists()

        # Clean up the file
        storage_manager.cleanup_inbox_file(test_file)
        assert not test_file.exists()

    def test_cleanup_inbox_file_outside_inbox(self, storage_manager, temp_dir):
        """Test cleanup_inbox_file doesn't remove files outside inbox."""
        # Create a file outside inbox
        outside_file = temp_dir / "outside.txt"
        outside_file.write_text("test content")
        assert outside_file.exists()

        # Try to clean it up (should not remove it)
        storage_manager.cleanup_inbox_file(outside_file)
        assert outside_file.exists()

    def test_cleanup_inbox_file_nonexistent(self, storage_manager):
        """Test cleanup_inbox_file handles nonexistent files gracefully."""
        nonexistent_file = storage_manager.inbox_dir / "nonexistent.txt"
        # Should not raise an exception
        storage_manager.cleanup_inbox_file(nonexistent_file)

    def test_cleanup_output_file_deletion_disabled(self, storage_manager):
        """Test cleanup_output_file doesn't delete when deletion is disabled."""
        # Create a test file in output
        test_file = storage_manager.output_dir / "test.mp4"
        test_file.write_text("test content")
        assert test_file.exists()

        # Clean up should not remove file when deletion is disabled
        storage_manager.cleanup_output_file(test_file)
        assert test_file.exists()

    def test_cleanup_output_file_deletion_enabled(self, storage_manager, mock_settings):
        """Test cleanup_output_file deletes when deletion is enabled."""
        # Enable deletion
        mock_settings.delete_on_success = True

        # Create a test file in output
        test_file = storage_manager.output_dir / "test.mp4"
        test_file.write_text("test content")
        assert test_file.exists()

        # Clean up should remove file when deletion is enabled
        storage_manager.cleanup_output_file(test_file)
        assert not test_file.exists()

    def test_cleanup_output_file_outside_output(self, storage_manager, mock_settings, temp_dir):
        """Test cleanup_output_file doesn't remove files outside output directory."""
        # Enable deletion
        mock_settings.delete_on_success = True

        # Create a file outside output
        outside_file = temp_dir / "outside.mp4"
        outside_file.write_text("test content")
        assert outside_file.exists()

        # Try to clean it up (should not remove it)
        storage_manager.cleanup_output_file(outside_file)
        assert outside_file.exists()

    def test_cleanup_all_inbox_files(self, storage_manager):
        """Test cleanup_all_inbox_files removes all files from inbox."""
        # Create multiple test files
        files = []
        for i in range(3):
            test_file = storage_manager.inbox_dir / f"test_{i}.txt"
            test_file.write_text(f"content {i}")
            files.append(test_file)

        # Verify files exist
        for file_path in files:
            assert file_path.exists()

        # Clean up all files
        count = storage_manager.cleanup_all_inbox_files()

        # Verify cleanup
        assert count == 3
        for file_path in files:
            assert not file_path.exists()

    def test_cleanup_all_inbox_files_empty_directory(self, storage_manager):
        """Test cleanup_all_inbox_files on empty directory."""
        count = storage_manager.cleanup_all_inbox_files()
        assert count == 0

    def test_file_exists(self, storage_manager):
        """Test file_exists method."""
        # Test with existing file
        existing_file = storage_manager.inbox_dir / "existing.txt"
        existing_file.write_text("content")
        assert storage_manager.file_exists(existing_file) is True

        # Test with nonexistent file
        nonexistent_file = storage_manager.inbox_dir / "nonexistent.txt"
        assert storage_manager.file_exists(nonexistent_file) is False

        # Test with directory (should return False)
        assert storage_manager.file_exists(storage_manager.inbox_dir) is False

    def test_get_file_size(self, storage_manager):
        """Test get_file_size method."""
        # Test with existing file
        test_content = "test content with some length"
        test_file = storage_manager.inbox_dir / "test.txt"
        test_file.write_text(test_content)

        size = storage_manager.get_file_size(test_file)
        assert size == len(test_content.encode())

        # Test with nonexistent file
        nonexistent_file = storage_manager.inbox_dir / "nonexistent.txt"
        size = storage_manager.get_file_size(nonexistent_file)
        assert size is None

    def test_validate_file_size_within_limit(self, storage_manager):
        """Test validate_file_size with file within size limit."""
        # Create small file
        test_file = storage_manager.inbox_dir / "small.txt"
        test_file.write_text("small content")

        assert storage_manager.validate_file_size(test_file) is True

    def test_validate_file_size_exceeds_limit(self, storage_manager, mock_settings):
        """Test validate_file_size with file exceeding size limit."""
        # Set a very small limit
        mock_settings.max_file_size = 5

        # Create file larger than limit
        test_file = storage_manager.inbox_dir / "large.txt"
        test_file.write_text("this content exceeds the 5-byte limit")

        assert storage_manager.validate_file_size(test_file) is False

    def test_validate_file_size_nonexistent_file(self, storage_manager):
        """Test validate_file_size with nonexistent file."""
        nonexistent_file = storage_manager.inbox_dir / "nonexistent.txt"
        assert storage_manager.validate_file_size(nonexistent_file) is False

    def test_get_disk_usage(self, storage_manager):
        """Test get_disk_usage method."""
        # Create files in different directories
        inbox_file = storage_manager.inbox_dir / "inbox_file.txt"
        inbox_file.write_text("inbox content")

        output_file = storage_manager.output_dir / "output_file.mp4"
        output_file.write_text("output content")

        assets_file = storage_manager.assets_dir / "bg.jpg"
        assets_file.write_text("background image data")

        usage = storage_manager.get_disk_usage()

        assert "work" in usage
        assert "inbox" in usage
        assert "output" in usage
        assert "assets" in usage

        # Check that usage values are reasonable
        assert usage["inbox"] > 0
        assert usage["output"] > 0
        assert usage["assets"] > 0
        assert usage["work"] >= usage["inbox"] + usage["output"] + usage["assets"]

    def test_list_inbox_files(self, storage_manager):
        """Test list_inbox_files method."""
        # Create test files
        file1 = storage_manager.inbox_dir / "file1.txt"
        file2 = storage_manager.inbox_dir / "file2.mp3"
        file1.write_text("content1")
        file2.write_text("content2")

        # Create a subdirectory (should be ignored)
        subdir = storage_manager.inbox_dir / "subdir"
        subdir.mkdir()

        files = storage_manager.list_inbox_files()

        assert len(files) == 2
        assert file1 in files
        assert file2 in files
        assert subdir not in files

    def test_list_inbox_files_empty(self, storage_manager):
        """Test list_inbox_files with empty directory."""
        files = storage_manager.list_inbox_files()
        assert files == []

    def test_list_output_files(self, storage_manager):
        """Test list_output_files method."""
        # Create test files
        file1 = storage_manager.output_dir / "video1.mp4"
        file2 = storage_manager.output_dir / "video2.mp4"
        file1.write_text("video1 content")
        file2.write_text("video2 content")

        files = storage_manager.list_output_files()

        assert len(files) == 2
        assert file1 in files
        assert file2 in files

    def test_list_output_files_empty(self, storage_manager):
        """Test list_output_files with empty directory."""
        files = storage_manager.list_output_files()
        assert files == []

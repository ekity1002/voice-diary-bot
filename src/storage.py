"""Storage module for Discord Voice Diary Bot.

Provides file management functionality including path generation,
directory structure management, file cleanup, and file utilities.
"""

from pathlib import Path

from .settings import Settings


class StorageManager:
    """Manages file storage operations for the voice diary bot.

    Handles directory structure, file paths, cleanup operations,
    and file information utilities.
    """

    def __init__(self, settings: Settings) -> None:
        """Initialize storage manager with settings.

        Args:
            settings: Application settings containing paths and configuration
        """
        self.settings = settings
        self.work_dir = settings.work_dir
        self.inbox_dir = self.work_dir / "inbox"
        self.output_dir = self.work_dir / "out"
        self.assets_dir = self.work_dir / "assets"

        # Ensure directories exist
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Create required directories if they don't exist."""
        directories = [self.work_dir, self.inbox_dir, self.output_dir, self.assets_dir]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def get_inbox_path(self, filename: str) -> Path:
        """Generate path for temporary audio file in inbox.

        Args:
            filename: Original filename from Discord attachment

        Returns:
            Path: Full path for the inbox file
        """
        return self.inbox_dir / filename

    def get_output_path(self, input_filename: str) -> Path:
        """Generate path for output MP4 video file.

        Args:
            input_filename: Original audio filename

        Returns:
            Path: Full path for the output MP4 file
        """
        # Change extension to .mp4
        base_name = Path(input_filename).stem
        output_filename = f"{base_name}.mp4"
        return self.output_dir / output_filename

    def get_background_image_path(self) -> Path:
        """Get path to background image for video generation.

        Returns:
            Path: Path to background image file
        """
        return self.settings.background_image

    def cleanup_inbox_file(self, file_path: Path) -> None:
        """Remove file from inbox directory.

        Args:
            file_path: Path to file to be removed
        """
        if file_path.exists() and file_path.parent == self.inbox_dir:
            file_path.unlink()

    def cleanup_output_file(self, file_path: Path) -> None:
        """Remove file from output directory if deletion is enabled.

        Args:
            file_path: Path to file to be removed
        """
        if (
            self.settings.delete_on_success
            and file_path.exists()
            and file_path.parent == self.output_dir
        ):
            file_path.unlink()

    def cleanup_all_inbox_files(self) -> int:
        """Remove all files from inbox directory.

        Returns:
            int: Number of files removed
        """
        count = 0
        for file_path in self.inbox_dir.iterdir():
            if file_path.is_file():
                file_path.unlink()
                count += 1
        return count

    def file_exists(self, file_path: Path) -> bool:
        """Check if file exists.

        Args:
            file_path: Path to check

        Returns:
            bool: True if file exists and is a regular file
        """
        return file_path.exists() and file_path.is_file()

    def get_file_size(self, file_path: Path) -> int | None:
        """Get file size in bytes.

        Args:
            file_path: Path to file

        Returns:
            Optional[int]: File size in bytes, None if file doesn't exist
        """
        if not self.file_exists(file_path):
            return None

        return file_path.stat().st_size

    def validate_file_size(self, file_path: Path) -> bool:
        """Validate that file size is within limits.

        Args:
            file_path: Path to file to validate

        Returns:
            bool: True if file size is within configured limits
        """
        file_size = self.get_file_size(file_path)
        if file_size is None:
            return False

        return file_size <= self.settings.max_file_size

    def get_disk_usage(self) -> dict[str, int]:
        """Get disk usage information for work directories.

        Returns:
            dict: Dictionary with usage information for each directory
        """
        usage = {}

        for name, directory in [
            ("work", self.work_dir),
            ("inbox", self.inbox_dir),
            ("output", self.output_dir),
            ("assets", self.assets_dir),
        ]:
            if directory.exists():
                total_size = sum(
                    f.stat().st_size for f in directory.rglob("*") if f.is_file()
                )
                usage[name] = total_size
            else:
                usage[name] = 0

        return usage

    def list_inbox_files(self) -> list[Path]:
        """List all files in inbox directory.

        Returns:
            list[Path]: List of file paths in inbox
        """
        if not self.inbox_dir.exists():
            return []

        return [f for f in self.inbox_dir.iterdir() if f.is_file()]

    def list_output_files(self) -> list[Path]:
        """List all files in output directory.

        Returns:
            list[Path]: List of file paths in output
        """
        if not self.output_dir.exists():
            return []

        return [f for f in self.output_dir.iterdir() if f.is_file()]

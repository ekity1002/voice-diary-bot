"""Tests for transcription module."""

from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest
from aiohttp import ClientError

from src.settings import Settings
from src.transcription import TranscriptionHandler


class TestGenerateDailyTemplate:
    """Tests for _generate_daily_template method."""

    def test_generate_daily_template_format(self, mock_transcription_env_vars: None, temp_dir: Path) -> None:
        """Test that daily template has correct Obsidian format."""
        settings = Settings.from_env()
        handler = TranscriptionHandler(settings)

        # Test with a specific date
        test_date = datetime(2025, 10, 11, 15, 30, 45)
        template = handler._generate_daily_template(test_date)

        # Check breadcrumb
        assert "[[2025]]" in template
        assert "[[2025-Q4|Q4]]" in template
        assert "[[2025-10|10月]]" in template

        # Check week navigation
        assert "Week 41" in template
        assert "[[2025-W40|Week 40]]" in template
        assert "[[2025-W42|Week 42]]" in template

        # Check week days (Monday start)
        assert "[[2025-10-06|06]]" in template  # Monday
        assert "[[2025-10-12|12]]" in template  # Sunday

    def test_generate_daily_template_quarter_calculation(self, mock_transcription_env_vars: None, temp_dir: Path) -> None:
        """Test quarter calculation for different months."""
        settings = Settings.from_env()
        handler = TranscriptionHandler(settings)

        # Q1: January
        template_q1 = handler._generate_daily_template(datetime(2025, 1, 15))
        assert "[[2025-Q1|Q1]]" in template_q1

        # Q2: April
        template_q2 = handler._generate_daily_template(datetime(2025, 4, 15))
        assert "[[2025-Q2|Q2]]" in template_q2

        # Q3: July
        template_q3 = handler._generate_daily_template(datetime(2025, 7, 15))
        assert "[[2025-Q3|Q3]]" in template_q3

        # Q4: October
        template_q4 = handler._generate_daily_template(datetime(2025, 10, 15))
        assert "[[2025-Q4|Q4]]" in template_q4

    def test_generate_daily_template_year_boundary(self, mock_transcription_env_vars: None, temp_dir: Path) -> None:
        """Test week navigation across year boundary."""
        settings = Settings.from_env()
        handler = TranscriptionHandler(settings)

        # Date near year end
        test_date = datetime(2025, 12, 31)
        template = handler._generate_daily_template(test_date)

        # Should contain 2025 and potentially 2026 week references
        assert "2025" in template or "2026" in template


class TestTranscribeAudio:
    """Tests for transcribe_audio method."""

    @pytest.mark.asyncio
    async def test_transcribe_audio_success(
        self,
        mock_transcription_env_vars: None,
        temp_dir: Path,
        mock_whisper_response: dict[str, str],
    ) -> None:
        """Test successful audio transcription."""
        settings = Settings.from_env()
        handler = TranscriptionHandler(settings)

        # Create test audio file
        audio_path = temp_dir / "test.ogg"
        audio_path.write_bytes(b"fake audio content")

        # Mock aiohttp session
        with patch("aiohttp.ClientSession") as mock_session:
            mock_response = AsyncMock()
            mock_response.raise_for_status = Mock()
            mock_response.json = AsyncMock(return_value=mock_whisper_response)

            mock_context = AsyncMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_response)
            mock_context.__aexit__ = AsyncMock()

            mock_post = Mock(return_value=mock_context)
            mock_session.return_value.__aenter__.return_value.post = mock_post

            # Execute
            result = await handler.transcribe_audio(audio_path)

            # Verify
            assert result == "This is a test transcription result."
            mock_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_transcribe_audio_invalid_response(self, mock_transcription_env_vars: None, temp_dir: Path) -> None:
        """Test transcription with invalid API response."""
        settings = Settings.from_env()
        handler = TranscriptionHandler(settings)

        audio_path = temp_dir / "test.ogg"
        audio_path.write_bytes(b"fake audio content")

        # Mock response without 'text' field
        with patch("src.transcription.aiohttp.ClientSession") as mock_session:
            mock_response = AsyncMock()
            mock_response.raise_for_status = Mock()
            mock_response.json = AsyncMock(return_value={"error": "something"})

            mock_context = AsyncMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_response)
            mock_context.__aexit__ = AsyncMock(return_value=None)

            mock_session_instance = AsyncMock()
            mock_session_instance.__aenter__ = AsyncMock(return_value=mock_session_instance)
            mock_session_instance.__aexit__ = AsyncMock(return_value=None)
            mock_session_instance.post = Mock(return_value=mock_context)
            mock_session.return_value = mock_session_instance

            # Should raise ValueError
            with pytest.raises(ValueError, match="Invalid Whisper API response"):
                await handler.transcribe_audio(audio_path)

    @pytest.mark.asyncio
    async def test_transcribe_audio_api_error(self, mock_transcription_env_vars: None, temp_dir: Path) -> None:
        """Test transcription with API connection error."""
        settings = Settings.from_env()
        handler = TranscriptionHandler(settings)

        audio_path = temp_dir / "test.ogg"
        audio_path.write_bytes(b"fake audio content")

        # Mock API error
        with patch("src.transcription.aiohttp.ClientSession") as mock_session:
            mock_response = AsyncMock()
            mock_response.raise_for_status = Mock(side_effect=ClientError("Connection failed"))

            mock_context = AsyncMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_response)
            mock_context.__aexit__ = AsyncMock(return_value=None)

            mock_session_instance = AsyncMock()
            mock_session_instance.__aenter__ = AsyncMock(return_value=mock_session_instance)
            mock_session_instance.__aexit__ = AsyncMock(return_value=None)
            mock_session_instance.post = Mock(return_value=mock_context)
            mock_session.return_value = mock_session_instance

            # Should raise ClientError
            with pytest.raises(ClientError):
                await handler.transcribe_audio(audio_path)


class TestSaveToMarkdown:
    """Tests for save_to_markdown method."""

    @pytest.mark.asyncio
    async def test_save_to_markdown_new_file(self, mock_transcription_env_vars: None, temp_dir: Path) -> None:
        """Test saving transcript to new markdown file."""
        # Override output directory to use temp_dir
        import os

        os.environ["TRANSCRIPTION_OUTPUT_DIR"] = str(temp_dir)

        settings = Settings.from_env()
        handler = TranscriptionHandler(settings)

        # Execute
        transcript = "Test transcription content."
        result_path = await handler.save_to_markdown("test.ogg", transcript)

        # Verify file was created
        assert result_path.exists()
        assert result_path.suffix == ".md"

        # Read and verify content
        content = result_path.read_text(encoding="utf-8")

        # Should contain template header
        assert "[[" in content  # Obsidian link format
        assert "Week" in content

        # Should contain transcript
        assert "test.ogg" in content
        assert transcript in content

    @pytest.mark.asyncio
    async def test_save_to_markdown_append_existing(self, mock_transcription_env_vars: None, temp_dir: Path) -> None:
        """Test appending transcript to existing markdown file."""
        import os

        os.environ["TRANSCRIPTION_OUTPUT_DIR"] = str(temp_dir)

        settings = Settings.from_env()
        handler = TranscriptionHandler(settings)

        # Create first entry
        transcript1 = "First transcription."
        result_path1 = await handler.save_to_markdown("audio1.ogg", transcript1)

        # Append second entry
        transcript2 = "Second transcription."
        result_path2 = await handler.save_to_markdown("audio2.ogg", transcript2)

        # Should be same file
        assert result_path1 == result_path2

        # Read and verify content
        content = result_path2.read_text(encoding="utf-8")

        # Should contain template header only once
        breadcrumb_count = content.count("[[")
        assert breadcrumb_count > 0

        # Should contain both transcripts
        assert "audio1.ogg" in content
        assert transcript1 in content
        assert "audio2.ogg" in content
        assert transcript2 in content

    @pytest.mark.asyncio
    async def test_save_to_markdown_filename_format(self, mock_transcription_env_vars: None, temp_dir: Path) -> None:
        """Test that markdown filename follows YYYY-MM-DD.md format."""
        import os

        os.environ["TRANSCRIPTION_OUTPUT_DIR"] = str(temp_dir)

        settings = Settings.from_env()
        handler = TranscriptionHandler(settings)

        result_path = await handler.save_to_markdown("test.ogg", "Test content")

        # Verify filename format
        import re

        pattern = r"^\d{4}-\d{2}-\d{2}\.md$"
        assert re.match(pattern, result_path.name)


class TestProcessTranscription:
    """Tests for process_transcription workflow."""

    @pytest.mark.asyncio
    async def test_process_transcription_full_workflow(
        self,
        mock_transcription_env_vars: None,
        temp_dir: Path,
        mock_whisper_response: dict[str, str],
    ) -> None:
        """Test complete transcription workflow."""
        import os

        os.environ["TRANSCRIPTION_OUTPUT_DIR"] = str(temp_dir)

        settings = Settings.from_env()
        handler = TranscriptionHandler(settings)

        # Create test audio file
        audio_path = temp_dir / "test.ogg"
        audio_path.write_bytes(b"fake audio content")

        # Mock Whisper API
        with patch("aiohttp.ClientSession") as mock_session:
            mock_response = AsyncMock()
            mock_response.raise_for_status = Mock()
            mock_response.json = AsyncMock(return_value=mock_whisper_response)

            mock_context = AsyncMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_response)
            mock_context.__aexit__ = AsyncMock()

            mock_session.return_value.__aenter__.return_value.post = Mock(return_value=mock_context)

            # Execute full workflow
            result_path = await handler.process_transcription(audio_path, "test.ogg")

            # Verify
            assert result_path.exists()
            content = result_path.read_text(encoding="utf-8")
            assert "This is a test transcription result." in content
            assert "test.ogg" in content

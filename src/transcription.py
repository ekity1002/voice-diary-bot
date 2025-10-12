"""Transcription module for Voice Diary Bot.

Handles audio transcription using Whisper API and markdown file generation.
"""

import logging
from datetime import datetime, timedelta
from pathlib import Path

import aiohttp

from .settings import Settings

logger = logging.getLogger(__name__)


class TranscriptionHandler:
    """Handler for audio transcription operations.

    Manages Whisper API calls and markdown file generation.
    """

    def __init__(self, settings: Settings) -> None:
        """Initialize the transcription handler.

        Args:
            settings: Application settings
        """
        self.settings = settings
        logger.info("TranscriptionHandler initialized")

    async def transcribe_audio(self, audio_path: Path) -> str:
        """Transcribe audio file using Whisper API.

        Args:
            audio_path: Path to audio file

        Returns:
            str: Transcribed text

        Raises:
            aiohttp.ClientError: If API request fails
            ValueError: If API response is invalid
        """
        logger.info(f"Transcribing audio with Whisper API: {audio_path}")

        # Construct API endpoint
        api_url = f"{self.settings.whisper_api_url}/v1/audio/transcriptions"

        try:
            # Read audio file content
            with open(audio_path, "rb") as audio_file:
                audio_content = audio_file.read()

            async with aiohttp.ClientSession() as session:
                # Prepare multipart form data
                data = aiohttp.FormData()

                # Add audio file with content
                data.add_field("file", audio_content, filename=audio_path.name, content_type="application/octet-stream")

                # Add model parameter
                data.add_field("model", self.settings.whisper_model)

                # Send request
                async with session.post(api_url, data=data) as response:
                    response.raise_for_status()
                    result = await response.json()

                    # Extract text from response
                    if "text" not in result:
                        raise ValueError(f"Invalid Whisper API response: {result}")

                    transcribed_text = result["text"]
                    if not isinstance(transcribed_text, str):
                        raise ValueError(f"Expected text to be str, got {type(transcribed_text)}")

                    logger.info(f"Transcription complete: {len(transcribed_text)} characters")
                    return transcribed_text

        except aiohttp.ClientError as e:
            logger.error(f"Whisper API request failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during transcription: {e}")
            raise

    def _generate_daily_template(self, date: datetime) -> str:
        """Generate Obsidian Daily note template header.

        Args:
            date: Date for the daily note

        Returns:
            str: Formatted template header with front matter, breadcrumb, week nav, and week days
        """
        # === Front Matter ===
        front_matter = "---\ntags:\n  - 日記\n---\n\n"

        # === Breadcrumb ===
        year = date.year
        quarter = (date.month - 1) // 3 + 1
        breadcrumb = f"[[{year}]] / [[{year}-Q{quarter}|Q{quarter}]] / [[{date.strftime('%Y-%m')}|{date.month}月]]"

        # === ISO Week ===
        _, iso_week, _ = date.isocalendar()
        prev_week = (date - timedelta(weeks=1)).isocalendar()
        next_week = (date + timedelta(weeks=1)).isocalendar()

        def week_link(year: int, week: int) -> str:
            return f"[[{year}-W{week:02d}|Week {week}]]"

        week_nav = f"❮ {week_link(prev_week[0], prev_week[1])} | Week {iso_week} | {week_link(next_week[0], next_week[1])} ❯"

        # === Same week day links (Monday start) ===
        start_of_week = date - timedelta(days=date.isoweekday() - 1)
        days = [
            f"[[{(start_of_week + timedelta(days=i)).strftime('%Y-%m-%d')}|{(start_of_week + timedelta(days=i)).strftime('%d')}]]" for i in range(7)
        ]
        week_days = " - ".join(days)

        return f"{front_matter}{breadcrumb}\n{week_nav}\n{week_days}\n\n"

    async def save_to_markdown(self, filename: str, transcript: str) -> Path:
        """Save transcript to markdown file.

        Creates or appends to a daily note file in YYYY-MM-DD.md format.
        New files include Obsidian Daily note template header.

        Args:
            filename: Original audio filename
            transcript: Transcribed text

        Returns:
            Path: Path to saved markdown file

        Raises:
            OSError: If file operations fail
        """
        logger.info(f"Saving transcript to markdown: {filename}")

        # Get current date for filename
        now = datetime.now()
        markdown_filename = now.strftime("%Y-%m-%d.md")
        output_dir = self.settings.transcription_output_dir
        markdown_path = output_dir / markdown_filename

        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)

        # Check if file exists
        file_exists = markdown_path.exists()

        try:
            # Prepare transcript entry
            timestamp = now.strftime("%H:%M:%S")
            transcript_entry = f"\n## {timestamp} - {filename}\n\n{transcript}\n"

            # Open file in append mode
            with open(markdown_path, "a", encoding="utf-8") as f:
                # If new file, write template header first
                if not file_exists:
                    logger.info(f"Creating new daily note: {markdown_path}")
                    template_header = self._generate_daily_template(now)
                    f.write(template_header)
                else:
                    logger.info(f"Appending to existing daily note: {markdown_path}")

                # Write transcript entry
                f.write(transcript_entry)

            logger.info(f"Transcript saved successfully to: {markdown_path}")
            return markdown_path

        except OSError as e:
            logger.error(f"Failed to save transcript to {markdown_path}: {e}")
            raise

    async def process_transcription(self, audio_path: Path, original_filename: str) -> Path:
        """Complete transcription workflow.

        Args:
            audio_path: Path to downloaded audio file
            original_filename: Original filename from Discord

        Returns:
            Path: Path to saved markdown file

        Raises:
            Exception: If transcription or saving fails
        """
        logger.info(f"Starting transcription workflow for: {original_filename}")

        # Step 1: Transcribe audio
        transcript = await self.transcribe_audio(audio_path)

        # Step 2: Save to markdown
        markdown_path = await self.save_to_markdown(original_filename, transcript)

        logger.info(f"Transcription workflow complete: {markdown_path}")
        return markdown_path

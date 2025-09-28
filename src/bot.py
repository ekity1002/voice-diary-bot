"""Discord bot module for Voice Diary Bot.

Handles Discord integration including message events, file downloads,
processing coordination, and user notifications.
"""

import logging
from pathlib import Path
from typing import Any

import aiohttp
import discord

from .ffmpeg_runner import FFmpegError, FFmpegRunner
from .settings import Settings
from .storage import StorageManager

logger = logging.getLogger(__name__)


class VoiceDiaryBot:
    """Discord bot that converts voice attachments to MP4 videos.

    Monitors specified channel for audio attachments, downloads them,
    converts to video using FFmpeg, and notifies users of results.
    """

    def __init__(self, settings: Settings) -> None:
        """Initialize the voice diary bot.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.storage = StorageManager(settings)
        self.ffmpeg = FFmpegRunner(settings)

        # Configure Discord intents
        intents = discord.Intents.default()
        intents.message_content = True

        # Initialize Discord client
        self.client = discord.Client(intents=intents)

        # Register event handlers
        self.client.event(self.on_ready)
        self.client.event(self.on_message)
        self.client.event(self.on_error)

    async def on_ready(self) -> None:
        """Handle bot ready event."""
        logger.info(f"Bot logged in as {self.client.user}")
        logger.info(f"Monitoring channel ID: {self.settings.channel_id}")

        # Validate FFmpeg installation
        if not await self.ffmpeg.validate_ffmpeg_installation():
            logger.error("FFmpeg is not installed or not accessible!")
        else:
            logger.info("FFmpeg installation validated successfully")

    async def on_message(self, message: discord.Message) -> None:
        """Handle incoming Discord messages.

        Args:
            message: Discord message object
        """
        # Ignore bot's own messages
        if message.author == self.client.user:
            return

        # Check if message is in the monitored channel
        if message.channel.id != self.settings.channel_id:
            return

        # Check for audio attachments
        audio_attachments = self._get_audio_attachments(message)

        if not audio_attachments:
            return

        # Process each audio attachment
        for attachment in audio_attachments:
            await self._process_audio_attachment(message, attachment)

    async def on_error(self, event: str, *args: Any, **kwargs: Any) -> None:
        """Handle Discord client errors.

        Args:
            event: Event name where error occurred
        """
        logger.exception(f"Discord client error in event {event}")

    def _get_audio_attachments(
        self, message: discord.Message
    ) -> list[discord.Attachment]:
        """Extract audio attachments from message.

        Args:
            message: Discord message to check

        Returns:
            list[discord.Attachment]: List of audio attachments
        """
        audio_attachments = []

        for attachment in message.attachments:
            # Check if attachment is an audio file
            if attachment.content_type and attachment.content_type.startswith("audio/"):
                # Check file size
                if attachment.size > self.settings.max_file_size:
                    logger.warning(
                        f"Audio file {attachment.filename} is too large: "
                        f"{attachment.size} bytes (max: {self.settings.max_file_size})"
                    )
                    continue

                audio_attachments.append(attachment)

        return audio_attachments

    async def _process_audio_attachment(
        self, message: discord.Message, attachment: discord.Attachment
    ) -> None:
        """Process a single audio attachment.

        Args:
            message: Original Discord message
            attachment: Audio attachment to process
        """
        logger.info(f"Processing audio attachment: {attachment.filename}")

        # Generate file paths
        inbox_path = self.storage.get_inbox_path(attachment.filename)
        output_path = self.storage.get_output_path(attachment.filename)

        try:
            # Send initial processing message
            processing_msg = await message.reply(
                f"🎵 Processing audio file: `{attachment.filename}`"
            )

            # Download audio file
            await self._download_attachment(attachment, inbox_path)
            logger.info(f"Downloaded {attachment.filename} to {inbox_path}")

            # Convert to video
            await self.ffmpeg.convert_audio_to_video(inbox_path, output_path)
            logger.info(f"Converted {attachment.filename} to {output_path}")

            # Send success message
            await processing_msg.edit(
                content=f"✅ Successfully converted `{attachment.filename}` to video! "
                f"Output: `{output_path.name}`"
            )

            # Cleanup inbox file
            self.storage.cleanup_inbox_file(inbox_path)

            # Optionally cleanup output file
            if self.settings.delete_on_success:
                self.storage.cleanup_output_file(output_path)
                logger.info(f"Cleaned up output file: {output_path}")

        except aiohttp.ClientError as e:
            error_msg = f"❌ Failed to download `{attachment.filename}`: Network error"
            logger.error(f"Download failed for {attachment.filename}: {e}")
            await self._send_error_message(message, error_msg)

        except FFmpegError as e:
            error_msg = (
                f"❌ Failed to convert `{attachment.filename}`: Video processing error"
            )
            logger.error(f"FFmpeg error for {attachment.filename}: {e}")
            await self._send_error_message(message, error_msg)

            # Cleanup inbox file on error
            self.storage.cleanup_inbox_file(inbox_path)

        except Exception as e:
            error_msg = f"❌ Unexpected error processing `{attachment.filename}`"
            logger.exception(f"Unexpected error processing {attachment.filename}: {e}")
            await self._send_error_message(message, error_msg)

            # Cleanup inbox file on error
            self.storage.cleanup_inbox_file(inbox_path)

    async def _download_attachment(
        self, attachment: discord.Attachment, output_path: Path
    ) -> None:
        """Download Discord attachment to local file.

        Args:
            attachment: Discord attachment to download
            output_path: Local path to save file

        Raises:
            aiohttp.ClientError: If download fails
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(attachment.url) as response:
                response.raise_for_status()

                with open(output_path, "wb") as f:
                    async for chunk in response.content.iter_chunked(8192):
                        f.write(chunk)

        # Validate downloaded file size
        if not self.storage.validate_file_size(output_path):
            raise ValueError(f"Downloaded file exceeds size limit: {output_path}")

    async def _send_error_message(
        self, message: discord.Message, error_text: str
    ) -> None:
        """Send error message to Discord channel.

        Args:
            message: Original message to reply to
            error_text: Error message to send
        """
        try:
            await message.reply(error_text)
        except discord.DiscordException as e:
            logger.error(f"Failed to send error message: {e}")

    async def start(self) -> None:
        """Start the Discord bot."""
        logger.info("Starting Discord bot...")
        await self.client.start(self.settings.discord_token)

    async def close(self) -> None:
        """Close the Discord bot connection."""
        logger.info("Closing Discord bot...")
        await self.client.close()

    def run(self) -> None:
        """Run the Discord bot (blocking).

        This is a convenience method that runs the bot using discord.py's
        built-in event loop management.
        """
        self.client.run(self.settings.discord_token)

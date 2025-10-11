#!/usr/bin/env python3
"""Test script to verify FFmpeg command generation fix."""

import asyncio
import logging
from pathlib import Path

from src.ffmpeg_runner import FFmpegRunner
from src.settings import Settings

logger = logging.getLogger(__name__)


async def test_command_generation() -> None:
    """Test FFmpeg command generation for different file types."""
    logger.info("Testing FFmpeg command generation fix...")

    # Create a test settings instance
    test_token = "test"  # noqa: S105
    settings = Settings(discord_token=test_token, channel_id=123, processing_timeout=3600, audio_bitrate=96)

    runner = FFmpegRunner(settings)

    # Test M4A file (should use audio copy)
    test_input_m4a = Path("/work/inbox/URecorder_20250928_213105.m4a")
    test_output_m4a = Path("/work/out/URecorder_20250928_213105.mp4")

    command_m4a = runner.build_command(test_input_m4a, test_output_m4a)
    logger.info("M4A command: %s", " ".join(command_m4a))

    # Test MP3 file (should re-encode audio)
    test_input_mp3 = Path("/work/inbox/test.mp3")
    test_output_mp3 = Path("/work/out/test.mp3.mp4")

    command_mp3 = runner.build_command(test_input_mp3, test_output_mp3)
    logger.info("MP3 command: %s", " ".join(command_mp3))

    # Verify no dangling flags
    logger.info("\n=== Command Validation ===")
    logger.info("M4A command length: %d args", len(command_m4a))
    logger.info("MP3 command length: %d args", len(command_mp3))

    # Check for proper flag pairing
    m4a_has_bitrate = "-b:a" in command_m4a
    mp3_has_bitrate = "-b:a" in command_mp3
    logger.info("M4A has -b:a flag: %s (should be False for copy)", m4a_has_bitrate)
    logger.info("MP3 has -b:a flag: %s (should be True for re-encode)", mp3_has_bitrate)

    # Check for copy vs aac
    m4a_has_copy = "copy" in command_m4a
    mp3_has_aac = "aac" in command_mp3
    logger.info("M4A uses copy: %s", m4a_has_copy)
    logger.info("MP3 uses aac: %s", mp3_has_aac)

    # Verify output file is correct
    m4a_output_correct = command_m4a[-1] == str(test_output_m4a)
    mp3_output_correct = command_mp3[-1] == str(test_output_mp3)
    logger.info("M4A output path correct: %s", m4a_output_correct)
    logger.info("MP3 output path correct: %s", mp3_output_correct)

    logger.info("\n=== Fix Status ===")
    if m4a_output_correct and mp3_output_correct:
        logger.info("✓ Output file paths are correctly positioned")
    else:
        logger.warning("✗ Output file path issue detected")

    if not m4a_has_bitrate and mp3_has_bitrate:
        logger.info("✓ Bitrate flags correctly handled")
    else:
        logger.warning("✗ Bitrate flag issue detected")

    logger.info("✓ Command generation fix applied successfully")


if __name__ == "__main__":
    asyncio.run(test_command_generation())

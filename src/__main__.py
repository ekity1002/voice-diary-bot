"""Main entry point for Discord Voice Diary Bot.

Provides application initialization, configuration loading,
bot lifecycle management, and graceful shutdown handling.
"""

import asyncio
import logging
import signal
import sys
from typing import Any

from .bot import VoiceDiaryBot
from .settings import Settings


class Application:
    """Main application class for the Discord Voice Diary Bot."""

    def __init__(self) -> None:
        """Initialize the application."""
        self.bot: VoiceDiaryBot | None = None
        self.settings: Settings | None = None
        self._shutdown_event = asyncio.Event()

    def setup_logging(self) -> None:
        """Configure application logging."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.StreamHandler(sys.stdout),
            ],
        )

        # Set discord.py logging level to WARNING to reduce noise
        logging.getLogger("discord").setLevel(logging.WARNING)
        logging.getLogger("discord.http").setLevel(logging.WARNING)

    def setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""

        def signal_handler(signum: int, frame: Any) -> None:
            """Handle shutdown signals."""
            logger = logging.getLogger(__name__)
            logger.info(f"Received signal {signum}, initiating shutdown...")
            self._shutdown_event.set()

        # Register signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    async def initialize(self) -> None:
        """Initialize application components."""
        logger = logging.getLogger(__name__)

        try:
            # Load settings from environment
            self.settings = Settings.from_env()
            logger.info("Settings loaded successfully")
            logger.info(f"Bot mode: {self.settings.bot_mode.value}")

            # Initialize bot
            self.bot = VoiceDiaryBot(self.settings)
            logger.info("Bot initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize application: {e}")
            raise

    async def run(self) -> None:
        """Run the main application."""
        logger = logging.getLogger(__name__)

        try:
            # Start bot
            if self.bot is None:
                raise RuntimeError("Bot not initialized. Call initialize() first.")
            bot_task = asyncio.create_task(self.bot.start())
            shutdown_task = asyncio.create_task(self._shutdown_event.wait())

            logger.info("Application started successfully")

            # Wait for either bot completion or shutdown signal
            done, pending = await asyncio.wait({bot_task, shutdown_task}, return_when=asyncio.FIRST_COMPLETED)

            # Cancel remaining tasks
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

            # Check if bot task completed with an exception
            if bot_task in done:
                try:
                    await bot_task
                except Exception as e:
                    logger.error(f"Bot task failed: {e}")
                    raise

        except Exception as e:
            logger.error(f"Application error: {e}")
            raise

        finally:
            await self.shutdown()

    async def shutdown(self) -> None:
        """Shutdown application gracefully."""
        logger = logging.getLogger(__name__)
        logger.info("Shutting down application...")

        if self.bot:
            try:
                await self.bot.close()
                logger.info("Bot closed successfully")
            except Exception as e:
                logger.error(f"Error closing bot: {e}")

        logger.info("Application shutdown complete")


async def main() -> None:
    """Main entry point."""
    app = Application()

    # Setup logging and signal handlers
    app.setup_logging()
    app.setup_signal_handlers()

    try:
        # Initialize and run application
        await app.initialize()
        await app.run()

    except KeyboardInterrupt:
        logging.getLogger(__name__).info("Received keyboard interrupt")
    except Exception as e:
        logging.getLogger(__name__).error(f"Application failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Run the application
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.getLogger(__name__).info("Shutdown complete")
    except Exception as e:
        logging.getLogger(__name__).error(f"Fatal error: {e}")
        sys.exit(1)

# Multi-stage build for Discord Voice Diary Bot
# Stage 1: Build dependencies
FROM python:3.12-slim as builder

# Install system dependencies needed for building
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /build

# Copy dependency files and source code
COPY pyproject.toml ./
COPY src/ src/

# Create a virtual environment and install dependencies
ENV UV_VENV=/opt/venv
RUN uv venv $UV_VENV && \
    . $UV_VENV/bin/activate && \
    uv pip install --no-cache .

# Stage 2: Production image
FROM python:3.12-slim

# Install runtime dependencies including FFmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN groupadd -r voicediary && useradd -r -g voicediary voicediary

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Set up environment
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH="/app/src:$PYTHONPATH"

# Create work directory structure
RUN mkdir -p /work/inbox /work/out /work/assets && \
    chown -R voicediary:voicediary /work

# Create app directory
WORKDIR /app
RUN chown voicediary:voicediary /app

# Copy application code
COPY --chown=voicediary:voicediary src/ src/
COPY --chown=voicediary:voicediary assets/ assets/

# Copy default assets to work directory
RUN cp -r assets/* /work/assets/ && \
    chown -R voicediary:voicediary /work/assets

# Switch to non-root user
USER voicediary

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import asyncio; from src.ffmpeg_runner import FFmpegRunner; from src.settings import Settings; \
    async def check(): \
        settings = Settings.from_env(); \
        runner = FFmpegRunner(settings); \
        return await runner.validate_ffmpeg_installation(); \
    exit(0 if asyncio.run(check()) else 1)"

# Set work directory as volume mount point
VOLUME ["/work"]

# Expose no ports (this is a Discord bot, not a web service)

# Default command
CMD ["python", "-m", "src"]

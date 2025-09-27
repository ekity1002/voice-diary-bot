# Discord Voice Diary Bot - Technical Design

## Architecture Overview

### System Architecture
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Discord API   │◄──►│  Discord Bot     │◄──►│   File System   │
│                 │    │  (bot.py)        │    │   (/work)       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │  FFmpeg Runner   │
                       │ (ffmpeg_runner.py)│
                       └──────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │     Storage      │
                       │  (storage.py)    │
                       └──────────────────┘
```

### Component Responsibilities

**bot.py** - Discord Integration Layer
- Discord event handling and message filtering
- File download and upload coordination
- User communication and error reporting

**ffmpeg_runner.py** - Media Processing Layer
- FFmpeg command execution and management
- Audio/video conversion logic
- Process monitoring and error handling

**storage.py** - File Management Layer
- Path generation and validation
- Directory structure management
- File cleanup and lifecycle management

**settings.py** - Configuration Layer
- Environment variable loading and validation
- Configuration schema definition
- Default value management

## Detailed Component Design

### 1. bot.py - Discord Integration

#### Class Structure
```python
class VoiceDiaryBot:
    def __init__(self, token: str, channel_id: int)
    async def on_ready(self) -> None
    async def on_message(self, message: discord.Message) -> None
    async def process_audio_attachment(self, attachment: discord.Attachment, message: discord.Message) -> None
    async def download_attachment(self, attachment: discord.Attachment, file_path: Path) -> bool
    async def send_completion_message(self, message: discord.Message, output_path: Path) -> None
    async def send_error_message(self, message: discord.Message, error: str) -> None
```

#### Event Flow
1. **on_message** - Filter messages by channel ID and audio attachments
2. **process_audio_attachment** - Coordinate download → conversion → notification
3. **download_attachment** - HTTP download with error handling
4. **send_completion_message** - Success notification with file info
5. **send_error_message** - Error notification with details

#### Error Handling Strategy
- Network errors: Retry with exponential backoff
- File size errors: Immediate user notification
- Processing errors: Cleanup partial files and notify
- Discord API errors: Log and attempt graceful recovery

### 2. ffmpeg_runner.py - Media Processing

#### Class Structure
```python
class FFmpegRunner:
    def __init__(self, background_image: Path)
    async def convert_audio_to_video(self, audio_path: Path, output_path: Path) -> ConversionResult
    def build_ffmpeg_command(self, audio_path: Path, output_path: Path) -> list[str]
    async def execute_command(self, command: list[str]) -> subprocess.CompletedProcess
    def validate_output(self, output_path: Path) -> bool
```

#### Conversion Pipeline
```python
@dataclass
class ConversionResult:
    success: bool
    output_path: Optional[Path]
    error_message: Optional[str]
    processing_time: float
```

#### FFmpeg Command Template
```bash
ffmpeg -y \
  -loop 1 -i {background_image} \
  -i {input_audio} \
  -c:v libx264 -tune stillimage -pix_fmt yuv420p \
  -c:a aac -b:a {audio_bitrate}k -ac 1 \
  -shortest \
  -movflags +faststart \
  {output_video}
```

**Audio Bitrate Configuration**: 64-128 kbps range (configurable, default: 96k)

#### Process Management
- Timeout: 300 seconds maximum processing time
- Resource limits: Memory and CPU constraints
- Cleanup: Temporary file removal on failure
- Validation: Output file existence and basic integrity

### 3. storage.py - File Management

#### Class Structure
```python
class StorageManager:
    def __init__(self, work_dir: Path, delete_on_success: bool)
    def get_inbox_path(self, message_id: int, extension: str) -> Path
    def get_output_path(self, message_id: int) -> Path
    def ensure_directories(self) -> None
    def cleanup_file(self, file_path: Path) -> bool
    def get_file_info(self, file_path: Path) -> FileInfo
```

#### Directory Structure
```
/work/
├── inbox/          # Temporary audio downloads
│   ├── {message_id}.m4a
│   └── {message_id}.mp3
├── out/            # Generated MP4 videos
│   ├── {message_id}.mp4
│   └── {message_id}.mp4
└── assets/         # Static resources
    └── bg.jpg      # Background image
```

#### File Lifecycle
1. **Download** → `/work/inbox/{message_id}.{ext}`
2. **Processing** → Input from inbox, output to `/work/out/`
3. **Cleanup** → Remove inbox file based on `DELETE_ON_SUCCESS`
4. **Retention** → Keep output files for manual management

### 4. settings.py - Configuration

#### Configuration Schema
```python
@dataclass
class Settings:
    # Required
    discord_token: str
    channel_id: int

    # Optional with defaults
    work_dir: Path = Path("/work")
    background_image: Path = Path("/work/assets/bg.jpg")
    delete_on_success: bool = False

    # Audio processing
    audio_bitrate: int = 96  # kbps, range: 64-128

    # Processing limits
    max_file_size: int = 25 * 1024 * 1024  # 25MB
    processing_timeout: int = 300  # 5 minutes

    @classmethod
    def from_env(cls) -> "Settings"
    def validate(self) -> None
```

#### Environment Variable Mapping
```env
DISCORD_TOKEN=<required>
CHANNEL_ID=<required>
WORK_DIR=/work
BACKGROUND_IMAGE=/work/assets/bg.jpg
DELETE_ON_SUCCESS=false
AUDIO_BITRATE=96
MAX_FILE_SIZE=26214400
PROCESSING_TIMEOUT=300
```

## Data Flow Design

### Primary Processing Flow
```
Discord Message
       │
       ▼
   Channel Filter ──► Channel ID Match?
       │                    │
       ▼                    ▼ No
 Audio Attachment?        Ignore
       │
       ▼ Yes
   Download File
       │
       ▼
   FFmpeg Convert
       │
       ▼
   Success? ──► No ──► Error Message
       │
       ▼ Yes
   Completion Message
       │
       ▼
   Cleanup (optional)
```

### Error Handling Flow
```
Error Occurs
       │
       ▼
   Log Error Details
       │
       ▼
   Cleanup Partial Files
       │
       ▼
   Send User Notification
       │
       ▼
   Continue Processing
```

## Development Environment Design

### DevContainer Configuration

#### devcontainer.json Structure
```json
{
  "name": "Discord Voice Diary Bot",
  "dockerFile": "Dockerfile.dev",
  "features": {
    "ghcr.io/devcontainers/features/python:1": {
      "version": "3.12"
    }
  },
  "customizations": {
    "vscode": {
      "extensions": [
        "ms-python.python",
        "ms-python.flake8",
        "charliermarsh.ruff",
        "ms-python.mypy-type-checker"
      ],
      "settings": {
        "python.defaultInterpreterPath": "/usr/local/bin/python",
        "python.linting.enabled": true,
        "ruff.organizeImports": true,
        "editor.formatOnSave": true
      }
    }
  },
  "forwardPorts": [8000],
  "mounts": [
    "source=${localWorkspaceFolder}/data,target=/work,type=bind"
  ]
}
```

#### Development Dockerfile
```dockerfile
FROM mcr.microsoft.com/devcontainers/python:3.12

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Set up development environment
USER vscode
COPY pyproject.toml uv.lock ./
RUN uv sync --dev

# Set up work directory
RUN mkdir -p /work/inbox /work/out /work/assets
RUN chown -R vscode:vscode /work
```

### Code Quality Tools Configuration

#### pyproject.toml - Tool Configuration
```toml
[tool.ruff]
target-version = "py312"
line-length = 88
select = ["E", "F", "I", "N", "W", "UP", "S", "B", "A", "C4", "T20"]
ignore = ["S101"]  # Allow assert statements in tests

[tool.ruff.per-file-ignores]
"tests/*" = ["S101", "B011"]

[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
python_files = ["test_*.py"]
```

#### Pre-commit Configuration
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.6
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

## Testing Strategy

### Test Structure
```
tests/
├── unit/
│   ├── test_ffmpeg_runner.py
│   ├── test_storage.py
│   └── test_settings.py
├── integration/
│   ├── test_bot_integration.py
│   └── test_file_processing.py
└── fixtures/
    ├── sample_audio.m4a
    └── test_bg.jpg
```

### Test Categories

#### Unit Tests
- FFmpeg command generation
- File path validation
- Configuration loading
- Error handling logic

#### Integration Tests
- End-to-end file processing
- Discord mock integration
- Container environment validation

#### Test Data Management
- Sample audio files for conversion
- Mock Discord messages and attachments
- Test environment configuration

## Deployment Design

### Production Container

#### Multi-stage Dockerfile
```dockerfile
# Build stage
FROM python:3.12-slim as builder
RUN pip install uv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Runtime stage
FROM python:3.12-slim
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY src/ /app/src/
COPY assets/ /work/assets/
RUN useradd -m -u 1000 bot && chown -R bot:bot /work
USER bot
WORKDIR /app
CMD ["python", "-m", "src.bot"]
```

#### Docker Compose Configuration
```yaml
version: '3.8'
services:
  voice-diary-bot:
    build: .
    restart: unless-stopped
    env_file: .env
    volumes:
      - ./data:/work
    healthcheck:
      test: ["CMD", "pgrep", "-f", "python"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## Security Considerations

### Token Management
- Discord token via environment variables only
- No token logging or exposure in error messages
- Container secrets management

### File System Security
- Non-root container execution
- Restricted file permissions
- Input validation for file paths
- Temporary file cleanup

### Resource Limits
- Maximum file size enforcement
- Processing timeout limits
- Memory usage constraints
- Disk space monitoring

## Performance Considerations

### Processing Optimization
- Async/await for I/O operations
- FFmpeg hardware acceleration support
- Parallel processing for multiple files
- Resource usage monitoring

### Memory Management
- Streaming file downloads
- Temporary file cleanup
- Container memory limits
- Garbage collection optimization

### Scalability Preparation
- Stateless bot design
- External storage compatibility
- Queue-based processing support
- Horizontal scaling readiness

## Monitoring and Observability

### Logging Strategy
- Structured logging with JSON format
- Log levels: DEBUG, INFO, WARNING, ERROR
- Request correlation IDs
- Performance metrics logging

### Health Checks
- Container process monitoring
- Discord API connectivity
- File system availability
- FFmpeg executable validation

### Metrics Collection
- Processing success/failure rates
- File size and processing time
- Memory and CPU usage
- Error categorization and frequency

## Future Extension Points

### Phase 2 - YouTube Integration
- YouTube API client integration
- OAuth2 authentication flow
- Video metadata management
- Upload progress tracking

### Enhanced Features
- Multiple background image support
- Audio processing filters
- Batch processing capabilities
- Web interface for configuration

### Infrastructure Improvements
- Database integration for state management
- Message queue for processing pipeline
- Microservice architecture migration
- Cloud storage integration

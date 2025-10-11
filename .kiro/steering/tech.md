# Technology Stack & Architectural Decisions

## Core Technologies

### Language & Runtime
- **Python 3.12**: Modern Python with latest features and performance improvements
- **asyncio**: Asynchronous programming for Discord integration and file processing
- **uv**: Fast Python package management and dependency resolution

### Key Dependencies
- **discord.py 2.3+**: Official Discord API client library
- **python-dotenv**: Environment variable management
- **aiohttp 3.9+**: Async HTTP client for file downloads
- **FFmpeg**: Media processing engine (external system dependency)

### Development Tools
- **Ruff**: Fast Python linter and formatter (replaces black, flake8, isort)
- **mypy**: Static type checking with strict mode enabled
- **pytest**: Testing framework with async support
- **pre-commit**: Git hooks for code quality enforcement

## Architecture Patterns

### Component Structure
```
src/
├── bot.py          # Discord integration & event handling
├── ffmpeg_runner.py # Media processing with FFmpeg
├── storage.py      # File system operations
└── settings.py     # Configuration management
```

### Design Principles
1. **Separation of Concerns**: Each module has single responsibility
2. **Async-First**: All I/O operations use async/await patterns
3. **Error Handling**: Comprehensive exception handling with user feedback
4. **Type Safety**: Full type annotations with mypy strict mode
5. **Configuration Driven**: All behavior configurable via environment variables

### Error Handling Strategy
- **Graceful Degradation**: Bot continues operating despite individual file failures
- **User Feedback**: Clear Discord messages for success/failure states
- **Comprehensive Logging**: Detailed logs for debugging and monitoring
- **Resource Cleanup**: Automatic cleanup of temporary files on errors

## Infrastructure Decisions

### Containerization
- **Docker**: Consistent deployment environment across development and production
- **Docker Compose**: Simplified orchestration with volume mounts for data persistence
- **Multi-stage builds**: Optimized container images

### File Management
- **Volume Mounts**: Persistent storage for processed files
- **Structured Directories**: `data/inbox/` for downloads, `data/out/` for results
- **Configurable Cleanup**: Optional deletion of processed files

### Security Considerations
- **No Secret Embedding**: All sensitive data via environment variables
- **File Size Limits**: Configurable maximum file size protection
- **Input Validation**: Strict content type checking for audio files

## Development Environment

### DevContainer Support
- **VSCode Integration**: Consistent development environment
- **Pre-configured Tools**: All linting, formatting, and testing tools ready
- **Docker-based**: Matches production environment closely

### Code Quality Standards
- **Line Length**: 150 characters (configured in ruff)
- **Import Sorting**: First-party imports separate from third-party
- **Type Coverage**: 100% type annotation requirement
- **Test Coverage**: Comprehensive unit and integration tests

## Performance Considerations
- **Async Processing**: Non-blocking Discord message handling
- **Stream Processing**: Chunked file downloads to manage memory
- **FFmpeg Optimization**: Efficient media processing with configurable quality settings
- **Resource Monitoring**: Logging for performance tracking

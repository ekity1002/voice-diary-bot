#!/bin/bash
set -euo pipefail

echo "🚀 Starting devcontainer setup..."

# Load environment variables
if [ -f "$(dirname "$0")/.env" ]; then
    echo "📄 Loading environment variables..."
    source "$(dirname "$0")/.env"
else
    echo "⚠️  No .env file found, using default values"
    GIT_USER_EMAIL="user@example.com"
    GIT_USER_NAME="Devcontainer User"
fi

# Configure git
echo "📝 Configuring git..."
git config --global user.email "${GIT_USER_EMAIL}"
git config --global user.name "${GIT_USER_NAME}"
echo "✅ Git configured with email: ${GIT_USER_EMAIL}, name: ${GIT_USER_NAME}"

# Install npm packages
echo "📦 Installing npm packages..."
npm install -g npm @anthropic-ai/claude-code
echo "✅ npm packages installed"

# Install Python dependencies including dev dependencies
echo "🐍 Installing Python dependencies with uv..."
uv pip install --editable ".[dev]"
echo "✅ Python dependencies installed"

# Verify pre-commit is available
echo "🔍 Verifying pre-commit availability..."
if uv run pre-commit --version; then
    echo "✅ pre-commit is available"
else
    echo "❌ pre-commit not available, retrying..."
    sleep 3
    uv run pre-commit --version
fi

# Install pre-commit hooks
echo "🪝 Installing pre-commit hooks..."
uv run pre-commit install
echo "✅ Pre-commit hooks installed"

echo "🎉 Devcontainer setup complete!"

#!/bin/bash
# Purisa CLI Install Script
# Installs the 'purisa' command to your system

set -e

echo "🔧 Installing Purisa CLI..."
echo ""

# Get the directory where this script lives
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Determine install location
if [ -w "/usr/local/bin" ]; then
    INSTALL_DIR="/usr/local/bin"
else
    INSTALL_DIR="$HOME/.local/bin"
    # Create directory if it doesn't exist
    mkdir -p "$INSTALL_DIR"
fi

# Create symlink
echo "Creating symlink in $INSTALL_DIR..."
ln -sf "$SCRIPT_DIR/purisa" "$INSTALL_DIR/purisa"

# Check if install dir is in PATH
if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
    echo ""
    echo "⚠️  Warning: $INSTALL_DIR is not in your PATH"
    echo ""
    echo "Add this line to your ~/.bashrc or ~/.zshrc:"
    echo "  export PATH=\"\$PATH:$INSTALL_DIR\""
    echo ""
else
    echo ""
    echo "✅ Purisa CLI installed successfully!"
    echo ""
    echo "Try it out:"
    echo "  purisa --help"
    echo "  purisa collect --platform bluesky --query \"#politics\" --limit 50"
    echo "  purisa analyze --platform bluesky --hours 6"
    echo "  purisa spikes --platform bluesky"
    echo "  purisa stats"
    echo ""
fi

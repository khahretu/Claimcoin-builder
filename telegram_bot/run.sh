#!/bin/bash
# Run script for Telegram Bot

cd "$(dirname "$0")"

# Install dependencies if needed
if ! python3 -c "import telegram" 2>/dev/null; then
    echo "Installing dependencies..."
    pip3 install -r requirements.txt
fi

# Create necessary directories
mkdir -p data
mkdir -p /var/www/wallet-api/pages

# Run the bot
echo "Starting Telegram Bot..."
python3 bot.py

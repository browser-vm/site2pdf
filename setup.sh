#!/bin/bash

# Stop script on error
set -e

echo "🚀 Starting Playwright Setup..."

# --- Step 0: Remove Broken Yarn Repo (Fixes GPG Errors) ---
if [ -f /etc/apt/sources.list.d/yarn.list ]; then
    echo "🗑️  Found broken Yarn source list. Removing it to fix apt-get..."
    sudo rm /etc/apt/sources.list.d/yarn.list
else
    echo "✅ Yarn source list not found (or already removed). Proceeding..."
fi

# --- Step 1: Update System Packages ---
echo "📦 Updating package lists..."
# We run this to ensure we have fresh lists
sudo apt-get update -y

# --- Step 2: Uninstall Old Playwright Versions ---
echo "🧹 Removing old Playwright versions (if any)..."
pip uninstall -y playwright || echo "No existing Playwright installation found. Skipping..."

# --- Step 3: Install Python Dependencies ---
echo "🐍 Installing Python libraries..."
pip install -r requirements.txt

# --- Step 4: Install Playwright Browsers ---
echo "🌐 Downloading Playwright browsers..."
playwright install chromium

# --- Step 5: Install System Dependencies ---
echo "🏗️  Installing system dependencies (this may take a minute)..."
sudo playwright install-deps

echo "✅ Setup Complete! You can now run your scripts."
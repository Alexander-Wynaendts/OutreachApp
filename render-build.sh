#!/usr/bin/env bash

# Create a folder to store Chrome and Chromedriver locally
mkdir -p ~/chrome && cd ~/chrome

# Install Chromium locally
apt-get update && apt-get install -y wget unzip
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
dpkg -x google-chrome-stable_current_amd64.deb ./

# Download ChromeDriver locally if it doesn't exist or overwrite without prompt
CHROME_DRIVER_VERSION=$(curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE)
wget -N https://chromedriver.storage.googleapis.com/$CHROME_DRIVER_VERSION/chromedriver_linux64.zip
unzip -o chromedriver_linux64.zip  # Force overwrite without asking
chmod +x chromedriver

# Move ChromeDriver to a known location in the local directory
mv -f chromedriver ~/chrome/chromedriver

# Verify the installations
~/chrome/opt/google/chrome/google-chrome --version
~/chrome/chromedriver --version

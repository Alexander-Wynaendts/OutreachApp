#!/usr/bin/env bash

# Créer un dossier pour Chrome
mkdir -p ~/chrome && cd ~/chrome

# Installer Chromium localement
apt-get update && apt-get install -y wget unzip
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
dpkg -x google-chrome-stable_current_amd64.deb ./

# Télécharger ChromeDriver localement
CHROME_DRIVER_VERSION=$(curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE)
wget -N https://chromedriver.storage.googleapis.com/$CHROME_DRIVER_VERSION/chromedriver_linux64.zip
unzip chromedriver_linux64.zip
chmod +x chromedriver

# Déplacer ChromeDriver dans le dossier local
mv chromedriver ~/chrome/chromedriver

# Vérifier les installations locales
~/chrome/opt/google/chrome/google-chrome --version
~/chrome/chromedriver --version

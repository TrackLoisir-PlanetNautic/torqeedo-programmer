#!/bin/bash

# Nom du projet et version de l'application
APP_NAME="ToreedoProgrammer"
VERSION="2.0.8"

# Création de l'environnement virtuel si non existant
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activation de l'environnement virtuel
source venv/bin/activate

# Installation des dépendances
pip install -r requirements.txt
pip install py2app

# Création du fichier setup.py si non existant
if [ ! -f "setup.py" ]; then
cat > setup.py <<EOF
from setuptools import setup

APP = ['main.py']
DATA_FILES = [('images'),['Ressources/Full_logo_black.png'])]
PACKAGES = ['Frames', 'certifi', 'esptool', 'espefuse', espsecure']
OPTIONS = {
    'packages': PACKAGES,
    'resources': DATA_FILES,
}

setup(
    app=APP,
    name='$APP_NAME-$VERSION',
    version='$VERSION',
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
EOF
fi

# Création de l'application .app
python setup.py py2app

# Création du fichier .dmg
hdiutil create dist/$APP_NAME-$VERSION.dmg -volname "$APP_NAME $VERSION" -srcfolder dist/$APP_NAME.app

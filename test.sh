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
pip install pyinstaller

# Compilation de l'application avec PyInstaller
# L'option -w permet de générer une application sans console (GUI uniquement)
# L'option --onefile génère un exécutable unique
pyinstaller main.py -w --onefile --name="$APP_NAME-$VERSION" --add-data="Ressources/Full_logo_black.png:images"

# Déplacement de l'exécutable dans un dossier de distribution spécifique
DIST_DIR="dist/$APP_NAME-$VERSION"
mkdir -p $DIST_DIR
mv dist/"$APP_NAME-$VERSION" $DIST_DIR

# Création du fichier .dmg
hdiutil create $DIST_DIR.dmg -volname "$APP_NAME $VERSION" -srcfolder $DIST_DIR

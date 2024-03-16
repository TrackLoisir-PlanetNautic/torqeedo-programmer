from setuptools import setup

APP = ['main.py']
DATA_FILES = ['Ressources/Full_logo_black.png']
OPTIONS = {
    'argv_emulation': True,
    'packages': ['certifi'],
    'resources': DATA_FILES,
}

setup(
    app=APP,
    name='ToreedoProgrammer',
    version='1.1',
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)

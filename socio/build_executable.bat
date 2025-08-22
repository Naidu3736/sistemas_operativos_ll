@echo off
echo Instalando PyInstaller si no está presente...
pip install pyinstaller

echo Creando ejecutable...
pyinstaller --name="BuddySystemVisualizer" --windowed --onefile --add-data "utils;utils" main.py

echo.
echo ¡Ejecutable creado!
echo Encuentra tu archivo .exe en la carpeta 'dist'
pause
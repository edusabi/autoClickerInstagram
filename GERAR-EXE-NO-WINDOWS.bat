@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Instalando dependencias e compilador...
py -3 -m pip install --upgrade pip pyinstaller -r requirements.txt
if errorlevel 1 goto erro
echo.
echo Gerando AutoClicker.exe...
py -3 -m PyInstaller --noconfirm --clean --onefile --windowed --name AutoClicker --add-data "seguindo.jpeg;." --add-data "confirmar.jpeg;." script.py
if errorlevel 1 goto erro
echo.
echo Pronto! O executavel esta em dist\AutoClicker.exe
pause
exit /b 0
:erro
echo Ocorreu um erro. Confira se Python 3 esta instalado e se ha internet.
pause
exit /b 1

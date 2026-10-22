@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Instalando dependencias do AutoClicker...
py -m pip install --upgrade pip
if errorlevel 1 goto erro
py -m pip install -r requirements.txt
if errorlevel 1 goto erro
echo.
echo Instalação concluída. Para abrir, execute INICIAR.bat.
pause
exit /b 0
:erro
echo.
echo Não foi possível instalar automaticamente. Verifique se Python 3 está instalado e adicionado ao PATH.
pause
exit /b 1

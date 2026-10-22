@echo off
chcp 65001 >nul
cd /d "%~dp0"
py script.py
if errorlevel 1 (
  echo.
  echo O aplicativo fechou com erro. Tente executar INSTALAR.bat primeiro.
  pause
)

@echo off
cd /d "%~dp0"

rem Ejecuta la app sin ventana de consola.
rem pythonw / pyw = interprete de Python en modo "windowed" (sin consola).

where pythonw >nul 2>&1
if %errorlevel%==0 (
    start "" pythonw main.py
    exit /b
)

where pyw >nul 2>&1
if %errorlevel%==0 (
    start "" pyw main.py
    exit /b
)

echo No se encontro Python instalado. Instala Python 3 desde python.org.
pause

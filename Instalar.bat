@echo off
setlocal
cd /d "%~dp0"

echo ==================================================
echo    Instalador de dependencias - PDF a Excel EGEHID
echo ==================================================
echo.

rem --- Detectar Python (lanzador "py" o "python") ---
set "PY="
where py >nul 2>&1 && set "PY=py"
if not defined PY (
    where python >nul 2>&1 && set "PY=python"
)

if not defined PY (
    echo [ERROR] No se encontro Python instalado.
    echo.
    echo Descargalo desde: https://www.python.org/downloads/
    echo IMPORTANTE: marca la casilla "Add Python to PATH" al instalarlo.
    echo.
    pause
    exit /b 1
)

echo Python detectado:
%PY% --version
echo.

echo [1/2] Actualizando pip...
%PY% -m pip install --upgrade pip
echo.

echo [2/2] Instalando dependencias desde requirements.txt...
%PY% -m pip install -r requirements.txt || %PY% -m pip install --user -r requirements.txt
if errorlevel 1 goto :error

echo.
echo ==================================================
echo   [OK] Instalacion completada.
echo   Ya puedes abrir la aplicacion con  Ejecutar.bat
echo ==================================================
echo.
pause
exit /b 0

:error
echo.
echo [ERROR] No se pudieron instalar todas las dependencias.
echo Revisa el mensaje de error de arriba y tu conexion a internet.
echo.
pause
exit /b 1

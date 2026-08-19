@echo off
setlocal
cd /d "%~dp0"

echo ==================================================
echo    Ejecutando pruebas - PDF a Excel EGEHID
echo ==================================================
echo.

set "PY="
where py >nul 2>&1 && set "PY=py"
if not defined PY (
    where python >nul 2>&1 && set "PY=python"
)
if not defined PY (
    echo [ERROR] No se encontro Python. Ejecuta primero Instalar.bat
    echo.
    pause
    exit /b 1
)

%PY% run_tests.py
set "RES=%errorlevel%"

echo.
if "%RES%"=="0" (
    echo [OK] Todas las pruebas pasaron.
) else (
    echo [ATENCION] Hubo pruebas que fallaron. Revisa el detalle arriba.
)
echo.
pause
exit /b %RES%

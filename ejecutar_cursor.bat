@echo off
REM Script para ejecutar el bot desde Cursor usando el intérprete correcto de Python
echo ============================================================
echo EJECUTANDO BOT DESDE CURSOR
echo ============================================================
echo.

REM Verificar que Python esté disponible
python --version
if errorlevel 1 (
    echo ERROR: Python no encontrado
    pause
    exit /b 1
)

echo.
echo Verificando dependencias...
python verificar_entorno.py

echo.
echo ============================================================
echo Iniciando bot...
echo ============================================================
echo.

REM Ejecutar el bot
python main.py

pause











@echo off
REM Script para ejecutar el scraper periódicamente
REM Este script se ejecuta en bucle cada hora

echo ========================================
echo SCRAPER PERIODICO DE PLAYTOMIC
echo ========================================
echo Este script ejecutara el scraper cada hora
echo Presiona Ctrl+C para detener
echo.

REM Cambiar al directorio del script
cd /d "%~dp0"

:loop
echo.
echo [%date% %time%] Ejecutando scraper...
python scraper_playtomic.py 3

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: El scraper fallo con codigo %ERRORLEVEL%
)

echo.
echo Esperando 1 hora antes de la siguiente ejecucion...
echo (Presiona Ctrl+C para detener)
timeout /t 3600 /nobreak >nul

goto loop


@echo off
REM Script para ejecutar el scraper de Playtomic
REM Este script puede ser ejecutado manualmente o programado con Task Scheduler

echo ========================================
echo SCRAPER DE PLAYTOMIC
echo ========================================
echo.

REM Cambiar al directorio del script
cd /d "%~dp0"

REM Ejecutar el scraper (3 días: hoy + 2 días más)
echo Ejecutando scraper para 3 dias (hoy + 2 dias mas)...
python scraper_playtomic.py 3

echo.
echo ========================================
echo Scraping completado
echo ========================================
pause


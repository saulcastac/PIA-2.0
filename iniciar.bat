@echo off
echo ========================================
echo    PAD-IA - Sistema de Reservas
echo ========================================
echo.

REM Verificar si existe .env
if not exist .env (
    echo [ERROR] Archivo .env no encontrado!
    echo.
    echo Por favor crea un archivo .env con tus credenciales.
    echo Ver EJECUTAR.md para mas informacion.
    echo.
    pause
    exit /b 1
)

echo [OK] Iniciando sistema...
echo.
echo NOTA: Se abrira Chrome con WhatsApp Web.
echo       Escanea el codigo QR con tu WhatsApp.
echo.
echo.

python main.py

pause












# Script para iniciar ngrok automáticamente
# Este script busca ngrok en ubicaciones comunes y lo ejecuta

$ngrokPaths = @(
    "ngrok",  # Si está en PATH
    "$env:LOCALAPPDATA\ngrok\ngrok.exe",
    "$env:ProgramFiles\ngrok\ngrok.exe",
    "$env:ProgramFiles(x86)\ngrok\ngrok.exe",
    "C:\ngrok\ngrok.exe"
)

$ngrokExe = $null

foreach ($path in $ngrokPaths) {
    if (Test-Path $path) {
        $ngrokExe = $path
        break
    }
    # Intentar ejecutar directamente
    try {
        $result = Get-Command $path -ErrorAction SilentlyContinue
        if ($result) {
            $ngrokExe = $path
            break
        }
    } catch {
        continue
    }
}

if (-not $ngrokExe) {
    Write-Host "❌ ngrok no encontrado. Por favor instálalo primero:" -ForegroundColor Red
    Write-Host "   1. Ejecuta install_ngrok.ps1 como Administrador" -ForegroundColor Yellow
    Write-Host "   2. O descarga desde: https://ngrok.com/download" -ForegroundColor Yellow
    Write-Host "   3. O instala con: choco install ngrok (como Administrador)" -ForegroundColor Yellow
    exit 1
}

Write-Host "🚀 Iniciando ngrok en el puerto 5000..." -ForegroundColor Green
Write-Host "   URL del webhook: https://[url-ngrok]/webhook" -ForegroundColor Yellow
Write-Host "   Presiona Ctrl+C para detener ngrok" -ForegroundColor Yellow
Write-Host ""

# Ejecutar ngrok
& $ngrokExe http 5000


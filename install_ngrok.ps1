# Script para instalar ngrok en Windows
# Ejecutar como Administrador: PowerShell -ExecutionPolicy Bypass -File install_ngrok.ps1

Write-Host "Instalando ngrok..." -ForegroundColor Green

# Método 1: Intentar con Chocolatey
if (Get-Command choco -ErrorAction SilentlyContinue) {
    Write-Host "Instalando ngrok con Chocolatey..." -ForegroundColor Yellow
    choco install ngrok -y
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ ngrok instalado correctamente con Chocolatey" -ForegroundColor Green
        exit 0
    }
}

# Método 2: Descargar manualmente
Write-Host "Descargando ngrok manualmente..." -ForegroundColor Yellow

$ngrokUrl = "https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-windows-amd64.zip"
$downloadPath = "$env:TEMP\ngrok.zip"
$installPath = "$env:LOCALAPPDATA\ngrok"

try {
    # Crear directorio de instalación
    New-Item -ItemType Directory -Force -Path $installPath | Out-Null
    
    # Descargar ngrok
    Write-Host "Descargando desde $ngrokUrl..." -ForegroundColor Yellow
    Invoke-WebRequest -Uri $ngrokUrl -OutFile $downloadPath
    
    # Extraer
    Write-Host "Extrayendo archivos..." -ForegroundColor Yellow
    Expand-Archive -Path $downloadPath -DestinationPath $installPath -Force
    
    # Agregar al PATH del usuario
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($userPath -notlike "*$installPath*") {
        [Environment]::SetEnvironmentVariable("Path", "$userPath;$installPath", "User")
        Write-Host "✅ ngrok agregado al PATH del usuario" -ForegroundColor Green
    }
    
    # Limpiar
    Remove-Item $downloadPath -Force
    
    Write-Host "✅ ngrok instalado correctamente en: $installPath" -ForegroundColor Green
    Write-Host "Reinicia PowerShell para usar ngrok, o ejecuta: `$env:Path += ';$installPath'" -ForegroundColor Yellow
    
} catch {
    Write-Host "❌ Error instalando ngrok: $_" -ForegroundColor Red
    Write-Host "Por favor instala ngrok manualmente desde: https://ngrok.com/download" -ForegroundColor Yellow
    exit 1
}


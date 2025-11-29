# Configuración de Twilio para Desarrollo Local

## Opción 1: Instalar ngrok (Recomendado)

### Instalación Automática (Windows)

**Ejecutar como Administrador:**
```powershell
PowerShell -ExecutionPolicy Bypass -File install_ngrok.ps1
```

O ejecuta manualmente:
```powershell
.\install_ngrok.ps1
```

### Instalación Manual

1. **Descargar ngrok:**
   - Ve a https://ngrok.com/download
   - Descarga la versión para Windows
   - O usa Chocolatey (como Administrador): `choco install ngrok -y`
   - O usa Scoop: `scoop install ngrok`

2. **Instalación manual:**
   - Extrae el archivo `ngrok.exe` a una carpeta (ej: `C:\ngrok`)
   - Agrega esa carpeta al PATH del sistema, o
   - Ejecuta ngrok desde esa carpeta

3. **Autenticarse (opcional pero recomendado):**
   ```powershell
   ngrok config add-authtoken TU_TOKEN_DE_NGROK
   ```
   Obtén tu token en: https://dashboard.ngrok.com/get-started/your-authtoken

4. **Ejecutar ngrok:**
   ```powershell
   .\start_ngrok.ps1
   ```
   O manualmente:
   ```powershell
   ngrok http 5000
   ```

5. **Copiar la URL HTTPS:**
   - ngrok mostrará una URL como: `https://abc123.ngrok-free.app`
   - Usa esta URL en la configuración de Twilio: `https://abc123.ngrok-free.app/webhook`

## Opción 2: Usar localtunnel (Alternativa a ngrok)

Si no quieres instalar ngrok, puedes usar localtunnel:

1. **Instalar localtunnel globalmente:**
   ```powershell
   npm install -g localtunnel
   ```

2. **Exponer el puerto 5000:**
   ```powershell
   lt --port 5000
   ```

3. **Usar la URL proporcionada en Twilio**

## Opción 3: Usar serveo.net (Sin instalación)

1. **Usar SSH para exponer el puerto:**
   ```powershell
   ssh -R 80:localhost:5000 serveo.net
   ```

## Configuración en Twilio Console

1. Ve a: https://www.twilio.com/console/sms/whatsapp/sandbox
2. En "When a message comes in", ingresa tu URL de webhook:
   ```
   https://tu-url-ngrok.ngrok-free.app/webhook
   ```
3. Guarda la configuración

## Probar la Conexión

1. Inicia tu aplicación:
   ```powershell
   python main.py
   ```

2. Asegúrate de que ngrok esté corriendo en otra terminal:
   ```powershell
   ngrok http 5000
   ```

3. Envía un mensaje de WhatsApp al número de Twilio Sandbox

## Notas Importantes

- **ngrok gratuito**: La URL cambia cada vez que reinicias ngrok (a menos que tengas cuenta de pago)
- **Para producción**: Usa un servidor con IP pública o dominio propio
- **Seguridad**: Considera agregar autenticación al webhook en producción


# Cómo Ejecutar el Sistema PAD-IA

## ✅ Dependencias Instaladas

Todas las dependencias necesarias ya están instaladas:
- ✅ Selenium
- ✅ Playwright
- ✅ SQLAlchemy
- ✅ APScheduler
- ✅ Y todas las demás...

## 📝 Pasos para Ejecutar

### 1. Crear archivo .env

Crea un archivo llamado `.env` en la raíz del proyecto con este contenido:

```env
# Credenciales Playtomic (REQUERIDO - llenar con tus datos reales)
PLAYTOMIC_EMAIL=tu_email@ejemplo.com
PLAYTOMIC_PASSWORD=tu_password

# Configuración WhatsApp
WHATSAPP_SESSION_PATH=./whatsapp_session

# Configuración de recordatorios
REMINDER_24H_ENABLED=true
REMINDER_3H_ENABLED=true
NO_SHOW_TOLERANCE_MINUTES=10

# Sistema de strikes
MAX_STRIKES=2

# Base de datos
DATABASE_URL=sqlite:///./pad_ia.db

# Configuración general
TIMEZONE=America/Argentina/Buenos_Aires
```

**⚠️ IMPORTANTE**: Cambia `PLAYTOMIC_EMAIL` y `PLAYTOMIC_PASSWORD` con tus credenciales reales de Playtomic.

### 2. Ejecutar el Sistema

```bash
python main.py
```

### 3. Primera Ejecución

La primera vez que ejecutes:

1. **Se abrirá Chrome automáticamente** con WhatsApp Web
2. **Escanea el código QR** con tu WhatsApp
3. **Espera a que se conecte** (verás "✅ WhatsApp Web conectado" en la consola)
4. El sistema estará listo cuando veas "✅ Sistema iniciado correctamente"

### 4. Probar el Bot

1. Envía un mensaje de WhatsApp al bot: **"hola"**
2. Sigue el flujo de conversación
3. Prueba hacer una reserva

## 🔧 Solución de Problemas

### Error: "No se pudo conectar a WhatsApp Web"
- Verifica que Chrome esté instalado
- Asegúrate de escanear el QR correctamente
- Espera unos segundos después de escanear

### Error: "PLAYTOMIC_EMAIL no configurado"
- Verifica que el archivo `.env` existe
- Verifica que tiene tus credenciales reales de Playtomic

### Error: "Module not found"
- Ejecuta: `pip install -r requirements.txt`

### El bot no responde
- Verifica que WhatsApp Web esté conectado (verás el icono verde)
- Revisa los logs en la consola para errores
- Reinicia el sistema

## 📱 Comandos del Bot

- **"hola"** o **"inicio"** - Menú principal
- **"reservar"** - Iniciar proceso de reserva
- **"confirmo"** - Confirmar asistencia a recordatorio

## ⚠️ Notas Importantes

1. **Playtomic**: Los selectores CSS en `playtomic_automation.py` deben ajustarse según la estructura real de Playtomic
2. **WhatsApp**: Mantén la ventana de Chrome abierta mientras el bot funciona
3. **Base de datos**: Se crea automáticamente en `pad_ia.db` la primera vez

## 🛑 Detener el Sistema

Presiona `Ctrl + C` en la terminal para detener el sistema de forma segura.

## 📊 Próximos Pasos

1. ✅ Configurar `.env` con credenciales reales
2. ⏳ Ajustar selectores CSS de Playtomic (si es necesario)
3. ⏳ Probar con reservas reales
4. ⏳ Configurar número oficial de WhatsApp

---

**¡Listo para ejecutar!** 🚀












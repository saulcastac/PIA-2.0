# PAD-IA: Sistema de Reservas Automatizadas de Pádel

Sistema automatizado de reservas de canchas de pádel mediante WhatsApp, sin intervención humana.

## 🎯 Características Principales

- 🤖 **Bot de WhatsApp 24/7**: Atención automática e instantánea
- 🎾 **Automatización Playtomic**: Reservas automáticas usando Playwright
- ⏰ **Sistema Anti No-Show**: Recordatorios y confirmaciones
- 📊 **Control de Strikes**: Penalización por no-shows
- 📱 **Experiencia 100% WhatsApp**: Sin fricción ni descargas

## 🚀 Instalación

### Requisitos

- Python 3.8+
- Navegador Chromium (instalado por Playwright)
- Cuenta de Playtomic
- Cuenta de Twilio con WhatsApp API habilitada
- Servidor público accesible (para webhooks de Twilio)

### Pasos

1. **Clonar o descargar el proyecto**

2. **Instalar dependencias**:
```bash
pip install -r requirements.txt
```

3. **Instalar navegadores de Playwright**:
```bash
playwright install chromium
```

4. **Configurar variables de entorno**:
   - Crear archivo `.env` en la raíz del proyecto
   - Editar `.env` con tus credenciales:
   ```
   PLAYTOMIC_EMAIL=tu_email@ejemplo.com
   PLAYTOMIC_PASSWORD=tu_password
   TWILIO_ACCOUNT_SID=tu_account_sid
   TWILIO_AUTH_TOKEN=tu_auth_token
   TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
   ```
   
   **Configuración de Twilio:**
   1. Crear cuenta en [Twilio](https://www.twilio.com/)
   2. Obtener Account SID y Auth Token desde el dashboard
   3. Habilitar WhatsApp Sandbox o solicitar un número de WhatsApp aprobado
   4. Configurar el webhook URL en Twilio: `https://tu-servidor.com/webhook`

5. **Inicializar base de datos**:
   La base de datos se crea automáticamente al ejecutar la aplicación.

## 📖 Uso

### Iniciar el sistema

```bash
python main.py
```

El bot iniciará un servidor Flask en el puerto 5000 para recibir webhooks de Twilio.

**Importante**: Asegúrate de que tu servidor sea accesible públicamente. Puedes usar:
- ngrok: `ngrok http 5000` (para desarrollo)
- Un servidor en la nube con IP pública (para producción)

### Flujo de Reserva

1. El usuario escribe por WhatsApp: "hola" o "reservar"
2. El bot pregunta fecha y horario
3. El bot consulta disponibilidad en Playtomic
4. El usuario selecciona una opción
5. El sistema confirma la reserva automáticamente
6. Se envían recordatorios 24h y 3h antes
7. Control de asistencia el día del partido

## 🔧 Configuración

### Variables de Entorno (.env)

- `PLAYTOMIC_EMAIL`: Email de tu cuenta Playtomic
- `PLAYTOMIC_PASSWORD`: Contraseña de Playtomic
- `TWILIO_ACCOUNT_SID`: Account SID de Twilio
- `TWILIO_AUTH_TOKEN`: Auth Token de Twilio
- `TWILIO_WHATSAPP_NUMBER`: Número de WhatsApp de Twilio (formato: whatsapp:+14155238886)
- `REMINDER_24H_ENABLED`: Activar recordatorio 24h antes (true/false)
- `REMINDER_3H_ENABLED`: Activar recordatorio 3h antes (true/false)
- `NO_SHOW_TOLERANCE_MINUTES`: Tolerancia en minutos para marcar no-show
- `MAX_STRIKES`: Máximo de strikes antes de requerir prepago
- `TIMEZONE`: Zona horaria (ej: America/Argentina/Buenos_Aires)

## 📁 Estructura del Proyecto

```
PAD-IA/
├── main.py                 # Aplicación principal
├── whatsapp_bot_twilio.py  # Bot de WhatsApp con Twilio
├── whatsapp_bot.py         # Bot de WhatsApp (deprecado)
├── whatsapp_bot_selenium.py # Bot de WhatsApp con Selenium (deprecado)
├── playtomic_automation.py # Módulo Playwright para Playtomic
├── reminder_system.py      # Sistema de recordatorios y anti no-show
├── database.py             # Modelos de base de datos
├── config.py               # Configuración
├── requirements.txt        # Dependencias Python
└── README.md              # Este archivo
```

## 🛠️ Módulo Externo (Playtomic)

El módulo `playtomic_automation.py` utiliza Playwright para automatizar el navegador:

- Abre Playtomic como un usuario real
- Navega, selecciona cancha, fecha y hora
- Ejecuta la reserva de manera automática

**Nota**: Los selectores CSS en el código son ejemplos. Debes ajustarlos según la estructura real de Playtomic.

## 📊 Sistema Anti No-Show

- ✅ Confirmación obligatoria antes de bloquear cancha
- ⏰ Recordatorio 24 horas antes
- ⏰ Recordatorio 3 horas antes
- ⏱️ Tolerancia de 10 minutos el día del partido
- ⚠️ No-show = 1 strike
- 🚫 2 strikes → futuras reservas requieren prepago

## 🔍 Troubleshooting

### El bot no responde
- Verifica que el webhook de Twilio esté configurado correctamente
- Asegúrate de que tu servidor sea accesible públicamente
- Revisa los logs para errores
- Verifica las credenciales de Twilio en `.env`

### Playtomic no funciona
- Verifica credenciales en `.env`
- Ajusta los selectores CSS en `playtomic_automation.py` si Playtomic cambió su interfaz
- Ejecuta con `headless=False` para ver qué está pasando

### Recordatorios no se envían
- Verifica que el sistema de recordatorios esté corriendo
- Revisa la configuración de timezone

## 📈 Métricas Esperadas

- **Tiempo de respuesta**: < 1 minuto (vs 5-20 min manual)
- **No-shows**: < 10% (vs 20-40% antes)
- **Conversión**: 65-85% (vs 30-50% antes)

## 🚧 Próximos Pasos

- [x] Implementar integración con Twilio WhatsApp API
- [ ] Solicitar número de WhatsApp aprobado en Twilio (fuera del Sandbox)
- [ ] Activar módulo Playwright con credenciales reales
- [ ] Ajustar selectores CSS de Playtomic
- [ ] Pruebas internas con 5-10 reservas reales
- [ ] Implementar sistema de pagos
- [ ] Dashboard de administración

## 📝 Licencia

Este proyecto es privado y de uso interno.

## 👥 Soporte

Para problemas o preguntas, contacta al equipo de desarrollo.


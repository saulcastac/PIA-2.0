# Bot de WhatsApp para Reservas de Canchas de Padel 🤖🏸

Sistema completo y escalable de bot de WhatsApp que utiliza inteligencia artificial (ChatGPT) para gestionar reservas de canchas de padel, integrado con Google Calendar y Twilio.

## 📋 Características

- ✅ **Procesamiento de lenguaje natural** con ChatGPT para entender solicitudes de los usuarios
- ✅ **Detección automática** de cancha, fecha, hora y duración de reservas
- ✅ **Integración con Google Calendar** para gestionar reservas en calendarios separados por cancha
- ✅ **Consulta de disponibilidad** en tiempo real
- ✅ **Respuestas inteligentes** sobre horarios, canchas disponibles y reservas
- ✅ **Escalable y replicable** - fácil de configurar para múltiples establecimientos
- ✅ **Duración configurable** (por defecto 60 minutos)

## 🏗️ Arquitectura

```
src/
├── config/
│   └── config.js              # Configuración centralizada
├── services/
│   ├── twilioService.js       # Integración con Twilio WhatsApp
│   ├── openaiService.js       # Integración con OpenAI API
│   └── calendarService.js     # Integración con Google Calendar
├── controllers/
│   └── messageController.js   # Lógica de procesamiento de mensajes
├── routes/
│   └── webhook.js             # Endpoints de webhook
└── server.js                  # Servidor principal
```

## 🚀 Instalación y Configuración

### Prerrequisitos

- Node.js 18.0.0 o superior
- Cuenta de Twilio con WhatsApp habilitado
- Cuenta de OpenAI con API key
- Cuenta de Google con acceso a Google Calendar API
- Servidor con acceso a internet (para recibir webhooks de Twilio)

### Paso 1: Clonar e Instalar Dependencias

```bash
# Instalar dependencias
npm install
```

### Paso 2: Configurar Variables de Entorno

Copia el archivo `env.example` a `.env` y completa las variables:

```bash
cp env.example .env
```

Edita el archivo `.env` con tus credenciales:

```env
# Twilio Configuration
TWILIO_ACCOUNT_SID=tu_account_sid_de_twilio
TWILIO_AUTH_TOKEN=tu_auth_token_de_twilio
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
TWILIO_WEBHOOK_URL=https://tu-dominio.com/webhook

# OpenAI Configuration
OPENAI_API_KEY=tu_api_key_de_openai
OPENAI_MODEL=gpt-4

# Google Calendar Configuration
GOOGLE_CALENDAR_CLIENT_ID=tu_client_id_de_google
GOOGLE_CALENDAR_CLIENT_SECRET=tu_client_secret_de_google
GOOGLE_CALENDAR_REDIRECT_URI=http://localhost:3000/auth/callback
GOOGLE_CALENDAR_REFRESH_TOKEN=tu_refresh_token_de_google

# Server Configuration
PORT=3000
NODE_ENV=development

# Canchas Configuration
CANCHA_1_CALENDAR_ID=cancha1@group.calendar.google.com
CANCHA_2_CALENDAR_ID=cancha2@group.calendar.google.com
CANCHA_3_CALENDAR_ID=cancha3@group.calendar.google.com

# Establecimiento Configuration
ESTABLECIMIENTO_NOMBRE=Tu Centro de Padel
ESTABLECIMIENTO_HORARIO_APERTURA=08:00
ESTABLECIMIENTO_HORARIO_CIERRE=22:00
DURACION_DEFAULT_MINUTOS=60
```

### Paso 3: Configurar Twilio

1. **Crear cuenta en Twilio**: https://www.twilio.com/
2. **Habilitar WhatsApp Sandbox** (para pruebas) o **WhatsApp Business API** (para producción)
3. **Obtener credenciales**:
   - Account SID
   - Auth Token
   - Número de WhatsApp

4. **Configurar Webhook**:
   - En la consola de Twilio, ve a WhatsApp > Sandbox Settings (o tu configuración de WhatsApp)
   - Establece la URL del webhook: `https://tu-dominio.com/webhook`
   - Método: POST

### Paso 4: Configurar OpenAI

1. **Crear cuenta en OpenAI**: https://platform.openai.com/
2. **Generar API Key**: Ve a API Keys y crea una nueva
3. **Configurar modelo**: Puedes usar `gpt-4`, `gpt-4-turbo` o `gpt-3.5-turbo` (más económico)

### Paso 5: Configurar Google Calendar

#### 5.1. Crear Proyecto en Google Cloud

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un nuevo proyecto o selecciona uno existente
3. Habilita la **Google Calendar API**

#### 5.2. Crear Credenciales OAuth 2.0

1. Ve a **APIs & Services > Credentials**
2. Click en **Create Credentials > OAuth client ID**
3. Tipo de aplicación: **Web application**
4. Agrega URI de redirección: `http://localhost:3000/auth/callback`
5. Descarga las credenciales (Client ID y Client Secret)

#### 5.3. Crear Calendarios para cada Cancha

1. Ve a [Google Calendar](https://calendar.google.com/)
2. Crea un calendario separado para cada cancha
3. Obtén el ID de cada calendario:
   - Ve a configuración del calendario
   - Busca "Calendar ID" (formato: `xxxxx@group.calendar.google.com`)
   - Agrega estos IDs en el archivo `.env`

#### 5.4. Obtener Refresh Token

Para obtener el refresh token, necesitas autenticarte una vez. Puedes usar este script temporal:

```javascript
// scripts/getRefreshToken.js
import { google } from 'googleapis';
import readline from 'readline';

const oauth2Client = new google.auth.OAuth2(
  process.env.GOOGLE_CALENDAR_CLIENT_ID,
  process.env.GOOGLE_CALENDAR_CLIENT_SECRET,
  process.env.GOOGLE_CALENDAR_REDIRECT_URI
);

const scopes = ['https://www.googleapis.com/auth/calendar'];

const authUrl = oauth2Client.generateAuthUrl({
  access_type: 'offline',
  scope: scopes,
});

console.log('Autoriza esta aplicación visitando esta URL:', authUrl);

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
});

rl.question('Ingresa el código de autorización: ', (code) => {
  oauth2Client.getToken(code, (err, token) => {
    if (err) return console.error('Error obteniendo token:', err);
    console.log('Refresh Token:', token.refresh_token);
    rl.close();
  });
});
```

Ejecuta el script y sigue las instrucciones para obtener el refresh token.

### Paso 6: Configurar Canchas

En el archivo `.env`, agrega una línea por cada cancha:

```env
CANCHA_1_CALENDAR_ID=cancha1@group.calendar.google.com
CANCHA_2_CALENDAR_ID=cancha2@group.calendar.google.com
CANCHA_3_CALENDAR_ID=cancha3@group.calendar.google.com
# Agrega más según sea necesario
```

El sistema detectará automáticamente todas las canchas configuradas.

### Paso 7: Iniciar el Servidor

```bash
# Modo desarrollo (con auto-reload)
npm run dev

# Modo producción
npm start
```

El servidor estará disponible en `http://localhost:3000`

## 📱 Uso del Bot

### Ejemplos de Mensajes que el Bot Puede Procesar

**Reservar una cancha:**
- "Quiero reservar la cancha 1 mañana a las 3pm"
- "Reserva cancha 2 para el 15 de enero a las 14:00"
- "Necesito cancha 3 hoy a las 6 de la tarde por 90 minutos"

**Consultar disponibilidad:**
- "¿Qué canchas hay disponibles mañana a las 2pm?"
- "¿Hay horarios libres para la cancha 1 hoy?"
- "Muéstrame los horarios disponibles para mañana"

**Consultar información:**
- "¿Cuál es el horario del establecimiento?"
- "¿Cuántas canchas tienen?"
- "¿A qué hora cierran?"

### Flujo de Reserva

1. Usuario envía mensaje con intención de reservar
2. Bot procesa con IA para extraer: cancha, fecha, hora, duración
3. Si falta información, el bot la solicita
4. Bot verifica disponibilidad en Google Calendar
5. Si está disponible, crea la reserva
6. Bot confirma la reserva al usuario

## 🔧 Personalización

### Modificar Horarios del Establecimiento

Edita en `.env`:
```env
ESTABLECIMIENTO_HORARIO_APERTURA=08:00
ESTABLECIMIENTO_HORARIO_CIERRE=22:00
```

### Cambiar Duración por Defecto

```env
DURACION_DEFAULT_MINUTOS=60
```

### Agregar más Canchas

1. Crea un nuevo calendario en Google Calendar
2. Obtén el Calendar ID
3. Agrega en `.env`:
```env
CANCHA_4_CALENDAR_ID=nuevo_calendario@group.calendar.google.com
```

### Personalizar Respuestas de la IA

Edita el `systemPrompt` en `src/services/openaiService.js` para cambiar el comportamiento y tono del bot.

## 🌐 Despliegue en Producción

> 📖 **Guía Completa de Despliegue**: Consulta [DEPLOY.md](DEPLOY.md) para instrucciones detalladas paso a paso.

### Opciones de Hosting Recomendadas

- **Railway** ⭐ (Recomendado): Despliegue automático desde GitHub, muy fácil de usar
- **Render**: Tier gratuito disponible, ideal para empezar
- **Heroku**: Fácil despliegue con Git, clásico y confiable
- **DigitalOcean**: App Platform con buena relación precio/rendimiento
- **AWS/GCP/Azure**: Para proyectos más grandes con más control

### Configuración Rápida

1. **Preparación**:
   - Asegúrate de tener todas las credenciales configuradas
   - El código debe estar en un repositorio Git

2. **Variables de entorno**:
   - Configura todas las variables en tu plataforma de hosting
   - Usa `env.example` como referencia
   - Nunca subas el archivo `.env` a Git

3. **Actualizar configuraciones externas**:
   - **Google Calendar**: Agrega la URL de producción a los redirect URIs
   - **Twilio**: Actualiza el webhook a la URL de producción

4. **Verificar**:
   - Visita `/health` para verificar que el servidor funcione
   - Prueba enviando un mensaje de WhatsApp

Para instrucciones detalladas de cada plataforma, consulta [DEPLOY.md](DEPLOY.md)

## 🧪 Testing

Para probar localmente, puedes usar herramientas como:

- **ngrok**: Para exponer tu servidor local a internet
  ```bash
  ngrok http 3000
  ```
  Usa la URL de ngrok como `TWILIO_WEBHOOK_URL`

- **Twilio Sandbox**: Para pruebas sin costo

## 📊 Estructura de Datos

### Reserva en Google Calendar

Cada reserva se crea como un evento con:
- **Título**: "Reserva Padel - [Nombre Cliente]"
- **Descripción**: Incluye nombre y teléfono del cliente
- **Duración**: Configurable (default 60 min)
- **Recordatorios**: Email 1 día antes, Popup 1 hora antes

## 🔒 Seguridad

- ✅ Nunca subas `.env` a Git
- ✅ Usa HTTPS en producción
- ✅ Valida webhooks de Twilio (implementar validación de firma)
- ✅ Limita acceso a endpoints sensibles
- ✅ Rota credenciales regularmente

## 🐛 Solución de Problemas

### El bot no responde

1. Verifica que el servidor esté corriendo
2. Verifica que el webhook esté configurado correctamente en Twilio
3. Revisa los logs del servidor

### Error de autenticación con Google Calendar

1. Verifica que el refresh token sea válido
2. Regenera el refresh token si es necesario
3. Verifica que los scopes incluyan `calendar`

### La IA no entiende las solicitudes

1. Verifica que la API key de OpenAI sea válida
2. Revisa el modelo configurado (gpt-4 requiere créditos)
3. Ajusta el `systemPrompt` en `openaiService.js`

## 📈 Escalabilidad

Este sistema está diseñado para ser escalable:

- **Múltiples canchas**: Agrega más calendarios en `.env`
- **Múltiples establecimientos**: Duplica el proyecto y configura diferentes credenciales
- **Alta concurrencia**: Considera usar un queue system (Redis + Bull) para procesar mensajes
- **Base de datos**: Puedes agregar una BD para historial de reservas, clientes, etc.

## 💰 Costos Estimados

- **Twilio**: ~$0.005 por mensaje (WhatsApp)
- **OpenAI**: Depende del modelo (gpt-4 es más caro que gpt-3.5-turbo)
- **Google Calendar**: Gratis hasta cierto límite
- **Hosting**: Varía según proveedor ($5-20/mes típicamente)

## 📝 Licencia

MIT License - Libre para uso comercial y personal

## 🤝 Contribuciones

Este proyecto está diseñado para ser fácilmente replicable. Si mejoras algo, considera compartirlo.

## 📞 Soporte

Para problemas o preguntas:
1. Revisa la documentación
2. Verifica los logs del servidor
3. Consulta la documentación de las APIs (Twilio, OpenAI, Google Calendar)

## 🎯 Próximas Mejoras Sugeridas

- [ ] Base de datos para historial de reservas
- [ ] Sistema de confirmación de reservas
- [ ] Cancelación de reservas
- [ ] Notificaciones de recordatorio
- [ ] Dashboard web para administración
- [ ] Integración con sistema de pagos
- [ ] Multi-idioma
- [ ] Análisis y reportes

---

**Desarrollado para ser escalable, replicable y fácil de configurar** 🚀
>>>>>>> 30b90484fca9e4becc35080314b3cf9635e8a0c2


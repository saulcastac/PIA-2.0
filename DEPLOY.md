# Guía de Despliegue en la Nube

Esta guía te ayudará a desplegar el bot de WhatsApp para reservas de padel en diferentes plataformas de hosting en la nube.

## 📋 Requisitos Previos

Antes de desplegar, asegúrate de tener:

1. ✅ Todas las credenciales configuradas (Twilio, OpenAI, Google Calendar)
2. ✅ El código en un repositorio Git (GitHub, GitLab, etc.)
3. ✅ Una cuenta en la plataforma de hosting elegida

## 🔧 Variables de Entorno Requeridas

Necesitarás configurar las siguientes variables de entorno en tu plataforma de hosting:

### Twilio
- `TWILIO_ACCOUNT_SID` - Account SID de Twilio
- `TWILIO_AUTH_TOKEN` - Auth Token de Twilio
- `TWILIO_WHATSAPP_NUMBER` - Número de WhatsApp (formato: `whatsapp:+14155238886`)
- `TWILIO_WEBHOOK_URL` - URL del webhook (se actualizará después del despliegue)

### OpenAI
- `OPENAI_API_KEY` - API Key de OpenAI
- `OPENAI_MODEL` - Modelo a usar (opcional, default: `gpt-4`)

### Google Calendar
- `GOOGLE_CALENDAR_CLIENT_ID` - Client ID de OAuth 2.0
- `GOOGLE_CALENDAR_CLIENT_SECRET` - Client Secret de OAuth 2.0
- `GOOGLE_CALENDAR_REDIRECT_URI` - Redirect URI (debe ser la URL de producción + `/auth/callback`)
- `GOOGLE_CALENDAR_REFRESH_TOKEN` - Refresh Token de Google

### Servidor
- `PORT` - Puerto del servidor (generalmente se configura automáticamente)
- `NODE_ENV` - Entorno (debe ser `production`)

### Establecimiento
- `ESTABLECIMIENTO_NOMBRE` - Nombre del establecimiento
- `ESTABLECIMIENTO_HORARIO_APERTURA` - Horario de apertura (formato: `HH:MM`)
- `ESTABLECIMIENTO_HORARIO_CIERRE` - Horario de cierre (formato: `HH:MM`)
- `DURACION_DEFAULT_MINUTOS` - Duración por defecto de las reservas (opcional, default: `60`)

### Canchas
- `CANCHA_1_CALENDAR_ID` - Calendar ID de la cancha 1
- `CANCHA_2_CALENDAR_ID` - Calendar ID de la cancha 2 (opcional)
- `CANCHA_3_CALENDAR_ID` - Calendar ID de la cancha 3 (opcional)
- ... (puedes agregar más canchas)

---

## 🚂 Despliegue en Railway

Railway es la opción más fácil y recomendada para este proyecto.

### Paso 1: Crear Proyecto en Railway

1. Ve a https://railway.app/
2. Inicia sesión con GitHub
3. Click en **"New Project"**
4. Selecciona **"Deploy from GitHub repo"**
5. Conecta tu repositorio y selecciona el proyecto

### Paso 2: Configurar Variables de Entorno

1. En tu proyecto de Railway, ve a la pestaña **"Variables"**
2. Agrega todas las variables de entorno listadas arriba
3. **IMPORTANTE**: Deja `TWILIO_WEBHOOK_URL` vacío por ahora (lo actualizarás después)

### Paso 3: Obtener URL Pública

1. Railway asignará automáticamente una URL (ej: `https://tu-proyecto.up.railway.app`)
2. Copia esta URL

### Paso 4: Actualizar Configuraciones

1. **Actualizar `GOOGLE_CALENDAR_REDIRECT_URI`**:
   - En Railway, actualiza la variable: `https://tu-proyecto.up.railway.app/auth/callback`
   - En Google Cloud Console, agrega esta URL a los "Authorized redirect URIs" de tu OAuth client

2. **Actualizar `TWILIO_WEBHOOK_URL`**:
   - En Railway, actualiza la variable: `https://tu-proyecto.up.railway.app/webhook`
   - En Twilio Console, ve a **Messaging > Settings > WhatsApp Sandbox Settings**
   - Actualiza el webhook a: `https://tu-proyecto.up.railway.app/webhook`

### Paso 5: Verificar Despliegue

1. Railway desplegará automáticamente
2. Ve a `https://tu-proyecto.up.railway.app/health` para verificar que esté funcionando
3. Revisa los logs en Railway para asegurarte de que no hay errores

### Costos

- **Plan Hobby**: $5/mes (incluye $5 de crédito)
- **Plan Pro**: $20/mes (más recursos)

---

## 🎨 Despliegue en Render

Render ofrece un tier gratuito con algunas limitaciones.

### Paso 1: Crear Servicio en Render

1. Ve a https://render.com/
2. Inicia sesión con GitHub
3. Click en **"New +"** > **"Web Service"**
4. Conecta tu repositorio
5. Configura:
   - **Name**: `padel-booking-bot`
   - **Environment**: `Node`
   - **Build Command**: `npm install`
   - **Start Command**: `node src/server.js`

### Paso 2: Configurar Variables de Entorno

1. En la sección **"Environment Variables"**, agrega todas las variables
2. Asegúrate de configurar `NODE_ENV=production`

### Paso 3: Obtener URL y Actualizar Configuraciones

Sigue los mismos pasos que en Railway (Paso 3 y 4).

### Paso 4: Desplegar

1. Click en **"Create Web Service"**
2. Render comenzará el despliegue automáticamente

### Costos

- **Free Tier**: Gratis (pero el servicio se "duerme" después de 15 minutos de inactividad)
- **Starter Plan**: $7/mes (sin sleep, mejor rendimiento)

---

## 🟣 Despliegue en Heroku

### Paso 1: Instalar Heroku CLI

```bash
# Windows (con Chocolatey)
choco install heroku-cli

# O descarga desde: https://devcenter.heroku.com/articles/heroku-cli
```

### Paso 2: Crear Aplicación

```bash
# Iniciar sesión
heroku login

# Crear aplicación
heroku create tu-nombre-app

# O crea desde el dashboard: https://dashboard.heroku.com/new-app
```

### Paso 3: Configurar Variables de Entorno

```bash
# Configurar todas las variables
heroku config:set TWILIO_ACCOUNT_SID=tu_account_sid
heroku config:set TWILIO_AUTH_TOKEN=tu_auth_token
# ... (repite para todas las variables)

# O configura desde el dashboard en Settings > Config Vars
```

### Paso 4: Desplegar

```bash
# Si es la primera vez
git push heroku main

# Para despliegues futuros
git push heroku main
```

### Paso 5: Obtener URL y Actualizar Configuraciones

1. Tu URL será: `https://tu-nombre-app.herokuapp.com`
2. Sigue los pasos 3 y 4 de Railway para actualizar Google Calendar y Twilio

### Costos

- **Eco Dyno**: $5/mes (se duerme después de 30 min de inactividad)
- **Basic Dyno**: $7/mes (sin sleep)

---

## 🐳 Despliegue en DigitalOcean App Platform

### Paso 1: Crear App

1. Ve a https://cloud.digitalocean.com/apps
2. Click en **"Create App"**
3. Conecta tu repositorio de GitHub
4. DigitalOcean detectará automáticamente Node.js

### Paso 2: Configurar

1. **Build Command**: `npm install`
2. **Run Command**: `node src/server.js`
3. Selecciona el plan (Starter desde $5/mes)

### Paso 3: Variables de Entorno

1. En la sección **"Environment Variables"**, agrega todas las variables
2. Configura `NODE_ENV=production`

### Paso 4: Desplegar

1. Click en **"Create Resources"**
2. DigitalOcean desplegará automáticamente
3. Obtén la URL y actualiza Google Calendar y Twilio

### Costos

- **Starter**: $5/mes
- **Basic**: $12/mes

---

## 🔄 Actualizar Google Calendar OAuth

Después de obtener la URL de producción, debes actualizar el OAuth client:

1. Ve a https://console.cloud.google.com/
2. Selecciona tu proyecto
3. Ve a **APIs & Services > Credentials**
4. Click en tu OAuth 2.0 Client ID
5. En **"Authorized redirect URIs"**, agrega:
   - `https://tu-dominio.com/auth/callback`
6. Guarda los cambios

**Nota**: Si ya obtuviste el refresh token con `localhost`, no necesitas regenerarlo. El refresh token funciona con cualquier redirect URI autorizado.

---

## 🔔 Actualizar Webhook de Twilio

1. Ve a https://console.twilio.com/
2. Ve a **Messaging > Settings > WhatsApp Sandbox Settings** (o tu configuración de WhatsApp)
3. En **"When a message comes in"**, actualiza la URL a:
   - `https://tu-dominio.com/webhook`
4. Método: `POST`
5. Guarda los cambios

---

## ✅ Verificación Post-Despliegue

### 1. Verificar Salud del Servidor

```bash
curl https://tu-dominio.com/health
```

Deberías recibir:
```json
{
  "status": "ok",
  "timestamp": "2024-01-01T00:00:00.000Z",
  "service": "Padel Booking Bot",
  "version": "2.0.0"
}
```

### 2. Verificar Webhook de Twilio

1. Envía un mensaje de prueba a tu número de WhatsApp
2. El bot debería responder
3. Revisa los logs en tu plataforma de hosting para verificar que los mensajes lleguen

### 3. Verificar Google Calendar

1. Intenta hacer una reserva a través del bot
2. Verifica que el evento se cree en Google Calendar

---

## 🔍 Monitoreo y Logs

### Ver Logs en Tiempo Real

- **Railway**: Pestaña "Deployments" > Click en el deployment > "View Logs"
- **Render**: Pestaña "Logs"
- **Heroku**: `heroku logs --tail`
- **DigitalOcean**: Pestaña "Runtime Logs"

### Servicios de Monitoreo Recomendados

- **Uptime Robot** (gratis): Monitorea que el servidor esté en línea
- **Sentry** (tier gratuito): Captura y reporta errores
- **Logtail** (tier gratuito): Agregación y búsqueda de logs

---

## 🐛 Troubleshooting

### El servidor no inicia

1. Verifica que todas las variables de entorno estén configuradas
2. Revisa los logs para ver errores específicos
3. Asegúrate de que `NODE_ENV=production` esté configurado

### El bot no responde

1. Verifica que el webhook de Twilio esté configurado correctamente
2. Verifica que la URL del webhook sea accesible públicamente
3. Revisa los logs para ver si los mensajes están llegando

### Error "Invalid refresh token"

1. Regenera el refresh token usando el script `scripts/getRefreshToken.js`
2. Asegúrate de usar la URL de producción en el redirect URI
3. Actualiza la variable `GOOGLE_CALENDAR_REFRESH_TOKEN` en tu plataforma

### El servicio se "duerme" (solo en tiers gratuitos)

- **Render Free**: Se duerme después de 15 min de inactividad
- **Heroku Eco**: Se duerme después de 30 min de inactividad

Solución: Usa un servicio de monitoreo como Uptime Robot para hacer ping periódico al endpoint `/health`

---

## 🔒 Seguridad

- ✅ Nunca subas el archivo `.env` a Git
- ✅ Usa HTTPS (todas las plataformas lo proporcionan automáticamente)
- ✅ Mantén tus credenciales seguras
- ✅ Considera rotar las API keys periódicamente
- ✅ Usa variables de entorno del hosting, no archivos `.env` en producción

---

## 📞 Soporte

Si tienes problemas:

1. Revisa los logs de tu plataforma de hosting
2. Verifica la documentación de la plataforma elegida
3. Revisa la sección de Troubleshooting en `SETUP_DETALLADO.md`

---

¡Listo! Tu bot debería estar funcionando en la nube. 🎉


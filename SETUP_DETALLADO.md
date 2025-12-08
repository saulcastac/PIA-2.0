# Guía Detallada de Configuración

Esta guía te llevará paso a paso para configurar completamente el bot de WhatsApp para reservas de padel.

## 📋 Índice

1. [Configuración de Twilio](#1-configuración-de-twilio)
2. [Configuración de OpenAI](#2-configuración-de-openai)
3. [Configuración de Google Calendar](#3-configuración-de-google-calendar)
4. [Configuración del Servidor](#4-configuración-del-servidor)
5. [Pruebas Locales](#5-pruebas-locales)
6. [Despliegue en Producción](#6-despliegue-en-producción)

---

## 1. Configuración de Twilio

### 1.1. Crear Cuenta en Twilio

1. Ve a https://www.twilio.com/
2. Crea una cuenta gratuita (incluye $15 de crédito)
3. Verifica tu número de teléfono

### 1.2. Configurar WhatsApp Sandbox (Para Pruebas)

1. En el dashboard de Twilio, ve a **Messaging > Try it out > Send a WhatsApp message**
2. Sigue las instrucciones para unirte al Sandbox:
   - Envía el código que te proporciona Twilio a su número de WhatsApp
3. Una vez unido, podrás recibir y enviar mensajes

### 1.3. Obtener Credenciales

1. En el dashboard, ve a **Account > Account Info**
2. Copia:
   - **Account SID**
   - **Auth Token**
3. En **Phone Numbers > Manage > Active numbers**, encuentra tu número de WhatsApp
   - Formato: `whatsapp:+14155238886`

### 1.4. Configurar Webhook

1. Ve a **Messaging > Settings > WhatsApp Sandbox Settings** (o tu configuración de WhatsApp)
2. En **When a message comes in**, ingresa:
   - URL: `https://tu-dominio.com/webhook` (o tu URL de ngrok para pruebas)
   - Método: `POST`
3. Guarda los cambios

### 1.5. Actualizar a WhatsApp Business API (Producción)

Para producción, necesitarás:
- Número de WhatsApp Business verificado
- Aprobación de Twilio para WhatsApp Business API
- Costo: ~$0.005 por mensaje

---

## 2. Configuración de OpenAI

### 2.1. Crear Cuenta

1. Ve a https://platform.openai.com/
2. Crea una cuenta
3. Agrega método de pago (requerido para usar la API)

### 2.2. Generar API Key

1. Ve a **API Keys** en el menú lateral
2. Click en **Create new secret key**
3. Copia la clave (solo se muestra una vez)
4. Guárdala de forma segura

### 2.3. Elegir Modelo

- **gpt-4**: Más inteligente, más caro (~$0.03 por 1K tokens)
- **gpt-4-turbo**: Balance entre precio y rendimiento
- **gpt-3.5-turbo**: Más económico (~$0.002 por 1K tokens), suficiente para la mayoría de casos

Recomendación: Empieza con `gpt-3.5-turbo` y actualiza a `gpt-4` si necesitas mejor comprensión.

---

## 3. Configuración de Google Calendar

### 3.1. Crear Proyecto en Google Cloud

1. Ve a https://console.cloud.google.com/
2. Click en el selector de proyectos (arriba)
3. Click en **New Project**
4. Nombre: "Padel Booking Bot" (o el que prefieras)
5. Click en **Create**

### 3.2. Habilitar Google Calendar API

1. En el proyecto recién creado, ve a **APIs & Services > Library**
2. Busca "Google Calendar API"
3. Click en **Enable**

### 3.3. Crear Credenciales OAuth 2.0

1. Ve a **APIs & Services > Credentials**
2. Click en **+ CREATE CREDENTIALS > OAuth client ID**
3. Si es la primera vez, configura la pantalla de consentimiento:
   - Tipo de usuario: **External**
   - Nombre de la app: "Padel Booking Bot"
   - Email de soporte: Tu email
   - Click en **Save and Continue** en cada paso
4. Para crear el OAuth client:
   - Tipo de aplicación: **Web application**
   - Nombre: "Padel Booking Bot Web Client"
   - **Authorized redirect URIs**: 
     - `http://localhost:3000/auth/callback` (para desarrollo)
     - `https://tu-dominio.com/auth/callback` (para producción)
   - Click en **Create**
5. **IMPORTANTE**: Copia el **Client ID** y **Client Secret** (descarga el JSON si prefieres)

### 3.4. Crear Calendarios para Canchas

1. Ve a https://calendar.google.com/
2. En el panel izquierdo, click en el **+** junto a "Other calendars"
3. Click en **Create new calendar**
4. Nombre: "Cancha 1" (o el nombre que prefieras)
5. Click en **Create calendar**
6. Repite para cada cancha que tengas

### 3.5. Obtener Calendar IDs

1. En Google Calendar, ve a **Settings** (⚙️)
2. En el panel izquierdo, click en el calendario que quieres usar
3. Busca la sección **Integrate calendar**
4. Copia el **Calendar ID** (formato: `xxxxx@group.calendar.google.com`)
5. Repite para cada cancha

### 3.6. Obtener Refresh Token

#### Opción A: Usando el Script Incluido

1. Asegúrate de tener las variables en tu `.env`:
   ```env
   GOOGLE_CALENDAR_CLIENT_ID=tu_client_id
   GOOGLE_CALENDAR_CLIENT_SECRET=tu_client_secret
   GOOGLE_CALENDAR_REDIRECT_URI=http://localhost:3000/auth/callback
   ```

2. Ejecuta el script:
   ```bash
   node scripts/getRefreshToken.js
   ```

3. Sigue las instrucciones en pantalla:
   - Abre la URL que se muestra
   - Autoriza la aplicación
   - Copia el código de autorización
   - Pégalo en la terminal

4. Copia el **Refresh Token** que se muestra y agrégalo a tu `.env`

#### Opción B: Manualmente

1. Construye esta URL (reemplaza `YOUR_CLIENT_ID`):
   ```
   https://accounts.google.com/o/oauth2/v2/auth?client_id=YOUR_CLIENT_ID&redirect_uri=http://localhost:3000/auth/callback&response_type=code&scope=https://www.googleapis.com/auth/calendar&access_type=offline&prompt=consent
   ```

2. Abre la URL en tu navegador
3. Autoriza la aplicación
4. Serás redirigido a una URL como:
   ```
   http://localhost:3000/auth/callback?code=4/0AeanS...
   ```
5. Copia el valor del parámetro `code`
6. Usa este comando (reemplaza los valores):
   ```bash
   curl -X POST https://oauth2.googleapis.com/token \
     -d "client_id=YOUR_CLIENT_ID" \
     -d "client_secret=YOUR_CLIENT_SECRET" \
     -d "code=CODE_FROM_URL" \
     -d "grant_type=authorization_code" \
     -d "redirect_uri=http://localhost:3000/auth/callback"
   ```
7. En la respuesta, copia el `refresh_token`

### 3.7. Compartir Calendarios (Opcional)

Si quieres que otros usuarios vean las reservas:

1. En configuración del calendario, ve a **Share with specific people**
2. Agrega los emails que quieres que tengan acceso
3. Selecciona el nivel de permiso (Viewer es suficiente)

---

## 4. Configuración del Servidor

### 4.1. Instalar Dependencias

```bash
npm install
```

### 4.2. Configurar Variables de Entorno

1. Copia `env.example` a `.env`:
   ```bash
   cp env.example .env
   ```

2. Edita `.env` con todos los valores obtenidos en los pasos anteriores

### 4.3. Verificar Configuración

El servidor validará automáticamente la configuración al iniciar. Si falta algo, verás un error claro.

### 4.4. Iniciar Servidor

```bash
# Desarrollo
npm run dev

# Producción
npm start
```

Deberías ver:
```
✅ Configuración validada correctamente
✅ Google Calendar inicializado
🚀 Servidor iniciado en puerto 3000
📱 Webhook URL: http://localhost:3000/webhook
```

---

## 5. Pruebas Locales

### 5.1. Usar ngrok para Exponer el Servidor

1. Descarga ngrok: https://ngrok.com/download
2. Inicia ngrok:
   ```bash
   ngrok http 3000
   ```
3. Copia la URL HTTPS que ngrok proporciona (ej: `https://abc123.ngrok.io`)
4. Actualiza el webhook en Twilio con: `https://abc123.ngrok.io/webhook`
5. Actualiza `TWILIO_WEBHOOK_URL` en tu `.env` (opcional, solo para referencia)

### 5.2. Probar el Bot

1. Envía un mensaje de WhatsApp al número de Twilio
2. El bot debería responder
3. Prueba diferentes tipos de mensajes:
   - "Quiero reservar cancha 1 mañana a las 3pm"
   - "¿Qué horarios hay disponibles?"
   - "¿Cuál es el horario del establecimiento?"

### 5.3. Verificar Reservas en Google Calendar

1. Ve a Google Calendar
2. Verifica que las reservas se creen en el calendario correcto
3. Verifica que la información sea correcta

---

## 6. Despliegue en Producción

> 📖 **Guía Completa**: Para instrucciones detalladas paso a paso, consulta el archivo [DEPLOY.md](DEPLOY.md)

### 6.1. Preparación para Despliegue

Antes de desplegar, asegúrate de:

1. ✅ Tener todas las credenciales configuradas localmente
2. ✅ El código está en un repositorio Git (GitHub, GitLab, etc.)
3. ✅ Has probado el bot localmente con ngrok

### 6.2. Elegir Plataforma de Hosting

**Recomendaciones:**

- **Railway** (⭐ Más fácil y recomendado): https://railway.app/
  - Conecta GitHub, despliega automáticamente
  - Variables de entorno fáciles de configurar
  - HTTPS incluido
  - Plan desde $5/mes

- **Render** (Gratis con limitaciones): https://render.com/
  - Tier gratuito disponible
  - Se duerme después de 15 min de inactividad
  - Plan de pago desde $7/mes

- **Heroku**: https://www.heroku.com/
  - Clásico y confiable
  - Plan Eco desde $5/mes (se duerme después de 30 min)
  - Plan Basic desde $7/mes

- **DigitalOcean App Platform**: https://www.digitalocean.com/products/app-platform
  - Buena relación precio/rendimiento
  - Plan Starter desde $5/mes
  - Fácil de usar

- **AWS/GCP/Azure**: Para proyectos más grandes y con más control

### 6.3. Pasos Generales de Despliegue

1. **Crear proyecto en la plataforma elegida**
   - Conecta tu repositorio de GitHub
   - La plataforma detectará automáticamente Node.js

2. **Configurar Variables de Entorno**
   - Agrega TODAS las variables de tu `.env` local
   - **IMPORTANTE**: Actualiza `GOOGLE_CALENDAR_REDIRECT_URI` a la URL de producción
   - **IMPORTANTE**: Deja `TWILIO_WEBHOOK_URL` vacío inicialmente

3. **Obtener URL Pública**
   - La plataforma asignará una URL (ej: `https://tu-app.railway.app`)
   - Copia esta URL

4. **Actualizar Configuraciones Externas**
   
   **a) Google Calendar OAuth:**
   - Ve a Google Cloud Console > Credentials
   - Agrega a "Authorized redirect URIs": `https://tu-dominio.com/auth/callback`
   
   **b) Twilio Webhook:**
   - Actualiza `TWILIO_WEBHOOK_URL` en las variables de entorno: `https://tu-dominio.com/webhook`
   - En Twilio Console, actualiza el webhook a la misma URL

5. **Verificar Despliegue**
   - Visita `https://tu-dominio.com/health` para verificar que funcione
   - Revisa los logs en tu plataforma
   - Prueba enviando un mensaje de WhatsApp

### 6.4. Variables de Entorno Requeridas

Todas estas variables deben configurarse en tu plataforma de hosting:

**Twilio:**
- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_WHATSAPP_NUMBER`
- `TWILIO_WEBHOOK_URL` (actualizar después de obtener URL)

**OpenAI:**
- `OPENAI_API_KEY`
- `OPENAI_MODEL` (opcional, default: `gpt-4`)

**Google Calendar:**
- `GOOGLE_CALENDAR_CLIENT_ID`
- `GOOGLE_CALENDAR_CLIENT_SECRET`
- `GOOGLE_CALENDAR_REDIRECT_URI` (debe ser URL de producción)
- `GOOGLE_CALENDAR_REFRESH_TOKEN`

**Servidor:**
- `PORT` (generalmente se configura automáticamente)
- `NODE_ENV=production`

**Establecimiento:**
- `ESTABLECIMIENTO_NOMBRE`
- `ESTABLECIMIENTO_HORARIO_APERTURA`
- `ESTABLECIMIENTO_HORARIO_CIERRE`
- `DURACION_DEFAULT_MINUTOS` (opcional)

**Canchas:**
- `CANCHA_1_CALENDAR_ID`
- `CANCHA_2_CALENDAR_ID` (opcional)
- `CANCHA_3_CALENDAR_ID` (opcional)
- ... (más canchas según necesites)

### 6.5. Archivos de Configuración Incluidos

El proyecto incluye archivos de configuración para facilitar el despliegue:

- **`Procfile`**: Para Heroku y Railway
- **`railway.json`**: Configuración específica para Railway
- **`render.yaml`**: Configuración para Render.com
- **`.dockerignore`**: Para optimizar builds

### 6.6. Monitoreo Post-Despliegue

- **Logs**: Revisa los logs en tu plataforma de hosting regularmente
- **Salud del Servidor**: Usa el endpoint `/health` para verificar estado
- **Servicios Recomendados**:
  - **Uptime Robot** (gratis): Monitorea que el servidor esté en línea
  - **Sentry** (tier gratuito): Captura y reporta errores
  - **Logtail** (tier gratuito): Agregación y búsqueda de logs

### 6.7. Troubleshooting de Despliegue

**El servidor no inicia:**
- Verifica que todas las variables de entorno estén configuradas
- Revisa los logs para ver errores específicos
- Asegúrate de que `NODE_ENV=production` esté configurado

**El bot no responde:**
- Verifica que el webhook de Twilio esté configurado correctamente
- Verifica que la URL sea accesible públicamente
- Revisa los logs para ver si los mensajes están llegando

**El servicio se "duerme" (tiers gratuitos):**
- Render Free: Se duerme después de 15 min de inactividad
- Heroku Eco: Se duerme después de 30 min de inactividad
- Solución: Usa Uptime Robot para hacer ping periódico a `/health`

Para más detalles, consulta [DEPLOY.md](DEPLOY.md)

---

## 🔧 Troubleshooting Común

### El bot no responde

1. ✅ Verifica que el servidor esté corriendo
2. ✅ Verifica que el webhook esté configurado en Twilio
3. ✅ Revisa los logs del servidor
4. ✅ Verifica que el número de WhatsApp esté correcto

### Error "Invalid refresh token"

1. Regenera el refresh token usando el script
2. Asegúrate de usar `prompt=consent` para obtener un nuevo refresh token

### La IA no entiende bien

1. Verifica que la API key de OpenAI sea válida
2. Verifica que tengas créditos en OpenAI
3. Considera cambiar a `gpt-4` si `gpt-3.5-turbo` no es suficiente
4. Ajusta el `systemPrompt` en `src/services/openaiService.js`

### Las reservas no se crean en Calendar

1. Verifica que los Calendar IDs sean correctos
2. Verifica que el refresh token sea válido
3. Verifica que la API de Calendar esté habilitada
4. Revisa los logs para ver errores específicos

---

## 📞 Soporte Adicional

Si tienes problemas:

1. Revisa los logs del servidor
2. Verifica la documentación de cada servicio:
   - Twilio: https://www.twilio.com/docs/whatsapp
   - OpenAI: https://platform.openai.com/docs
   - Google Calendar: https://developers.google.com/calendar

---

¡Listo! Tu bot debería estar funcionando. 🎉


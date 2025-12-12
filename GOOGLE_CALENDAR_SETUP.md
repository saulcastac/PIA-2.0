# Configuración de Google Calendar

Este documento explica cómo configurar la integración con Google Calendar para el sistema de reservas.

## Requisitos Previos

1. Una cuenta de Google
2. Acceso a Google Cloud Console
3. Python 3.8 o superior

## Pasos de Configuración

### 1. Crear Proyecto en Google Cloud Console

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un nuevo proyecto o selecciona uno existente
3. Habilita la API de Google Calendar:
   - Ve a "APIs & Services" > "Library"
   - Busca "Google Calendar API"
   - Haz clic en "Enable"

### 2. Crear Credenciales OAuth 2.0

1. Ve a "APIs & Services" > "Credentials"
2. Haz clic en "Create Credentials" > "OAuth client ID"
3. Si es la primera vez, configura la pantalla de consentimiento OAuth:
   - Ve a "APIs & Services" > "OAuth consent screen"
   - Tipo de usuario: **"Internal"** (si tienes Google Workspace) o **"External"** (si es cuenta personal)
   - Nombre de la app: "PAD-IA_APP" o "Padel Reservation Bot"
   - Email de soporte: tu email
   - Dominios autorizados: déjalo vacío (no necesario para Desktop app)
   - Ámbitos: Agrega `https://www.googleapis.com/auth/calendar`
   - Usuarios de prueba: **IMPORTANTE** - Agrega tu email aquí (ver paso 4)
   - Guarda y continúa
4. **Configurar Usuarios de Prueba (CRÍTICO para evitar error 403):**
   - En "OAuth consent screen" > "Test users"
   - Haz clic en "+ ADD USERS"
   - Agrega tu email de Google (el que usarás para autenticarte)
   - Guarda
5. Vuelve a "Credentials" > "Create Credentials" > "OAuth client ID"
6. Selecciona "Desktop app" como tipo de aplicación
7. Nombre: "Padel Reservation Bot" (o el que prefieras)
8. Descarga el archivo JSON de credenciales
9. Renombra el archivo a `credentials.json` y colócalo en la raíz del proyecto

### 3. Configurar Variables de Entorno

Agrega las siguientes variables a tu archivo `.env`:

```env
# Google Calendar
GOOGLE_CREDENTIALS_FILE=credentials.json
GOOGLE_TOKEN_FILE=token.pickle
GOOGLE_CALENDAR_ID=primary
TIMEZONE=America/Mexico_City
```

**Nota sobre TIMEZONE:**
- Ajusta la zona horaria según tu ubicación
- Ejemplos: `America/Mexico_City`, `America/Argentina/Buenos_Aires`, `America/New_York`

### 4. Primera Autenticación

La primera vez que ejecutes el bot, se abrirá una ventana del navegador para autenticarte:

1. Inicia el bot
2. Se abrirá una ventana del navegador
3. Selecciona la cuenta de Google que quieres usar
4. Autoriza el acceso al calendario
5. El token se guardará en `token.pickle` para futuras ejecuciones

### 5. Usar Calendario Específico (Opcional)

Por defecto, el bot usa el calendario principal (`primary`). Para usar un calendario específico:

1. Ve a [Google Calendar](https://calendar.google.com/)
2. Crea un nuevo calendario o selecciona uno existente
3. Ve a "Configuración" > "Configuración de calendarios"
4. Encuentra el ID del calendario (está en la URL o en la configuración)
5. Actualiza `GOOGLE_CALENDAR_ID` en el `.env` con el ID del calendario

## Estructura de Archivos

Después de la configuración, deberías tener:

```
PAD-IA/
├── credentials.json          # Credenciales OAuth (NO subir a Git)
├── token.pickle              # Token de acceso (NO subir a Git)
├── .env                      # Variables de entorno
└── ...
```

## Verificación

Para verificar que la configuración funciona:

```python
from google_calendar_client import GoogleCalendarClient

client = GoogleCalendarClient()
if client.authenticate():
    print("✅ Autenticación exitosa")
    calendars = client.list_calendars()
    print(f"Calendarios disponibles: {len(calendarios)}")
else:
    print("❌ Error en autenticación")
```

## Solución de Problemas

### Error 403: "access_denied" - "App no completó el proceso de verificación"

**Este es el error más común cuando acabas de crear la app.**

**Solución:**
1. Ve a Google Cloud Console > "APIs & Services" > "OAuth consent screen"
2. En la sección "Test users", haz clic en "+ ADD USERS"
3. Agrega tu email de Google (el mismo que usarás para autenticarte)
4. Guarda los cambios
5. Espera 1-2 minutos para que los cambios se propaguen
6. Intenta autenticarte nuevamente

**Nota:** Si tu app está en modo "External", solo los usuarios agregados como "Test users" pueden autenticarse hasta que completes la verificación de Google (que puede tardar semanas). Para uso personal, agrega tu email como test user.

### Error: "Archivo de credenciales no encontrado"

- Verifica que `credentials.json` esté en la raíz del proyecto
- Verifica que `GOOGLE_CREDENTIALS_FILE` en `.env` apunte al archivo correcto

### Error: "Token expirado"

- Elimina `token.pickle`
- Ejecuta el bot nuevamente para reautenticarte

### Error: "Permisos insuficientes"

- Verifica que la API de Google Calendar esté habilitada
- Verifica que las credenciales OAuth sean del tipo "Desktop app"
- Verifica que hayas autorizado todos los permisos necesarios
- Verifica que tu email esté en la lista de "Test users"

## Seguridad

⚠️ **IMPORTANTE:**

- **NUNCA** subas `credentials.json` o `token.pickle` a Git
- Estos archivos están en `.gitignore` por defecto
- Si compartes el proyecto, cada usuario debe generar sus propias credenciales

## Próximos Pasos

Una vez configurado, el bot:
- Creará eventos en Google Calendar cuando se haga una reserva
- Eliminará eventos cuando se cancele una reserva
- Guardará el ID del evento en la base de datos para referencia futura


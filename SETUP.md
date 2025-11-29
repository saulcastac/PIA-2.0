# Guía de Configuración - PAD-IA

## Paso a Paso para Configurar el Sistema

### 1. Instalación de Dependencias

```bash
# Instalar Python 3.8 o superior si no lo tienes
python --version

# Crear entorno virtual (recomendado)
python -m venv venv

# Activar entorno virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instalar dependencias Python
pip install -r requirements.txt

# Instalar navegadores de Playwright
playwright install chromium
```

### 2. Configuración de Variables de Entorno

1. Copia el archivo `.env.example` a `.env`:
```bash
copy .env.example .env  # Windows
# o
cp .env.example .env    # Linux/Mac
```

2. Edita el archivo `.env` con tus credenciales:

```env
# Credenciales Playtomic
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

### 3. Configurar Playtomic Automation

El módulo `playtomic_automation.py` necesita ajustes según la estructura real de Playtomic:

1. Abre `playtomic_automation.py`
2. Inspecciona la página de Playtomic en el navegador
3. Ajusta los selectores CSS en:
   - `login()`: Selectores del formulario de login
   - `get_available_courts()`: Selectores de las canchas disponibles
   - `make_reservation()`: Selectores del proceso de reserva

**Ejemplo de cómo encontrar selectores:**
- Abre Playtomic en el navegador
- Haz clic derecho en el elemento que necesitas
- Selecciona "Inspeccionar"
- Copia el selector CSS o XPath

### 4. Configurar WhatsApp

El bot usa `whatsapp-web.py` que requiere:

1. Primera ejecución mostrará un código QR
2. Escanea el código con tu WhatsApp
3. La sesión se guardará en `whatsapp_session/`

**Nota**: Si cambias de número o necesitas desconectar:
- Elimina la carpeta `whatsapp_session/`
- Reinicia el bot para escanear nuevo QR

### 5. Inicializar Base de Datos

La base de datos se crea automáticamente al ejecutar por primera vez. Si necesitas reiniciarla:

```bash
# Elimina el archivo de base de datos
del pad_ia.db  # Windows
rm pad_ia.db   # Linux/Mac

# Se recreará automáticamente al ejecutar
```

### 6. Ejecutar el Sistema

```bash
python main.py
```

**Primera vez:**
- Se mostrará un QR para escanear con WhatsApp
- Espera a que se conecte
- El sistema estará listo cuando veas "✅ Sistema iniciado correctamente"

### 7. Probar el Sistema

1. Envía un mensaje de WhatsApp al bot: "hola"
2. Sigue el flujo de conversación
3. Prueba una reserva de prueba

## Ajustes Necesarios para Producción

### Playtomic Selectors

Debes ajustar los selectores en `playtomic_automation.py`:

```python
# Ejemplo de selectores que debes ajustar:
await self.page.click("text=Iniciar sesión")  # Ajustar según Playtomic
await self.page.fill('input[type="email"]', self.email)  # Verificar selector real
```

### Headless Mode

Para producción, cambia en `playtomic_automation.py`:

```python
# Cambiar de:
self.browser = await playwright.chromium.launch(headless=False)

# A:
self.browser = await playwright.chromium.launch(headless=True)
```

### Logging

Ajusta el nivel de logging en producción:

```python
# En cada módulo, cambiar:
logging.basicConfig(level=logging.INFO)

# A:
logging.basicConfig(level=logging.WARNING)
```

## Troubleshooting

### Error: "whatsapp-web.py no encontrado"
```bash
pip install whatsapp-web.py
```

### Error: "Playwright no está instalado"
```bash
playwright install chromium
```

### El bot no responde
- Verifica que WhatsApp Web esté conectado
- Revisa los logs para errores
- Verifica que la sesión de WhatsApp esté guardada

### Playtomic no funciona
- Verifica credenciales en `.env`
- Ejecuta con `headless=False` para ver qué pasa
- Ajusta los selectores CSS según la estructura real de Playtomic

### Recordatorios no se envían
- Verifica que el sistema de recordatorios esté corriendo
- Revisa la configuración de timezone
- Verifica que las reservas tengan fecha correcta

## Próximos Pasos

1. ✅ Configurar credenciales Playtomic
2. ✅ Ajustar selectores CSS de Playtomic
3. ✅ Probar con 5-10 reservas reales
4. ✅ Configurar número de WhatsApp oficial
5. ⏳ Implementar sistema de pagos (cuando esté listo)

## Soporte

Para problemas o preguntas, revisa los logs en la consola o contacta al equipo de desarrollo.


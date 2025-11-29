# Guía de Inicio Rápido - PAD-IA

## Solución al Error de whatsapp-web.py

El error indica que `whatsapp-web.py>=0.4.0` no existe. Solo está disponible la versión `0.1.0`.

## Opciones de Instalación

### Opción 1: Instalar whatsapp-web.py v0.1.0

```bash
pip install whatsapp-web.py==0.1.0
```

**Nota**: La API puede ser diferente. Puede requerir ajustes en el código.

### Opción 2: Usar Selenium (Recomendado - Ya Instalado)

Ya he instalado las dependencias de Selenium. Usa la implementación alternativa:

**Cambiar en `main.py`:**
```python
# Cambiar de:
from whatsapp_bot import get_bot_instance

# A:
from whatsapp_bot_selenium import PadelReservationBotSelenium as PadelReservationBot
```

Luego modificar `main.py` para usar la clase correctamente.

### Opción 3: Instalar todas las dependencias restantes

```bash
# Instalar el resto de dependencias (sin whatsapp-web.py)
pip install playwright sqlalchemy apscheduler python-dotenv pytz

# Instalar navegadores de Playwright
playwright install chromium
```

## Instalación Completa Recomendada

```bash
# 1. Instalar dependencias base (ya instaladas: selenium, webdriver-manager, qrcode, Pillow)
pip install playwright sqlalchemy apscheduler python-dotenv pytz python-dateutil requests pydantic

# 2. Instalar navegadores
playwright install chromium

# 3. (Opcional) Intentar instalar whatsapp-web.py
pip install whatsapp-web.py==0.1.0

# 4. Configurar .env
copy .env.example .env
# Editar .env con tus credenciales

# 5. Ejecutar
python main.py
```

## Nota Importante

El código actual usa `whatsapp-web.py`. Si no quieres usarlo:

1. **Usa la implementación Selenium** (`whatsapp_bot_selenium.py`)
2. **O ajusta `whatsapp_bot.py`** para la API de whatsapp-web.py v0.1.0

## Próximos Pasos

1. ✅ Dependencias base instaladas (Selenium, etc.)
2. ⏳ Instalar dependencias restantes
3. ⏳ Configurar .env
4. ⏳ Ajustar código según la librería de WhatsApp elegida
5. ⏳ Ejecutar y probar


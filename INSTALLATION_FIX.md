# Solución al Error de Instalación de whatsapp-web.py

## Problema

El paquete `whatsapp-web.py>=0.4.0` no existe en PyPI. Solo está disponible la versión `0.1.0`.

## Soluciones

### Opción 1: Usar whatsapp-web.py versión 0.1.0 (Recomendado para empezar)

```bash
pip install whatsapp-web.py==0.1.0
```

**Nota**: La API de la versión 0.1.0 puede ser diferente. Puede requerir ajustes en el código.

### Opción 2: Usar Selenium directamente (Más estable)

Ya he creado una implementación alternativa usando Selenium en `whatsapp_bot_selenium.py`.

**Instalar dependencias:**
```bash
pip install selenium webdriver-manager qrcode Pillow
```

**Cambiar en `main.py`:**
```python
# Cambiar de:
from whatsapp_bot import get_bot_instance

# A:
from whatsapp_bot_selenium import PadelReservationBotSelenium as PadelReservationBot
```

### Opción 3: Usar otra librería de WhatsApp

Alternativas populares:
- **whatsapp-api-client-python**: Para WhatsApp Business API (requiere cuenta oficial)
- **yowsup**: Librería antigua pero funcional
- **twilio**: Para WhatsApp Business API oficial (de pago)

## Instalación Recomendada

Para comenzar rápidamente, usa esta instalación:

```bash
# Instalar dependencias base
pip install -r requirements.txt

# Si whatsapp-web.py falla, instalar manualmente:
pip install whatsapp-web.py==0.1.0

# O usar la alternativa Selenium:
# El código ya está preparado en whatsapp_bot_selenium.py
```

## Verificación

Para verificar qué versión está instalada:

```bash
pip show whatsapp-web.py
```

## Próximos Pasos

1. **Probar whatsapp-web.py v0.1.0**:
   - Puede funcionar con ajustes menores
   - Verificar la API en la documentación

2. **Si no funciona, usar Selenium**:
   - Cambiar a `whatsapp_bot_selenium.py`
   - Más estable pero consume más recursos

3. **Para producción, considerar WhatsApp Business API**:
   - Requiere cuenta oficial de WhatsApp
   - Más robusto y escalable

## Nota Importante

La implementación actual en `whatsapp_bot.py` usa `whatsapp-web.py`. Si encuentras problemas:

1. Verifica la documentación de `whatsapp-web.py` v0.1.0
2. Ajusta el código según la API real
3. O cambia a la implementación Selenium


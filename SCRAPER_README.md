# Scraper de Playtomic - Guía de Uso

Este script independiente realiza web scraping de la disponibilidad de canchas en Playtomic y guarda los resultados en un archivo JSON que el bot de WhatsApp puede usar.

## Archivos

- **`scraper_playtomic.py`**: Script principal de scraping
- **`ejecutar_scraper.bat`**: Script para ejecutar el scraper manualmente
- **`ejecutar_scraper_periodico.bat`**: Script para ejecutar el scraper cada hora
- **`availability_cache.json`**: Archivo JSON con la disponibilidad cacheada (se crea automáticamente)

## Uso Manual

### Ejecutar una vez:
```bash
python scraper_playtomic.py [días]
```

**Ejemplos:**
```bash
# Scrapear 3 días (por defecto)
python scraper_playtomic.py

# Scrapear 7 días
python scraper_playtomic.py 7

# Scrapear 14 días
python scraper_playtomic.py 14
```

### Usando el script batch:
```bash
# Ejecutar una vez
ejecutar_scraper.bat

# Ejecutar periódicamente (cada hora)
ejecutar_scraper_periodico.bat
```

## Configuración Automática (Task Scheduler de Windows)

Para ejecutar el scraper automáticamente cada hora:

1. Abre **Task Scheduler** (Programador de tareas)
2. Clic en **"Create Basic Task"** (Crear tarea básica)
3. Nombre: `Playtomic Scraper`
4. Trigger: **Daily** (Diario)
5. Repetir cada: **1 hour** (1 hora)
6. Action: **Start a program** (Iniciar un programa)
7. Programa: `python`
8. Argumentos: `scraper_playtomic.py 7`
9. Iniciar en: `C:\Users\saulc\Documents\Cursor code\PAD-IA` (tu ruta del proyecto)

## Formato del Cache

El archivo `availability_cache.json` tiene el siguiente formato:

```json
{
  "timestamp": "2024-12-15T10:30:00",
  "scraped_days": 7,
  "availability": {
    "2024-12-15": [
      {
        "name": "Pista 1 Descubierta",
        "time": "18:00",
        "date": "2024-12-15"
      },
      ...
    ],
    "2024-12-16": [...],
    ...
  }
}
```

## Validez del Cache

- El cache es válido por **1 hora** (configurable en `MAX_CACHE_AGE_HOURS`)
- Si el cache expira, el bot buscará directamente en Playtomic
- El scraper puede ejecutarse más frecuentemente para mantener el cache actualizado

## Ventajas de este Sistema

✅ **No bloquea el bot**: El scraping se hace en segundo plano  
✅ **Respuestas rápidas**: El bot usa el cache para responder inmediatamente  
✅ **Fácil de depurar**: Puedes ejecutar el scraper manualmente y ver los resultados  
✅ **Escalable**: Puedes scrapear más días sin afectar la experiencia del usuario  
✅ **Robusto**: Si el scraper falla, el bot puede buscar directamente

## Troubleshooting

### El cache no se actualiza
- Verifica que el scraper se esté ejecutando correctamente
- Revisa los logs del scraper para ver errores
- Asegúrate de que el archivo `availability_cache.json` se esté creando

### El bot no encuentra canchas
- Verifica que el cache tenga datos para la fecha solicitada
- Revisa que el formato de fecha sea correcto (YYYY-MM-DD)
- Si el cache está vacío, el bot buscará directamente en Playtomic

### El scraper falla
- Verifica que Playwright esté instalado: `playwright install`
- Revisa que las credenciales de Playtomic estén correctas en `config.py`
- Verifica la conexión a internet







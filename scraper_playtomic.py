"""
Script independiente para hacer web scraping de Playtomic
Se ejecuta periódicamente y guarda disponibilidad en archivo JSON

Uso:
    python scraper_playtomic.py [días]

Ejemplo:
    python scraper_playtomic.py      # Scrapear 3 días (hoy + 2 días más) - por defecto
    python scraper_playtomic.py 3    # Scrapear 3 días (hoy + 2 días más)
    
Nota: El scraper está limitado a máximo 3 días para optimizar el rendimiento.
"""
import asyncio
import json
import sys
import os
from datetime import datetime, timedelta
from playtomic_automation import get_playtomic_instance
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True
)

logger = logging.getLogger(__name__)

# Configurar encoding para Windows
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

CACHE_FILE = 'availability_cache.json'
MAX_CACHE_AGE_HOURS = 1  # Cache válido por 1 hora


async def scrape_availability(days=3, club_name=None, club_url=None):
    """
    Scrapear disponibilidad de Playtomic y guardar en archivo JSON
    
    Args:
        days: Número de días a scrapear (por defecto 3)
        club_name: Nombre del club (opcional, usa config por defecto)
        club_url: URL del club (opcional, usa config por defecto)
    
    Returns:
        Diccionario con la disponibilidad por fecha
    """
    try:
        logger.info("=" * 80)
        logger.info("🚀 INICIANDO SCRAPER DE PLAYTOMIC")
        logger.info(f"📅 Días a scrapear: {days}")
        logger.info("=" * 80)
        
        # Obtener instancia de Playtomic
        logger.info("🔧 Obteniendo instancia de Playtomic...")
        playtomic = await get_playtomic_instance()
        logger.info("✅ Instancia obtenida")
        
        availability = {}
        today = datetime.now()
        
        for day_offset in range(days):
            date = today + timedelta(days=day_offset)
            date_str = date.strftime('%Y-%m-%d')
            date_formatted = date.strftime('%d/%m/%Y')
            
            logger.info("=" * 60)
            logger.info(f"📅 Scrapeando {date_str} ({date_formatted})...")
            logger.info("=" * 60)
            
            try:
                # Scrapear canchas disponibles para este día
                courts = await playtomic.get_available_courts(
                    date, 
                    time_slot=None,
                    club_name=club_name,
                    club_url=club_url
                )
                
                availability[date_str] = courts
                
                logger.info(f"✅ {date_str}: {len(courts)} canchas encontradas")
                
                # Mostrar resumen de canchas encontradas
                if courts:
                    logger.info("📋 Canchas encontradas:")
                    for i, court in enumerate(courts[:5], 1):
                        logger.info(f"   {i}. {court.get('name', 'N/A')} - {court.get('time', 'N/A')}")
                    if len(courts) > 5:
                        logger.info(f"   ... y {len(courts) - 5} más")
                
                # Pausa entre días para no sobrecargar
                if day_offset < days - 1:  # No esperar después del último día
                    logger.info("⏳ Esperando 2 segundos antes del siguiente día...")
                    await asyncio.sleep(2)
                    
            except Exception as e:
                logger.error(f"❌ Error scrapeando {date_str}: {e}")
                import traceback
                logger.error(traceback.format_exc())
                availability[date_str] = []
        
        # Guardar en archivo JSON
        cache_data = {
            'timestamp': datetime.now().isoformat(),
            'scraped_days': days,
            'availability': availability
        }
        
        logger.info("=" * 60)
        logger.info(f"💾 Guardando disponibilidad en {CACHE_FILE}...")
        
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)
        
        # Calcular estadísticas
        total_courts = sum(len(courts) for courts in availability.values())
        days_with_courts = sum(1 for courts in availability.values() if len(courts) > 0)
        
        logger.info("=" * 80)
        logger.info("✅ SCRAPING COMPLETADO")
        logger.info(f"📊 Total de canchas encontradas: {total_courts}")
        logger.info(f"📅 Días con disponibilidad: {days_with_courts}/{days}")
        logger.info(f"💾 Cache guardado en: {CACHE_FILE}")
        logger.info("=" * 80)
        
        return availability
        
    except Exception as e:
        logger.error(f"❌ Error en scraping: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {}


def load_availability_cache():
    """
    Cargar disponibilidad desde cache JSON
    
    Returns:
        Diccionario con disponibilidad si el cache es válido, None si no
    """
    try:
        if not os.path.exists(CACHE_FILE):
            logger.debug(f"Cache file {CACHE_FILE} no existe")
            return None
        
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Verificar que el cache no sea muy viejo
        cache_time = datetime.fromisoformat(data['timestamp'])
        age_hours = (datetime.now() - cache_time).total_seconds() / 3600
        
        if age_hours > MAX_CACHE_AGE_HOURS:
            logger.info(f"⚠️  Cache expirado (edad: {age_hours:.1f} horas)")
            return None
        
        logger.info(f"✅ Cache válido (edad: {age_hours:.1f} horas)")
        return data.get('availability', {})
        
    except Exception as e:
        logger.warning(f"⚠️  Error cargando cache: {e}")
        return None


async def main():
    """Función principal"""
    # Obtener número de días desde argumentos
    # Por defecto: 3 días (hoy + 2 días más)
    days = 3
    if len(sys.argv) > 1:
        try:
            days = int(sys.argv[1])
            if days < 1 or days > 30:
                logger.warning(f"⚠️  Número de días inválido ({days}), usando 3 por defecto")
                days = 3
        except ValueError:
            logger.warning(f"⚠️  Argumento inválido, usando 3 días por defecto")
    
    # Limitar a máximo 3 días (hoy + 2 días más)
    if days > 3:
        logger.info(f"⚠️  Limitando a 3 días (hoy + 2 días más). Solicitado: {days}")
        days = 3
    
    logger.info(f"📅 Scrapeando {days} días: hoy + {days-1} días más")
    
    # Ejecutar scraping
    await scrape_availability(days=days)
    
    # Cerrar instancia de Playtomic
    try:
        playtomic = await get_playtomic_instance()
        await playtomic.close()
    except:
        pass


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n⚠️  Scraping interrumpido por el usuario")
    except Exception as e:
        logger.error(f"❌ Error fatal: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


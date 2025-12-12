"""
Script de prueba para verificar reservas en múltiples calendarios de Google Calendar
Prueba que cada cancha se reserve en su calendario correspondiente
"""
import asyncio
import logging
from datetime import datetime, timedelta
from google_calendar_client import get_google_calendar_instance
from config import COURT_CALENDAR_MAPPING, TIMEZONE
import pytz

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_multi_calendar_reservations():
    """
    Probar reservas en múltiples calendarios
    """
    logger.info("=" * 60)
    logger.info("🧪 PRUEBA DE RESERVAS EN MÚLTIPLES CALENDARIOS")
    logger.info("=" * 60)
    
    try:
        # Obtener instancia de Google Calendar
        logger.info("🔧 Obteniendo instancia de Google Calendar...")
        calendar_client = await get_google_calendar_instance()
        
        if not calendar_client.authenticated:
            logger.error("❌ No se pudo autenticar con Google Calendar")
            return
        
        logger.info("✅ Autenticación exitosa")
        
        # Mostrar mapeo de canchas a calendarios
        logger.info("\n📋 Mapeo de canchas a calendarios:")
        for court_name, calendar_id in COURT_CALENDAR_MAPPING.items():
            logger.info(f"  • {court_name} → {calendar_id}")
        
        # Obtener fecha de mañana para las pruebas
        tz = pytz.timezone(TIMEZONE)
        tomorrow = datetime.now(tz) + timedelta(days=1)
        
        # Canchas a probar
        test_courts = ["MONEX", "GOCSA", "WOODWARD", "TEDS"]
        
        logger.info(f"\n📅 Fecha de prueba: {tomorrow.strftime('%d/%m/%Y')}")
        logger.info(f"⏰ Hora de prueba: 10:00")
        
        # Probar cada cancha
        created_events = []
        
        for i, court_name in enumerate(test_courts, 1):
            logger.info(f"\n{'=' * 60}")
            logger.info(f"🏓 Prueba {i}/4: Cancha {court_name}")
            logger.info(f"{'=' * 60}")
            
            # Verificar que la cancha tenga un calendario configurado
            calendar_id = COURT_CALENDAR_MAPPING.get(court_name)
            if not calendar_id or calendar_id == "primary":
                logger.warning(f"⚠️  Cancha {court_name} no tiene calendario específico configurado (usando 'primary')")
            else:
                logger.info(f"✅ Calendario configurado: {calendar_id}")
            
            # Crear evento de prueba
            test_time = "10:00"
            test_name = f"Prueba {court_name}"
            
            logger.info(f"🔄 Creando evento de prueba...")
            logger.info(f"   Cancha: {court_name}")
            logger.info(f"   Fecha: {tomorrow.strftime('%d/%m/%Y')}")
            logger.info(f"   Hora: {test_time}")
            logger.info(f"   Nombre: {test_name}")
            
            event_result = calendar_client.create_event(
                court_name=court_name,
                date=tomorrow,
                time_slot=test_time,
                duration_minutes=60,
                name=test_name,
                description=f"Evento de prueba para verificar calendario de {court_name}"
            )
            
            if event_result and event_result.get('id'):
                event_id = event_result.get('id')
                event_link = event_result.get('htmlLink', 'N/A')
                
                logger.info(f"✅ Evento creado exitosamente!")
                logger.info(f"   ID: {event_id}")
                logger.info(f"   Link: {event_link}")
                
                created_events.append({
                    'court': court_name,
                    'event_id': event_id,
                    'calendar_id': calendar_id,
                    'link': event_link
                })
            else:
                logger.error(f"❌ No se pudo crear el evento para {court_name}")
        
        # Resumen
        logger.info(f"\n{'=' * 60}")
        logger.info("📊 RESUMEN DE PRUEBAS")
        logger.info(f"{'=' * 60}")
        logger.info(f"✅ Eventos creados exitosamente: {len(created_events)}/{len(test_courts)}")
        
        if created_events:
            logger.info("\n📋 Eventos creados:")
            for event in created_events:
                logger.info(f"  • {event['court']}: {event['event_id']}")
                logger.info(f"    Calendario: {event['calendar_id']}")
                logger.info(f"    Link: {event['link']}")
            
            logger.info("\n💡 IMPORTANTE:")
            logger.info("   - Verifica en Google Calendar que cada evento esté en el calendario correcto")
            logger.info("   - Los eventos de prueba se pueden eliminar manualmente desde Google Calendar")
            logger.info("   - O ejecuta este script con --cleanup para eliminarlos automáticamente")
        else:
            logger.warning("⚠️  No se crearon eventos. Revisa la configuración.")
        
        return created_events
        
    except Exception as e:
        logger.error(f"❌ Error en la prueba: {e}")
        import traceback
        traceback.print_exc()
        return []


async def cleanup_test_events(event_ids: list):
    """
    Eliminar eventos de prueba
    """
    logger.info("\n🧹 Limpiando eventos de prueba...")
    
    try:
        calendar_client = await get_google_calendar_instance()
        
        for event_info in event_ids:
            court_name = event_info.get('court')
            event_id = event_info.get('event_id')
            
            logger.info(f"🗑️  Eliminando evento de {court_name}...")
            success = calendar_client.delete_event(event_id, court_name)
            
            if success:
                logger.info(f"✅ Evento eliminado: {event_id}")
            else:
                logger.warning(f"⚠️  No se pudo eliminar evento: {event_id}")
        
        logger.info("✅ Limpieza completada")
        
    except Exception as e:
        logger.error(f"❌ Error en limpieza: {e}")


if __name__ == "__main__":
    import sys
    
    # Verificar si se quiere limpiar eventos anteriores
    cleanup = "--cleanup" in sys.argv or "-c" in sys.argv
    
    if cleanup:
        logger.info("🧹 Modo limpieza activado")
        # En modo limpieza, necesitarías tener los IDs guardados
        # Por ahora, solo informamos
        logger.warning("⚠️  Para limpiar eventos, necesitas los IDs de eventos anteriores")
        logger.info("   Puedes eliminarlos manualmente desde Google Calendar")
    else:
        # Ejecutar pruebas
        events = asyncio.run(test_multi_calendar_reservations())
        
        if events:
            logger.info(f"\n💾 IDs de eventos creados (para limpieza futura):")
            for event in events:
                logger.info(f"  {event['court']}: {event['event_id']}")




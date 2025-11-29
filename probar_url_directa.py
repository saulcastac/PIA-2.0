"""
Script para probar reserva usando URL directa de la API de Playtomic
Usa la URL exacta proporcionada por el usuario
"""
import asyncio
from playtomic_api_client import PlaytomicAPIClient
import logging
import sys
import os

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True
)

# Configurar encoding para Windows
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

logger = logging.getLogger(__name__)


async def probar_url_directa():
    """
    Probar reserva usando la URL directa proporcionada
    """
    print("=" * 80)
    print("🧪 PRUEBA DE RESERVA CON URL DIRECTA")
    print("=" * 80)
    print()
    
    # URL proporcionada por el usuario
    payment_url = "https://playtomic.com/api/web-app/payments?type=CUSTOMER_MATCH&tenant_id=65a5b336-e05c-4989-a3b8-3374e9ad335f&resource_id=c5270541-aeec-4640-b67d-346bd8e9d072&start=2025-11-27T15%3A00%3A00.000Z&duration=60"
    
    print("📋 DETALLES DE LA RESERVA:")
    print(f"   🏢 Club: Carbono Manzanillo")
    print(f"   🏓 Cancha: GOCSA")
    print(f"   📅 Fecha: 27/11/2025")
    print(f"   ⏰ Hora: 15:00 UTC (9:00 AM hora local)")
    print(f"   ⏱️  Duración: 60 minutos")
    print()
    print(f"🔗 URL: {payment_url}")
    print()
    
    # Verificar credenciales
    email = os.getenv('PLAYTOMIC_EMAIL')
    password = os.getenv('PLAYTOMIC_PASSWORD')
    
    if not email or not password:
        print("❌ ERROR: Credenciales no configuradas")
        print("   Ejecuta 'python setup_env.py' para configurarlas")
        return
    
    print(f"👤 Usuario: {email}")
    print()
    
    # Crear instancia del cliente API
    playtomic_client = PlaytomicAPIClient()
    
    try:
        print("🚀 Iniciando cliente API...")
        await playtomic_client.start()
        print("✅ Cliente API iniciado")
        print()
        
        print("🔐 Iniciando sesión...")
        login_result = await playtomic_client.login(email, password)
        if not login_result:
            print("❌ Error: No se pudo iniciar sesión")
            print("   Verifica tus credenciales")
            return
        print("✅ Sesión iniciada correctamente")
        print()
        
        print("=" * 80)
        print("🎯 EJECUTANDO RESERVA CON URL DIRECTA")
        print("=" * 80)
        print()
        
        # Intentar hacer la reserva usando la URL directa
        reservation_id = await playtomic_client.make_reservation_from_url(payment_url)
        
        print()
        print("=" * 80)
        if reservation_id:
            print("✅ ¡RESERVA EXITOSA!")
            print(f"🆔 ID de reserva: {reservation_id}")
            print(f"🏓 Cancha: GOCSA")
            print(f"📅 Fecha: 27/11/2025")
            print(f"⏰ Hora: 15:00 UTC (9:00 AM local)")
            print(f"⏱️  Duración: 60 minutos")
        else:
            print("❌ RESERVA FALLIDA")
            print("Posibles causas:")
            print("- La cancha ya está ocupada en ese horario")
            print("- Horario fuera del rango permitido")
            print("- Problemas con el método de pago")
            print("- Sesión expirada o credenciales incorrectas")
            print("- La fecha/hora ya pasó")
            print()
            print("💡 SUGERENCIAS:")
            print("- Verifica que la fecha sea futura")
            print("- Comprueba la disponibilidad en la web de Playtomic")
            print("- Revisa los logs arriba para más detalles")
        print("=" * 80)
        
    except Exception as e:
        print()
        print("=" * 80)
        print(f"❌ ERROR: {e}")
        print("=" * 80)
        import traceback
        traceback.print_exc()
        
    finally:
        # Cerrar cliente API
        print()
        print("🔒 Cerrando cliente API...")
        await playtomic_client.close()
        print("✅ Cliente API cerrado")


if __name__ == "__main__":
    print()
    print("⚠️  ADVERTENCIA: Este script intentará hacer una reserva REAL en Playtomic")
    print("⚠️  Usando la URL directa proporcionada:")
    print("⚠️  Cancha GOCSA - 27/11/2025 - 15:00 UTC (9:00 AM local)")
    print()
    respuesta = input("¿Continuar con la reserva? (s/n): ").strip().lower()
    
    if respuesta in ['s', 'si', 'sí', 'y', 'yes']:
        try:
            asyncio.run(probar_url_directa())
        except KeyboardInterrupt:
            print("\n\n⚠️  Prueba interrumpida por el usuario")
    else:
        print("❌ Prueba cancelada")

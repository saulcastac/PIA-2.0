"""
Script de prueba para probar la funcionalidad de reserva usando navegador
Hace login en Playtomic y luego navega al link de reserva para automatizar el proceso de pago
"""
import asyncio
from datetime import datetime
from playtomic_browser_automation import PlaytomicBrowserAutomation
import logging
import sys
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

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


async def probar_reserva():
    """
    Probar la reserva usando navegador y automatización de clicks
    """
    print("=" * 80)
    print("🧪 PRUEBA DE RESERVA CON NAVEGADOR")
    print("=" * 80)
    print()
    
    # URL de reserva para cancha MONEX
    reservation_url = "https://playtomic.com/api/web-app/payments?type=CUSTOMER_MATCH&tenant_id=65a5b336-e05c-4989-a3b8-3374e9ad335f&resource_id=c5270541-aeec-4640-b67d-346bd8e9d072&start=2025-11-27T16%3A00%3A00.000Z&duration=60"
    
    print("📋 DETALLES DE LA RESERVA:")
    print(f"   🏢 Club: Carbono Manzanillo")
    print(f"   🏓 Cancha: MONEX")
    print(f"   📅 Fecha: 27/11/2025")
    print(f"   ⏰ Hora: 11:00 UTC (10:00 AM hora local)")
    print(f"   ⏱️  Duración: 60 minutos")
    print()
    print(f"🔗 URL: {reservation_url}")
    print()
    
    # Verificar credenciales
    email = os.getenv('PLAYTOMIC_EMAIL')
    password = os.getenv('PLAYTOMIC_PASSWORD')
    
    print("🔍 Verificando credenciales...")
    print(f"   Email encontrado: {'Sí' if email else 'No'}")
    print(f"   Password encontrado: {'Sí' if password else 'No'}")
    print()
    
    if not email or not password:
        print("❌ ERROR: Credenciales no configuradas")
        print("   Configura las variables de entorno:")
        print("   - PLAYTOMIC_EMAIL: tu email de Playtomic")
        print("   - PLAYTOMIC_PASSWORD: tu contraseña de Playtomic")
        print()
        print("   Ejemplo en Windows PowerShell:")
        print("   $env:PLAYTOMIC_EMAIL='tu_email@ejemplo.com'")
        print("   $env:PLAYTOMIC_PASSWORD='tu_contraseña'")
        print()
        print("   O ejecuta: python setup_env.py")
        return
    
    print(f"👤 Usuario: {email}")
    print()
    
    # Crear instancia del automatizador de navegador
    playtomic_automation = PlaytomicBrowserAutomation()
    
    try:
        print("🚀 Iniciando navegador...")
        # Iniciar en modo visible para poder ver qué pasa
        await playtomic_automation.start(headless=False)
        print("✅ Navegador iniciado")
        print()
        
        print("🔐 Iniciando sesión en Playtomic...")
        login_result = await playtomic_automation.login(email, password)
        if not login_result:
            print("❌ Error: No se pudo iniciar sesión")
            print("   Verifica tus credenciales y que tu cuenta esté activa")
            return
        print("✅ Sesión iniciada correctamente")
        print()
        
        print("=" * 80)
        print("🎯 NAVEGANDO AL LINK DE RESERVA")
        print("=" * 80)
        print()
        
        # Hacer la reserva usando el URL proporcionado
        reservation_id = await playtomic_automation.make_reservation_from_url(reservation_url)
        
        print()
        print("=" * 80)
        if reservation_id:
            print("✅ ¡RESERVA EXITOSA!")
            print(f"🆔 ID de reserva: {reservation_id}")
            print(f"🏓 Cancha: MONEX")
            print(f"📅 Fecha: 27/11/2025")
            print(f"⏰ Hora: 15:00 UTC (10:00 AM local)")
            print(f"⏱️  Duración: 60 minutos")
        else:
            print("❌ RESERVA FALLIDA")
            print("No se pudo completar la reserva. Posibles causas:")
            print("- La cancha ya está ocupada en ese horario")
            print("- Horario fuera del rango permitido")
            print("- Problemas con el método de pago")
            print("- Sesión expirada")
            print("- La fecha/hora ya pasó")
            print()
            print("💡 SUGERENCIAS:")
            print("- Verifica que la fecha sea futura")
            print("- Comprueba la disponibilidad manualmente en Playtomic")
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
        # Cerrar navegador
        print()
        print("🔒 Cerrando navegador...")
        await playtomic_automation.close()
        print("✅ Navegador cerrado")


if __name__ == "__main__":
    print()
    print("⚠️  ADVERTENCIA: Este script intentará hacer una reserva REAL en Playtomic")
    print("⚠️  Asegúrate de que la fecha, horario y cancha estén disponibles")
    print("⚠️  Necesitas configurar las variables de entorno PLAYTOMIC_EMAIL y PLAYTOMIC_PASSWORD")
    print()
    respuesta = input("¿Continuar? (s/n): ").strip().lower()
    
    if respuesta in ['s', 'si', 'sí', 'y', 'yes']:
        try:
            asyncio.run(probar_reserva())
        except KeyboardInterrupt:
            print("\n\n⚠️  Prueba interrumpida por el usuario")
    else:
        print("❌ Prueba cancelada")


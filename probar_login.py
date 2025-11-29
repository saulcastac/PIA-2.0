"""
Script simple para probar solo el login con Playtomic
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

logger = logging.getLogger(__name__)


async def probar_solo_login():
    """
    Probar solo el proceso de login
    """
    print("=" * 60)
    print("🧪 PRUEBA DE LOGIN EN PLAYTOMIC")
    print("=" * 60)
    print()
    
    # Verificar credenciales
    email = os.getenv('PLAYTOMIC_EMAIL')
    password = os.getenv('PLAYTOMIC_PASSWORD')
    
    if not email or not password:
        print("❌ ERROR: Credenciales no configuradas")
        print("   Ejecuta 'python setup_env.py' para configurarlas")
        return
    
    print(f"👤 Usuario: {email}")
    print(f"🔑 Password: {'*' * len(password)}")
    print()
    
    # Crear instancia del cliente API
    client = PlaytomicAPIClient()
    
    try:
        print("🚀 Iniciando cliente...")
        await client.start()
        print("✅ Cliente iniciado")
        print()
        
        print("🔐 Intentando login...")
        login_result = await client.login(email, password)
        
        print()
        print("=" * 60)
        if login_result:
            print("✅ ¡LOGIN EXITOSO!")
            print("Las cookies de sesión han sido obtenidas")
            
            # Mostrar algunas cookies para verificar
            cookies = list(client.session.cookie_jar)
            print(f"🍪 Cookies obtenidas: {len(cookies)}")
            for cookie in cookies[:3]:  # Mostrar solo las primeras 3
                print(f"   - {cookie.key}: {cookie.value[:20]}...")
        else:
            print("❌ LOGIN FALLIDO")
            print("Verifica tus credenciales")
        print("=" * 60)
        
    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ ERROR: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        
    finally:
        print()
        print("🔒 Cerrando cliente...")
        await client.close()
        print("✅ Cliente cerrado")


if __name__ == "__main__":
    print()
    print("Este script solo probará el login, no hará ninguna reserva")
    print()
    
    try:
        asyncio.run(probar_solo_login())
    except KeyboardInterrupt:
        print("\n\n⚠️  Prueba interrumpida por el usuario")

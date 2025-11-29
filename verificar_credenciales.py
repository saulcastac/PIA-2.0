"""
Script para verificar las credenciales de Playtomic
"""
import os
from dotenv import load_dotenv

def verificar_credenciales():
    """Verificar que las credenciales estén configuradas"""
    
    print("🔍 VERIFICANDO CREDENCIALES")
    print("=" * 50)
    print()
    
    # Cargar variables de entorno desde .env
    load_dotenv()
    
    # Verificar variables
    email = os.getenv('PLAYTOMIC_EMAIL')
    password = os.getenv('PLAYTOMIC_PASSWORD')
    
    print("📋 ESTADO DE LAS VARIABLES:")
    print()
    
    if email:
        # Mostrar solo parte del email por seguridad
        email_display = email[:3] + "***" + email[email.find('@'):]
        print(f"✅ PLAYTOMIC_EMAIL: {email_display}")
    else:
        print("❌ PLAYTOMIC_EMAIL: NO CONFIGURADA")
    
    if password:
        print(f"✅ PLAYTOMIC_PASSWORD: {'*' * len(password)} (configurada)")
    else:
        print("❌ PLAYTOMIC_PASSWORD: NO CONFIGURADA")
    
    print()
    
    if email and password:
        print("✅ CREDENCIALES CORRECTAMENTE CONFIGURADAS")
        return True
    else:
        print("❌ FALTAN CREDENCIALES")
        print()
        print("💡 SOLUCIONES:")
        print("1. Ejecuta: python setup_env.py")
        print("2. O configura manualmente:")
        print("   set PLAYTOMIC_EMAIL=tu_email@ejemplo.com")
        print("   set PLAYTOMIC_PASSWORD=tu_contraseña")
        print("3. O verifica que el archivo .env tenga el formato correcto")
        return False

if __name__ == "__main__":
    verificar_credenciales()

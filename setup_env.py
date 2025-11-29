"""
Script para configurar las variables de entorno necesarias para el sistema
"""
import os
from pathlib import Path

def create_env_file():
    """Crear archivo .env con las variables necesarias"""
    
    env_file = Path(".env")
    
    print("🔧 Configuración del Sistema de Reservas de Pádel")
    print("=" * 50)
    print()
    
    # Verificar si ya existe
    if env_file.exists():
        print("⚠️  El archivo .env ya existe.")
        respuesta = input("¿Deseas sobrescribirlo? (s/n): ").strip().lower()
        if respuesta not in ['s', 'si', 'sí', 'y', 'yes']:
            print("❌ Configuración cancelada")
            return
    
    print("Ingresa las siguientes credenciales:")
    print()
    
    # Credenciales Playtomic
    print("📱 CREDENCIALES PLAYTOMIC:")
    email = input("Email de Playtomic: ").strip()
    password = input("Contraseña de Playtomic: ").strip()
    print()
    
    # Credenciales Twilio (opcional)
    print("📞 CREDENCIALES TWILIO (opcional - para WhatsApp):")
    print("Si no tienes Twilio configurado, puedes dejarlo en blanco por ahora")
    twilio_sid = input("Twilio Account SID (opcional): ").strip()
    twilio_token = input("Twilio Auth Token (opcional): ").strip()
    twilio_number = input("Twilio WhatsApp Number (ej: whatsapp:+14155238886) (opcional): ").strip()
    print()
    
    # Credenciales OpenAI (opcional)
    print("🤖 CREDENCIALES OPENAI (opcional - para chatbot AI):")
    print("Si no tienes OpenAI API key, el bot usará extracción básica")
    openai_key = input("OpenAI API Key (opcional): ").strip()
    print()
    
    # Crear contenido del archivo .env
    env_content = f"""# Credenciales Playtomic
PLAYTOMIC_EMAIL={email}
PLAYTOMIC_PASSWORD={password}

# Configuración API Playtomic
PLAYTOMIC_TENANT_ID=65a5b336-e05c-4989-a3b8-3374e9ad335f
PLAYTOMIC_CLUB_NAME=Carbono Manzanillo

# IDs de las canchas (ya configurados para Carbono Manzanillo)
PLAYTOMIC_MONEX_ID=da1fda51-61f8-4432-92b9-d93f980ed106
PLAYTOMIC_GOCSA_ID=c5270541-aeec-4640-b67d-346bd8e9d072
PLAYTOMIC_WOODWARD_ID=
PLAYTOMIC_TEDS_ID=

# Credenciales Twilio WhatsApp
TWILIO_ACCOUNT_SID={twilio_sid}
TWILIO_AUTH_TOKEN={twilio_token}
TWILIO_WHATSAPP_NUMBER={twilio_number}

# Credenciales OpenAI
OPENAI_API_KEY={openai_key}

# Configuración general
TIMEZONE=America/Argentina/Buenos_Aires
DATABASE_URL=sqlite:///./pad_ia.db

# Configuración de recordatorios
REMINDER_24H_ENABLED=true
REMINDER_3H_ENABLED=true
NO_SHOW_TOLERANCE_MINUTES=10
MAX_STRIKES=2
"""
    
    # Escribir archivo
    try:
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(env_content)
        
        print("✅ Archivo .env creado exitosamente")
        print()
        print("📋 PRÓXIMOS PASOS:")
        print("1. Ejecuta 'python probar_reserva.py' para probar la conexión")
        print("2. Si funciona, ejecuta 'python main.py' para iniciar el sistema completo")
        print("3. Para WhatsApp, configura Twilio siguiendo TWILIO_SETUP.md")
        print()
        print("⚠️  IMPORTANTE: Mantén tus credenciales seguras y no las compartas")
        
    except Exception as e:
        print(f"❌ Error creando archivo .env: {e}")

def verify_env():
    """Verificar que las variables de entorno estén configuradas"""
    
    print("🔍 Verificando configuración...")
    print()
    
    # Cargar variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Variables requeridas
    required_vars = {
        'PLAYTOMIC_EMAIL': 'Email de Playtomic',
        'PLAYTOMIC_PASSWORD': 'Contraseña de Playtomic',
        'PLAYTOMIC_TENANT_ID': 'ID del club',
        'PLAYTOMIC_MONEX_ID': 'ID de cancha MONEX',
        'PLAYTOMIC_GOCSA_ID': 'ID de cancha GOCSA'
    }
    
    # Variables opcionales
    optional_vars = {
        'TWILIO_ACCOUNT_SID': 'Twilio Account SID',
        'TWILIO_AUTH_TOKEN': 'Twilio Auth Token',
        'TWILIO_WHATSAPP_NUMBER': 'Número WhatsApp de Twilio'
    }
    
    all_good = True
    
    print("✅ VARIABLES REQUERIDAS:")
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            # Mostrar solo los primeros caracteres para seguridad
            display_value = value[:10] + "..." if len(value) > 10 else value
            print(f"   {description}: {display_value}")
        else:
            print(f"   ❌ {description}: NO CONFIGURADA")
            all_good = False
    
    print()
    print("📋 VARIABLES OPCIONALES:")
    for var, description in optional_vars.items():
        value = os.getenv(var)
        if value:
            display_value = value[:10] + "..." if len(value) > 10 else value
            print(f"   {description}: {display_value}")
        else:
            print(f"   ⚠️  {description}: No configurada")
    
    print()
    if all_good:
        print("✅ Configuración básica completa")
        print("Puedes ejecutar 'python probar_reserva.py' para probar")
    else:
        print("❌ Faltan variables requeridas")
        print("Ejecuta este script de nuevo para configurarlas")

if __name__ == "__main__":
    print()
    print("¿Qué deseas hacer?")
    print("1. Crear/actualizar archivo .env")
    print("2. Verificar configuración actual")
    print()
    
    opcion = input("Selecciona una opción (1/2): ").strip()
    
    if opcion == "1":
        create_env_file()
    elif opcion == "2":
        verify_env()
    else:
        print("❌ Opción inválida")

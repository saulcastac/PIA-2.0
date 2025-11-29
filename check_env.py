"""
Script simple para verificar credenciales
"""
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

print("VERIFICANDO CREDENCIALES")
print("=" * 40)
print()

email = os.getenv('PLAYTOMIC_EMAIL')
password = os.getenv('PLAYTOMIC_PASSWORD')

print("Estado de las variables:")
print()

if email:
    email_display = email[:3] + "***" + email[email.find('@'):] if '@' in email else email[:3] + "***"
    print(f"PLAYTOMIC_EMAIL: {email_display}")
else:
    print("PLAYTOMIC_EMAIL: NO CONFIGURADA")

if password:
    print(f"PLAYTOMIC_PASSWORD: {'*' * len(password)} (configurada)")
else:
    print("PLAYTOMIC_PASSWORD: NO CONFIGURADA")

print()

if email and password:
    print("CREDENCIALES OK")
else:
    print("FALTAN CREDENCIALES")
    print()
    print("SOLUCION:")
    print("1. Ejecuta: python setup_env.py")
    print("2. O configura manualmente en PowerShell:")
    print("   $env:PLAYTOMIC_EMAIL='tu_email@ejemplo.com'")
    print("   $env:PLAYTOMIC_PASSWORD='tu_contraseña'")

"""
Script para verificar el entorno de Python y las dependencias
"""
import sys
import os

# Configurar encoding para Windows
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=" * 60)
print("VERIFICACION DEL ENTORNO DE PYTHON")
print("=" * 60)
print(f"Python ejecutable: {sys.executable}")
print(f"Version de Python: {sys.version}")
print(f"Ruta de Python: {sys.path[0]}")
print("=" * 60)

# Verificar dependencias críticas
dependencias = [
    "sqlalchemy",
    "flask",
    "twilio",
    "playwright",
    "apscheduler",
    "pytz"
]

print("\nVERIFICANDO DEPENDENCIAS:")
print("-" * 60)
for dep in dependencias:
    try:
        mod = __import__(dep)
        version = getattr(mod, '__version__', 'N/A')
        print(f"[OK] {dep}: {version}")
    except ImportError:
        print(f"[ERROR] {dep}: NO INSTALADO")
        print(f"   Instala con: python -m pip install {dep}")

print("=" * 60)
print("\nSi alguna dependencia falta, ejecuta:")
print("python -m pip install -r requirements.txt")
print("=" * 60)


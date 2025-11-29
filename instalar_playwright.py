"""
Script para instalar Playwright y sus navegadores
"""
import subprocess
import sys
import os

def install_playwright():
    """Instalar Playwright y sus dependencias"""
    
    print("🎭 INSTALACIÓN DE PLAYWRIGHT")
    print("=" * 50)
    print()
    
    try:
        # Verificar si playwright ya está instalado
        import playwright
        print("✅ Playwright ya está instalado")
    except ImportError:
        print("📦 Instalando Playwright...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright"])
        print("✅ Playwright instalado")
    
    print()
    print("🌐 Instalando navegadores de Playwright...")
    print("   Esto puede tomar varios minutos...")
    
    try:
        # Instalar navegadores
        subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
        print("✅ Navegador Chromium instalado")
        
        print()
        print("🎉 ¡Instalación completada!")
        print()
        print("📋 PRÓXIMOS PASOS:")
        print("1. Ejecuta 'python setup_env.py' si no has configurado credenciales")
        print("2. Ejecuta 'python probar_reserva.py' para probar el sistema")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error instalando navegadores: {e}")
        print()
        print("💡 SOLUCIÓN ALTERNATIVA:")
        print("Ejecuta manualmente: playwright install chromium")
        return False
    
    return True

if __name__ == "__main__":
    print()
    print("Este script instalará Playwright y sus navegadores")
    print("Necesario para la automatización del navegador")
    print()
    
    respuesta = input("¿Continuar con la instalación? (s/n): ").strip().lower()
    
    if respuesta in ['s', 'si', 'sí', 'y', 'yes']:
        install_playwright()
    else:
        print("❌ Instalación cancelada")

"""
Script para verificar que el servidor Flask esté corriendo correctamente
"""
import requests
import sys
import time

def verificar_servidor():
    """Verificar que el servidor Flask esté corriendo"""
    print("=" * 60)
    print("VERIFICANDO SERVIDOR FLASK")
    print("=" * 60)
    
    url = "http://localhost:5000/health"
    
    try:
        print(f"🔍 Intentando conectar a {url}...")
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            print("✅ Servidor Flask está corriendo correctamente")
            print(f"   Respuesta: {response.json()}")
            return True
        else:
            print(f"⚠️  Servidor respondió con código: {response.status_code}")
            print(f"   Respuesta: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: No se pudo conectar al servidor Flask")
        print("   El servidor no está corriendo en localhost:5000")
        print("\n💡 Soluciones:")
        print("   1. Asegúrate de que el servidor esté corriendo:")
        print("      python main.py")
        print("   2. Verifica que no haya otro proceso usando el puerto 5000")
        print("   3. Espera unos segundos después de iniciar el servidor")
        return False
        
    except requests.exceptions.Timeout:
        print("❌ ERROR: Timeout al conectar al servidor")
        print("   El servidor puede estar iniciando o hay un problema de red")
        return False
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def verificar_webhook():
    """Verificar que el endpoint /webhook esté disponible"""
    print("\n" + "=" * 60)
    print("VERIFICANDO ENDPOINT /webhook")
    print("=" * 60)
    
    url = "http://localhost:5000/webhook"
    
    try:
        # Hacer un POST vacío para verificar que el endpoint existe
        response = requests.post(url, timeout=5, json={})
        print(f"✅ Endpoint /webhook está disponible")
        print(f"   Código de respuesta: {response.status_code}")
        return True
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: No se pudo conectar al endpoint /webhook")
        return False
    except Exception as e:
        print(f"⚠️  Advertencia: {e}")
        return False

if __name__ == "__main__":
    print("\n🔧 Verificador de Servidor Flask\n")
    
    # Verificar servidor
    servidor_ok = verificar_servidor()
    
    if servidor_ok:
        # Verificar webhook
        webhook_ok = verificar_webhook()
        
        print("\n" + "=" * 60)
        if servidor_ok and webhook_ok:
            print("✅ TODO ESTÁ FUNCIONANDO CORRECTAMENTE")
            print("   El servidor Flask está listo para recibir requests de ngrok")
        else:
            print("⚠️  ALGUNOS PROBLEMAS DETECTADOS")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ EL SERVIDOR NO ESTÁ CORRIENDO")
        print("=" * 60)
        print("\nPasos para solucionar:")
        print("1. Abre una nueva terminal")
        print("2. Navega a la carpeta del proyecto")
        print("3. Ejecuta: python main.py")
        print("4. Espera a ver el mensaje: '✅ Servidor Flask verificado'")
        print("5. Luego ejecuta ngrok en otra terminal")
        print("6. Vuelve a ejecutar este script para verificar")
        sys.exit(1)









"""
Prueba de integración completa sin caracteres especiales
"""
import asyncio
from ai_chatbot import PadelReservationChatbot
from playtomic_browser_automation import PlaytomicBrowserAutomation
import logging
import sys

# Configurar logging simple
logging.basicConfig(level=logging.WARNING)

async def test_reserva_completa():
    """Probar integración completa con reserva real"""
    
    print("PRUEBA DE INTEGRACION COMPLETA")
    print("=" * 50)
    print()
    
    # Mensaje de prueba
    test_message = "Si, quiero reservar manana a las 11:00 AM en MONEX"
    
    print(f"Mensaje simulado: {test_message}")
    print()
    
    # Procesar con chatbot
    print("PASO 1: PROCESANDO MENSAJE")
    print("-" * 30)
    
    chatbot = PadelReservationChatbot()
    info = chatbot.extract_reservation_info(test_message)
    
    print(f"Info extraida: {info}")
    
    # Verificar si es válido
    if info.get("confirmado") and info.get("fecha") and info.get("hora"):
        print("OK - Mensaje valido para reserva")
        
        # Generar URL
        url = chatbot.generate_reservation_url(info)
        print(f"URL: {url[:80]}...")
        
        print()
        print("PASO 2: CONFIRMACION")
        print("-" * 30)
        print("ADVERTENCIA: Esto hara una reserva REAL")
        print(f"Cancha: {info.get('cancha')}")
        print(f"Fecha: {info.get('fecha')}")
        print(f"Hora: {info.get('hora')}")
        print()
        
        # Pedir confirmación
        confirmacion = input("Continuar con reserva REAL? (s/n): ").strip().lower()
        
        if confirmacion in ['s', 'si', 'y', 'yes']:
            print()
            print("PASO 3: EJECUTANDO RESERVA")
            print("-" * 30)
            
            automation = PlaytomicBrowserAutomation()
            
            try:
                print("Iniciando navegador...")
                await automation.start(headless=False)
                
                print("Haciendo login...")
                login_ok = await automation.login()
                if not login_ok:
                    print("ERROR: Login fallo")
                    return
                
                print("OK - Login exitoso")
                
                print("Procesando reserva...")
                reservation_id = await automation.make_reservation_from_url(url)
                
                print()
                print("RESULTADO FINAL")
                print("=" * 30)
                
                if reservation_id:
                    print("EXITO - RESERVA CONFIRMADA!")
                    print(f"ID: {reservation_id}")
                    print(f"Cancha: {info.get('cancha')}")
                    print(f"Fecha: {info.get('fecha')}")
                    print(f"Hora: {info.get('hora')}")
                    
                    print()
                    print("Mensaje para WhatsApp:")
                    print("-" * 20)
                    whatsapp_msg = f"""RESERVA CONFIRMADA!

ID: {reservation_id}
Cancha: {info.get('cancha')}
Fecha: {info.get('fecha')}
Hora: {info.get('hora')}
Duracion: {info.get('duracion')} min

Nos vemos en la cancha!"""
                    print(whatsapp_msg)
                    
                else:
                    print("ERROR - RESERVA FALLO")
                    print("Posibles causas:")
                    print("- Cancha ocupada")
                    print("- Horario no disponible")
                    
                    print()
                    print("Mensaje de error para WhatsApp:")
                    print("-" * 20)
                    error_msg = f"""No se pudo completar la reserva

Cancha: {info.get('cancha')}
Fecha: {info.get('fecha')}
Hora: {info.get('hora')}

Intenta con otro horario."""
                    print(error_msg)
                    
            except Exception as e:
                print(f"ERROR: {e}")
                
            finally:
                await automation.close()
                print("Navegador cerrado")
        else:
            print("Reserva cancelada")
    else:
        print("ERROR - Mensaje no valido para reserva")
        response = chatbot.generate_response_message(info)
        print(f"Respuesta: {response}")

if __name__ == "__main__":
    try:
        asyncio.run(test_reserva_completa())
    except KeyboardInterrupt:
        print("\nPrueba interrumpida")

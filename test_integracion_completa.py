"""
Prueba de integración completa: Chatbot + Automatización de reserva real
Simula un mensaje de WhatsApp y hace una reserva real en Playtomic
"""
import asyncio
from ai_chatbot import PadelReservationChatbot
from playtomic_browser_automation import PlaytomicBrowserAutomation
import logging
import sys

# Configurar logging simple
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

async def test_integracion_completa():
    """Probar integración completa con reserva real"""
    
    print("PRUEBA DE INTEGRACION COMPLETA")
    print("=" * 50)
    print()
    
    # Mensaje de prueba que debería activar una reserva
    test_message = "Si, quiero reservar manana a las 11:00 AM en MONEX"
    
    print(f"Mensaje simulado: {test_message}")
    print()
    
    # Paso 1: Procesar mensaje con chatbot
    print("PASO 1: PROCESANDO MENSAJE CON CHATBOT")
    print("-" * 40)
    
    chatbot = PadelReservationChatbot()
    reservation_info = chatbot.extract_reservation_info(test_message)
    
    print(f"Informacion extraida: {reservation_info}")
    
    # Verificar si es válido para reserva
    if reservation_info.get("confirmado") and reservation_info.get("fecha") and reservation_info.get("hora"):
        print("✓ Mensaje valido para reserva automatica")
        
        # Generar URL
        reservation_url = chatbot.generate_reservation_url(reservation_info)
        print(f"URL generada: {reservation_url}")
        
        # Generar respuesta para usuario
        response_message = chatbot.generate_response_message(reservation_info)
        print(f"Respuesta para usuario: {response_message}")
        
        print()
        print("PASO 2: CONFIRMACION DE RESERVA REAL")
        print("-" * 40)
        print("ADVERTENCIA: Esto hara una reserva REAL en Playtomic")
        print(f"Cancha: {reservation_info.get('cancha')}")
        print(f"Fecha: {reservation_info.get('fecha')}")
        print(f"Hora: {reservation_info.get('hora')}")
        print()
        
        # Pedir confirmación
        confirmacion = input("Continuar con reserva REAL? (s/n): ").strip().lower()
        
        if confirmacion in ['s', 'si', 'y', 'yes']:
            print()
            print("PASO 3: EJECUTANDO RESERVA AUTOMATICA")
            print("-" * 40)
            
            # Crear automatización
            automation = PlaytomicBrowserAutomation()
            
            try:
                # Iniciar navegador (visible para ver el proceso)
                print("Iniciando navegador...")
                await automation.start(headless=False)
                
                # Login
                print("Haciendo login...")
                login_success = await automation.login()
                if not login_success:
                    print("ERROR: No se pudo hacer login")
                    return
                
                print("✓ Login exitoso")
                
                # Hacer reserva
                print("Procesando reserva...")
                reservation_id = await automation.make_reservation_from_url(reservation_url)
                
                print()
                print("RESULTADO FINAL")
                print("=" * 50)
                
                if reservation_id:
                    print("✓ RESERVA EXITOSA!")
                    print(f"ID de reserva: {reservation_id}")
                    print(f"Cancha: {reservation_info.get('cancha')}")
                    print(f"Fecha: {reservation_info.get('fecha')}")
                    print(f"Hora: {reservation_info.get('hora')}")
                    
                    # Mensaje que se enviaría por WhatsApp
                    whatsapp_response = f"""RESERVA CONFIRMADA!

ID: {reservation_id}
Cancha: {reservation_info.get('cancha')}
Fecha: {reservation_info.get('fecha')}
Hora: {reservation_info.get('hora')}
Duracion: {reservation_info.get('duracion')} min

Nos vemos en la cancha!"""
                    
                    print()
                    print("Mensaje que se enviaria por WhatsApp:")
                    print("-" * 30)
                    print(whatsapp_response)
                    
                else:
                    print("✗ RESERVA FALLO")
                    print("Posibles causas:")
                    print("- Cancha ocupada")
                    print("- Horario no disponible")
                    print("- Problemas tecnicos")
                    
                    # Mensaje de error para WhatsApp
                    error_response = f"""No se pudo completar la reserva

Cancha: {reservation_info.get('cancha')}
Fecha: {reservation_info.get('fecha')}
Hora: {reservation_info.get('hora')}

Intenta con otro horario o contacta soporte."""
                    
                    print()
                    print("Mensaje de error para WhatsApp:")
                    print("-" * 30)
                    print(error_response)
                    
            except Exception as e:
                print(f"ERROR durante reserva: {e}")
                
            finally:
                # Cerrar navegador
                await automation.close()
                print()
                print("Navegador cerrado")
        else:
            print("Reserva cancelada por el usuario")
    else:
        print("✗ Mensaje no valido para reserva automatica")
        response = chatbot.generate_response_message(reservation_info)
        print(f"Respuesta que se enviaria: {response}")

if __name__ == "__main__":
    try:
        asyncio.run(test_integracion_completa())
    except KeyboardInterrupt:
        print("\nPrueba interrumpida por el usuario")

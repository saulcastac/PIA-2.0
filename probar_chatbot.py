"""
Script para probar el chatbot AI sin WhatsApp
Simula mensajes y muestra las respuestas
"""
import asyncio
from ai_chatbot import PadelReservationChatbot
from playtomic_browser_automation import PlaytomicBrowserAutomation
import logging
import sys

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True
)

logger = logging.getLogger(__name__)


async def test_chatbot():
    """Probar el chatbot AI"""
    
    print("🤖 PRUEBA DEL CHATBOT AI")
    print("=" * 50)
    print()
    
    # Crear chatbot
    chatbot = PadelReservationChatbot()
    
    # Mensajes de prueba
    test_messages = [
        "Hola, quiero reservar mañana a las 10:00 AM",
        "Reservar MONEX para mañana 16:00",
        "¿Puedo hacer una reserva?",
        "Sí, confirmar reserva para mañana 11:00",
        "Quiero reservar el 28/11/2025 a las 15:30"
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"📱 MENSAJE {i}: {message}")
        print("-" * 30)
        
        # Extraer información
        info = chatbot.extract_reservation_info(message)
        print(f"📊 Info extraída: {info}")
        
        # Generar URL
        url = chatbot.generate_reservation_url(info)
        print(f"🔗 URL: {url}")
        
        # Generar respuesta
        response = chatbot.generate_response_message(info)
        print(f"💬 Respuesta: {response}")
        
        print()
        print("=" * 50)
        print()


async def test_full_integration():
    """Probar integración completa (chatbot + automatización)"""
    
    print("🎯 PRUEBA DE INTEGRACIÓN COMPLETA")
    print("=" * 50)
    print()
    
    # Mensaje de prueba que debería activar una reserva
    test_message = "Sí, quiero reservar mañana a las 11:00 AM en MONEX"
    
    print(f"📱 Mensaje de prueba: {test_message}")
    print()
    
    # Crear chatbot
    chatbot = PadelReservationChatbot()
    
    # Extraer información
    info = chatbot.extract_reservation_info(test_message)
    print(f"📊 Información extraída: {info}")
    
    if info.get("confirmado") and info.get("fecha") and info.get("hora"):
        print("✅ Mensaje válido para reserva")
        
        # Generar URL
        url = chatbot.generate_reservation_url(info)
        print(f"🔗 URL generada: {url}")
        
        # Preguntar si quiere hacer la reserva real
        print()
        respuesta = input("¿Quieres hacer la reserva REAL? (s/n): ").strip().lower()
        
        if respuesta in ['s', 'si', 'sí', 'y', 'yes']:
            print()
            print("🚀 Iniciando proceso de reserva...")
            
            # Crear automatización
            automation = PlaytomicBrowserAutomation()
            
            try:
                # Iniciar navegador
                await automation.start(headless=False)  # Visible para ver el proceso
                
                # Login
                login_success = await automation.login()
                if not login_success:
                    print("❌ Error en login")
                    return
                
                print("✅ Login exitoso")
                
                # Hacer reserva
                reservation_id = await automation.make_reservation_from_url(url)
                
                if reservation_id:
                    print(f"✅ ¡RESERVA EXITOSA! ID: {reservation_id}")
                else:
                    print("❌ Reserva falló")
                    
            finally:
                await automation.close()
        else:
            print("❌ Reserva cancelada")
    else:
        print("⚠️ Mensaje no válido para reserva automática")
        response = chatbot.generate_response_message(info)
        print(f"💬 Respuesta que se enviaría: {response}")


if __name__ == "__main__":
    print("¿Qué quieres probar?")
    print("1. Solo chatbot (extracción de información)")
    print("2. Integración completa (chatbot + reserva real)")
    print()
    
    opcion = input("Selecciona opción (1/2): ").strip()
    
    if opcion == "1":
        asyncio.run(test_chatbot())
    elif opcion == "2":
        asyncio.run(test_full_integration())
    else:
        print("❌ Opción inválida")

"""
Prueba simple del chatbot AI - sin entrada interactiva
"""
import asyncio
from ai_chatbot import PadelReservationChatbot
import logging
import sys

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True
)

def test_chatbot_simple():
    """Probar el chatbot con mensajes predefinidos"""
    
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
        
        try:
            # Extraer información
            info = chatbot.extract_reservation_info(message)
            print(f"📊 Info extraída: {info}")
            
            # Generar URL
            url = chatbot.generate_reservation_url(info)
            print(f"🔗 URL: {url[:100]}...")  # Mostrar solo parte de la URL
            
            # Generar respuesta
            response = chatbot.generate_response_message(info)
            print(f"💬 Respuesta:")
            print(response)
            
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print()
        print("=" * 50)
        print()

if __name__ == "__main__":
    test_chatbot_simple()

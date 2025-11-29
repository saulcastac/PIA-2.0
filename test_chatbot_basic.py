"""
Prueba basica del chatbot AI - sin emojis
"""
from ai_chatbot import PadelReservationChatbot
import logging
import sys

# Configurar logging simple
logging.basicConfig(level=logging.WARNING)

def test_chatbot_basic():
    """Probar el chatbot con mensajes predefinidos"""
    
    print("PRUEBA DEL CHATBOT AI")
    print("=" * 50)
    print()
    
    # Crear chatbot
    chatbot = PadelReservationChatbot()
    
    # Mensajes de prueba
    test_messages = [
        "Hola, quiero reservar manana a las 10:00 AM",
        "Reservar MONEX para manana 16:00", 
        "Puedo hacer una reserva?",
        "Si, confirmar reserva para manana 11:00",
        "Quiero reservar el 28/11/2025 a las 15:30"
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"MENSAJE {i}: {message}")
        print("-" * 30)
        
        try:
            # Extraer informacion
            info = chatbot.extract_reservation_info(message)
            print(f"Info extraida: {info}")
            
            # Generar URL
            url = chatbot.generate_reservation_url(info)
            print(f"URL generada: {url[:80]}...")
            
            # Generar respuesta
            response = chatbot.generate_response_message(info)
            print(f"Respuesta:")
            print(response[:200] + "..." if len(response) > 200 else response)
            
        except Exception as e:
            print(f"Error: {e}")
        
        print()
        print("=" * 50)
        print()

if __name__ == "__main__":
    test_chatbot_basic()

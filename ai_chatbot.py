"""
Chatbot AI para extraer información de reservas de pádel
Usa OpenAI GPT para procesar mensajes de WhatsApp y extraer datos de reserva
"""
import openai
import json
import re
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
import logging
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class PadelReservationChatbot:
    """
    Chatbot AI para procesar solicitudes de reservas de pádel
    """
    
    def __init__(self):
        # Configurar OpenAI
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        if self.openai_api_key:
            openai.api_key = self.openai_api_key
        
        # Configuración por defecto para MONEX
        self.default_config = {
            "tenant_id": "65a5b336-e05c-4989-a3b8-3374e9ad335f",
            "resource_id": "c5270541-aeec-4640-b67d-346bd8e9d072",  # MONEX
            "cancha": "MONEX",
            "duracion": 60
        }
        
        # Mapeo de canchas (por si en el futuro agregamos más)
        self.court_mapping = {
            "MONEX": "c5270541-aeec-4640-b67d-346bd8e9d072",
            "GOCSA": "da1fda51-61f8-4432-92b9-d93f980ed106",  # Si necesitas agregar más
        }
    
    def extract_reservation_info(self, message: str) -> Dict[str, Any]:
        """
        Extraer información de reserva del mensaje usando AI
        
        Args:
            message: Mensaje del usuario
        
        Returns:
            Dict con información extraída
        """
        try:
            if not self.openai_api_key:
                logger.warning("OpenAI API key no configurada, usando extracción básica")
                return self._extract_basic_info(message)
            
            # Prompt para ChatGPT
            prompt = f"""
Eres un asistente para reservas de pádel. Analiza el siguiente mensaje y extrae la información de reserva.

Mensaje del usuario: "{message}"

Extrae la siguiente información en formato JSON:
- fecha: en formato YYYY-MM-DD (si no se especifica, usa mañana)
- hora: en formato HH:MM (24 horas)
- cancha: nombre de la cancha (por defecto "MONEX")
- duracion: duración en minutos (por defecto 60)
- confirmado: true si el usuario quiere confirmar la reserva, false si solo pregunta

Reglas importantes:
1. Si dice "mañana", usa la fecha de mañana
2. Si dice una hora como "10 AM" o "10:00", conviértela a formato 24h
3. Si no especifica cancha, usa "MONEX"
4. Si no especifica duración, usa 60 minutos
5. Detecta si quiere hacer la reserva o solo preguntar

Responde SOLO con el JSON, sin explicaciones adicionales.

Ejemplo de respuesta:
{{"fecha": "2025-11-28", "hora": "10:00", "cancha": "MONEX", "duracion": 60, "confirmado": true}}
"""

            # Llamada a OpenAI (nueva API)
            from openai import OpenAI
            client = OpenAI(api_key=self.openai_api_key)
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Eres un experto en extraer información de reservas de pádel."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.1
            )
            
            # Extraer respuesta
            ai_response = response.choices[0].message.content.strip()
            logger.info(f"Respuesta AI: {ai_response}")
            
            # Parsear JSON
            try:
                extracted_info = json.loads(ai_response)
                
                # Validar y completar información
                return self._validate_and_complete_info(extracted_info)
                
            except json.JSONDecodeError:
                logger.error(f"Error parseando JSON de AI: {ai_response}")
                return self._extract_basic_info(message)
                
        except Exception as e:
            logger.error(f"Error en extracción AI: {e}")
            return self._extract_basic_info(message)
    
    def _extract_basic_info(self, message: str) -> Dict[str, Any]:
        """
        Extracción básica sin AI (fallback)
        """
        info = {
            "fecha": None,
            "hora": None,
            "cancha": "MONEX",
            "duracion": 60,
            "confirmado": False
        }
        
        message_lower = message.lower()
        
        # Detectar confirmación
        confirm_words = ["reservar", "confirmar", "quiero", "hacer reserva", "sí", "si"]
        info["confirmado"] = any(word in message_lower for word in confirm_words)
        
        # Extraer hora (formato básico)
        time_patterns = [
            r'(\d{1,2}):(\d{2})',  # 10:00
            r'(\d{1,2})\s*(?:am|pm)',  # 10 AM
            r'(\d{1,2})\s*(?:h|hrs|horas)',  # 10h
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, message_lower)
            if match:
                hour = int(match.group(1))
                minute = int(match.group(2)) if len(match.groups()) > 1 else 0
                
                # Convertir AM/PM si es necesario
                if 'pm' in message_lower and hour < 12:
                    hour += 12
                elif 'am' in message_lower and hour == 12:
                    hour = 0
                
                info["hora"] = f"{hour:02d}:{minute:02d}"
                break
        
        # Fecha por defecto (mañana)
        tomorrow = datetime.now() + timedelta(days=1)
        info["fecha"] = tomorrow.strftime("%Y-%m-%d")
        
        return info
    
    def _validate_and_complete_info(self, info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validar y completar información extraída
        """
        # Valores por defecto
        if not info.get("cancha"):
            info["cancha"] = "MONEX"
        
        if not info.get("duracion"):
            info["duracion"] = 60
        
        if not info.get("fecha"):
            tomorrow = datetime.now() + timedelta(days=1)
            info["fecha"] = tomorrow.strftime("%Y-%m-%d")
        
        # Validar formato de hora
        if info.get("hora"):
            try:
                # Validar que sea formato HH:MM válido
                datetime.strptime(info["hora"], "%H:%M")
            except ValueError:
                logger.warning(f"Formato de hora inválido: {info['hora']}")
                info["hora"] = None
        
        return info
    
    def generate_reservation_url(self, info: Dict[str, Any]) -> str:
        """
        Generar URL de reserva basada en la información extraída
        
        Args:
            info: Información de reserva extraída
        
        Returns:
            URL completa para la reserva
        """
        try:
            # Obtener resource_id de la cancha
            cancha = info.get("cancha", "MONEX").upper()
            resource_id = self.court_mapping.get(cancha, self.default_config["resource_id"])
            
            # Formatear fecha y hora para UTC
            fecha_str = info.get("fecha")
            hora_str = info.get("hora")
            
            if not fecha_str or not hora_str:
                raise ValueError("Fecha u hora no especificadas")
            
            # Crear datetime
            fecha_hora = datetime.strptime(f"{fecha_str} {hora_str}", "%Y-%m-%d %H:%M")
            
            # Formatear para URL (UTC)
            start_time = fecha_hora.strftime("%Y-%m-%dT%H:%M:%S.000Z")
            
            # Construir URL
            url = f"https://playtomic.com/api/web-app/payments?type=CUSTOMER_MATCH&tenant_id={self.default_config['tenant_id']}&resource_id={resource_id}&start={start_time}&duration={info.get('duracion', 60)}"
            
            return url
            
        except Exception as e:
            logger.error(f"Error generando URL: {e}")
            # URL por defecto (mañana 10:00)
            tomorrow = datetime.now() + timedelta(days=1)
            default_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
            start_time = default_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")
            
            return f"https://playtomic.com/api/web-app/payments?type=CUSTOMER_MATCH&tenant_id={self.default_config['tenant_id']}&resource_id={self.default_config['resource_id']}&start={start_time}&duration=60"
    
    def generate_response_message(self, info: Dict[str, Any]) -> str:
        """
        Generar mensaje de respuesta para el usuario
        """
        cancha = info.get("cancha", "MONEX")
        fecha = info.get("fecha", "No especificada")
        hora = info.get("hora", "No especificada")
        duracion = info.get("duracion", 60)
        confirmado = info.get("confirmado", False)
        
        if confirmado and fecha != "No especificada" and hora != "No especificada":
            return f"""Perfecto! Procesando tu reserva:

Cancha: {cancha}
Fecha: {fecha}
Hora: {hora}
Duracion: {duracion} minutos

Iniciando proceso de reserva...
Te confirmare en unos momentos si fue exitosa."""
        
        elif confirmado:
            return f"""Necesito mas informacion para tu reserva:

Cancha: {cancha}
Fecha: {fecha if fecha != "No especificada" else "Falta especificar"}
Hora: {hora if hora != "No especificada" else "Falta especificar"}

Por favor, especifica la fecha y hora. Ejemplo:
"Quiero reservar manana a las 10:00 AM" """
        
        else:
            return f"""Informacion detectada:

Cancha: {cancha}
Fecha: {fecha}
Hora: {hora}
Duracion: {duracion} minutos

Quieres confirmar esta reserva? Responde "si" para proceder."""


# Función de conveniencia
def create_chatbot() -> PadelReservationChatbot:
    """Crear instancia del chatbot"""
    return PadelReservationChatbot()


if __name__ == "__main__":
    # Ejemplo de uso
    chatbot = PadelReservationChatbot()
    
    # Ejemplos de mensajes
    test_messages = [
        "Quiero reservar mañana a las 10:00 AM",
        "Reservar MONEX para el 27/11/2025 a las 16:00",
        "¿Puedo hacer una reserva para mañana?",
        "Confirmar reserva 10 AM mañana"
    ]
    
    for msg in test_messages:
        print(f"\n📱 Mensaje: {msg}")
        info = chatbot.extract_reservation_info(msg)
        print(f"📊 Info extraída: {info}")
        url = chatbot.generate_reservation_url(info)
        print(f"🔗 URL: {url}")
        response = chatbot.generate_response_message(info)
        print(f"💬 Respuesta: {response}")
        print("-" * 50)

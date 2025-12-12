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
        
        # Mapeo de canchas disponibles
        self.court_mapping = {
            "MONEX": "c5270541-aeec-4640-b67d-346bd8e9d072",
            "GOCSA": "da1fda51-61f8-4432-92b9-d93f980ed106",
        }
        
        # Lista de canchas disponibles para mostrar al usuario
        # Se puede expandir fácilmente agregando más canchas aquí
        self.available_courts = ["MONEX", "GOCSA", "WOODWARD", "TEDS"]
        
        # Horarios de operación (opcional - puedes configurar restricciones aquí)
        # Formato: {"cancha": {"inicio": "HH:MM", "fin": "HH:MM"}}
        self.court_hours = {
            "MONEX": {"inicio": "06:00", "fin": "23:00"},
            "GOCSA": {"inicio": "06:00", "fin": "23:00"},
            "WOODWARD": {"inicio": "06:00", "fin": "23:00"},
            "TEDS": {"inicio": "06:00", "fin": "23:00"},
        }
    
    def extract_reservation_info(self, message: str, context: Dict = None) -> Dict[str, Any]:
        """
        Extraer información de reserva del mensaje usando AI con contexto
        
        Args:
            message: Mensaje del usuario
            context: Contexto previo de la conversación (nombre, cancha, fecha, hora, duracion)
        
        Returns:
            Dict con información extraída
        """
        if context is None:
            context = {}
        try:
            # Primero verificar si el mensaje es sobre reservas
            if not self._is_reservation_related(message):
                return {
                    "es_reserva": False,
                    "mensaje": "Lo siento, solo puedo ayudarte con reservas de canchas de pádel. ¿Quieres hacer una reserva?"
                }
            
            if not self.openai_api_key:
                logger.warning("OpenAI API key no configurada, usando extracción básica")
                return self._extract_basic_info(message)
            
            # Verificar si pregunta por canchas disponibles o información general
            message_lower = message.lower().strip()
            
            # Detectar preguntas sobre canchas disponibles (más flexible)
            preguntas_canchas = [
                "qué canchas", "cuáles canchas", "canchas disponibles", 
                "canchas tiene", "canchas hay", "qué canchas hay",
                "canchas disponibles", "listar canchas", "mostrar canchas",
                "horarios", "qué horarios", "horarios disponibles",
                "qué canchas tienes", "cuáles canchas tienes",
                "disponible", "disponibles", "disponibilidad"
            ]
            
            # Detectar si es pregunta simple sobre canchas (sin contexto de reserva)
            es_pregunta_simple = any(phrase in message_lower for phrase in preguntas_canchas)
            tiene_palabras_reserva = any(word in message_lower for word in ["reservar", "reserva", "quiero", "necesito", "agendar"])
            
            # Si pregunta por canchas pero NO menciona reservar, es pregunta informativa
            if es_pregunta_simple and not tiene_palabras_reserva:
                return {
                    "es_reserva": False,
                    "pregunta_info": True,
                    "tipo_pregunta": "canchas_disponibles",
                    "mensaje": "info_canchas"
                }
            
            # Construir contexto para el prompt
            context_str = ""
            if context:
                context_parts = []
                if context.get("nombre"):
                    context_parts.append(f"Nombre mencionado anteriormente: {context['nombre']}")
                if context.get("cancha"):
                    context_parts.append(f"Cancha mencionada anteriormente: {context['cancha']}")
                if context.get("fecha"):
                    context_parts.append(f"Fecha mencionada anteriormente: {context['fecha']}")
                if context.get("hora"):
                    context_parts.append(f"Hora mencionada anteriormente: {context['hora']}")
                if context.get("duracion"):
                    context_parts.append(f"Duración mencionada anteriormente: {context['duracion']} minutos")
                
                if context_parts:
                    context_str = "\n\nCONTEXTO DE CONVERSACIÓN PREVIA:\n" + "\n".join(context_parts) + "\n\nSi el usuario no menciona algo nuevo, usa la información del contexto."
            
            # Prompt mejorado para ChatGPT - más amigable y preciso para Google Calendar
            today = datetime.now()
            tomorrow = today + timedelta(days=1)
            tomorrow_str = tomorrow.strftime("%Y-%m-%d")
            
            prompt = f"""
Eres un asistente amigable y conversacional para reservas de canchas de pádel. Eres cálido, profesional y siempre buscas ayudar al usuario de la mejor manera.

Mensaje del usuario: "{message}"
{context_str}

FECHA ACTUAL: {today.strftime("%Y-%m-%d")} ({today.strftime("%A")})
FECHA MAÑANA: {tomorrow_str}

TIPOS DE MENSAJES QUE PUEDES RECIBIR:
1. PREGUNTAS SOBRE CANCHAS DISPONIBLES:
   - "qué canchas tiene disponible [fecha] a las [hora]"
   - "canchas disponibles mañana a las 2pm"
   - "qué canchas hay el martes a las 10:00"
   - "disponible el 15/12 a las 14:00"
   → Responde: {{"es_reserva": false, "pregunta_info": true, "tipo_pregunta": "canchas_disponibles", "fecha": "YYYY-MM-DD", "hora": "HH:MM"}}

2. SOLICITUDES DE CAMBIO DE DURACIÓN:
   - "extender a 90 minutos", "cambiar a 90 minutos", "90 minutos"
   - "quiero 90 minutos", "hazlo de 90 minutos", "extender la sesión a 90"
   - "quiero que dure 90 minutos", "cambiar duración a 90"
   → Responde: {{"es_reserva": true, "cambiar_duracion": true, "duracion": 90, "confirmado": true}}

3. PREGUNTAS GENERALES O SALUDOS:
   - "hola", "buenos días", "qué tal"
   - "cómo funciona", "qué puedes hacer"
   → Responde: {{"es_reserva": false, "mensaje": "saludo"}}

4. SOLICITUDES DE RESERVA:
   - "quiero reservar...", "reservar...", "necesito..."
   → Extrae información y responde con JSON de reserva

IMPORTANTE: 
- Si el mensaje es una PREGUNTA sobre canchas disponibles (sin mencionar "reservar"), responde con: {{"es_reserva": false, "pregunta_info": true, "tipo_pregunta": "canchas_disponibles"}}
- Si el mensaje NO es sobre reservas de pádel, responde con: {{"es_reserva": false}}

🎯 TU OBJETIVO:
Extraer información de reserva de forma precisa y amigable. El formato de salida DEBE ser compatible con Google Calendar API.

📋 CANCHAS DISPONIBLES (reconoce cualquiera de estas variaciones):
- MONEX (también: "monex", "Monex")
- GOCSA (también: "gocsa", "Gocsa")
- WOODWARD (también: "woodward", "Woodward")
- TEDS (también: "teds", "Teds")

EJEMPLOS DE EXTRACCIÓN CORRECTA:
1. "Quiero reservar el martes a las 11:00 AM en GOCSA para Juan"
   → {{"es_reserva": true, "nombre": "Juan", "cancha": "GOCSA", "fecha": "2025-12-03", "hora": "11:00", "duracion": 60, "confirmado": true}}

2. "José 12:30 PM"
   → {{"es_reserva": true, "nombre": "José", "hora": "12:30", "cancha": null, "fecha": "{tomorrow_str}", "duracion": 60, "confirmado": false}}

3. "GOCSA mañana 10:00 para María"
   → {{"es_reserva": true, "nombre": "María", "cancha": "GOCSA", "fecha": "{tomorrow_str}", "hora": "10:00", "duracion": 60, "confirmado": true}}

4. "Quiero reservar MONEX"
   → {{"es_reserva": true, "nombre": null, "cancha": "MONEX", "fecha": "{tomorrow_str}", "hora": null, "duracion": 60, "confirmado": true}}

5. "Sí, confirma"
   → {{"es_reserva": true, "confirmado": true}} (usa contexto previo para el resto)

FORMATO DE SALIDA (JSON estricto):
{{
  "es_reserva": true,
  "nombre": string | null,  // Nombre REAL de la persona, NO palabras comunes
  "cancha": "MONEX" | "GOCSA" | "WOODWARD" | "TEDS" | null,  // EXACTAMENTE en mayúsculas
  "fecha": "YYYY-MM-DD",  // Formato ISO estricto para Google Calendar
  "hora": "HH:MM",  // Formato 24 horas (ej: "14:30" para 2:30 PM)
  "duracion": 60,  // Minutos (default: 60). Si usuario dice "90 minutos", "extender a 90", usa 90
  "cambiar_duracion": boolean,  // true si quiere cambiar duración de reserva existente
  "confirmado": boolean  // true si quiere confirmar/reservar ahora
}}

REGLAS CRÍTICAS DE EXTRACCIÓN:

1. NOMBRE (nombre real de persona):
   ✅ CORRECTO: "para Juan" → "Juan", "María quiere" → "María", "José 12:30" → "José"
   ❌ INCORRECTO: "quiero", "reservar", "para", "necesito", "cancha", nombres de canchas
   - Busca DESPUÉS de "para", "de", "para el/la"
   - Si el mensaje es "Nombre Hora", la primera palabra es el nombre
   - Si no hay nombre claro, usa null

2. CANCHA (EXACTAMENTE en mayúsculas):
   ✅ DEBE SER: "MONEX", "GOCSA", "WOODWARD", "TEDS" (en mayúsculas)
   - Reconoce variaciones pero devuelve en MAYÚSCULAS
   - Si el usuario dice "GOCSA", NO uses "MONEX" por defecto
   - Si no se menciona, usa null (NO inventes)

3. FECHA (formato YYYY-MM-DD para Google Calendar):
   - "mañana" → {tomorrow_str}
   - "hoy" → {today.strftime("%Y-%m-%d")}
   - "martes", "miércoles", etc. → calcula el próximo día de la semana
   - "15/12/2025" o "15-12-2025" → "2025-12-15"
   - Si no se especifica → {tomorrow_str} (mañana)

4. HORA (formato HH:MM en 24 horas):
   - "10 AM" → "10:00"
   - "2 PM" → "14:00"
   - "12:30 PM" → "12:30"
   - "12:00 AM" (medianoche) → "00:00"
   - "12:00 PM" (mediodía) → "12:00"
   - Si no se especifica → null

5. CONFIRMADO:
   - true: "sí", "confirmar", "hazlo", "adelante", "reservar", "quiero reservar"
   - false: "pregunta", "disponible", "qué horarios", solo consulta

6. CONTEXTO:
   - Si hay contexto previo y el usuario no menciona algo nuevo, usa el contexto
   - Si el usuario dice "sí" o "confirmar", usa toda la info del contexto

IMPORTANTE PARA GOOGLE CALENDAR:
- La fecha DEBE estar en formato YYYY-MM-DD (ej: "2025-12-01")
- La hora DEBE estar en formato HH:MM en 24 horas (ej: "14:30")
- La cancha DEBE estar en mayúsculas exactas (MONEX, GOCSA, WOODWARD, TEDS)
- Si falta información crítica, marca confirmado: false

Responde SOLO con el JSON válido, sin texto adicional, sin explicaciones, sin markdown.
"""

            # Llamada a OpenAI (nueva API)
            from openai import OpenAI
            client = OpenAI(api_key=self.openai_api_key)
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",  # Usar modelo más reciente y eficiente
                messages=[
                    {
                        "role": "system", 
                        "content": """Eres un asistente amigable y profesional para reservas de canchas de pádel. 
                        Tu objetivo es entender las solicitudes de los usuarios de forma natural y conversacional, 
                        pero siempre devolver información precisa en formato JSON compatible con Google Calendar API.
                        
                        Características:
                        - Eres cálido y amigable, pero profesional
                        - Entiendes lenguaje natural y coloquial
                        - Puedes responder preguntas simples sobre canchas disponibles
                        - Puedes mantener conversaciones naturales
                        - Extraes información precisa: nombres reales, fechas, horas, canchas
                        - El formato de salida DEBE ser JSON válido compatible con Google Calendar
                        - Las canchas disponibles son: MONEX, GOCSA, WOODWARD, TEDS (siempre en mayúsculas)
                        - Fechas en formato YYYY-MM-DD, horas en formato HH:MM (24h)
                        - Solo extraes nombres propios reales, nunca palabras comunes como "quiero", "reservar", etc.
                        
                        TIPOS DE RESPUESTAS:
                        - Si preguntan por canchas disponibles (sin mencionar "reservar"): {"es_reserva": false, "pregunta_info": true, "tipo_pregunta": "canchas_disponibles"}
                        - Si es saludo o pregunta general: {"es_reserva": false, "mensaje": "saludo"}
                        - Si es solicitud de reserva: extrae la información en formato JSON de reserva"""
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=400,  # Aumentado para respuestas más completas
                temperature=0.1,  # Más bajo para mayor precisión
                response_format={"type": "json_object"}  # Forzar formato JSON
            )
            
            # Extraer respuesta
            ai_response = response.choices[0].message.content.strip()
            logger.info(f"Respuesta AI: {ai_response}")
            
            # Parsear JSON (ahora viene directamente como JSON por response_format)
            try:
                # Limpiar respuesta si tiene markdown o texto adicional
                ai_response_clean = ai_response.strip()
                # Remover bloques de código markdown si existen
                if ai_response_clean.startswith("```json"):
                    ai_response_clean = ai_response_clean[7:]  # Remover ```json
                if ai_response_clean.startswith("```"):
                    ai_response_clean = ai_response_clean[3:]  # Remover ```
                if ai_response_clean.endswith("```"):
                    ai_response_clean = ai_response_clean[:-3]  # Remover ```
                ai_response_clean = ai_response_clean.strip()
                
                extracted_info = json.loads(ai_response_clean)
                
                # Si no es sobre reservas, retornar directamente
                if not extracted_info.get("es_reserva", True):
                    return extracted_info
                
                # Procesar fecha relativa (días de la semana)
                if extracted_info.get("fecha"):
                    fecha_str = extracted_info["fecha"]
                    # Si la fecha parece ser un día de la semana, convertirla
                    if any(dia in fecha_str.lower() for dia in ["lunes", "martes", "miércoles", "miercoles", "jueves", "viernes", "sábado", "sabado", "domingo"]):
                        extracted_info["fecha"] = self._parse_weekday_to_date(fecha_str)
                
                # Combinar con contexto si falta información
                if context:
                    if not extracted_info.get("nombre") and context.get("nombre"):
                        extracted_info["nombre"] = context["nombre"]
                    if not extracted_info.get("cancha") and context.get("cancha"):
                        extracted_info["cancha"] = context["cancha"]
                    if not extracted_info.get("fecha") and context.get("fecha"):
                        extracted_info["fecha"] = context["fecha"]
                    if not extracted_info.get("hora") and context.get("hora"):
                        extracted_info["hora"] = context["hora"]
                    if not extracted_info.get("duracion") and context.get("duracion"):
                        extracted_info["duracion"] = context["duracion"]
                
                # Validar y completar información
                return self._validate_and_complete_info(extracted_info)
                
            except json.JSONDecodeError:
                logger.error(f"Error parseando JSON de AI: {ai_response}")
                return self._extract_basic_info(message)
                
        except Exception as e:
            logger.error(f"Error en extracción AI: {e}")
            return self._extract_basic_info(message)
    
    def get_available_courts_info(self) -> str:
        """
        Obtener información de canchas disponibles para mostrar al usuario
        
        Returns:
            String con información de canchas disponibles
        """
        info = "🏓 *Canchas disponibles:*\n\n"
        for i, cancha in enumerate(self.available_courts, 1):
            hours = self.court_hours.get(cancha, {})
            inicio = hours.get("inicio", "06:00")
            fin = hours.get("fin", "23:00")
            info += f"{i}. *{cancha}*\n"
            info += f"   Horarios: {inicio} - {fin}\n\n"
        return info
    
    def _is_reservation_related(self, message: str) -> bool:
        """
        Verificar si el mensaje está relacionado con reservas de pádel
        Incluye preguntas sobre canchas, disponibilidad, etc.
        """
        message_lower = message.lower()
        
        # Palabras clave de reservas (más amplio para incluir preguntas)
        reservation_keywords = [
            "reservar", "reserva", "cancha", "pádel", "padel", "agendar", 
            "cita", "disponible", "disponibles", "disponibilidad", "horario", "horarios", 
            "hora", "fecha", "mañana", "hoy", "cancelar", "cancelación", 
            "cancelar reserva", "eliminar reserva", "canchas", "qué canchas", 
            "cuáles canchas", "canchas disponibles", "canchas tiene", "canchas hay",
            "qué canchas hay", "listar canchas", "mostrar canchas", "qué canchas tienes",
            "cuáles canchas tienes", "monex", "gocsa", "woodward", "teds"
        ]
        
        # Patrones que indican información de reserva (nombre + hora, etc.)
        # Ejemplo: "José 12:30 PM" o "Juan 10:00"
        time_pattern = r'\d{1,2}:\d{2}|(\d{1,2})\s*(am|pm|AM|PM)'
        has_time = bool(re.search(time_pattern, message))
        
        # Si tiene hora y un nombre (palabra que no es común), probablemente es información de reserva
        if has_time and len(message.split()) >= 2:
            # Verificar si hay palabras que parecen nombres (no palabras comunes)
            palabras = message.split()
            palabras_comunes = ["quiero", "reservar", "para", "necesito", "puedo", "hacer", "reserva", "cancha"]
            tiene_nombre_potencial = any(palabra.lower() not in palabras_comunes and len(palabra) > 2 for palabra in palabras)
            if tiene_nombre_potencial:
                return True
        
        # Palabras que indican que NO es sobre reservas
        non_reservation_keywords = [
            "clima", "tiempo", "temperatura", "lluvia", "noticias",
            "chiste", "joke", "historia", "cuéntame", "qué eres",
            "quien eres", "ayuda general", "información general"
        ]
        
        # Si contiene palabras de no-reserva, no es sobre reservas
        if any(keyword in message_lower for keyword in non_reservation_keywords):
            # Pero si también menciona reservas, sí es sobre reservas
            if not any(keyword in message_lower for keyword in reservation_keywords):
                return False
        
        # Si contiene palabras de reserva, es sobre reservas
        return any(keyword in message_lower for keyword in reservation_keywords)
    
    def is_cancellation_request(self, message: str) -> bool:
        """
        Verificar si el mensaje es una solicitud de cancelación
        """
        message_lower = message.lower()
        cancellation_keywords = [
            "cancelar", "cancelación", "cancelar reserva", "eliminar reserva",
            "borrar reserva", "anular", "anular reserva"
        ]
        return any(keyword in message_lower for keyword in cancellation_keywords)
    
    def _extract_basic_info(self, message: str) -> Dict[str, Any]:
        """
        Extracción básica sin AI (fallback)
        """
        info = {
            "es_reserva": True,
            "nombre": None,
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
        
        # Intentar extraer nombre (patrones básicos)
        name_patterns = [
            r'(?:soy|me llamo|nombre es|es)\s+([A-Z][a-z]+)',
            r'([A-Z][a-z]+)\s+(?:quiere|quiero|reservar)',
        ]
        for pattern in name_patterns:
            match = re.search(pattern, message)
            if match:
                info["nombre"] = match.group(1)
                break
        
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
        # Asegurar que es_reserva está en True
        info["es_reserva"] = True
        
        # Validar cancha - debe ser una de las disponibles
        cancha = info.get("cancha", "").upper().strip()
        cancha_original = cancha
        
        if cancha not in self.available_courts:
            # Intentar encontrar coincidencia parcial (más flexible)
            cancha_lower = cancha.lower()
            for court in self.available_courts:
                court_lower = court.lower()
                # Coincidencia exacta (case insensitive)
                if cancha_lower == court_lower:
                    cancha = court
                    break
                # Coincidencia parcial
                elif court_lower in cancha_lower or cancha_lower in court_lower:
                    cancha = court
                    break
            
            if cancha not in self.available_courts:
                # Si aún no coincide, usar MONEX por defecto PERO loguear advertencia
                logger.warning(f"⚠️ Cancha '{cancha_original}' no reconocida, usando MONEX por defecto")
                cancha = "MONEX"
        
        info["cancha"] = cancha
        logger.info(f"✅ Cancha validada: {cancha} (original: {cancha_original})")
        
        # Valores por defecto
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
        
        # Validar nombre - no debe ser una palabra común de reserva
        nombre = info.get("nombre", "").strip() if info.get("nombre") else None
        if nombre:
            palabras_comunes = [
                "quiero", "reservar", "para", "necesito", "puedo", "hacer", "reserva", 
                "cancha", "mañana", "hoy", "el", "la", "los", "las", "un", "una",
                "monex", "gocsa", "woodward", "teds", "en", "a", "de", "del"
            ]
            nombre_lower = nombre.lower().strip()
            
            # Verificar si es una palabra común
            if nombre_lower in palabras_comunes:
                logger.warning(f"Nombre '{nombre}' es una palabra común, descartando")
                info["nombre"] = None
            # Verificar si es muy corto
            elif len(nombre) < 2:
                logger.warning(f"Nombre '{nombre}' es muy corto, descartando")
                info["nombre"] = None
            # Verificar si parece ser una cancha
            elif nombre_lower in [c.lower() for c in self.available_courts]:
                logger.warning(f"Nombre '{nombre}' parece ser una cancha, descartando")
                info["nombre"] = None
            else:
                info["nombre"] = nombre
                logger.info(f"✅ Nombre validado: {nombre}")
        
        # Nombre puede ser None si no se especifica
        if "nombre" not in info:
            info["nombre"] = None
        
        return info
    
    def _parse_weekday_to_date(self, weekday_str: str) -> str:
        """
        Convertir día de la semana a fecha real
        
        Args:
            weekday_str: String con día de la semana (ej: "martes", "el martes")
        
        Returns:
            Fecha en formato YYYY-MM-DD
        """
        from datetime import datetime, timedelta
        
        weekday_str = weekday_str.lower().strip()
        
        # Mapeo de días de la semana
        dias_semana = {
            "lunes": 0,
            "martes": 1,
            "miércoles": 2, "miercoles": 2,
            "jueves": 3,
            "viernes": 4,
            "sábado": 5, "sabado": 5,
            "domingo": 6
        }
        
        # Extraer el día de la semana
        target_weekday = None
        for dia, num in dias_semana.items():
            if dia in weekday_str:
                target_weekday = num
                break
        
        if target_weekday is None:
            # Si no se encuentra, usar mañana
            tomorrow = datetime.now() + timedelta(days=1)
            return tomorrow.strftime("%Y-%m-%d")
        
        # Calcular el próximo día de la semana
        today = datetime.now()
        current_weekday = today.weekday()
        
        # Calcular días hasta el próximo día de la semana
        days_ahead = target_weekday - current_weekday
        if days_ahead <= 0:  # Si ya pasó esta semana, usar el de la próxima semana
            days_ahead += 7
        
        target_date = today + timedelta(days=days_ahead)
        return target_date.strftime("%Y-%m-%d")
    
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
        Generar mensaje de respuesta amigable y conversacional para el usuario
        """
        # Si pregunta por información de canchas disponibles
        if info.get("pregunta_info") and info.get("tipo_pregunta") == "canchas_disponibles":
            mensaje = "🏓 *Canchas disponibles:*\n\n"
            for i, cancha in enumerate(self.available_courts, 1):
                hours = self.court_hours.get(cancha, {})
                inicio = hours.get("inicio", "06:00")
                fin = hours.get("fin", "23:00")
                mensaje += f"{i}. *{cancha}*\n"
                mensaje += f"   ⏰ Horarios: {inicio} - {fin}\n\n"
            mensaje += "💡 *Para reservar, puedes decirme por ejemplo:*\n"
            mensaje += "\"Quiero reservar GOCSA mañana a las 10:00 AM para Juan\"\n\n"
            mensaje += "O también puedes decirme:\n"
            mensaje += "\"Reservar MONEX el martes a las 2 PM\""
            return mensaje
        
        # Si es saludo o pregunta general
        if info.get("mensaje") == "saludo" or (not info.get("es_reserva", True) and not info.get("pregunta_info")):
            return """👋 ¡Hola! Soy tu asistente para reservas de canchas de pádel.

Puedo ayudarte con:
🏓 Ver canchas disponibles
📅 Hacer reservas
❓ Responder tus preguntas

*Canchas disponibles:*
• MONEX
• GOCSA
• WOODWARD
• TEDS

💡 *¿Qué te gustaría hacer?*
Puedes preguntarme:
• "Qué canchas tiene disponible"
• "Quiero reservar GOCSA mañana a las 10:00 AM"
• O simplemente dime lo que necesitas 😊"""
        
        # Si no es sobre reservas, retornar mensaje amigable
        if not info.get("es_reserva", True):
            return info.get("mensaje", "👋 Hola! Puedo ayudarte con reservas de canchas de pádel. ¿Te gustaría hacer una reserva o ver las canchas disponibles?")
        
        nombre = info.get("nombre")
        cancha = info.get("cancha")
        fecha = info.get("fecha")
        hora = info.get("hora")
        duracion = info.get("duracion", 60)
        confirmado = info.get("confirmado", False)
        
        # Verificar qué información falta
        falta_info = []
        if not nombre:
            falta_info.append("nombre")
        if not fecha:
            falta_info.append("fecha")
        if not hora:
            falta_info.append("hora")
        if not cancha:
            falta_info.append("cancha")
        
        # Si está confirmado y tiene toda la info, no mostrar mensaje aquí (se procesa directamente)
        if confirmado and not falta_info:
            return "✅ ¡Perfecto! Estoy procesando tu reserva..."
        
        elif confirmado:
            # Falta información pero quiere confirmar - mensaje amigable
            mensaje = "😊 ¡Casi estamos listos! Solo me falta un poco más de información:\n\n"
            if "nombre" in falta_info:
                mensaje += "• 👤 Tu nombre\n"
            if "cancha" in falta_info:
                mensaje += "• 🏓 La cancha (MONEX, GOCSA, WOODWARD o TEDS)\n"
            if "fecha" in falta_info:
                mensaje += "• 📅 La fecha\n"
            if "hora" in falta_info:
                mensaje += "• ⏰ La hora\n"
            
            mensaje += "\n💡 *Puedes decirme todo junto, por ejemplo:*\n"
            mensaje += "\"Mañana a las 10:00 AM en GOCSA para Juan\""
            return mensaje
        
        else:
            # Mensaje conversacional mostrando lo que tenemos
            partes = []
            
            if nombre:
                partes.append(f"👤 *Nombre:* {nombre}")
            if cancha:
                partes.append(f"🏓 *Cancha:* {cancha}")
            if fecha:
                # Formatear fecha de forma más amigable
                try:
                    fecha_obj = datetime.strptime(fecha, "%Y-%m-%d")
                    # Obtener día de la semana
                    dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
                    dia_semana = dias_semana[fecha_obj.weekday()]
                    fecha_formateada = fecha_obj.strftime(f"%d/%m/%Y ({dia_semana})")
                    partes.append(f"📅 *Fecha:* {fecha_formateada}")
                except:
                    partes.append(f"📅 *Fecha:* {fecha}")
            if hora:
                # Formatear hora de forma más amigable
                try:
                    hora_obj = datetime.strptime(hora, "%H:%M")
                    hora_formateada = hora_obj.strftime("%I:%M %p").lower()
                    partes.append(f"⏰ *Hora:* {hora_formateada} ({hora})")
                except:
                    partes.append(f"⏰ *Hora:* {hora}")
            if duracion and duracion != 60:
                partes.append(f"⏱️ *Duración:* {duracion} minutos")
            
            if partes:
                mensaje = "✅ *Perfecto, entendí:*\n\n" + "\n".join(partes)
                
                if falta_info:
                    mensaje += "\n\n📝 *Me falta:*\n"
                    if "nombre" in falta_info:
                        mensaje += "• 👤 Tu nombre\n"
                    if "cancha" in falta_info:
                        mensaje += "• 🏓 La cancha\n"
                    if "fecha" in falta_info:
                        mensaje += "• 📅 La fecha\n"
                    if "hora" in falta_info:
                        mensaje += "• ⏰ La hora\n"
                    
                    mensaje += "\n💬 *Dime lo que falta y procedo con la reserva.*"
                else:
                    mensaje += "\n\n✅ *¿Confirmo esta reserva?* Responde *'sí'* o *'confirmar'*."
            else:
                # Mensaje de bienvenida más amigable
                mensaje = "👋 *¡Hola!* Te ayudo a reservar una cancha de pádel.\n\n"
                mensaje += "📋 *Necesito:*\n"
                mensaje += "• 👤 Tu nombre\n"
                mensaje += "• 🏓 La cancha (MONEX, GOCSA, WOODWARD o TEDS)\n"
                mensaje += "• 📅 Fecha y hora\n\n"
                mensaje += "💡 *Puedes decírmelo todo junto, por ejemplo:*\n"
                mensaje += "\"Quiero reservar mañana a las 10:00 AM en GOCSA para Juan\"\n\n"
                mensaje += "O también puedes decírmelo por partes, yo te iré guiando 😊"
            
            return mensaje


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

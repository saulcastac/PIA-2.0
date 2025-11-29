"""
Bot de WhatsApp para gestionar reservas de pádel
Usa whatsapp-web.py para conectar con WhatsApp Web
"""
import asyncio
from datetime import datetime
from typing import Optional, Dict
import json
import logging
from database import SessionLocal, User, Reservation, ConversationState
from playtomic_automation import get_playtomic_instance
from config import TIMEZONE, WHATSAPP_SESSION_PATH
import pytz
# Intentar importar whatsapp-web.py, si no está disponible usar Selenium
try:
    from whatsapp_web import WhatsApp
    USE_WHATSAPP_WEB = True
except ImportError:
    USE_WHATSAPP_WEB = False
    logger.warning("whatsapp-web.py no disponible, usando implementación alternativa")
from pathlib import Path
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PadelReservationBot:
    """Bot de WhatsApp para reservas de pádel"""
    
    def __init__(self):
        self.db = SessionLocal()
        self.timezone = pytz.timezone(TIMEZONE)
        if USE_WHATSAPP_WEB:
            self.whatsapp = WhatsApp()
        else:
            # Si whatsapp-web.py no está disponible, usar implementación alternativa
            logger.warning("whatsapp-web.py no disponible. Usa whatsapp_bot_selenium.py o instala whatsapp-web.py")
            raise ImportError("whatsapp-web.py no está instalado. Instala con: pip install whatsapp-web.py==0.1.0")
        
    async def start(self):
        """Iniciar el bot de WhatsApp"""
        logger.info("Iniciando bot de WhatsApp...")
        
        # Crear directorio de sesión si no existe
        WHATSAPP_SESSION_PATH.mkdir(parents=True, exist_ok=True)
        
        # Inicializar WhatsApp
        try:
            await self.whatsapp.start()
            logger.info("Bot iniciado. Esperando mensajes...")
            
            # Configurar callback de mensajes
            @self.whatsapp.on_message
            async def on_message(message):
                await self.handle_message(message)
                
        except Exception as e:
            logger.error(f"Error iniciando bot: {e}")
            raise
    
    async def handle_message(self, message):
        """Manejar mensajes entrantes"""
        try:
            # Extraer información del mensaje
            phone = message.from_user.phone if hasattr(message, 'from_user') else message.from_
            text = message.text.lower().strip() if message.text else ""
            
            logger.info(f"Mensaje recibido de {phone}: {text}")
            
            # Obtener o crear usuario
            user = self.db.query(User).filter(User.phone_number == phone).first()
            if not user:
                name = message.from_user.name if hasattr(message, 'from_user') else "Usuario"
                user = User(phone_number=phone, name=name)
                self.db.add(user)
                self.db.commit()
            
            # Obtener estado de conversación
            conv_state = self.db.query(ConversationState).filter(
                ConversationState.phone_number == phone
            ).first()
            
            if not conv_state:
                conv_state = ConversationState(phone_number=phone, state="idle")
                self.db.add(conv_state)
                self.db.commit()
            
            # Procesar mensaje según estado
            await self.process_message(user, conv_state, text)
            
        except Exception as e:
            logger.error(f"Error manejando mensaje: {e}")
            try:
                phone = message.from_user.phone if hasattr(message, 'from_user') else message.from_
                await self.send_message(phone, "❌ Ocurrió un error. Por favor intenta nuevamente.")
            except:
                pass
    
    async def process_message(self, user: User, conv_state: ConversationState, text: str):
        """Procesar mensaje según el estado de la conversación"""
        state = conv_state.state
        
        if text in ["hola", "hi", "inicio", "start", "/start"]:
            await self.send_welcome_message(user.phone_number)
            conv_state.state = "waiting_intent"
            self.db.commit()
            
        elif text in ["reservar", "reserva", "agendar", "cita"]:
            await self.send_message(
                user.phone_number,
                "📅 Perfecto, vamos a reservar una cancha.\n\n¿Para qué fecha? (ejemplo: 15/12/2024)"
            )
            conv_state.state = "waiting_date"
            self.db.commit()
            
        elif state == "waiting_date":
            date = await self.parse_date(text)
            if date:
                context = json.loads(conv_state.context or "{}")
                context["date"] = date.isoformat()
                conv_state.context = json.dumps(context)
                conv_state.state = "waiting_time"
                self.db.commit()
                
                await self.send_message(
                    user.phone_number,
                    f"✅ Fecha: {date.strftime('%d/%m/%Y')}\n\n¿A qué hora? (ejemplo: 18:00)"
                )
            else:
                await self.send_message(
                    user.phone_number,
                    "❌ No entendí la fecha. Por favor usa el formato DD/MM/YYYY (ejemplo: 15/12/2024)"
                )
                
        elif state == "waiting_time":
            time_slot = await self.parse_time(text)
            if time_slot:
                context = json.loads(conv_state.context or "{}")
                context["time"] = time_slot
                conv_state.context = json.dumps(context)
                self.db.commit()
                
                # Buscar canchas disponibles
                date_str = context.get("date")
                date = datetime.fromisoformat(date_str)
                
                await self.send_message(
                    user.phone_number,
                    "🔍 Buscando canchas disponibles..."
                )
                
                playtomic = await get_playtomic_instance()
                available_courts = await playtomic.get_available_courts(date, time_slot)
                
                if available_courts:
                    # Guardar canchas disponibles en contexto
                    context["available_courts"] = available_courts
                    conv_state.context = json.dumps(context)
                    
                    # Mostrar opciones
                    message = "✅ Canchas disponibles:\n\n"
                    for i, court in enumerate(available_courts, 1):
                        message += f"{i}. {court['name']} - {court['time']}\n"
                    message += "\n¿Cuál quieres? Responde con el número."
                    
                    await self.send_message(user.phone_number, message)
                    conv_state.state = "waiting_court_selection"
                    self.db.commit()
                else:
                    await self.send_message(
                        user.phone_number,
                        "❌ No hay canchas disponibles para ese horario. ¿Quieres buscar otro horario? (responde 'sí' o 'no')"
                    )
                    conv_state.state = "waiting_retry"
                    self.db.commit()
            else:
                await self.send_message(
                    user.phone_number,
                    "❌ No entendí la hora. Por favor usa el formato HH:MM (ejemplo: 18:00)"
                )
                
        elif state == "waiting_retry":
            if text in ["si", "sí", "yes"]:
                await self.send_message(
                    user.phone_number,
                    "📅 ¿Para qué fecha? (ejemplo: 15/12/2024)"
                )
                conv_state.state = "waiting_date"
                self.db.commit()
            else:
                await self.send_welcome_message(user.phone_number)
                conv_state.state = "idle"
                self.db.commit()
                
        elif state == "waiting_court_selection":
            try:
                court_index = int(text) - 1
                context = json.loads(conv_state.context or "{}")
                available_courts = context.get("available_courts", [])
                
                if 0 <= court_index < len(available_courts):
                    selected_court = available_courts[court_index]
                    context["selected_court"] = selected_court
                    conv_state.context = json.dumps(context)
                    conv_state.state = "waiting_confirmation"
                    self.db.commit()
                    
                    await self.send_confirmation_message(user, context)
                else:
                    await self.send_message(
                        user.phone_number,
                        "❌ Opción inválida. Por favor elige un número de la lista."
                    )
            except ValueError:
                await self.send_message(
                    user.phone_number,
                    "❌ Por favor responde con un número."
                )
                
        elif state == "waiting_confirmation":
            if text in ["si", "sí", "confirmar", "confirmo", "ok"]:
                context = json.loads(conv_state.context or "{}")
                await self.confirm_reservation(user, context)
                conv_state.state = "idle"
                conv_state.context = None
                self.db.commit()
            elif text in ["no", "cancelar", "cancel"]:
                await self.send_message(
                    user.phone_number,
                    "❌ Reserva cancelada. ¿Quieres intentar con otra fecha? (responde 'reservar')"
                )
                conv_state.state = "idle"
                conv_state.context = None
                self.db.commit()
            else:
                await self.send_message(
                    user.phone_number,
                    "❓ Por favor responde 'sí' para confirmar o 'no' para cancelar."
                )
        else:
            await self.send_welcome_message(user.phone_number)
            conv_state.state = "waiting_intent"
            self.db.commit()
    
    async def send_welcome_message(self, phone: str):
        """Enviar mensaje de bienvenida"""
        message = """🏓 ¡Hola! Soy tu asistente de reservas de pádel.

Puedo ayudarte a:
📅 Reservar una cancha
📋 Ver tus reservas
❌ Cancelar una reserva

¿Qué quieres hacer? Responde con 'reservar' para comenzar."""
        
        await self.send_message(phone, message)
    
    async def send_confirmation_message(self, user: User, context: Dict):
        """Enviar mensaje de confirmación antes de reservar"""
        date_str = context.get("date")
        time = context.get("time")
        selected_court = context.get("selected_court", {})
        court_name = selected_court.get("name", "Cancha")
        
        date = datetime.fromisoformat(date_str)
        
        message = f"""📋 Confirma tu reserva:

🏓 Cancha: {court_name}
📅 Fecha: {date.strftime('%d/%m/%Y')}
⏰ Hora: {time}

¿Confirmas esta reserva? Responde 'sí' para confirmar o 'no' para cancelar."""
        
        await self.send_message(user.phone_number, message)
    
    async def confirm_reservation(self, user: User, context: Dict):
        """Confirmar y crear la reserva"""
        try:
            date_str = context.get("date")
            time = context.get("time")
            selected_court = context.get("selected_court", {})
            court_name = selected_court.get("name", "Cancha")
            
            date = datetime.fromisoformat(date_str)
            date_time = datetime.combine(date.date(), datetime.strptime(time, "%H:%M").time())
            date_time = self.timezone.localize(date_time)
            
            # Verificar si requiere prepago
            if user.requires_prepayment:
                await self.send_message(
                    user.phone_number,
                    "⚠️ Tu cuenta requiere prepago debido a reservas anteriores sin asistencia.\n"
                    "Por favor realiza el pago antes de confirmar."
                )
                return
            
            # Realizar reserva en Playtomic
            await self.send_message(user.phone_number, "🔄 Confirmando reserva en Playtomic...")
            
            playtomic = await get_playtomic_instance()
            reservation_id = await playtomic.make_reservation(court_name, date, time)
            
            if reservation_id:
                # Crear reserva en BD
                reservation = Reservation(
                    user_id=user.id,
                    playtomic_reservation_id=reservation_id,
                    court_name=court_name,
                    date=date_time,
                    status="confirmed",
                    confirmed=True
                )
                self.db.add(reservation)
                self.db.commit()
                
                await self.send_message(
                    user.phone_number,
                    f"""✅ ¡Reserva confirmada!

🏓 Cancha: {court_name}
📅 Fecha: {date.strftime('%d/%m/%Y')}
⏰ Hora: {time}
🆔 ID: {reservation_id}

Te enviaremos recordatorios antes del partido. ¡Nos vemos!"""
                )
            else:
                await self.send_message(
                    user.phone_number,
                    "❌ No se pudo completar la reserva. Por favor intenta nuevamente o contacta soporte."
                )
                
        except Exception as e:
            logger.error(f"Error confirmando reserva: {e}")
            await self.send_message(
                user.phone_number,
                "❌ Ocurrió un error al confirmar la reserva. Por favor intenta nuevamente."
            )
    
    async def parse_date(self, text: str) -> Optional[datetime]:
        """Parsear fecha del texto"""
        try:
            # Intentar formato DD/MM/YYYY
            date = datetime.strptime(text, "%d/%m/%Y")
            return date
        except:
            try:
                # Intentar formato DD-MM-YYYY
                date = datetime.strptime(text, "%d-%m-%Y")
                return date
            except:
                return None
    
    async def parse_time(self, text: str) -> Optional[str]:
        """Parsear hora del texto"""
        try:
            # Intentar formato HH:MM
            time = datetime.strptime(text, "%H:%M")
            return time.strftime("%H:%M")
        except:
            try:
                # Intentar formato HHMM
                if len(text) == 4 and text.isdigit():
                    return f"{text[:2]}:{text[2:]}"
            except:
                return None
        return None
    
    async def send_message(self, phone: str, message: str):
        """Enviar mensaje de WhatsApp"""
        try:
            await self.whatsapp.send_message(phone, message)
        except Exception as e:
            logger.error(f"Error enviando mensaje a {phone}: {e}")


# Singleton del bot
_bot_instance: Optional[PadelReservationBot] = None


async def get_bot_instance() -> PadelReservationBot:
    """Obtener instancia única del bot"""
    global _bot_instance
    if _bot_instance is None:
        _bot_instance = PadelReservationBot()
        await _bot_instance.start()
    return _bot_instance

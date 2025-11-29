"""
Bot de WhatsApp con AI para gestionar reservas de pádel
Integra chatbot AI + automatización de navegador + Twilio
"""
import asyncio
from datetime import datetime
from typing import Optional, Dict
import json
import logging
import os
from database import SessionLocal, User, Reservation, ConversationState
from playtomic_browser_automation import PlaytomicBrowserAutomation
from ai_chatbot import PadelReservationChatbot
from config import TIMEZONE
import pytz
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from flask import Flask, request
import threading
import sys
from dotenv import load_dotenv

load_dotenv()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True
)

logger = logging.getLogger(__name__)


class PadelReservationBotAI:
    """
    Bot de WhatsApp con AI para reservas de pádel
    """
    
    def __init__(self):
        # Configuración Twilio
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.whatsapp_number = os.getenv('TWILIO_WHATSAPP_NUMBER')
        
        if self.account_sid and self.auth_token:
            self.client = Client(self.account_sid, self.auth_token)
        else:
            logger.warning("Credenciales de Twilio no configuradas")
            self.client = None
        
        # Chatbot AI
        self.chatbot = PadelReservationChatbot()
        
        # Automatización de navegador
        self.automation = None
        
        # Flask app para webhook
        self.app = Flask(__name__)
        self.setup_routes()
    
    def setup_routes(self):
        """Configurar rutas de Flask"""
        
        @self.app.route('/webhook', methods=['POST'])
        def webhook():
            """Webhook para recibir mensajes de WhatsApp"""
            try:
                # Obtener datos del mensaje
                from_number = request.form.get('From')
                message_body = request.form.get('Body')
                
                logger.info(f"📱 Mensaje recibido de {from_number}: {message_body}")
                
                # Procesar mensaje
                response_text = asyncio.run(self.process_message(from_number, message_body))
                
                # Crear respuesta
                resp = MessagingResponse()
                resp.message(response_text)
                
                return str(resp)
                
            except Exception as e:
                logger.error(f"Error en webhook: {e}")
                resp = MessagingResponse()
                resp.message("❌ Error procesando mensaje. Intenta de nuevo.")
                return str(resp)
        
        @self.app.route('/health', methods=['GET'])
        def health():
            """Endpoint de salud"""
            return {"status": "ok", "service": "padel-bot-ai"}
    
    async def process_message(self, from_number: str, message: str) -> str:
        """
        Procesar mensaje recibido
        
        Args:
            from_number: Número de teléfono del remitente
            message: Contenido del mensaje
        
        Returns:
            Respuesta para enviar al usuario
        """
        try:
            # Extraer información usando AI
            logger.info(f"🤖 Procesando mensaje con AI: {message}")
            reservation_info = self.chatbot.extract_reservation_info(message)
            
            logger.info(f"📊 Información extraída: {reservation_info}")
            
            # Generar respuesta inicial
            response_message = self.chatbot.generate_response_message(reservation_info)
            
            # Si el usuario quiere confirmar y tenemos toda la info
            if reservation_info.get("confirmado") and reservation_info.get("fecha") and reservation_info.get("hora"):
                
                # Enviar mensaje de confirmación inmediatamente
                await self.send_message(from_number, response_message)
                
                # Procesar reserva en segundo plano
                asyncio.create_task(self.process_reservation_async(from_number, reservation_info))
                
                return "🔄 Procesando reserva..."
            
            else:
                return response_message
                
        except Exception as e:
            logger.error(f"Error procesando mensaje: {e}")
            return "❌ Error procesando tu mensaje. Por favor intenta de nuevo."
    
    async def process_reservation_async(self, from_number: str, reservation_info: Dict):
        """
        Procesar reserva de forma asíncrona
        """
        try:
            logger.info(f"🎯 Iniciando proceso de reserva para {from_number}")
            
            # Generar URL de reserva
            reservation_url = self.chatbot.generate_reservation_url(reservation_info)
            logger.info(f"🔗 URL generada: {reservation_url}")
            
            # Inicializar automatización si no existe
            if not self.automation:
                self.automation = PlaytomicBrowserAutomation()
                await self.automation.start(headless=False)  # Modo headless para producción
                
                # Hacer login
                login_success = await self.automation.login()
                if not login_success:
                    await self.send_message(from_number, "❌ Error: No se pudo iniciar sesión en Playtomic. Intenta más tarde.")
                    return
            
            # Hacer la reserva
            reservation_id = await self.automation.make_reservation_from_url(reservation_url)
            
            # Enviar resultado
            if reservation_id:
                success_message = f"""✅ ¡RESERVA EXITOSA!

🆔 ID: {reservation_id}
🏓 Cancha: {reservation_info.get('cancha', 'MONEX')}
📅 Fecha: {reservation_info.get('fecha')}
⏰ Hora: {reservation_info.get('hora')}
⏱️ Duración: {reservation_info.get('duracion', 60)} min

¡Nos vemos en la cancha! 🎾"""
                
                await self.send_message(from_number, success_message)
                
                # Guardar en base de datos
                await self.save_reservation_to_db(from_number, reservation_info, reservation_id)
                
            else:
                error_message = f"""❌ No se pudo completar la reserva

Posibles causas:
• La cancha está ocupada
• Horario no disponible
• Problemas técnicos

🔄 Intenta con otro horario o contacta soporte."""
                
                await self.send_message(from_number, error_message)
                
        except Exception as e:
            logger.error(f"Error en proceso de reserva: {e}")
            await self.send_message(from_number, "❌ Error técnico procesando reserva. Intenta más tarde.")
    
    async def send_message(self, to_number: str, message: str):
        """
        Enviar mensaje por WhatsApp
        """
        try:
            if self.client and self.whatsapp_number:
                message_obj = self.client.messages.create(
                    body=message,
                    from_=self.whatsapp_number,
                    to=to_number
                )
                logger.info(f"📤 Mensaje enviado a {to_number}: {message[:50]}...")
            else:
                logger.warning(f"📤 [SIMULADO] Mensaje a {to_number}: {message}")
                
        except Exception as e:
            logger.error(f"Error enviando mensaje: {e}")
    
    async def save_reservation_to_db(self, phone_number: str, reservation_info: Dict, reservation_id: str):
        """
        Guardar reserva en base de datos
        """
        try:
            db = SessionLocal()
            
            # Buscar o crear usuario
            user = db.query(User).filter(User.phone_number == phone_number).first()
            if not user:
                user = User(
                    phone_number=phone_number,
                    name=f"Usuario {phone_number[-4:]}",  # Nombre temporal
                    is_active=True
                )
                db.add(user)
                db.commit()
                db.refresh(user)
            
            # Crear reserva
            reservation_datetime = datetime.strptime(
                f"{reservation_info['fecha']} {reservation_info['hora']}", 
                "%Y-%m-%d %H:%M"
            )
            
            reservation = Reservation(
                user_id=user.id,
                court_name=reservation_info.get('cancha', 'MONEX'),
                date=reservation_datetime.date(),
                time=reservation_datetime.time(),
                duration_minutes=reservation_info.get('duracion', 60),
                status='confirmed',
                reservation_id=reservation_id,
                created_at=datetime.now()
            )
            
            db.add(reservation)
            db.commit()
            
            logger.info(f"💾 Reserva guardada en BD: {reservation_id}")
            
        except Exception as e:
            logger.error(f"Error guardando reserva en BD: {e}")
        finally:
            db.close()
    
    async def start(self):
        """Iniciar el bot"""
        logger.info("🤖 Iniciando bot de WhatsApp con AI...")
        
        # Verificar configuración
        if not self.client:
            logger.warning("⚠️ Twilio no configurado - modo simulación")
        
        # Inicializar automatización
        try:
            self.automation = PlaytomicBrowserAutomation()
            await self.automation.start(headless=False)
            
            # Hacer login inicial
            login_success = await self.automation.login()
            if login_success:
                logger.info("✅ Login inicial en Playtomic exitoso")
            else:
                logger.warning("⚠️ Login inicial falló - se intentará en cada reserva")
                
        except Exception as e:
            logger.error(f"Error inicializando automatización: {e}")
        
        logger.info("✅ Bot iniciado correctamente")
    
    def run_flask(self, host='0.0.0.0', port=5000):
        """Ejecutar servidor Flask"""
        logger.info(f"🌐 Iniciando servidor Flask en {host}:{port}")
        self.app.run(host=host, port=port, debug=False)
    
    async def close(self):
        """Cerrar recursos"""
        if self.automation:
            await self.automation.close()
        logger.info("🔒 Bot cerrado")


# Función principal para ejecutar el bot
async def main():
    """Función principal"""
    bot = PadelReservationBotAI()
    
    try:
        # Iniciar bot
        await bot.start()
        
        # Ejecutar Flask en hilo separado
        flask_thread = threading.Thread(
            target=bot.run_flask,
            kwargs={'host': '0.0.0.0', 'port': 5000}
        )
        flask_thread.daemon = True
        flask_thread.start()
        
        logger.info("🚀 Sistema completo iniciado")
        logger.info("📱 Webhook disponible en: http://localhost:5000/webhook")
        
        # Mantener el programa corriendo
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("👋 Cerrando bot...")
        await bot.close()


if __name__ == "__main__":
    asyncio.run(main())

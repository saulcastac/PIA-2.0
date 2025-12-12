"""
Bot de WhatsApp para gestionar reservas de pádel
Implementación usando Twilio WhatsApp API
"""
import asyncio
from datetime import datetime
from typing import Optional, Dict
import json
import logging
import os
from database import SessionLocal, User, Reservation, ConversationState
from google_calendar_client import get_google_calendar_instance
from ai_chatbot import PadelReservationChatbot
from config import TIMEZONE
import pytz
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from flask import Flask, request
import threading
import re

import sys

# Configurar logging para que se muestre en consola
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True
)

# Configurar encoding para Windows
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

logger = logging.getLogger(__name__)

# Archivo de cache de disponibilidad
AVAILABILITY_CACHE_FILE = 'availability_cache.json'
MAX_CACHE_AGE_HOURS = 24  # Cache válido por 24 horas (aumentado para pruebas)


def load_availability_cache():
    """
    Cargar disponibilidad desde cache JSON
    
    Returns:
        Diccionario con disponibilidad si el cache es válido, None si no
    """
    try:
        if not os.path.exists(AVAILABILITY_CACHE_FILE):
            logger.debug(f"Cache file {AVAILABILITY_CACHE_FILE} no existe")
            return None
        
        with open(AVAILABILITY_CACHE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Verificar que el cache no sea muy viejo
        cache_time = datetime.fromisoformat(data['timestamp'])
        age_hours = (datetime.now() - cache_time).total_seconds() / 3600
        
        if age_hours > MAX_CACHE_AGE_HOURS:
            logger.info(f"⚠️  Cache expirado (edad: {age_hours:.1f} horas)")
            return None
        
        logger.info(f"✅ Cache válido (edad: {age_hours:.1f} horas)")
        return data.get('availability', {})
        
    except Exception as e:
        logger.warning(f"⚠️  Error cargando cache: {e}")
        return None


class PadelReservationBotTwilio:
    """Bot de WhatsApp usando Twilio para reservas de pádel"""
    
    def __init__(self):
        self.db = SessionLocal()
        self.timezone = pytz.timezone(TIMEZONE)
        self.twilio_client = None
        self.twilio_whatsapp_number = None
        self.app = Flask(__name__)
        self.chatbot = PadelReservationChatbot()  # Inicializar chatbot AI
        self._setup_flask_routes()
        
    def _setup_flask_routes(self):
        """Configurar rutas de Flask para webhooks"""
        def handle_webhook():
            """Función común para manejar webhooks"""
            try:
                # Logging detallado de la request (también con print para asegurar visibilidad)
                print("=" * 60)
                print("WEBHOOK RECIBIDO DE TWILIO")
                print("=" * 60)
                
                logger.info("=" * 60)
                logger.info("📨 WEBHOOK RECIBIDO DE TWILIO")
                logger.info(f"📋 Método: {request.method}")
                logger.info(f"📋 URL: {request.url}")
                logger.info(f"📋 Headers: {dict(request.headers)}")
                logger.info(f"📋 Form data: {dict(request.form)}")
                logger.info(f"📋 Values: {dict(request.values)}")
                logger.info("=" * 60)
                
                # Obtener datos del mensaje
                incoming_message = request.values.get('Body', '').strip()
                from_number = request.values.get('From', '').strip()
                
                # Si no hay Body, intentar obtener de otros campos
                if not incoming_message:
                    incoming_message = request.form.get('Body', '').strip()
                if not incoming_message:
                    incoming_message = request.json.get('Body', '') if request.is_json else ''
                
                # Si no hay From, intentar obtener de otros campos
                if not from_number:
                    from_number = request.form.get('From', '').strip()
                if not from_number:
                    from_number = request.json.get('From', '') if request.is_json else ''
                
                logger.info(f"📝 Mensaje extraído: '{incoming_message}'")
                logger.info(f"📱 Número extraído: '{from_number}'")
                
                # Print directo para debugging
                print(f"Mensaje extraído: '{incoming_message}'")
                print(f"Número extraído: '{from_number}'")
                
                if not incoming_message:
                    logger.warning("⚠️  No se encontró el campo 'Body' en la request")
                    logger.warning("⚠️  Esto puede indicar que Twilio no está enviando el mensaje correctamente")
                    # Responder a Twilio de todas formas
                    resp = MessagingResponse()
                    return str(resp)
                
                if not from_number:
                    logger.warning("⚠️  No se encontró el campo 'From' en la request")
                    resp = MessagingResponse()
                    return str(resp)
                
                # Limpiar número de teléfono (remover whatsapp: prefix)
                phone = from_number.replace('whatsapp:', '')
                
                logger.info(f"✅ Mensaje recibido de {phone}: '{incoming_message}'")
                logger.info("🔄 Iniciando procesamiento del mensaje...")
                
                # Print directo para debugging
                print(f"Mensaje recibido de {phone}: '{incoming_message}'")
                print("Iniciando procesamiento del mensaje...")
                
                # Procesar mensaje de forma asíncrona en un thread separado
                # para no bloquear la respuesta a Twilio
                def process_async():
                    try:
                        print("Creando nuevo event loop para procesar mensaje...")
                        logger.info("🔀 Creando nuevo event loop para procesar mensaje...")
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            print(f"Ejecutando handle_message para {phone}...")
                            logger.info(f"▶️  Ejecutando handle_message para {phone}...")
                            loop.run_until_complete(self.handle_message(phone, incoming_message))
                            print("handle_message completado exitosamente")
                            logger.info("✅ handle_message completado exitosamente")
                        except Exception as e:
                            print(f"ERROR en handle_message: {e}")
                            logger.error(f"❌ Error en handle_message: {e}")
                            import traceback
                            traceback.print_exc()
                            logger.error(traceback.format_exc())
                        finally:
                            loop.close()
                            print("Event loop cerrado")
                            logger.info("🔚 Event loop cerrado")
                    except Exception as e:
                        print(f"ERROR en process_async: {e}")
                        logger.error(f"❌ Error en process_async: {e}")
                        import traceback
                        traceback.print_exc()
                        logger.error(traceback.format_exc())
                
                thread = threading.Thread(target=process_async, daemon=True)
                thread.start()
                logger.info("✅ Thread de procesamiento iniciado")
                
                # Responder inmediatamente a Twilio
                resp = MessagingResponse()
                logger.info("📤 Respondiendo a Twilio con 200 OK")
                return str(resp)
                
            except Exception as e:
                logger.error(f"❌ Error en webhook: {e}")
                import traceback
                logger.error(traceback.format_exc())
                resp = MessagingResponse()
                return str(resp)
        
        # Ruta en /webhook (recomendada) - Para recibir mensajes entrantes
        @self.app.route('/webhook', methods=['POST'])
        def webhook():
            print("📨 RUTA /webhook LLAMADA")
            logger.info("📨 Ruta /webhook llamada")
            return handle_webhook()
        
        # Ruta en raíz / (para compatibilidad si Twilio está configurado sin /webhook)
        @self.app.route('/', methods=['POST'])
        def root_webhook():
            print("📨 RUTA / (raíz) LLAMADA")
            logger.info("📨 Ruta / (raíz) llamada")
            return handle_webhook()
        
        # Ruta GET para verificar que el servidor está funcionando
        @self.app.route('/', methods=['GET'])
        def root_get():
            print("✅ GET / recibido - Servidor funcionando")
            return "Bot de WhatsApp funcionando. Usa POST para enviar mensajes.", 200
        
        # Ruta para status callback (opcional) - Para recibir actualizaciones del estado de mensajes
        @self.app.route('/status', methods=['POST', 'GET'])
        def status_callback():
            """Endpoint para recibir actualizaciones del estado de mensajes enviados"""
            try:
                print("=" * 60)
                print("STATUS CALLBACK RECIBIDO")
                print("=" * 60)
                
                # Obtener datos del status
                message_sid = request.values.get('MessageSid', '')
                message_status = request.values.get('MessageStatus', '')
                error_code = request.values.get('ErrorCode', '')
                
                print(f"MessageSid: {message_sid}")
                print(f"MessageStatus: {message_status}")
                if error_code:
                    print(f"ErrorCode: {error_code}")
                
                logger.info(f"📊 Status callback - MessageSid: {message_sid}, Status: {message_status}")
                
                # Aquí puedes agregar lógica para manejar los estados:
                # - queued: Mensaje en cola
                # - sent: Mensaje enviado
                # - delivered: Mensaje entregado
                # - read: Mensaje leído
                # - failed: Mensaje fallido
                
                if message_status == 'failed':
                    logger.error(f"❌ Mensaje fallido - MessageSid: {message_sid}, ErrorCode: {error_code}")
                elif message_status == 'delivered':
                    logger.info(f"✅ Mensaje entregado - MessageSid: {message_sid}")
                elif message_status == 'read':
                    logger.info(f"👁️  Mensaje leído - MessageSid: {message_sid}")
                
                return '', 200
            except Exception as e:
                logger.error(f"Error en status callback: {e}")
                return '', 200
        
        @self.app.route('/health', methods=['GET'])
        def health():
            """Endpoint de salud"""
            return {'status': 'ok'}, 200
    
    async def start(self):
        """Inicializar el bot de WhatsApp con Twilio"""
        from config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER
        
        logger.info("Iniciando bot de WhatsApp con Twilio...")
        
        # Inicializar cliente de Twilio
        self.twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        self.twilio_whatsapp_number = TWILIO_WHATSAPP_NUMBER
        
        # Iniciar servidor Flask en un thread separado
        def run_flask():
            try:
                print("=" * 80)
                print("INICIANDO SERVIDOR FLASK")
                print("Host: 0.0.0.0")
                print("Puerto: 5000")
                print("Rutas disponibles:")
                print("  - POST /webhook (para recibir mensajes de Twilio)")
                print("  - POST / (alternativa)")
                print("  - POST /status (para status callbacks)")
                print("  - GET /health (para verificar que está funcionando)")
                print("=" * 80)
                logger.info("=" * 80)
                logger.info("INICIANDO SERVIDOR FLASK")
                logger.info("Host: 0.0.0.0")
                logger.info("Puerto: 5000")
                logger.info("=" * 80)
                
                # Usar threaded=True para manejar múltiples requests
                self.app.run(
                    host='0.0.0.0', 
                    port=5000, 
                    debug=False, 
                    use_reloader=False,
                    threaded=True
                )
            except Exception as e:
                logger.error(f"❌ Error iniciando servidor Flask: {e}")
                import traceback
                logger.error(traceback.format_exc())
                print(f"❌ ERROR: No se pudo iniciar el servidor Flask: {e}")
        
        # NO usar daemon=True para que el thread mantenga el servidor vivo
        flask_thread = threading.Thread(target=run_flask, daemon=False)
        flask_thread.start()
        
        # Esperar un momento para que Flask inicie y verificar que esté corriendo
        import time
        time.sleep(3)
        
        # Verificar que el servidor esté corriendo
        try:
            import requests
            response = requests.get('http://localhost:5000/health', timeout=2)
            if response.status_code == 200:
                logger.info("✅ Servidor Flask verificado y corriendo correctamente")
                print("✅ Servidor Flask verificado y corriendo correctamente")
            else:
                logger.warning(f"⚠️  Servidor Flask respondió con código: {response.status_code}")
        except Exception as e:
            logger.warning(f"⚠️  No se pudo verificar el servidor Flask: {e}")
            print(f"⚠️  Advertencia: No se pudo verificar el servidor Flask: {e}")
            print("   El servidor debería estar corriendo, pero no se pudo verificar.")
        
        print("=" * 80)
        print("BOT INICIADO")
        print("Esperando mensajes en /webhook...")
        print("Configura el webhook de Twilio a: http://tu-ngrok-url/webhook")
        print("=" * 80)
        logger.info("=" * 80)
        logger.info("Bot iniciado. Esperando mensajes en /webhook...")
        logger.info("Configura el webhook de Twilio a: http://tu-ngrok-url/webhook")
        logger.info("=" * 80)
    
    async def handle_message(self, phone: str, text: str):
        """Manejar mensajes entrantes"""
        try:
            logger.info("=" * 60)
            logger.info(f"💬 HANDLE_MESSAGE INICIADO")
            logger.info(f"📱 Teléfono: {phone}")
            logger.info(f"📝 Texto: '{text}'")
            logger.info("=" * 60)
            
            # Normalizar número de teléfono
            phone = self.normalize_phone_number(phone)
            logger.info(f"📱 Teléfono normalizado: {phone}")
            
            logger.info(f"✅ Procesando mensaje de {phone}: '{text}'")
            
            # Obtener o crear usuario
            user = self.db.query(User).filter(User.phone_number == phone).first()
            if not user:
                user = User(phone_number=phone, name="Usuario")
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
            await self.process_message(user, conv_state, text.lower().strip())
            
        except Exception as e:
            logger.error(f"Error manejando mensaje: {e}")
            import traceback
            logger.error(traceback.format_exc())
            try:
                # Limpiar el mensaje de error (remover caracteres ANSI y caracteres especiales)
                error_msg = str(e)
                # Remover códigos ANSI (colores de terminal)
                import re
                ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
                error_msg = ansi_escape.sub('', error_msg)
                # Limitar longitud y remover caracteres problemáticos
                error_msg = error_msg[:150].replace('\n', ' ').replace('\r', '')
                await self.send_message(phone, f"❌ Ocurrió un error. Por favor intenta nuevamente.")
            except:
                pass
    
    async def process_message(self, user: User, conv_state: ConversationState, text: str):
        """Procesar mensaje según el estado de la conversación"""
        state = conv_state.state
        
        print("=" * 80)
        print(f"PROCESANDO MENSAJE")
        print(f"Estado actual: {state}")
        print(f"Texto recibido: '{text}'")
        print(f"Usuario: {user.phone_number}")
        print("=" * 80)
        
        logger.info("=" * 80)
        logger.info(f"PROCESANDO MENSAJE - Estado: {state}, Texto: '{text}'")
        logger.info(f"Usuario: {user.phone_number}")
        logger.info("=" * 80)
        
        # PRIMERO: Intentar procesar con AI para preguntas naturales
        # Solo si el estado es "idle" o "waiting_intent" (conversación libre)
        if state in ["idle", "waiting_intent", None]:
            try:
                # Obtener contexto previo si existe
                context = {}
                if conv_state.context:
                    try:
                        context = json.loads(conv_state.context)
                    except:
                        context = {}
                
                # Procesar con chatbot AI
                logger.info("🤖 Procesando con chatbot AI...")
                reservation_info = self.chatbot.extract_reservation_info(text, context)
                
                logger.info(f"📊 Información extraída por AI: {reservation_info}")
                
                # Si pregunta por canchas disponibles
                if reservation_info.get("pregunta_info") and reservation_info.get("tipo_pregunta") == "canchas_disponibles":
                    response_message = self.chatbot.generate_response_message(reservation_info)
                    await self.send_message(user.phone_number, response_message)
                    return
                
                # Si es saludo o pregunta general
                if reservation_info.get("mensaje") == "saludo" or (not reservation_info.get("es_reserva", True) and not reservation_info.get("pregunta_info")):
                    response_message = self.chatbot.generate_response_message(reservation_info)
                    await self.send_message(user.phone_number, response_message)
                    # Cambiar estado a waiting_intent para continuar conversación
                    conv_state.state = "waiting_intent"
                    self.db.commit()
                    return
                
                # Si es una reserva con información completa y confirmada
                if reservation_info.get("es_reserva") and reservation_info.get("confirmado"):
                    if reservation_info.get("cancha") and reservation_info.get("fecha") and reservation_info.get("hora"):
                        # Tiene toda la info, procesar reserva directamente
                        await self.process_ai_reservation(user, reservation_info)
                        return
                
                # Si es reserva pero falta info, mostrar lo que tenemos y pedir lo que falta
                if reservation_info.get("es_reserva"):
                    response_message = self.chatbot.generate_response_message(reservation_info)
                    await self.send_message(user.phone_number, response_message)
                    
                    # Guardar contexto para continuar la conversación
                    context.update({
                        "nombre": reservation_info.get("nombre"),
                        "cancha": reservation_info.get("cancha"),
                        "fecha": reservation_info.get("fecha"),
                        "hora": reservation_info.get("hora"),
                        "duracion": reservation_info.get("duracion", 60)
                    })
                    conv_state.context = json.dumps(context)
                    conv_state.state = "waiting_intent"  # Mantener en conversación libre
                    self.db.commit()
                    return
                    
            except Exception as e:
                logger.error(f"Error procesando con AI: {e}")
                # Continuar con el flujo normal si falla AI
        
        if text in ["hola", "hi", "inicio", "start", "/start"]:
            # Enviar mensaje de bienvenida
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
            print(f"ESTADO: waiting_date - Parseando fecha: '{text}'")
            logger.info(f"ESTADO: waiting_date - Parseando fecha: '{text}'")
            
            date = await self.parse_date(text)
            print(f"Fecha parseada: {date}")
            logger.info(f"Fecha parseada: {date}")
            
            if date:
                print("✅ Fecha parseada correctamente")
                logger.info("✅ Fecha parseada correctamente")
                
                context = json.loads(conv_state.context or "{}")
                context["date"] = date.isoformat()
                
                date_str = date.strftime('%Y-%m-%d')
                
                print(f"Fecha guardada en contexto: {date.strftime('%d/%m/%Y')}")
                logger.info(f"Fecha guardada en contexto: {date.strftime('%d/%m/%Y')}")
                
                print("Enviando mensaje de confirmación...")
                await self.send_message(
                    user.phone_number,
                    f"✅ Fecha: {date.strftime('%d/%m/%Y')}\n\n🔍 Buscando canchas disponibles para esta fecha..."
                )
                print("✅ Mensaje enviado")
                
                print("=" * 80)
                print("BUSCANDO CANCHAS DISPONIBLES")
                print("=" * 80)
                
                # Intentar cargar del cache JSON primero
                available_courts = []
                cache = load_availability_cache()
                
                print(f"🔍 DEBUG: date_str buscado: '{date_str}'")
                print(f"🔍 DEBUG: cache cargado: {cache is not None}")
                if cache:
                    print(f"🔍 DEBUG: keys en cache: {list(cache.keys())}")
                    print(f"🔍 DEBUG: ¿Existe {date_str} en cache? {date_str in cache}")
                logger.info(f"🔍 DEBUG: date_str buscado: '{date_str}'")
                logger.info(f"🔍 DEBUG: cache cargado: {cache is not None}")
                if cache:
                    logger.info(f"🔍 DEBUG: keys en cache: {list(cache.keys())}")
                    logger.info(f"🔍 DEBUG: ¿Existe {date_str} en cache? {date_str in cache}")
                
                if cache and date_str in cache:
                    print("✅ Usando cache de disponibilidad para esta fecha")
                    logger.info(f"✅ Usando cache de disponibilidad para {date_str}")
                    cache_data = cache[date_str]
                    
                    # Validar y filtrar datos del cache
                    if isinstance(cache_data, list):
                        # Filtrar entradas inválidas (como "Playtomic Logo")
                        available_courts = [
                            court for court in cache_data 
                            if isinstance(court, dict) and 
                            court.get('name') and 
                            court.get('name') not in ['Playtomic Logo', 'Logo', ''] and
                            len(court.get('name', '')) > 3
                        ]
                        print(f"Canchas encontradas en cache: {len(cache_data)} (válidas: {len(available_courts)})")
                        logger.info(f"Canchas en cache: {len(cache_data)} totales, {len(available_courts)} válidas")
                    else:
                        logger.warning(f"⚠️  Formato de cache inválido para {date_str}: {type(cache_data)}")
                        available_courts = []
                else:
                    print("⚠️  Fecha no encontrada en cache. Solo usamos cache para pruebas.")
                    logger.info(f"⚠️  Fecha {date_str} no encontrada en cache. Usando solo cache.")
                    
                    # NO hacer scraping, solo usar cache
                    await self.send_message(
                        user.phone_number,
                        f"❌ *No hay disponibilidad en cache para esta fecha*\n\n"
                        f"📅 Fecha: {date.strftime('%d/%m/%Y')}\n\n"
                        f"💡 Por favor ejecuta el scraper primero o intenta con otra fecha que esté en el cache.\n"
                        f"Responde con *'reservar'* para intentar con otra fecha."
                    )
                    conv_state.state = "idle"
                    self.db.commit()
                    return
                
                # Procesar canchas encontradas (ya sea del cache o de búsqueda nueva)
                if available_courts:
                    print("PASO 3: Procesando canchas encontradas...")
                    logger.info("PASO 3: Procesando canchas encontradas...")
                    
                    # Validar formato de canchas
                    valid_courts = []
                    for court in available_courts:
                        if isinstance(court, dict) and court.get('name'):
                            # Filtrar nombres inválidos
                            court_name = court.get('name', '').strip()
                            if court_name and court_name not in ['Playtomic Logo', 'Logo', ''] and len(court_name) > 3:
                                valid_courts.append(court)
                            else:
                                logger.debug(f"Filtrando cancha inválida: {court_name}")
                        else:
                            logger.warning(f"Cancha con formato inválido: {court}")
                    
                    available_courts = valid_courts
                    logger.info(f"Canchas válidas después de filtrar: {len(available_courts)}")
                    
                    if not available_courts:
                        await self.send_message(
                            user.phone_number,
                            f"❌ *No se encontraron canchas válidas*\n\n"
                            f"📅 Fecha: {date.strftime('%d/%m/%Y')}\n\n"
                            f"💡 Por favor intenta nuevamente o busca otra fecha."
                        )
                        conv_state.state = "idle"
                        self.db.commit()
                        return
                    
                    # Agrupar canchas por horario
                    courts_by_time = {}
                    for court in available_courts:
                        time = court.get('time', 'Sin horario')
                        if time not in courts_by_time:
                            courts_by_time[time] = []
                        courts_by_time[time].append(court.get('name', 'Cancha'))
                    
                    print(f"Canchas agrupadas por horario: {len(courts_by_time)} horarios diferentes")
                    logger.info(f"Canchas agrupadas por horario: {len(courts_by_time)} horarios diferentes")
                    
                    # Guardar canchas disponibles en contexto
                    context["available_courts"] = available_courts
                    context["courts_by_time"] = courts_by_time
                    conv_state.context = json.dumps(context)
                    self.db.commit()
                    print("✅ Contexto guardado en base de datos")
                    
                    # Mostrar horarios disponibles
                    print("PASO 4: Preparando mensaje con horarios disponibles...")
                    
                    # Contar total de canchas disponibles
                    total_courts = len(available_courts)
                    
                    message = f"✅ *Disponibilidad de canchas para {date.strftime('%d/%m/%Y')}*\n\n"
                    message += f"📊 Total de opciones disponibles: {total_courts}\n\n"
                    
                    # Mostrar horarios ordenados
                    sorted_times = sorted([t for t in courts_by_time.keys() if t != 'Disponible' and ':' in str(t)])
                    
                    print(f"Horarios ordenados: {len(sorted_times)} horarios")
                    
                    if sorted_times:
                        message += "⏰ *Horarios disponibles:*\n"
                        message += "─" * 30 + "\n"
                        for time in sorted_times[:20]:  # Mostrar máximo 20 horarios
                            courts = courts_by_time[time]
                            message += f"\n🕐 *{time}* ({len(courts)} cancha{'s' if len(courts) > 1 else ''}):\n"
                            for court_name in courts[:5]:  # Máximo 5 canchas por horario
                                message += f"   • {court_name}\n"
                            if len(courts) > 5:
                                message += f"   ... y {len(courts) - 5} más\n"
                    else:
                        # Si no hay horarios específicos, mostrar todas las canchas
                        message += "📋 *Canchas disponibles:*\n"
                        message += "─" * 30 + "\n"
                        for i, court in enumerate(available_courts[:20], 1):
                            message += f"{i}. {court.get('name', 'Cancha')} - {court.get('time', 'Disponible')}\n"
                    
                    message += "\n" + "─" * 30 + "\n"
                    message += "💡 *Responde con el horario que prefieres*\n"
                    message += "Ejemplo: *18:00*"
                    
                    print("PASO 5: Enviando mensaje con horarios disponibles...")
                    print(f"Mensaje a enviar (primeros 200 caracteres): {message[:200]}...")
                    await self.send_message(user.phone_number, message)
                    print("✅ Mensaje enviado")
                    
                    conv_state.state = "waiting_time_selection"
                    self.db.commit()
                    print(f"✅ Estado cambiado a: waiting_time_selection")
                    logger.info("✅ Estado cambiado a: waiting_time_selection")
                else:
                    await self.send_message(
                        user.phone_number,
                        f"❌ *No hay canchas disponibles*\n\n"
                        f"📅 Fecha: {date.strftime('%d/%m/%Y')}\n\n"
                        f"💡 ¿Quieres buscar otra fecha?\n"
                        f"Responde con *'reservar'* para comenzar de nuevo."
                    )
                    conv_state.state = "idle"
                    self.db.commit()
            else:
                await self.send_message(
                    user.phone_number,
                    "❌ No entendí la fecha. Por favor usa el formato DD/MM/YYYY (ejemplo: 15/12/2024)"
                )
                
        elif state == "waiting_time_selection":
            # El usuario puede responder con un horario o un número de cancha
            time_slot = await self.parse_time(text)
            
            if time_slot:
                # Usuario seleccionó un horario
                print(f"Horario seleccionado: {time_slot}")
                context = json.loads(conv_state.context or "{}")
                context["time"] = time_slot
                courts_by_time = context.get("courts_by_time", {})
                
                # Filtrar canchas para ese horario específico
                available_courts = []
                if time_slot in courts_by_time:
                    for court_name in courts_by_time[time_slot]:
                        available_courts.append({
                            'name': court_name,
                            'time': time_slot,
                            'date': context.get("date")
                        })
                
                if available_courts:
                    context["available_courts"] = available_courts
                    context["time"] = time_slot
                    conv_state.context = json.dumps(context)
                    
                    # Mostrar canchas para ese horario
                    message = f"✅ *Disponibilidad a las {time_slot}*\n\n"
                    message += f"📊 Total de canchas disponibles: {len(available_courts)}\n\n"
                    message += "─" * 30 + "\n"
                    message += "🏓 *Canchas disponibles:*\n\n"
                    for i, court in enumerate(available_courts, 1):
                        message += f"{i}. {court['name']}\n"
                    message += "\n" + "─" * 30 + "\n"
                    message += "💡 *¿Cuál quieres? Responde con el número.*"
                    
                    await self.send_message(user.phone_number, message)
                    conv_state.state = "waiting_court_selection"
                    self.db.commit()
                else:
                    await self.send_message(
                        user.phone_number,
                        f"❌ *No hay canchas disponibles*\n\n"
                        f"⏰ Horario: {time_slot}\n\n"
                        f"💡 Por favor elige otro horario de la lista anterior."
                    )
            else:
                # Intentar interpretar como número de cancha
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
                            "❌ Opción inválida. Por favor elige un horario (ejemplo: 18:00) o un número de la lista."
                        )
                except ValueError:
                    await self.send_message(
                        user.phone_number,
                        "❌ Por favor responde con un horario (ejemplo: 18:00) o el número de la cancha."
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
    
    async def process_ai_reservation(self, user: User, reservation_info: Dict):
        """Procesar reserva directamente desde información del chatbot AI"""
        try:
            court_name = reservation_info.get("cancha")
            fecha_str = reservation_info.get("fecha")
            hora = reservation_info.get("hora")
            nombre = reservation_info.get("nombre")
            duracion = reservation_info.get("duracion", 60)
            
            if not court_name or not fecha_str or not hora:
                logger.error("Información incompleta para reserva")
                return
            
            # Parsear fecha
            date = datetime.strptime(fecha_str, "%Y-%m-%d")
            date_time = datetime.combine(date.date(), datetime.strptime(hora, "%H:%M").time())
            date_time = self.timezone.localize(date_time)
            
            # Verificar si requiere prepago
            if user.requires_prepayment:
                await self.send_message(
                    user.phone_number,
                    "⚠️ Tu cuenta requiere prepago debido a reservas anteriores sin asistencia.\n"
                    "Por favor realiza el pago antes de confirmar."
                )
                return
            
            # Realizar reserva en Google Calendar
            await self.send_message(user.phone_number, "🔄 Confirmando reserva en Google Calendar...")
            
            google_calendar = await get_google_calendar_instance()
            event_result = google_calendar.create_event(
                court_name=court_name,
                date=date,
                time_slot=hora,
                duration_minutes=duracion,
                name=nombre if nombre else (user.name if user.name else None)
            )
            
            if event_result and event_result.get('id'):
                # Crear reserva en BD
                reservation = Reservation(
                    user_id=user.id,
                    google_calendar_event_id=event_result.get('id'),
                    google_calendar_link=event_result.get('htmlLink'),
                    court_name=court_name,
                    date=date_time,
                    status="confirmed",
                    confirmed=True,
                    name=nombre if nombre else None
                )
                self.db.add(reservation)
                self.db.commit()
                
                calendar_link = event_result.get('htmlLink', '')
                message = f"""✅ ¡Reserva confirmada!

🏓 Cancha: {court_name}
📅 Fecha: {date.strftime('%d/%m/%Y')}
⏰ Hora: {hora}
📆 Evento creado en Google Calendar

¡Nos vemos!"""
                
                if calendar_link:
                    message += f"\n\n🔗 Ver en calendario: {calendar_link}"
                
                await self.send_message(user.phone_number, message)
            else:
                await self.send_message(
                    user.phone_number,
                    "❌ No se pudo completar la reserva. Por favor intenta más tarde o contacta soporte."
                )
                
        except Exception as e:
            logger.error(f"Error procesando reserva AI: {e}")
            await self.send_message(
                user.phone_number,
                "❌ Ocurrió un error al confirmar la reserva. Por favor intenta nuevamente."
            )
    
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
            
            # Realizar reserva en Google Calendar
            await self.send_message(user.phone_number, "🔄 Confirmando reserva en Google Calendar...")
            
            google_calendar = await get_google_calendar_instance()
            event_result = google_calendar.create_event(
                court_name=court_name,
                date=date,
                time_slot=time,
                duration_minutes=60,
                name=user.name if user.name else None
            )
            
            if event_result and event_result.get('id'):
                # Crear reserva en BD
                reservation = Reservation(
                    user_id=user.id,
                    google_calendar_event_id=event_result.get('id'),
                    google_calendar_link=event_result.get('htmlLink'),
                    court_name=court_name,
                    date=date_time,
                    status="confirmed",
                    confirmed=True
                )
                self.db.add(reservation)
                self.db.commit()
                
                calendar_link = event_result.get('htmlLink', '')
                message = f"""✅ ¡Reserva confirmada!

🏓 Cancha: {court_name}
📅 Fecha: {date.strftime('%d/%m/%Y')}
⏰ Hora: {time}
📆 Evento creado en Google Calendar

¡Nos vemos!"""
                
                if calendar_link:
                    message += f"\n\n🔗 Ver en calendario: {calendar_link}"
                
                await self.send_message(user.phone_number, message)
            else:
                await self.send_message(
                    user.phone_number,
                    "❌ No se pudo completar la reserva. Por favor intenta más tarde o contacta soporte."
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
    
    def normalize_phone_number(self, phone: str) -> str:
        """Normalizar número de teléfono a formato E.164"""
        # Remover caracteres no numéricos excepto +
        phone = re.sub(r'[^\d+]', '', phone)
        
        # Si no empieza con +, agregar código de país (Argentina por defecto: +54)
        if not phone.startswith('+'):
            # Remover 0 inicial si existe
            if phone.startswith('0'):
                phone = phone[1:]
            # Agregar código de país
            phone = '+54' + phone
        
        return phone
    
    def format_phone_for_twilio(self, phone: str) -> str:
        """Formatear número para Twilio (whatsapp:+549..."""
        normalized = self.normalize_phone_number(phone)
        return f"whatsapp:{normalized}"
    
    async def send_message(self, phone: str, message: str):
        """Enviar mensaje de WhatsApp usando Twilio"""
        try:
            print("=" * 60)
            print("ENVIANDO MENSAJE")
            print(f"Teléfono: {phone}")
            print(f"Mensaje (primeros 100 caracteres): {message[:100]}...")
            print("=" * 60)
            
            logger.info("=" * 60)
            logger.info(f"📤 Enviando mensaje a {phone}")
            logger.info(f"📝 Mensaje: {message[:100]}...")
            logger.info("=" * 60)
            
            to_number = self.format_phone_for_twilio(phone)
            print(f"Teléfono formateado para Twilio: {to_number}")
            print(f"Desde: {self.twilio_whatsapp_number}")
            
            logger.info(f"Enviando mensaje desde {self.twilio_whatsapp_number} a {to_number}")
            
            message_obj = self.twilio_client.messages.create(
                body=message,
                from_=self.twilio_whatsapp_number,
                to=to_number
            )
            
            print(f"✅ Mensaje enviado exitosamente")
            print(f"MessageSid: {message_obj.sid}")
            logger.info(f"✅ Mensaje enviado a {phone} - MessageSid: {message_obj.sid}")
            
        except Exception as e:
            print(f"❌ ERROR ENVIANDO MENSAJE: {e}")
            import traceback
            traceback.print_exc()
            logger.error(f"❌ Error enviando mensaje a {phone}: {e}")
            logger.error(traceback.format_exc())
            raise
    
    def close(self):
        """Cerrar el bot"""
        # Flask se cierra automáticamente cuando el proceso termina
        logger.info("Bot de Twilio cerrado")


# Singleton del bot
_bot_instance: Optional[PadelReservationBotTwilio] = None


async def get_bot_instance() -> PadelReservationBotTwilio:
    """Obtener instancia única del bot"""
    global _bot_instance
    if _bot_instance is None:
        _bot_instance = PadelReservationBotTwilio()
        await _bot_instance.start()
    return _bot_instance


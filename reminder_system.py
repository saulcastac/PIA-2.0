"""
Sistema de recordatorios y control anti no-show
"""
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
from typing import List
import logging
from database import SessionLocal, Reservation, User
from whatsapp_bot_twilio import get_bot_instance
from config import (
    REMINDER_24H_ENABLED,
    REMINDER_3H_ENABLED,
    NO_SHOW_TOLERANCE_MINUTES,
    MAX_STRIKES,
    TIMEZONE
)
import pytz

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ReminderSystem:
    """Sistema de recordatorios y control de no-shows"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler(timezone=TIMEZONE)
        self.db = SessionLocal()
        self.timezone = pytz.timezone(TIMEZONE)
        
    async def start(self):
        """Iniciar el sistema de recordatorios"""
        logger.info("Iniciando sistema de recordatorios...")
        
        # Programar tareas periódicas
        # Verificar recordatorios cada 5 minutos
        self.scheduler.add_job(
            self.check_reminders,
            trigger=CronTrigger(minute="*/5"),
            id="check_reminders"
        )
        
        # Verificar no-shows cada hora
        self.scheduler.add_job(
            self.check_no_shows,
            trigger=CronTrigger(hour="*"),
            id="check_no_shows"
        )
        
        self.scheduler.start()
        logger.info("Sistema de recordatorios iniciado")
    
    async def check_reminders(self):
        """Verificar y enviar recordatorios pendientes"""
        try:
            now = datetime.now(self.timezone)
            
            # Recordatorio 24 horas antes
            if REMINDER_24H_ENABLED:
                await self.send_24h_reminders(now)
            
            # Recordatorio 3 horas antes
            if REMINDER_3H_ENABLED:
                await self.send_3h_reminders(now)
                
        except Exception as e:
            logger.error(f"Error en check_reminders: {e}")
    
    async def send_24h_reminders(self, now: datetime):
        """Enviar recordatorios 24 horas antes"""
        target_time = now + timedelta(hours=24)
        target_start = target_time.replace(hour=0, minute=0, second=0, microsecond=0)
        target_end = target_start + timedelta(hours=1)
        
        reservations = self.db.query(Reservation).filter(
            Reservation.status == "confirmed",
            Reservation.confirmed == True,
            Reservation.reminder_24h_sent == False,
            Reservation.date >= target_start,
            Reservation.date < target_end
        ).all()
        
        try:
            bot = await get_bot_instance()
            
            for reservation in reservations:
                try:
                    user = reservation.user
                    message = f"""⏰ Recordatorio de reserva

Tu partido de pádel es mañana:
🏓 Cancha: {reservation.court_name}
📅 Fecha: {reservation.date.strftime('%d/%m/%Y')}
⏰ Hora: {reservation.date.strftime('%H:%M')}

Por favor confirma tu asistencia respondiendo 'confirmo'."""
                    
                    await bot.send_message(user.phone_number, message)
                    reservation.reminder_24h_sent = True
                    self.db.commit()
                    
                    logger.info(f"Recordatorio 24h enviado a {user.phone_number}")
                except Exception as e:
                    logger.error(f"Error enviando recordatorio 24h: {e}")
        except Exception as e:
            logger.error(f"Error obteniendo bot en send_24h_reminders: {e}")
    
    async def send_3h_reminders(self, now: datetime):
        """Enviar recordatorios 3 horas antes"""
        target_time = now + timedelta(hours=3)
        target_start = target_time.replace(minute=0, second=0, microsecond=0)
        target_end = target_start + timedelta(minutes=5)
        
        reservations = self.db.query(Reservation).filter(
            Reservation.status == "confirmed",
            Reservation.confirmed == True,
            Reservation.reminder_3h_sent == False,
            Reservation.date >= target_start,
            Reservation.date < target_end
        ).all()
        
        try:
            bot = await get_bot_instance()
            
            for reservation in reservations:
                try:
                    user = reservation.user
                    message = f"""⏰ Recordatorio de reserva

Tu partido de pádel es en 3 horas:
🏓 Cancha: {reservation.court_name}
📅 Fecha: {reservation.date.strftime('%d/%m/%Y')}
⏰ Hora: {reservation.date.strftime('%H:%M')}

¡Nos vemos pronto!"""
                    
                    await bot.send_message(user.phone_number, message)
                    reservation.reminder_3h_sent = True
                    self.db.commit()
                    
                    logger.info(f"Recordatorio 3h enviado a {user.phone_number}")
            except Exception as e:
                logger.error(f"Error enviando recordatorio 3h: {e}")
        except Exception as e:
            logger.error(f"Error obteniendo bot en send_3h_reminders: {e}")
    
    async def check_no_shows(self):
        """Verificar y marcar no-shows"""
        try:
            now = datetime.now(self.timezone)
            tolerance_minutes = NO_SHOW_TOLERANCE_MINUTES
            
            # Buscar reservas que ya pasaron y no fueron confirmadas como asistidas
            cutoff_time = now - timedelta(minutes=tolerance_minutes)
            
            reservations = self.db.query(Reservation).filter(
                Reservation.status == "confirmed",
                Reservation.date < cutoff_time,
                Reservation.confirmed == True
            ).all()
            
            for reservation in reservations:
                # Verificar si el usuario confirmó asistencia
                # Si no, marcar como no-show
                if reservation.status == "confirmed":
                    await self.mark_no_show(reservation)
                    
        except Exception as e:
            logger.error(f"Error en check_no_shows: {e}")
    
    async def mark_no_show(self, reservation: Reservation):
        """Marcar una reserva como no-show y aplicar strike"""
        try:
            reservation.status = "no_show"
            self.db.commit()
            
            user = reservation.user
            user.strikes += 1
            
            try:
                bot = await get_bot_instance()
                
                if user.strikes >= MAX_STRIKES:
                    user.requires_prepayment = True
                    message = f"""⚠️ No-show registrado

No asististe a tu reserva del {reservation.date.strftime('%d/%m/%Y')} {reservation.date.strftime('%H:%M')}.

Has alcanzado {user.strikes} strikes. Las futuras reservas requerirán prepago."""
                else:
                    message = f"""⚠️ No-show registrado

No asististe a tu reserva del {reservation.date.strftime('%d/%m/%Y')} {reservation.date.strftime('%H:%M')}.

Strikes acumulados: {user.strikes}/{MAX_STRIKES}"""
                
                await bot.send_message(user.phone_number, message)
                self.db.commit()
                
                logger.info(f"No-show marcado para usuario {user.phone_number}, strikes: {user.strikes}")
            except Exception as e:
                logger.error(f"Error obteniendo bot en mark_no_show: {e}")
            
        except Exception as e:
            logger.error(f"Error marcando no-show: {e}")
    
    async def confirm_attendance(self, phone_number: str, reservation_id: int) -> bool:
        """Confirmar asistencia de un usuario"""
        try:
            reservation = self.db.query(Reservation).filter(
                Reservation.id == reservation_id
            ).first()
            
            if not reservation or reservation.user.phone_number != phone_number:
                return False
            
            if reservation.status == "confirmed":
                reservation.status = "completed"
                self.db.commit()
                logger.info(f"Asistencia confirmada para reserva {reservation_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error confirmando asistencia: {e}")
            return False
    
    def stop(self):
        """Detener el sistema de recordatorios"""
        self.scheduler.shutdown()
        logger.info("Sistema de recordatorios detenido")


"""
Cliente para Google Calendar API
Maneja la autenticación y creación de eventos en Google Calendar
"""
import os
import pickle
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from config import (
    GOOGLE_CREDENTIALS_FILE,
    GOOGLE_TOKEN_FILE,
    GOOGLE_CALENDAR_ID,
    COURT_CALENDAR_MAPPING,
    TIMEZONE
)
import pytz

# Scopes necesarios para Google Calendar
SCOPES = ['https://www.googleapis.com/auth/calendar']

logger = logging.getLogger(__name__)


class GoogleCalendarClient:
    """
    Cliente para interactuar con Google Calendar API
    """
    
    def __init__(self):
        self.service = None
        self.credentials = None
        self.authenticated = False
        
    def authenticate(self) -> bool:
        """
        Autenticar con Google Calendar API
        
        Returns:
            bool: True si la autenticación fue exitosa
        """
        try:
            creds = None
            
            # Cargar token existente si existe
            if os.path.exists(GOOGLE_TOKEN_FILE):
                with open(GOOGLE_TOKEN_FILE, 'rb') as token:
                    creds = pickle.load(token)
            
            # Si no hay credenciales válidas, autenticar
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    # Refrescar token expirado
                    creds.refresh(Request())
                else:
                    # Autenticación inicial
                    if not os.path.exists(GOOGLE_CREDENTIALS_FILE):
                        logger.error(f"❌ Archivo de credenciales no encontrado: {GOOGLE_CREDENTIALS_FILE}")
                        logger.error("Por favor, descarga credentials.json de Google Cloud Console")
                        return False
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        GOOGLE_CREDENTIALS_FILE, SCOPES)
                    creds = flow.run_local_server(port=0)
                
                # Guardar token para futuras ejecuciones
                with open(GOOGLE_TOKEN_FILE, 'wb') as token:
                    pickle.dump(creds, token)
            
            # Construir servicio de Google Calendar
            self.service = build('calendar', 'v3', credentials=creds)
            self.credentials = creds
            self.authenticated = True
            
            logger.info("✅ Autenticación con Google Calendar exitosa")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error en autenticación con Google Calendar: {e}")
            self.authenticated = False
            return False
    
    def list_calendars(self) -> List[Dict[str, Any]]:
        """
        Listar calendarios disponibles
        
        Returns:
            Lista de calendarios con su información
        """
        if not self.authenticated or not self.service:
            logger.error("No autenticado. Llama a authenticate() primero.")
            return []
        
        try:
            calendar_list = self.service.calendarList().list().execute()
            calendars = calendar_list.get('items', [])
            return calendars
        except HttpError as e:
            logger.error(f"Error listando calendarios: {e}")
            return []
    
    def create_event(
        self,
        court_name: str,
        date: datetime,
        time_slot: str,
        duration_minutes: int = 60,
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Crear un evento en Google Calendar
        
        Args:
            court_name: Nombre de la cancha (MONEX, GOCSA, etc.)
            date: Fecha de la reserva (datetime object)
            time_slot: Hora en formato "HH:MM"
            duration_minutes: Duración en minutos (default: 60)
            name: Nombre del reservante (opcional)
            description: Descripción adicional (opcional)
        
        Returns:
            Dict con información del evento creado (incluye 'id' y 'htmlLink'), None si falló
        """
        if not self.authenticated or not self.service:
            logger.error("No autenticado. Llama a authenticate() primero.")
            return None
        
        try:
            # Obtener el calendario específico para esta cancha
            calendar_id = COURT_CALENDAR_MAPPING.get(court_name, GOOGLE_CALENDAR_ID)
            
            # Parsear hora
            hour, minute = map(int, time_slot.split(':'))
            
            # Crear datetime con la hora especificada
            start_datetime = date.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            # Aplicar timezone
            tz = pytz.timezone(TIMEZONE)
            if start_datetime.tzinfo is None:
                start_datetime = tz.localize(start_datetime)
            
            # Calcular hora de fin
            end_datetime = start_datetime + timedelta(minutes=duration_minutes)
            
            # Formatear para Google Calendar API (RFC3339)
            start_time = start_datetime.isoformat()
            end_time = end_datetime.isoformat()
            
            # Crear título del evento
            title = f"Reserva Pádel - {court_name}"
            if name:
                title = f"Reserva Pádel - {court_name} - {name}"
            
            # Crear descripción
            event_description = f"Cancha: {court_name}\n"
            if name:
                event_description += f"Reservado por: {name}\n"
            if description:
                event_description += f"\n{description}"
            
            # Crear evento
            event = {
                'summary': title,
                'description': event_description,
                'start': {
                    'dateTime': start_time,
                    'timeZone': TIMEZONE,
                },
                'end': {
                    'dateTime': end_time,
                    'timeZone': TIMEZONE,
                },
            }
            
            # Insertar evento en el calendario
            created_event = self.service.events().insert(
                calendarId=calendar_id,
                body=event
            ).execute()
            
            logger.info(f"✅ Evento creado en Google Calendar: {created_event.get('id')}")
            
            return {
                'id': created_event.get('id'),
                'htmlLink': created_event.get('htmlLink'),
                'summary': created_event.get('summary'),
                'start': created_event.get('start'),
                'end': created_event.get('end')
            }
            
        except HttpError as e:
            logger.error(f"❌ Error creando evento en Google Calendar: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Error inesperado creando evento: {e}")
            return None
    
    def delete_event(self, event_id: str, court_name: Optional[str] = None) -> bool:
        """
        Eliminar un evento de Google Calendar
        
        Args:
            event_id: ID del evento a eliminar
            court_name: Nombre de la cancha (opcional, para obtener el calendario correcto)
        
        Returns:
            bool: True si se eliminó exitosamente
        """
        if not self.authenticated or not self.service:
            logger.error("No autenticado. Llama a authenticate() primero.")
            return False
        
        try:
            # Obtener el calendario específico para esta cancha
            calendar_id = COURT_CALENDAR_MAPPING.get(court_name, GOOGLE_CALENDAR_ID) if court_name else GOOGLE_CALENDAR_ID
            
            self.service.events().delete(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()
            
            logger.info(f"✅ Evento eliminado de Google Calendar: {event_id}")
            return True
            
        except HttpError as e:
            logger.error(f"❌ Error eliminando evento de Google Calendar: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error inesperado eliminando evento: {e}")
            return False
    
    def get_availability(self, date: datetime, court_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Obtener disponibilidad de una cancha en una fecha específica
        
        Args:
            date: Fecha para consultar disponibilidad
            court_name: Nombre de la cancha (opcional)
        
        Returns:
            Lista de eventos existentes en esa fecha
        """
        if not self.authenticated or not self.service:
            logger.error("No autenticado. Llama a authenticate() primero.")
            return []
        
        try:
            # Obtener el calendario específico para esta cancha
            calendar_id = COURT_CALENDAR_MAPPING.get(court_name, GOOGLE_CALENDAR_ID) if court_name else GOOGLE_CALENDAR_ID
            
            # Calcular inicio y fin del día
            tz = pytz.timezone(TIMEZONE)
            start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
            if start_of_day.tzinfo is None:
                start_of_day = tz.localize(start_of_day)
            end_of_day = start_of_day + timedelta(days=1)
            
            # Formatear para Google Calendar API
            time_min = start_of_day.isoformat()
            time_max = end_of_day.isoformat()
            
            # Obtener eventos
            events_result = self.service.events().list(
                calendarId=calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            return events
            
        except HttpError as e:
            logger.error(f"❌ Error obteniendo disponibilidad: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ Error inesperado obteniendo disponibilidad: {e}")
            return []


# Instancia global del cliente
_calendar_client: Optional[GoogleCalendarClient] = None


async def get_google_calendar_instance() -> GoogleCalendarClient:
    """
    Obtener instancia singleton del cliente de Google Calendar
    
    Returns:
        GoogleCalendarClient: Instancia autenticada del cliente
    """
    global _calendar_client
    
    if _calendar_client is None:
        _calendar_client = GoogleCalendarClient()
        if not _calendar_client.authenticate():
            raise Exception("No se pudo autenticar con Google Calendar")
    
    return _calendar_client




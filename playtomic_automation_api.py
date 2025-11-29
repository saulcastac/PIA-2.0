"""
Playtomic Automation usando API - Versión simplificada que usa llamadas directas a la API
Reemplaza la automatización basada en Selenium con llamadas HTTP directas
"""
import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from playtomic_api_client import PlaytomicAPIClient

logger = logging.getLogger(__name__)


class PlaytomicAutomation:
    """
    Automatización de Playtomic usando API directa
    Mantiene la misma interfaz que la versión anterior para compatibilidad
    """
    
    def __init__(self):
        self.api_client: Optional[PlaytomicAPIClient] = None
        self.logged_in = False
        
    async def start(self):
        """Inicializar el cliente API"""
        try:
            self.api_client = PlaytomicAPIClient()
            await self.api_client.start()
            logger.info("✅ Cliente API de Playtomic iniciado")
            return True
        except Exception as e:
            logger.error(f"❌ Error iniciando cliente API: {e}")
            return False
    
    async def close(self):
        """Cerrar el cliente API"""
        if self.api_client:
            try:
                await self.api_client.close()
                logger.info("Cliente API cerrado")
            except Exception as e:
                logger.warning(f"Error cerrando cliente API: {e}")
            finally:
                self.api_client = None
                self.logged_in = False
    
    async def login(self, email: str = None, password: str = None) -> bool:
        """
        Iniciar sesión en Playtomic
        
        Args:
            email: Email del usuario (opcional, se puede leer de variables de entorno)
            password: Contraseña (opcional, se puede leer de variables de entorno)
        
        Returns:
            bool: True si el login fue exitoso
        """
        if not self.api_client:
            logger.error("Cliente API no iniciado. Llama a start() primero.")
            return False
        
        try:
            result = await self.api_client.login(email, password)
            self.logged_in = result
            if result:
                logger.info("✅ Login exitoso en Playtomic")
            else:
                logger.error("❌ Login falló en Playtomic")
            return result
        except Exception as e:
            logger.error(f"❌ Error durante login: {e}")
            return False
    
    async def make_reservation(self, court_name: str, date: datetime, time_slot: str, duration: int = 60) -> Optional[str]:
        """
        Hacer una reserva
        
        Args:
            court_name: Nombre de la cancha (MONEX, GOCSA, etc.)
            date: Fecha de la reserva
            time_slot: Hora en formato "HH:MM"
            duration: Duración en minutos (default: 60)
        
        Returns:
            str: ID de la reserva si fue exitosa, None si falló
        """
        if not self.api_client:
            logger.error("Cliente API no iniciado")
            return None
        
        if not self.logged_in:
            logger.error("No hay sesión activa. Debes hacer login primero.")
            return None
        
        try:
            logger.info(f"🎯 Intentando reserva: {court_name} - {date.strftime('%d/%m/%Y')} {time_slot}")
            
            reservation_id = await self.api_client.make_reservation(
                court_name=court_name,
                date=date,
                time_slot=time_slot,
                duration=duration
            )
            
            if reservation_id:
                logger.info(f"✅ Reserva exitosa: {reservation_id}")
            else:
                logger.error("❌ Reserva falló")
            
            return reservation_id
            
        except Exception as e:
            logger.error(f"❌ Error durante reserva: {e}")
            return None
    
    async def get_availability(self, date: datetime, court_name: str = None) -> List[Dict[str, Any]]:
        """
        Obtener disponibilidad para una fecha específica
        
        Args:
            date: Fecha para consultar disponibilidad
            court_name: Nombre específico de cancha (opcional)
        
        Returns:
            List[Dict]: Lista de horarios disponibles
        """
        if not self.api_client:
            logger.error("Cliente API no iniciado")
            return []
        
        if not self.logged_in:
            logger.error("No hay sesión activa. Debes hacer login primero.")
            return []
        
        try:
            logger.info(f"🔍 Consultando disponibilidad para {date.strftime('%d/%m/%Y')}")
            
            availability_data = await self.api_client.get_availability(date, court_name)
            
            # Convertir el formato de la API a la estructura esperada por el resto del sistema
            availability_list = []
            
            if availability_data:
                # Procesar la respuesta de la API y convertirla al formato esperado
                # Esto dependerá del formato exacto que devuelva la API de Playtomic
                logger.info(f"✅ Disponibilidad obtenida: {len(availability_data)} elementos")
                
                # Por ahora, devolvemos la estructura básica
                # Puedes ajustar esto según el formato real de la API
                for item in availability_data.get('slots', []):
                    availability_list.append({
                        'time': item.get('time'),
                        'court': item.get('court'),
                        'available': item.get('available', False),
                        'price': item.get('price')
                    })
            else:
                logger.warning("No se obtuvo disponibilidad")
            
            return availability_list
            
        except Exception as e:
            logger.error(f"❌ Error consultando disponibilidad: {e}")
            return []
    
    async def search_and_navigate_to_club(self, club_name: str) -> bool:
        """
        Buscar y navegar a un club específico
        En la versión API, esto no es necesario ya que usamos tenant_id directamente
        
        Args:
            club_name: Nombre del club
        
        Returns:
            bool: True si fue exitoso (siempre True en versión API)
        """
        logger.info(f"🏢 Configurando club: {club_name}")
        # En la versión API, el tenant_id ya está configurado en el cliente
        return True
    
    # Métodos de compatibilidad con la versión anterior
    @property
    def browser(self):
        """Propiedad de compatibilidad - no hay navegador en versión API"""
        return None
    
    @property
    def page(self):
        """Propiedad de compatibilidad - no hay página en versión API"""
        return None


# Función de conveniencia para obtener una instancia
async def get_playtomic_instance() -> PlaytomicAutomation:
    """
    Obtener una instancia configurada de PlaytomicAutomation
    Mantiene compatibilidad con el código existente
    """
    automation = PlaytomicAutomation()
    await automation.start()
    return automation


if __name__ == "__main__":
    # Ejemplo de uso
    async def test_automation():
        automation = PlaytomicAutomation()
        
        try:
            # Iniciar
            await automation.start()
            
            # Login
            if await automation.login():
                # Obtener disponibilidad
                from datetime import datetime
                test_date = datetime(2025, 11, 27)
                availability = await automation.get_availability(test_date)
                print(f"Disponibilidad: {len(availability)} slots")
                
                # Hacer reserva
                reservation_id = await automation.make_reservation("MONEX", test_date, "19:30")
                if reservation_id:
                    print(f"✅ Reserva exitosa: {reservation_id}")
                else:
                    print("❌ Reserva falló")
            else:
                print("❌ Login falló")
                
        finally:
            await automation.close()
    
    asyncio.run(test_automation())

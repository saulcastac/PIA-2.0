"""
Cliente API para Playtomic - Manejo directo de reservas a través de la API
"""
import aiohttp
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import json
from urllib.parse import urlencode
import os
from config import PLAYTOMIC_TENANT_ID, PLAYTOMIC_COURT_MAPPING

logger = logging.getLogger(__name__)


class PlaytomicAPIClient:
    """Cliente para interactuar con la API de Playtomic"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.base_url = "https://playtomic.com"
        self.api_base = f"{self.base_url}/api/web-app"
        self.logged_in = False
        self.user_data = None
        
        # Configuración de headers comunes para simular navegador
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
        
        # Configuración del club (tenant)
        self.tenant_id = PLAYTOMIC_TENANT_ID
        
        # Mapeo de canchas a resource_ids
        self.court_mapping = PLAYTOMIC_COURT_MAPPING
    
    async def start(self):
        """Inicializar la sesión HTTP"""
        if not self.session:
            connector = aiohttp.TCPConnector(ssl=False)
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(
                headers=self.headers,
                connector=connector,
                timeout=timeout
            )
            logger.info("Sesión HTTP iniciada")
    
    async def close(self):
        """Cerrar la sesión HTTP"""
        if self.session:
            await self.session.close()
            self.session = None
            logger.info("Sesión HTTP cerrada")
    
    async def login(self, email: str = None, password: str = None) -> bool:
        """
        Iniciar sesión en Playtomic usando el formulario web
        
        Args:
            email: Email del usuario (si no se proporciona, se lee de variables de entorno)
            password: Contraseña (si no se proporciona, se lee de variables de entorno)
        
        Returns:
            bool: True si el login fue exitoso
        """
        if not self.session:
            await self.start()
        
        # Obtener credenciales
        if not email:
            email = os.getenv('PLAYTOMIC_EMAIL')
        if not password:
            password = os.getenv('PLAYTOMIC_PASSWORD')
        
        if not email or not password:
            logger.error("Credenciales no encontradas. Configura PLAYTOMIC_EMAIL y PLAYTOMIC_PASSWORD")
            return False
        
        try:
            # Paso 1: Obtener la página de login para conseguir cookies y tokens CSRF
            login_page_url = "https://playtomic.com/login"
            logger.info(f"Obteniendo página de login: {login_page_url}")
            
            async with self.session.get(login_page_url) as response:
                if response.status != 200:
                    logger.error(f"❌ Error obteniendo página de login: {response.status}")
                    return False
                
                login_html = await response.text()
                logger.info("✅ Página de login obtenida")
            
            # Paso 2: Extraer token CSRF si es necesario
            csrf_token = None
            if 'csrf' in login_html.lower() or '_token' in login_html.lower():
                # Buscar token CSRF en el HTML
                import re
                csrf_match = re.search(r'name=["\']_token["\'] value=["\']([^"\']+)["\']', login_html)
                if not csrf_match:
                    csrf_match = re.search(r'name=["\']csrf_token["\'] value=["\']([^"\']+)["\']', login_html)
                if csrf_match:
                    csrf_token = csrf_match.group(1)
                    logger.info("✅ Token CSRF encontrado")
            
            # Paso 3: Preparar datos de login
            login_data = {
                'email': email,
                'password': password
            }
            
            # Agregar token CSRF si se encontró
            if csrf_token:
                login_data['_token'] = csrf_token
            
            # Paso 4: Realizar login POST
            login_post_url = "https://playtomic.com/login"
            
            # Headers para simular un navegador
            login_headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Referer': 'https://playtomic.com/login',
                'Origin': 'https://playtomic.com'
            }
            
            logger.info(f"Enviando credenciales de login...")
            
            async with self.session.post(login_post_url, data=login_data, headers=login_headers, allow_redirects=True) as response:
                response_text = await response.text()
                
                # Verificar si el login fue exitoso
                # Si nos redirige o no hay errores de login, asumimos éxito
                if response.status in [200, 302] and 'error' not in response_text.lower() and 'invalid' not in response_text.lower():
                    # Verificar si tenemos cookies de sesión
                    session_cookies = [cookie for cookie in self.session.cookie_jar if 'session' in cookie.key.lower() or 'auth' in cookie.key.lower()]
                    
                    if session_cookies or response.status == 302:
                        self.logged_in = True
                        logger.info("✅ Login exitoso - cookies de sesión obtenidas")
                        return True
                    else:
                        logger.warning("⚠️  Login posiblemente exitoso pero sin cookies claras")
                        self.logged_in = True  # Intentamos de todas formas
                        return True
                else:
                    logger.error(f"❌ Error en login: {response.status}")
                    logger.error(f"Respuesta contiene: {response_text[:200]}...")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Excepción durante login: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _format_datetime_for_api(self, date: datetime, time_str: str) -> str:
        """
        Formatear fecha y hora para la API de Playtomic
        
        Args:
            date: Fecha de la reserva
            time_str: Hora en formato "HH:MM" (se asume que ya está en UTC)
        
        Returns:
            str: Fecha y hora en formato ISO 8601 UTC
        """
        try:
            # Parsear la hora
            hour, minute = map(int, time_str.split(':'))
            
            # Crear datetime combinando fecha y hora
            # Asumimos que time_str ya está en UTC como en el link proporcionado
            reservation_datetime = date.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            # Formatear para la API (ya está en UTC)
            formatted_time = reservation_datetime.strftime('%Y-%m-%dT%H:%M:%S.000Z')
            
            logger.info(f"Fecha/hora formateada para API: {formatted_time}")
            return formatted_time
            
        except Exception as e:
            logger.error(f"Error formateando datetime: {e}")
            raise
    
    async def make_reservation_from_url(self, payment_url: str) -> Optional[str]:
        """
        Hacer una reserva usando una URL completa de la API de pagos
        
        Args:
            payment_url: URL completa de la API de pagos de Playtomic
        
        Returns:
            str: ID de la reserva si fue exitosa, None si falló
        """
        if not self.logged_in:
            logger.error("❌ No hay sesión activa. Debes hacer login primero.")
            return None
        
        try:
            logger.info(f"🎯 Intentando reserva con URL directa:")
            logger.info(f"   URL: {payment_url}")
            
            # Realizar la petición de reserva
            async with self.session.get(payment_url) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info("✅ Reserva exitosa")
                    logger.info(f"Respuesta: {json.dumps(result, indent=2)}")
                    
                    # Extraer ID de reserva si está disponible
                    reservation_id = result.get('id') or result.get('reservation_id') or result.get('payment_id')
                    return reservation_id or "SUCCESS"
                    
                elif response.status == 400:
                    error_text = await response.text()
                    logger.error(f"❌ Error 400 - Petición inválida: {error_text}")
                    return None
                    
                elif response.status == 401:
                    logger.error("❌ Error 401 - No autorizado. Sesión expirada?")
                    self.logged_in = False
                    return None
                    
                elif response.status == 409:
                    logger.error("❌ Error 409 - Conflicto. La cancha puede estar ocupada")
                    return None
                    
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Error {response.status}: {error_text}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Excepción durante reserva: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def make_reservation(self, court_name: str, date: datetime, time_slot: str, duration: int = 60) -> Optional[str]:
        """
        Hacer una reserva usando la API de pagos de Playtomic
        
        Args:
            court_name: Nombre de la cancha (MONEX, GOCSA, etc.)
            date: Fecha de la reserva
            time_slot: Hora en formato "HH:MM"
            duration: Duración en minutos (default: 60)
        
        Returns:
            str: ID de la reserva si fue exitosa, None si falló
        """
        if not self.logged_in:
            logger.error("❌ No hay sesión activa. Debes hacer login primero.")
            return None
        
        # Obtener resource_id de la cancha
        resource_id = self.court_mapping.get(court_name.upper())
        if not resource_id:
            logger.error(f"❌ Cancha '{court_name}' no encontrada en el mapeo")
            return None
        
        try:
            # Formatear fecha y hora para la API
            start_datetime = self._format_datetime_for_api(date, time_slot)
            
            # Construir URL de la API de pagos
            params = {
                'type': 'CUSTOMER_MATCH',
                'tenant_id': self.tenant_id,
                'resource_id': resource_id,
                'start': start_datetime,
                'duration': duration
            }
            
            payment_url = f"{self.api_base}/payments?{urlencode(params)}"
            
            logger.info(f"🎯 Intentando reserva:")
            logger.info(f"   Cancha: {court_name} ({resource_id})")
            logger.info(f"   Fecha/Hora: {start_datetime}")
            logger.info(f"   Duración: {duration} minutos")
            logger.info(f"   URL: {payment_url}")
            
            # Realizar la petición de reserva
            async with self.session.get(payment_url) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info("✅ Reserva exitosa")
                    logger.info(f"Respuesta: {json.dumps(result, indent=2)}")
                    
                    # Extraer ID de reserva si está disponible
                    reservation_id = result.get('id') or result.get('reservation_id') or result.get('payment_id')
                    return reservation_id or "SUCCESS"
                    
                elif response.status == 400:
                    error_text = await response.text()
                    logger.error(f"❌ Error 400 - Petición inválida: {error_text}")
                    return None
                    
                elif response.status == 401:
                    logger.error("❌ Error 401 - No autorizado. Sesión expirada?")
                    self.logged_in = False
                    return None
                    
                elif response.status == 409:
                    logger.error("❌ Error 409 - Conflicto. La cancha puede estar ocupada")
                    return None
                    
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Error {response.status}: {error_text}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Excepción durante reserva: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def get_availability(self, date: datetime, court_name: str = None) -> Dict[str, Any]:
        """
        Obtener disponibilidad para una fecha específica
        
        Args:
            date: Fecha para consultar disponibilidad
            court_name: Nombre específico de cancha (opcional)
        
        Returns:
            dict: Información de disponibilidad
        """
        if not self.logged_in:
            logger.error("❌ No hay sesión activa. Debes hacer login primero.")
            return {}
        
        try:
            # Construir URL para consultar disponibilidad
            date_str = date.strftime('%Y-%m-%d')
            availability_url = f"{self.api_base}/availability/{self.tenant_id}/{date_str}"
            
            logger.info(f"🔍 Consultando disponibilidad para {date_str}")
            
            async with self.session.get(availability_url) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info("✅ Disponibilidad obtenida")
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Error obteniendo disponibilidad: {response.status} - {error_text}")
                    return {}
                    
        except Exception as e:
            logger.error(f"❌ Excepción consultando disponibilidad: {e}")
            return {}
    
    async def __aenter__(self):
        """Context manager entry"""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        await self.close()


# Función de conveniencia para obtener una instancia
async def get_playtomic_api_client() -> PlaytomicAPIClient:
    """Obtener una instancia configurada del cliente API"""
    client = PlaytomicAPIClient()
    await client.start()
    return client


if __name__ == "__main__":
    # Ejemplo de uso
    async def test_api():
        async with PlaytomicAPIClient() as client:
            # Login
            if await client.login():
                # Hacer una reserva de prueba
                from datetime import datetime
                test_date = datetime(2025, 11, 27)
                reservation_id = await client.make_reservation("MONEX", test_date, "19:30")
                if reservation_id:
                    print(f"✅ Reserva exitosa: {reservation_id}")
                else:
                    print("❌ Reserva falló")
            else:
                print("❌ Login falló")
    
    asyncio.run(test_api())

"""
Automatización de Playtomic usando navegador (Playwright)
Hace login y luego navega al link de reserva para automatizar los clicks de pago
"""
import asyncio
import logging
from datetime import datetime
from typing import Optional
from playwright.async_api import async_playwright, Browser, Page
import os

logger = logging.getLogger(__name__)


class PlaytomicBrowserAutomation:
    """
    Automatización de Playtomic usando navegador real
    """
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.logged_in = False
        
    async def start(self, headless: bool = False):
        """
        Iniciar el navegador
        
        Args:
            headless: Si True, ejecuta sin interfaz gráfica
        """
        try:
            playwright = await async_playwright().start()
            
            # Iniciar navegador Chrome
            self.browser = await playwright.chromium.launch(
                headless=headless,
                args=[
                    '--no-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor'
                ]
            )
            
            # Crear contexto con user agent real
            context = await self.browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080}
            )
            
            # Crear página
            self.page = await context.new_page()
            
            logger.info("✅ Navegador iniciado correctamente")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error iniciando navegador: {e}")
            return False
    
    async def close(self):
        """Cerrar el navegador"""
        if self.browser:
            try:
                await self.browser.close()
                logger.info("Navegador cerrado")
            except Exception as e:
                logger.warning(f"Error cerrando navegador: {e}")
            finally:
                self.browser = None
                self.page = None
                self.logged_in = False
    
    async def login(self, email: str = None, password: str = None) -> bool:
        """
        Hacer login en Playtomic
        
        Args:
            email: Email del usuario
            password: Contraseña del usuario
        
        Returns:
            bool: True si el login fue exitoso
        """
        if not self.page:
            logger.error("Navegador no iniciado")
            return False
        
        # Obtener credenciales
        if not email:
            email = os.getenv('PLAYTOMIC_EMAIL')
        if not password:
            password = os.getenv('PLAYTOMIC_PASSWORD')
        
        if not email or not password:
            logger.error("Credenciales no encontradas")
            return False
        
        try:
            logger.info("🔐 Navegando a página de login...")
            await self.page.goto('https://app.playtomic.com/login', wait_until='networkidle')
            
            # Aceptar cookies si aparece el popup
            try:
                await self.page.wait_for_selector('button:has-text("Aceptar")', timeout=3000)
                await self.page.click('button:has-text("Aceptar")')
                logger.info("✅ Cookies aceptadas")
            except:
                try:
                    await self.page.wait_for_selector('button:has-text("Accept")', timeout=3000)
                    await self.page.click('button:has-text("Accept")')
                    logger.info("✅ Cookies aceptadas")
                except:
                    logger.info("ℹ️  No se encontró popup de cookies")
            
            # Esperar a que aparezcan los campos de login
            await self.page.wait_for_selector('input[placeholder="Email"], input[type="email"]', timeout=10000)
            
            # Llenar email
            logger.info("📧 Ingresando email...")
            await self.page.fill('input[placeholder="Email"], input[type="email"]', email)
            
            # Llenar password  
            logger.info("🔑 Ingresando contraseña...")
            await self.page.fill('input[placeholder="Password"], input[type="password"]', password)
            
            # Hacer click en login
            logger.info("🚀 Haciendo click en login...")
            await self.page.click('button:has-text("Log in"), button[type="submit"]')
            
            # Esperar a que se complete el login
            await self.page.wait_for_load_state('networkidle')
            
            # Verificar si el login fue exitoso
            current_url = self.page.url
            logger.info(f"URL después del login: {current_url}")
            
            # Si ya no estamos en la página de login, el login fue exitoso
            if 'login' not in current_url.lower() or 'dashboard' in current_url.lower() or 'app.playtomic.com' in current_url.lower():
                self.logged_in = True
                logger.info("✅ Login exitoso")
                return True
            else:
                # Verificar si hay mensajes de error
                try:
                    error_elements = await self.page.query_selector_all('.error, .alert-danger, [class*="error"], .text-red-500')
                    if error_elements:
                        error_text = await error_elements[0].inner_text()
                        logger.error(f"❌ Error de login: {error_text}")
                    else:
                        logger.error("❌ Login falló - verificar credenciales")
                except:
                    logger.error("❌ Login falló - verificar credenciales")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error durante login: {e}")
            return False
    
    async def navigate_to_reservation_url(self, reservation_url: str) -> bool:
        """
        Navegar al URL de reserva
        
        Args:
            reservation_url: URL de la reserva de Playtomic
        
        Returns:
            bool: True si la navegación fue exitosa
        """
        if not self.page or not self.logged_in:
            logger.error("Necesitas hacer login primero")
            return False
        
        try:
            logger.info(f"🎯 Navegando al URL de reserva...")
            logger.info(f"URL: {reservation_url}")
            
            await self.page.goto(reservation_url, wait_until='networkidle')
            
            # Esperar a que cargue la página
            await asyncio.sleep(2)
            
            current_url = self.page.url
            logger.info(f"✅ Navegación completada. URL actual: {current_url}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error navegando al URL: {e}")
            return False
    
    async def complete_payment_process(self) -> Optional[str]:
        """
        Completar el proceso de pago automatizando los clicks necesarios
        
        Returns:
            str: ID de reserva si fue exitoso, None si falló
        """
        if not self.page:
            logger.error("Página no disponible")
            return None
        
        try:
            logger.info("💳 Iniciando proceso de pago...")
            
            # Esperar a que cargue la página de pago
            await self.page.wait_for_load_state('networkidle')
            
            # Buscar y hacer click en botón de continuar/confirmar
            continue_selectors = [
                'button:has-text("Continuar")',
                'button:has-text("Continue")',
                'button:has-text("Confirmar")',
                'button:has-text("Confirm")',
                'button:has-text("Reservar")',
                'button:has-text("Reserve")',
                'button[type="submit"]',
                '.btn-primary',
                '.continue-btn'
            ]
            
            for selector in continue_selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=3000)
                    logger.info(f"🔘 Haciendo click en: {selector}")
                    await self.page.click(selector)
                    await asyncio.sleep(2)
                    break
                except:
                    continue
            
            # Esperar a que se procese
            await self.page.wait_for_load_state('networkidle')
            
            # Buscar confirmación de reserva exitosa
            success_indicators = [
                'text=reserva confirmada',
                'text=reservation confirmed',
                'text=éxito',
                'text=success',
                '.success',
                '.confirmation'
            ]
            
            for indicator in success_indicators:
                try:
                    element = await self.page.wait_for_selector(indicator, timeout=5000)
                    if element:
                        logger.info("✅ Reserva confirmada!")
                        
                        # Intentar extraer ID de reserva
                        page_content = await self.page.content()
                        import re
                        id_match = re.search(r'reserva[:\s#]*([A-Za-z0-9-]+)', page_content, re.IGNORECASE)
                        if id_match:
                            return id_match.group(1)
                        else:
                            return "SUCCESS"
                except:
                    continue
            
            # Si llegamos aquí, verificar si hay errores
            error_indicators = [
                'text=error',
                'text=failed',
                'text=no disponible',
                'text=not available',
                '.error',
                '.alert-danger'
            ]
            
            for indicator in error_indicators:
                try:
                    element = await self.page.wait_for_selector(indicator, timeout=2000)
                    if element:
                        error_text = await element.inner_text()
                        logger.error(f"❌ Error en reserva: {error_text}")
                        return None
                except:
                    continue
            
            logger.warning("⚠️  No se pudo determinar el resultado de la reserva")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error en proceso de pago: {e}")
            return None
    
    async def make_reservation_from_url(self, reservation_url: str) -> Optional[str]:
        """
        Hacer reserva completa desde URL
        
        Args:
            reservation_url: URL de reserva de Playtomic
        
        Returns:
            str: ID de reserva si fue exitoso
        """
        try:
            # Navegar al URL
            if not await self.navigate_to_reservation_url(reservation_url):
                return None
            
            # Completar proceso de pago
            return await self.complete_payment_process()
            
        except Exception as e:
            logger.error(f"❌ Error en reserva: {e}")
            return None


# Función de conveniencia
async def get_playtomic_browser_instance(headless: bool = False) -> PlaytomicBrowserAutomation:
    """Obtener instancia del automatizador de navegador"""
    automation = PlaytomicBrowserAutomation()
    await automation.start(headless=headless)
    return automation


if __name__ == "__main__":
    # Ejemplo de uso
    async def test_browser_automation():
        automation = PlaytomicBrowserAutomation()
        
        try:
            # Iniciar navegador (visible para debug)
            await automation.start(headless=False)
            
            # Login
            if await automation.login():
                # URL de ejemplo
                test_url = "https://playtomic.com/api/web-app/payments?type=CUSTOMER_MATCH&tenant_id=65a5b336-e05c-4989-a3b8-3374e9ad335f&resource_id=c5270541-aeec-4640-b67d-346bd8e9d072&start=2025-11-27T15%3A00%3A00.000Z&duration=60"
                
                # Hacer reserva
                reservation_id = await automation.make_reservation_from_url(test_url)
                if reservation_id:
                    print(f"✅ Reserva exitosa: {reservation_id}")
                else:
                    print("❌ Reserva falló")
            else:
                print("❌ Login falló")
                
        finally:
            await automation.close()
    
    asyncio.run(test_browser_automation())

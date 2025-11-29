"""
Aplicación principal del sistema de reservas de pádel
"""
import asyncio
import logging
import sys
from database import init_db
from whatsapp_bot_twilio import PadelReservationBotTwilio as PadelReservationBot
from playtomic_automation_api import get_playtomic_instance
import signal

# Configurar logging para que se muestre correctamente en consola de Windows
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
    force=True
)

# Configurar encoding para Windows
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

logger = logging.getLogger(__name__)


class PadelReservationApp:
    """Aplicación principal"""
    
    def __init__(self):
        self.bot = None
        self.playtomic = None
        self.running = False
        
    async def start(self):
        """Iniciar la aplicación"""
        logger.info("Iniciando sistema de reservas de pádel...")
        
        # Inicializar base de datos
        logger.info("Inicializando base de datos...")
        init_db()
        
        # Iniciar Playtomic automation
        logger.info("Iniciando módulo Playtomic...")
        self.playtomic = await get_playtomic_instance()
        
        # Iniciar bot de WhatsApp
        logger.info("Iniciando bot de WhatsApp...")
        self.bot = PadelReservationBot()
        await self.bot.start()
        
        self.running = True
        logger.info("✅ Sistema iniciado correctamente")
        logger.info("Esperando mensajes de WhatsApp...")
        
    async def stop(self):
        """Detener la aplicación"""
        logger.info("Deteniendo sistema...")
        self.running = False
        
        if self.playtomic:
            try:
                await self.playtomic.close()
            except Exception as e:
                logger.warning(f"Error cerrando Playtomic (puede estar ya cerrado): {e}")
        
        if self.bot and hasattr(self.bot, 'close'):
            try:
                self.bot.close()
            except Exception as e:
                logger.warning(f"Error cerrando bot: {e}")
        
        logger.info("Sistema detenido")
    
    def run(self):
        """Ejecutar la aplicación"""
        # Ejecutar
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Iniciar aplicación
            loop.run_until_complete(self.start())
            
            # Mantener el loop corriendo
            try:
                loop.run_forever()
            except KeyboardInterrupt:
                logger.info("Interrupción del teclado (Ctrl+C)...")
                try:
                    loop.run_until_complete(self.stop())
                except Exception as e:
                    logger.warning(f"Error durante cierre: {e}")
                finally:
                    # Cerrar el loop de forma segura
                    try:
                        pending = asyncio.all_tasks(loop)
                        for task in pending:
                            task.cancel()
                        if pending:
                            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                    except Exception as e:
                        logger.warning(f"Error cancelando tareas: {e}")
                    finally:
                        loop.close()
                
        except Exception as e:
            logger.error(f"Error en la aplicación: {e}")
            if 'loop' in locals():
                try:
                    loop.run_until_complete(self.stop())
                except Exception as stop_error:
                    logger.warning(f"Error durante cierre: {stop_error}")
                finally:
                    try:
                        loop.close()
                    except:
                        pass


if __name__ == "__main__":
    app = PadelReservationApp()
    app.run()


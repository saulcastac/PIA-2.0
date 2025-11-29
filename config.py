"""
Configuración del sistema de reservas de pádel
"""
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

# Credenciales Playtomic
PLAYTOMIC_EMAIL = os.getenv("PLAYTOMIC_EMAIL", "")
PLAYTOMIC_PASSWORD = os.getenv("PLAYTOMIC_PASSWORD", "")

# Configuración API de Playtomic
PLAYTOMIC_TENANT_ID = os.getenv("PLAYTOMIC_TENANT_ID", "65a5b336-e05c-4989-a3b8-3374e9ad335f")
PLAYTOMIC_CLUB_NAME = os.getenv("PLAYTOMIC_CLUB_NAME", "Carbono Manzanillo")

# Mapeo de canchas a resource_ids
PLAYTOMIC_COURT_MAPPING = {
    "MONEX": os.getenv("PLAYTOMIC_MONEX_ID", "da1fda51-61f8-4432-92b9-d93f980ed106"),
    "GOCSA": os.getenv("PLAYTOMIC_GOCSA_ID", "c5270541-aeec-4640-b67d-346bd8e9d072"),
    "WOODWARD": os.getenv("PLAYTOMIC_WOODWARD_ID", ""),  # Necesitarás obtener este ID
    "TEDS": os.getenv("PLAYTOMIC_TEDS_ID", "")  # Necesitarás obtener este ID
}

# Configuración WhatsApp
WHATSAPP_SESSION_PATH = Path(os.getenv("WHATSAPP_SESSION_PATH", "./whatsapp_session"))

# Configuración de recordatorios
REMINDER_24H_ENABLED = os.getenv("REMINDER_24H_ENABLED", "true").lower() == "true"
REMINDER_3H_ENABLED = os.getenv("REMINDER_3H_ENABLED", "true").lower() == "true"
NO_SHOW_TOLERANCE_MINUTES = int(os.getenv("NO_SHOW_TOLERANCE_MINUTES", "10"))

# Sistema de strikes
MAX_STRIKES = int(os.getenv("MAX_STRIKES", "2"))

# Base de datos
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./pad_ia.db")

# Timezone
TIMEZONE = os.getenv("TIMEZONE", "America/Argentina/Buenos_Aires")

# Configuración Twilio WhatsApp
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER", "")  # Formato: whatsapp:+14155238886

# Configuración OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Validación (comentada para desarrollo - descomentar en producción)
# if not PLAYTOMIC_EMAIL or not PLAYTOMIC_PASSWORD:
#     raise ValueError("PLAYTOMIC_EMAIL y PLAYTOMIC_PASSWORD deben estar configurados en .env")
# if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN or not TWILIO_WHATSAPP_NUMBER:
#     raise ValueError("TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN y TWILIO_WHATSAPP_NUMBER deben estar configurados en .env")


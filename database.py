"""
Modelos de base de datos para el sistema de reservas
"""
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from config import DATABASE_URL

Base = declarative_base()
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class User(Base):
    """Usuario del sistema identificado por número de WhatsApp"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    strikes = Column(Integer, default=0)
    requires_prepayment = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    reservations = relationship("Reservation", back_populates="user")


class Reservation(Base):
    """Reserva de cancha de pádel"""
    __tablename__ = "reservations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    playtomic_reservation_id = Column(String, nullable=True)  # ID de reserva en Playtomic (legacy)
    google_calendar_event_id = Column(String, nullable=True)  # ID del evento en Google Calendar
    google_calendar_link = Column(String, nullable=True)  # Link al evento en Google Calendar
    name = Column(String, nullable=True)  # Nombre de la persona que hace la reserva
    court_name = Column(String, nullable=False)  # Nombre de la cancha
    date = Column(DateTime, nullable=False)  # Fecha y hora de la reserva
    duration_minutes = Column(Integer, default=60)  # Duración en minutos
    status = Column(String, default="pending")  # pending, confirmed, completed, cancelled, no_show
    confirmed = Column(Boolean, default=False)
    reminder_24h_sent = Column(Boolean, default=False)
    reminder_3h_sent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    notes = Column(Text, nullable=True)
    
    user = relationship("User", back_populates="reservations")


class ConversationState(Base):
    """Estado de conversación con usuarios para manejar flujos"""
    __tablename__ = "conversation_states"
    
    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String, unique=True, index=True, nullable=False)
    state = Column(String, nullable=False)  # waiting_date, waiting_time, waiting_confirmation, etc.
    context = Column(Text, nullable=True)  # JSON con datos temporales
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


def init_db():
    """Inicializar la base de datos creando las tablas"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Obtener sesión de base de datos"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


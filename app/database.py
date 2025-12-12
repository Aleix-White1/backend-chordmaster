from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, ForeignKey, Float, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, timezone
from app.config import DATABASE_URL

# Crear el motor de la base de datos
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Modelo de Usuario
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relación con refresh tokens
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")

# Modelo de Refresh Token
class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(500), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_active = Column(String(10), default="true", nullable=False)
    
    # Relación con usuario
    user = relationship("User", back_populates="refresh_tokens")

# Modelo de Historial de Canciones
class SongHistory(Base):
    __tablename__ = "song_history"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(36), nullable=False, unique=True)  # Campo requerido en la tabla
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(500), nullable=False)
    source = Column(String(50), nullable=False, default="youtube")  # Campo requerido
    youtube_url = Column(String(500), nullable=True)
    tempo_bpm = Column(Float, nullable=True)  # Float en lugar de Integer
    key = Column(String(20), nullable=True)  # Campo original
    key_detected = Column(String(20), nullable=True)  # Campo agregado
    mode_detected = Column(String(20), nullable=True)  # Campo agregado
    beats_per_bar = Column(Integer, nullable=True)  # Campo existente
    chords = Column(JSON, nullable=True)  # Campo original
    chords_json = Column(JSON, nullable=True)  # Campo agregado
    analyzed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relación con usuario
    user = relationship("User")

# Función para obtener la sesión de la base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Crear las tablas
def create_tables():
    Base.metadata.create_all(bind=engine)

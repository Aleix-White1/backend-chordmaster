
import os
from dotenv import load_dotenv

load_dotenv()

# Detectar entorno
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
IS_PRODUCTION = ENVIRONMENT == "production"

# Configuración de base de datos
if IS_PRODUCTION:
    # En producción usar PostgreSQL desde variable de entorno
    DATABASE_URL = os.getenv("DATABASE_URL")
    if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
else:
    # Configuración para desarrollo local (MySQL)
    DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT = os.getenv("DB_PORT", "3306")
    DB_USER = os.getenv("DB_USER", "chorduser")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "chordpass")
    DB_NAME = os.getenv("DB_NAME", "railway")
    DATABASE_URL = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Configuración JWT
JWT_SECRET_KEY = os.getenv("JWT_SECRET", "chordmaster_secret_key_2025_development")

# CORS origins
CORS_ORIGINS = [
    "http://localhost:3000",  # React local
    "http://localhost:3001",  # React alternativo
    "https://chordmaster-frontend.vercel.app",  # Frontend en Vercel
]

# En producción, permitir orígenes específicos desde variables de entorno
if IS_PRODUCTION:
    frontend_url = os.getenv("FRONTEND_URL")
    if frontend_url:
        CORS_ORIGINS.append(frontend_url)
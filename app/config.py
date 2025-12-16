
import os
from dotenv import load_dotenv

load_dotenv()

# Detectar entorno
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
IS_PRODUCTION = ENVIRONMENT == "production"

# Configuración de base de datos
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # Si DATABASE_URL existe, usarla (producción)
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
else:
    # Fallback a configuración local (desarrollo)
    DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT = os.getenv("DB_PORT", "3306")
    DB_USER = os.getenv("DB_USER", "chorduser")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "chordpass")
    DB_NAME = os.getenv("DB_NAME", "railway")
    DATABASE_URL = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    # En producción sin DATABASE_URL, usar SQLite temporal
    if IS_PRODUCTION:
        print("⚠️  DATABASE_URL no configurada en producción, usando SQLite temporal")
        DATABASE_URL = "sqlite:///./chordmaster.db"

# Validar que DATABASE_URL esté configurada
if not DATABASE_URL:
    raise ValueError("No se pudo configurar DATABASE_URL")

# Configuración JWT
JWT_SECRET_KEY = os.getenv("JWT_SECRET", "chordmaster_secret_key_2025_development")

# CORS origins
if IS_PRODUCTION:
    # En producción: orígenes específicos y seguros
    CORS_ORIGINS = [
        "https://chordmaster-frontend.vercel.app",  # Frontend en Vercel
    ]
    # Agregar URL del frontend desde variables de entorno
    frontend_url = os.getenv("FRONTEND_URL")
    if frontend_url:
        CORS_ORIGINS.append(frontend_url)
else:
    # En desarrollo: permitir localhost y redes locales
    CORS_ORIGINS = [
        "http://localhost",       # Localhost sin puerto (importante para emuladores)
        "http://localhost:3000",  # React local
        "http://localhost:3001",  # React alternativo  
        "http://localhost:4200",  # Angular local
        "http://127.0.0.1:3000",  # Localhost explícito
        "http://127.0.0.1:4200",  # Angular localhost explícito
        # Permitir toda la red local para desarrollo y emuladores
        "http://192.168.1.192:4200",  # IP específica del emulador
        "capacitor://localhost",  # Ionic/Capacitor
        "ionic://localhost",      # Ionic
        "http://ionic.local",     # Ionic local
    ]
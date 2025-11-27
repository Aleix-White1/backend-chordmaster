
# Configuración para entorno local (Docker Compose)
DB_HOST = "127.0.0.1"  # Cambia a 'db' si ejecutas la app en Docker
DB_PORT = "3306"
DB_USER = "chorduser"
DB_PASSWORD = "chordpass"
DB_NAME = "railway"

# Clave secreta para JWT (CAMBIAR EN PRODUCCIÓN)
JWT_SECRET_KEY = "chordmaster_secret_key_2025_cambiar_en_produccion"


# Construir la URL de la base de datos para SQLAlchemy
# Usa mysql+mysqlconnector o mysql+pymysql según el paquete instalado
DATABASE_URL = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


# Si prefieres usar PyMySQL, descomenta la siguiente línea y comenta la de arriba:
# DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
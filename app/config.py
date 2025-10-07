# Configuración de la base de datos
# Datos de conexión para sql7.freesqldatabase.com

DB_HOST = "sql7.freesqldatabase.com"
DB_PORT = "3306"
DB_USER = "sql7801600"
DB_PASSWORD = "yUaDeGbc8N"
DB_NAME = "sql7801600"

# Clave secreta para JWT (CAMBIAR EN PRODUCCIÓN)
JWT_SECRET_KEY = "chordmaster_secret_key_2025_cambiar_en_produccion"

# Construir la URL de la base de datos
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

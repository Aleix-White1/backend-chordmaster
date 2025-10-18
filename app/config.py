# Configuración de la base de datos
# Datos de conexión para sql7.freesqldatabase.com


DB_HOST = "hopper.proxy.rlwy.net"
DB_PORT = "42867"
DB_USER = "root"
DB_PASSWORD = "idWkfpovxnqUDKoEMLlEwozwYiUJcTKy"
DB_NAME = "railway"

# Clave secreta para JWT (CAMBIAR EN PRODUCCIÓN)
JWT_SECRET_KEY = "chordmaster_secret_key_2025_cambiar_en_produccion"

# Construir la URL de la base de datos
DATABASE_URL = "mysql+pymysql://root:idWkfpovxnqUDKoEMLlEwozwYiUJcTKy@hopper.proxy.rlwy.net:42867/railway"

# ...existing code...
# DATABASE_URL = "mysql+pymysql://root:idWkfpovxnqUDKoEMLlEwozwYiUJcTKy@127.0.0.1:3306/railway"
# ...existing code...
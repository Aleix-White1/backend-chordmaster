# ChordMaster Backend

API backend para análisis musical automático con detección de acordes, tonalidad y tempo.

## 🎵 Características

- **Análisis de audio**: Detección automática de acordes, tonalidad y tempo
- **Autenticación JWT**: Sistema seguro de usuarios con tokens de acceso y refresh
- **Historial de canciones**: Seguimiento de análisis previos por usuario
- **API RESTful**: Endpoints bien documentados con FastAPI
- **Base de datos MySQL**: Almacenamiento persistente con SQLAlchemy

## 🚀 Instalación

### Prerrequisitos

- Python 3.8+
- Docker y Docker Compose
- pip y virtualenv

### Configuración del entorno

1. **Crear entorno virtual**:
```bash
python -m venv venv
source venv/bin/activate  # En macOS/Linux
# o venv\Scripts\activate en Windows
```

2. **Instalar dependencias**:
```bash
pip install -r requirements.txt
```

3. **Configurar base de datos con Docker**:
```bash
# Iniciar MySQL y Adminer
docker-compose up -d
```

4. **Configurar variables de entorno**:
- Revisar/copiar `.env.db` para credenciales de base de datos
- Adminer disponible en: `http://localhost:8080`

5. **Crear tablas de base de datos**:
```bash
python -c "from app.database import engine, Base; Base.metadata.create_all(bind=engine)"
```

## 🔧 Uso

### Ejecutar el servidor

```bash
uvicorn main:app --reload
```

La API estará disponible en: `http://localhost:8000`

### Documentación de la API

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 📚 Endpoints principales

### Autenticación
- `POST /api/auth/register` - Registrar usuario
- `POST /api/auth/login` - Iniciar sesión
- `POST /api/auth/refresh` - Renovar token
- `DELETE /api/auth/logout` - Cerrar sesión

### Análisis musical
- `POST /api/analyze/link` - Analizar desde URL
- `POST /api/analyze/file` - Analizar archivo de audio
- `GET /api/analyze/history` - Historial de análisis
- `GET /api/analyze/audio/{job_id}` - Obtener audio analizado

## 🗄️ Base de datos

### Configuración de conexión

- **Desde host**: `mysql+mysqlconnector://chorduser:chordpass@127.0.0.1:3306/railway`
- **Desde Docker**: `mysql+mysqlconnector://chorduser:chordpass@db:3306/railway`

### Herramientas de administración

- **Adminer**: `http://localhost:8080`
- **Credenciales**: Definidas en `.env.db`

## 🔒 Seguridad

- Autenticación JWT con tokens de acceso y refresh
- Validación de tokens en endpoints protegidos
- Hashing seguro de contraseñas con bcrypt

## 🛠️ Tecnologías utilizadas

- **FastAPI**: Framework web moderno y rápido
- **SQLAlchemy**: ORM para Python
- **MySQL**: Base de datos relacional
- **librosa**: Análisis de audio y música
- **PyJWT**: Manejo de tokens JWT
- **Docker**: Containerización

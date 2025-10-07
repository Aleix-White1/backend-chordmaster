# Ejemplos de uso de la API

## 1. Registrar un nuevo usuario

### Endpoint: POST /api/auth/register

```json
{
    "name": "Juan Pérez",
    "email": "juan@ejemplo.com",
    "password": "micontraseña123"
}
```

### Respuesta exitosa:
```json
{
    "id": 1,
    "name": "Juan Pérez",
    "email": "juan@ejemplo.com",
    "created_at": "2025-10-06T10:30:00",
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
}
```

### Respuesta de error (email ya existe):
```json
{
    "detail": "El email ya está registrado"
}
```

## 2. Iniciar sesión

### Endpoint: POST /api/auth/login

```json
{
    "email": "juan@ejemplo.com",
    "password": "micontraseña123"
}
```

### Respuesta exitosa:
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
}
```

### Respuesta de error:
```json
{
    "detail": "Email o contraseña incorrectos"
}
```

## Configuración de la base de datos

Antes de usar la API, asegúrate de configurar tu base de datos en `app/config.py`:

```python
DB_HOST = "sql7.freesqldatabase.com"
DB_PORT = "3306"
DB_USER = "tu_usuario_real"
DB_PASSWORD = "tu_contraseña_real"
DB_NAME = "tu_base_de_datos_real"
```

## Ejecutar el servidor

```bash
uvicorn main:app --reload
```

La API estará disponible en: http://localhost:8000

Documentación automática: http://localhost:8000/docs

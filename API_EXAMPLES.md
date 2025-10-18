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
    "refresh_token": "mF_9.B5f-4.1JqM...",
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
    "refresh_token": "mF_9.B5f-4.1JqM...",
    "token_type": "bearer"
}
```

### Respuesta de error:
```json
{
    "detail": "Email o contraseña incorrectos"
}
```

## 3. Renovar token de acceso

### Endpoint: POST /api/auth/refresh

```json
{
    "refresh_token": "mF_9.B5f-4.1JqM..."
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
    "detail": "Refresh token inválido o expirado"
}
```

## 4. Cerrar sesión

### Endpoint: POST /api/auth/logout

```json
{
    "refresh_token": "mF_9.B5f-4.1JqM..."
}
```

### Respuesta exitosa:
```json
{
    "message": "Logout exitoso"
}
```

## 5. Cerrar sesión en todos los dispositivos

### Endpoint: POST /api/auth/logout-all

```json
{
    "refresh_token": "mF_9.B5f-4.1JqM..."
}
```

### Respuesta exitosa:
```json
{
    "message": "Logout exitoso en todos los dispositivos"
}
```

## 6. Crear tablas (solo desarrollo)

### Endpoint: POST /api/auth/create-tables

Sin parámetros necesarios.

### Respuesta exitosa:
```json
{
    "message": "Tablas creadas exitosamente"
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

# 🚀 Deploy ChordMaster Backend

## Railway (Recomendado)

### 1. Setup inicial
```bash
npm install -g @railway/cli
railway login
```

### 2. Deploy
```bash
railway init
railway add postgresql
railway up
```

### 3. Variables de entorno en Railway Dashboard
```
ENVIRONMENT=production
JWT_SECRET=tu_jwt_secret_super_seguro_cambiar_aqui
FRONTEND_URL=https://tu-frontend.vercel.app
```

### 4. Inicializar BD (una sola vez)
En Railway Terminal ejecutar:
```bash
python init_db.py
```

---

## Render

### 1. Conectar repositorio GitHub a Render
### 2. Configurar como Web Service
### 3. Agregar PostgreSQL Database (gratis)
### 4. Variables de entorno:
```
ENVIRONMENT=production
JWT_SECRET=tu_jwt_secret_super_seguro
DATABASE_URL=postgresql://... (auto desde Render)
FRONTEND_URL=https://tu-frontend.vercel.app
```

---

## Heroku

### 1. Setup
```bash
heroku create chordmaster-backend
heroku addons:create heroku-postgresql:mini
```

### 2. Variables de entorno
```bash
heroku config:set ENVIRONMENT=production
heroku config:set JWT_SECRET=tu_jwt_secret_super_seguro
heroku config:set FRONTEND_URL=https://tu-frontend.vercel.app
```

### 3. Deploy
```bash
git push heroku main
```

### 4. Inicializar BD
```bash
heroku run python init_db.py
```

---

## Variables de entorno requeridas para producción

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `ENVIRONMENT` | Entorno de ejecución | `production` |
| `DATABASE_URL` | URL de base de datos | `postgresql://user:pass@host:5432/db` |
| `JWT_SECRET` | Clave secreta para JWT | `mi_clave_super_segura_2025` |
| `FRONTEND_URL` | URL del frontend | `https://mi-app.vercel.app` |

## ✅ Checklist pre-deploy

- [ ] Variables de entorno configuradas
- [ ] Base de datos PostgreSQL creada
- [ ] Frontend URL agregada a CORS_ORIGINS
- [ ] JWT_SECRET cambiada por una segura
- [ ] init_db.py ejecutado para crear tablas
- [ ] Testear endpoints principales

## 🔗 URLs después del deploy

- **API Base**: `https://tu-app.railway.app`
- **Health Check**: `https://tu-app.railway.app/`
- **Docs**: Solo en desarrollo (`/docs`, `/redoc`)
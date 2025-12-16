from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.auth_routes import router as auth_router
from app.analize_routes import router as analize_router
from app.config import CORS_ORIGINS, IS_PRODUCTION

app = FastAPI(
    title="ChordMaster Backend", 
    version="1.0.0",
    docs_url="/docs" if not IS_PRODUCTION else None,  # Ocultar docs en producción
    redoc_url="/redoc" if not IS_PRODUCTION else None
)

# Configuración CORS más permisiva en desarrollo
if IS_PRODUCTION:
    cors_origins = CORS_ORIGINS
else:
    # En desarrollo, usar wildcard para máxima compatibilidad
    cors_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

@app.options("/{full_path:path}")
async def handle_options(request: Request, full_path: str):
    """Manejar todas las solicitudes OPTIONS para CORS preflight"""
    origin = request.headers.get("origin", "*")
    
    # En desarrollo: permitir cualquier origin
    # En producción: verificar que esté en la lista
    if IS_PRODUCTION:
        allowed_origin = origin if origin in CORS_ORIGINS else "null"
    else:
        allowed_origin = origin  # Permisivo en desarrollo
    
    return JSONResponse(
        content={},
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": allowed_origin,
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, Accept, Origin, X-Requested-With",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Max-Age": "86400"
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Error interno del servidor"},
        headers={"Access-Control-Allow-Origin": "*"}
    )

app.include_router(auth_router, prefix="/api/auth", tags=["authentication"])
app.include_router(analize_router, prefix="/api/analyze", tags=["analyze"])

@app.get("/")
async def root():
    return {"message": "ChordMaster Backend API", "version": "1.0.0"}


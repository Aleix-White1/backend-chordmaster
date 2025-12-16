from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.auth_routes import router as auth_router
from app.analize_routes import router as analize_router
from app.config import CORS_ORIGINS, IS_PRODUCTION
from app.database import create_tables
import os

app = FastAPI(
    title="ChordMaster Backend", 
    version="1.0.0",
    docs_url="/docs" if not IS_PRODUCTION else None,  # Ocultar docs en producción
    redoc_url="/redoc" if not IS_PRODUCTION else None
)

# Inicializar base de datos y directorio jobs al arrancar
@app.on_event("startup")
async def startup_event():
    # Crear tablas de base de datos
    create_tables()
    
    # Crear directorio jobs si no existe
    os.makedirs("jobs", exist_ok=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
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


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.auth_routes import router as auth_router
from app.analize_routes import router as analize_router
from app.config import CORS_ORIGINS, IS_PRODUCTION

app = FastAPI(
    title="ChordMaster Backend", 
    version="1.0.0",
    docs_url="/docs" if not IS_PRODUCTION else None,  # Ocultar docs en producción
    redoc_url="/redoc" if not IS_PRODUCTION else None
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/auth", tags=["authentication"])
app.include_router(analize_router, prefix="/api/analyze", tags=["analyze"])

@app.get("/")
async def root():
    return {"message": "ChordMaster Backend API", "version": "1.0.0"}


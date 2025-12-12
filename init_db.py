#!/usr/bin/env python3
"""
Script para inicializar la base de datos en producción
"""
import sys
import os

# Agregar el directorio del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, Base
from app.config import DATABASE_URL, IS_PRODUCTION

def init_db():
    """Inicializar base de datos creando todas las tablas"""
    try:
        print(f"Inicializando base de datos...")
        print(f"Entorno: {'Producción' if IS_PRODUCTION else 'Desarrollo'}")
        print(f"Database URL: {DATABASE_URL[:50]}..." if DATABASE_URL else "No DATABASE_URL configurada")
        
        # Crear todas las tablas
        Base.metadata.create_all(bind=engine)
        print("✅ Tablas de base de datos creadas exitosamente")
        
    except Exception as e:
        print(f"❌ Error inicializando base de datos: {e}")
        sys.exit(1)

if __name__ == "__main__":
    init_db()
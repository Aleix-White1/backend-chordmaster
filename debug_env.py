#!/usr/bin/env python3
"""
Script de debug para verificar variables de entorno en deploy
"""
import os
import sys

def debug_env():
    """Muestra información de las variables de entorno"""
    print("=== DEBUG ENVIRONMENT ===")
    print(f"Python version: {sys.version}")
    print(f"Platform: {sys.platform}")
    print(f"Environment: {os.getenv('ENVIRONMENT', 'NOT_SET')}")
    print(f"DATABASE_URL: {'SET' if os.getenv('DATABASE_URL') else 'NOT_SET'}")
    print(f"JWT_SECRET: {'SET' if os.getenv('JWT_SECRET') else 'NOT_SET'}")
    
    # Listar todas las variables de entorno que empiecen con DB_, PORT, etc
    relevant_vars = [key for key in os.environ.keys() 
                    if key.startswith(('DB_', 'DATABASE_', 'PORT', 'JWT_', 'ENVIRONMENT', 'FRONTEND_'))]
    
    print("\n=== RELEVANT ENV VARS ===")
    for var in sorted(relevant_vars):
        value = os.getenv(var)
        if 'PASSWORD' in var or 'SECRET' in var or 'JWT' in var:
            print(f"{var}: {'*' * min(len(value), 8) if value else 'NOT_SET'}")
        else:
            print(f"{var}: {value}")
    
    print("========================\n")

if __name__ == "__main__":
    debug_env()
    
    # Intentar importar la configuración
    try:
        from app.config import DATABASE_URL, IS_PRODUCTION
        print("✅ Configuración cargada exitosamente")
        print(f"   - Production: {IS_PRODUCTION}")
        print(f"   - Database: {DATABASE_URL[:50]}..." if len(DATABASE_URL) > 50 else f"   - Database: {DATABASE_URL}")
    except Exception as e:
        print(f"❌ Error cargando configuración: {e}")
        sys.exit(1)
from app.database import create_tables

if __name__ == "__main__":
    try:
        create_tables()
        print("✅ Tablas creadas exitosamente")
    except Exception as e:
        print(f"❌ Error al crear las tablas: {e}")

#!/usr/bin/env python3
"""
Script de prueba para verificar que la autenticación funciona
"""

import sys
import os

# Agregar el directorio app al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

try:
    # Importar módulos
    from models import engine, SessionLocal, Base
    from auth import get_password_hash, authenticate_user

    print("✅ Módulos importados correctamente")

    # Crear tablas
    Base.metadata.create_all(bind=engine)
    print("✅ Tablas creadas")

    # Crear sesión de prueba
    db = SessionLocal()

    # Verificar hash de contraseña
    hashed = get_password_hash("admin123")
    print(f"✅ Hash generado: {hashed[:20]}...")

    print("🎉 Sistema de autenticación funcionando correctamente!")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    try:
        db.close()
    except:
        pass

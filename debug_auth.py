#!/usr/bin/env python3
"""
Script de debug para verificar autenticación
"""

import sys
import os
import hashlib

# Cambiar al directorio app
os.chdir(os.path.join(os.path.dirname(__file__), 'app'))

# Agregar el directorio actual al path
sys.path.insert(0, '.')

try:
    from models import engine, SessionLocal, Base
    from models.user import User

    print("Verificando autenticacion...")

    # Crear sesión
    db = SessionLocal()

    # Verificar si existe el superadmin
    superadmin = db.query(User).filter(User.nombre_usuario == "superadmin").first()

    if superadmin:
        print(f"Usuario encontrado: {superadmin.nombre_usuario}")
        print(f"Hash almacenado: {superadmin.contraseña[:32]}...")
        print(f"Rol: {superadmin.rol}")
        print(f"Estado: {superadmin.estado}")

        # Probar hash de "admin123"
        test_hash = hashlib.sha256("admin123".encode()).hexdigest()
        print(f"Hash esperado: {test_hash[:32]}...")

        # Comparar
        if superadmin.contraseña == test_hash:
            print("Hash coincide - autenticacion deberia funcionar")
        else:
            print("Hash NO coincide - problema de autenticacion")
            print(f"Almacenado: {superadmin.contraseña}")
            print(f"Esperado:   {test_hash}")
    else:
        print("Usuario 'superadmin' no encontrado en la base de datos")

    # Verificar otros usuarios
    all_users = db.query(User).all()
    print(f"\nTotal de usuarios en BD: {len(all_users)}")
    for user in all_users:
        print(f"  - {user.nombre_usuario} ({user.rol}) - Estado: {user.estado}")

    # Probar autenticación manual con diferentes usuarios
    print("\nProbando autenticacion manual...")

    test_cases = [
        ("superadmin", "admin123"),
        ("admin_test", "admin123"),
        ("test_admin", "admin123"),
        ("juan_admin", "admin123"),
    ]

    from auth import authenticate_user
    for username, password in test_cases:
        test_user = authenticate_user(db, username, password)
        if test_user:
            print(f"Autenticacion {username}: EXITOSA (rol: {test_user.rol})")
        else:
            print(f"Autenticacion {username}: FALLIDA")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    try:
        db.close()
    except:
        pass

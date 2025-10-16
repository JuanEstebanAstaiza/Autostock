#!/usr/bin/env python3
"""
Script para probar las funciones de reset de contraseña
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.models import SessionLocal, User, Negocio
from app.auth import generate_random_password, get_password_hash

def test_password_functions():
    """Probar las funciones de generación y hash de contraseñas"""
    print("🧪 Probando funciones de contraseña...")

    # Probar generación de contraseña
    password1 = generate_random_password()
    password2 = generate_random_password()

    print(f"✅ Contraseña 1: {password1} (longitud: {len(password1)})")
    print(f"✅ Contraseña 2: {password2} (longitud: {len(password2)})")

    # Verificar que sean diferentes
    assert password1 != password2, "Las contraseñas deberían ser diferentes"
    print("✅ Las contraseñas generadas son únicas")

    # Probar hash
    hash1 = get_password_hash(password1)
    hash2 = get_password_hash(password2)

    print(f"✅ Hash 1: {hash1}")
    print(f"✅ Hash 2: {hash2}")

    # Verificar que los hashes sean diferentes
    assert hash1 != hash2, "Los hashes deberían ser diferentes"
    print("✅ Los hashes son únicos")

    # Verificar formato
    assert len(hash1) == 64, "El hash debería tener 64 caracteres (SHA256)"
    print("✅ Formato de hash correcto (SHA256)")

def test_database_users():
    """Verificar que hay usuarios en la base de datos para probar"""
    db = SessionLocal()

    try:
        # Contar usuarios por tipo
        total_users = db.query(User).count()
        admins = db.query(User).filter(User.rol == "admin").count()
        vendedores = db.query(User).filter(User.rol == "vendedor").count()

        print("\n📊 Usuarios en base de datos:")
        print(f"   Total: {total_users}")
        print(f"   Administradores: {admins}")
        print(f"   Vendedores: {vendedores}")

        if total_users > 0:
            print("✅ Hay usuarios para probar")
        else:
            print("⚠️ No hay usuarios en la base de datos")

        # Mostrar algunos usuarios de ejemplo
        if admins > 0:
            admin = db.query(User).filter(User.rol == "admin").first()
            print(f"📋 Admin de ejemplo: {admin.nombre_usuario} (ID: {admin.id})")

        if vendedores > 0:
            vendedor = db.query(User).filter(User.rol == "vendedor").first()
            print(f"📋 Vendedor de ejemplo: {vendedor.nombre_usuario} (ID: {vendedor.id})")

    except Exception as e:
        print(f"❌ Error al consultar usuarios: {e}")
    finally:
        db.close()

def test_endpoints():
    """Probar que los endpoints están definidos correctamente"""
    print("\n🔗 Verificando endpoints:")

    # Verificar que los endpoints existen en los archivos
    with open('app/routers/superadmin.py', 'r') as f:
        superadmin_content = f.read()
        if '@router.post("/reset-password/{user_id}")' in superadmin_content:
            print("✅ Endpoint SuperAdmin: /superadmin/reset-password/{user_id}")
        else:
            print("❌ Endpoint SuperAdmin no encontrado")

    with open('app/routers/admin_negocio.py', 'r') as f:
        admin_content = f.read()
        if '@router.post("/reset-password/{user_id}")' in admin_content:
            print("✅ Endpoint Admin Negocio: /negocio/reset-password/{user_id}")
        else:
            print("❌ Endpoint Admin Negocio no encontrado")

if __name__ == "__main__":
    print("🔐 Probando sistema de reset de contraseñas...")
    test_password_functions()
    test_database_users()
    test_endpoints()
    print("\n✅ Pruebas completadas")
    print("\n📝 Para probar manualmente:")
    print("   1. SuperAdmin: Ve a /superadmin/negocios/[id] y busca botón 'Resetear Contraseña'")
    print("   2. Admin Negocio: Ve a /negocio/usuarios y busca botón 'Reset Contraseña'")

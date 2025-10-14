#!/usr/bin/env python3
"""
Script para inicializar la base de datos de Autostock.
Crea todas las tablas y datos iniciales.
"""

from models import Base, engine, SessionLocal
from models.user import User
from models.plan import Plan
import hashlib

def init_database():
    """Inicializar la base de datos creando todas las tablas"""
    print("Creando tablas en la base de datos...")
    Base.metadata.create_all(bind=engine)
    print("✓ Tablas creadas exitosamente")

def create_initial_data():
    """Crear datos iniciales: usuario superadmin y planes"""
    db = SessionLocal()
    try:
        # Verificar si ya existe un superadmin
        superadmin = db.query(User).filter(User.rol == "superadmin").first()
        if not superadmin:
            # Crear usuario superadmin
            hashed_password = hashlib.sha256("admin123".encode()).hexdigest()
            superadmin = User(
                nombre_usuario="superadmin",
                contraseña=hashed_password,
                rol="superadmin",
                estado="activo"
            )
            db.add(superadmin)
            print("✓ Usuario superadmin creado (usuario: superadmin, contraseña: admin123)")

        # Verificar si ya existen planes
        existing_plans = db.query(Plan).count()
        if existing_plans == 0:
            # Crear planes iniciales
            planes = [
                Plan(
                    nombre_plan="Básico",
                    descripcion="Plan básico para pequeños negocios de montallantas",
                    precio=29.99,
                    duracion_dias=30
                ),
                Plan(
                    nombre_plan="Profesional",
                    descripcion="Plan profesional con reportes avanzados",
                    precio=59.99,
                    duracion_dias=30
                ),
                Plan(
                    nombre_plan="Premium",
                    descripcion="Plan completo con soporte prioritario",
                    precio=99.99,
                    duracion_dias=30
                )
            ]

            for plan in planes:
                db.add(plan)

            print("✓ Planes iniciales creados")

        db.commit()
        print("✓ Datos iniciales insertados correctamente")

    except Exception as e:
        db.rollback()
        print(f"✗ Error al crear datos iniciales: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("Inicializando base de datos de Autostock...")
    init_database()
    create_initial_data()
    print("🎉 Base de datos inicializada correctamente!")

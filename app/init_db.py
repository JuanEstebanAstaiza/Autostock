#!/usr/bin/env python3
"""
Script para inicializar la base de datos de Autostock.
Crea todas las tablas y datos iniciales.
"""

import os
import sys
from models import Base, engine, SessionLocal
from models.user import User
from models.plan import Plan
import hashlib

def ensure_database_directory():
    """Asegurar que el directorio database existe"""
    database_dir = os.path.join(os.getcwd(), "database")
    if not os.path.exists(database_dir):
        try:
            os.makedirs(database_dir)
            print(f"[OK] Directorio database creado: {database_dir}")
        except Exception as e:
            print(f"[ERROR] No se pudo crear el directorio database: {e}")
            return False
    return True

def init_database():
    """Inicializar la base de datos creando todas las tablas"""
    print("Creando tablas en la base de datos...")

    try:
        Base.metadata.create_all(bind=engine)
        print("[OK] Tablas creadas exitosamente")
        return True
    except Exception as e:
        print(f"[ERROR] Error al crear tablas: {e}")
        return False

def create_initial_data():
    """Crear datos iniciales: usuario superadmin y planes"""
    try:
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
                print("[OK] Usuario superadmin creado (usuario: superadmin, contraseña: admin123)")

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

                print("[OK] Planes iniciales creados")

            db.commit()
            print("[OK] Datos iniciales insertados correctamente")
            return True

        except Exception as e:
            db.rollback()
            print(f"[ERROR] Error al crear datos iniciales: {e}")
            return False
        finally:
            db.close()

    except Exception as e:
        print(f"[ERROR] Error al conectar con la base de datos: {e}")
        return False

if __name__ == "__main__":
    print("Inicializando base de datos de Autostock...")

    # Asegurar que el directorio database existe
    if not ensure_database_directory():
        print("[ERROR] No se puede continuar sin el directorio database")
        sys.exit(1)

    # Inicializar base de datos
    if not init_database():
        print("[ERROR] Fallo al inicializar la base de datos")
        sys.exit(1)

    # Crear datos iniciales
    if not create_initial_data():
        print("[ERROR] Fallo al crear los datos iniciales")
        sys.exit(1)

    print("EXITO: Base de datos inicializada correctamente!")

#!/usr/bin/env python3
"""
Script para probar el control de popups de notificaciones
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.models import SessionLocal, User, Negocio, Producto, Venta, Notificacion
import time

def test_popup_control():
    """Probar que los popups se controlan correctamente"""
    db = SessionLocal()

    try:
        # Obtener datos de prueba
        negocio = db.query(Negocio).first()
        if not negocio:
            print("❌ No hay negocios en la base de datos")
            return

        usuario = db.query(User).filter(User.negocio_id == negocio.id, User.rol == "vendedor").first()
        if not usuario:
            print("❌ No hay vendedores en el negocio")
            return

        producto = db.query(Producto).filter(Producto.negocio_id == negocio.id).first()
        if not producto:
            print("❌ No hay productos en el negocio")
            return

        print("🔔 Probando control de popups...")

        # Crear una notificación de prueba que NO esté leída
        mensaje = f"{usuario.nombre_usuario} vendió 2 {producto.nombre}"
        notificacion = Notificacion(
            negocio_id=negocio.id,
            vendedor_id=usuario.id,
            producto_id=producto.id,
            cantidad_vendida=2,
            mensaje=mensaje,
            leida=False  # No leída para que aparezca en popups
        )
        db.add(notificacion)
        db.commit()

        print(f"✅ Notificación de prueba creada: {notificacion.mensaje}")
        print(f"   ID: {notificacion.id}")
        print(f"   Leída: {notificacion.leida}")
        print()
        print("📋 Sistema de control de popups:")
        print("   • Máximo 3 apariciones por notificación")
        print("   • Intervalos de 10-20 segundos entre apariciones")
        print("   • Se detiene cuando se marca como leída")
        print()
        print("🧪 Para probar:")
        print("   1. Ve al dashboard (/negocio/dashboard)")
        print("   2. Espera los popups (máximo 3 veces)")
        print("   3. Ve a notificaciones (/negocio/notificaciones)")
        print("   4. Marca como leída - debería detener los popups")
        print()
        print("🔍 Revisa la consola del navegador para logs de control de popups")

    except Exception as e:
        print(f"❌ Error durante la creación de pruebas: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("🎯 Probando sistema de control de popups de notificaciones...")
    test_popup_control()
    print("✅ Prueba preparada")

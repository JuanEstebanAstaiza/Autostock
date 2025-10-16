#!/usr/bin/env python3
"""
Script para probar las correcciones de navegación en las notificaciones
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.models import SessionLocal, User, Negocio, Producto, Venta, Notificacion
import time

def create_test_notifications():
    """Crear notificaciones de prueba para verificar la navegación"""
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

        print(f"📊 Creando notificaciones de prueba para:")
        print(f"   Negocio: {negocio.nombre_negocio}")
        print(f"   Vendedor: {usuario.nombre_usuario}")
        print(f"   Producto: {producto.nombre}")

        # Crear varias notificaciones de prueba
        notifications_data = [
            {"cantidad": 3, "leida": False},
            {"cantidad": 1, "leida": False},
            {"cantidad": 5, "leida": True},
            {"cantidad": 2, "leida": True},
        ]

        for data in notifications_data:
            # Crear venta
            venta = Venta(
                negocio_id=negocio.id,
                producto_id=producto.id,
                vendedor_id=usuario.id,
                cantidad_vendida=data["cantidad"],
                valor_total=producto.precio * data["cantidad"]
            )
            db.add(venta)

            # Crear notificación
            mensaje = f"{usuario.nombre_usuario} vendió {data['cantidad']} {producto.nombre}"
            notificacion = Notificacion(
                negocio_id=negocio.id,
                vendedor_id=usuario.id,
                producto_id=producto.id,
                cantidad_vendida=data["cantidad"],
                mensaje=mensaje,
                leida=data["leida"]
            )
            db.add(notificacion)

            # Pequeño delay para que las fechas sean diferentes
            time.sleep(0.1)

        db.commit()

        # Contar notificaciones
        total_notifs = db.query(Notificacion).filter(Notificacion.negocio_id == negocio.id).count()
        unread_notifs = db.query(Notificacion).filter(
            Notificacion.negocio_id == negocio.id,
            Notificacion.leida == False
        ).count()

        print(f"✅ Notificaciones creadas:")
        print(f"   Total: {total_notifs}")
        print(f"   No leídas: {unread_notifs}")

        # Mostrar las últimas 3 notificaciones
        recientes = db.query(Notificacion).filter(
            Notificacion.negocio_id == negocio.id
        ).order_by(Notificacion.fecha_creacion.desc()).limit(3).all()

        print("📋 Últimas notificaciones:")
        for notif in recientes:
            status = "✅ Leída" if notif.leida else "🔔 No leída"
            print(f"   {notif.mensaje} - {status}")

    except Exception as e:
        print(f"❌ Error durante la creación de pruebas: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("🔔 Creando notificaciones de prueba para verificar navegación...")
    create_test_notifications()
    print("✅ Prueba completada")
    print("📱 Ahora puedes verificar la navegación en /negocio/notificaciones")

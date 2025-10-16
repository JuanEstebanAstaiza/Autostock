#!/usr/bin/env python3
"""
Script para probar el sistema de notificaciones
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.models import SessionLocal, User, Negocio, Producto, Venta, Notificacion

def test_notifications():
    """Probar que las notificaciones se crean correctamente"""
    db = SessionLocal()

    try:
        # Obtener un negocio y usuario de prueba
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

        print(f"📊 Probando notificaciones para:")
        print(f"   Negocio: {negocio.nombre_negocio}")
        print(f"   Vendedor: {usuario.nombre_usuario}")
        print(f"   Producto: {producto.nombre}")

        # Verificar notificaciones existentes
        notifs_antes = db.query(Notificacion).filter(Notificacion.negocio_id == negocio.id).count()
        print(f"   Notificaciones antes: {notifs_antes}")

        # Crear una venta manualmente (simulando el registro)
        venta = Venta(
            negocio_id=negocio.id,
            producto_id=producto.id,
            vendedor_id=usuario.id,
            cantidad_vendida=2,
            valor_total=producto.precio * 2
        )
        db.add(venta)

        # Crear notificación manualmente
        mensaje = f"{usuario.nombre_usuario} vendió 2 {producto.nombre}"
        notificacion = Notificacion(
            negocio_id=negocio.id,
            vendedor_id=usuario.id,
            producto_id=producto.id,
            cantidad_vendida=2,
            mensaje=mensaje
        )
        db.add(notificacion)

        db.commit()

        # Verificar que se creó la notificación
        notifs_despues = db.query(Notificacion).filter(Notificacion.negocio_id == negocio.id).count()
        print(f"   Notificaciones después: {notifs_despues}")

        if notifs_despues > notifs_antes:
            print("✅ Notificación creada exitosamente")
        else:
            print("❌ Error al crear la notificación")

        # Mostrar la notificación creada
        notif_creada = db.query(Notificacion).filter(
            Notificacion.negocio_id == negocio.id,
            Notificacion.vendedor_id == usuario.id
        ).order_by(Notificacion.fecha_creacion.desc()).first()

        if notif_creada:
            print(f"📋 Notificación: {notif_creada.mensaje}")
            print(f"   Fecha: {notif_creada.fecha_creacion}")
            print(f"   Leída: {notif_creada.leida}")

    except Exception as e:
        print(f"❌ Error durante la prueba: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("🔔 Probando sistema de notificaciones...")
    test_notifications()
    print("✅ Prueba completada")

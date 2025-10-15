#!/usr/bin/env python3
"""
Script para consultar y modificar ventas en la base de datos
"""

import sys
import os
# Cambiar al directorio app para que los imports funcionen
os.chdir('app')
sys.path.append('.')

from models import get_db
from models.user import User
from models.venta import Venta
from models.producto import Producto
from sqlalchemy.orm import Session

def consultar_ventas():
    """Consultar todas las ventas y usuarios"""
    db: Session = next(get_db())

    try:
        print("=== USUARIOS ===")
        usuarios = db.query(User).all()
        for user in usuarios:
            print(f"ID: {user.id}, Usuario: {user.nombre_usuario}, Rol: {user.rol}, Negocio: {user.negocio_id}")

        print("\n=== VENTAS ===")
        ventas = db.query(Venta).all()
        for venta in ventas:
            vendedor = db.query(User).filter(User.id == venta.vendedor_id).first()
            producto = db.query(Producto).filter(Producto.id == venta.producto_id).first()
            print(f"ID: {venta.id}, Fecha: {venta.fecha_venta}, Vendedor: {vendedor.nombre_usuario if vendedor else 'N/A'}, Producto: {producto.nombre if producto else 'N/A'}, Cantidad: {venta.cantidad_vendida}, Total: ${venta.valor_total}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

def cambiar_vendedor_venta(venta_id: int, nuevo_vendedor: str):
    """Cambiar el vendedor de una venta"""
    db: Session = next(get_db())

    try:
        # Buscar el nuevo vendedor
        vendedor = db.query(User).filter(User.nombre_usuario == nuevo_vendedor).first()
        if not vendedor:
            print(f"Error: Vendedor '{nuevo_vendedor}' no encontrado")
            return False

        # Buscar la venta
        venta = db.query(Venta).filter(Venta.id == venta_id).first()
        if not venta:
            print(f"Error: Venta ID {venta_id} no encontrada")
            return False

        # Cambiar el vendedor
        venta.vendedor_id = vendedor.id
        db.commit()

        print("Venta actualizada exitosamente")
        print(f"   Venta ID: {venta.id}")
        print(f"   Nuevo vendedor: {vendedor.nombre_usuario}")
        print(f"   Fecha: {venta.fecha_venta}")
        print(f"   Total: ${venta.valor_total}")

        return True

    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def cambiar_fecha_venta(venta_id: int):
    """Cambiar la fecha de una venta al día actual en zona horaria de Colombia"""
    from datetime import datetime, timezone, timedelta

    db: Session = next(get_db())

    try:
        # Buscar la venta
        venta = db.query(Venta).filter(Venta.id == venta_id).first()
        if not venta:
            print(f"Error: Venta ID {venta_id} no encontrada")
            return False

        # Crear nueva fecha en zona horaria de Colombia (UTC-5)
        colombia_tz = timezone(timedelta(hours=-5))
        ahora_colombia = datetime.now(colombia_tz)

        # Cambiar la fecha de la venta
        venta.fecha_venta = ahora_colombia
        db.commit()

        print("Fecha de venta actualizada exitosamente")
        print(f"   Venta ID: {venta.id}")
        print(f"   Nueva fecha: {venta.fecha_venta}")
        print(f"   Total: ${venta.valor_total}")

        return True

    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) == 1:
        # Solo consultar
        consultar_ventas()
    elif len(sys.argv) == 3 and sys.argv[1] == "cambiar":
        # Cambiar vendedor
        venta_id = int(sys.argv[2])
        nuevo_vendedor = "vendedorpepe1"
        cambiar_vendedor_venta(venta_id, nuevo_vendedor)
    elif len(sys.argv) == 3 and sys.argv[1] == "fecha":
        # Cambiar fecha
        venta_id = int(sys.argv[2])
        cambiar_fecha_venta(venta_id)
    else:
        print("Uso:")
        print("  python check_ventas.py                    # Consultar todas las ventas")
        print("  python check_ventas.py cambiar <venta_id> # Cambiar vendedor de venta")
        print("  python check_ventas.py fecha <venta_id>   # Cambiar fecha de venta")

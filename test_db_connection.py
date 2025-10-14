#!/usr/bin/env python3
"""
Script para probar la conexión a la base de datos y verificar que las consultas funcionan
"""

import sys
import os

# Agregar el directorio app al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from models import engine, SessionLocal, Venta, Producto, User, Negocio
from sqlalchemy import func, desc, text
from datetime import datetime, timedelta

def test_db_connection():
    """Prueba básica de conexión a la base de datos"""
    print("Probando conexión a la base de datos...")

    try:
        # Crear sesión
        db = SessionLocal()

        # Verificar que podemos hacer una consulta básica
        result = db.execute(text("SELECT 1")).fetchone()
        print(f"Conexion exitosa: SELECT 1 = {result[0]}")

        # Contar registros en cada tabla
        ventas_count = db.query(func.count(Venta.id)).scalar()
        productos_count = db.query(func.count(Producto.id)).scalar()
        usuarios_count = db.query(func.count(User.id)).scalar()
        negocios_count = db.query(func.count(Negocio.id)).scalar()

        print("Registros en la base de datos:")
        print(f"   - Ventas: {ventas_count}")
        print(f"   - Productos: {productos_count}")
        print(f"   - Usuarios: {usuarios_count}")
        print(f"   - Negocios: {negocios_count}")

        # Verificar ventas recientes (últimas 24 horas)
        fecha_limite = datetime.now() - timedelta(hours=24)
        ventas_recientes = db.query(func.count(Venta.id)).filter(
            Venta.fecha_venta >= fecha_limite
        ).scalar()

        print(f"Ventas en las ultimas 24 horas: {ventas_recientes}")

        # Mostrar fecha de la venta más reciente
        venta_reciente = db.query(Venta.fecha_venta).order_by(desc(Venta.fecha_venta)).first()
        if venta_reciente:
            print(f"Fecha de la venta mas reciente: {venta_reciente.fecha_venta}")

        # Probar consulta de KPIs (similar a la que usamos en el endpoint)
        now = datetime.now()
        fecha_inicio = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        fecha_inicio_date = fecha_inicio.date()
        fecha_fin_date = now.date()

        print(f"Fecha actual: {now}")
        print(f"Fecha inicio mes: {fecha_inicio}")
        print(f"Fecha inicio date: {fecha_inicio_date}")
        print(f"Fecha fin date: {fecha_fin_date}")

        # Consulta original (problemática)
        total_ventas_original = db.query(func.count(Venta.id)).filter(
            Venta.fecha_venta >= fecha_inicio,
            Venta.fecha_venta <= now
        ).scalar() or 0

        # Consulta corregida con func.date()
        total_ventas_corregida = db.query(func.count(Venta.id)).filter(
            func.date(Venta.fecha_venta) >= fecha_inicio_date,
            func.date(Venta.fecha_venta) <= fecha_fin_date
        ).scalar() or 0

        total_ingresos_corregida = db.query(func.sum(Venta.valor_total)).filter(
            func.date(Venta.fecha_venta) >= fecha_inicio_date,
            func.date(Venta.fecha_venta) <= fecha_fin_date
        ).scalar() or 0.0

        print("KPIs del mes actual:")
        print(f"   - Total ventas (original): {total_ventas_original}")
        print(f"   - Total ventas (corregida): {total_ventas_corregida}")
        print(f"   - Total ingresos (corregida): ${total_ingresos_corregida:.2f}")

        # Verificar todas las ventas del mes actual usando strftime
        ventas_mes_strftime = db.query(
            func.strftime('%Y-%m', Venta.fecha_venta).label('mes'),
            func.count(Venta.id).label('ventas')
        ).filter(
            func.strftime('%Y-%m', Venta.fecha_venta) == '2025-10'
        ).group_by(func.strftime('%Y-%m', Venta.fecha_venta)).all()

        print(f"   - Ventas del mes 2025-10 (strftime): {ventas_mes_strftime}")

        # Probar todas las ventas sin filtro
        todas_las_ventas = db.query(func.count(Venta.id)).scalar() or 0
        print(f"   - Todas las ventas en BD: {todas_las_ventas}")

        # Probar consulta de tendencias mensuales
        fecha_limite_mensual = now - timedelta(days=365)

        tendencias_raw = db.query(
            func.strftime('%Y-%m', Venta.fecha_venta).label('mes'),
            func.count(Venta.id).label('ventas'),
            func.sum(Venta.valor_total).label('ingresos'),
            func.sum(Venta.cantidad_vendida).label('productos')
        ).filter(
            Venta.fecha_venta >= fecha_limite_mensual
        ).group_by(func.strftime('%Y-%m', Venta.fecha_venta)).order_by('mes').all()

        print(f"Tendencias mensuales encontradas: {len(tendencias_raw)} meses")

        # Mostrar las últimas tendencias
        for row in tendencias_raw[-3:]:  # Últimos 3 meses
            print(f"   - {row.mes}: {row.ventas} ventas, ${row.ingresos:.2f} ingresos")

        db.close()
        print("Todas las pruebas pasaron exitosamente!")

    except Exception as e:
        print(f"Error en la base de datos: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True

if __name__ == "__main__":
    success = test_db_connection()
    sys.exit(0 if success else 1)

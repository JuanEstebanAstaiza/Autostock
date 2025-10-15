"""
Router del SuperAdministrador para Autostock
Gestiona negocios, planes de suscripción y métricas globales
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Form, File, UploadFile
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List
import os
import csv
import json
from datetime import datetime, timedelta

from models import get_db
from auth import require_superadmin_from_cookie, get_password_hash
from models.user import User
from models.negocio import Negocio
from models.plan import Plan
from models.producto import Producto
from models.venta import Venta

router = APIRouter(prefix="/superadmin")
templates = Jinja2Templates(directory="templates")

# Dashboard del SuperAdmin
@router.get("/dashboard")
async def dashboard(request: Request, db: Session = Depends(get_db), _: User = Depends(require_superadmin_from_cookie)):
    """Dashboard principal del SuperAdministrador - Métricas del SaaS"""
    # Estadísticas de clientes y planes
    total_negocios = db.query(Negocio).count()
    negocios_activos = db.query(Negocio).filter(Negocio.estado_suscripcion == "activo").count()
    negocios_con_plan = db.query(Negocio).filter(Negocio.plan_id.isnot(None)).count()
    total_usuarios = db.query(User).count()

    # Ingresos por venta de planes (no por productos vendidos por clientes)
    # Calculamos ingresos históricos por planes asignados
    ingresos_por_planes = db.query(func.sum(Plan.precio)).join(Negocio).filter(
        Negocio.plan_id.isnot(None)
    ).scalar() or 0.0

    # MRR (Monthly Recurring Revenue) - ingresos mensuales de planes activos
    mrr = db.query(func.sum(Plan.precio)).join(Negocio).filter(
        Negocio.plan_id.isnot(None),
        Negocio.estado_suscripcion == "activo"
    ).scalar() or 0.0

    # Planes más populares
    planes_populares = db.query(
        Plan.nombre_plan,
        func.count(Negocio.id).label('cantidad')
    ).join(Negocio).group_by(Plan.id).order_by(desc('cantidad')).limit(3).all()

    # Ingresos del mes actual por nuevos clientes
    mes_actual = datetime.now().replace(day=1)
    ingresos_mes_nuevos_clientes = db.query(func.sum(Plan.precio)).join(Negocio).filter(
        Negocio.fecha_registro >= mes_actual,
        Negocio.plan_id.isnot(None)
    ).scalar() or 0.0

    # Negocios recientes (últimos 5)
    negocios_recientes = db.query(Negocio).order_by(Negocio.fecha_registro.desc()).limit(5).all()

    return templates.TemplateResponse("superadmin_dashboard.html", {
        "request": request,
        "total_negocios": total_negocios,
        "negocios_activos": negocios_activos,
        "negocios_con_plan": negocios_con_plan,
        "total_usuarios": total_usuarios,
        "ingresos_por_planes": f"{ingresos_por_planes:.2f}",
        "mrr": f"{mrr:.2f}",
        "ingresos_mes_nuevos_clientes": f"{ingresos_mes_nuevos_clientes:.2f}",
        "planes_populares": planes_populares,
        "negocios_recientes": negocios_recientes
    })

# Gestión de Negocios
@router.get("/negocios")
async def listar_negocios(request: Request, db: Session = Depends(get_db), _: User = Depends(require_superadmin_from_cookie)):
    """Listar todos los negocios"""
    negocios = db.query(Negocio).all()
    planes = db.query(Plan).all()
    return templates.TemplateResponse("superadmin_negocios.html", {
        "request": request,
        "negocios": negocios,
        "planes": planes
    })

@router.post("/negocios")
async def crear_negocio(
    nombre_negocio: str = Form(...),
    propietario: str = Form(...),
    plan_id: int = Form(...),
    admin_username: str = Form(...),
    db: Session = Depends(get_db),
    _: User = Depends(require_superadmin_from_cookie)
):
    """Crear un nuevo negocio con su administrador"""
    try:
        # Verificar que el plan existe
        plan = db.query(Plan).filter(Plan.id == plan_id).first()
        if not plan:
            raise HTTPException(status_code=400, detail="Plan no encontrado")

        # Verificar que el nombre de usuario no exista
        existing_user = db.query(User).filter(User.nombre_usuario == admin_username).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Nombre de usuario ya existe")

        # Crear el negocio
        negocio = Negocio(
            nombre_negocio=nombre_negocio,
            propietario=propietario,
            plan_id=plan_id,
            estado_suscripcion="activo",
            fecha_vencimiento=datetime.now() + timedelta(days=plan.duracion_dias)
        )
        db.add(negocio)
        db.flush()  # Para obtener el ID del negocio

        # Crear usuario administrador para el negocio
        hashed_password = get_password_hash("admin123")  # Contraseña temporal
        admin_user = User(
            nombre_usuario=admin_username,
            contraseña=hashed_password,
            rol="admin",
            negocio_id=negocio.id,
            estado="activo"
        )
        db.add(admin_user)

        # Crear un vendedor de ejemplo
        vendedor_user = User(
            nombre_usuario=f"{admin_username}_vendedor",
            contraseña=get_password_hash("vendedor123"),
            rol="vendedor",
            negocio_id=negocio.id,
            estado="activo"
        )
        db.add(vendedor_user)

        # NOTA: Los productos deben ser creados por el administrador del negocio,
        # no automáticamente al crear el negocio.
        # Los productos de ejemplo han sido removidos.

        db.commit()

        return RedirectResponse(url="/superadmin/negocios", status_code=302)

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error al crear negocio: {str(e)}")

@router.get("/negocios/{negocio_id}")
async def ver_negocio(negocio_id: int, request: Request, db: Session = Depends(get_db), _: User = Depends(require_superadmin_from_cookie)):
    """Ver detalles de un negocio específico"""
    negocio = db.query(Negocio).filter(Negocio.id == negocio_id).first()
    if not negocio:
        raise HTTPException(status_code=404, detail="Negocio no encontrado")

    # Obtener usuarios del negocio
    usuarios = db.query(User).filter(User.negocio_id == negocio_id).all()

    # Estadísticas del negocio
    total_productos = db.query(Producto).filter(Producto.negocio_id == negocio_id).count()
    total_ventas_result = db.query(func.sum(Venta.valor_total)).filter(Venta.negocio_id == negocio_id).scalar()
    total_ventas = float(total_ventas_result) if total_ventas_result is not None else 0.0

    return templates.TemplateResponse("superadmin_negocio_detalle.html", {
        "request": request,
        "negocio": negocio,
        "usuarios": usuarios,
        "total_productos": total_productos,
        "total_ventas": total_ventas
    })

@router.post("/negocios/{negocio_id}/estado")
async def cambiar_estado_negocio(
    negocio_id: int,
    estado: str = Form(...),
    db: Session = Depends(get_db),
    _: User = Depends(require_superadmin_from_cookie)
):
    """Cambiar estado de suscripción de un negocio"""
    negocio = db.query(Negocio).filter(Negocio.id == negocio_id).first()
    if not negocio:
        raise HTTPException(status_code=404, detail="Negocio no encontrado")

    negocio.estado_suscripcion = estado
    db.commit()

    return RedirectResponse(url=f"/superadmin/negocios/{negocio_id}", status_code=302)

@router.post("/negocios/{negocio_id}/reset-password")
async def reset_password_admin(
    negocio_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_superadmin_from_cookie)
):
    """Restablecer contraseña del administrador del negocio"""
    admin = db.query(User).filter(
        User.negocio_id == negocio_id,
        User.rol == "admin"
    ).first()

    if admin:
        from auth import get_password_hash
        admin.contraseña = get_password_hash("admin123")  # Contraseña temporal
        db.commit()

    return RedirectResponse(url=f"/superadmin/negocios/{negocio_id}", status_code=302)

# Gestión de Planes
@router.get("/planes")
async def listar_planes(request: Request, db: Session = Depends(get_db), _: User = Depends(require_superadmin_from_cookie)):
    """Listar todos los planes"""
    planes = db.query(Plan).all()
    return templates.TemplateResponse("superadmin_planes.html", {
        "request": request,
        "planes": planes
    })

@router.post("/planes")
async def crear_plan(
    nombre_plan: str = Form(...),
    descripcion: str = Form(...),
    precio: float = Form(...),
    duracion_dias: int = Form(...),
    db: Session = Depends(get_db),
    _: User = Depends(require_superadmin_from_cookie)
):
    """Crear un nuevo plan"""
    plan = Plan(
        nombre_plan=nombre_plan,
        descripcion=descripcion,
        precio=precio,
        duracion_dias=duracion_dias
    )
    db.add(plan)
    db.commit()

    return RedirectResponse(url="/superadmin/planes", status_code=302)

@router.post("/planes/{plan_id}")
async def actualizar_plan(
    plan_id: int,
    nombre_plan: str = Form(...),
    descripcion: str = Form(...),
    precio: float = Form(...),
    duracion_dias: int = Form(...),
    db: Session = Depends(get_db),
    _: User = Depends(require_superadmin_from_cookie)
):
    """Actualizar un plan existente"""
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")

    plan.nombre_plan = nombre_plan
    plan.descripcion = descripcion
    plan.precio = precio
    plan.duracion_dias = duracion_dias
    db.commit()

    return RedirectResponse(url="/superadmin/planes", status_code=302)

# Backups
@router.get("/backups")
async def backups_page(request: Request, _: User = Depends(require_superadmin_from_cookie)):
    """Página de gestión de backups"""
    return templates.TemplateResponse("superadmin_backups.html", {"request": request})

@router.get("/backups/download/{tipo}")
async def descargar_backup(tipo: str, db: Session = Depends(get_db), _: User = Depends(require_superadmin_from_cookie)):
    """Descargar backup de datos"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if tipo == "usuarios":
        # Exportar usuarios a CSV
        usuarios = db.query(User).all()
        filename = f"backup_usuarios_{timestamp}.csv"

        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['ID', 'Usuario', 'Rol', 'Negocio_ID', 'Estado'])
            for user in usuarios:
                writer.writerow([user.id, user.nombre_usuario, user.rol, user.negocio_id, user.estado])

    elif tipo == "negocios":
        # Exportar negocios a CSV
        negocios = db.query(Negocio).all()
        filename = f"backup_negocios_{timestamp}.csv"

        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['ID', 'Nombre', 'Propietario', 'Plan_ID', 'Estado', 'Fecha_Vencimiento'])
            for negocio in negocios:
                writer.writerow([
                    negocio.id, negocio.nombre_negocio, negocio.propietario,
                    negocio.plan_id, negocio.estado_suscripcion, negocio.fecha_vencimiento
                ])

    elif tipo == "productos":
        # Exportar productos a CSV
        productos = db.query(Producto).all()
        filename = f"backup_productos_{timestamp}.csv"

        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['ID', 'Negocio_ID', 'Nombre', 'Código', 'Categoría', 'Precio', 'Cantidad'])
            for producto in productos:
                writer.writerow([
                    producto.id, producto.negocio_id, producto.nombre, producto.codigo,
                    producto.categoria, producto.precio, producto.cantidad
                ])

    elif tipo == "ventas":
        # Exportar ventas a CSV
        ventas = db.query(Venta).all()
        filename = f"backup_ventas_{timestamp}.csv"

        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['ID', 'Negocio_ID', 'Producto_ID', 'Vendedor_ID', 'Cantidad', 'Valor_Total', 'Fecha'])
            for venta in ventas:
                writer.writerow([
                    venta.id, venta.negocio_id, venta.producto_id, venta.vendedor_id,
                    venta.cantidad_vendida, venta.valor_total, venta.fecha_venta
                ])

    else:
        raise HTTPException(status_code=400, detail="Tipo de backup no válido")

    return FileResponse(filename, media_type='application/octet-stream', filename=filename)

# Eliminar negocios suspendidos
@router.delete("/negocios/{negocio_id}")
async def eliminar_negocio_suspendido(
    negocio_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_superadmin_from_cookie)
):
    """Eliminar un negocio suspendido (solo negocios suspendidos pueden ser eliminados)"""
    negocio = db.query(Negocio).filter(Negocio.id == negocio_id).first()
    if not negocio:
        raise HTTPException(status_code=404, detail="Negocio no encontrado")

    # Solo permitir eliminar negocios suspendidos
    if negocio.estado_suscripcion != "suspendido":
        raise HTTPException(
            status_code=400,
            detail="Solo se pueden eliminar negocios suspendidos. Cambie el estado a 'suspendido' primero."
        )

    try:
        # Obtener usuarios del negocio antes de eliminar
        usuarios_negocio = db.query(User).filter(User.negocio_id == negocio_id).all()

        # Eliminar ventas relacionadas
        db.query(Venta).filter(Venta.negocio_id == negocio_id).delete()

        # Eliminar productos del negocio
        db.query(Producto).filter(Producto.negocio_id == negocio_id).delete()

        # Eliminar usuarios del negocio
        db.query(User).filter(User.negocio_id == negocio_id).delete()

        # Finalmente eliminar el negocio
        db.delete(negocio)

        db.commit()

        return {"message": f"Negocio '{negocio.nombre_negocio}' y todos sus datos asociados han sido eliminados exitosamente"}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al eliminar negocio: {str(e)}")

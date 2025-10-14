"""
Router del SuperAdministrador para Autostock
Gestiona negocios, planes de suscripción y métricas globales
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Form, File, UploadFile
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
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
    """Dashboard principal del SuperAdministrador"""
    # Estadísticas globales
    total_negocios = db.query(Negocio).count()
    negocios_activos = db.query(Negocio).filter(Negocio.estado_suscripcion == "activo").count()
    total_usuarios = db.query(User).count()
    total_ventas = db.query(func.sum(Venta.valor_total)).scalar() or 0

    # Ventas del mes actual
    mes_actual = datetime.now().replace(day=1)
    ventas_mes = db.query(func.sum(Venta.valor_total)).filter(
        Venta.fecha_venta >= mes_actual
    ).scalar() or 0

    # Negocios recientes (últimos 5)
    negocios_recientes = db.query(Negocio).order_by(Negocio.fecha_registro.desc()).limit(5).all()

    return templates.TemplateResponse("superadmin_dashboard.html", {
        "request": request,
        "total_negocios": total_negocios,
        "negocios_activos": negocios_activos,
        "total_usuarios": total_usuarios,
        "total_ventas": f"{total_ventas:.2f}",
        "ventas_mes": f"{ventas_mes:.2f}",
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

        # Crear productos de ejemplo
        productos_ejemplo = [
            {"codigo": "LLANTA001", "nombre": "Llanta 185/65R14", "categoria": "Llantas", "precio": 45.99, "cantidad": 20},
            {"codigo": "LLANTA002", "nombre": "Llanta 195/55R15", "categoria": "Llantas", "precio": 52.99, "cantidad": 15},
            {"codigo": "LLANTA003", "nombre": "Llanta 205/55R16", "categoria": "Llantas", "precio": 59.99, "cantidad": 12},
            {"codigo": "ACEITE001", "nombre": "Aceite Motor 5W30", "categoria": "Aceites", "precio": 12.99, "cantidad": 25},
            {"codigo": "ACEITE002", "nombre": "Aceite Motor 10W40", "categoria": "Aceites", "precio": 14.99, "cantidad": 20},
            {"codigo": "FILTRO001", "nombre": "Filtro de Aire Universal", "categoria": "Filtros", "precio": 8.99, "cantidad": 30},
            {"codigo": "FILTRO002", "nombre": "Filtro de Aceite", "categoria": "Filtros", "precio": 6.99, "cantidad": 35},
            {"codigo": "BATERIA001", "nombre": "Batería 12V 45Ah", "categoria": "Baterías", "precio": 89.99, "cantidad": 8},
        ]

        for producto_data in productos_ejemplo:
            producto = Producto(
                negocio_id=negocio.id,
                codigo=producto_data["codigo"],
                nombre=producto_data["nombre"],
                categoria=producto_data["categoria"],
                precio=producto_data["precio"],
                cantidad=producto_data["cantidad"],
                proveedor="Proveedor Demo"
            )
            db.add(producto)

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

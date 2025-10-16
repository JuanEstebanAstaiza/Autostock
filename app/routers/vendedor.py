"""
Router del Vendedor para Autostock
Permite consultar inventario y registrar ventas
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List
from datetime import datetime, timedelta, timezone

from models import get_db
from auth import require_vendedor_from_cookie
from models.user import User
from models.negocio import Negocio
from models.producto import Producto
from models.venta import Venta
from models.notificacion import Notificacion

router = APIRouter(prefix="/vendedor")
templates = Jinja2Templates(directory="templates")

# Dashboard del Vendedor
@router.get("/dashboard")
async def dashboard(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_vendedor_from_cookie)
):
    """Dashboard simple del vendedor"""
    negocio_id = current_user.negocio_id

    # Zona horaria de Colombia (UTC-5)
    colombia_tz = timezone(timedelta(hours=-5))
    ahora_colombia = datetime.now(colombia_tz)
    hoy_colombia = ahora_colombia.date()

    # Estadísticas personales del día en zona horaria de Colombia
    inicio_dia = datetime.combine(hoy_colombia, datetime.min.time()).replace(tzinfo=colombia_tz)
    fin_dia = datetime.combine(hoy_colombia, datetime.max.time()).replace(tzinfo=colombia_tz)

    # Convertir a UTC para comparación con la base de datos
    inicio_dia_utc = inicio_dia.astimezone(timezone.utc)
    fin_dia_utc = fin_dia.astimezone(timezone.utc)

    ventas_hoy = db.query(func.sum(Venta.valor_total)).filter(
        Venta.vendedor_id == current_user.id,
        Venta.fecha_venta >= inicio_dia_utc,
        Venta.fecha_venta <= fin_dia_utc
    ).scalar() or 0


    cantidad_ventas_hoy = db.query(Venta).filter(
        Venta.vendedor_id == current_user.id,
        Venta.fecha_venta >= inicio_dia_utc,
        Venta.fecha_venta <= fin_dia_utc
    ).count()

    # Productos con bajo stock (para información)
    productos_bajo_stock = db.query(Producto).filter(
        Producto.negocio_id == negocio_id,
        Producto.cantidad <= 10
    ).count()

    # Ventas recientes del vendedor
    ventas_recientes = db.query(Venta).filter(
        Venta.vendedor_id == current_user.id
    ).order_by(Venta.fecha_venta.desc()).limit(5).all()

    return templates.TemplateResponse("vendedor_dashboard.html", {
        "request": request,
        "ventas_hoy": f"{ventas_hoy:.2f}",
        "cantidad_ventas_hoy": cantidad_ventas_hoy,
        "productos_bajo_stock": productos_bajo_stock,
        "ventas_recientes": ventas_recientes
    })

# Consulta de Inventario
@router.get("/inventario")
async def inventario(
    request: Request,
    search: str = "",
    db: Session = Depends(get_db),
    current_user: User = Depends(require_vendedor_from_cookie)
):
    """Consultar inventario de productos"""
    negocio_id = current_user.negocio_id

    query = db.query(Producto).filter(Producto.negocio_id == negocio_id)

    # Filtro de búsqueda
    if search:
        query = query.filter(
            (Producto.nombre.contains(search)) |
            (Producto.codigo.contains(search)) |
            (Producto.categoria.contains(search))
        )

    productos = query.order_by(Producto.nombre).all()

    return templates.TemplateResponse("vendedor_inventario.html", {
        "request": request,
        "productos": productos,
        "search": search
    })

@router.get("/api/productos/{codigo}")
async def buscar_producto_por_codigo(
    codigo: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_vendedor_from_cookie)
):
    """API para buscar producto por código (para AJAX)"""
    negocio_id = current_user.negocio_id

    producto = db.query(Producto).filter(
        Producto.negocio_id == negocio_id,
        Producto.codigo == codigo
    ).first()

    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    return {
        "id": producto.id,
        "codigo": producto.codigo,
        "nombre": producto.nombre,
        "precio": producto.precio,
        "cantidad": producto.cantidad,
        "categoria": producto.categoria
    }

# Registro de Ventas
@router.get("/ventas")
async def ventas_form(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_vendedor_from_cookie)
):
    """Formulario para registrar ventas"""
    negocio_id = current_user.negocio_id

    # Obtener productos disponibles (con stock)
    productos = db.query(Producto).filter(
        Producto.negocio_id == negocio_id,
        Producto.cantidad > 0
    ).order_by(Producto.nombre).all()

    return templates.TemplateResponse("vendedor_ventas.html", {
        "request": request,
        "productos": productos
    })

@router.post("/ventas")
async def registrar_venta(
    producto_id: int = Form(...),
    cantidad: int = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_vendedor_from_cookie)
):
    """Registrar una nueva venta"""
    negocio_id = current_user.negocio_id

    # Verificar que el producto existe y pertenece al negocio
    producto = db.query(Producto).filter(
        Producto.id == producto_id,
        Producto.negocio_id == negocio_id
    ).first()

    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    # Verificar stock suficiente
    if producto.cantidad < cantidad:
        raise HTTPException(status_code=400, detail=f"Stock insuficiente. Disponible: {producto.cantidad}")

    # Verificar cantidad válida
    if cantidad <= 0:
        raise HTTPException(status_code=400, detail="La cantidad debe ser mayor a 0")

    # Calcular valor total
    valor_total = producto.precio * cantidad

    # Crear venta
    venta = Venta(
        negocio_id=negocio_id,
        producto_id=producto_id,
        vendedor_id=current_user.id,
        cantidad_vendida=cantidad,
        valor_total=valor_total
    )
    db.add(venta)

    # Actualizar stock
    producto.cantidad -= cantidad

    # Crear notificación para el administrador del negocio
    mensaje_notificacion = f"{current_user.nombre_usuario} vendió {cantidad} {producto.nombre}"
    notificacion = Notificacion(
        negocio_id=negocio_id,
        vendedor_id=current_user.id,
        producto_id=producto_id,
        cantidad_vendida=cantidad,
        mensaje=mensaje_notificacion
    )
    db.add(notificacion)

    db.commit()

    return RedirectResponse(url="/vendedor/dashboard", status_code=302)

@router.get("/ventas/historial")
async def historial_ventas(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_vendedor_from_cookie)
):
    """Ver historial de ventas del vendedor"""
    ventas_list = db.query(Venta).filter(
        Venta.vendedor_id == current_user.id
    ).order_by(Venta.fecha_venta.desc()).all()

    return templates.TemplateResponse("vendedor_historial.html", {
        "request": request,
        "ventas": ventas_list
    })

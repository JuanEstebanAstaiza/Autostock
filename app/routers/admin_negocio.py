"""
Router del Administrador de Montallantas para Autostock
Gestiona inventario, ventas, empleados y reportes de su negocio
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Form, File, UploadFile
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List
import csv
import json
from datetime import datetime, timedelta
from auth import require_admin_from_cookie, require_same_business_from_cookie, get_password_hash

from models import get_db
from models.user import User
from models.negocio import Negocio
from models.plan import Plan
from models.producto import Producto
from models.venta import Venta

router = APIRouter(prefix="/negocio")
templates = Jinja2Templates(directory="templates")

# Dashboard del Admin
@router.get("/dashboard")
async def dashboard(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_same_business_from_cookie)
):
    """Dashboard principal del Administrador"""
    negocio_id = current_user.negocio_id

    # Estadísticas del negocio
    total_productos = db.query(Producto).filter(Producto.negocio_id == negocio_id).count()
    productos_bajo_stock = db.query(Producto).filter(
        Producto.negocio_id == negocio_id,
        Producto.cantidad <= 10
    ).count()

    # Ventas del día
    hoy = datetime.now().date()
    ventas_hoy = db.query(func.sum(Venta.valor_total)).filter(
        Venta.negocio_id == negocio_id,
        func.date(Venta.fecha_venta) == hoy
    ).scalar() or 0

    # Ventas del mes
    mes_actual = datetime.now().replace(day=1)
    ventas_mes = db.query(func.sum(Venta.valor_total)).filter(
        Venta.negocio_id == negocio_id,
        Venta.fecha_venta >= mes_actual
    ).scalar() or 0

    # Productos más vendidos (últimos 30 días)
    fecha_limite = datetime.now() - timedelta(days=30)
    productos_top = db.query(
        Producto.nombre,
        func.sum(Venta.cantidad_vendida).label('total_vendido')
    ).join(Venta).filter(
        Producto.negocio_id == negocio_id,
        Venta.fecha_venta >= fecha_limite
    ).group_by(Producto.id).order_by(desc('total_vendido')).limit(5).all()

    # Ventas recientes
    ventas_recientes = db.query(Venta).filter(
        Venta.negocio_id == negocio_id
    ).order_by(Venta.fecha_venta.desc()).limit(10).all()

    return templates.TemplateResponse("admin_dashboard.html", {
        "request": request,
        "total_productos": total_productos,
        "productos_bajo_stock": productos_bajo_stock,
        "ventas_hoy": f"{ventas_hoy:.2f}",
        "ventas_mes": f"{ventas_mes:.2f}",
        "productos_top": productos_top,
        "ventas_recientes": ventas_recientes
    })

# Gestión de Inventario
@router.get("/inventario")
async def inventario(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_same_business_from_cookie)
):
    """Ver inventario de productos"""
    negocio_id = current_user.negocio_id
    productos = db.query(Producto).filter(Producto.negocio_id == negocio_id).all()

    return templates.TemplateResponse("admin_inventario.html", {
        "request": request,
        "productos": productos
    })

@router.post("/inventario")
async def crear_producto(
    nombre: str = Form(...),
    codigo: str = Form(...),
    categoria: str = Form(""),
    precio: float = Form(...),
    cantidad: int = Form(...),
    proveedor: str = Form(""),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_same_business_from_cookie)
):
    """Crear un nuevo producto"""
    negocio_id = current_user.negocio_id

    # Verificar que el código no exista
    existing = db.query(Producto).filter(
        Producto.negocio_id == negocio_id,
        Producto.codigo == codigo
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Código de producto ya existe")

    producto = Producto(
        negocio_id=negocio_id,
        nombre=nombre,
        codigo=codigo,
        categoria=categoria,
        precio=precio,
        cantidad=cantidad,
        proveedor=proveedor
    )
    db.add(producto)
    db.commit()

    return RedirectResponse(url="/negocio/inventario", status_code=302)

@router.post("/inventario/{producto_id}")
async def actualizar_producto(
    producto_id: int,
    nombre: str = Form(...),
    codigo: str = Form(...),
    categoria: str = Form(""),
    precio: float = Form(...),
    cantidad: int = Form(...),
    proveedor: str = Form(""),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_same_business_from_cookie)
):
    """Actualizar producto existente"""
    negocio_id = current_user.negocio_id

    producto = db.query(Producto).filter(
        Producto.id == producto_id,
        Producto.negocio_id == negocio_id
    ).first()

    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    # Verificar código único si cambió
    if producto.codigo != codigo:
        existing = db.query(Producto).filter(
            Producto.negocio_id == negocio_id,
            Producto.codigo == codigo,
            Producto.id != producto_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Código de producto ya existe")

    producto.nombre = nombre
    producto.codigo = codigo
    producto.categoria = categoria
    producto.precio = precio
    producto.cantidad = cantidad
    producto.proveedor = proveedor
    db.commit()

    return RedirectResponse(url="/negocio/inventario", status_code=302)

@router.post("/inventario/{producto_id}/delete")
async def eliminar_producto(
    producto_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_same_business_from_cookie)
):
    """Eliminar producto"""
    negocio_id = current_user.negocio_id

    producto = db.query(Producto).filter(
        Producto.id == producto_id,
        Producto.negocio_id == negocio_id
    ).first()

    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    db.delete(producto)
    db.commit()

    return RedirectResponse(url="/negocio/inventario", status_code=302)

# Gestión de Ventas
@router.get("/ventas")
async def ventas(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_same_business_from_cookie)
):
    """Ver historial de ventas"""
    negocio_id = current_user.negocio_id

    ventas_list = db.query(Venta).filter(
        Venta.negocio_id == negocio_id
    ).order_by(Venta.fecha_venta.desc()).all()

    return templates.TemplateResponse("admin_ventas.html", {
        "request": request,
        "ventas": ventas_list
    })

@router.post("/ventas")
async def registrar_venta(
    producto_id: int = Form(...),
    vendedor_id: int = Form(...),
    cantidad: int = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_same_business_from_cookie)
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
        raise HTTPException(status_code=400, detail="Stock insuficiente")

    # Verificar que el vendedor pertenece al negocio
    vendedor = db.query(User).filter(
        User.id == vendedor_id,
        User.negocio_id == negocio_id,
        User.rol == "vendedor"
    ).first()

    if not vendedor:
        raise HTTPException(status_code=404, detail="Vendedor no encontrado")

    # Calcular valor total
    valor_total = producto.precio * cantidad

    # Crear venta
    venta = Venta(
        negocio_id=negocio_id,
        producto_id=producto_id,
        vendedor_id=vendedor_id,
        cantidad_vendida=cantidad,
        valor_total=valor_total
    )
    db.add(venta)

    # Actualizar stock
    producto.cantidad -= cantidad

    db.commit()

    return RedirectResponse(url="/negocio/ventas", status_code=302)

# Gestión de Usuarios
@router.get("/usuarios")
async def usuarios(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_same_business_from_cookie)
):
    """Ver usuarios del negocio"""
    negocio_id = current_user.negocio_id

    usuarios_list = db.query(User).filter(
        User.negocio_id == negocio_id
    ).all()

    return templates.TemplateResponse("admin_usuarios.html", {
        "request": request,
        "usuarios": usuarios_list
    })

@router.post("/usuarios")
async def crear_usuario(
    nombre_usuario: str = Form(...),
    rol: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_same_business_from_cookie)
):
    """Crear un nuevo usuario (vendedor)"""
    negocio_id = current_user.negocio_id

    # Verificar que el nombre de usuario no exista
    existing = db.query(User).filter(User.nombre_usuario == nombre_usuario).first()
    if existing:
        raise HTTPException(status_code=400, detail="Nombre de usuario ya existe")

    # Solo permitir crear vendedores
    if rol not in ["vendedor"]:
        raise HTTPException(status_code=400, detail="Solo se pueden crear usuarios vendedores")

    usuario = User(
        nombre_usuario=nombre_usuario,
        contraseña=get_password_hash("vendedor123"),  # Contraseña temporal
        rol=rol,
        negocio_id=negocio_id,
        estado="activo"
    )
    db.add(usuario)
    db.commit()

    return RedirectResponse(url="/negocio/usuarios", status_code=302)

@router.post("/usuarios/{usuario_id}/estado")
async def cambiar_estado_usuario(
    usuario_id: int,
    estado: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_same_business_from_cookie)
):
    """Cambiar estado de un usuario"""
    negocio_id = current_user.negocio_id

    usuario = db.query(User).filter(
        User.id == usuario_id,
        User.negocio_id == negocio_id
    ).first()

    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    usuario.estado = estado
    db.commit()

    return RedirectResponse(url="/negocio/usuarios", status_code=302)

@router.post("/usuarios/{usuario_id}/reset-password")
async def reset_password_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_same_business_from_cookie)
):
    """Restablecer contraseña de un usuario"""
    negocio_id = current_user.negocio_id

    usuario = db.query(User).filter(
        User.id == usuario_id,
        User.negocio_id == negocio_id
    ).first()

    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    usuario.contraseña = get_password_hash("temp123")
    db.commit()

    return RedirectResponse(url=f"/negocio/usuarios", status_code=302)

# Páginas dedicadas para reportes
@router.get("/reportes/productos-vendidos")
async def productos_vendidos(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_same_business_from_cookie)
):
    """Página dedicada para productos más vendidos"""
    negocio_id = current_user.negocio_id

    # Productos más vendidos (últimos 30 días)
    fecha_limite = datetime.now() - timedelta(days=30)
    productos_top = db.query(
        Producto.nombre,
        func.sum(Venta.cantidad_vendida).label('total_vendido'),
        func.sum(Venta.valor_total).label('total_valor')
    ).join(Venta).filter(
        Producto.negocio_id == negocio_id,
        Venta.fecha_venta >= fecha_limite
    ).group_by(Producto.id).order_by(desc('total_vendido')).all()

    return templates.TemplateResponse("admin_productos_vendidos.html", {
        "request": request,
        "productos_top": productos_top
    })

@router.get("/reportes/ventas-recientes")
async def ventas_recientes_pagina(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_same_business_from_cookie)
):
    """Página dedicada para ventas recientes"""
    negocio_id = current_user.negocio_id

    # Ventas recientes (últimos 50 registros)
    ventas_recientes = db.query(Venta).filter(
        Venta.negocio_id == negocio_id
    ).order_by(Venta.fecha_venta.desc()).limit(50).all()

    # Estadísticas de ventas
    total_ventas = len(ventas_recientes)
    total_ingresos = sum(venta.valor_total for venta in ventas_recientes)

    # Ventas por día (últimos 30 días)
    fecha_limite = datetime.now() - timedelta(days=30)
    ventas_por_dia_raw = db.query(
        func.date(Venta.fecha_venta).label('fecha'),
        func.sum(Venta.valor_total).label('total'),
        func.count(Venta.id).label('cantidad')
    ).filter(
        Venta.negocio_id == negocio_id,
        Venta.fecha_venta >= fecha_limite
    ).group_by(func.date(Venta.fecha_venta)).order_by('fecha').all()

    # Convertir los objetos Row a diccionarios para JSON serialization
    ventas_por_dia = [
        {
            'fecha': str(row.fecha),
            'total': float(row.total) if row.total else 0.0,
            'cantidad': int(row.cantidad) if row.cantidad else 0
        }
        for row in ventas_por_dia_raw
    ]

    return templates.TemplateResponse("admin_ventas_recientes.html", {
        "request": request,
        "ventas_recientes": ventas_recientes,
        "total_ventas": total_ventas,
        "total_ingresos": total_ingresos,
        "ventas_por_dia": ventas_por_dia
    })

# Reportes
@router.get("/reportes")
async def reportes(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_same_business_from_cookie)
):
    """Ver reportes del negocio"""
    negocio_id = current_user.negocio_id

    # Ventas por día (últimos 30 días)
    fecha_limite = datetime.now() - timedelta(days=30)
    ventas_por_dia = db.query(
        func.date(Venta.fecha_venta).label('fecha'),
        func.sum(Venta.valor_total).label('total')
    ).filter(
        Venta.negocio_id == negocio_id,
        Venta.fecha_venta >= fecha_limite
    ).group_by(func.date(Venta.fecha_venta)).order_by('fecha').all()

    # Productos más vendidos
    productos_top = db.query(
        Producto.nombre,
        func.sum(Venta.cantidad_vendida).label('total_vendido'),
        func.sum(Venta.valor_total).label('total_valor')
    ).join(Venta).filter(
        Producto.negocio_id == negocio_id,
        Venta.fecha_venta >= fecha_limite
    ).group_by(Producto.id).order_by(desc('total_vendido')).limit(10).all()

    # Stock bajo
    stock_bajo = db.query(Producto).filter(
        Producto.negocio_id == negocio_id,
        Producto.cantidad <= 10
    ).order_by(Producto.cantidad).all()

    return templates.TemplateResponse("admin_reportes.html", {
        "request": request,
        "ventas_por_dia": ventas_por_dia,
        "productos_top": productos_top,
        "stock_bajo": stock_bajo
    })

@router.get("/reportes/export/{tipo}")
async def exportar_reporte(
    tipo: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_same_business_from_cookie)
):
    """Exportar reportes a CSV"""
    negocio_id = current_user.negocio_id
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if tipo == "ventas":
        # Exportar ventas
        ventas_list = db.query(Venta).filter(Venta.negocio_id == negocio_id).all()
        filename = f"reporte_ventas_{timestamp}.csv"

        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Fecha', 'Producto', 'Vendedor', 'Cantidad', 'Valor Total'])
            for venta in ventas_list:
                producto = db.query(Producto).filter(Producto.id == venta.producto_id).first()
                vendedor = db.query(User).filter(User.id == venta.vendedor_id).first()
                writer.writerow([
                    venta.fecha_venta.strftime("%Y-%m-%d %H:%M"),
                    producto.nombre if producto else "N/A",
                    vendedor.nombre_usuario if vendedor else "N/A",
                    venta.cantidad_vendida,
                    venta.valor_total
                ])

    elif tipo == "inventario":
        # Exportar inventario
        productos = db.query(Producto).filter(Producto.negocio_id == negocio_id).all()
        filename = f"reporte_inventario_{timestamp}.csv"

        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Código', 'Nombre', 'Categoría', 'Precio', 'Cantidad', 'Proveedor'])
            for producto in productos:
                writer.writerow([
                    producto.codigo, producto.nombre, producto.categoria,
                    producto.precio, producto.cantidad, producto.proveedor
                ])

    else:
        raise HTTPException(status_code=400, detail="Tipo de reporte no válido")

    return FileResponse(filename, media_type='application/octet-stream', filename=filename)

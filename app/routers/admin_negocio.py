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

# Reportes adicionales
@router.get("/reportes/stock-bajo")
async def stock_bajo(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_same_business_from_cookie)
):
    """Página de productos con stock bajo"""
    negocio_id = current_user.negocio_id

    # Productos con stock bajo (menos de 10 unidades)
    stock_bajo = db.query(Producto).filter(
        Producto.negocio_id == negocio_id,
        Producto.cantidad <= 10
    ).order_by(Producto.cantidad).all()

    # Productos agotados (0 unidades)
    productos_agotados = db.query(Producto).filter(
        Producto.negocio_id == negocio_id,
        Producto.cantidad == 0
    ).all()

    # Estadísticas
    total_productos_bajo_stock = len(stock_bajo)
    total_productos_agotados = len(productos_agotados)
    total_productos = db.query(Producto).filter(Producto.negocio_id == negocio_id).count()

    return templates.TemplateResponse("admin_stock_bajo.html", {
        "request": request,
        "stock_bajo": stock_bajo,
        "productos_agotados": productos_agotados,
        "total_productos_bajo_stock": total_productos_bajo_stock,
        "total_productos_agotados": total_productos_agotados,
        "total_productos": total_productos
    })

@router.get("/reportes/ventas-periodo")
async def ventas_periodo(
    request: Request,
    periodo: str = "mes",  # dia, semana, mes, trimestre
    db: Session = Depends(get_db),
    current_user: User = Depends(require_same_business_from_cookie)
):
    """Página de ventas por período"""
    negocio_id = current_user.negocio_id

    # Calcular fecha límite según período
    now = datetime.now()
    if periodo == "dia":
        fecha_limite = now - timedelta(days=1)
        periodo_texto = "Hoy"
    elif periodo == "semana":
        fecha_limite = now - timedelta(days=7)
        periodo_texto = "Última Semana"
    elif periodo == "mes":
        fecha_limite = now - timedelta(days=30)
        periodo_texto = "Último Mes"
    elif periodo == "trimestre":
        fecha_limite = now - timedelta(days=90)
        periodo_texto = "Último Trimestre"
    else:
        fecha_limite = now - timedelta(days=30)
        periodo_texto = "Último Mes"

    # Ventas del período
    ventas = db.query(Venta).filter(
        Venta.negocio_id == negocio_id,
        Venta.fecha_venta >= fecha_limite
    ).order_by(Venta.fecha_venta.desc()).all()

    # Estadísticas del período
    total_ventas = len(ventas)
    total_ingresos = sum(venta.valor_total for venta in ventas)

    # Ventas por día
    ventas_por_dia_raw = db.query(
        func.date(Venta.fecha_venta).label('fecha'),
        func.sum(Venta.valor_total).label('total'),
        func.count(Venta.id).label('cantidad')
    ).filter(
        Venta.negocio_id == negocio_id,
        Venta.fecha_venta >= fecha_limite
    ).group_by(func.date(Venta.fecha_venta)).order_by('fecha').all()

    ventas_por_dia = [
        {
            'fecha': str(row.fecha),
            'total': float(row.total) if row.total else 0.0,
            'cantidad': int(row.cantidad) if row.cantidad else 0
        }
        for row in ventas_por_dia_raw
    ]

    return templates.TemplateResponse("admin_ventas_periodo.html", {
        "request": request,
        "ventas": ventas,
        "periodo": periodo,
        "periodo_texto": periodo_texto,
        "total_ventas": total_ventas,
        "total_ingresos": total_ingresos,
        "ventas_por_dia": ventas_por_dia
    })

@router.get("/reportes/rendimiento-vendedores")
async def rendimiento_vendedores(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_same_business_from_cookie)
):
    """Página de rendimiento de vendedores"""
    negocio_id = current_user.negocio_id
    fecha_limite = datetime.now() - timedelta(days=30)

    # Rendimiento por vendedor
    rendimiento = db.query(
        User.nombre_usuario,
        func.count(Venta.id).label('total_ventas'),
        func.sum(Venta.valor_total).label('total_ingresos'),
        func.avg(Venta.valor_total).label('venta_promedio')
    ).join(Venta, User.id == Venta.vendedor_id).filter(
        User.negocio_id == negocio_id,
        Venta.fecha_venta >= fecha_limite
    ).group_by(User.id).order_by(desc('total_ingresos')).all()

    # Ventas por día por vendedor (últimos 7 días)
    fecha_semana = datetime.now() - timedelta(days=7)
    ventas_por_vendedor_dia = db.query(
        User.nombre_usuario,
        func.date(Venta.fecha_venta).label('fecha'),
        func.count(Venta.id).label('ventas'),
        func.sum(Venta.valor_total).label('total')
    ).join(Venta, User.id == Venta.vendedor_id).filter(
        User.negocio_id == negocio_id,
        Venta.fecha_venta >= fecha_semana
    ).group_by(User.id, func.date(Venta.fecha_venta)).order_by(User.nombre_usuario, 'fecha').all()

    # Convertir a formato serializable
    rendimiento_data = [
        {
            'vendedor': row[0],
            'total_ventas': int(row[1]),
            'total_ingresos': float(row[2]) if row[2] else 0.0,
            'venta_promedio': float(row[3]) if row[3] else 0.0
        }
        for row in rendimiento
    ]

    return templates.TemplateResponse("admin_rendimiento_vendedores.html", {
        "request": request,
        "rendimiento": rendimiento_data,
        "ventas_por_vendedor_dia": ventas_por_vendedor_dia,
        "max_ingresos": max([v['total_ingresos'] for v in rendimiento_data]) if rendimiento_data else 0
    })

@router.get("/reportes/inventario-completo")
async def inventario_completo(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_same_business_from_cookie)
):
    """Página de inventario completo con estadísticas detalladas"""
    negocio_id = current_user.negocio_id

    # Todos los productos
    productos = db.query(Producto).filter(Producto.negocio_id == negocio_id).all()

    # Estadísticas del inventario
    total_productos = len(productos)
    valor_total_inventario = sum(producto.precio * producto.cantidad for producto in productos)

    # Productos por stock
    stock_bajo = [p for p in productos if 0 < p.cantidad <= 10]
    agotados = [p for p in productos if p.cantidad == 0]
    stock_normal = [p for p in productos if p.cantidad > 10]

    # Productos por categoría
    categorias = {}
    for producto in productos:
        categoria = producto.categoria or 'Sin categoría'
        if categoria not in categorias:
            categorias[categoria] = []
        categorias[categoria].append(producto)

    # Estadísticas por categoría
    categorias_stats = []
    for categoria, prods in categorias.items():
        total_prods = len(prods)
        valor_categoria = sum(p.precio * p.cantidad for p in prods)
        stock_bajo_cat = len([p for p in prods if 0 < p.cantidad <= 10])
        agotados_cat = len([p for p in prods if p.cantidad == 0])

        categorias_stats.append({
            'categoria': categoria,
            'total_productos': total_prods,
            'valor_total': valor_categoria,
            'stock_bajo': stock_bajo_cat,
            'agotados': agotados_cat
        })

    # Top productos por valor
    productos_por_valor = sorted(productos,
                               key=lambda p: p.precio * p.cantidad,
                               reverse=True)[:10]

    return templates.TemplateResponse("admin_inventario_completo.html", {
        "request": request,
        "productos": productos,
        "total_productos": total_productos,
        "valor_total_inventario": valor_total_inventario,
        "stock_bajo": stock_bajo,
        "agotados": agotados,
        "stock_normal": stock_normal,
        "categorias_stats": categorias_stats,
        "productos_por_valor": productos_por_valor
    })

@router.get("/reportes/ingresos")
async def ingresos(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_same_business_from_cookie)
):
    """Página de análisis de ingresos"""
    negocio_id = current_user.negocio_id

    # Ingresos por meses (últimos 12 meses)
    fecha_limite = datetime.now() - timedelta(days=365)
    fecha_limite_date = fecha_limite.date()

    # Para SQLite usamos strftime en lugar de date_trunc
    ingresos_mensuales_raw = db.query(
        func.strftime('%Y-%m', Venta.fecha_venta).label('mes'),
        func.sum(Venta.valor_total).label('total_ingresos'),
        func.count(Venta.id).label('total_ventas')
    ).filter(
        Venta.negocio_id == negocio_id,
        func.date(Venta.fecha_venta) >= fecha_limite_date
    ).group_by(func.strftime('%Y-%m', Venta.fecha_venta)).order_by('mes').all()

    ingresos_mensuales = [
        {
            'mes': str(row.mes),
            'mes_formateado': datetime.strptime(row.mes, '%Y-%m').strftime('%B %Y'),
            'ingresos': float(row.total_ingresos) if row.total_ingresos else 0.0,
            'ventas': int(row.total_ventas) if row.total_ventas else 0
        }
        for row in ingresos_mensuales_raw
    ]

    # Ingresos del mes actual vs mes anterior
    fecha_mes_actual = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    fecha_mes_anterior = (fecha_mes_actual - timedelta(days=1)).replace(day=1)
    fecha_mes_actual_date = fecha_mes_actual.date()
    fecha_mes_anterior_date = fecha_mes_anterior.date()
    fecha_mes_actual_fin_date = datetime.now().date()

    ingresos_mes_actual = db.query(func.sum(Venta.valor_total)).filter(
        Venta.negocio_id == negocio_id,
        func.date(Venta.fecha_venta) >= fecha_mes_actual_date,
        func.date(Venta.fecha_venta) <= fecha_mes_actual_fin_date
    ).scalar() or 0.0

    ingresos_mes_anterior = db.query(func.sum(Venta.valor_total)).filter(
        Venta.negocio_id == negocio_id,
        func.date(Venta.fecha_venta) >= fecha_mes_anterior_date,
        func.date(Venta.fecha_venta) < fecha_mes_actual_date
    ).scalar() or 0.0

    # Calcular porcentaje de cambio
    if ingresos_mes_anterior > 0:
        cambio_porcentaje = ((ingresos_mes_actual - ingresos_mes_anterior) / ingresos_mes_anterior) * 100
    else:
        cambio_porcentaje = 0.0 if ingresos_mes_actual == 0 else 100.0

    # Ingresos por día del mes actual
    ingresos_dia_actual_raw = db.query(
        func.strftime('%Y-%m-%d', Venta.fecha_venta).label('dia'),
        func.sum(Venta.valor_total).label('ingresos')
    ).filter(
        Venta.negocio_id == negocio_id,
        func.date(Venta.fecha_venta) >= fecha_mes_actual_date,
        func.date(Venta.fecha_venta) <= fecha_mes_actual_fin_date
    ).group_by(func.strftime('%Y-%m-%d', Venta.fecha_venta)).order_by('dia').all()

    ingresos_dia_actual = [
        {
            'dia': str(row.dia),
            'dia_formateado': datetime.strptime(row.dia, '%Y-%m-%d').strftime('%d/%m'),
            'ingresos': float(row.ingresos) if row.ingresos else 0.0
        }
        for row in ingresos_dia_actual_raw
    ]

    # Estadísticas generales
    total_ingresos_anio = sum(mes['ingresos'] for mes in ingresos_mensuales)
    promedio_mensual = total_ingresos_anio / max(len(ingresos_mensuales), 1)
    mejor_mes = max(ingresos_mensuales, key=lambda x: x['ingresos']) if ingresos_mensuales else None

    # Formatear fechas para el template
    mes_actual_formateado = datetime.now().strftime("%B %Y")
    mes_anterior_formateado = (datetime.now() - timedelta(days=30)).strftime("%B %Y")

    return templates.TemplateResponse("admin_ingresos.html", {
        "request": request,
        "ingresos_mensuales": ingresos_mensuales,
        "ingresos_mes_actual": ingresos_mes_actual,
        "ingresos_mes_anterior": ingresos_mes_anterior,
        "cambio_porcentaje": cambio_porcentaje,
        "ingresos_dia_actual": ingresos_dia_actual,
        "total_ingresos_anio": total_ingresos_anio,
        "promedio_mensual": promedio_mensual,
        "mejor_mes": mejor_mes,
        "mes_actual_formateado": mes_actual_formateado,
        "mes_anterior_formateado": mes_anterior_formateado
    })

@router.get("/reportes/ganancias")
async def ganancias(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_same_business_from_cookie)
):
    """Página de análisis de ganancias"""
    negocio_id = current_user.negocio_id

    # Calcular ganancias basadas en productos vendidos
    # Por simplicidad, asumimos un margen de ganancia del 30% sobre el precio de venta
    margen_ganancia = 0.3  # 30%

    # Ganancias por mes (últimos 12 meses)
    fecha_limite = datetime.now() - timedelta(days=365)
    fecha_limite_date = fecha_limite.date()

    ganancias_mensuales_raw = db.query(
        func.strftime('%Y-%m', Venta.fecha_venta).label('mes'),
        func.sum(Venta.valor_total).label('ingresos'),
        (func.sum(Venta.valor_total) * margen_ganancia).label('ganancias')
    ).filter(
        Venta.negocio_id == negocio_id,
        func.date(Venta.fecha_venta) >= fecha_limite_date
    ).group_by(func.strftime('%Y-%m', Venta.fecha_venta)).order_by('mes').all()

    ganancias_mensuales = [
        {
            'mes': str(row.mes),
            'mes_formateado': datetime.strptime(row.mes, '%Y-%m').strftime('%B %Y'),
            'ingresos': float(row.ingresos) if row.ingresos else 0.0,
            'ganancias': float(row.ganancias) if row.ganancias else 0.0
        }
        for row in ganancias_mensuales_raw
    ]

    # Ganancias del mes actual vs mes anterior
    fecha_mes_actual = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    fecha_mes_anterior = (fecha_mes_actual - timedelta(days=1)).replace(day=1)
    fecha_mes_actual_date = fecha_mes_actual.date()
    fecha_mes_anterior_date = fecha_mes_anterior.date()
    fecha_mes_actual_fin_date = datetime.now().date()

    ganancias_mes_actual = db.query(func.sum(Venta.valor_total) * margen_ganancia).filter(
        Venta.negocio_id == negocio_id,
        func.date(Venta.fecha_venta) >= fecha_mes_actual_date,
        func.date(Venta.fecha_venta) <= fecha_mes_actual_fin_date
    ).scalar() or 0.0

    ganancias_mes_anterior = db.query(func.sum(Venta.valor_total) * margen_ganancia).filter(
        Venta.negocio_id == negocio_id,
        func.date(Venta.fecha_venta) >= fecha_mes_anterior_date,
        func.date(Venta.fecha_venta) < fecha_mes_actual_date
    ).scalar() or 0.0

    # Calcular porcentaje de cambio
    if ganancias_mes_anterior > 0:
        cambio_porcentaje = ((ganancias_mes_actual - ganancias_mes_anterior) / ganancias_mes_anterior) * 100
    else:
        cambio_porcentaje = 0.0 if ganancias_mes_actual == 0 else 100.0

    # Ganancias por producto (top 10)
    ganancias_por_producto = db.query(
        Producto.nombre,
        func.sum(Venta.cantidad_vendida).label('cantidad'),
        func.sum(Venta.valor_total).label('ingresos'),
        (func.sum(Venta.valor_total) * margen_ganancia).label('ganancias')
    ).join(Venta).filter(
        Producto.negocio_id == negocio_id,
        func.date(Venta.fecha_venta) >= fecha_mes_actual_date,
        func.date(Venta.fecha_venta) <= fecha_mes_actual_fin_date
    ).group_by(Producto.id).order_by(desc('ganancias')).limit(10).all()

    ganancias_por_producto_data = [
        {
            'producto': row[0],
            'cantidad': int(row[1]),
            'ingresos': float(row[2]) if row[2] else 0.0,
            'ganancias': float(row[3]) if row[3] else 0.0
        }
        for row in ganancias_por_producto
    ]

    # Estadísticas generales
    total_ganancias_anio = sum(mes['ganancias'] for mes in ganancias_mensuales)
    promedio_mensual = total_ganancias_anio / max(len(ganancias_mensuales), 1)
    mejor_mes = max(ganancias_mensuales, key=lambda x: x['ganancias']) if ganancias_mensuales else None

    return templates.TemplateResponse("admin_ganancias.html", {
        "request": request,
        "ganancias_mensuales": ganancias_mensuales,
        "ganancias_mes_actual": ganancias_mes_actual,
        "ganancias_mes_anterior": ganancias_mes_anterior,
        "cambio_porcentaje": cambio_porcentaje,
        "ganancias_por_producto": ganancias_por_producto_data,
        "total_ganancias_anio": total_ganancias_anio,
        "promedio_mensual": promedio_mensual,
        "mejor_mes": mejor_mes,
        "margen_ganancia": margen_ganancia * 100
    })

@router.get("/reportes/comparativas")
async def comparativas(
    request: Request,
    periodo1: str = "mes-actual",
    periodo2: str = "mes-anterior",
    db: Session = Depends(get_db),
    current_user: User = Depends(require_same_business_from_cookie)
):
    """Página de comparativas entre períodos"""
    negocio_id = current_user.negocio_id

    # Definir períodos de comparación
    now = datetime.now()

    # Período 1
    if periodo1 == "mes-actual":
        p1_inicio = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        p1_fin = now
        p1_nombre = "Mes Actual"
    elif periodo1 == "mes-anterior":
        p1_fin = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        p1_inicio = (p1_fin - timedelta(days=1)).replace(day=1)
        p1_nombre = "Mes Anterior"
    elif periodo1 == "semana-actual":
        p1_inicio = now - timedelta(days=now.weekday())
        p1_inicio = p1_inicio.replace(hour=0, minute=0, second=0, microsecond=0)
        p1_fin = now
        p1_nombre = "Semana Actual"
    else:
        p1_inicio = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        p1_fin = now
        p1_nombre = "Mes Actual"

    # Período 2
    if periodo2 == "mes-actual":
        p2_inicio = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        p2_fin = now
        p2_nombre = "Mes Actual"
    elif periodo2 == "mes-anterior":
        p2_fin = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        p2_inicio = (p2_fin - timedelta(days=1)).replace(day=1)
        p2_nombre = "Mes Anterior"
    elif periodo2 == "semana-actual":
        p2_inicio = now - timedelta(days=now.weekday())
        p2_inicio = p2_inicio.replace(hour=0, minute=0, second=0, microsecond=0)
        p2_fin = now
        p2_nombre = "Semana Actual"
    elif periodo2 == "semana-anterior":
        semana_actual_inicio = now - timedelta(days=now.weekday())
        semana_actual_inicio = semana_actual_inicio.replace(hour=0, minute=0, second=0, microsecond=0)
        p2_inicio = semana_actual_inicio - timedelta(days=7)
        p2_fin = semana_actual_inicio
        p2_nombre = "Semana Anterior"
    else:
        p2_fin = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        p2_inicio = (p2_fin - timedelta(days=1)).replace(day=1)
        p2_nombre = "Mes Anterior"

    # Métricas período 1
    ventas_p1 = db.query(func.count(Venta.id)).filter(
        Venta.negocio_id == negocio_id,
        Venta.fecha_venta >= p1_inicio,
        Venta.fecha_venta <= p1_fin
    ).scalar() or 0

    ingresos_p1 = db.query(func.sum(Venta.valor_total)).filter(
        Venta.negocio_id == negocio_id,
        Venta.fecha_venta >= p1_inicio,
        Venta.fecha_venta <= p1_fin
    ).scalar() or 0.0

    productos_vendidos_p1 = db.query(func.sum(Venta.cantidad_vendida)).filter(
        Venta.negocio_id == negocio_id,
        Venta.fecha_venta >= p1_inicio,
        Venta.fecha_venta <= p1_fin
    ).scalar() or 0

    # Métricas período 2
    ventas_p2 = db.query(func.count(Venta.id)).filter(
        Venta.negocio_id == negocio_id,
        Venta.fecha_venta >= p2_inicio,
        Venta.fecha_venta <= p2_fin
    ).scalar() or 0

    ingresos_p2 = db.query(func.sum(Venta.valor_total)).filter(
        Venta.negocio_id == negocio_id,
        Venta.fecha_venta >= p2_inicio,
        Venta.fecha_venta <= p2_fin
    ).scalar() or 0.0

    productos_vendidos_p2 = db.query(func.sum(Venta.cantidad_vendida)).filter(
        Venta.negocio_id == negocio_id,
        Venta.fecha_venta >= p2_inicio,
        Venta.fecha_venta <= p2_fin
    ).scalar() or 0

    # Calcular diferencias y porcentajes
    diff_ventas = ventas_p1 - ventas_p2
    diff_ingresos = ingresos_p1 - ingresos_p2
    diff_productos = productos_vendidos_p1 - productos_vendidos_p2

    pct_ventas = ((ventas_p1 - ventas_p2) / ventas_p2 * 100) if ventas_p2 > 0 else (100.0 if ventas_p1 > 0 else 0.0)
    pct_ingresos = ((ingresos_p1 - ingresos_p2) / ingresos_p2 * 100) if ingresos_p2 > 0 else (100.0 if ingresos_p1 > 0 else 0.0)
    pct_productos = ((productos_vendidos_p1 - productos_vendidos_p2) / productos_vendidos_p2 * 100) if productos_vendidos_p2 > 0 else (100.0 if productos_vendidos_p1 > 0 else 0.0)

    # Top productos período 1
    top_productos_p1 = db.query(
        Producto.nombre,
        func.sum(Venta.cantidad_vendida).label('cantidad'),
        func.sum(Venta.valor_total).label('total')
    ).join(Venta).filter(
        Producto.negocio_id == negocio_id,
        Venta.fecha_venta >= p1_inicio,
        Venta.fecha_venta <= p1_fin
    ).group_by(Producto.id).order_by(desc('total')).limit(5).all()

    # Top productos período 2
    top_productos_p2 = db.query(
        Producto.nombre,
        func.sum(Venta.cantidad_vendida).label('cantidad'),
        func.sum(Venta.valor_total).label('total')
    ).join(Venta).filter(
        Producto.negocio_id == negocio_id,
        Venta.fecha_venta >= p2_inicio,
        Venta.fecha_venta <= p2_fin
    ).group_by(Producto.id).order_by(desc('total')).limit(5).all()

    # Convertir a formato serializable
    top_p1_data = [
        {
            'nombre': row[0],
            'cantidad': int(row[1]),
            'total': float(row[2])
        }
        for row in top_productos_p1
    ]

    top_p2_data = [
        {
            'nombre': row[0],
            'cantidad': int(row[1]),
            'total': float(row[2])
        }
        for row in top_productos_p2
    ]

    return templates.TemplateResponse("admin_comparativas.html", {
        "request": request,
        "periodo1": periodo1,
        "periodo2": periodo2,
        "p1_nombre": p1_nombre,
        "p2_nombre": p2_nombre,
        "ventas_p1": ventas_p1,
        "ventas_p2": ventas_p2,
        "ingresos_p1": ingresos_p1,
        "ingresos_p2": ingresos_p2,
        "productos_p1": productos_vendidos_p1,
        "productos_p2": productos_vendidos_p2,
        "diff_ventas": diff_ventas,
        "diff_ingresos": diff_ingresos,
        "diff_productos": diff_productos,
        "pct_ventas": pct_ventas,
        "pct_ingresos": pct_ingresos,
        "pct_productos": pct_productos,
        "top_p1_data": top_p1_data,
        "top_p2_data": top_p2_data
    })

@router.get("/reportes/tendencias")
async def tendencias(
    request: Request,
    periodo: str = "12m",
    db: Session = Depends(get_db),
    current_user: User = Depends(require_same_business_from_cookie)
):
    """Página de análisis de tendencias"""
    negocio_id = current_user.negocio_id

    # Determinar período de análisis
    now = datetime.now()
    if periodo == "3m":
        fecha_limite = now - timedelta(days=90)
        periodo_nombre = "Últimos 3 Meses"
    elif periodo == "6m":
        fecha_limite = now - timedelta(days=180)
        periodo_nombre = "Últimos 6 Meses"
    elif periodo == "12m":
        fecha_limite = now - timedelta(days=365)
        periodo_nombre = "Últimos 12 Meses"
    else:
        fecha_limite = now - timedelta(days=365)
        periodo_nombre = "Últimos 12 Meses"

    # Tendencias mensuales de ventas e ingresos
    fecha_limite_date = fecha_limite.date()
    tendencias_mensuales_raw = db.query(
        func.strftime('%Y-%m', Venta.fecha_venta).label('mes'),
        func.count(Venta.id).label('ventas'),
        func.sum(Venta.valor_total).label('ingresos'),
        func.sum(Venta.cantidad_vendida).label('productos')
    ).filter(
        Venta.negocio_id == negocio_id,
        func.date(Venta.fecha_venta) >= fecha_limite_date
    ).group_by(func.strftime('%Y-%m', Venta.fecha_venta)).order_by('mes').all()

    tendencias_mensuales = [
        {
            'mes': str(row.mes),
            'mes_formateado': datetime.strptime(row.mes, '%Y-%m').strftime('%b %Y'),
            'ventas': int(row.ventas) if row.ventas else 0,
            'ingresos': float(row.ingresos) if row.ingresos else 0.0,
            'productos': int(row.productos) if row.productos else 0
        }
        for row in tendencias_mensuales_raw
    ]

    # Tendencias semanales (últimas 12 semanas)
    fecha_limite_semanal = now - timedelta(days=84)  # 12 semanas

    tendencias_semanales_raw = db.query(
        func.strftime('%Y-%W', Venta.fecha_venta).label('semana'),
        func.count(Venta.id).label('ventas'),
        func.sum(Venta.valor_total).label('ingresos')
    ).filter(
        Venta.negocio_id == negocio_id,
        Venta.fecha_venta >= fecha_limite_semanal
    ).group_by(func.strftime('%Y-%W', Venta.fecha_venta)).order_by('semana').all()

    tendencias_semanales = [
        {
            'semana': str(row.semana),
            'ventas': int(row.ventas) if row.ventas else 0,
            'ingresos': float(row.ingresos) if row.ingresos else 0.0
        }
        for row in tendencias_semanales_raw
    ]

    # Tendencias por día de la semana (último mes)
    fecha_limite_dia = now - timedelta(days=30)
    fecha_limite_dia_date = fecha_limite_dia.date()

    tendencias_dia_semana_raw = db.query(
        func.strftime('%w', Venta.fecha_venta).label('dia_semana'),
        func.count(Venta.id).label('ventas'),
        func.sum(Venta.valor_total).label('ingresos')
    ).filter(
        Venta.negocio_id == negocio_id,
        func.date(Venta.fecha_venta) >= fecha_limite_dia_date
    ).group_by(func.strftime('%w', Venta.fecha_venta)).order_by('dia_semana').all()

    # Mapear números de día a nombres
    dias_semana_map = {
        '0': 'Domingo',
        '1': 'Lunes',
        '2': 'Martes',
        '3': 'Miércoles',
        '4': 'Jueves',
        '5': 'Viernes',
        '6': 'Sábado'
    }

    tendencias_dia_semana = [
        {
            'dia': dias_semana_map.get(str(row.dia_semana), 'Desconocido'),
            'dia_num': int(row.dia_semana),
            'ventas': int(row.ventas) if row.ventas else 0,
            'ingresos': float(row.ingresos) if row.ingresos else 0.0
        }
        for row in tendencias_dia_semana_raw
    ]

    # Tendencias de productos más vendidos (evolución)
    productos_tendencia_raw = db.query(
        Producto.nombre,
        func.sum(Venta.cantidad_vendida).label('total_vendido'),
        func.sum(Venta.valor_total).label('total_ingresos'),
        func.count(Venta.id).label('ventas_count')
    ).join(Venta).filter(
        Producto.negocio_id == negocio_id,
        func.date(Venta.fecha_venta) >= fecha_limite_date
    ).group_by(Producto.id).order_by(desc('total_ingresos')).limit(10).all()

    productos_tendencia = [
        {
            'nombre': row[0],
            'total_vendido': int(row[1]) if row[1] else 0,
            'total_ingresos': float(row[2]) if row[2] else 0.0,
            'ventas_count': int(row[3]) if row[3] else 0
        }
        for row in productos_tendencia_raw
    ]

    # Cálculos de tendencias
    if len(tendencias_mensuales) >= 2:
        ventas_iniciales = tendencias_mensuales[0]['ventas']
        ventas_finales = tendencias_mensuales[-1]['ventas']
        tendencia_ventas_pct = ((ventas_finales - ventas_iniciales) / ventas_iniciales * 100) if ventas_iniciales > 0 else 0.0

        ingresos_iniciales = tendencias_mensuales[0]['ingresos']
        ingresos_finales = tendencias_mensuales[-1]['ingresos']
        tendencia_ingresos_pct = ((ingresos_finales - ingresos_iniciales) / ingresos_iniciales * 100) if ingresos_iniciales > 0 else 0.0
    else:
        tendencia_ventas_pct = 0.0
        tendencia_ingresos_pct = 0.0

    # Mes con más ventas
    if tendencias_mensuales:
        mejor_mes = max(tendencias_mensuales, key=lambda x: x['ventas'])
        peor_mes = min(tendencias_mensuales, key=lambda x: x['ventas'])
    else:
        mejor_mes = None
        peor_mes = None

    return templates.TemplateResponse("admin_tendencias.html", {
        "request": request,
        "periodo": periodo,
        "periodo_nombre": periodo_nombre,
        "tendencias_mensuales": tendencias_mensuales,
        "tendencias_semanales": tendencias_semanales,
        "tendencias_dia_semana": tendencias_dia_semana,
        "productos_tendencia": productos_tendencia,
        "tendencia_ventas_pct": tendencia_ventas_pct,
        "tendencia_ingresos_pct": tendencia_ingresos_pct,
        "mejor_mes": mejor_mes,
        "peor_mes": peor_mes
    })

@router.get("/reportes/kpis")
async def kpis(
    request: Request,
    periodo: str = "mes-actual",
    db: Session = Depends(get_db),
    current_user: User = Depends(require_same_business_from_cookie)
):
    """Página de KPIs - Indicadores clave de rendimiento"""
    negocio_id = current_user.negocio_id
    now = datetime.now()

    # Determinar período de análisis
    if periodo == "hoy":
        fecha_inicio = now.replace(hour=0, minute=0, second=0, microsecond=0)
        fecha_fin = now
        periodo_nombre = "Hoy"
    elif periodo == "semana-actual":
        fecha_inicio = now - timedelta(days=now.weekday())
        fecha_inicio = fecha_inicio.replace(hour=0, minute=0, second=0, microsecond=0)
        fecha_fin = now
        periodo_nombre = "Semana Actual"
    elif periodo == "mes-actual":
        fecha_inicio = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        fecha_fin = now
        periodo_nombre = "Mes Actual"
    elif periodo == "mes-anterior":
        fecha_fin = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        fecha_inicio = (fecha_fin - timedelta(days=1)).replace(day=1)
        periodo_nombre = "Mes Anterior"
    else:
        fecha_inicio = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        fecha_fin = now
        periodo_nombre = "Mes Actual"

    # Convertir fechas a formato date para comparación consistente
    fecha_inicio_date = fecha_inicio.date()
    fecha_fin_date = fecha_fin.date()

    # KPIs principales
    total_ventas = db.query(func.count(Venta.id)).filter(
        Venta.negocio_id == negocio_id,
        func.date(Venta.fecha_venta) >= fecha_inicio_date,
        func.date(Venta.fecha_venta) <= fecha_fin_date
    ).scalar() or 0

    total_ingresos = db.query(func.sum(Venta.valor_total)).filter(
        Venta.negocio_id == negocio_id,
        func.date(Venta.fecha_venta) >= fecha_inicio_date,
        func.date(Venta.fecha_venta) <= fecha_fin_date
    ).scalar() or 0.0

    total_productos_vendidos = db.query(func.sum(Venta.cantidad_vendida)).filter(
        Venta.negocio_id == negocio_id,
        func.date(Venta.fecha_venta) >= fecha_inicio_date,
        func.date(Venta.fecha_venta) <= fecha_fin_date
    ).scalar() or 0

    # Promedio por venta
    promedio_por_venta = total_ingresos / total_ventas if total_ventas > 0 else 0.0

    # Número de productos diferentes vendidos
    productos_diferentes = db.query(func.count(func.distinct(Venta.producto_id))).filter(
        Venta.negocio_id == negocio_id,
        func.date(Venta.fecha_venta) >= fecha_inicio_date,
        func.date(Venta.fecha_venta) <= fecha_fin_date
    ).scalar() or 0

    # Número de vendedores activos
    vendedores_activos = db.query(func.count(func.distinct(Venta.vendedor_id))).filter(
        Venta.negocio_id == negocio_id,
        func.date(Venta.fecha_venta) >= fecha_inicio_date,
        func.date(Venta.fecha_venta) <= fecha_fin_date
    ).scalar() or 0

    # Top productos del período
    top_productos = db.query(
        Producto.nombre,
        func.sum(Venta.cantidad_vendida).label('cantidad'),
        func.sum(Venta.valor_total).label('ingresos')
    ).join(Venta).filter(
        Producto.negocio_id == negocio_id,
        func.date(Venta.fecha_venta) >= fecha_inicio_date,
        func.date(Venta.fecha_venta) <= fecha_fin_date
    ).group_by(Producto.id).order_by(desc('ingresos')).limit(5).all()

    # Top vendedores del período
    top_vendedores = db.query(
        User.nombre_usuario,
        func.count(Venta.id).label('ventas'),
        func.sum(Venta.valor_total).label('ingresos')
    ).join(Venta).filter(
        User.negocio_id == negocio_id,
        func.date(Venta.fecha_venta) >= fecha_inicio_date,
        func.date(Venta.fecha_venta) <= fecha_fin_date
    ).group_by(User.id).order_by(desc('ingresos')).limit(5).all()

    # KPIs de inventario
    total_productos_inventario = db.query(func.count(Producto.id)).filter(
        Producto.negocio_id == negocio_id
    ).scalar() or 0

    valor_total_inventario = db.query(func.sum(Producto.precio * Producto.cantidad)).filter(
        Producto.negocio_id == negocio_id
    ).scalar() or 0.0

    productos_sin_stock = db.query(func.count(Producto.id)).filter(
        Producto.negocio_id == negocio_id,
        Producto.cantidad == 0
    ).scalar() or 0

    productos_stock_bajo = db.query(func.count(Producto.id)).filter(
        Producto.negocio_id == negocio_id,
        Producto.cantidad > 0,
        Producto.cantidad <= 10
    ).scalar() or 0

    # Cálculos adicionales
    tasa_rotacion_inventario = (total_productos_vendidos / total_productos_inventario * 100) if total_productos_inventario > 0 else 0.0

    # Comparación con período anterior (para crecimiento)
    if periodo == "mes-actual":
        # Comparar con mes anterior
        mes_anterior_fin = fecha_inicio
        mes_anterior_inicio = (mes_anterior_fin - timedelta(days=1)).replace(day=1)
        mes_anterior_inicio_date = mes_anterior_inicio.date()
        mes_anterior_fin_date = mes_anterior_fin.date()

        ventas_anterior = db.query(func.count(Venta.id)).filter(
            Venta.negocio_id == negocio_id,
            func.date(Venta.fecha_venta) >= mes_anterior_inicio_date,
            func.date(Venta.fecha_venta) < mes_anterior_fin_date
        ).scalar() or 0

        ingresos_anterior = db.query(func.sum(Venta.valor_total)).filter(
            Venta.negocio_id == negocio_id,
            func.date(Venta.fecha_venta) >= mes_anterior_inicio_date,
            func.date(Venta.fecha_venta) < mes_anterior_fin_date
        ).scalar() or 0.0

        crecimiento_ventas = ((total_ventas - ventas_anterior) / ventas_anterior * 100) if ventas_anterior > 0 else (100.0 if total_ventas > 0 else 0.0)
        crecimiento_ingresos = ((total_ingresos - ingresos_anterior) / ingresos_anterior * 100) if ingresos_anterior > 0 else (100.0 if total_ingresos > 0 else 0.0)

    elif periodo == "semana-actual":
        # Comparar con semana anterior
        semana_anterior_inicio = fecha_inicio - timedelta(days=7)
        semana_anterior_fin = fecha_inicio
        semana_anterior_inicio_date = semana_anterior_inicio.date()
        semana_anterior_fin_date = semana_anterior_fin.date()

        ventas_anterior = db.query(func.count(Venta.id)).filter(
            Venta.negocio_id == negocio_id,
            func.date(Venta.fecha_venta) >= semana_anterior_inicio_date,
            func.date(Venta.fecha_venta) < semana_anterior_fin_date
        ).scalar() or 0

        ingresos_anterior = db.query(func.sum(Venta.valor_total)).filter(
            Venta.negocio_id == negocio_id,
            func.date(Venta.fecha_venta) >= semana_anterior_inicio_date,
            func.date(Venta.fecha_venta) < semana_anterior_fin_date
        ).scalar() or 0.0

        crecimiento_ventas = ((total_ventas - ventas_anterior) / ventas_anterior * 100) if ventas_anterior > 0 else (100.0 if total_ventas > 0 else 0.0)
        crecimiento_ingresos = ((total_ingresos - ingresos_anterior) / ingresos_anterior * 100) if ingresos_anterior > 0 else (100.0 if total_ingresos > 0 else 0.0)
    else:
        crecimiento_ventas = 0.0
        crecimiento_ingresos = 0.0

    # Formatear datos para templates
    top_productos_data = [
        {
            'nombre': row[0],
            'cantidad': int(row[1]),
            'ingresos': float(row[2])
        }
        for row in top_productos
    ]

    top_vendedores_data = [
        {
            'nombre': row[0],
            'ventas': int(row[1]),
            'ingresos': float(row[2])
        }
        for row in top_vendedores
    ]

    return templates.TemplateResponse("admin_kpis.html", {
        "request": request,
        "periodo": periodo,
        "periodo_nombre": periodo_nombre,
        "total_ventas": total_ventas,
        "total_ingresos": total_ingresos,
        "total_productos_vendidos": total_productos_vendidos,
        "promedio_por_venta": promedio_por_venta,
        "productos_diferentes": productos_diferentes,
        "vendedores_activos": vendedores_activos,
        "total_productos_inventario": total_productos_inventario,
        "valor_total_inventario": valor_total_inventario,
        "productos_sin_stock": productos_sin_stock,
        "productos_stock_bajo": productos_stock_bajo,
        "tasa_rotacion_inventario": tasa_rotacion_inventario,
        "crecimiento_ventas": crecimiento_ventas,
        "crecimiento_ingresos": crecimiento_ingresos,
        "top_productos": top_productos_data,
        "top_vendedores": top_vendedores_data
    })

@router.get("/reportes/dashboard")
async def dashboard_reportes(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_same_business_from_cookie)
):
    """Dashboard general de métricas y KPIs"""
    negocio_id = current_user.negocio_id

    # Métricas generales
    fecha_mes = datetime.now() - timedelta(days=30)

    # Ventas del mes
    ventas_mes = db.query(func.count(Venta.id)).filter(
        Venta.negocio_id == negocio_id,
        Venta.fecha_venta >= fecha_mes
    ).scalar() or 0

    # Ingresos del mes
    ingresos_mes = db.query(func.sum(Venta.valor_total)).filter(
        Venta.negocio_id == negocio_id,
        Venta.fecha_venta >= fecha_mes
    ).scalar() or 0.0

    # Productos vendidos del mes
    productos_vendidos_mes = db.query(func.sum(Venta.cantidad_vendida)).filter(
        Venta.negocio_id == negocio_id,
        Venta.fecha_venta >= fecha_mes
    ).scalar() or 0

    # Stock bajo
    stock_bajo_count = db.query(func.count(Producto.id)).filter(
        Producto.negocio_id == negocio_id,
        Producto.cantidad <= 10,
        Producto.cantidad > 0
    ).scalar() or 0

    # Productos agotados
    agotados_count = db.query(func.count(Producto.id)).filter(
        Producto.negocio_id == negocio_id,
        Producto.cantidad == 0
    ).scalar() or 0

    # Total productos
    total_productos = db.query(func.count(Producto.id)).filter(
        Producto.negocio_id == negocio_id
    ).scalar() or 0

    # Vendedores activos
    vendedores_activos = db.query(func.count(User.id)).filter(
        User.negocio_id == negocio_id,
        User.rol == "vendedor",
        User.estado == "activo"
    ).scalar() or 0

    # Tendencia semanal (últimas 4 semanas)
    semanas = []
    for i in range(4):
        fecha_inicio = datetime.now() - timedelta(days=(i+1)*7)
        fecha_fin = datetime.now() - timedelta(days=i*7)

        ventas_semana = db.query(func.sum(Venta.valor_total)).filter(
            Venta.negocio_id == negocio_id,
            Venta.fecha_venta >= fecha_inicio,
            Venta.fecha_venta < fecha_fin
        ).scalar() or 0.0

        semanas.append({
            'semana': f'Semana {4-i}',
            'ingresos': float(ventas_semana)
        })

    # Top productos del mes
    top_productos = db.query(
        Producto.nombre,
        func.sum(Venta.cantidad_vendida).label('cantidad'),
        func.sum(Venta.valor_total).label('total')
    ).join(Venta).filter(
        Producto.negocio_id == negocio_id,
        Venta.fecha_venta >= fecha_mes
    ).group_by(Producto.id).order_by(desc('total')).limit(5).all()

    top_productos_data = [
        {
            'nombre': row[0],
            'cantidad': int(row[1]),
            'total': float(row[2])
        }
        for row in top_productos
    ]

    return templates.TemplateResponse("admin_dashboard_reportes.html", {
        "request": request,
        "ventas_mes": ventas_mes,
        "ingresos_mes": ingresos_mes,
        "productos_vendidos_mes": productos_vendidos_mes,
        "stock_bajo_count": stock_bajo_count,
        "agotados_count": agotados_count,
        "total_productos": total_productos,
        "vendedores_activos": vendedores_activos,
        "semanas": semanas,
        "top_productos": top_productos_data
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

"""
Autostock - Sistema SaaS para gestión de inventario y ventas en montallantas
Aplicación web responsive con tres niveles de acceso: SuperAdministrador, Administrador y Vendedor
"""

from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import uvicorn

# Importar modelos y configuración de base de datos
from models import engine, get_db
from models import Base

# Importar routers
from routers.auth import router as auth_router
from routers.superadmin import router as superadmin_router
from routers.admin_negocio import router as admin_router
from routers.vendedor import router as vendedor_router

# Crear todas las tablas si no existen
Base.metadata.create_all(bind=engine)

# Crear aplicación FastAPI
app = FastAPI(
    title="Autostock",
    description="Sistema SaaS para gestión de inventario y ventas en negocios de montallantas",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4553", "http://127.0.0.1:4553"],  # Especificar orígenes permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar archivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configurar templates
templates = Jinja2Templates(directory="templates")

# Incluir routers
app.include_router(auth_router, tags=["auth"])
app.include_router(superadmin_router, tags=["superadmin"])
app.include_router(admin_router, tags=["admin"])
app.include_router(vendedor_router, tags=["vendedor"])

# Ruta raíz - redirige al login
@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "autostock"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=4553,
        reload=True,
        log_level="info"
    )

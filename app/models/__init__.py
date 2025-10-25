from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Crear directorio database si no existe
database_dir = os.path.join(os.getcwd(), "database")
if not os.path.exists(database_dir):
    os.makedirs(database_dir)
    print(f"[OK] Directorio database creado: {database_dir}")

DATABASE_URL = "sqlite:///./database/inventario.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Importar todos los modelos para que se registren con Base
from .user import User
from .negocio import Negocio
from .plan import Plan
from .producto import Producto
from .venta import Venta
from .notificacion import Notificacion
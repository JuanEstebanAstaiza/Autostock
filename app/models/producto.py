from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from . import Base

class Producto(Base):
    __tablename__ = "productos"

    id = Column(Integer, primary_key=True, index=True)
    negocio_id = Column(Integer, ForeignKey("negocios.id"), nullable=False)
    nombre = Column(String, nullable=False)
    codigo = Column(String, nullable=False, index=True)  # Código único por negocio
    categoria = Column(String, nullable=True)
    precio = Column(Float, nullable=False)
    cantidad = Column(Integer, default=0)
    proveedor = Column(String, nullable=True)
    fecha_registro = Column(DateTime(timezone=True), server_default=func.now())

    # Relaciones
    negocio = relationship("Negocio", back_populates="productos")
    ventas = relationship("Venta", back_populates="producto")
    notificaciones = relationship("Notificacion", back_populates="producto")

    def __repr__(self):
        return f"<Producto(id={self.id}, nombre='{self.nombre}', codigo='{self.codigo}', cantidad={self.cantidad})>"

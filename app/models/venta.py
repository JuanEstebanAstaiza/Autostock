from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from . import Base

class Venta(Base):
    __tablename__ = "ventas"

    id = Column(Integer, primary_key=True, index=True)
    negocio_id = Column(Integer, ForeignKey("negocios.id"), nullable=False)
    producto_id = Column(Integer, ForeignKey("productos.id"), nullable=False)
    vendedor_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    cantidad_vendida = Column(Integer, nullable=False)
    valor_total = Column(Float, nullable=False)
    fecha_venta = Column(DateTime(timezone=True), server_default=func.now())

    # Relaciones
    negocio = relationship("Negocio", back_populates="ventas")
    producto = relationship("Producto", back_populates="ventas")
    vendedor = relationship("User", back_populates="ventas")

    def __repr__(self):
        return f"<Venta(id={self.id}, producto_id={self.producto_id}, cantidad={self.cantidad_vendida}, total={self.valor_total})>"

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from . import Base

class Notificacion(Base):
    __tablename__ = "notificaciones"

    id = Column(Integer, primary_key=True, index=True)
    negocio_id = Column(Integer, ForeignKey("negocios.id"), nullable=False)
    vendedor_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    producto_id = Column(Integer, ForeignKey("productos.id"), nullable=False)
    cantidad_vendida = Column(Integer, nullable=False)
    mensaje = Column(String, nullable=False)
    leida = Column(Boolean, default=False)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())

    # Relaciones
    negocio = relationship("Negocio", back_populates="notificaciones")
    vendedor = relationship("User", back_populates="notificaciones_enviadas")
    producto = relationship("Producto", back_populates="notificaciones")

    def __repr__(self):
        return f"<Notificacion(id={self.id}, negocio_id={self.negocio_id}, leida={self.leida})>"

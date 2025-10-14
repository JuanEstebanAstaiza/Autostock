from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from . import Base

class Negocio(Base):
    __tablename__ = "negocios"

    id = Column(Integer, primary_key=True, index=True)
    nombre_negocio = Column(String, nullable=False)
    propietario = Column(String, nullable=False)
    fecha_registro = Column(DateTime(timezone=True), server_default=func.now())
    plan_id = Column(Integer, ForeignKey("planes.id"), nullable=True)
    estado_suscripcion = Column(String, default="activo")  # activo, suspendido, vencido
    fecha_vencimiento = Column(DateTime(timezone=True), nullable=True)
    logo = Column(String, nullable=True)  # URL o path del logo
    datos_contacto = Column(Text, nullable=True)  # JSON string con datos de contacto

    # Relaciones
    plan = relationship("Plan", back_populates="negocios")
    usuarios = relationship("User", back_populates="negocio")
    productos = relationship("Producto", back_populates="negocio")
    ventas = relationship("Venta", back_populates="negocio")

    def __repr__(self):
        return f"<Negocio(id={self.id}, nombre='{self.nombre_negocio}', propietario='{self.propietario}')>"

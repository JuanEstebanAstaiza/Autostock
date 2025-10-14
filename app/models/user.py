from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from . import Base

class User(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre_usuario = Column(String, unique=True, index=True, nullable=False)
    contraseña = Column(String, nullable=False)
    rol = Column(String, nullable=False)  # superadmin, admin, vendedor
    negocio_id = Column(Integer, ForeignKey("negocios.id"), nullable=True)
    estado = Column(String, default="activo")  # activo, inactivo
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())

    # Relaciones
    negocio = relationship("Negocio", back_populates="usuarios")
    ventas = relationship("Venta", back_populates="vendedor")

    def __repr__(self):
        return f"<User(id={self.id}, nombre_usuario='{self.nombre_usuario}', rol='{self.rol}')>"

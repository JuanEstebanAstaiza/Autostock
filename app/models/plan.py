from sqlalchemy import Column, Integer, String, Text, Float
from sqlalchemy.orm import relationship
from . import Base

class Plan(Base):
    __tablename__ = "planes"

    id = Column(Integer, primary_key=True, index=True)
    nombre_plan = Column(String, nullable=False)
    descripcion = Column(Text, nullable=True)
    precio = Column(Float, nullable=False)
    duracion_dias = Column(Integer, nullable=False)

    # Relaciones
    negocios = relationship("Negocio", back_populates="plan")

    def __repr__(self):
        return f"<Plan(id={self.id}, nombre='{self.nombre_plan}', precio={self.precio})>"

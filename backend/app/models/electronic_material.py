from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.core.database import Base


class ElectronicMaterial(Base):
    __tablename__ = "electronic_materials"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    file_url = Column(String(255), nullable=False)
    file_type = Column(String(30), nullable=False)
    summary = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="published")
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

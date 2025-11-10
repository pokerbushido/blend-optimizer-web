"""
SQLAlchemy Models
Maps to PostgreSQL tables defined in migrations
"""
from sqlalchemy import Boolean, Column, String, Numeric, Integer, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from app.database import Base


class UserRole(str, enum.Enum):
    """User role enumeration"""
    ADMIN = "admin"
    OPERATORE = "operatore"
    VISUALIZZATORE = "visualizzatore"


class User(Base):
    """User model with role-based access control"""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))
    role = Column(String(20), nullable=False, default=UserRole.VISUALIZZATORE.value, index=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))

    # Relationships
    inventory_uploads = relationship("InventoryUpload", back_populates="uploaded_by_user")


class InventoryUpload(Base):
    """Tracks CSV inventory uploads"""
    __tablename__ = "inventory_uploads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(255), nullable=False)
    upload_timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    total_lots = Column(Integer, nullable=False)
    status = Column(String(50), nullable=False, default="completed")
    notes = Column(Text)

    # Relationships
    uploaded_by_user = relationship("User", back_populates="inventory_uploads")
    lots = relationship("InventoryLot", back_populates="upload", cascade="all, delete-orphan")


class InventoryLot(Base):
    """Inventory lot with quality parameters"""
    __tablename__ = "inventory_lots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    upload_id = Column(UUID(as_uuid=True), ForeignKey("inventory_uploads.id", ondelete="CASCADE"))

    # Identificazione
    article_code = Column(String(50), nullable=False, index=True)
    lot_code = Column(String(100), nullable=False, index=True)
    description = Column(Text)

    # Valori Reali (Real Values)
    dc_real = Column(Numeric(5, 2), index=True)  # Down Cluster %
    fp_real = Column(Numeric(6, 1), index=True)  # Fill Power cuin/oz
    duck_real = Column(Numeric(5, 2), index=True)  # Duck %
    oe_real = Column(Numeric(5, 2))  # OE (Other Elements) %
    feather_real = Column(Numeric(5, 2))  # Feather %
    oxygen_real = Column(Numeric(6, 2))  # Oxygen mg/100g
    turbidity_real = Column(Numeric(6, 2))  # Turbidity mm

    # Valori Nominali (Target/Nominal Values)
    dc_nominal = Column(Numeric(5, 2))
    fp_nominal = Column(Numeric(6, 1))
    standard_nominal = Column(Text)  # Nominal standard specification (e.g., "EN", "USA", "JIS")

    # Qualità Aggiuntiva
    total_fibres = Column(Numeric(5, 2))
    broken = Column(Numeric(5, 2))
    landfowl = Column(Numeric(5, 2))

    # Business Data
    available_kg = Column(Numeric(10, 2), nullable=False, index=True)
    cost_per_kg = Column(Numeric(10, 2))

    # Metadata
    group_code = Column(String(50))  # '3', 'G', etc.
    species = Column(String(50))  # 'O', 'A', 'OA', 'C'
    color = Column(String(50))  # 'B', 'G', 'PW', 'NPW'
    state = Column(String(50))  # 'P', 'M', 'S', 'O'
    certification = Column(String(20))  # 'GWR', 'NWR', etc.
    quality_nominal = Column(Text)  # Full quality description
    lab_notes = Column(Text)

    # Flags
    is_estimated = Column(Boolean, default=False)
    dc_was_imputed = Column(Boolean, default=False)
    fp_was_imputed = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True, index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    upload = relationship("InventoryUpload", back_populates="lots")

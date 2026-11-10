from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

def utc_now():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(String(20), nullable=False) # "ADMIN" hoặc "SALE"
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now)

    # Relationships
    licenses_created = relationship("License", back_populates="creator")
    audit_logs = relationship("AuditLog", back_populates="user")

class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    df = Column(String(19), unique=True, index=True, nullable=False) # XXXX-XXXX-XXXX-XXXX
    model = Column(String(100), nullable=False) # NLS-MT90, MC3300x, Swift 2...
    customer_name = Column(String(150), index=True, nullable=False)
    customer_phone = Column(String(20), index=True, nullable=True)
    customer_email = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    # Relationships
    licenses = relationship("License", back_populates="device", cascade="all, delete-orphan", order_by="desc(License.version)")

class License(Base):
    __tablename__ = "licenses"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False, index=True)
    license_jwt = Column(Text, nullable=False)
    license_type = Column(String(20), nullable=False) # TRIAL, PRO, ENTERPRISE, PERPETUAL
    issued_at = Column(DateTime, nullable=False, default=utc_now)
    expires_at = Column(DateTime, nullable=True) # None nếu là vĩnh viễn
    is_permanent = Column(Boolean, default=False, nullable=False)
    status = Column(String(20), default="ACTIVE", nullable=False, index=True) # ACTIVE, SUPERSEDED, REVOKED
    version = Column(Integer, default=1, nullable=False)
    qr_code_base64 = Column(Text, nullable=False) # Data URI image/png;base64,...
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=utc_now)

    # Relationships
    device = relationship("Device", back_populates="licenses")
    creator = relationship("User", back_populates="licenses_created")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(50), nullable=False) # GENERATE, UPGRADE, REISSUE_VIEW, SEARCH, REVOKE
    target_df = Column(String(19), nullable=True)
    details = Column(Text, nullable=True)
    ip_address = Column(String(50), nullable=True)
    timestamp = Column(DateTime, default=utc_now)

    # Relationships
    user = relationship("User", back_populates="audit_logs")


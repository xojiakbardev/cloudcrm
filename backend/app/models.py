"""SQLAlchemy ORM models for the CRM and infrastructure registry."""
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="agent")  # admin | agent
    created_at = Column(DateTime, default=datetime.utcnow)


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), index=True)
    phone = Column(String(50))
    company = Column(String(255))
    status = Column(String(50), default="lead")  # lead | active | churned
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    deals = relationship("Deal", back_populates="customer", cascade="all, delete-orphan")


class Deal(Base):
    __tablename__ = "deals"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    amount = Column(Float, default=0.0)
    stage = Column(String(50), default="new")  # new | qualified | proposal | won | lost
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    customer = relationship("Customer", back_populates="deals")


class InstanceHeartbeat(Base):
    """Registry of running backend instances for the infrastructure view.

    Each FastAPI container periodically updates its row here so the
    infrastructure dashboard can render the live network topology and show
    how the Nginx load balancer distributes traffic across instances.
    """

    __tablename__ = "instance_heartbeats"

    id = Column(Integer, primary_key=True, index=True)
    instance_id = Column(String(100), unique=True, index=True, nullable=False)
    zone = Column(String(50), default="az-a")
    status = Column(String(20), default="healthy")  # healthy | unhealthy
    request_count = Column(Integer, default=0)
    last_seen = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, default=datetime.utcnow)

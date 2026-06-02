"""Pydantic schemas for request/response validation."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr


# ---- Auth ----
class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    role: str = "agent"


class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    role: str

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---- Customers ----
class CustomerBase(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    status: str = "lead"
    notes: Optional[str] = None


class CustomerCreate(CustomerBase):
    pass


class CustomerOut(CustomerBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ---- Deals ----
class DealBase(BaseModel):
    title: str
    amount: float = 0.0
    stage: str = "new"
    customer_id: int


class DealCreate(DealBase):
    pass


class DealOut(DealBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ---- Dashboard ----
class DashboardStats(BaseModel):
    total_customers: int
    active_customers: int
    total_deals: int
    won_deals: int
    pipeline_value: float
    won_value: float
    deals_by_stage: dict
    customers_by_status: dict


# ---- Infrastructure ----
class InstanceOut(BaseModel):
    instance_id: str
    zone: str
    status: str
    request_count: int
    last_seen: datetime
    started_at: datetime

    class Config:
        from_attributes = True


class TopologyNode(BaseModel):
    id: str
    label: str
    type: str  # gateway | loadbalancer | instance | database
    status: str
    meta: dict = {}


class TopologyEdge(BaseModel):
    source: str
    target: str
    label: Optional[str] = None


class TopologyOut(BaseModel):
    nodes: List[TopologyNode]
    edges: List[TopologyEdge]


class PingResult(BaseModel):
    served_by: str
    zone: str
    request_count: int
    timestamp: datetime

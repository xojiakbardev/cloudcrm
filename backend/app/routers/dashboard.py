"""Aggregated CRM metrics for the dashboard."""
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Customer, Deal, User
from app.schemas import DashboardStats
from app.security import get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
def stats(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    total_customers = db.query(func.count(Customer.id)).scalar() or 0
    active_customers = (
        db.query(func.count(Customer.id)).filter(Customer.status == "active").scalar() or 0
    )
    total_deals = db.query(func.count(Deal.id)).scalar() or 0
    won_deals = db.query(func.count(Deal.id)).filter(Deal.stage == "won").scalar() or 0

    pipeline_value = (
        db.query(func.coalesce(func.sum(Deal.amount), 0.0))
        .filter(Deal.stage.notin_(["won", "lost"]))
        .scalar()
        or 0.0
    )
    won_value = (
        db.query(func.coalesce(func.sum(Deal.amount), 0.0))
        .filter(Deal.stage == "won")
        .scalar()
        or 0.0
    )

    deals_by_stage = {
        stage: count
        for stage, count in db.query(Deal.stage, func.count(Deal.id))
        .group_by(Deal.stage)
        .all()
    }
    customers_by_status = {
        status: count
        for status, count in db.query(Customer.status, func.count(Customer.id))
        .group_by(Customer.status)
        .all()
    }

    return DashboardStats(
        total_customers=total_customers,
        active_customers=active_customers,
        total_deals=total_deals,
        won_deals=won_deals,
        pipeline_value=float(pipeline_value),
        won_value=float(won_value),
        deals_by_stage=deals_by_stage,
        customers_by_status=customers_by_status,
    )

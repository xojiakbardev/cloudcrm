"""Aggregated CRM metrics for the dashboard."""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy import func, extract
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Customer, Deal, Order, OrderItem, Product, User
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

    # ── Orders by status ───────────────────────────────────────────────
    orders_by_status = {
        status: count
        for status, count in db.query(Order.status, func.count(Order.id))
        .group_by(Order.status)
        .all()
    }

    # ── Monthly revenue — last 6 months ───────────────────────────────
    six_months_ago = datetime.utcnow() - timedelta(days=180)
    monthly_rows = (
        db.query(
            extract("year", Order.created_at).label("yr"),
            extract("month", Order.created_at).label("mo"),
            func.coalesce(func.sum(Order.total_amount), 0.0).label("revenue"),
        )
        .filter(Order.created_at >= six_months_ago)
        .filter(Order.status.in_(["delivered", "shipped", "confirmed"]))
        .group_by("yr", "mo")
        .order_by("yr", "mo")
        .all()
    )
    monthly_revenue = {
        f"{int(row.yr)}-{int(row.mo):02d}": float(row.revenue)
        for row in monthly_rows
    }

    # ── Top 5 products by order quantity ──────────────────────────────
    top_products_rows = (
        db.query(
            Product.name,
            func.coalesce(func.sum(OrderItem.quantity), 0).label("qty"),
        )
        .join(OrderItem, OrderItem.product_id == Product.id)
        .group_by(Product.id, Product.name)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(5)
        .all()
    )
    top_products = {
        row.name[:28] + ("…" if len(row.name) > 28 else ""): int(row.qty)
        for row in top_products_rows
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
        orders_by_status=orders_by_status,
        monthly_revenue=monthly_revenue,
        top_products=top_products,
    )

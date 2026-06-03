"""CRUD routes for orders (buyurtmalar)."""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Customer, Order, OrderItem, Product, User
from app.schemas import OrderCreate, OrderOut, OrderUpdate
from app.security import get_current_user

router = APIRouter(prefix="/api/orders", tags=["orders"])


def _recalc_total(order: Order) -> float:
    """Recompute total_amount from items."""
    total = sum(item.unit_price * item.quantity for item in order.items)
    order.total_amount = total
    return total


def _load_order(order_id: int, db: Session) -> Order:
    order = (
        db.query(Order)
        .options(joinedload(Order.items))
        .filter(Order.id == order_id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.get("", response_model=List[OrderOut])
def list_orders(
    status: Optional[str] = None,
    customer_id: Optional[int] = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = db.query(Order).options(joinedload(Order.items))
    if status:
        query = query.filter(Order.status == status)
    if customer_id:
        query = query.filter(Order.customer_id == customer_id)
    return query.order_by(Order.created_at.desc()).all()


@router.post("", response_model=OrderOut, status_code=201)
def create_order(
    payload: OrderCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    customer = db.query(Customer).filter(Customer.id == payload.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    order = Order(
        customer_id=payload.customer_id,
        status=payload.status,
        notes=payload.notes,
        total_amount=0.0,
    )
    db.add(order)
    db.flush()  # get order.id

    for item_in in payload.items:
        product = db.query(Product).filter(Product.id == item_in.product_id).first()
        if not product:
            raise HTTPException(
                status_code=404,
                detail=f"Product {item_in.product_id} not found",
            )
        unit_price = item_in.unit_price if item_in.unit_price > 0 else product.price
        db.add(
            OrderItem(
                order_id=order.id,
                product_id=item_in.product_id,
                quantity=item_in.quantity,
                unit_price=unit_price,
            )
        )

    db.flush()
    db.refresh(order)
    _recalc_total(order)
    db.commit()
    db.refresh(order)
    return order


@router.get("/{order_id}", response_model=OrderOut)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return _load_order(order_id, db)


@router.patch("/{order_id}/status", response_model=OrderOut)
def update_order_status(
    order_id: int,
    payload: OrderUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    order = _load_order(order_id, db)
    order.status = payload.status
    if payload.notes is not None:
        order.notes = payload.notes
    db.commit()
    db.refresh(order)
    return order


@router.delete("/{order_id}", status_code=204)
def delete_order(
    order_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    db.delete(order)
    db.commit()

"""CRUD routes for deals."""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Customer, Deal, User
from app.schemas import DealCreate, DealOut
from app.security import get_current_user

router = APIRouter(prefix="/api/deals", tags=["deals"])


@router.get("", response_model=List[DealOut])
def list_deals(
    stage: Optional[str] = None,
    customer_id: Optional[int] = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = db.query(Deal)
    if stage:
        query = query.filter(Deal.stage == stage)
    if customer_id:
        query = query.filter(Deal.customer_id == customer_id)
    return query.order_by(Deal.created_at.desc()).all()


@router.post("", response_model=DealOut, status_code=201)
def create_deal(
    payload: DealCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    customer = db.query(Customer).filter(Customer.id == payload.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    deal = Deal(**payload.model_dump())
    db.add(deal)
    db.commit()
    db.refresh(deal)
    return deal


@router.put("/{deal_id}", response_model=DealOut)
def update_deal(
    deal_id: int,
    payload: DealCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    deal = db.query(Deal).filter(Deal.id == deal_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    for key, value in payload.model_dump().items():
        setattr(deal, key, value)
    db.commit()
    db.refresh(deal)
    return deal


@router.delete("/{deal_id}", status_code=204)
def delete_deal(
    deal_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    deal = db.query(Deal).filter(Deal.id == deal_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    db.delete(deal)
    db.commit()

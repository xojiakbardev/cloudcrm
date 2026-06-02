"""Seed the database with an admin user and demo CRM data."""
from sqlalchemy.orm import Session

from app.models import Customer, Deal, User
from app.security import hash_password


def seed(db: Session) -> None:
    if db.query(User).count() > 0:
        return

    admin = User(
        email="admin@cloudcrm.dev",
        full_name="Admin User",
        hashed_password=hash_password("admin123"),
        role="admin",
    )
    db.add(admin)

    demo_customers = [
        Customer(name="Akme Textiles", email="info@akme.uz", phone="+998901112233",
                 company="Akme Textiles LLC", status="active",
                 notes="Wholesale apparel buyer, monthly orders."),
        Customer(name="Bella Moda", email="sales@bellamoda.uz", phone="+998901114455",
                 company="Bella Moda", status="lead",
                 notes="Interested in spring collection."),
        Customer(name="Cotton House", email="order@cottonhouse.uz", phone="+998901116677",
                 company="Cotton House Group", status="active",
                 notes="Bulk cotton garments."),
        Customer(name="Denim World", email="hello@denimworld.uz", phone="+998901118899",
                 company="Denim World", status="churned",
                 notes="Switched to another supplier."),
    ]
    db.add_all(demo_customers)
    db.flush()

    demo_deals = [
        Deal(title="Spring wholesale order", amount=12000, stage="won",
             customer_id=demo_customers[0].id),
        Deal(title="Summer collection proposal", amount=8500, stage="proposal",
             customer_id=demo_customers[1].id),
        Deal(title="Q3 cotton supply", amount=15000, stage="qualified",
             customer_id=demo_customers[2].id),
        Deal(title="Reorder negotiation", amount=5000, stage="new",
             customer_id=demo_customers[0].id),
        Deal(title="Denim restock", amount=3000, stage="lost",
             customer_id=demo_customers[3].id),
    ]
    db.add_all(demo_deals)
    db.commit()

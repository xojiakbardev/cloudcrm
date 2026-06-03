"""Seed the database with an admin user and Faker-generated demo CRM data."""
import random

from faker import Faker
from sqlalchemy.orm import Session

from app.models import Customer, Deal, Order, OrderItem, Product, User
from app.security import hash_password

fake = Faker()
Faker.seed(42)
random.seed(42)

CATEGORIES = [
    "Kiyim-kechak",
    "Poyabzal",
    "Aksessuarlar",
    "Sport anjomlar",
    "Elektronika",
    "Uy-ro'zg'or",
    "Go'zallik",
    "Oziq-ovqat",
]

DEAL_STAGES = ["new", "qualified", "proposal", "won", "lost"]
CUSTOMER_STATUSES = ["lead", "active", "churned"]
ORDER_STATUSES = ["pending", "confirmed", "shipped", "delivered", "cancelled"]
ORDER_STATUS_WEIGHTS = [3, 4, 3, 5, 2]
PRODUCT_STATUS_WEIGHTS = ["active"] * 7 + ["draft"] * 2 + ["archived"] * 1


def _fake_phone() -> str:
    return f"+998{random.randint(90, 99)}{random.randint(1000000, 9999999)}"


def _fake_sku(category: str, index: int) -> str:
    prefix = "".join([w[0].upper() for w in category.split("-")])[:3]
    return f"{prefix}-{index:04d}"


def seed(db: Session) -> None:
    if db.query(User).count() > 0:
        return

    # ── Admin user ──────────────────────────────────────────────────────────
    admin = User(
        email="admin@cloudcrm.dev",
        full_name="Admin User",
        hashed_password=hash_password("admin123"),
        role="admin",
    )
    db.add(admin)

    # ── Faker-generated agent users ─────────────────────────────────────────
    agents = []
    for _ in range(5):
        user = User(
            email=fake.unique.email(),
            full_name=fake.name(),
            hashed_password=hash_password("agent123"),
            role="agent",
        )
        db.add(user)
        agents.append(user)

    # ── Faker-generated customers ────────────────────────────────────────────
    customers = []
    for _ in range(30):
        status = random.choices(CUSTOMER_STATUSES, weights=[3, 5, 2], k=1)[0]
        c = Customer(
            name=fake.name(),
            email=fake.unique.company_email(),
            phone=_fake_phone(),
            company=fake.company(),
            status=status,
            notes=fake.sentence(nb_words=12),
        )
        customers.append(c)

    db.add_all(customers)
    db.flush()

    # ── Faker-generated deals ────────────────────────────────────────────────
    deals = []
    for _ in range(50):
        customer = random.choice(customers)
        stage = random.choices(DEAL_STAGES, weights=[2, 3, 3, 4, 2], k=1)[0]
        amount = round(random.uniform(500, 50000), -2)
        deals.append(
            Deal(
                title=fake.bs().title(),
                amount=amount,
                stage=stage,
                customer_id=customer.id,
            )
        )
    db.add_all(deals)

    # ── Faker-generated products ─────────────────────────────────────────────
    products = []
    ADJS = ["Premium", "Classic", "Sport", "Slim", "Comfort", "Eco", "Pro", "Ultra", "Elite", "Basic"]
    for i in range(1, 41):
        category = random.choice(CATEGORIES)
        status = random.choice(PRODUCT_STATUS_WEIGHTS)
        products.append(
            Product(
                name=f"{random.choice(ADJS)} {fake.word().capitalize()} {category}",
                sku=_fake_sku(category, i),
                category=category,
                description=fake.paragraph(nb_sentences=2),
                price=round(random.uniform(5, 999), 2),
                stock=random.randint(0, 500),
                status=status,
            )
        )

    db.add_all(products)
    db.flush()

    # ── Faker-generated orders (60 ta) ───────────────────────────────────────
    active_products = [p for p in products if p.status == "active"] or products

    orders = []
    for _ in range(60):
        customer = random.choice(customers)
        status = random.choices(ORDER_STATUSES, weights=ORDER_STATUS_WEIGHTS, k=1)[0]
        order = Order(
            customer_id=customer.id,
            status=status,
            notes=fake.sentence(nb_words=8) if random.random() > 0.5 else None,
            total_amount=0.0,
        )
        orders.append(order)

    db.add_all(orders)
    db.flush()

    # ── Order items ──────────────────────────────────────────────────────────
    for order in orders:
        chosen = random.sample(active_products, min(random.randint(1, 5), len(active_products)))
        total = 0.0
        for product in chosen:
            qty = random.randint(1, 10)
            unit_price = round(product.price * random.uniform(0.9, 1.1), 2)
            db.add(
                OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    quantity=qty,
                    unit_price=unit_price,
                )
            )
            total += qty * unit_price
        order.total_amount = round(total, 2)

    db.commit()

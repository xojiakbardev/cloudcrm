"""FastAPI application entrypoint for CloudCRM."""
import os
import threading
import time
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import settings
from app.database import Base, SessionLocal, engine
from app.models import InstanceHeartbeat
from app.routers import auth, customers, dashboard, deals, infrastructure, orders, products
from app.seed import seed

# Refresh our heartbeat row this often, regardless of request traffic. The
# infrastructure dashboard uses last_seen to flip instances between healthy
# and unhealthy — without this the row would go stale during idle periods.
HEARTBEAT_REFRESH_SECONDS = 5

app = FastAPI(
    title="CloudCRM API",
    version="1.0.0",
    description="CRM with cloud-networking infrastructure visualisation (BTEC Unit 6).",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(customers.router)
app.include_router(deals.router)
app.include_router(dashboard.router)
app.include_router(infrastructure.router)
app.include_router(orders.router)
app.include_router(products.router)


@app.middleware("http")
async def add_instance_header(request: Request, call_next):
    """Tag every response with the serving instance id (visible in DevTools)."""
    response = await call_next(request)
    response.headers["X-Served-By"] = settings.instance_id
    response.headers["X-Zone"] = settings.instance_zone
    return response


def _wait_for_db(retries: int = 20, delay: float = 1.5) -> None:
    for attempt in range(retries):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(delay)


def _refresh_heartbeat_loop() -> None:
    """Keep our heartbeat row fresh so idle instances don't flip to unhealthy."""
    while True:
        try:
            db = SessionLocal()
            try:
                now = datetime.utcnow()
                updated = (
                    db.query(InstanceHeartbeat)
                    .filter(InstanceHeartbeat.instance_id == settings.instance_id)
                    .update(
                        {
                            InstanceHeartbeat.last_seen: now,
                            InstanceHeartbeat.status: "healthy",
                        },
                        synchronize_session=False,
                    )
                )
                if updated == 0:
                    db.add(
                        InstanceHeartbeat(
                            instance_id=settings.instance_id,
                            zone=settings.instance_zone,
                            status="healthy",
                            request_count=0,
                            last_seen=now,
                            started_at=now,
                        )
                    )
                db.commit()
            finally:
                db.close()
        except Exception:
            # Never let the heartbeat loop kill the process — the next tick retries.
            pass
        time.sleep(HEARTBEAT_REFRESH_SECONDS)


@app.on_event("startup")
def on_startup():
    # In tests the DB is provisioned by fixtures; skip the production bootstrap.
    if os.getenv("TESTING") == "1":
        return
    _wait_for_db()
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed(db)
        # Register this instance immediately so it appears in the topology.
        existing = (
            db.query(InstanceHeartbeat)
            .filter(InstanceHeartbeat.instance_id == settings.instance_id)
            .first()
        )
        now = datetime.utcnow()
        if existing is None:
            db.add(
                InstanceHeartbeat(
                    instance_id=settings.instance_id,
                    zone=settings.instance_zone,
                    status="healthy",
                    request_count=0,
                    last_seen=now,
                    started_at=now,
                )
            )
        else:
            existing.last_seen = now
            existing.started_at = now
            existing.status = "healthy"
        db.commit()
    finally:
        db.close()

    threading.Thread(target=_refresh_heartbeat_loop, daemon=True).start()


@app.get("/api/health")
def health():
    """Liveness probe used by the load balancer and CI."""
    return {"status": "ok", "instance": settings.instance_id, "zone": settings.instance_zone}

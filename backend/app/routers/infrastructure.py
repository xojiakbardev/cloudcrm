"""Infrastructure / cloud-networking routes.

This router powers the CRM "Infrastructure" page that visualises the cloud
network design required by the BTEC Unit 6 brief:

  Internet Gateway -> Nginx Load Balancer -> FastAPI instances -> PostgreSQL

Every request that reaches a FastAPI instance is counted against that
instance's heartbeat row, so the dashboard can show how the load balancer
distributes traffic across instances (round-robin) and how new instances
appear when the service is scaled out (`docker compose up --scale api=N`).
"""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import InstanceHeartbeat, User
from app.schemas import (
    InstanceOut,
    PingResult,
    TopologyEdge,
    TopologyNode,
    TopologyOut,
)
from app.security import get_current_user

router = APIRouter(prefix="/api/infrastructure", tags=["infrastructure"])

# An instance is considered healthy if it sent a heartbeat within this window.
HEALTHY_WINDOW_SECONDS = 15


def _touch_instance(db: Session) -> InstanceHeartbeat:
    """Record that this instance handled a request (heartbeat + counter).

    Uses an atomic UPDATE so concurrent requests do not lose increments.
    The naive read-modify-write pattern hit a classic lost-update race
    under load (Phase 3 testing observed ~49% of increments lost at 50
    concurrent VUs). The UPDATE runs in a single SQL statement and the
    database serialises the increment for us.
    """
    now = datetime.utcnow()
    updated = (
        db.query(InstanceHeartbeat)
        .filter(InstanceHeartbeat.instance_id == settings.instance_id)
        .update(
            {
                InstanceHeartbeat.request_count: InstanceHeartbeat.request_count + 1,
                InstanceHeartbeat.last_seen: now,
                InstanceHeartbeat.status: "healthy",
            },
            synchronize_session=False,
        )
    )
    if updated == 0:
        # First request from this replica — insert the heartbeat row.
        db.add(
            InstanceHeartbeat(
                instance_id=settings.instance_id,
                zone=settings.instance_zone,
                status="healthy",
                request_count=1,
                last_seen=now,
                started_at=now,
            )
        )
    db.commit()
    return (
        db.query(InstanceHeartbeat)
        .filter(InstanceHeartbeat.instance_id == settings.instance_id)
        .first()
    )


def _is_healthy(instance: InstanceHeartbeat) -> bool:
    return instance.last_seen >= datetime.utcnow() - timedelta(seconds=HEALTHY_WINDOW_SECONDS)


@router.get("/ping", response_model=PingResult)
def ping(db: Session = Depends(get_db)):
    """Public, lightweight endpoint used by the frontend to generate load.

    Returns which instance served the request. Hammering this endpoint through
    the Nginx load balancer shows traffic spreading across instances.
    """
    instance = _touch_instance(db)
    return PingResult(
        served_by=instance.instance_id,
        zone=instance.zone,
        request_count=instance.request_count,
        timestamp=datetime.utcnow(),
    )


@router.get("/instances", response_model=list[InstanceOut])
def list_instances(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    """List all known backend instances with live health status."""
    instances = db.query(InstanceHeartbeat).order_by(InstanceHeartbeat.instance_id).all()
    for inst in instances:
        inst.status = "healthy" if _is_healthy(inst) else "unhealthy"
    db.commit()
    return instances


@router.get("/topology", response_model=TopologyOut)
def topology(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    """Build the network topology graph for visualisation.

    Nodes: Internet Gateway -> Load Balancer -> N instances -> Database.
    """
    instances = db.query(InstanceHeartbeat).order_by(InstanceHeartbeat.instance_id).all()

    nodes: list[TopologyNode] = [
        TopologyNode(
            id="gateway",
            label="Internet Gateway",
            type="gateway",
            status="healthy",
            meta={"role": "Ingress / public entrypoint", "port": 80},
        ),
        TopologyNode(
            id="lb",
            label="Nginx Load Balancer",
            type="loadbalancer",
            status="healthy",
            meta={"algorithm": "round-robin", "upstream": "crm_api"},
        ),
        TopologyNode(
            id="db",
            label="PostgreSQL",
            type="database",
            status="healthy",
            meta={"engine": "postgresql", "subnet": "private"},
        ),
    ]
    edges: list[TopologyEdge] = [
        TopologyEdge(source="gateway", target="lb", label="HTTP :80"),
    ]

    total_requests = sum(i.request_count for i in instances) or 1
    for inst in instances:
        healthy = _is_healthy(inst)
        share = round(inst.request_count / total_requests * 100, 1)
        nodes.append(
            TopologyNode(
                id=inst.instance_id,
                label=inst.instance_id,
                type="instance",
                status="healthy" if healthy else "unhealthy",
                meta={
                    "zone": inst.zone,
                    "requests": inst.request_count,
                    "traffic_share": share,
                    "subnet": "private",
                },
            )
        )
        edges.append(
            TopologyEdge(source="lb", target=inst.instance_id, label=f"{share}%")
        )
        edges.append(TopologyEdge(source=inst.instance_id, target="db", label="SQL"))

    return TopologyOut(nodes=nodes, edges=edges)


@router.post("/instances/{instance_id}/drain", response_model=InstanceOut)
def drain_instance(
    instance_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Mark an instance as drained/unhealthy (simulated LB management action).

    In a real environment this would deregister the target from the load
    balancer. Here it flips the status so the topology reflects the change.
    """
    instance = (
        db.query(InstanceHeartbeat)
        .filter(InstanceHeartbeat.instance_id == instance_id)
        .first()
    )
    if instance:
        instance.status = "unhealthy"
        instance.last_seen = datetime.utcnow() - timedelta(seconds=HEALTHY_WINDOW_SECONDS + 1)
        db.commit()
        db.refresh(instance)
    return instance


@router.delete("/instances/{instance_id}", status_code=204)
def deregister_instance(
    instance_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Remove a stale instance row from the registry."""
    instance = (
        db.query(InstanceHeartbeat)
        .filter(InstanceHeartbeat.instance_id == instance_id)
        .first()
    )
    if instance:
        db.delete(instance)
        db.commit()

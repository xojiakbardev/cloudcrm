"""Control-plane API for scaling the CRM API tier.

Exposed under /api/control/* (the Nginx LB routes this prefix to the
controller instead of the API instances). All mutating endpoints require a
valid JWT issued by the CRM backend (shared SECRET_KEY).
"""
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from app.autoscaler import autoscaler
from app.config import settings
from app.docker_manager import manager

app = FastAPI(title="CloudCRM Controller", version="1.0.0")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=True)


def require_auth(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        if payload.get("sub") is None:
            raise JWTError("no subject")
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    return True


class ScaleRequest(BaseModel):
    target: int


class ToggleRequest(BaseModel):
    enabled: bool


@app.on_event("startup")
def _startup():
    autoscaler.start()


@app.get("/api/control/health")
def health():
    return {"status": "ok", "role": "controller"}


@app.get("/api/control/status")
def control_status(_: bool = Depends(require_auth)):
    return {
        "instances": manager.list_api_containers(),
        "count": manager.current_count(),
        "limits": {
            "min": settings.min_instances,
            "max": settings.max_instances,
        },
        "autoscaler": autoscaler.status(),
    }


@app.post("/api/control/scale")
def scale(req: ScaleRequest, _: bool = Depends(require_auth)):
    if req.target < settings.min_instances or req.target > settings.max_instances:
        raise HTTPException(
            status_code=400,
            detail=f"target must be between {settings.min_instances} and {settings.max_instances}",
        )
    result = manager.scale_to(req.target)
    return result


@app.post("/api/control/scale/up")
def scale_up(_: bool = Depends(require_auth)):
    current = manager.current_count()
    if current >= settings.max_instances:
        raise HTTPException(status_code=400, detail=f"already at max ({settings.max_instances})")
    return manager.scale_to(current + 1)


@app.post("/api/control/scale/down")
def scale_down(_: bool = Depends(require_auth)):
    current = manager.current_count()
    if current <= settings.min_instances:
        raise HTTPException(status_code=400, detail=f"already at min ({settings.min_instances})")
    return manager.scale_to(current - 1)


@app.post("/api/control/autoscaler")
def toggle_autoscaler(req: ToggleRequest, _: bool = Depends(require_auth)):
    autoscaler.set_enabled(req.enabled)
    return autoscaler.status()


@app.delete("/api/control/instances/{name}")
def remove_instance(name: str, _: bool = Depends(require_auth)):
    ok = manager.remove_container(name)
    if not ok:
        raise HTTPException(
            status_code=400,
            detail=f"cannot remove (would drop below min={settings.min_instances} or not found)",
        )
    return {"removed": name, "current": manager.current_count()}

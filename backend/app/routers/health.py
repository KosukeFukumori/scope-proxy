from fastapi import APIRouter
from sqlmodel import text

from app.deps import SessionDep
from app.schemas.health import HealthRead

# Intentionally unauthenticated: used by Docker Compose healthcheck and load
# balancer liveness probes, which cannot go through the session-based login flow.
router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health", response_model=HealthRead)
def health(session: SessionDep) -> HealthRead:
    """Return 200 once the app is up and the database is reachable."""
    session.execute(text("SELECT 1"))
    return HealthRead(status="ok")

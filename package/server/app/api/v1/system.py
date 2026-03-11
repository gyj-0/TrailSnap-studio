"""System API routes."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logger import get_logger
from app.core.security import get_current_user_id
from app.db.session import get_db
from app.schemas.common import HealthCheck

router = APIRouter()
logger = get_logger(__name__)


@router.get("/health", response_model=HealthCheck)
async def health_check(
    db: AsyncSession = Depends(get_db),
) -> HealthCheck:
    """System health check endpoint."""
    components = {
        "api": "healthy",
        "version": settings.APP_VERSION,
    }
    
    # Check database connection
    try:
        await db.execute("SELECT 1")
        components["database"] = "healthy"
    except Exception as e:
        components["database"] = f"unhealthy: {str(e)}"
    
    return HealthCheck(
        status="healthy" if all(v == "healthy" for v in components.values() if k != "version") else "degraded",
        version=settings.APP_VERSION,
        timestamp=datetime.now(timezone.utc).isoformat(),
        components=components,
    )


@router.get("/info")
async def system_info(
    current_user_id: str = Depends(get_current_user_id),
) -> dict:
    """Get system information (requires authentication)."""
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
    }


@router.get("/stats")
async def system_stats(
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
) -> dict:
    """Get system statistics (requires authentication)."""
    # TODO: Implement proper statistics
    return {
        "users": 0,
        "albums": 0,
        "photos": 0,
        "storage_used": 0,
    }

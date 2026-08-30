"""API route modules for Scriptorium."""

from services.api.routes.health import router as health_router
from services.api.routes.project import router as project_router

__all__ = [
    "health_router",
    "project_router",
]

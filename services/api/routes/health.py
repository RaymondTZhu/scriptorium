"""Health-check routes for the Scriptorium API."""

from __future__ import annotations

from fastapi import APIRouter


router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict[str, str]:
    """Return a simple API health-check response."""
    return {
        "status": "ok",
        "service": "scriptorium-api",
    }

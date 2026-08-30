"""FastAPI application entrypoint for Scriptorium."""

from __future__ import annotations

from fastapi import FastAPI

from services.api.routes import health_router, project_router


app = FastAPI(
    title="Scriptorium API",
    description="Backend scaffold for consent-based handwriting style synthesis experiments.",
    version="0.1.0",
)

app.include_router(health_router)
app.include_router(project_router)


@app.get("/")
def root() -> dict[str, str]:
    """Return a simple root API response."""
    return {
        "message": "Scriptorium API",
        "docs": "/docs",
    }

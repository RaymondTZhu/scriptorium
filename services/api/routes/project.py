"""Project metadata routes for the Scriptorium API."""

from __future__ import annotations

from fastapi import APIRouter

from packages.common.config import ProjectConfig


router = APIRouter(tags=["project"])


@router.get("/project")
def project_info() -> dict[str, str | bool]:
    """Return basic project configuration and safety defaults."""
    config = ProjectConfig()

    return {
        "project_name": config.project_name,
        "app_env": config.app_env,
        "renderer_version": config.renderer_version,
        "template_version": config.template_version,
        "visible_watermark_enabled": config.visible_watermark_enabled,
        "metadata_provenance_enabled": config.metadata_provenance_enabled,
    }

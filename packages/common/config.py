"""Shared configuration models for Scriptorium."""

from pydantic import BaseModel, Field


class ProjectConfig(BaseModel):
    """Runtime configuration shared across local scripts and future services."""

    project_name: str = Field(default="scriptorium")
    app_env: str = Field(default="development")

    renderer_version: str = Field(default="0.1.0")
    template_version: str = Field(default="0.1.0")

    visible_watermark_enabled: bool = Field(default=True)
    metadata_provenance_enabled: bool = Field(default=True)

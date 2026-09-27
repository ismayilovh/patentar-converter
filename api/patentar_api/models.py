from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CatalogRow(BaseModel):
    """A row returned by the read-only Supabase API views."""

    model_config = ConfigDict(extra="forbid")

    model_id: UUID
    slug: str
    title: str
    description: str | None = None
    model_created_at: datetime
    model_updated_at: datetime
    version_id: UUID
    version_label: str
    storage_bucket: str
    storage_path: str
    sha256: str | None = None
    size_bytes: int | None = Field(default=None, ge=0)
    triangle_count: int | None = Field(default=None, ge=0)
    node_count: int | None = Field(default=None, ge=0)
    converter_version: str | None = None
    version_created_at: datetime


class VersionResponse(BaseModel):
    id: UUID
    label: str
    download_url: str
    sha256: str | None = None
    size_bytes: int | None = None
    triangle_count: int | None = None
    node_count: int | None = None
    converter_version: str | None = None
    created_at: datetime


class ModelResponse(BaseModel):
    id: UUID
    slug: str
    title: str
    description: str | None = None
    version: VersionResponse
    created_at: datetime
    updated_at: datetime


class ModelListResponse(BaseModel):
    items: list[ModelResponse]
    limit: int
    offset: int


class HealthResponse(BaseModel):
    status: str

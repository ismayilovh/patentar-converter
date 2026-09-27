from collections.abc import Sequence
from typing import Protocol
from urllib.parse import quote
from uuid import UUID

import httpx

from .config import Settings
from .models import CatalogRow


class RepositoryError(RuntimeError):
    """Base error for catalog access failures."""


class RepositoryNotConfiguredError(RepositoryError):
    """Raised when required Supabase settings are missing."""


class ModelRepository(Protocol):
    async def healthcheck(self) -> None: ...

    async def list_models(self, limit: int, offset: int) -> Sequence[CatalogRow]: ...

    async def get_current_model(self, slug: str) -> CatalogRow | None: ...

    async def get_model_version(self, slug: str, version_id: UUID) -> CatalogRow | None: ...

    def public_object_url(self, row: CatalogRow) -> str: ...


class SupabaseRepository:
    """Read the public catalog through Supabase's PostgREST Data API."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client: httpx.AsyncClient | None = None

        if settings.supabase_is_configured:
            base_url = f"{settings.supabase_url.strip().rstrip('/')}/rest/v1/"
            self._client = httpx.AsyncClient(
                base_url=base_url,
                headers={
                    "Accept": "application/json",
                    "apikey": settings.supabase_publishable_key.strip(),
                },
                timeout=settings.supabase_timeout_seconds,
            )

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()

    def _require_client(self) -> httpx.AsyncClient:
        if self._client is None:
            raise RepositoryNotConfiguredError(
                "SUPABASE_URL and SUPABASE_PUBLISHABLE_KEY must be configured"
            )
        return self._client

    async def _fetch_rows(self, view: str, params: dict[str, str]) -> list[CatalogRow]:
        client = self._require_client()
        try:
            response = await client.get(view, params=params)
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise RepositoryError("Supabase request timed out") from exc
        except httpx.HTTPStatusError as exc:
            raise RepositoryError(
                f"Supabase returned HTTP {exc.response.status_code}"
            ) from exc
        except httpx.RequestError as exc:
            raise RepositoryError("Supabase could not be reached") from exc

        try:
            return [CatalogRow.model_validate(item) for item in response.json()]
        except (TypeError, ValueError) as exc:
            raise RepositoryError("Supabase returned an invalid catalog response") from exc

    async def healthcheck(self) -> None:
        await self._fetch_rows("api_models", {"select": "*", "limit": "1"})

    async def list_models(self, limit: int, offset: int) -> Sequence[CatalogRow]:
        return await self._fetch_rows(
            "api_models",
            {
                "select": "*",
                "order": "title.asc,model_id.asc",
                "limit": str(limit),
                "offset": str(offset),
            },
        )

    async def get_current_model(self, slug: str) -> CatalogRow | None:
        rows = await self._fetch_rows(
            "api_models",
            {"select": "*", "slug": f"eq.{slug}", "limit": "1"},
        )
        return rows[0] if rows else None

    async def get_model_version(self, slug: str, version_id: UUID) -> CatalogRow | None:
        rows = await self._fetch_rows(
            "api_model_versions",
            {
                "select": "*",
                "slug": f"eq.{slug}",
                "version_id": f"eq.{version_id}",
                "limit": "1",
            },
        )
        return rows[0] if rows else None

    def public_object_url(self, row: CatalogRow) -> str:
        base_url = self._settings.supabase_url.strip().rstrip("/")
        bucket = quote(row.storage_bucket, safe="")
        path = quote(row.storage_path.lstrip("/"), safe="/")
        return f"{base_url}/storage/v1/object/public/{bucket}/{path}"

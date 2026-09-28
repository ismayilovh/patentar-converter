from datetime import UTC, datetime
from uuid import UUID

import httpx
import pytest

from patentar_api.app import create_app
from patentar_api.config import Settings
from patentar_api.models import CatalogRow

MODEL_ID = UUID("11111111-1111-4111-8111-111111111111")
VERSION_ID = UUID("22222222-2222-4222-8222-222222222222")


def catalog_row() -> CatalogRow:
    now = datetime(2026, 9, 28, tzinfo=UTC)
    return CatalogRow(
        model_id=MODEL_ID,
        slug="sample-bearing",
        title="Sample Bearing",
        description="A test model",
        model_created_at=now,
        model_updated_at=now,
        version_id=VERSION_ID,
        version_label="1.0.0",
        storage_bucket="model-results",
        storage_path=f"models/{MODEL_ID}/{VERSION_ID}/model.glb",
        sha256="a" * 64,
        size_bytes=1024,
        triangle_count=120,
        node_count=3,
        converter_version="0.1.0",
        version_created_at=now,
    )


class FakeRepository:
    def __init__(self, row: CatalogRow | None = None) -> None:
        self.row = row

    async def healthcheck(self) -> None:
        return None

    async def list_models(self, limit: int, offset: int):
        return [self.row] if self.row is not None and offset == 0 and limit > 0 else []

    async def get_current_model(self, slug: str):
        return self.row if self.row is not None and self.row.slug == slug else None

    async def get_model_version(self, slug: str, version_id: UUID):
        if self.row is not None and self.row.slug == slug and self.row.version_id == version_id:
            return self.row
        return None

    def public_object_url(self, row: CatalogRow) -> str:
        return (
            "https://project.supabase.co/storage/v1/object/public/"
            f"{row.storage_bucket}/{row.storage_path}"
        )


def app_client(row: CatalogRow | None = None) -> httpx.AsyncClient:
    settings = Settings(
        supabase_url="https://project.supabase.co",
        supabase_publishable_key="sb_publishable_test",
        public_base_url="https://models.example.org",
    )
    app = create_app(settings=settings, repository=FakeRepository(row))
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")


@pytest.mark.anyio
async def test_liveness_and_readiness() -> None:
    async with app_client() as client:
        assert (await client.get("/health/live")).json() == {"status": "ok"}
        assert (await client.get("/health/ready")).json() == {"status": "ready"}


@pytest.mark.anyio
async def test_lists_models_with_immutable_download_url() -> None:
    async with app_client(catalog_row()) as client:
        response = await client.get("/v1/models")

    assert response.status_code == 200
    body = response.json()
    assert body["items"][0]["slug"] == "sample-bearing"
    assert body["items"][0]["version"]["download_url"] == (
        f"https://models.example.org/m/sample-bearing/v/{VERSION_ID}"
    )


@pytest.mark.anyio
async def test_current_model_redirect_is_short_lived() -> None:
    async with app_client(catalog_row()) as client:
        response = await client.get("/m/sample-bearing")

    assert response.status_code == 307
    assert response.headers["location"].endswith(
        f"/model-results/models/{MODEL_ID}/{VERSION_ID}/model.glb"
    )
    assert response.headers["cache-control"] == "public, max-age=60"


@pytest.mark.anyio
async def test_version_redirect_is_immutable() -> None:
    async with app_client(catalog_row()) as client:
        response = await client.get(f"/m/sample-bearing/v/{VERSION_ID}")

    assert response.status_code == 307
    assert "immutable" in response.headers["cache-control"]


@pytest.mark.anyio
async def test_unpublished_or_unknown_model_is_not_found() -> None:
    async with app_client() as client:
        response = await client.get("/v1/models/not-published")

    assert response.status_code == 404


@pytest.mark.anyio
async def test_slug_rejects_unsafe_characters() -> None:
    async with app_client(catalog_row()) as client:
        response = await client.get("/v1/models/NOT_VALID")

    assert response.status_code == 422

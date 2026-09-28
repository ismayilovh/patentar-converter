from datetime import UTC, datetime
from uuid import UUID

import httpx
import pytest

from patentar_api.config import Settings
from patentar_api.repository import (
    RepositoryError,
    RepositoryNotConfiguredError,
    SupabaseRepository,
)

MODEL_ID = UUID("11111111-1111-4111-8111-111111111111")
VERSION_ID = UUID("22222222-2222-4222-8222-222222222222")


def row_payload() -> dict[str, object]:
    now = datetime(2026, 9, 28, tzinfo=UTC).isoformat()
    return {
        "model_id": str(MODEL_ID),
        "slug": "sample-bearing",
        "title": "Sample Bearing",
        "description": None,
        "model_created_at": now,
        "model_updated_at": now,
        "version_id": str(VERSION_ID),
        "version_label": "1.0.0",
        "storage_bucket": "model-results",
        "storage_path": "models/sample bearing/model.glb",
        "sha256": None,
        "size_bytes": 1024,
        "triangle_count": None,
        "node_count": None,
        "converter_version": None,
        "version_created_at": now,
    }


def configured_settings() -> Settings:
    return Settings(
        supabase_url="https://project.supabase.co",
        supabase_publishable_key="sb_publishable_test",
    )


@pytest.mark.anyio
async def test_repository_reads_catalog_with_publishable_key() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["apikey"] == "sb_publishable_test"
        assert request.url.path == "/rest/v1/api_models"
        assert request.url.params["limit"] == "10"
        return httpx.Response(200, json=[row_payload()])

    repository = SupabaseRepository(
        configured_settings(),
        transport=httpx.MockTransport(handler),
    )
    try:
        rows = await repository.list_models(limit=10, offset=0)
    finally:
        await repository.close()

    assert rows[0].slug == "sample-bearing"
    assert repository.public_object_url(rows[0]).endswith(
        "/model-results/models/sample%20bearing/model.glb"
    )


@pytest.mark.anyio
async def test_repository_returns_none_for_unknown_model() -> None:
    repository = SupabaseRepository(
        configured_settings(),
        transport=httpx.MockTransport(lambda _: httpx.Response(200, json=[])),
    )
    try:
        assert await repository.get_current_model("missing") is None
        assert await repository.get_model_version("missing", VERSION_ID) is None
    finally:
        await repository.close()


@pytest.mark.anyio
async def test_repository_rejects_missing_configuration() -> None:
    repository = SupabaseRepository(
        Settings(supabase_url="", supabase_publishable_key="")
    )
    with pytest.raises(RepositoryNotConfiguredError):
        await repository.healthcheck()


@pytest.mark.anyio
async def test_repository_hides_upstream_error_body() -> None:
    repository = SupabaseRepository(
        configured_settings(),
        transport=httpx.MockTransport(
            lambda _: httpx.Response(403, json={"message": "sensitive upstream detail"})
        ),
    )
    try:
        with pytest.raises(RepositoryError, match="HTTP 403") as error:
            await repository.healthcheck()
    finally:
        await repository.close()

    assert "sensitive upstream detail" not in str(error.value)

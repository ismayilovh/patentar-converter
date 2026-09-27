from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Path, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from . import __version__
from .config import Settings
from .models import (
    CatalogRow,
    HealthResponse,
    ModelListResponse,
    ModelResponse,
    VersionResponse,
)
from .repository import ModelRepository, RepositoryError, SupabaseRepository

SLUG_PATTERN = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"


def create_app(
    *,
    settings: Settings | None = None,
    repository: ModelRepository | None = None,
) -> FastAPI:
    runtime_settings = settings or Settings()
    runtime_repository = repository or SupabaseRepository(runtime_settings)
    owns_repository = repository is None

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield
        if owns_repository and isinstance(runtime_repository, SupabaseRepository):
            await runtime_repository.close()

    application = FastAPI(
        title="3DPatentAR Model API",
        version=__version__,
        description=(
            "Public, read-only model catalog and stable GLB resolver. "
            "Models are administered directly in Supabase."
        ),
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=runtime_settings.parsed_cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "HEAD", "OPTIONS"],
        allow_headers=["Accept", "Content-Type"],
    )

    def get_repository() -> ModelRepository:
        return runtime_repository

    RepositoryDependency = Annotated[ModelRepository, Depends(get_repository)]

    def public_url(request: Request, path: str) -> str:
        if runtime_settings.normalized_public_base_url:
            return f"{runtime_settings.normalized_public_base_url}{path}"
        return str(request.base_url).rstrip("/") + path

    def model_response(request: Request, row: CatalogRow) -> ModelResponse:
        download_path = f"/m/{row.slug}/v/{row.version_id}"
        return ModelResponse(
            id=row.model_id,
            slug=row.slug,
            title=row.title,
            description=row.description,
            version=VersionResponse(
                id=row.version_id,
                label=row.version_label,
                download_url=public_url(request, download_path),
                sha256=row.sha256,
                size_bytes=row.size_bytes,
                triangle_count=row.triangle_count,
                node_count=row.node_count,
                converter_version=row.converter_version,
                created_at=row.version_created_at,
            ),
            created_at=row.model_created_at,
            updated_at=row.model_updated_at,
        )

    async def guarded(call):
        try:
            return await call
        except RepositoryError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Model catalog is temporarily unavailable",
            ) from exc

    @application.get("/health/live", response_model=HealthResponse, tags=["health"])
    async def liveness() -> HealthResponse:
        return HealthResponse(status="ok")

    @application.get("/health/ready", response_model=HealthResponse, tags=["health"])
    async def readiness(repo: RepositoryDependency) -> HealthResponse:
        await guarded(repo.healthcheck())
        return HealthResponse(status="ready")

    @application.get("/v1/models", response_model=ModelListResponse, tags=["models"])
    async def list_models(
        request: Request,
        repo: RepositoryDependency,
        limit: Annotated[int, Query(ge=1, le=100)] = 50,
        offset: Annotated[int, Query(ge=0)] = 0,
    ) -> ModelListResponse:
        rows = await guarded(repo.list_models(limit, offset))
        return ModelListResponse(
            items=[model_response(request, row) for row in rows],
            limit=limit,
            offset=offset,
        )

    @application.get("/v1/models/{slug}", response_model=ModelResponse, tags=["models"])
    async def get_model(
        request: Request,
        repo: RepositoryDependency,
        slug: Annotated[str, Path(pattern=SLUG_PATTERN, max_length=80)],
    ) -> ModelResponse:
        row = await guarded(repo.get_current_model(slug))
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
        return model_response(request, row)

    @application.get(
        "/m/{slug}",
        response_class=RedirectResponse,
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        tags=["downloads"],
    )
    async def resolve_current_model(
        repo: RepositoryDependency,
        slug: Annotated[str, Path(pattern=SLUG_PATTERN, max_length=80)],
    ) -> RedirectResponse:
        row = await guarded(repo.get_current_model(slug))
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
        return RedirectResponse(
            repo.public_object_url(row),
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Cache-Control": "public, max-age=60"},
        )

    @application.get(
        "/m/{slug}/v/{version_id}",
        response_class=RedirectResponse,
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        tags=["downloads"],
    )
    async def resolve_model_version(
        repo: RepositoryDependency,
        slug: Annotated[str, Path(pattern=SLUG_PATTERN, max_length=80)],
        version_id: UUID,
    ) -> RedirectResponse:
        row = await guarded(repo.get_model_version(slug, version_id))
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
        return RedirectResponse(
            repo.public_object_url(row),
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Cache-Control": "public, max-age=31536000, immutable"},
        )

    return application


app = create_app()

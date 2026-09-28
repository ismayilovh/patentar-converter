# 3DPatentAR Converter and Model API

This repository contains the 3D model conversion experiments and the public model API used by the 3DPatentAR Unity application. Large research samples are deliberately excluded from Git.

## Current architecture

The web service is intentionally small and has no end-user identity system:

1. An administrator uploads a validated `.glb` file to the public `model-results` bucket in Supabase Storage.
2. The administrator creates the model/version metadata in Supabase Postgres and marks the version ready.
3. Supabase Row Level Security exposes only published models and ready versions to the API's publishable key.
4. The FastAPI service exposes catalog JSON and stable download URLs.
5. Unity scans a QR URL such as `https://models.example.org/m/sample-bearing`; the service redirects it to the current GLB object.

There are no signup, login, token, profile, or browser upload endpoints. The Supabase publishable key identifies the API component; it is not a user credential and has read-only access under RLS. Do not configure a Supabase secret/service-role key for this service.

## API

| Endpoint | Purpose |
| --- | --- |
| `GET /health/live` | Process liveness |
| `GET /health/ready` | Supabase connectivity/readiness |
| `GET /v1/models` | Published model catalog |
| `GET /v1/models/{slug}` | Current published model metadata |
| `GET /m/{slug}` | Stable QR URL for the current model version |
| `GET /m/{slug}/v/{version_id}` | Immutable URL for one model version |
| `GET /docs` | Interactive OpenAPI documentation |

Unpublished models, draft versions, and unknown models all return `404`, so private catalog state is not disclosed.

## Local development

Python 3.12 or newer is required.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
pytest
patentar-api
```

The service listens on port `8080` by default. Configuration is loaded from environment variables:

| Variable | Required | Meaning |
| --- | --- | --- |
| `SUPABASE_URL` | Yes | Supabase project URL |
| `SUPABASE_PUBLISHABLE_KEY` | Yes | `sb_publishable_...` key governed by RLS |
| `PUBLIC_BASE_URL` | Production | Canonical API origin used in returned URLs |
| `CORS_ORIGINS` | No | Comma-separated origins; defaults to `*` |
| `SUPABASE_TIMEOUT_SECONDS` | No | Upstream request timeout; defaults to 10 seconds |

Never commit `.env` or place a Supabase secret key in this service.

After starting the service, run the installed contract check:

```powershell
patentar-verify-api --base-url http://127.0.0.1:8080
```

After a model is published, include its slug to verify both metadata and the stable GLB redirect:

```powershell
patentar-verify-api --base-url http://127.0.0.1:8080 --slug sample-bearing
```

## Supabase setup (manual checkpoint)

The migration at `supabase/migrations/202609280001_model_catalog.sql` creates:

- `models` and `model_versions` tables;
- read-only `api_models` and `api_model_versions` views;
- RLS policies that expose only published/ready records to `anon`;
- a public `model-results` bucket limited to GLB MIME types and 500 MiB objects.

Apply this migration once through the Supabase SQL Editor or a linked Supabase CLI project. This is intentionally not automated because selecting and modifying the correct Supabase project requires the project owner.

Afterward, copy the project URL and publishable key from the Supabase Connect dialog into a local `.env`. Do not use the secret key.

### Manually publish a model

Use this order so the database integrity trigger can verify the current version:

1. Insert a row in `models` with a lowercase hyphenated `slug`; leave `is_published` false and `current_version_id` empty.
2. Note the generated model UUID and choose a never-reused version label such as `1.0.0`.
3. Upload the GLB to `model-results/models/{model_id}/{version_label}/model.glb` with content type `model/gltf-binary` (or `application/octet-stream`).
4. Insert a `model_versions` row with the model UUID, version label, storage path, and status `ready`; note its generated version UUID.
5. Update the model: set `current_version_id` to that version UUID and `is_published` to true.
6. Confirm `/health/ready`, `/v1/models/{slug}`, and `/m/{slug}` before creating the QR code.

Use a new immutable storage path and version UUID for every replacement. Never overwrite a published GLB in place because CDN and client caches can retain the old bytes.

## Container and deployment

The API container is separate from Blender and FreeCAD converter images:

```powershell
docker build -f api/Dockerfile -t patentar-model-api .
docker run --rm -p 8080:8080 --env-file .env patentar-model-api
```

It is compatible with Cloud Run: the process listens on `0.0.0.0` and uses the injected `PORT`. Deploy the API only after the Supabase manual checkpoint is complete, then set the four environment variables in the Cloud Run service. Converter workers should remain separate jobs because they need large native runtimes and very different CPU/memory limits.

The manual GitHub Actions deployment workflow and its required Google Cloud/GitHub configuration are documented in [`deploy/cloud-run.md`](deploy/cloud-run.md). The workflow uses Workload Identity Federation and does not store a downloadable Google service-account key.

## Repository boundaries

- `api/`: lightweight public FastAPI service.
- `supabase/`: versioned database/storage schema.
- `Converter/`: existing Blender/FreeCAD conversion prototype; it is not imported by the API.
- `SampleModels/`: local-only research data, ignored by Git because it is large and may have third-party licensing restrictions.
- `tests/`: API unit/contract tests using an in-memory fake repository.

The Unity application remains in its separate repository and communicates only through HTTPS model URLs.

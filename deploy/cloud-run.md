# Cloud Run deployment checkpoint

The repository contains a manual `Deploy API` GitHub Actions workflow. It uses GitHub OIDC and Google Cloud Workload Identity Federation, so no long-lived Google service-account key is stored in GitHub.

The workflow is deliberately `workflow_dispatch` only. It cannot deploy until an owner selects the Google Cloud project, region, Artifact Registry repository, and public-access policy.

## Required Google Cloud resources

Create or select a Google Cloud project with billing enabled, then:

1. Enable Cloud Run, Artifact Registry, IAM Credentials, Security Token Service, and Cloud Resource Manager APIs.
2. Create a Docker Artifact Registry repository in the same region selected for Cloud Run.
3. Create a deployment service account with the minimum roles needed to push images and deploy the service.
4. Configure a Workload Identity Pool/provider restricted to the exact GitHub repository.
5. Grant that GitHub principal permission to impersonate the deployment service account.
6. Review the deliberate public-access setting in the workflow. It passes `--allow-unauthenticated` because Unity must resolve QR links without a Google identity token.

Follow Google Cloud's Workload Identity Federation documentation rather than creating a downloadable JSON service-account key.

## Required GitHub repository variables

Configure these under **Settings → Secrets and variables → Actions → Variables**:

| Variable | Example/purpose |
| --- | --- |
| `GCP_PROJECT_ID` | Google Cloud project ID |
| `GCP_REGION` | Cloud Run and Artifact Registry region |
| `GCP_ARTIFACT_REPOSITORY` | Docker repository name |
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | Full provider resource name containing the numeric project number |
| `GCP_SERVICE_ACCOUNT` | Deployment service-account email |
| `SUPABASE_URL` | Existing Supabase project URL |
| `SUPABASE_PUBLISHABLE_KEY` | Existing `sb_publishable_...` key; never use the secret key |
| `PUBLIC_BASE_URL` | Optional custom API origin; leave empty for the initial Cloud Run URL |
| `CORS_ORIGINS` | `*` for the public API, or comma-separated browser origins |

The publishable Supabase key is not an administrator credential; database access remains limited by grants and RLS. It is stored as a variable so the deployment workflow can set the Cloud Run environment consistently.

The deployment service account needs permission to push to the selected Artifact Registry repository, deploy Cloud Run revisions, attach the runtime service identity, and set the service's public invoker policy. Do not give the running API service account database or Google Cloud administrator roles; the container only makes HTTPS requests to Supabase.

## First release

1. Push the local `main` branch to GitHub.
2. Confirm the normal `API CI` workflow passes.
3. Open **Actions → Deploy API → Run workflow**.
4. Copy the resulting Cloud Run URL.
5. Run `patentar-verify-api --base-url https://SERVICE_URL`.
6. If using a custom domain, map it in Cloud Run, set `PUBLIC_BASE_URL`, then redeploy.

Do not create QR codes until at least one GLB is uploaded and the version has passed the stable redirect check with `patentar-verify-api --slug MODEL_SLUG`.

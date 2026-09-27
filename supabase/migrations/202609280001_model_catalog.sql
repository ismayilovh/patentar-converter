-- Public, read-only model catalog for 3DPatentAR.
-- Administration remains in the Supabase dashboard; no end-user accounts are used.

create extension if not exists pgcrypto;

create table public.models (
    id uuid primary key default gen_random_uuid(),
    slug text not null unique,
    title text not null,
    description text,
    is_published boolean not null default false,
    current_version_id uuid,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint models_slug_format check (slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$'),
    constraint models_title_not_blank check (length(btrim(title)) > 0)
);

create table public.model_versions (
    id uuid primary key default gen_random_uuid(),
    model_id uuid not null references public.models(id) on delete cascade,
    version_label text not null,
    status text not null default 'draft',
    storage_bucket text not null default 'model-results',
    storage_path text not null,
    sha256 text,
    size_bytes bigint,
    triangle_count bigint,
    node_count bigint,
    converter_version text,
    created_at timestamptz not null default now(),
    constraint model_versions_model_label_unique unique (model_id, version_label),
    constraint model_versions_label_not_blank check (length(btrim(version_label)) > 0),
    constraint model_versions_status_valid check (status in ('draft', 'ready', 'archived')),
    constraint model_versions_glb_path check (
        storage_path ~ '^[A-Za-z0-9._/-]+[.]glb$'
        and storage_path not like '%..%'
        and storage_path not like '/%'
    ),
    constraint model_versions_sha256_valid check (
        sha256 is null or sha256 ~ '^[0-9a-f]{64}$'
    ),
    constraint model_versions_size_valid check (size_bytes is null or size_bytes >= 0),
    constraint model_versions_triangles_valid check (
        triangle_count is null or triangle_count >= 0
    ),
    constraint model_versions_nodes_valid check (node_count is null or node_count >= 0)
);

alter table public.models
    add constraint models_current_version_id_fkey
    foreign key (current_version_id)
    references public.model_versions(id)
    on delete set null;

create index model_versions_model_id_idx on public.model_versions(model_id);
create index model_versions_ready_idx
    on public.model_versions(model_id, created_at desc)
    where status = 'ready';

create or replace function public.set_updated_at()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

create trigger models_set_updated_at
before update on public.models
for each row execute function public.set_updated_at();

create or replace function public.validate_current_model_version()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
    if new.current_version_id is not null and not exists (
        select 1
        from public.model_versions as version
        where version.id = new.current_version_id
          and version.model_id = new.id
          and version.status = 'ready'
    ) then
        raise exception 'current_version_id must reference a ready version of the same model';
    end if;
    return new;
end;
$$;

create trigger models_validate_current_version
before insert or update of current_version_id on public.models
for each row execute function public.validate_current_model_version();

revoke execute on function public.set_updated_at() from public, anon, authenticated;
revoke execute on function public.validate_current_model_version() from public, anon, authenticated;

alter table public.models enable row level security;
alter table public.model_versions enable row level security;

create policy models_public_read
on public.models
for select
to anon
using (is_published);

create policy model_versions_public_read
on public.model_versions
for select
to anon
using (
    status = 'ready'
    and exists (
        select 1
        from public.models
        where models.id = model_versions.model_id
          and models.is_published
    )
);

revoke all on table public.models from anon, authenticated;
revoke all on table public.model_versions from anon, authenticated;
grant select on table public.models to anon;
grant select on table public.model_versions to anon;

create view public.api_model_versions
with (security_invoker = true)
as
select
    model.id as model_id,
    model.slug,
    model.title,
    model.description,
    model.created_at as model_created_at,
    model.updated_at as model_updated_at,
    version.id as version_id,
    version.version_label,
    version.storage_bucket,
    version.storage_path,
    version.sha256,
    version.size_bytes,
    version.triangle_count,
    version.node_count,
    version.converter_version,
    version.created_at as version_created_at
from public.models as model
join public.model_versions as version on version.model_id = model.id
where model.is_published
  and version.status = 'ready';

create view public.api_models
with (security_invoker = true)
as
select versions.*
from public.api_model_versions as versions
join public.models as model on model.id = versions.model_id
where model.current_version_id = versions.version_id;

revoke all on table public.api_models from anon, authenticated;
revoke all on table public.api_model_versions from anon, authenticated;
grant select on table public.api_models to anon;
grant select on table public.api_model_versions to anon;

insert into storage.buckets (
    id,
    name,
    public,
    file_size_limit,
    allowed_mime_types
)
values (
    'model-results',
    'model-results',
    true,
    524288000,
    array['model/gltf-binary', 'application/octet-stream']
)
on conflict (id) do update set
    public = excluded.public,
    file_size_limit = excluded.file_size_limit,
    allowed_mime_types = excluded.allowed_mime_types;

create policy model_results_public_read
on storage.objects
for select
to anon
using (bucket_id = 'model-results');

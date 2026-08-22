# scope-proxy

[日本語](./README.ja.md)

[![CI](https://github.com/KosukeFukumori/scope-proxy/actions/workflows/ci.yml/badge.svg)](https://github.com/KosukeFukumori/scope-proxy/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Python 3.13+](https://img.shields.io/badge/python-3.13%2B-blue.svg)](./backend/pyproject.toml)
[![FastAPI](https://img.shields.io/badge/backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![React 19](https://img.shields.io/badge/frontend-React%2019-61DAFB.svg)](./frontend/package.json)

A wrapper server that sits in front of an existing API server (one that publishes an OpenAPI JSON but has no authentication of its own), providing token-based authorization and proxying.

**No auth server, no OAuth dance, no code changes to the upstream API.** Point scope-proxy at an OpenAPI schema, and it gives every upstream operation a permission you can grant or revoke per token — turning any unauthenticated internal API into a properly access-controlled one in minutes.

## Why scope-proxy?

- **Zero changes to the upstream API** — it doesn't need to know auth exists. scope-proxy sits in front and speaks the exact same URL structure.
- **No OAuth server to run** — tokens are self-service, opaque, and scoped to individual `operationId`s straight from the upstream's own OpenAPI schema. No client registration, no redirect URIs, no identity provider.
- **Schema drift is handled safely** — when the upstream OpenAPI changes, new operations start with zero permissions (allowlist), so nothing is accidentally exposed.
- **Small footprint** — a single FastAPI service + SQLite, deployable as one Docker container with `docker compose up`.

## Features

- Self-service, token-based authorization (not a three-legged OAuth flow)
- Per-token permissions defined at the `operationId` level of the upstream OpenAPI schema
- A proxy that forwards only authorized requests to the upstream server, **preserving the original URL structure**
- Detects changes in the upstream OpenAPI schema and reflects them into permissions on the safe side (allowlist)
- A frontend where logged-in users can issue and manage their own tokens

## Architecture overview

- Everything under the wrapper server's root `/` is proxied to the upstream backend using **exactly the same URL structure** (e.g. the backend's `GET /users/1` is forwarded as-is as `GET /users/1`).
- All admin APIs and the admin UI are reserved under `/_admin/*`. If the upstream OpenAPI schema contains operations starting with `/_admin`, they are excluded from proxying (with a warning) during schema sync.
- Tokens are issued as random opaque strings; only their SHA-256 hash is stored in the database. The raw value is shown only once, at issuance time.

## Setup

### Docker Compose (quickest way to try it out)

For a single-port setup, build the frontend into the backend image and run it with Docker Compose:

```bash
docker compose up --build
```

This serves the whole app (admin UI + proxy) on `http://localhost:8000`. The SQLite database is persisted in the `scope_proxy_db` named volume. To create the initial admin user:

```bash
docker compose exec app .venv/bin/python scripts/create_admin_user.py
```

The script also supports a non-interactive mode: set both `ADMIN_EMAIL` and `ADMIN_PASSWORD` (e.g. as environment variables on the `app` service in `docker-compose.yml`) and it will create the user without prompting, skipping silently if that user already exists. This makes it safe to run automatically on every container startup.

Set a fixed `SECRET_KEY` in `docker-compose.yml` for production use; otherwise a random one is generated on every restart and sessions are invalidated each time.

Once logged in, users can manage their own password from the "Account" page, and add or remove other users from the "Users" page in the admin UI — the CLI script above is only needed to bootstrap the very first user.

### Development

#### Backend

```bash
cd backend
uv sync
uv run scripts/create_admin_user.py  # create the initial admin user
uv run uvicorn app.main:app --reload
```

Database schema migrations run automatically on startup (see [Database migrations](#database-migrations) below).

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

The admin UI follows the OS color scheme setting and supports both light and dark modes.

During development, frontend requests to `/_admin/api/*` are proxied to the backend (`http://127.0.0.1:8000`) via the `vite.config.ts` configuration. Start the backend before running `npm run dev`.

The production build (`npm run build`) output is served from `/_admin/` by `backend/app/main.py` (as an SPA, any path without a matching file falls back to `index.html`).

## Database migrations

`backend/migrations/` holds numbered, idempotent SQL files (`0001_initial.sql`, `0002_xxx.sql`, ...). On every startup (`app.main.lifespan` → `app.db.init_db`), `app.migration_runner.run_migrations` applies any files not yet recorded in the `schema_migrations` table, in filename order. There is no separate migration command to run manually — adding a new numbered `.sql` file under `backend/migrations/` is enough; it gets applied automatically the next time the app starts.

## Health check

`GET /_admin/api/health` is unauthenticated and returns `{"status": "ok"}` once the app is up and the database is reachable. It's registered before the catch-all proxy router, so it's exempt from authentication. Use it for Docker Compose `healthcheck` and load balancer liveness probes (see `docker-compose.yml` and `Dockerfile` for the built-in `HEALTHCHECK`).

## Environment variables (backend/.env)

See `backend/.env.example`.

## Tests

```bash
cd backend
uv run pytest
uv run ruff check .
```

```bash
cd frontend
npm run lint
npm run build
```

## Security notes

- Requests to unmatched paths/methods are denied by default (404).
- Newly added operations have no permissions by default (allowlist).
- Removed operations are soft-deleted (`is_active=false`) and are always denied.

## License

[MIT](./LICENSE)

# ![scope-proxy logo](./frontend/public/favicon.svg) scope-proxy

[日本語](./README.ja.md)

[![CI](https://github.com/KosukeFukumori/scope-proxy/actions/workflows/ci.yml/badge.svg)](https://github.com/KosukeFukumori/scope-proxy/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Python 3.13+](https://img.shields.io/badge/python-3.13%2B-blue.svg)](./backend/pyproject.toml)
[![FastAPI](https://img.shields.io/badge/backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![React 19](https://img.shields.io/badge/frontend-React%2019-61DAFB.svg)](./frontend/package.json)

A wrapper server that sits in front of an existing API server (one that publishes an OpenAPI JSON but has no authentication of its own), providing token-based authorization and proxying.

**No auth server, no OAuth dance, no code changes to the upstream API.** Point scope-proxy at an OpenAPI schema, and it gives every upstream operation a permission you can grant or revoke per token — turning any unauthenticated internal API into a properly access-controlled one in minutes.

## Demo

**[Try the admin UI demo](https://kosukefukumori.github.io/scope-proxy/)** — login: `admin` / `demo-password`

This is a static build of the admin UI hosted on GitHub Pages, with all API calls answered by mock data in the browser (see `frontend/src/demo/mockApi.ts`). There is no real backend behind it — nothing you do there is persisted beyond your browser tab, and it exists only to let you click through the screens. To try scope-proxy itself, see [Quick start](#quick-start-pre-built-image) below.

## Why scope-proxy?

- **Zero changes to the upstream API** — it doesn't need to know auth exists. scope-proxy sits in front and speaks the exact same URL structure.
- **No OAuth server to run** — tokens are self-service, opaque, and scoped to individual `operationId`s straight from the upstream's own OpenAPI schema. No client registration, no redirect URIs, no identity provider.
- **Schema drift is handled safely** — when the upstream OpenAPI changes, new operations start with zero permissions (allowlist), so nothing is accidentally exposed.
- **Small footprint** — a single FastAPI service + SQLite, deployable as one Docker container with `docker compose up`.

## Features

- Self-service, token-based authorization (not a three-legged OAuth flow)
- Per-token permissions defined at the `operationId` level of the upstream OpenAPI schema
- A proxy that forwards only authorized requests to the upstream server, **preserving the original URL structure**
- Detects changes in the upstream OpenAPI schema and reflects them into permissions on the safe side (allowlist), either via the dashboard's manual "Refresh now" button or an optional periodic background sync (`SCHEMA_SYNC_INTERVAL_SECONDS`)
- A frontend where logged-in users can issue and manage their own tokens

## Architecture overview

- Everything under the wrapper server's root `/` is proxied to the upstream backend using **exactly the same URL structure** (e.g. the backend's `GET /users/1` is forwarded as-is as `GET /users/1`).
- All admin APIs and the admin UI are reserved under `/_admin/*`. If the upstream OpenAPI schema contains operations starting with `/_admin`, they are excluded from proxying (with a warning) during schema sync.
- Tokens are issued as random opaque strings; only their SHA-256 hash is stored in the database. The raw value is shown only once, at issuance time.

## Setup

### Quick start (pre-built image)

The fastest way to try scope-proxy is to pull the pre-built image from GHCR and run it directly — no need to clone this repo. Multi-arch (`linux/amd64`, `linux/arm64`) images are published on every tagged release via `.github/workflows/docker-publish.yml`.

```bash
docker pull ghcr.io/kosukefukumori/scope-proxy:latest

docker run -d --name scope-proxy \
  -p 8000:8000 \
  -v scope_proxy_db:/app/backend/data \
  -e DATABASE_URL=sqlite:////app/backend/data/scope_proxy.db \
  ghcr.io/kosukefukumori/scope-proxy:latest
```

This serves the whole app (admin UI + proxy) on `http://localhost:8000`. The SQLite database is persisted in the `scope_proxy_db` named volume. Open `http://localhost:8000/_admin/` — as long as no account exists yet, you'll be shown a setup screen to create the admin username and password on the spot.

For production use, also set a fixed `SECRET_KEY` (via `-e SECRET_KEY=...`); otherwise a random one is generated on every restart and sessions are invalidated each time.

### Docker Compose

If you've cloned this repo, Docker Compose gives you a config file to keep your settings in instead of a long `docker run` command. `docker-compose.yml` builds the image locally by default; to use the pre-built image from GHCR instead, replace the `build:` block with `image: ghcr.io/kosukefukumori/scope-proxy:latest`.

```bash
docker compose up --build
```

There are two ways to create the initial admin account:

- **Interactively**: just open `http://localhost:8000/_admin/`. As long as no account exists yet, you'll be shown a setup screen to create the admin username and password on the spot.
- **Via environment variables** (useful for unattended/scripted deployments): set both `ADMIN_USERNAME` and `ADMIN_PASSWORD_HASH` (e.g. as environment variables on the `app` service in `docker-compose.yml`). On startup, if no user exists yet, the app creates that account automatically; if a user already exists, these variables are ignored. `ADMIN_PASSWORD_HASH` must be a **bcrypt hash**, not a plaintext password — generate one with:

  ```bash
  docker compose exec app .venv/bin/python -c "import bcrypt, getpass; print(bcrypt.hashpw(getpass.getpass().encode(), bcrypt.gensalt()).decode())"
  ```

  Paste the resulting hash as `ADMIN_PASSWORD_HASH`.

Set a fixed `SECRET_KEY` in `docker-compose.yml` for production use; otherwise a random one is generated on every restart and sessions are invalidated each time.

scope-proxy has a single admin account; once logged in, it can be renamed and have its password changed from the "Account" page — `ADMIN_USERNAME`/`ADMIN_PASSWORD_HASH` and the setup screen are only used to bootstrap that initial account.

### Development

#### Backend

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload
```

Database schema migrations run automatically on startup (see [Database migrations](#database-migrations) below). Open `http://127.0.0.1:8000/_admin/` and use the setup screen to create the initial admin account (or set `ADMIN_USERNAME`/`ADMIN_PASSWORD_HASH` beforehand — see [Environment variables](#environment-variables-backendenv)).

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

CORS is disabled by default (`CORS_ALLOWED_ORIGINS` empty), which is the safe default: every request, including a browser's CORS preflight `OPTIONS`, goes through the normal auth flow and is denied without a bearer token — this also means the proxy **cannot** be called directly from a browser-based SPA. To allow that, set `CORS_ALLOWED_ORIGINS` to a comma-separated list of allowed origins; preflight requests from those origins are then answered before hitting auth/routing.

`ADMIN_USERNAME` and `ADMIN_PASSWORD_HASH` bootstrap the initial admin account non-interactively; both must be set together, and they only take effect while no account exists yet. `ADMIN_PASSWORD_HASH` must be a bcrypt hash, generated with:

```bash
cd backend
uv run python -c "import bcrypt, getpass; print(bcrypt.hashpw(getpass.getpass().encode(), bcrypt.gensalt()).decode())"
```

If these are left unset, the first visit to the admin UI shows a setup screen to create the account interactively instead.

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
- CORS is disabled by default; enabling it via `CORS_ALLOWED_ORIGINS` only affects the preflight `OPTIONS` handshake — actual requests still require a valid bearer token.

## License

[MIT](./LICENSE)

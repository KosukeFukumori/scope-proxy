# scope-proxy

[日本語](./README.ja.md)

A wrapper server that sits in front of an existing API server (one that publishes an OpenAPI JSON but has no authentication of its own), providing token-based authorization and proxying.

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

### Backend

```bash
cd backend
uv sync
uv run scripts/create_admin_user.py  # create the initial admin user
uv run uvicorn app.main:app --reload
```

Database schema migrations run automatically on startup (see [Database migrations](#database-migrations) below).

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The admin UI follows the OS color scheme setting and supports both light and dark modes.

During development, frontend requests to `/_admin/api/*` are proxied to the backend (`http://127.0.0.1:8000`) via the `vite.config.ts` configuration. Start the backend before running `npm run dev`.

The production build (`npm run build`) output is served from `/_admin/` by `backend/app/main.py` (as an SPA, any path without a matching file falls back to `index.html`).

### Docker Compose

For a single-port setup, build the frontend into the backend image and run it with Docker Compose:

```bash
docker compose up --build
```

This serves the whole app (admin UI + proxy) on `http://localhost:8000`. The SQLite database is persisted in the `scope_proxy_db` named volume. To create the initial admin user:

```bash
docker compose exec app .venv/bin/python scripts/create_admin_user.py
```

Set a fixed `SECRET_KEY` in `docker-compose.yml` for production use; otherwise a random one is generated on every restart and sessions are invalidated each time.

## Database migrations

`backend/migrations/` holds numbered, idempotent SQL files (`0001_initial.sql`, `0002_xxx.sql`, ...). On every startup (`app.main.lifespan` → `app.db.init_db`), `app.migration_runner.run_migrations` applies any files not yet recorded in the `schema_migrations` table, in filename order. There is no separate migration command to run manually — adding a new numbered `.sql` file under `backend/migrations/` is enough; it gets applied automatically the next time the app starts.

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

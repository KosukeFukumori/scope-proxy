# --- Stage 1: build the frontend SPA ---
FROM node:22-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# --- Stage 2: backend runtime, serving the built frontend ---
FROM python:3.13-slim AS backend
WORKDIR /app/backend

# Install uv (used to manage the Python environment, per project convention).
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev

COPY backend/ ./
COPY --from=frontend-build /app/frontend/dist /app/frontend/dist

EXPOSE 8000

# Use the stdlib instead of curl to avoid adding an extra apt package just for this.
# A failed request raises, which makes python3 exit non-zero on its own.
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/_admin/api/health', timeout=2)"

# Call the venv's uvicorn directly rather than "uv run", which would
# otherwise re-sync dev dependencies (pytest, ruff, ...) on every start.
CMD [".venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

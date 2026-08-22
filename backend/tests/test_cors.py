"""Tests for the CORS preflight behavior described in issue #13.

By default CORS is disabled (`CORS_ALLOWED_ORIGINS` empty) and a browser's preflight
`OPTIONS` request is treated like any other request: it goes through the normal auth
flow and is denied (401) without a bearer token. When `CORS_ALLOWED_ORIGINS` lists the
requesting origin, `CORSMiddleware` must short-circuit the preflight before it reaches
auth/routing, so it responds 200 without requiring a bearer token.
"""

from httpx import ASGITransport, AsyncClient

from app.config import Settings
from app.main import app as default_app
from app.main import create_app


async def test_preflight_options_is_unauthorized_when_cors_disabled(
    client: AsyncClient,
) -> None:
    """Default settings (no CORS_ALLOWED_ORIGINS): preflight OPTIONS still requires auth."""
    response = await client.options(
        "/users/1",
        headers={
            "Origin": "https://app.example.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 401
    assert "access-control-allow-origin" not in response.headers


async def test_default_app_has_no_cors_middleware() -> None:
    """The process-wide singleton app (built with default settings) has CORS disabled."""
    from starlette.middleware.cors import CORSMiddleware

    assert not any(m.cls is CORSMiddleware for m in default_app.user_middleware)


async def test_preflight_options_is_allowed_when_origin_is_configured() -> None:
    """With CORS_ALLOWED_ORIGINS set, preflight OPTIONS from an allowed origin gets 200
    without needing a bearer token or DB access, because CORSMiddleware short-circuits
    it before auth/routing runs.
    """
    cors_app = create_app(Settings(cors_allowed_origins="https://app.example.com"))

    transport = ASGITransport(app=cors_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        response = await ac.options(
            "/users/1",
            headers={
                "Origin": "https://app.example.com",
                "Access-Control-Request-Method": "GET",
            },
        )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://app.example.com"


async def test_preflight_options_is_rejected_for_unlisted_origin() -> None:
    """An origin that isn't in the allowlist doesn't get CORS headers back."""
    cors_app = create_app(Settings(cors_allowed_origins="https://app.example.com"))

    transport = ASGITransport(app=cors_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        response = await ac.options(
            "/users/1",
            headers={
                "Origin": "https://not-allowed.example.com",
                "Access-Control-Request-Method": "GET",
            },
        )

    assert "access-control-allow-origin" not in response.headers

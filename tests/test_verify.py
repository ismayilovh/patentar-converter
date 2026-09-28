import httpx
import pytest

from patentar_api.verify import VerificationError, verify


def test_verify_accepts_healthy_empty_catalog() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        responses = {
            "/health/live": {"status": "ok"},
            "/health/ready": {"status": "ready"},
            "/v1/models": {"items": [], "limit": 50, "offset": 0},
        }
        return httpx.Response(200, json=responses[request.url.path])

    assert verify("https://models.example.org", transport=httpx.MockTransport(handler)) == 0


def test_verify_checks_model_and_stable_redirect() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/health/live":
            return httpx.Response(200, json={"status": "ok"})
        if request.url.path == "/health/ready":
            return httpx.Response(200, json={"status": "ready"})
        if request.url.path == "/v1/models":
            return httpx.Response(200, json={"items": [], "limit": 50, "offset": 0})
        if request.url.path == "/v1/models/sample-bearing":
            return httpx.Response(200, json={"slug": "sample-bearing"})
        if request.url.path == "/m/sample-bearing":
            return httpx.Response(307, headers={"location": "https://storage/model.glb"})
        raise AssertionError(f"Unexpected request: {request.url}")

    assert (
        verify(
            "https://models.example.org",
            "sample-bearing",
            transport=httpx.MockTransport(handler),
        )
        == 0
    )


def test_verify_rejects_unready_service() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/health/live":
            return httpx.Response(200, json={"status": "ok"})
        return httpx.Response(503, json={"detail": "unavailable"})

    with pytest.raises(VerificationError, match="HTTP 503"):
        verify("https://models.example.org", transport=httpx.MockTransport(handler))

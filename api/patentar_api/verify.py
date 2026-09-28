import argparse
import sys
from collections.abc import Sequence

import httpx


class VerificationError(RuntimeError):
    """Raised when a deployed API does not satisfy its public contract."""


def require_ok(client: httpx.Client, path: str) -> httpx.Response:
    response = client.get(path)
    if response.status_code != 200:
        raise VerificationError(f"GET {path} returned HTTP {response.status_code}")
    return response


def verify(
    base_url: str,
    slug: str | None = None,
    *,
    transport: httpx.BaseTransport | None = None,
) -> int:
    with httpx.Client(
        base_url=base_url.rstrip("/"),
        follow_redirects=False,
        timeout=15,
        transport=transport,
    ) as client:
        live = require_ok(client, "/health/live").json()
        ready = require_ok(client, "/health/ready").json()
        catalog = require_ok(client, "/v1/models").json()

        if live != {"status": "ok"}:
            raise VerificationError("Liveness response does not match the API contract")
        if ready != {"status": "ready"}:
            raise VerificationError("Readiness response does not match the API contract")
        if not isinstance(catalog.get("items"), list):
            raise VerificationError("Catalog response does not contain an items list")

        print(f"API ready; {len(catalog['items'])} published model(s) found.")

        if slug:
            model = require_ok(client, f"/v1/models/{slug}").json()
            if model.get("slug") != slug:
                raise VerificationError("Model response slug does not match the request")

            redirect = client.get(f"/m/{slug}")
            if redirect.status_code != 307 or not redirect.headers.get("location"):
                raise VerificationError("Stable model URL did not return a redirect")
            print(f"Model '{slug}' resolves to a GLB object URL.")

    return 0


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify a deployed 3DPatentAR Model API")
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8080",
        help="API origin without a trailing path",
    )
    parser.add_argument(
        "--slug",
        help="Optional published model slug to verify through the stable redirect",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        return verify(args.base_url, args.slug)
    except (httpx.HTTPError, ValueError, VerificationError) as exc:
        print(f"Verification failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

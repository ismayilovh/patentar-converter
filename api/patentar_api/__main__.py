import os

import uvicorn


def main() -> None:
    """Run the API using the port supplied by Cloud Run or the local environment."""
    uvicorn.run(
        "patentar_api.app:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8080")),
        proxy_headers=True,
    )


if __name__ == "__main__":
    main()

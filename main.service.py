import argparse
import os

import uvicorn

DEFAULT_HOST = os.getenv("BAAS_SERVICE_HOST", "127.0.0.1")
DEFAULT_PORT = int(os.getenv("BAAS_SERVICE_PORT", "8190"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Start BAAS service mode backend")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Host to bind (default: %(default)s)")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port to bind (default: %(default)s)")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload (development only)")
    parser.add_argument("--log-level", default="info", help="Uvicorn log level")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = uvicorn.Config(
        "service.app:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level,
    )
    server = uvicorn.Server(config)
    server.run()


if __name__ == "__main__":
    main()


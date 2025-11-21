import argparse
import os

import uvicorn

DEFAULT_HOST = os.getenv("BAAS_SERVICE_HOST", "127.0.0.1")
DEFAULT_PORT = int(os.getenv("BAAS_SERVICE_PORT", "8190"))

import logging, re

ANSI_ESCAPE = re.compile(r'\x1b\[([0-9;]*[mGKH])')

STATUS_TERMINAL = {
    logging.INFO: "   INFO",
    logging.WARNING: " WARNING",
    logging.ERROR: "   ERROR",
    logging.CRITICAL: "CRITICAL",
}

class PlainFormatter(logging.Formatter):
    def format(self, record):
        level = STATUS_TERMINAL.get(record.levelno, "   INFO")
        log_fmt = f"{level} | %(asctime)s | %(message)s"
        formatter = logging.Formatter(log_fmt, "%Y-%m-%d %H:%M:%S")
        output = formatter.format(record)

        return ANSI_ESCAPE.sub('', output)


handler = logging.StreamHandler()
handler.setFormatter(PlainFormatter())

root = logging.getLogger()
root.setLevel(logging.INFO)
root.handlers = [handler]




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
        log_config=None
    )
    server = uvicorn.Server(config)
    server.run()


if __name__ == "__main__":
    main()

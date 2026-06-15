import argparse
import os

import uvicorn
from service import set_log_format

DEFAULT_HOST = os.getenv("BAAS_SERVICE_HOST", "0.0.0.0")
DEFAULT_PORT = int(os.getenv("BAAS_SERVICE_PORT", "8190"))
OCR_UPDATE_CHECK_ENV = "BAAS_SERVICE_OCR_UPDATE_CHECK"


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() not in {"0", "false", "no", "off"}


def save_pid(pid):
    with open(".pid", "w") as f:
        f.write(str(pid))


def delete_pid_file():
    if os.path.exists(".pid"):
        os.remove(".pid")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Start BAAS service mode backend")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Host to bind (default: %(default)s)")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port to bind (default: %(default)s)")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload (development only)")
    parser.add_argument("--log-level", default="info", help="Uvicorn log level")
    ocr_update_check_default = _env_bool(OCR_UPDATE_CHECK_ENV, True)
    parser.add_argument(
        "--ocr-update-check",
        dest="ocr_update_check",
        action="store_true",
        default=ocr_update_check_default,
        help="Check for OCR server updates during startup (default: %(default)s)",
    )
    parser.add_argument(
        "--no-ocr-update-check",
        dest="ocr_update_check",
        action="store_false",
        help="Skip OCR server update check during startup",
    )
    return parser.parse_args()


def main() -> None:
    try:
        set_log_format()
        args = parse_args()
        os.environ[OCR_UPDATE_CHECK_ENV] = "1" if args.ocr_update_check else "0"
        config = uvicorn.Config(
            "service.app:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            log_level=args.log_level,
            log_config=None
        )
        server = uvicorn.Server(config)
        save_pid(os.getpid())
        server.run()
    finally:
        delete_pid_file()


if __name__ == "__main__":
    main()

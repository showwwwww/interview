import logging
from pathlib import Path

_LOG_DIR = Path(__file__).resolve().parent.parent
_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
_configured = False


def _configure_root():
    global _configured
    if _configured:
        return
    _configured = True

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter(_LOG_FORMAT))
    root.addHandler(console)

    file_handler = logging.FileHandler(_LOG_DIR / "converter.log", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(_LOG_FORMAT))
    root.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    _configure_root()
    return logging.getLogger(name)

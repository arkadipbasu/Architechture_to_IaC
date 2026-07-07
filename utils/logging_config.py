"""
Logging configuration for Arch2IaC using loguru.
"""
import sys
import os
from datetime import datetime
from loguru import logger

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, f"arch2iac_{datetime.now().strftime('%Y%m%d')}.log")


def setup_logger():
    """Configure loguru logger."""
    logger.remove()  # Remove default handler

    # Console — human-readable
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> — <level>{message}</level>",
        level="INFO",
        colorize=True,
    )

    # File — detailed JSON-structured
    logger.add(
        LOG_FILE,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} — {message}",
        level="DEBUG",
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        enqueue=True,
    )

    logger.info(f"Logger initialized. Log file: {LOG_FILE}")
    return logger


def get_log_contents(n_lines: int = 100) -> str:
    """Read last N lines from log file."""
    try:
        with open(LOG_FILE, "r") as f:
            lines = f.readlines()
        return "".join(lines[-n_lines:])
    except FileNotFoundError:
        return "No log file found yet."
    except Exception as e:
        return f"Error reading logs: {e}"


def get_log_file_path() -> str:
    return LOG_FILE


# Initialize on import
setup_logger()

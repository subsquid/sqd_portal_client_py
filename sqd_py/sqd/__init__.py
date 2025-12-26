"""SQD Portal Client - Lightweight Python client for querying blockchain data."""

import logging
import sys

from .dataset import Dataset
from .query.evm import fields as EvmFields  # noqa: N812
from .query.solana import fields as SolanaFields  # noqa: N812
from .sqd import SQD

__version__ = "0.1.0"
__all__ = [
    "SQD",
    "Dataset",
    "EvmFields",
    "SolanaFields",
    "__version__",
    "setup_logging",
]


class ColoredFormatter(logging.Formatter):
    """Formatter with ANSI color codes for log levels."""

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[1;31m",  # Bold Red
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.RESET}"
        result = super().format(record)
        record.levelname = levelname  # Reset for reuse
        return result


def setup_logging(level: int = logging.INFO) -> None:
    """
    Configure logging for the SQD client.

    Args:
        level: Logging level (default: logging.INFO)
        colors: Enable colored output (default: True, auto-disabled if not TTY)

    Example:
        import sqd
        sqd.setup_logging()  # Enable INFO level logging with colors
        sqd.setup_logging(logging.DEBUG)  # Enable DEBUG level logging
        sqd.setup_logging(colors=False)  # Disable colors
    """
    # Remove existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Use stdout instead of stderr to avoid red text in some terminals
    handler = logging.StreamHandler(sys.stdout)

    fmt = "\r%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    handler.setFormatter(ColoredFormatter(fmt))

    root_logger.addHandler(handler)
    root_logger.setLevel(level)


if not logging.root.handlers:
    setup_logging()

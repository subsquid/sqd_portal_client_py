from dataclasses import asdict
from logging import getLogger

import aiohttp
import ujson

from sqd.dataset import Dataset

logger = getLogger()


def _request_to_sqd_string(r: object) -> dict[str, object]:
    """Convert request dataclass to an SQD-compatible payload."""

    def normalize_key(key: str) -> str:
        return "from" if key == "from_" else key

    return {
        normalize_key(key): value
        for key, value in asdict(r).items()  # type: ignore[arg-type]
        if value is not None
    }


def _normalize_dataset(dataset: Dataset | str) -> Dataset | str:
    if isinstance(dataset, Dataset):
        return dataset
    try:
        return Dataset(dataset)
    except ValueError:
        logger.warning(
            "Dataset '%s' is not recognized and may lead to unexpected behavior.",
            dataset,
        )
        return dataset


def validate_evm_address(address: str) -> str:
    """
    Validate and normalize Ethereum address format.

    Args:
        address: Ethereum address string

    Returns:
        Normalized address (lowercase, 0x prefix)

    Raises:
        ValueError: If address format is invalid
    """
    if not address:
        raise ValueError("Address cannot be empty")

    address = address.lower()

    if not address.startswith("0x"):
        address = "0x" + address

    if len(address) != 42:
        raise ValueError(
            f"Invalid address length: {len(address)}. Expected 42 characters (including 0x prefix)"
        )

    # Basic hex validation
    try:
        int(address, 16)
    except ValueError:
        raise ValueError(f"Invalid address format: {address}")

    return address


# Optimized connector settings for performance
def create_connector(limit_per_host: int = 50) -> aiohttp.TCPConnector:
    """Create an optimized TCP connector with connection pooling.

    Args:
        limit_per_host: Max concurrent connections per host (default: 50)
    """
    return aiohttp.TCPConnector(
        limit=200,  # Total connection pool size
        limit_per_host=limit_per_host,  # Per-host limit
        ttl_dns_cache=300,  # DNS cache TTL
        enable_cleanup_closed=True,
        force_close=False,  # Keep connections alive
    )


def create_session(limit_per_host: int = 50) -> aiohttp.ClientSession:
    """Create an optimized aiohttp session.

    Args:
        limit_per_host: Max concurrent connections per host (default: 50)
    """
    return aiohttp.ClientSession(
        connector=create_connector(limit_per_host),
        json_serialize=ujson.dumps,
    )

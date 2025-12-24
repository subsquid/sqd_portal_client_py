from dataclasses import asdict


def _request_to_sqd_string(r) -> dict:
    """Convert request dataclass to an SQD-compatible payload."""

    def normalize_key(key: str) -> str:
        return "from" if key == "from_" else key

    return {
        normalize_key(key): value
        for key, value in asdict(r).items()
        if value is not None
    }

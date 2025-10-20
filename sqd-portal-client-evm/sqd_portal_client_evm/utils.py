from dataclasses import asdict

try:
    import ujson as json_lib
except ImportError:
    import json as json_lib


def _request_to_sqd_string(r) -> str:
    """Convert request object to SQD API string format"""

    def correctFromUnderscore(k: str) -> str:
        return "from" if k == "from_" else k

    return json_lib.dumps(
        {correctFromUnderscore(k): v for k, v in asdict(r).items() if v is not None},
        separators=(",", ":"),
    )

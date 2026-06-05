"""EVM decoding utilities for common events and data types."""

from typing import TypedDict


class DecodedTransfer(TypedDict):
    """Decoded ERC-20/ERC-721 Transfer event."""

    contract: str
    from_address: str
    to_address: str
    value: int
    transaction_hash: str | None
    log_index: int | None
    block_number: int | None


def decode_transfer(log: dict[str, object]) -> DecodedTransfer:
    """
    Decode an ERC-20/ERC-721 Transfer event log.

    Args:
        log: Raw log data from SQD API

    Returns:
        DecodedTransfer with parsed addresses and value

    Example:
        async for block in query:
            for log in block.get("logs", []):
                transfer = decode_transfer(log)
                print(f"{transfer['from_address']} -> {transfer['to_address']}: {transfer['value']}")
    """
    topics = log.get("topics", [])

    # Extract addresses from topics (remove 0x prefix, take last 40 chars)
    from_address = "0x" + topics[1][-40:] if len(topics) > 1 else "0x0"
    to_address = "0x" + topics[2][-40:] if len(topics) > 2 else "0x0"

    # Decode value from data field (uint256)
    data = log.get("data", "0x0")
    if data and data != "0x":
        value = int(data, 16)
    else:
        # For ERC-721, value might be tokenId in topic3
        value = int(topics[3], 16) if len(topics) > 3 else 0

    return DecodedTransfer(
        contract=log.get("address", ""),
        from_address=from_address,
        to_address=to_address,
        value=value,
        transaction_hash=log.get("transactionHash"),
        log_index=log.get("logIndex"),
        block_number=log.get("block", {}).get("number"),
    )


def format_token_amount(value: int, decimals: int) -> str:
    """
    Format a token amount with decimals for display.

    Args:
        value: Raw token amount (in smallest units)
        decimals: Token decimals (default: 18 for most ERC-20 tokens)

    Returns:
        Formatted string with decimal point

    Example:
        >>> format_token_amount(1000000000000000000, 18)
        '1.0'
        >>> format_token_amount(1500000, 6)  # USDC
        '1.5'
    """
    if decimals == 0:
        return str(value)

    divisor = 10**decimals
    whole = value // divisor
    fraction = value % divisor

    if fraction == 0:
        return str(whole)

    # Format fraction with leading zeros
    fraction_str = str(fraction).zfill(decimals).rstrip("0")
    return f"{whole}.{fraction_str}"


__all__ = ["decode_transfer", "format_token_amount", "DecodedTransfer"]

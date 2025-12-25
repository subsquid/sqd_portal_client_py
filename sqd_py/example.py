import asyncio
from logging import getLogger

from sqd import SQD, Dataset, EvmFields
from sqd.query.evm import decode_transfer

logger = getLogger(__name__)

transfers = []


async def main():
    sqd = SQD(dataset=Dataset.ETHEREUM, portal_url="https://portal.sqd.dev")
    query = sqd.get_transfers(
        from_block=12649280,
        to_block=24089500,
        from_address="0x6d1AeFc047d55C5d08c288a663711F7B7EFD82E0",
        to_address="0x6d1AeFc047d55C5d08c288a663711F7B7EFD82E0",
        include_fields=list(EvmFields.LogField),
        include_all_blocks=False,
        include_transaction=False,
    )

    # Use with_progress() for a progress bar!
    async for data in query.with_progress():
        if data.get("logs", {}):
            for t in data["logs"]:
                transfers.append(decode_transfer(t))


if __name__ == "__main__":
    asyncio.run(main())
    print(len(transfers))

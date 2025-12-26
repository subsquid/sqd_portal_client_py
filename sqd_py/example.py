import asyncio
from logging import getLogger

from sqd import SQD, Dataset, EvmFields
from sqd.query.evm import decode_transfer

logger = getLogger(__name__)

blocks = []


async def main():
    sqd = SQD(dataset=Dataset.ETHEREUM, portal_url="https://portal.sqd.dev")
    from_block = 12649280
    to_block = from_block + 100000
    query = sqd.get_transfers(
        from_block=from_block,
        contract_address="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        include_fields=list(EvmFields.LogField),
        include_all_blocks=True,
        include_transaction=False,
    )

    print(f"Fetching blocks {from_block} to {to_block}...")

    async for data in query.with_progress(shards=5):
        blocks.append(data["header"]["number"])
    with open("blocks.txt", "w") as f:
        for block in blocks:
            f.write(f"{block}\n")


def x():
    asyncio.run(main())


if __name__ == "__main__":
    # execution_time = timeit.timeit(lambda: x(), number=1)
    # print(execution_time)
    # print(execution_time / 5)
    x()

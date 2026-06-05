import asyncio
import timeit

from logging import getLogger

import clickhouse_connect
from sqd import SQD, Dataset, EvmFields

logger = getLogger(__name__)

blocks = []

client = clickhouse_connect.get_client(
    host="localhost", port=8123, username="default", password="default"
)


async def main():
    sqd = SQD(dataset=Dataset.ETHEREUM, portal_url="https://portal.sqd.dev")
    query = sqd.get_transfers(
        from_block=from_block,
        to_block=to_block,
        contract_address="0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        include_fields=list(EvmFields.LogField),
        include_all_blocks=True,
        include_transaction=False,
    )

    client.command("DROP TABLE IF EXISTS transfers")
    client.command(
        """
        CREATE TABLE IF NOT EXISTS transfers
        (
            block_number      UInt64,
            timestamp         UInt64,
            log_address       String,
            log_topics        Array(String),
            log_data          String,
            transaction_hash  String,
            transaction_index UInt32,
            log_index         UInt32
        )
            ENGINE = MergeTree()
                ORDER BY block_number
        """
    )

    batch = []
    t = None
    # print(f"Fetching blocks {from_block} to {to_block}...")

    async for data in query.with_progress(shards=1):
        for log in data.get("logs", []):
            batch.append(
                [
                    data["header"]["number"],
                    data["header"]["timestamp"],
                    log["address"],
                    log["topics"],
                    log["data"],
                    log["transactionHash"],
                    log["transactionIndex"],
                    log["logIndex"],
                ]
            )

        if len(batch) >= 20000:
            if t:
                await t
            t = asyncio.create_task(insert(batch))
            batch.clear()
            await t

    if batch:
        client.insert(
            "transfers",
            batch,
            column_names=[
                "block_number",
                "timestamp",
                "log_address",
                "log_topics",
                "log_data",
                "transaction_hash",
                "transaction_index",
                "log_index",
            ],
        )


async def insert(data):
    client.insert(
        "transfers",
        data,
        column_names=[
            "block_number",
            "timestamp",
            "log_address",
            "log_topics",
            "log_data",
            "transaction_hash",
            "transaction_index",
            "log_index",
        ],
    )


def x():
    asyncio.run(main())


if __name__ == "__main__":
    from_block = 23096000
    to_block = from_block + 100_000
    execution_time = timeit.timeit(lambda: x(), number=1)
    print(execution_time)
    print("Fetched blocks:", len(blocks))
    # x()

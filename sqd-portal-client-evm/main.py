from sqd_portal_client_evm import SQD, TransactionField, LogField, Dataset
from loguru import logger

async def main():
    sqd = SQD(dataset=Dataset.ETHEREUM, portal_url="https://portal.sqd.dev")
    query = sqd.get_transactions(
        address="0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
        from_block=17_000_000,
        to_block=17_000_010,
        include_fields=[TransactionField.BLOCK_NUMBER, TransactionField.FROM_ADDRESS],
    )
    query = query.get_logs(
        address="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        from_block=17_000_000,
        to_block=17_000_010,
        topic0="0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",
        include_fields=[LogField.LOG_INDEX, LogField.TRANSACTION_HASH],
    )
    async for transaction in query:
        logger.info(transaction)
        
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

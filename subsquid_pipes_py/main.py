import asyncio

from subsquid_pipes.evm import evm_portal_source, EvmQueryBuilder
from subsquid_pipes.core import create_default_logger
from subsquid_pipes.targets import MemoryTarget

logger = create_default_logger('info')

async def main():
    target = MemoryTarget()
    source = evm_portal_source(
        portal="https://portal.sqd.dev/datasets/ethereum-mainnet",
        query=EvmQueryBuilder().add_log(range={"from": 23_858_549, "to": 23_868_549}, request={
            'address': ['0xdac17f958d2ee523a2206206994597c13d831ec7'],
            'topic0': ['0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef']})
        .add_fields({'log': {'address': True, 'data': True}}),
        logger=logger,
    ).pipe(
        lambda events, ctx:
        [b['logs'] for b in events['blocks'] if b.get('logs')]
    )

    await source.pipe_to(target)

    count = 0
    async for batch in source:
        blocks = batch.data
        count += len(blocks)
        for block in blocks:
            ...
            # print(block)
    print("total blocks:", count)
    
    print(target.batches)  # Print first 10 batches stored in memory target
    
    
if __name__ == "__main__":
    asyncio.run(main())
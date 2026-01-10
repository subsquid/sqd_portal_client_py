"""Benchmark prefetch settings for historical ranges."""

import asyncio
import time

from sqd import SQD, Dataset


async def benchmark_shards(shards: int, from_block: int, to_block: int) -> float:
    """Run a benchmark with the given prefetch setting."""
    sqd = SQD(dataset=Dataset.ETHEREUM, portal_url="https://portal.sqd.dev")
    query = sqd.get_blocks(from_block=from_block, to_block=to_block)
    start = time.perf_counter()
    count = 0
    async for _ in query.with_progress(shards=shards):
        count += 1
    elapsed = time.perf_counter() - start

    return elapsed, count


async def main():
    from_block = 12649280
    to_block = from_block + 50000  # 50K blocks for reasonable test time

    print(f"Benchmarking block range: {from_block} to {to_block}")
    print(f"Total blocks: {to_block - from_block + 1}")
    print("-" * 60)

    results = []
    for shards in [1, 2]:
        print(f"\nTesting with {shards} prefetch setting...")
        elapsed, count = await benchmark_shards(shards, from_block, to_block)
        blocks_per_sec = count / elapsed
        results.append((shards, elapsed, blocks_per_sec))
        print(
            f"  {shards} prefetch setting: {elapsed:.2f}s "
            f"({blocks_per_sec:.0f} blocks/sec)"
        )

    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    print(f"{'Prefetch':<10} {'Time (s)':<12} {'Blocks/sec':<15} {'Speedup':<10}")
    print("-" * 60)

    baseline = results[0][1]  # 1-shard time
    for shards, elapsed, bps in results:
        speedup = baseline / elapsed
        print(f"{shards:<10} {elapsed:<12.2f} {bps:<15.0f} {speedup:<10.2f}x")


if __name__ == "__main__":
    asyncio.run(main())

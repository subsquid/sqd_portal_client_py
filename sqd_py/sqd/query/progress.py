"""Progress handlers for QueryCursor.

This module provides a protocol for progress reporting and a default
tqdm-based implementation. Users can implement their own handlers
by following the ProgressHandler protocol.
"""

import sys
from abc import ABC, abstractmethod
from typing import Any

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None


class ProgressHandler(ABC):
    """Abstract base class for progress handlers.

    Implement this interface to create custom progress reporting
    for QueryCursor operations.
    """

    @abstractmethod
    def on_start(
        self,
        dataset: str,
        from_block: int,
        to_block: int | None,
    ) -> None:
        """Called when the cursor starts fetching.

        Args:
            dataset: The dataset being queried (e.g., 'ethereum-mainnet')
            from_block: Starting block number
            to_block: Ending block number (None for infinite/live mode)
        """
        pass

    @abstractmethod
    def on_block(self, block_number: int) -> None:
        """Called when a block is received.

        Args:
            block_number: The block number that was just processed
        """
        pass

    @abstractmethod
    def on_switch_to_live(self, last_block: int | None) -> None:
        """Called when switching from catchup to live mode.

        Args:
            last_block: The last block processed during catchup
        """
        pass

    @abstractmethod
    def on_waiting(self, last_block: int) -> None:
        """Called when waiting for new blocks in live mode.

        Args:
            last_block: The last block that was processed
        """
        pass

    @abstractmethod
    def on_close(self) -> None:
        """Called when the cursor is closed."""
        pass


class TqdmProgressHandler(ProgressHandler):
    """Default progress handler using tqdm.

    Shows a progress bar during catchup and a live counter
    when in infinite/live mode.
    """

    def __init__(self) -> None:
        self._pbar: Any = None
        self._dataset: str = ""
        self._from_block: int = 0
        self._to_block: int | None = None
        self._is_live_mode: bool = False

    def on_start(
        self,
        dataset: str,
        from_block: int,
        to_block: int | None,
    ) -> None:
        if tqdm is None:
            return

        self._dataset = dataset
        self._from_block = from_block
        self._to_block = to_block

        if to_block is not None:
            # Finite mode: show progress towards to_block
            total_blocks = to_block - from_block + 1
            self._pbar = tqdm(
                total=total_blocks,
                desc=f"Syncing {dataset}",
                unit="blocks",
                unit_scale=True,
                initial=0,
            )
        else:
            # Infinite mode: show block count without total
            self._pbar = tqdm(
                desc=f"Syncing {dataset}",
                unit="blocks",
                unit_scale=True,
            )

    def on_block(self, block_number: int) -> None:
        if self._pbar is None:
            return

        if self._is_live_mode:
            # Live mode: increment by 1 and show block number
            self._pbar.update(1)
            self._pbar.set_description_str(
                f"{self._dataset} | block {block_number} |", refresh=True
            )
        elif self._pbar.total is not None:
            # Finite mode: update relative to from_block
            self._pbar.update(1)
            self._pbar.set_postfix_str(f"block={block_number}", refresh=True)
        else:
            # Infinite mode (not yet live): just increment
            self._pbar.update(1)

    def on_switch_to_live(self, last_block: int | None) -> None:
        if self._pbar is not None:
            self._pbar.close()

        self._is_live_mode = True

        if tqdm is not None:
            self._pbar = tqdm(
                total=None,
                unit="blocks",
                unit_scale=True,
                bar_format="Live {desc} {n_fmt} new [{elapsed}, {rate_fmt}]",
                dynamic_ncols=True,
                file=sys.stderr,
            )
            self._pbar.set_description_str(f"{self._dataset}")

    def on_waiting(self, last_block: int) -> None:
        if self._pbar is not None:
            self._pbar.set_description_str(
                f"{self._dataset} | block {last_block} (waiting...) |"
            )
            self._pbar.refresh()

    def on_close(self) -> None:
        if self._pbar is not None:
            self._pbar.close()
            self._pbar = None


class NoopProgressHandler(ProgressHandler):
    """A no-op progress handler that does nothing.

    Useful when progress reporting is not desired.
    """

    def on_start(
        self,
        dataset: str,
        from_block: int,
        to_block: int | None,
    ) -> None:
        pass

    def on_block(self, block_number: int) -> None:
        pass

    def on_switch_to_live(self, last_block: int | None) -> None:
        pass

    def on_waiting(self, last_block: int) -> None:
        pass

    def on_close(self) -> None:
        pass

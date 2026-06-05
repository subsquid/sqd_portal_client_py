"""Progress handlers for QueryCursor.

This module provides a protocol for progress reporting and a default
tqdm-based implementation. Users can implement their own handlers
by following the ProgressHandler protocol.
"""

import os
import sys
import time
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
        self._enabled: bool = False
        self._plain_enabled: bool = False
        self._last_plain_log_time: float = 0.0
        self._last_plain_wait_time: float = 0.0
        self._last_plain_logged_block: int | None = None
        self._plain_every_seconds: float = 5.0
        self._plain_every_blocks: int = 1000
        self._start_time: float | None = None
        self._last_rate_time: float | None = None
        self._last_rate_block: int | None = None

    def _tqdm_supported(self) -> bool:
        if tqdm is None:
            return False
        if not hasattr(sys.stderr, "isatty") or not sys.stderr.isatty():
            return False
        term = os.environ.get("TERM", "").lower()
        if term == "dumb":
            return False
        return True

    def _format_duration(self, seconds: float) -> str:
        if seconds < 0:
            seconds = 0
        if seconds < 1:
            return f"{seconds:.3f}s"
        if seconds < 60:
            return f"{seconds:.1f}s"
        total_seconds = int(seconds + 0.5)
        minutes, sec = divmod(total_seconds, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)
        if days > 0:
            return f"{days:d}d {hours:02d}:{minutes:02d}:{sec:02d}"
        if hours > 0:
            return f"{hours:d}:{minutes:02d}:{sec:02d}"
        return f"{minutes:d}:{sec:02d}"

    def _plain_log(self, message: str) -> None:
        self.logger.info(message)

    def _rate_from_start(self, now: float, block_number: int) -> float | None:
        if self._start_time is None:
            return None
        elapsed = now - self._start_time
        if elapsed <= 0:
            return None
        current = block_number - self._from_block + 1
        if current <= 0:
            return None
        return current / elapsed

    def _rate_from_delta(self, now: float, block_number: int) -> float | None:
        if self._last_rate_time is None or self._last_rate_block is None:
            return None
        delta_time = now - self._last_rate_time
        delta_blocks = block_number - self._last_rate_block
        if delta_time <= 0 or delta_blocks <= 0:
            return None
        return delta_blocks / delta_time

    def on_start(
        self,
        dataset: str,
        from_block: int,
        to_block: int | None,
    ) -> None:
        self._enabled = self._tqdm_supported()
        self._plain_enabled = not self._enabled
        self._dataset = dataset
        self._from_block = from_block
        self._to_block = to_block
        self._start_time = time.monotonic()
        self._last_rate_time = self._start_time
        self._last_rate_block = None

        if not self._enabled:
            import logging

            self.logger = logging.getLogger(":")
            if to_block is None:
                self._plain_log(f"Syncing {dataset} from block {from_block} (live)")
            else:
                self._plain_log(
                    f"Syncing {dataset} from block {from_block} to {to_block}"
                )
            return

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
            if not self._plain_enabled:
                return
            now = time.monotonic()
            should_log = False
            if self._last_plain_logged_block is None:
                should_log = True
            elif (
                block_number - self._last_plain_logged_block
            ) >= self._plain_every_blocks:
                should_log = True
            elif (now - self._last_plain_log_time) >= self._plain_every_seconds:
                should_log = True

            if should_log:
                rate = self._rate_from_delta(now, block_number)
                if rate is None:
                    rate = self._rate_from_start(now, block_number)

                self._last_plain_logged_block = block_number
                self._last_plain_log_time = now
                if self._to_block is not None:
                    total = self._to_block - self._from_block + 1
                    current = block_number - self._from_block + 1
                    remaining = max(total - current, 0)
                    eta = (remaining / rate) if rate is not None else None
                    eta_str = self._format_duration(eta) if eta is not None else "?"
                    rate_str = f"{rate:.2f}/s" if rate is not None else "?/s"
                    self._plain_log(
                        f"{self._dataset} {current}/{total} "
                        f"block={block_number} latest={self._to_block} "
                        f"rate={rate_str} eta={eta_str}"
                    )
                else:
                    elapsed = now - self._start_time if self._start_time else 0.0
                    rate_str = f"{rate:.2f}/s" if rate is not None else "?/s"
                    status = "live" if self._is_live_mode else "syncing"
                    self._plain_log(
                        f"{self._dataset} {status} block={block_number} "
                        f"rate={rate_str} elapsed={self._format_duration(elapsed)}"
                    )
                self._last_rate_time = now
                self._last_rate_block = block_number
            return

        if self._is_live_mode:
            # Live mode: increment by 1 and show block number
            self._pbar.update(1)
            self._pbar.set_description_str(
                f"{self._dataset} | block {block_number} |", refresh=True
            )
        elif self._pbar.total is not None:
            # Finite mode: update based on position in current range (absolute progress)
            # We track "blocks scanned" rather than "items received"
            current_progress = block_number - self._from_block + 1
            if current_progress > self._pbar.n:
                self._pbar.update(current_progress - self._pbar.n)
            self._pbar.set_postfix_str(f"block={block_number}", refresh=True)
        else:
            # Infinite mode (not yet live): just increment
            self._pbar.update(1)

    def on_switch_to_live(self, last_block: int | None) -> None:
        if self._pbar is not None:
            self._pbar.close()

        self._is_live_mode = True

        if self._enabled:
            self._pbar = tqdm(
                total=None,
                unit="blocks",
                unit_scale=True,
                bar_format="Live {desc} {n_fmt} new [{elapsed}, {rate_fmt}]",
                dynamic_ncols=True,
                file=sys.stderr,
            )
            self._pbar.set_description_str(f"{self._dataset}")
        elif self._plain_enabled:
            if last_block is None:
                self._plain_log(f"{self._dataset} switching to live mode")
            else:
                self._plain_log(
                    f"{self._dataset} switching to live mode at block {last_block}"
                )

    def on_waiting(self, last_block: int) -> None:
        if self._pbar is not None:
            self._pbar.set_description_str(
                f"{self._dataset} | block {last_block} (waiting...) |"
            )
            self._pbar.refresh()
        elif self._plain_enabled:
            now = time.monotonic()
            if (now - self._last_plain_wait_time) >= self._plain_every_seconds:
                self._last_plain_wait_time = now
                elapsed = now - self._start_time if self._start_time else 0.0
                rate = self._rate_from_delta(now, last_block)
                if rate is None:
                    rate = self._rate_from_start(now, last_block)
                rate_str = f"{rate:.2f}/s" if rate is not None else "?/s"
                self._plain_log(
                    f"{self._dataset} waiting latest={last_block} "
                    f"rate={rate_str} elapsed={self._format_duration(elapsed)}"
                )

    def on_close(self) -> None:
        if self._pbar is not None:
            self._pbar.close()
            self._pbar = None
        elif self._plain_enabled:
            self._plain_log(f"{self._dataset} progress stopped")


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

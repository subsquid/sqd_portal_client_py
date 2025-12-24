from __future__ import annotations

import logging
import os
from functools import lru_cache
from typing import Literal

import structlog

LogLevel = Literal['critical', 'error', 'warning', 'info', 'debug', 'trace', 'silent'] | None
Logger = structlog.types.BindableLogger


def _translate_level(level: LogLevel) -> int:
    if level in (None, 'silent'):
        return logging.CRITICAL + 1
    mapping: dict[str, int] = {
        'critical': logging.CRITICAL,
        'error': logging.ERROR,
        'warning': logging.WARNING,
        'info': logging.INFO,
        'debug': logging.DEBUG,
        'trace': logging.NOTSET,
    }
    return mapping.get(level or 'info', logging.INFO)


@lru_cache(maxsize=1)
def _configure_structlog() -> None:
    logging.basicConfig(
        format='%(message)s',
        level=_translate_level(os.getenv('LOG_LEVEL', 'info').lower()),
    )
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt='iso'),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer(colors=os.getenv('LOG_PRETTY', 'true').lower() != 'false'),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.getLogger().level),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def create_default_logger(level: LogLevel = None) -> Logger:
    """Return a configured structlog logger compatible with the TS runtime."""

    _configure_structlog()
    if level not in (None, 'silent'):
        logging.getLogger().setLevel(_translate_level(level))
    return structlog.get_logger('subsquid.pipes')


__all__ = ['Logger', 'LogLevel', 'create_default_logger']

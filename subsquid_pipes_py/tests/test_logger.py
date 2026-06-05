from __future__ import annotations

from subsquid_pipes.core import create_default_logger


def test_create_default_logger_produces_bindable_logger():
    logger = create_default_logger('debug')
    # structlog loggers expose bind/unbind helpers
    bound = logger.bind(component='test')
    bound.info('message', foo='bar')
    assert hasattr(bound, 'unbind')

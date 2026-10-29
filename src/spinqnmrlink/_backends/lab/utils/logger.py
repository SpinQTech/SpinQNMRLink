# Copyright 2025 SpinQ Technology Co., Ltd.
# SPDX-License-Identifier: GPL-3.0-only

"""SpinQLabLink logging API backed by the shared logging implementation."""

from spinqnmrlink._core.logging import (
    SensitiveDataFilter,
    SharedLoggerManager,
    summarize_payload,
    setup_package_logger,
)


class LoggerManager(SharedLoggerManager):
    """SpinQLabLink-owned logger manager with independent logger caching."""

    DEFAULT_NAME = "spinqnmrlink._backends.lab"
    _loggers = {}


def setup_default_logger(log_level="info", log_dir=None):
    return setup_package_logger(LoggerManager, "spinqnmrlink._backends.lab", log_level, log_dir)


default_logger = setup_default_logger()


debug = default_logger.debug
info = default_logger.info
warning = default_logger.warning
error = default_logger.error
critical = default_logger.critical

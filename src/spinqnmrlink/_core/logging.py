# Copyright 2026 SpinQ Technology Co., Ltd.
# SPDX-License-Identifier: GPL-3.0-only
"""Shared logging implementation used by both public packages."""

from __future__ import annotations

from collections.abc import Mapping
import logging
from logging.handlers import RotatingFileHandler
import os
import re
import threading
import datetime


class SensitiveDataFilter(logging.Filter):
    """Remove credentials and session identifiers from log records."""

    _lock = threading.RLock()
    _registered_secrets: set[str] = set()
    _sensitive_assignment = re.compile(
        r"(?i)(?P<key>['\"]?(?:account|password|passwd|session_id|sessionId)['\"]?\s*[:=]\s*)"
        r"(?:(?P<quote>['\"])(?P<quoted_value>.*?)(?P=quote)"
        r"|(?P<bare_value>[^\s,}\]]+))"
    )

    @classmethod
    def register_secret(cls, value) -> None:
        if value is None:
            return
        text = str(value)
        if len(text) < 4:
            return
        with cls._lock:
            cls._registered_secrets.add(text)

    @classmethod
    def sanitize(cls, value) -> str:
        text = cls._sensitive_assignment.sub(
            lambda match: f"{match.group('key')}<redacted>",
            str(value),
        )
        with cls._lock:
            for secret in sorted(cls._registered_secrets, key=len, reverse=True):
                text = text.replace(secret, "<redacted>")
        return text

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = self.sanitize(record.getMessage())
        record.args = ()
        return True


def summarize_payload(data) -> str:
    """Describe payload structure without exposing its values."""

    if isinstance(data, Mapping):
        keys = sorted(str(key) for key in data.keys())
        return f"mapping(keys={keys}, count={len(keys)})"
    if isinstance(data, (list, tuple, set)):
        return f"{type(data).__name__}(count={len(data)})"
    if data is None:
        return "none"
    return type(data).__name__


class SharedLoggerManager:
    """Common logger construction, caching, rotation and redaction."""

    DEFAULT_NAME = "spinq"
    DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LEVEL_MAP = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL,
    }
    _loggers: dict[str, logging.Logger] = {}

    @classmethod
    def get_logger(
        cls,
        name=None,
        level="info",
        log_file=None,
        max_size=10 * 1024 * 1024,
        backup_count=5,
        log_format="%(asctime)s [%(levelname)s] %(message)s",
    ):
        logger_name = name or cls.DEFAULT_NAME
        if logger_name in cls._loggers:
            return cls._loggers[logger_name]

        logger = logging.getLogger(logger_name)
        logger.setLevel(cls.LEVEL_MAP.get(level.lower(), logging.INFO))
        if not any(isinstance(item, SensitiveDataFilter) for item in logger.filters):
            logger.addFilter(SensitiveDataFilter())

        if not logger.handlers:
            formatter = logging.Formatter(log_format or cls.DEFAULT_FORMAT)
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

            if log_file:
                log_dir = os.path.dirname(log_file)
                if log_dir:
                    os.makedirs(log_dir, exist_ok=True)
                file_handler = RotatingFileHandler(
                    filename=log_file,
                    maxBytes=max_size,
                    backupCount=backup_count,
                    encoding="utf-8",
                )
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)

        cls._loggers[logger_name] = logger
        return logger

    @classmethod
    def register_secret(cls, value) -> None:
        SensitiveDataFilter.register_secret(value)


def setup_package_logger(manager_class, file_prefix, log_level="info", log_dir=None):
    """Create one package default logger with the shared dated-file policy."""

    log_file = None
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d")
        log_file = os.path.join(log_dir, "{}_{}.log".format(file_prefix, timestamp))
    return manager_class.get_logger(level=log_level, log_file=log_file)

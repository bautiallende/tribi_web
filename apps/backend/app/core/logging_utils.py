"""Logging helpers for structured output and request correlation."""

from __future__ import annotations

import json
import logging
import logging.config
from contextvars import ContextVar
from datetime import datetime
from typing import Any

_REQUEST_ID_CTX: ContextVar[str | None] = ContextVar("request_id", default=None)

_RESERVED_LOG_RECORD_ATTRS = {
    "name",
    "msg",
    "args",
    "levelname",
    "levelno",
    "pathname",
    "filename",
    "module",
    "exc_info",
    "exc_text",
    "stack_info",
    "lineno",
    "funcName",
    "created",
    "msecs",
    "relativeCreated",
    "thread",
    "threadName",
    "processName",
    "process",
    "message",
    "asctime",
}


class RequestContextFilter(logging.Filter):
    """Inject contextvars (request_id, etc.) into each log record."""

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: D401 (simple hook)
        record.request_id = _REQUEST_ID_CTX.get()
        return True


class JsonFormatter(logging.Formatter):
    """Render log records as JSON for ingestion by log platforms."""

    def format(self, record: logging.LogRecord) -> str:  # noqa: D401 (override)
        log_record: dict[str, Any] = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat(
                timespec="milliseconds"
            )
            + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        request_id = getattr(record, "request_id", None)
        if request_id:
            log_record["request_id"] = request_id

        if record.exc_info:
            log_record["exc_info"] = self.formatException(record.exc_info)

        for key, value in record.__dict__.items():
            if key in _RESERVED_LOG_RECORD_ATTRS:
                continue
            if key in log_record:
                continue
            log_record[key] = value

        return json.dumps(log_record, default=str)


def setup_logging(level: str = "INFO", log_format: str = "console") -> None:
    """Configure root logging with optional JSON output."""

    level_name = (level or "INFO").upper()
    format_key = "json" if log_format.lower() == "json" else "console"

    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "request_context": {"()": RequestContextFilter},
        },
        "formatters": {
            "console": {
                "format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s | request_id=%(request_id)s",
                "datefmt": "%Y-%m-%dT%H:%M:%S",
            },
            "json": {
                "()": JsonFormatter,
            },
        },
        "handlers": {
            "default": {
                "class": "logging.StreamHandler",
                "filters": ["request_context"],
                "formatter": format_key,
            }
        },
        "root": {
            "level": level_name,
            "handlers": ["default"],
        },
    }

    logging.config.dictConfig(logging_config)


def bind_request_context(request_id: str | None) -> None:
    """Store the active request id in the context for filters to consume."""

    _REQUEST_ID_CTX.set(request_id)


def clear_request_context() -> None:
    """Clear the request context to avoid leaking ids between requests."""

    _REQUEST_ID_CTX.set(None)


def get_request_id() -> str | None:
    """Return the current request id, if any."""

    return _REQUEST_ID_CTX.get()

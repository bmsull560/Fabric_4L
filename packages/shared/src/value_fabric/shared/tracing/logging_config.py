"""Standardized structured logging configuration for all Fabric_4L services.

Usage:
    from value_fabric.shared.tracing.logging_config import configure_structured_logging
    configure_structured_logging(service_name="layer2-extraction")
    logger = structlog.get_logger()
    logger.info("event_description", key="value")
"""

import logging
import sys

import structlog


def configure_structured_logging(
    service_name: str,
    log_level: str = "INFO",
    json_output: bool = True,
) -> None:
    """Configure structlog with JSON output and correlation ID support.

    Args:
        service_name: Service identifier (e.g., "layer2-extraction")
        log_level: Minimum log level (DEBUG, INFO, WARNING, ERROR)
        json_output: If True, output JSON; if False, output console-friendly format
    """
    # Map string level to logging constant
    level = getattr(logging, log_level.upper(), logging.INFO)

    # Configure stdlib logging to route through structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=level,
    )

    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_logger_name,
        structlog.stdlib.ExtraAdder(),
    ]

    if json_output:
        formatter = structlog.processors.JSONRenderer()
    else:
        formatter = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=shared_processors
        + [
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            formatter,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Suppress noisy third-party logs
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

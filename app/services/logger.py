import logging
import os
from typing import Optional


def get_logger(name: Optional[str] = None) -> logging.Logger:
    log_level = os.getenv("APP_LOG_LEVEL", "INFO").upper()
    logger_name = name or "cs_agent"
    logger = logging.getLogger(logger_name)

    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=getattr(logging, log_level, logging.INFO),
            format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        )

    logger.setLevel(getattr(logging, log_level, logging.INFO))
    return logger
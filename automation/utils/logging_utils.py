import logging
import os
from datetime import datetime

import colorlog


class LoggingUtils:
    @staticmethod
    def setup_logger(name, log_level=logging.INFO, log_to_file=False):
        # Create logs directory if it doesn't exist
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)

        # Create a logger
        logger = colorlog.getLogger(name)
        logger.setLevel(log_level)

        # Remove any existing handlers to avoid duplication
        if logger.handlers:
            logger.handlers.clear()

        # Create formatter
        console_formatter = colorlog.ColoredFormatter(
            "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s%(reset)s",
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "red,bg_white",
            },
            secondary_log_colors={},
            style="%",
        )

        # Create console handler
        console_handler = colorlog.StreamHandler()
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        if log_to_file:
            # Create file handler
            current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_handler = logging.FileHandler(f"{log_dir}/{name}_{current_time}.log")
            file_formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)

        # Prevent log messages from being passed to the root logger
        logger.propagate = False
        return logger


# Create and export the global logger instances
logger = LoggingUtils.setup_logger("AUTOMATION")
fast_api_logger = LoggingUtils.setup_logger("FASTAPI")

# Export the loggers
__all__ = ["logger", "fast_api_logger"]

"""
Утилиты для логирования. Путь файла берётся из config.Paths.LOGS_DIR
(можно переопределить через env PSHC_LOGS_DIR).
"""
import logging
import sys
from pathlib import Path

from config import Paths


def setup_logger(name: str, level=logging.INFO) -> logging.Logger:
    """Настроить логгер для модуля. Console + rotating-by-run app.log."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    try:
        log_dir = Path(Paths.LOGS_DIR)
        log_dir.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(
            log_dir / 'app.log',
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        logger.warning(f"Could not create file handler: {e}")

    return logger

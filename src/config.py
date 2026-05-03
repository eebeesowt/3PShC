"""
Централизованная конфигурация приложения.
Значения по умолчанию переопределяются через переменные окружения.
"""
import os


class OSCConfig:
    """Параметры OSC-сервера."""
    HOST: str = os.environ.get("PSHC_OSC_HOST", "127.0.0.1")
    PORT: int = int(os.environ.get("PSHC_OSC_PORT", "7001"))


class ProjectorConfig:
    """Параметры подключения к проекторам."""
    DEFAULT_PORT: int = int(os.environ.get("PSHC_PROJECTOR_PORT", "1024"))
    TIMEOUT_SECONDS: float = float(os.environ.get("PSHC_PROJECTOR_TIMEOUT", "2"))


class Paths:
    """Пути файлов данных."""
    SETTINGS_DIR: str = os.environ.get(
        "PSHC_SETTINGS_DIR",
        os.path.join(os.path.dirname(__file__), "data", "settings"),
    )
    LOGS_DIR: str = os.environ.get(
        "PSHC_LOGS_DIR",
        os.path.join(os.path.dirname(__file__), "logs"),
    )

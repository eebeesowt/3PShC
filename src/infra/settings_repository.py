"""
Репозиторий per-projector настроек: сохранение/загрузка JSON-файла на проектор.
Файлы лежат в Paths.SETTINGS_DIR (env PSHC_SETTINGS_DIR), по одному на IP:
projector_<ip_with_underscores>.json. Используются для быстрого восстановления
позиции линзы и настроек дисплея.
"""
import json
import os
from typing import Any, Dict, Optional

from config import Paths
from utils.logger import setup_logger

logger = setup_logger(__name__)


def get_settings_file_path(projector_ip: str) -> str:
    """Путь к JSON-файлу настроек по IP. Создаёт директорию при необходимости."""
    os.makedirs(Paths.SETTINGS_DIR, exist_ok=True)
    safe_ip = projector_ip.replace('.', '_')
    return os.path.join(Paths.SETTINGS_DIR, f"projector_{safe_ip}.json")


def create_projector_settings_dict(
    h_position: str,
    v_position: str,
    aspect_ratio: str,
    installation_mode: str,
) -> Dict[str, Dict[str, str]]:
    """Собрать словарь настроек в формате, который ожидает scene/settings storage."""
    return {
        'lens_settings': {
            'h_position': h_position,
            'v_position': v_position,
        },
        'display_settings': {
            'aspect_ratio': aspect_ratio,
            'installation_mode': installation_mode,
        },
    }


def save_projector_settings(
    projector_ip: str,
    h_position: str,
    v_position: str,
    aspect_ratio: str,
    installation_mode: str,
) -> bool:
    """Сохранить настройки конкретного проектора. True при успехе."""
    try:
        file_path = get_settings_file_path(projector_ip)
        payload = {
            'projector_ip': projector_ip,
            **create_projector_settings_dict(
                h_position, v_position, aspect_ratio, installation_mode
            ),
        }
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved settings for projector {projector_ip} to {file_path}")
        return True
    except Exception as exc:
        logger.error(f"Error saving settings for projector {projector_ip}: {exc}")
        return False


def load_projector_settings(projector_ip: str) -> Optional[Dict[str, Any]]:
    """Загрузить настройки или вернуть None, если файл отсутствует."""
    try:
        file_path = get_settings_file_path(projector_ip)
        if not os.path.exists(file_path):
            logger.info(f"Settings file not found for projector {projector_ip}")
            return None
        with open(file_path, 'r', encoding='utf-8') as f:
            settings = json.load(f)
        logger.info(f"Loaded settings for projector {projector_ip}")
        return settings
    except Exception as exc:
        logger.error(f"Error loading settings for projector {projector_ip}: {exc}")
        return None


def delete_projector_settings(projector_ip: str) -> bool:
    """Удалить файл настроек. True при успехе."""
    try:
        file_path = get_settings_file_path(projector_ip)
        if not os.path.exists(file_path):
            logger.warning(f"Settings file not found for projector {projector_ip}")
            return False
        os.remove(file_path)
        logger.info(f"Deleted settings file for projector {projector_ip}")
        return True
    except Exception as exc:
        logger.error(f"Error deleting settings for projector {projector_ip}: {exc}")
        return False

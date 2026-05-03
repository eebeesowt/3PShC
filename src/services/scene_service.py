"""
Сервис сцен: оркестрация load/save поверх scene_repository и Projector.

Нюанс: при сохранении делает live-снимок состояния каждого проектора
(get_lens_position + get_aspect_ratio + get_installation_mode) и собирает
итоговый dict через ProjectorApi.snapshot_settings_dict.
"""
from typing import List, Optional, Tuple

from infra.scene_repository import load_scene, save_scene_to_json
from infra.settings_repository import create_projector_settings_dict
from services.projector import Projector
from utils.logger import setup_logger

logger = setup_logger(__name__)

WindowSize = Tuple[int, int]
SceneEntry = Tuple[Projector, int, int, dict]
ProjectorWithPosition = Tuple[Projector, int, int]


class SceneService:
    """Загрузка и сохранение сцен. Без зависимости от UI."""

    @staticmethod
    async def load(
        file_path: str,
    ) -> Tuple[Optional[WindowSize], List[SceneEntry]]:
        """Делегирует scene_repository — auto-detect формата, async network probe."""
        return await load_scene(file_path)

    @staticmethod
    async def save(
        file_path: str,
        window_size: WindowSize,
        projectors_with_positions: List[ProjectorWithPosition],
    ) -> None:
        """
        Опросить состояние каждого проектора, собрать снимки настроек
        и записать сцену в JSON.
        """
        entries: List[SceneEntry] = []
        for projector, x, y in projectors_with_positions:
            settings = await SceneService._collect_settings(projector)
            entries.append((projector, x, y, settings))

        save_scene_to_json(file_path, window_size, entries)

    @staticmethod
    async def _collect_settings(projector: Projector) -> dict:
        try:
            await projector.get_lens_position()
            await projector.get_aspect_ratio()
            await projector.get_installation_mode()
            return projector.api.snapshot_settings_dict()
        except Exception as exc:
            logger.warning(
                f"Could not get settings for {projector.label}: {exc}"
            )
            return create_projector_settings_dict(
                h_position='0',
                v_position='0',
                aspect_ratio='16:9',
                installation_mode='Front/Desk',
            )

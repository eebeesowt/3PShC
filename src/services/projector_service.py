"""
Сервис управления группой проекторов.
Чистая бизнес-логика без UI и I/O — оркестрирует операции над списком Projector.
"""
import asyncio
from typing import List, Optional

from lib.projector import Projector
from utils.logger import setup_logger

logger = setup_logger(__name__)


class ProjectorService:
    """Управление списком проекторов и групповыми операциями."""

    def __init__(self) -> None:
        self.projectors: List[Projector] = []

    def add_projector(self, projector: Projector) -> bool:
        if any(p.ip == projector.ip for p in self.projectors):
            logger.warning(f"Projector with IP {projector.ip} already exists")
            return False
        self.projectors.append(projector)
        logger.info(f"Added projector {projector.label} ({projector.ip})")
        return True

    def remove_projector(self, projector: Projector) -> None:
        if projector in self.projectors:
            self.projectors.remove(projector)
            logger.info(f"Removed projector {projector.label}")

    def get_projector_by_ip_room_number(self, room_number: str) -> Optional[Projector]:
        for projector in self.projectors:
            if projector.ip_room_number == room_number:
                return projector
        return None

    async def update_all(self) -> None:
        tasks = []
        for projector in self.projectors:
            try:
                tasks.append(asyncio.create_task(projector.get_info()))
            except Exception as exc:
                logger.error(f"Error creating update task for {projector.label}: {exc}")

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(
                        f"Error updating projector {self.projectors[i].label}: {result}"
                    )

    async def open_group_shutters(self, group_indices: List[int]) -> None:
        await self._dispatch_indexed(group_indices, lambda p: p.shutter_open())

    async def close_group_shutters(self, group_indices: List[int]) -> None:
        await self._dispatch_indexed(group_indices, lambda p: p.shutter_close())

    async def power_on_all(self) -> None:
        await self._dispatch_all(lambda p: p.power_on())

    async def power_off_all(self) -> None:
        await self._dispatch_all(lambda p: p.power_off())

    def clear(self) -> None:
        self.projectors.clear()

    # ---- private dispatch helpers ----

    async def _dispatch_indexed(self, indices: List[int], action) -> None:
        tasks = [
            asyncio.create_task(action(self.projectors[idx]))
            for idx in indices
            if 0 <= idx < len(self.projectors)
        ]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _dispatch_all(self, action) -> None:
        tasks = [
            asyncio.create_task(action(projector))
            for projector in self.projectors
        ]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

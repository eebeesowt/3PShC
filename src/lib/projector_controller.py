"""
Контроллер для управления группой проекторов.
Содержит бизнес-логику без UI.
"""
import asyncio
from typing import List, Callable, Optional
from lib.projector import Projector
from utils.logger import setup_logger

logger = setup_logger(__name__)


class ProjectorController:
    """Управление проекторами без привязки к UI"""
    
    def __init__(self):
        self.projectors: List[Projector] = []
    
    def add_projector(self, projector: Projector) -> bool:
        """
        Добавить проектор в список.
        Возвращает False если проектор с таким IP уже существует.
        """
        if any(p.ip == projector.ip for p in self.projectors):
            logger.warning(f"Projector with IP {projector.ip} already exists")
            return False
        
        self.projectors.append(projector)
        logger.info(f"Added projector {projector.label} ({projector.ip})")
        return True
    
    def remove_projector(self, projector: Projector):
        """Удалить проектор из списка"""
        if projector in self.projectors:
            self.projectors.remove(projector)
            logger.info(f"Removed projector {projector.label}")
    
    def get_projector_by_ip_room_number(self, room_number: str) -> Optional[Projector]:
        """Найти проектор по последней части IP адреса"""
        for projector in self.projectors:
            if projector.ip_room_nomber == room_number:
                return projector
        return None
    
    async def update_all(self):
        """Обновить информацию о всех проекторах"""
        tasks = []
        for projector in self.projectors:
            try:
                task = asyncio.create_task(projector.get_info())
                tasks.append(task)
            except Exception as e:
                logger.error(f"Error creating update task for {projector.label}: {e}")
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Error updating projector {self.projectors[i].label}: {result}")
    
    async def open_group_shutters(self, group_indices: List[int]):
        """Открыть шаттеры у проекторов из группы"""
        tasks = []
        for idx in group_indices:
            if 0 <= idx < len(self.projectors):
                task = asyncio.create_task(
                    self.projectors[idx].shutter_open()
                )
                tasks.append(task)
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def close_group_shutters(self, group_indices: List[int]):
        """Закрыть шаттеры у проекторов из группы"""
        tasks = []
        for idx in group_indices:
            if 0 <= idx < len(self.projectors):
                task = asyncio.create_task(
                    self.projectors[idx].shutter_close()
                )
                tasks.append(task)
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def power_on_all(self):
        """Включить все проекторы"""
        tasks = [
            asyncio.create_task(projector.power_on())
            for projector in self.projectors
        ]
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def power_off_all(self):
        """Выключить все проекторы"""
        tasks = [
            asyncio.create_task(projector.power_off())
            for projector in self.projectors
        ]
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    def clear(self):
        """Очистить список проекторов"""
        self.projectors.clear()

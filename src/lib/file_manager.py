"""
Менеджер для работы с файлами конфигурации проекторов.
"""
import asyncio
from typing import List, Tuple, Optional
from lib.projector import Projector
from utils.logger import setup_logger

logger = setup_logger(__name__)


class FileManager:
    """Управление сохранением и загрузкой конфигурации проекторов"""
    
    @staticmethod
    async def load_from_file(file_path: str) -> Tuple[
        Optional[Tuple[int, int]], 
        List[Tuple[Projector, int, int]]
    ]:
        """
        Загрузить проекторы из файла.
        
        Returns:
            Tuple[window_size, projectors_with_positions]
            где window_size = (width, height) или None
            projectors_with_positions = [(projector, x, y), ...]
        """
        window_size = None
        projectors_data: List[Tuple[Projector, int, int]] = []
        pending_projectors: List[Tuple[Projector, int, int]] = []
        
        try:
            with open(file_path, "r", encoding='utf-8') as file:
                lines = file.readlines()
                
                # Загружаем размер окна из первой строки
                if len(lines) > 0:
                    try:
                        width, height = map(int, lines[0].strip().split(","))
                        window_size = (width, height)
                        logger.info(f"Window size: {width}x{height}")
                    except ValueError:
                        logger.warning("Invalid window size format; skipping.")
                
                # Загружаем проекторы из оставшихся строк
                for line in lines[1:]:
                    parts = line.strip().split(",")
                    if len(parts) != 7:
                        logger.warning(f"Invalid line format: {line}")
                        continue
                    
                    ip, port, username, password, label, x, y = parts
                    port = int(port)
                    x = int(x)
                    y = int(y)
                    
                    try:
                        new_projector = Projector(
                            ip=ip,
                            port=port,
                            login=username,
                            password=password,
                            label=label,
                            id=len(pending_projectors) + 1,
                        )
                        pending_projectors.append((new_projector, x, y))
                    except Exception as e:
                        logger.error(f"Error creating projector {ip}: {e}")
                        continue

            if pending_projectors:
                tasks = [
                    asyncio.create_task(projector.get_info())
                    for projector, _, _ in pending_projectors
                ]
                results = await asyncio.gather(*tasks, return_exceptions=True)

                for (projector, x, y), result in zip(pending_projectors, results):
                    if isinstance(result, Exception):
                        logger.error(
                            f"Error creating projector {projector.ip}: {result}"
                        )
                        continue
                    logger.info(f"Loaded projector {projector.label} ({projector.ip})")
                    projectors_data.append((projector, x, y))

                for idx, (projector, _, _) in enumerate(projectors_data, start=1):
                    projector.id = idx
            
            logger.info(f"Loaded {len(projectors_data)} projectors from {file_path}")
            return window_size, projectors_data
            
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            return None, []
        except Exception as e:
            logger.error(f"Error while loading projectors: {e}")
            return None, []
    
    @staticmethod
    def save_to_file(
        file_path: str,
        window_size: Tuple[int, int],
        projectors_with_positions: List[Tuple[Projector, int, int]]
    ):
        """
        Сохранить проекторы в файл.
        
        Args:
            file_path: Путь к файлу
            window_size: (width, height) окна
            projectors_with_positions: [(projector, x, y), ...]
        """
        try:
            with open(file_path, "w", encoding='utf-8') as file:
                # Сохраняем размер окна
                width, height = window_size
                file.write(f"{width},{height}\n")
                
                # Сохраняем данные проекторов
                for projector, x, y in projectors_with_positions:
                    file.write(
                        f"{projector.ip},{projector.port},{projector.login},"
                        f"{projector.password},{projector.label},{x},{y}\n"
                    )
            
            logger.info(f"Saved {len(projectors_with_positions)} projectors to {file_path}")
            
        except Exception as e:
            logger.error(f"Error while saving projectors: {e}")

"""
Точка входа 3P Shutter Control.
Bootstrapping: создаёт сервисы, инжектирует их в MainWindow, запускает
asyncio-цикл.
"""
import asyncio

from lib.osc_controller import OSCController
from services.projector_service import ProjectorService
from services.scene_service import SceneService
from ui.main_window import MainWindow
from utils.logger import setup_logger

logger = setup_logger(__name__)


def main() -> None:
    logger.info("=== Starting 3P Shutter Control ===")
    controller = ProjectorService()
    osc_controller = OSCController()
    scene_service = SceneService()
    window = MainWindow(controller, osc_controller, scene_service)
    asyncio.run(window.run())


if __name__ == "__main__":
    main()

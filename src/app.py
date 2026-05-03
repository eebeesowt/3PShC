"""
Точка входа 3P Shutter Control.

Bootstrap: собирает сервисы, OSC-контроллер и AppWindow на DearPyGui,
затем запускает единый asyncio-loop, который крутит DPG-frame и обслуживает
сетевые задачи.
"""
import asyncio

from infra.osc_server import OSCController
from services.projector_service import ProjectorService
from services.scene_service import SceneService
from ui.app_window import AppWindow
from utils.logger import setup_logger

logger = setup_logger(__name__)


def main() -> None:
    logger.info("=== Starting 3P Shutter Control ===")
    controller = ProjectorService()
    osc = OSCController()
    scene_service = SceneService()
    window = AppWindow(controller, osc, scene_service)
    asyncio.run(window.run())


if __name__ == "__main__":
    main()

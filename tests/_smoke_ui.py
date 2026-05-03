"""
Ручной smoke-запуск UI на ~2 секунды без проекторов. НЕ pytest-тест:
DPG требует main thread + display, и pytest на CI падал бы.
Запускать вручную: PYTHONPATH=src python tests/_smoke_ui.py
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from infra.osc_server import OSCController
from services.projector_service import ProjectorService
from services.scene_service import SceneService
from ui.app_window import AppWindow


async def main():
    window = AppWindow(ProjectorService(), OSCController(port=17001), SceneService())

    async def stop_after_delay():
        await asyncio.sleep(2.0)
        window._closing = True

    asyncio.create_task(stop_after_delay())
    await window.run()
    print("UI smoke OK")


if __name__ == "__main__":
    asyncio.run(main())

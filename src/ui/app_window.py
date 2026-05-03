"""
Главное окно приложения на DearPyGui.

Жизненный цикл:
- create_context → install_global_theme → create_viewport → setup_dearpygui
  → show_viewport → render-loop в asyncio → destroy_context

Render-loop:
- Корутина run() поочерёдно зовёт dpg.render_dearpygui_frame() и спит
  ~16 ms (60 fps). UI-колбэки выполняются внутри render_dearpygui_frame()
  в этом же потоке, поэтому asyncio.create_task() из них работает напрямую.

OSC интеграция:
- OSCController крутится в отдельном потоке; колбэки приходят в asyncio
  через call_soon_threadsafe → AppWindow подписывается на события
  (OSCEvent.SHUTTER_OPEN/CLOSE/GROUP_OPEN/CLOSE) при start().
"""
import asyncio
from typing import Any, Callable, Coroutine, Dict, List, Optional, Set

import dearpygui.dearpygui as dpg

from infra.osc_server import OSCController, OSCEvent
from services.projector import Projector
from services.projector_service import ProjectorService
from services.scene_service import SceneService
from ui.add_projector_dialog import AddProjectorDialog
from ui.dpg_theme import ButtonThemes, Palette, install_global_theme
from ui.file_dialogs import save_scene_dialog, load_scene_dialog
from ui.projector_card import CARD_HEIGHT, CARD_WIDTH, ProjectorCard
from ui.settings_dialog import ProjectorSettingsDialog
from utils.logger import setup_logger

logger = setup_logger(__name__)


VIEWPORT_TITLE = "3P Shutter Control"
VIEWPORT_WIDTH = 1100
VIEWPORT_HEIGHT = 720
TOOLBAR_HEIGHT = 70
FRAME_INTERVAL = 1 / 60


class AppWindow:
    """Корневой контроллер UI — собирает виджеты и крутит render-loop."""

    def __init__(
        self,
        controller: ProjectorService,
        osc: OSCController,
        scene_service: SceneService,
    ) -> None:
        self.controller = controller
        self.osc = osc
        self.scene_service = scene_service

        self.cards: List[ProjectorCard] = []
        self._tasks: Set[asyncio.Task] = set()
        self._closing = False
        self._open_dialogs: List[Any] = []

        # Layout offsets для авто-расстановки новых карточек
        self._next_grid_index = 0

    # ---- Жизненный цикл задач ----

    def _create_task(
        self, coro: Coroutine[Any, Any, Any], description: str
    ) -> asyncio.Task:
        task = asyncio.create_task(coro)
        self._tasks.add(task)

        def _on_done(done: asyncio.Task) -> None:
            self._tasks.discard(done)
            try:
                exc = done.exception()
            except asyncio.CancelledError:
                return
            if exc:
                logger.error(f"Task '{description}' failed: {exc}", exc_info=exc)

        task.add_done_callback(_on_done)
        return task

    # ---- Bootstrap ----

    def _setup_dpg(self) -> None:
        dpg.create_context()
        install_global_theme()
        dpg.create_viewport(
            title=VIEWPORT_TITLE,
            width=VIEWPORT_WIDTH,
            height=VIEWPORT_HEIGHT,
        )
        dpg.set_viewport_resize_callback(self._on_viewport_resize)
        dpg.setup_dearpygui()
        self._build_toolbar()
        dpg.show_viewport()

    def _build_toolbar(self) -> None:
        with dpg.window(
            tag="toolbar",
            no_title_bar=True,
            no_move=True,
            no_resize=True,
            no_collapse=True,
            no_scrollbar=True,
            pos=[0, 0],
            width=VIEWPORT_WIDTH,
            height=TOOLBAR_HEIGHT,
        ):
            with dpg.group(horizontal=True):
                self._add_button("Add Projector", self._on_add_projector, 'info', width=130)
                self._add_button("Load Scene", self._on_load_scene, 'success', width=110)
                self._add_button("Save Scene", self._on_save_scene, 'success_dark', width=110)
                dpg.add_spacer(width=18)
                self._add_button("Update", self._on_update, 'warning', width=90)
                dpg.add_spacer(width=18)
                self._add_button("Power All On", self._on_power_on_all, 'success_dark', width=120)
                self._add_button("Power All Off", self._on_power_off_all, 'danger_dark', width=120)

            with dpg.group(horizontal=True):
                self._add_button("Open Group", self._on_open_group, 'primary',
                                 width=140, height=34)
                self._add_button("Close Group", self._on_close_group, 'danger',
                                 width=140, height=34)

    def _add_button(
        self, label: str, callback: Callable, theme: str,
        width: int = 100, height: int = 28,
    ) -> int:
        btn = dpg.add_button(label=label, callback=callback, width=width, height=height)
        dpg.bind_item_theme(btn, ButtonThemes.get(theme))
        return btn

    def _on_viewport_resize(self) -> None:
        if dpg.does_item_exist("toolbar"):
            dpg.set_item_width("toolbar", dpg.get_viewport_client_width())

    # ---- OSC ----

    def _wire_osc(self) -> None:
        self.osc.on(OSCEvent.SHUTTER_OPEN, self._osc_shutter_open)
        self.osc.on(OSCEvent.SHUTTER_CLOSE, self._osc_shutter_close)
        self.osc.on(OSCEvent.GROUP_OPEN, self._on_open_group)
        self.osc.on(OSCEvent.GROUP_CLOSE, self._on_close_group)

    def _osc_shutter_open(self, room: str) -> None:
        self._dispatch_osc_shutter(room, open_shutter=True)

    def _osc_shutter_close(self, room: str) -> None:
        self._dispatch_osc_shutter(room, open_shutter=False)

    def _dispatch_osc_shutter(self, room: str, open_shutter: bool) -> None:
        projector = self.controller.get_projector_by_ip_room_number(room)
        if projector is None:
            logger.debug(f"OSC: no projector for room {room}")
            return
        for card in self.cards:
            if card.projector is projector:
                self._execute_shutter(card, open_shutter)
                return

    # ---- Карточки ----

    def _on_add_projector(self) -> None:
        dialog = AddProjectorDialog(on_add=self._add_projector_from_dialog)
        self._open_dialogs.append(dialog)

    def _add_projector_from_dialog(self, projector: Projector) -> None:
        if not self.controller.add_projector(projector):
            logger.warning(f"Projector {projector.ip} already exists")
            return
        card = self._create_card(projector)
        self._auto_place(card)

    def _create_card(self, projector: Projector) -> ProjectorCard:
        card = ProjectorCard(
            projector,
            on_remove=self._handle_card_removed,
            on_open_settings=self._open_settings_for,
            on_shutter=self._execute_shutter,
            on_set_shutter_in=self._handle_set_shutter_in,
            on_set_shutter_out=self._handle_set_shutter_out,
        )
        self.cards.append(card)
        return card

    def _auto_place(self, card: ProjectorCard) -> None:
        col = self._next_grid_index % 3
        row = self._next_grid_index // 3
        x = 10 + col * (CARD_WIDTH + 12)
        y = TOOLBAR_HEIGHT + 10 + row * (CARD_HEIGHT + 12)
        card.set_position(x, y)
        self._next_grid_index += 1

    def _handle_card_removed(self, card: ProjectorCard) -> None:
        if card in self.cards:
            self.cards.remove(card)
            self.controller.remove_projector(card.projector)
            logger.info(f"Removed card for {card.projector.label}")

    def _open_settings_for(self, card: ProjectorCard) -> None:
        dialog = ProjectorSettingsDialog(
            projector=card.projector,
            run_task=self._create_task,
        )
        self._open_dialogs.append(dialog)

    # ---- Действия с шаттером ----

    def _execute_shutter(self, card: ProjectorCard, open_shutter: bool) -> None:
        async def _run():
            try:
                if open_shutter:
                    await card.projector.shutter_open()
                else:
                    await card.projector.shutter_close()
                card.update_shutter_status()
            except Exception:
                card.show_error_status()
                raise

        action = "open" if open_shutter else "close"
        self._create_task(_run(), f"shutter {action} {card.projector.label}")

    def _handle_set_shutter_in(self, card: ProjectorCard, value: str) -> None:
        logger.info(f"Set shutter-in {value} for {card.projector.label}")
        self._create_task(
            card.projector.set_shutter_in(value),
            f"set shutter in {card.projector.label}",
        )

    def _handle_set_shutter_out(self, card: ProjectorCard, value: str) -> None:
        logger.info(f"Set shutter-out {value} for {card.projector.label}")
        self._create_task(
            card.projector.set_shutter_out(value),
            f"set shutter out {card.projector.label}",
        )

    # ---- Группа и питание ----

    def _on_open_group(self) -> None:
        self._dispatch_group("Open group", self.controller.open_group_shutters)

    def _on_close_group(self) -> None:
        self._dispatch_group("Close group", self.controller.close_group_shutters)

    def _dispatch_group(self, action_name: str, method) -> None:
        indices = [i for i, c in enumerate(self.cards) if c.is_in_group()]
        logger.info(f"{action_name} for {len(indices)} projectors")

        async def _run():
            await method(indices)
            for i in indices:
                if i < len(self.cards):
                    self.cards[i].update_shutter_status()

        self._create_task(_run(), action_name)

    def _on_update(self) -> None:
        async def _run():
            logger.info("Updating all projectors")
            await self.controller.update_all()
            for card in self.cards:
                card.update_power_status()
                card.update_shutter_status()

        self._create_task(_run(), "update all")

    def _on_power_on_all(self) -> None:
        self._dispatch_power("Power on all", self.controller.power_on_all)

    def _on_power_off_all(self) -> None:
        self._dispatch_power("Power off all", self.controller.power_off_all)

    def _dispatch_power(self, action_name: str, method) -> None:
        async def _run():
            logger.info(action_name)
            await method()
            for card in self.cards:
                card.update_power_status()

        self._create_task(_run(), action_name)

    # ---- Сцены ----

    def _on_load_scene(self) -> None:
        self._create_task(self._async_load_scene(), "load scene")

    async def _async_load_scene(self) -> None:
        path = await load_scene_dialog()
        if not path:
            return
        logger.info(f"Loading scene {path}")

        for card in list(self.cards):
            card.destroy()
        self.cards.clear()
        self.controller.clear()
        self._next_grid_index = 0

        window_size, entries = await self.scene_service.load(path)
        if window_size:
            try:
                dpg.set_viewport_width(window_size[0])
                dpg.set_viewport_height(window_size[1])
            except Exception as exc:
                logger.warning(f"Could not resize viewport: {exc}")

        for projector, x, y, settings in entries:
            self.controller.add_projector(projector)
            card = self._create_card(projector)
            card.set_position(x, y)
            self._next_grid_index = max(self._next_grid_index, len(self.cards))
            if settings:
                self._create_task(
                    projector.apply_saved_settings(settings),
                    f"apply scene settings {projector.label}",
                )
        logger.info(f"Loaded {len(entries)} projectors")

    def _on_save_scene(self) -> None:
        self._create_task(self._async_save_scene(), "save scene")

    async def _async_save_scene(self) -> None:
        path = await save_scene_dialog()
        if not path:
            return
        logger.info(f"Saving scene to {path}")
        size = (dpg.get_viewport_client_width(), dpg.get_viewport_client_height())
        with_positions = [(c.projector, *c.get_position()) for c in self.cards]
        await self.scene_service.save(path, size, with_positions)
        logger.info(f"Saved {len(self.cards)} projectors")

    # ---- Render-loop / shutdown ----

    async def run(self) -> None:
        self._setup_dpg()
        await self.osc.start()
        self._wire_osc()
        logger.info("Application UI ready")

        try:
            while not self._closing and dpg.is_dearpygui_running():
                dpg.render_dearpygui_frame()
                await asyncio.sleep(FRAME_INTERVAL)
        finally:
            await self._shutdown()

    async def _shutdown(self) -> None:
        if self._closing:
            return
        self._closing = True
        logger.info("Shutting down...")

        self.osc.stop()

        for dialog in list(self._open_dialogs):
            try:
                dialog.close()
            except Exception:
                pass
        self._open_dialogs.clear()

        pending = [t for t in self._tasks if not t.done()]
        for t in pending:
            t.cancel()
        if pending:
            await asyncio.gather(*pending, return_exceptions=True)

        try:
            ButtonThemes.reset()
            dpg.destroy_context()
        except Exception as exc:
            logger.warning(f"Error destroying DPG context: {exc}")

        logger.info("Application stopped")

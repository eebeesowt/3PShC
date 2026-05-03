"""
Главное окно приложения. Содержит виджеты, обработчики UI/OSC и главный цикл
Tkinter. Бизнес-логика инжектируется через конструктор.
"""
import asyncio
import customtkinter as ctk
from tkinter import filedialog
from typing import Any, Coroutine, List, Optional, Set

from lib.osc_controller import OSCController
from lib.projector import Projector
from services.projector_service import ProjectorService
from services.scene_service import SceneService
from theme import AppConfig, Theme
from ui.add_projector_dialog import AddProjectorDialog
from ui.projector_frame import ProjectorFrame
from utils.logger import setup_logger

logger = setup_logger(__name__)


class MainWindow:
    """Главное окно приложения."""

    def __init__(
        self,
        controller: ProjectorService,
        osc_controller: OSCController,
        scene_service: SceneService,
    ) -> None:
        self.controller = controller
        self.osc_controller = osc_controller
        self.scene_service = scene_service

        self.projector_frames: List[ProjectorFrame] = []
        self._tasks: Set[asyncio.Task] = set()
        self._closing = False

        self._create_window()
        self._create_widgets()
        self._setup_osc_callbacks()

    # ---- Жизненный цикл задач ----

    def _create_task(
        self, coro: Coroutine[Any, Any, Any], description: str
    ) -> asyncio.Task:
        """Создать отслеживаемую async-задачу с логированием ошибок."""
        task = asyncio.create_task(coro)
        self._tasks.add(task)

        def _on_done(done_task: asyncio.Task):
            self._tasks.discard(done_task)
            try:
                exception = done_task.exception()
            except asyncio.CancelledError:
                return
            if exception:
                logger.error(f"Task '{description}' failed: {exception}")

        task.add_done_callback(_on_done)
        return task

    # ---- Сборка окна ----

    def _create_window(self) -> None:
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.root = ctk.CTk()
        self.root.title(AppConfig.WINDOW_TITLE)
        self.root.geometry(f"{AppConfig.WINDOW_WIDTH}x{AppConfig.WINDOW_HEIGHT}")
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        logger.info("Main window created")

    def _create_button(
        self,
        text: str,
        command,
        fg_color: str,
        hover_color: str,
        width: Optional[int] = None,
        text_color: Optional[str] = None,
    ) -> ctk.CTkButton:
        kwargs = {
            'text': text,
            'command': command,
            'fg_color': fg_color,
            'hover_color': hover_color,
        }
        if width:
            kwargs['width'] = width
        if text_color:
            kwargs['text_color'] = text_color
        return ctk.CTkButton(self.button_frame, **kwargs)

    def _create_widgets(self) -> None:
        self.button_frame = ctk.CTkFrame(self.root)
        self.button_frame.pack(
            side='top', fill='x',
            padx=AppConfig.PADDING_MEDIUM, pady=AppConfig.PADDING_MEDIUM,
        )

        self.open_group_btn = self._create_button(
            'Open Group', self._on_open_group,
            Theme.PRIMARY, Theme.PRIMARY_HOVER,
        )
        self.close_group_btn = self._create_button(
            'Close Group', self._on_close_group,
            Theme.DANGER, Theme.DANGER_HOVER,
        )
        self.update_btn = self._create_button(
            'Update', self._on_update,
            Theme.WARNING, Theme.WARNING_HOVER,
            width=AppConfig.BUTTON_WIDTH_NORMAL,
            text_color=Theme.TEXT_SECONDARY,
        )
        self.add_projector_btn = self._create_button(
            'Add Projector', self._on_add_projector,
            Theme.INFO, Theme.INFO_HOVER,
            width=AppConfig.BUTTON_WIDTH_LARGE,
        )
        self.load_btn = self._create_button(
            'Load from File', self._on_load,
            Theme.SUCCESS, Theme.SUCCESS_HOVER,
            width=AppConfig.BUTTON_WIDTH_XLARGE,
        )
        self.save_btn = self._create_button(
            'Save to File', self._on_save,
            Theme.DARK, Theme.DARK_HOVER,
            width=AppConfig.BUTTON_WIDTH_XLARGE,
        )
        self.power_on_all_btn = self._create_button(
            'On All', self._on_power_on_all,
            Theme.SUCCESS_DARK, Theme.SUCCESS_DARK_HOVER, width=70,
        )
        self.power_off_all_btn = self._create_button(
            'Off All', self._on_power_off_all,
            Theme.ERROR_BG, Theme.ERROR_HOVER, width=70,
        )

        self.open_group_btn.grid(
            row=1, column=0,
            ipadx=AppConfig.GRID_IPADX, ipady=AppConfig.GRID_IPADY,
            pady=AppConfig.PADDING_LARGE,
        )
        self.close_group_btn.grid(
            row=1, column=1,
            ipadx=AppConfig.GRID_IPADX, ipady=AppConfig.GRID_IPADY,
            pady=AppConfig.PADDING_LARGE,
        )
        self.update_btn.grid(
            row=1, column=2,
            padx=AppConfig.PADDING_MEDIUM, pady=AppConfig.PADDING_LARGE,
        )

        self.add_projector_btn.grid(
            row=0, column=0,
            padx=AppConfig.PADDING_MEDIUM, pady=AppConfig.PADDING_SMALL,
        )
        self.load_btn.grid(
            row=0, column=1,
            padx=AppConfig.PADDING_MEDIUM, pady=AppConfig.PADDING_SMALL,
        )
        self.save_btn.grid(
            row=0, column=2,
            padx=AppConfig.PADDING_MEDIUM, pady=AppConfig.PADDING_SMALL,
        )
        self.power_on_all_btn.grid(
            row=0, column=3,
            padx=AppConfig.PADDING_MEDIUM, pady=AppConfig.PADDING_SMALL,
        )
        self.power_off_all_btn.grid(
            row=1, column=3,
            padx=AppConfig.PADDING_MEDIUM, pady=AppConfig.PADDING_SMALL,
        )

        self.canvas = ctk.CTkFrame(self.root, fg_color=Theme.CANVAS_BG)
        self.canvas.pack(
            side='top', fill='both', expand=True,
            padx=AppConfig.PADDING_MEDIUM, pady=AppConfig.PADDING_MEDIUM,
        )

    # ---- OSC ----

    def _setup_osc_callbacks(self) -> None:
        self.osc_controller.on_shutter_open = self._handle_osc_shutter_open
        self.osc_controller.on_shutter_close = self._handle_osc_shutter_close
        self.osc_controller.on_group_open = self._on_open_group
        self.osc_controller.on_group_close = self._on_close_group

    def _handle_osc_shutter_open(self, room_number: str) -> None:
        self._dispatch_osc_shutter(room_number, open_shutter=True)

    def _handle_osc_shutter_close(self, room_number: str) -> None:
        self._dispatch_osc_shutter(room_number, open_shutter=False)

    def _dispatch_osc_shutter(self, room_number: str, open_shutter: bool) -> None:
        projector = self.controller.get_projector_by_ip_room_number(room_number)
        if not projector:
            return
        for frame in self.projector_frames:
            if frame.projector == projector:
                action = 'open' if open_shutter else 'close'
                self._create_task(
                    frame.execute_shutter_action(open_shutter=open_shutter),
                    f"execute shutter {action} for {projector.label}",
                )
                return

    # ---- Группа и питание ----

    def _execute_group_action(self, action_name: str, controller_method) -> None:
        group_indices = [
            i for i, frame in enumerate(self.projector_frames)
            if frame.grp.get()
        ]
        logger.info(f"{action_name} for {len(group_indices)} projectors")
        self._create_task(controller_method(group_indices), action_name)
        for idx in group_indices:
            if idx < len(self.projector_frames):
                self.projector_frames[idx].update_screen_status()

    def _on_open_group(self) -> None:
        self._execute_group_action(
            "Opening group shutters", self.controller.open_group_shutters
        )

    def _on_close_group(self) -> None:
        self._execute_group_action(
            "Closing group shutters", self.controller.close_group_shutters
        )

    def _on_update(self) -> None:
        async def update_all():
            logger.info("Updating all projectors")
            await self.controller.update_all()
            for frame in self.projector_frames:
                frame.update_screen_status()
                frame.update_power_status()

        self._create_task(update_all(), "update all projectors")

    def _execute_power_action(self, action_name: str, controller_method) -> None:
        async def power_action():
            logger.info(action_name)
            await controller_method()
            for frame in self.projector_frames:
                frame.update_power_status()

        self._create_task(power_action(), action_name)

    def _on_power_on_all(self) -> None:
        self._execute_power_action(
            "Powering on all projectors", self.controller.power_on_all
        )

    def _on_power_off_all(self) -> None:
        self._execute_power_action(
            "Powering off all projectors", self.controller.power_off_all
        )

    # ---- Добавление/удаление проекторов ----

    def _on_add_projector(self) -> None:
        AddProjectorDialog(self.root, self._add_projector)

    def _add_projector(self, projector: Projector) -> None:
        if not self.controller.add_projector(projector):
            logger.warning(f"Projector {projector.ip} already exists")
            return

        logger.info(f"Adding projector {projector.label} ({projector.ip})")
        frame = ProjectorFrame(
            projector, self.canvas, self._remove_frame, lambda: None
        )
        x_offset = (
            AppConfig.PROJECTOR_OFFSET_X
            + (len(self.projector_frames) % 2) * AppConfig.PROJECTOR_SPACING_X
        )
        y_offset = (
            AppConfig.PROJECTOR_OFFSET_Y
            + (len(self.projector_frames) // 2) * AppConfig.PROJECTOR_SPACING_Y
        )
        frame.set_position(x_offset, y_offset)
        self.projector_frames.append(frame)

    def _remove_frame(self, frame: ProjectorFrame) -> None:
        if frame in self.projector_frames:
            logger.info(f"Removing projector {frame.projector.label}")
            self.projector_frames.remove(frame)
            self.controller.remove_projector(frame.projector)

    # ---- Сцена: load/save ----

    def _on_load(self) -> None:
        self._create_task(self._async_load(), "load projectors from file")

    async def _async_load(self) -> None:
        file_path = filedialog.askopenfilename(
            title="Select Projectors File",
            filetypes=(
                ("JSON Files", "*.json"),
                ("Text Files (legacy)", "*.txt"),
                ("All Files", "*.*"),
            ),
        )
        if not file_path:
            return

        logger.info(f"Loading projectors from {file_path}")

        for frame in self.projector_frames:
            frame.frame.destroy()
        self.projector_frames.clear()
        self.controller.clear()

        window_size, projectors_data = await self.scene_service.load(file_path)

        if window_size:
            width, height = window_size
            self.root.geometry(f"{width}x{height}")
            logger.info(f"Set window size to {width}x{height}")

        for projector, x, y, settings in projectors_data:
            self.controller.add_projector(projector)
            frame = ProjectorFrame(
                projector, self.canvas, self._remove_frame, lambda: None
            )
            frame.set_position(x, y)
            self.projector_frames.append(frame)

            if settings:
                logger.info(f"Applying scene settings for {projector.label}")
                self._create_task(
                    projector.apply_saved_settings(settings),
                    f"Applying settings for {projector.label}",
                )

        logger.info(f"Loaded {len(projectors_data)} projectors")

    def _on_save(self) -> None:
        self._create_task(self._async_save(), "save projectors to file")

    async def _async_save(self) -> None:
        file_path = filedialog.asksaveasfilename(
            title="Save Projectors File",
            defaultextension=".json",
            filetypes=(("JSON Files", "*.json"), ("All Files", "*.*")),
        )
        if not file_path:
            return

        logger.info(f"Saving projectors to {file_path}")
        window_size = (self.root.winfo_width(), self.root.winfo_height())
        projectors_with_positions = [
            (frame.projector, *frame.get_position())
            for frame in self.projector_frames
        ]
        await self.scene_service.save(file_path, window_size, projectors_with_positions)
        logger.info(f"Saved {len(self.projector_frames)} projectors")

    # ---- Закрытие приложения ----

    def _on_close(self) -> None:
        """Tk-callback при нажатии X. Запускает graceful shutdown в asyncio."""
        if self._closing:
            return
        self._closing = True
        # Не используем _create_task, чтобы shutdown сам себя не отменил
        asyncio.create_task(self._async_shutdown())

    async def _async_shutdown(self) -> None:
        """Корректно завершить in-flight задачи и закрыть окно."""
        logger.info("Closing application...")
        self.osc_controller.stop()

        pending = [t for t in self._tasks if not t.done()]
        for task in pending:
            task.cancel()
        if pending:
            await asyncio.gather(*pending, return_exceptions=True)

        try:
            self.root.destroy()
        except Exception as exc:
            logger.warning(f"Error while destroying root: {exc}")

    # ---- Главный цикл ----

    async def run(self) -> None:
        logger.info("Starting OSC server...")
        await self.osc_controller.start()

        try:
            while not self._closing and self.root.winfo_exists():
                self.root.update()
                await asyncio.sleep(0.01)
        finally:
            # Подстраховка: если loop вышел не через _on_close, дочистить задачи
            pending = [t for t in self._tasks if not t.done()]
            for task in pending:
                task.cancel()
            if pending:
                await asyncio.gather(*pending, return_exceptions=True)
            self.osc_controller.stop()
            logger.info("Application stopped")

"""
Главное приложение для управления проекторами Panasonic.
Рефакторенная версия с разделением логики и UI.
Использует CustomTkinter для современного интерфейса.
"""
import asyncio
import customtkinter as ctk
from tkinter import filedialog
from typing import Any, Coroutine, List, Optional, Set

from lib.projector import Projector
from lib.projector_controller import ProjectorController
from lib.file_manager import FileManager
from lib.osc_controller import OSCController
from ui.projector_frame import ProjectorFrame
from ui.add_projector_dialog import AddProjectorDialog
from theme import Theme, AppConfig
from utils.logger import setup_logger

logger = setup_logger(__name__)


class MainApplication:
    """Главное окно приложения"""
    
    def __init__(self):
        # Контроллеры (бизнес-логика)
        self.controller = ProjectorController()
        self.osc_controller = OSCController()
        self.file_manager = FileManager()
        
        # UI элементы
        self.projector_frames: List[ProjectorFrame] = []
        self._tasks: Set[asyncio.Task] = set()
        
        # Создание главного окна
        self._create_window()
        self._create_widgets()
        self._setup_osc_callbacks()

    def _create_task(self, coro: Coroutine[Any, Any, Any], description: str) -> asyncio.Task:
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
    
    def _create_window(self):
        """Создать главное окно"""
        # Установить тему и цветовую схему
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.root = ctk.CTk()
        self.root.title(AppConfig.WINDOW_TITLE)
        self.root.geometry(f"{AppConfig.WINDOW_WIDTH}x{AppConfig.WINDOW_HEIGHT}")
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        
        logger.info("Main window created")
    
    def _create_button(self, text: str, command, fg_color: str, hover_color: str, 
                      width: Optional[int] = None, text_color: Optional[str] = None) -> ctk.CTkButton:
        """Создать кнопку с заданными параметрами"""
        btn_config = {
            'text': text,
            'command': command,
            'fg_color': fg_color,
            'hover_color': hover_color
        }
        if width:
            btn_config['width'] = width
        if text_color:
            btn_config['text_color'] = text_color
        
        return ctk.CTkButton(self.button_frame, **btn_config)
    
    def _create_widgets(self):
        """Создать виджеты"""
        # Верхняя панель с кнопками
        self.button_frame = ctk.CTkFrame(self.root)
        self.button_frame.pack(side='top', fill='x', padx=AppConfig.PADDING_MEDIUM, pady=AppConfig.PADDING_MEDIUM)
        
        # Кнопки управления группой
        self.open_group_btn = self._create_button(
            'Open Group', self._on_open_group, 
            Theme.PRIMARY, Theme.PRIMARY_HOVER
        )
        
        self.close_group_btn = self._create_button(
            'Close Group', self._on_close_group,
            Theme.DANGER, Theme.DANGER_HOVER
        )
        
        # Кнопка обновления
        self.update_btn = self._create_button(
            'Update', self._on_update,
            Theme.WARNING, Theme.WARNING_HOVER,
            width=AppConfig.BUTTON_WIDTH_NORMAL,
            text_color=Theme.TEXT_SECONDARY
        )
        
        # Кнопка добавления проектора
        self.add_projector_btn = self._create_button(
            'Add Projector', self._on_add_projector,
            Theme.INFO, Theme.INFO_HOVER,
            width=AppConfig.BUTTON_WIDTH_LARGE
        )
        
        # Кнопки загрузки и сохранения
        self.load_btn = self._create_button(
            'Load from File', self._on_load,
            Theme.SUCCESS, Theme.SUCCESS_HOVER,
            width=AppConfig.BUTTON_WIDTH_XLARGE
        )
        
        self.save_btn = self._create_button(
            'Save to File', self._on_save,
            Theme.DARK, Theme.DARK_HOVER,
            width=AppConfig.BUTTON_WIDTH_XLARGE
        )
        
        # Кнопки питания
        self.power_on_all_btn = self._create_button(
            'On All', self._on_power_on_all,
            Theme.SUCCESS_DARK, Theme.SUCCESS_DARK_HOVER,
            width=70
        )
        
        self.power_off_all_btn = self._create_button(
            'Off All', self._on_power_off_all,
            Theme.ERROR_BG, Theme.ERROR_HOVER,
            width=70
        )
        
        # Расположение кнопок
        self.open_group_btn.grid(row=1, column=0, ipadx=AppConfig.GRID_IPADX, ipady=AppConfig.GRID_IPADY, pady=AppConfig.PADDING_LARGE)
        self.close_group_btn.grid(row=1, column=1, ipadx=AppConfig.GRID_IPADX, ipady=AppConfig.GRID_IPADY, pady=AppConfig.PADDING_LARGE)
        self.update_btn.grid(row=1, column=2, padx=AppConfig.PADDING_MEDIUM, pady=AppConfig.PADDING_LARGE)
        
        self.add_projector_btn.grid(row=0, column=0, padx=AppConfig.PADDING_MEDIUM, pady=AppConfig.PADDING_SMALL)
        self.load_btn.grid(row=0, column=1, padx=AppConfig.PADDING_MEDIUM, pady=AppConfig.PADDING_SMALL)
        self.save_btn.grid(row=0, column=2, padx=AppConfig.PADDING_MEDIUM, pady=AppConfig.PADDING_SMALL)
        
        self.power_on_all_btn.grid(row=0, column=3, padx=AppConfig.PADDING_MEDIUM, pady=AppConfig.PADDING_SMALL)
        self.power_off_all_btn.grid(row=1, column=3, padx=AppConfig.PADDING_MEDIUM, pady=AppConfig.PADDING_SMALL)
        
        # Область для фреймов проекторов
        self.canvas = ctk.CTkFrame(
            self.root,
            fg_color=Theme.CANVAS_BG
        )
        self.canvas.pack(side='top', fill='both', expand=True, padx=AppConfig.PADDING_MEDIUM, pady=AppConfig.PADDING_MEDIUM)
    
    def _setup_osc_callbacks(self):
        """Настроить обработчики OSC событий"""
        self.osc_controller.on_shutter_open = self._handle_osc_shutter_open
        self.osc_controller.on_shutter_close = self._handle_osc_shutter_close
        self.osc_controller.on_group_open = self._on_open_group
        self.osc_controller.on_group_close = self._on_close_group
    
    # Обработчики OSC событий
    
    def _handle_osc_shutter_open(self, room_number: str):
        """Обработать OSC команду открытия шаттера"""
        projector = self.controller.get_projector_by_ip_room_number(room_number)
        if projector:
            # Найти соответствующий UI фрейм
            for frame in self.projector_frames:
                if frame.projector == projector:
                    self._create_task(
                        frame.execute_shutter_action(open_shutter=True),
                        f"execute shutter open for {projector.label}"
                    )
                    break
    
    def _handle_osc_shutter_close(self, room_number: str):
        """Обработать OSC команду закрытия шаттера"""
        projector = self.controller.get_projector_by_ip_room_number(room_number)
        if projector:
            # Найти соответствующий UI фрейм
            for frame in self.projector_frames:
                if frame.projector == projector:
                    self._create_task(
                        frame.execute_shutter_action(open_shutter=False),
                        f"execute shutter close for {projector.label}"
                    )
                    break
    
    # Обработчики событий UI
    
    def _execute_group_action(self, action_name: str, controller_method):
        """Выполнить групповую операцию на выбранных проекторах"""
        group_indices = [
            i for i, frame in enumerate(self.projector_frames)
            if frame.grp.get()
        ]
        logger.info(f"{action_name} for {len(group_indices)} projectors")
        self._create_task(
            controller_method(group_indices),
            action_name
        )
        # Обновить UI фреймов
        for idx in group_indices:
            if idx < len(self.projector_frames):
                self.projector_frames[idx].update_screen_status()
    
    def _on_open_group(self):
        """Открыть шаттеры группы"""
        self._execute_group_action(
            "Opening group shutters",
            self.controller.open_group_shutters
        )
    
    def _on_close_group(self):
        """Закрыть шаттеры группы"""
        self._execute_group_action(
            "Closing group shutters",
            self.controller.close_group_shutters
        )
    
    def _on_update(self):
        """Обновить все проекторы"""
        async def update_all():
            logger.info("Updating all projectors")
            await self.controller.update_all()
            # Обновить UI
            for frame in self.projector_frames:
                frame.update_screen_status()
                frame.update_power_status()
        
        self._create_task(update_all(), "update all projectors")
    
    def _execute_power_action(self, action_name: str, controller_method):
        """Выполнить операцию питания на всех проекторах"""
        async def power_action():
            logger.info(action_name)
            await controller_method()
            # Обновить UI
            for frame in self.projector_frames:
                frame.update_power_status()
        
        self._create_task(power_action(), action_name)
    
    def _on_power_on_all(self):
        """Включить все проекторы"""
        self._execute_power_action(
            "Powering on all projectors",
            self.controller.power_on_all
        )
    
    def _on_power_off_all(self):
        """Выключить все проекторы"""
        self._execute_power_action(
            "Powering off all projectors",
            self.controller.power_off_all
        )
    
    def _on_add_projector(self):
        """Открыть диалог добавления проектора"""
        AddProjectorDialog(self.root, self._add_projector)
    
    def _add_projector(self, projector: Projector):
        """Добавить новый проектор"""
        # Добавить в контроллер
        if not self.controller.add_projector(projector):
            logger.warning(f"Projector {projector.ip} already exists")
            return
        
        logger.info(f"Adding projector {projector.label} ({projector.ip})")
        
        # Создать UI фрейм
        frame = ProjectorFrame(
            projector,
            self.canvas,
            self._remove_frame,
            lambda: None  # on_update callback
        )
        
        # Позиционировать фрейм
        x_offset = AppConfig.PROJECTOR_OFFSET_X + (len(self.projector_frames) % 2) * AppConfig.PROJECTOR_SPACING_X
        y_offset = AppConfig.PROJECTOR_OFFSET_Y + (len(self.projector_frames) // 2) * AppConfig.PROJECTOR_SPACING_Y
        frame.set_position(x_offset, y_offset)
        
        self.projector_frames.append(frame)
    
    def _remove_frame(self, frame: ProjectorFrame):
        """Удалить фрейм проектора"""
        if frame in self.projector_frames:
            logger.info(f"Removing projector {frame.projector.label}")
            self.projector_frames.remove(frame)
            self.controller.remove_projector(frame.projector)
    
    def _on_load(self):
        """Загрузить проекторы из файла"""
        self._create_task(self._async_load(), "load projectors from file")
    
    async def _async_load(self):
        """Асинхронная загрузка из файла"""
        file_path = filedialog.askopenfilename(
            title="Select Projectors File",
            filetypes=(("Text Files", "*.txt"), ("All Files", "*.*"))
        )
        
        if not file_path:
            return
        
        logger.info(f"Loading projectors from {file_path}")
        
        # Очистить текущие проекторы
        for frame in self.projector_frames:
            frame.frame.destroy()
        self.projector_frames.clear()
        self.controller.clear()
        
        # Загрузить из файла
        window_size, projectors_data = await self.file_manager.load_from_file(
            file_path
        )
        
        # Установить размер окна
        if window_size:
            width, height = window_size
            self.root.geometry(f"{width}x{height}")
            logger.info(f"Set window size to {width}x{height}")
        
        # Добавить проекторы
        for projector, x, y in projectors_data:
            self.controller.add_projector(projector)
            
            frame = ProjectorFrame(
                projector,
                self.canvas,
                self._remove_frame,
                lambda: None
            )
            frame.set_position(x, y)
            self.projector_frames.append(frame)
        
        logger.info(f"Loaded {len(projectors_data)} projectors")
    
    def _on_save(self):
        """Сохранить проекторы в файл"""
        file_path = filedialog.asksaveasfilename(
            title="Save Projectors File",
            defaultextension=".txt",
            filetypes=(("Text Files", "*.txt"), ("All Files", "*.*"))
        )
        
        if not file_path:
            return
        
        logger.info(f"Saving projectors to {file_path}")
        
        # Собрать данные
        window_size = (self.root.winfo_width(), self.root.winfo_height())
        projectors_data = [
            (frame.projector, *frame.get_position())
            for frame in self.projector_frames
        ]
        
        # Сохранить
        self.file_manager.save_to_file(file_path, window_size, projectors_data)
        logger.info(f"Saved {len(projectors_data)} projectors")
    
    def _on_close(self):
        """Обработать закрытие окна"""
        logger.info("Closing application...")
        self.osc_controller.stop()
        for task in list(self._tasks):
            task.cancel()
        self.root.destroy()
    
    # Главный цикл приложения
    
    async def run(self):
        """Запустить приложение"""
        # Запустить OSC сервер
        logger.info("Starting OSC server...")
        await self.osc_controller.start()
        
        # Главный цикл Tkinter
        try:
            while True:
                if not self.root.winfo_exists():
                    break
                self.root.update()
                await asyncio.sleep(0.01)
        finally:
            if self._tasks:
                pending = list(self._tasks)
                for task in pending:
                    task.cancel()
                await asyncio.gather(*pending, return_exceptions=True)
                self._tasks.difference_update(pending)
            self.osc_controller.stop()
            logger.info("Application stopped")


def main():
    """Точка входа в приложение"""
    logger.info("=== Starting 3P Shutter Control ===")
    app = MainApplication()
    asyncio.run(app.run())


if __name__ == "__main__":
    main()

"""
Диалог настроек проектора для управления объективом.
Переработанная версия с табами и улучшенным интерфейсом.
"""
import asyncio
import customtkinter as ctk
from typing import Any, Coroutine, Optional, Set
from core.constants import ProjectorStates
from infra.settings_repository import (
    load_projector_settings,
    save_projector_settings,
)
from lib.projector import Projector
from theme import Theme, AppConfig
from ui.widget_factory import WidgetFactory
from ui.lens_cross import FocusControls, LensShiftCross, ZoomControls
from utils.logger import setup_logger
from utils.async_helpers import handle_async_errors

logger = setup_logger(__name__)


class ProjectorSettingsDialog(ctk.CTkToplevel):
    """Диалог настроек проектора с управлением объективом"""
    
    def __init__(self, parent, projector: Projector):
        super().__init__(parent)

        self.projector = projector
        self.h_position = ctk.StringVar(value="---")
        self.v_position = ctk.StringVar(value="---")
        self.aspect_ratio = ctk.StringVar(value="16:9")
        self.test_pattern = ctk.StringVar(value="Off")
        self.installation_mode = ctk.StringVar(value="Front/Desk")

        self._dialog_tasks: Set[asyncio.Task] = set()
        self._closing = False

        self._setup_window()
        self._create_widgets()

        # Загрузить текущие настройки при открытии
        self._run(self._load_positions())
        self._run(self._load_aspect_ratio())
        self._run(self._load_test_pattern())
        self._run(self._load_installation_mode())

    def _run(self, coro: Coroutine[Any, Any, Any]) -> asyncio.Task:
        """
        Запустить async-задачу диалога. Все такие задачи отменяются при
        закрытии окна, чтобы не было обращений к уничтоженным виджетам.
        """
        task = asyncio.create_task(coro)
        self._dialog_tasks.add(task)
        task.add_done_callback(self._dialog_tasks.discard)
        return task
    
    def _setup_window(self):
        """Настроить окно диалога"""
        self.title(f"Settings: {self.projector.label}")
        self.geometry("900x680")
        self.resizable(True, True)
        self.minsize(900, 680)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Сделать окно модальным
        try:
            self.transient(self.master)  # type: ignore
        except Exception:
            pass
        self.grab_set()

        # Центрировать окно
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (800 // 2)
        y = (self.winfo_screenheight() // 2) - (580 // 2)
        self.geometry(f"800x580+{x}+{y}")

        # Настроить сетку для растяжения
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

    def _on_close(self) -> None:
        """Отменить in-flight задачи и закрыть диалог."""
        if self._closing:
            return
        self._closing = True
        for task in list(self._dialog_tasks):
            if not task.done():
                task.cancel()
        self.destroy()
    
    def _create_widgets(self):
        """Создать виджеты диалога с табами"""
        # Верхний фрейм с заголовком
        self.header_frame = ctk.CTkFrame(self, fg_color=Theme.BACKGROUND)
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 2))
        self.header_frame.grid_columnconfigure(0, weight=1)
        
        # Заголовок
        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text=f"{self.projector.label}",
            font=Theme.FONT_TITLE,
            text_color=Theme.TEXT_PRIMARY
        )
        self.title_label.grid(row=0, column=0, padx=5, pady=2)
        
        # Создаем вкладки
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=10, pady=(5, 5))
        
        # Добавляем вкладки
        self.tab_lens = self.tabview.add("🔍 Lens")
        self.tab_display = self.tabview.add("🖼️ Display")
        self.tab_info = self.tabview.add("ℹ️ Info")
        
        # Создаем виджеты для каждой вкладки
        self._create_lens_controls()
        self._create_display_controls()
        self._create_info_controls()
        
        # Нижний фрейм с кнопкой закрытия
        self.bottom_frame = ctk.CTkFrame(self, fg_color=Theme.BACKGROUND)
        self.bottom_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(5, 10))
        
        self.close_btn = WidgetFactory.create_action_button(
            self.bottom_frame,
            text="Close",
            command=self._on_close,
            button_type='dark',
            width=150
        )
        self.close_btn.pack(pady=2)
    
    def _create_section_frame(self, parent, title: str):
        """Вспомогательный метод для создания секции с заголовком"""
        frame = ctk.CTkFrame(parent, fg_color=Theme.BACKGROUND, 
                            border_width=1, border_color=Theme.PRIMARY)
        frame.pack(fill="x", padx=10, pady=10)
        
        title_label = ctk.CTkLabel(
            frame,
            text=title,
            font=Theme.FONT_NORMAL,
            text_color=Theme.PRIMARY
        )
        title_label.pack(pady=(8, 5), padx=8)
        
        return frame
    
    def _create_lens_controls(self):
        """Создать управления объективом во вкладке Lens"""
        # Используем прокручиваемый фрейм
        self.lens_scrollable_frame = ctk.CTkScrollableFrame(
            self.tab_lens,
            fg_color="transparent"
        )
        self.lens_scrollable_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # === LENS CONTROL (Shift, Focus, Zoom) ===
        lens_control_section = self._create_section_frame(
            self.lens_scrollable_frame, "🎮 Lens Control"
        )
        
        # Главный контейнер - горизонтальный layout
        main_container = ctk.CTkFrame(lens_control_section, fg_color="transparent")
        main_container.pack(pady=5, padx=8)

        shift_cross = LensShiftCross(
            main_container,
            on_shift_h_plus=self._on_shift_h_plus,
            on_shift_h_minus=self._on_shift_h_minus,
            on_shift_v_plus=self._on_shift_v_plus,
            on_shift_v_minus=self._on_shift_v_minus,
            on_lens_home=self._on_lens_home,
        )
        shift_cross.grid(row=0, column=0, padx=10, sticky="n")

        right_side_container = ctk.CTkFrame(main_container, fg_color="transparent")
        right_side_container.grid(row=0, column=1, padx=10, sticky="n")

        focus_controls = FocusControls(
            right_side_container,
            on_minus=self._on_focus_minus,
            on_plus=self._on_focus_plus,
        )
        focus_controls.pack(pady=(0, 10))

        zoom_controls = ZoomControls(
            right_side_container,
            on_minus=self._on_zoom_minus,
            on_plus=self._on_zoom_plus,
        )
        zoom_controls.pack()
        
        # === SETTINGS ACTIONS ===
        settings_actions_section = self._create_section_frame(
            self.lens_scrollable_frame, "💾 Settings Management"
        )
        
        actions_frame = ctk.CTkFrame(settings_actions_section, fg_color="transparent")
        actions_frame.pack(pady=10, padx=8)
        
        # Кнопка сохранения
        self.save_settings_btn = WidgetFactory.create_action_button(
            actions_frame,
            text="💾 Save Settings",
            command=self._on_save_settings,
            button_type='success',
            width=180
        )
        self.save_settings_btn.grid(row=0, column=0, padx=5, pady=5)
        
        # Кнопка загрузки
        self.load_settings_btn = WidgetFactory.create_action_button(
            actions_frame,
            text="📂 Load & Apply Settings",
            command=self._on_load_settings,
            button_type='warning',
            width=180
        )
        self.load_settings_btn.grid(row=0, column=1, padx=5, pady=5)
        
        # Информационное сообщение
        info_label = ctk.CTkLabel(
            settings_actions_section,
            text="💡 Load will reset lens to Home position and apply saved settings",
            font=Theme.FONT_NORMAL,
            text_color=Theme.TEXT_SECONDARY
        )
        info_label.pack(pady=(0, 8), padx=8)
    
    def _create_display_controls(self):
        """Создать управления дисплеем во вкладке Display"""
        scrollable_frame = ctk.CTkScrollableFrame(
            self.tab_display,
            fg_color="transparent"
        )
        scrollable_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # === ASPECT RATIO ===
        aspect_section = self._create_section_frame(
            scrollable_frame, "📐 Screen Aspect Ratio"
        )
        
        self.aspect_selector = ctk.CTkSegmentedButton(
            aspect_section,
            values=["16:10", "16:9", "4:3"],
            command=self._on_aspect_ratio_changed,
            variable=self.aspect_ratio
        )
        self.aspect_selector.set("16:9")
        self.aspect_selector.pack(pady=10, padx=8)
        
        # === INSTALLATION MODE ===
        installation_section = self._create_section_frame(
            scrollable_frame, "📽️ Projection Method & Installation"
        )
        
        installation_modes = list(ProjectorStates.INSTALLATION_MODES.keys())
        
        self.installation_selector = ctk.CTkSegmentedButton(
            installation_section,
            values=installation_modes,
            command=self._on_installation_mode_changed,
            variable=self.installation_mode
        )
        self.installation_selector.set("Front/Desk")
        self.installation_selector.pack(pady=10, padx=8)
        
        # === TEST PATTERN ===
        pattern_section = self._create_section_frame(
            scrollable_frame, "🎨 Test Pattern"
        )
        
        pattern_names = list(ProjectorStates.TEST_PATTERNS.keys())
        
        pattern_label = ctk.CTkLabel(
            pattern_section,
            text="Select Pattern:",
            font=Theme.FONT_NORMAL
        )
        pattern_label.pack(pady=(5, 8), padx=8)
        
        self.test_pattern_dropdown = WidgetFactory.create_combobox(
            pattern_section,
            values=pattern_names,
            command=self._on_test_pattern_changed,
            initial_value="Off",
            width=200
        )
        self.test_pattern_dropdown.pack(pady=(0, 10), padx=8)
    
    def _create_info_controls(self):
        """Создать информационную вкладку"""
        scrollable_frame = ctk.CTkScrollableFrame(
            self.tab_info,
            fg_color="transparent"
        )
        scrollable_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # === LENS POSITION ===
        position_section = self._create_section_frame(
            scrollable_frame, "📍 Lens Position"
        )
        
        pos_info_frame = ctk.CTkFrame(position_section, fg_color="transparent")
        pos_info_frame.pack(fill="x", pady=10, padx=8)
        
        # Horizontal position
        h_label = ctk.CTkLabel(
            pos_info_frame,
            text="Horizontal (H):",
            font=Theme.FONT_NORMAL
        )
        h_label.grid(row=0, column=0, sticky="w", pady=5, padx=5)
        
        self.h_position_label = ctk.CTkLabel(
            pos_info_frame,
            textvariable=self.h_position,
            font=Theme.FONT_NORMAL,
            text_color=Theme.PRIMARY
        )
        self.h_position_label.grid(row=0, column=1, sticky="w", pady=5, padx=5)
        
        # Vertical position
        v_label = ctk.CTkLabel(
            pos_info_frame,
            text="Vertical (V):",
            font=Theme.FONT_NORMAL
        )
        v_label.grid(row=1, column=0, sticky="w", pady=5, padx=5)
        
        self.v_position_label = ctk.CTkLabel(
            pos_info_frame,
            textvariable=self.v_position,
            font=Theme.FONT_NORMAL,
            text_color=Theme.PRIMARY
        )
        self.v_position_label.grid(row=1, column=1, sticky="w", pady=5, padx=5)
        
        pos_info_frame.grid_columnconfigure(1, weight=1)
        
        # Refresh button
        self.refresh_position_btn = WidgetFactory.create_action_button(
            position_section,
            text="🔄 Refresh Position",
            command=self._on_refresh_position,
            button_type='warning',
            width=150
        )
        self.refresh_position_btn.pack(pady=10)
        
        # === PROJECTOR INFO ===
        info_section = self._create_section_frame(
            scrollable_frame, "ℹ️ Projector Info"
        )
        
        info_frame = ctk.CTkFrame(info_section, fg_color="transparent")
        info_frame.pack(fill="x", pady=10, padx=8)
        
        # Info labels
        info_items = [
            ("Label:", self.projector.label),
            ("IP Address:", self.projector.ip),
            ("Port:", str(self.projector.port)),
            ("Room Number:", self.projector.ip_room_number),
        ]
        
        for idx, (key, value) in enumerate(info_items):
            label = ctk.CTkLabel(info_frame, text=key, font=Theme.FONT_NORMAL)
            label.grid(row=idx, column=0, sticky="w", pady=3, padx=5)
            
            value_label = ctk.CTkLabel(
                info_frame,
                text=str(value),
                font=Theme.FONT_NORMAL,
                text_color=Theme.PRIMARY
            )
            value_label.grid(row=idx, column=1, sticky="w", pady=3, padx=5)
        
        info_frame.grid_columnconfigure(1, weight=1)
    
    # === EVENT HANDLERS ===
    
    def _on_lens_home(self):
        """Обработчик возврата объектива в Home позицию"""
        self._run(self._execute_lens_command(
            self.projector.lens_home(),
            "Lens Home"
        ))
    
    # === SHIFT HANDLERS ===
    def _on_shift_h_plus(self, speed: str):
        """Обработчик сдвига объектива вправо"""
        self._run(self._execute_lens_command(
            self.projector.lens_shift_h('plus', speed),
            f"Shift Right ({speed})"
        ))
    
    def _on_shift_h_minus(self, speed: str):
        """Обработчик сдвига объектива влево"""
        self._run(self._execute_lens_command(
            self.projector.lens_shift_h('minus', speed),
            f"Shift Left ({speed})"
        ))
    
    def _on_shift_v_plus(self, speed: str):
        """Обработчик сдвига объектива вверх"""
        self._run(self._execute_lens_command(
            self.projector.lens_shift_v('plus', speed),
            f"Shift Up ({speed})"
        ))
    
    def _on_shift_v_minus(self, speed: str):
        """Обработчик сдвига объектива вниз"""
        self._run(self._execute_lens_command(
            self.projector.lens_shift_v('minus', speed),
            f"Shift Down ({speed})"
        ))
    
    # === FOCUS HANDLERS ===
    def _on_focus_plus(self, speed: str):
        """Обработчик фокусировки дальше"""
        self._run(self._execute_lens_command(
            self.projector.lens_focus('plus', speed),
            f"Focus Far ({speed})"
        ))
    
    def _on_focus_minus(self, speed: str):
        """Обработчик фокусировки ближе"""
        self._run(self._execute_lens_command(
            self.projector.lens_focus('minus', speed),
            f"Focus Near ({speed})"
        ))
    
    # === ZOOM HANDLERS ===
    def _on_zoom_plus(self, speed: str):
        """Обработчик увеличения зума"""
        self._run(self._execute_lens_command(
            self.projector.lens_zoom('plus', speed),
            f"Zoom In ({speed})"
        ))
    
    def _on_zoom_minus(self, speed: str):
        """Обработчик уменьшения зума"""
        self._run(self._execute_lens_command(
            self.projector.lens_zoom('minus', speed),
            f"Zoom Out ({speed})"
        ))
    
    def _on_refresh_position(self):
        """Обработчик обновления позиции"""
        self._run(self._load_positions())
    
    def _on_aspect_ratio_changed(self, value: str):
        """Обработчик изменения соотношения сторон"""
        logger.info(f"Changing aspect ratio to {value} for {self.projector.label}")
        self._run(self._set_aspect_ratio(value))
    
    @handle_async_errors("setting aspect ratio")
    async def _set_aspect_ratio(self, ratio: str):
        """Установить соотношение сторон"""
        await self.projector.set_aspect_ratio(ratio)
        logger.info(f"Aspect ratio changed to {ratio}")
    
    def _on_test_pattern_changed(self, value: str = None):  # type: ignore
        """Обработчик изменения тестового паттерна"""
        pattern = value or self.test_pattern_dropdown.get()
        logger.info(f"Changing test pattern to {pattern} for {self.projector.label}")
        self._run(self._set_test_pattern(pattern))
    
    @handle_async_errors("setting test pattern")
    async def _set_test_pattern(self, pattern: str):
        """Установить тестовый паттерн"""
        await self.projector.set_test_pattern(pattern)
        logger.info(f"Test pattern changed to {pattern}")
    
    @handle_async_errors("lens command")
    async def _execute_lens_command(self, command_coro, action_name: str):
        """Выполнить команду управления объективом"""
        logger.info(f"Executing {action_name} for {self.projector.label}")
        await command_coro
        # Обновить позиции после выполнения команды
        await self._load_positions()
    
    @handle_async_errors("loading lens positions")
    async def _load_positions(self):
        """Загрузить текущие позиции объектива"""
        h_pos, v_pos = await self.projector.get_lens_position()
        self.h_position.set(h_pos if h_pos else "---")
        self.v_position.set(v_pos if v_pos else "---")
        logger.debug(f"Loaded positions H:{h_pos}, V:{v_pos}")
    
    @handle_async_errors("loading aspect ratio")
    async def _load_aspect_ratio(self):
        """Загрузить текущее соотношение сторон"""
        result = await self.projector.get_aspect_ratio()
        ratio = ProjectorStates.ASPECT_RATIO_BY_CODE.get(result)
        if ratio is None:
            logger.warning(f"Unknown aspect ratio response: {result}")
            return
        self.aspect_ratio.set(ratio)
        self.aspect_selector.set(ratio)
        logger.debug(f"Loaded aspect ratio: {ratio}")
    
    @handle_async_errors("loading test pattern")
    async def _load_test_pattern(self):
        """Загрузить текущий тестовый паттерн"""
        result = await self.projector.get_test_pattern()
        # Парсим результат: ожидаем код паттерна (00-78)
        # Ищем соответствующее имя
        for name, code in ProjectorStates.TEST_PATTERNS.items():
            if result == code:
                self.test_pattern.set(name)
                self.test_pattern_dropdown.set(name)
                logger.debug(f"Loaded test pattern: {name}")
                return
        logger.warning(f"Unknown test pattern response: {result}")
    
    def _on_installation_mode_changed(self, value: str):
        """Обработчик изменения режима установки"""
        logger.info(f"Changing installation mode to {value} for {self.projector.label}")
        self._run(self._set_installation_mode(value))
    
    @handle_async_errors("setting installation mode")
    async def _set_installation_mode(self, mode: str):
        """Установить режим установки"""
        await self.projector.set_installation_mode(mode)
        logger.info(f"Installation mode changed to {mode}")
    
    @handle_async_errors("loading installation mode")
    async def _load_installation_mode(self):
        """Загрузить текущий режим установки"""
        result = await self.projector.get_installation_mode()
        # Парсим результат: ожидаем '0'-'5'
        # Ищем соответствующее имя
        for name, code in ProjectorStates.INSTALLATION_MODES.items():
            if result == code:
                self.installation_mode.set(name)
                self.installation_selector.set(name)
                logger.debug(f"Loaded installation mode: {name}")
                return
        logger.warning(f"Unknown installation mode response: {result}")
    
    def _on_save_settings(self):
        """Обработчик сохранения настроек"""
        logger.info(f"Saving settings for {self.projector.label}")
        self._run(self._save_settings())
    
    @handle_async_errors("saving settings")
    async def _save_settings(self):
        """Сохранить текущие настройки проектора"""
        success = save_projector_settings(
            projector_ip=self.projector.ip,
            h_position=self.h_position.get(),
            v_position=self.v_position.get(),
            aspect_ratio=self.aspect_ratio.get(),
            installation_mode=self.installation_mode.get(),
        )

        if success:
            logger.info(f"Settings saved successfully for {self.projector.label}")
        else:
            logger.error(f"Failed to save settings for {self.projector.label}")
    
    def _on_load_settings(self):
        """Обработчик загрузки и применения настроек"""
        logger.info(f"Loading and applying settings for {self.projector.label}")
        self._run(self._load_and_apply_settings())
    
    @handle_async_errors("loading and applying settings")
    async def _load_and_apply_settings(self):
        """Загрузить и применить сохраненные настройки"""
        settings = load_projector_settings(self.projector.ip)

        if settings is None:
            logger.warning(f"No saved settings found for {self.projector.label}")
            return

        await self.projector.apply_saved_settings(settings)

        # Обновляем UI после применения
        await self._load_positions()
        await self._load_aspect_ratio()
        await self._load_installation_mode()

        logger.info(f"Settings loaded and applied successfully for {self.projector.label}")

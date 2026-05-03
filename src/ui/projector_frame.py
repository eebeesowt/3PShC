"""
UI компонент для отображения одного проектора.
Использует CustomTkinter для современного вида.
"""
import asyncio
import customtkinter as ctk
from typing import Callable, Optional
from lib.projector import Projector
from theme import Theme, AppConfig
from ui.widget_factory import WidgetFactory
from ui.projector_settings_dialog import ProjectorSettingsDialog
from utils.logger import setup_logger
from utils.async_helpers import handle_async_errors, run_async

logger = setup_logger(__name__)


class ProjectorFrame:
    """UI фрейм для одного проектора"""
    
    def __init__(
        self,
        projector: Projector,
        parent,
        on_remove: Callable,
        on_update: Callable
    ) -> None:
        self.projector = projector
        self.grp = ctk.BooleanVar(value=False)
        self.on_remove = on_remove
        self.on_update = on_update
        
        self._drag_data = {"x": 0, "y": 0}
        
        self._create_widgets(parent)
        self._layout_widgets()
        self._setup_bindings()
    
    def _create_widgets(self, parent):
        """Создать UI элементы"""
        # Основной фрейм
        self.frame = ctk.CTkFrame(
            parent,
            border_width=1,
            fg_color=Theme.BACKGROUND
        )
        
        # Метка с названием
        self.label = ctk.CTkLabel(
            self.frame,
            text=self.projector.label,
            font=Theme.FONT_TITLE,
            text_color=Theme.TEXT_PRIMARY
        )
        
        # Кнопки управления шаттером
        self.shutter_on_btn = WidgetFactory.create_action_button(
            self.frame,
            text='Open',
            command=self._on_shutter_open,
            button_type='primary',
            width=AppConfig.BUTTON_WIDTH_MEDIUM
        )
        
        self.shutter_off_btn = WidgetFactory.create_action_button(
            self.frame,
            text='Close',
            command=self._on_shutter_close,
            button_type='danger',
            width=AppConfig.BUTTON_WIDTH_MEDIUM
        )
        
        # Чекбокс группы
        self.group = ctk.CTkCheckBox(
            self.frame,
            text="Grp",
            variable=self.grp,
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER
        )
        
        # Кнопка настроек
        self.settings_btn = WidgetFactory.create_action_button(
            self.frame,
            text='⚙',
            command=self._on_settings,
            button_type='info',
            width=AppConfig.BUTTON_WIDTH_SMALL,
            height=AppConfig.BUTTON_HEIGHT_SMALL
        )
        
        # Кнопка удаления
        self.close_btn = WidgetFactory.create_action_button(
            self.frame,
            text='×',
            command=self._on_close,
            button_type='danger_dark',
            width=AppConfig.BUTTON_WIDTH_SMALL,
            height=AppConfig.BUTTON_HEIGHT_SMALL
        )
        
        # Индикатор питания
        self.power_status = ctk.CTkLabel(
            self.frame,
            text="●",
            font=Theme.FONT_STATUS,
            text_color=self._get_power_color()
        )
        
        # Индикатор статуса шаттера
        self.screen_status = WidgetFactory.create_status_label(
            self.frame,
            text=self._get_shutter_text(),
            fg_color=self._get_shutter_color()
        )
        
        # Выпадающие списки для времени шаттера
        self.shutter_in_menu = self._create_shutter_time_menu(
            self.projector.shutter_in_time,
            self._on_set_shutter_in
        )
        
        self.shutter_out_menu = self._create_shutter_time_menu(
            self.projector.shutter_out_time,
            self._on_set_shutter_out
        )
    
    def _create_shutter_time_menu(
        self,
        initial_value: Optional[str],
        command: Callable
    ) -> Optional[ctk.CTkComboBox]:
        """Создать выпадающий список для времени шаттера"""
        if initial_value is None:
            return None
        
        return WidgetFactory.create_combobox(
            self.frame,
            values=[str(v) for v in self.projector.shutter_time_dict],
            command=command,
            initial_value=str(initial_value)
        )
    
    def _layout_widgets(self):
        """Разместить виджеты в сетке - компактный квадратный формат"""
        # Строка 0: Индикатор питания, название, кнопки управления
        self.power_status.grid(row=0, column=0, pady=2, padx=2)
        self.label.grid(row=0, column=1, pady=2, padx=2, sticky="w", columnspan=2)
        self.settings_btn.grid(row=0, column=3, pady=2, padx=2)
        self.close_btn.grid(row=0, column=4, pady=2, padx=2)
        
        # Строка 1: Кнопки Open/Close и статус
        self.shutter_on_btn.grid(row=1, column=0, pady=2, padx=2, columnspan=2)
        self.shutter_off_btn.grid(row=1, column=2, pady=2, padx=2, columnspan=2)
        self.screen_status.grid(row=1, column=4, pady=2, padx=2)
        
        # Строка 2: Выпадающие списки времени и чекбокс группы
        if self.shutter_in_menu:
            self.shutter_in_menu.grid(row=2, column=0, pady=2, padx=2, columnspan=2)
        
        if self.shutter_out_menu:
            self.shutter_out_menu.grid(row=2, column=2, pady=2, padx=2, columnspan=2)
        
        self.group.grid(row=2, column=4, pady=2, padx=2)
    
    def _setup_bindings(self):
        """Настроить события перетаскивания"""
        self.frame.bind("<Button-1>", self._start_drag)
        self.frame.bind("<B1-Motion>", self._do_drag)
    
    # Вспомогательные методы для получения состояния
    
    def _get_power_color(self) -> str:
        """Получить цвет индикатора питания"""
        if self.projector.power is None:
            return Theme.POWER_UNKNOWN_COLOR
        return Theme.POWER_ON_COLOR if self.projector.power else Theme.POWER_OFF_COLOR
    
    def _get_shutter_text(self) -> str:
        """Получить текст статуса шаттера"""
        if self.projector.shutter is None:
            return 'Unknown'
        return 'Closed' if self.projector.shutter else 'Open'
    
    def _get_shutter_color(self) -> str:
        """Получить цвет индикатора шаттера"""
        if self.projector.shutter is None:
            return Theme.SHUTTER_UNKNOWN_COLOR
        return Theme.SHUTTER_CLOSED_COLOR if self.projector.shutter else Theme.SHUTTER_OPEN_COLOR
    
    # Обработчики событий
    
    def _on_shutter_open(self):
        """Обработчик открытия шаттера"""
        run_async(self.execute_shutter_action(True))
    
    def _on_shutter_close(self):
        """Обработчик закрытия шаттера"""
        run_async(self.execute_shutter_action(False))
    
    @handle_async_errors("shutter operation", lambda self: self._show_error_status())
    async def execute_shutter_action(self, open_shutter: bool):
        """
        Универсальный метод для управления шаттером.
        
        Args:
            open_shutter: True для открытия, False для закрытия
        """
        if open_shutter:
            await self.projector.shutter_open()
        else:
            await self.projector.shutter_close()
        self.update_screen_status()
    
    def _show_error_status(self):
        """Показать ошибку на индикаторе"""
        self.screen_status.configure(
            fg_color=Theme.STATUS_ERROR,
            text_color=Theme.TEXT_PRIMARY,
            text='Error'
        )
    
    def _on_set_shutter_in(self, selected_time: str = None):  # type: ignore
        """Обработчик установки времени открытия шаттера"""
        if self.shutter_in_menu:
            time_value = selected_time or self.shutter_in_menu.get()
            logger.info(f"Setting shutter in time to {time_value} for {self.projector.label}")
            run_async(self.projector.set_shutter_in(time_value))
    
    def _on_set_shutter_out(self, selected_time: str = None):  # type: ignore
        """Обработчик установки времени закрытия шаттера"""
        if self.shutter_out_menu:
            time_value = selected_time or self.shutter_out_menu.get()
            logger.info(f"Setting shutter out time to {time_value} for {self.projector.label}")
            run_async(self.projector.set_shutter_out(time_value))
    
    def _on_settings(self):
        """Обработчик открытия настроек проектора"""
        logger.info(f"Opening settings for {self.projector.label}")
        # Открыть диалог настроек
        settings_dialog = ProjectorSettingsDialog(self.frame, self.projector)
        settings_dialog.focus()
    
    def _on_close(self):
        """Обработчик удаления фрейма"""
        self.frame.destroy()
        self.on_remove(self)
    
    def _start_drag(self, event):
        """Начать перетаскивание"""
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y
    
    def _do_drag(self, event):
        """Выполнить перетаскивание"""
        x = self.frame.winfo_x() - self._drag_data["x"] + event.x
        y = self.frame.winfo_y() - self._drag_data["y"] + event.y
        self.frame.place(x=x, y=y)
    
    # Публичные методы для обновления UI
    
    def update_power_status(self):
        """Обновить индикатор питания"""
        self.power_status.configure(text_color=self._get_power_color())
    
    def update_screen_status(self):
        """Обновить индикатор шаттера"""
        self.screen_status.configure(
            fg_color=self._get_shutter_color(),
            text=self._get_shutter_text()
        )
    
    @handle_async_errors("updating projector")
    async def update(self):
        """Обновить информацию о проекторе"""
        await self.projector.get_info()
        self.update_screen_status()
        self.update_power_status()
    
    @handle_async_errors("powering on projector", log_action=True)
    async def power_on(self):
        """Включить проектор"""
        await self.projector.power_on()
        self.update_power_status()
    
    @handle_async_errors("powering off projector", log_action=True)
    async def power_off(self):
        """Выключить проектор"""
        await self.projector.power_off()
        self.update_power_status()
    
    def get_position(self) -> tuple:
        """Получить позицию фрейма"""
        return (self.frame.winfo_x(), self.frame.winfo_y())
    
    def set_position(self, x: int, y: int):
        """Установить позицию фрейма"""
        self.frame.place(x=x, y=y)

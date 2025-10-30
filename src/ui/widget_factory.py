"""
Вспомогательные функции для создания UI виджетов.
"""
import customtkinter as ctk
from typing import Callable, Optional, List
from theme import Theme, AppConfig


class WidgetFactory:
    """Фабрика для создания стандартных виджетов"""
    
    @staticmethod
    def create_button(
        parent,
        text: str,
        command: Callable,
        fg_color: str,
        hover_color: str,
        width: Optional[int] = None,
        height: Optional[int] = None,
        **kwargs
    ) -> ctk.CTkButton:
        """Создать стандартную кнопку"""
        btn_kwargs = {
            'text': text,
            'command': command,
            'fg_color': fg_color,
            'hover_color': hover_color,
            'width': width or AppConfig.BUTTON_WIDTH_NORMAL,
            **kwargs
        }
        if height is not None:
            btn_kwargs['height'] = height
        return ctk.CTkButton(parent, **btn_kwargs)
    
    @staticmethod
    def create_action_button(
        parent,
        text: str,
        command: Callable,
        button_type: str = 'primary',
        width: Optional[int] = None,
        **kwargs
    ) -> ctk.CTkButton:
        """
        Создать кнопку действия с предустановленными цветами.
        
        Args:
            button_type: 'primary', 'danger', 'success', 'warning', 'info', 'dark'
        """
        color_map = {
            'primary': (Theme.PRIMARY, Theme.PRIMARY_HOVER),
            'danger': (Theme.DANGER, Theme.DANGER_HOVER),
            'danger_dark': (Theme.DANGER_DARK, Theme.DANGER_DARK_HOVER),
            'success': (Theme.SUCCESS, Theme.SUCCESS_HOVER),
            'success_dark': (Theme.SUCCESS_DARK, Theme.SUCCESS_DARK_HOVER),
            'warning': (Theme.WARNING, Theme.WARNING_HOVER),
            'info': (Theme.INFO, Theme.INFO_HOVER),
            'dark': (Theme.DARK, Theme.DARK_HOVER),
            'error': (Theme.ERROR_BG, Theme.ERROR_HOVER),
        }
        
        fg_color, hover_color = color_map.get(button_type, color_map['primary'])
        
        # Для warning кнопок текст черный
        text_color = Theme.TEXT_SECONDARY if button_type == 'warning' else None
        
        return WidgetFactory.create_button(
            parent, text, command, fg_color, hover_color, width,
            text_color=text_color, **kwargs
        )
    
    @staticmethod
    def create_combobox(
        parent,
        values: List[str],
        command: Callable,
        initial_value: Optional[str] = None,
        width: int = 70,
        **kwargs
    ) -> ctk.CTkComboBox:
        """Создать выпадающий список"""
        combobox = ctk.CTkComboBox(
            parent,
            values=values,
            state="readonly",
            width=width,
            command=command,
            **kwargs
        )
        if initial_value:
            combobox.set(initial_value)
        return combobox
    
    @staticmethod
    def create_status_label(
        parent,
        text: str,
        fg_color: str,
        corner_radius: int = 5,
        **kwargs
    ) -> ctk.CTkLabel:
        """Создать индикатор статуса"""
        return ctk.CTkLabel(
            parent,
            text=text,
            fg_color=fg_color,
            text_color=Theme.TEXT_PRIMARY,
            corner_radius=corner_radius,
            **kwargs
        )

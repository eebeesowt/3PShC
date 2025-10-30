"""
Диалоговое окно для добавления нового проектора.
Использует CustomTkinter.
"""
import asyncio
import customtkinter as ctk
from typing import Callable
from lib.projector import Projector
from theme import Theme
from utils.validator import Validator
from utils.logger import setup_logger

logger = setup_logger(__name__)


class AddProjectorDialog:
    """Диалог добавления проектора"""
    
    def __init__(self, parent, on_add: Callable[[Projector], None]):
        self.on_add = on_add
        
        # Создание окна
        self.window = ctk.CTkToplevel(parent)
        self.window.title("Add Projector")
        self.window.geometry("350x300")
        
        # Сообщение об ошибке
        self.error_label = None
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Создать виджеты"""
        # IP адрес
        ctk.CTkLabel(self.window, text="IP Address:").grid(
            row=0, column=0, padx=10, pady=5, sticky="w"
        )
        self.ip_entry = ctk.CTkEntry(self.window, width=200)
        self.ip_entry.grid(row=0, column=1, padx=10, pady=5)
        
        # Порт
        ctk.CTkLabel(self.window, text="Port:").grid(
            row=1, column=0, padx=10, pady=5, sticky="w"
        )
        self.port_entry = ctk.CTkEntry(self.window, width=200)
        self.port_entry.insert(0, "1024")  # Значение по умолчанию
        self.port_entry.grid(row=1, column=1, padx=10, pady=5)
        
        # Имя пользователя
        ctk.CTkLabel(self.window, text="Username:").grid(
            row=2, column=0, padx=10, pady=5, sticky="w"
        )
        self.username_entry = ctk.CTkEntry(self.window, width=200)
        self.username_entry.grid(row=2, column=1, padx=10, pady=5)
        
        # Пароль
        ctk.CTkLabel(self.window, text="Password:").grid(
            row=3, column=0, padx=10, pady=5, sticky="w"
        )
        self.password_entry = ctk.CTkEntry(self.window, width=200, show="*")
        self.password_entry.grid(row=3, column=1, padx=10, pady=5)
        
        # Метка
        ctk.CTkLabel(self.window, text="Label:").grid(
            row=4, column=0, padx=10, pady=5, sticky="w"
        )
        self.label_entry = ctk.CTkEntry(self.window, width=200)
        self.label_entry.grid(row=4, column=1, padx=10, pady=5)
        
        # Метка для ошибок
        self.error_label = ctk.CTkLabel(
            self.window,
            text="",
            text_color=Theme.DANGER_DARK,
            wraplength=300
        )
        self.error_label.grid(row=5, column=0, columnspan=2, pady=5)
        
        # Кнопка добавления
        self.add_button = ctk.CTkButton(
            self.window,
            text="Add Projector",
            command=self._on_add_click,
            fg_color=Theme.INFO,
            hover_color=Theme.INFO_HOVER,
            width=200
        )
        self.add_button.grid(row=6, column=0, columnspan=2, pady=10)
    
    def _show_error(self, message: str):
        """Показать сообщение об ошибке"""
        if self.error_label:
            self.error_label.configure(text=message)
            logger.warning(f"Validation error: {message}")
    
    def _clear_error(self):
        """Очистить сообщение об ошибке"""
        if self.error_label:
            self.error_label.configure(text="")
    
    def _on_add_click(self):
        """Обработчик нажатия кнопки Add"""
        asyncio.create_task(self._async_add())
    
    async def _async_add(self):
        """Асинхронное добавление проектора"""
        self._clear_error()
        
        ip = self.ip_entry.get().strip()
        port_str = self.port_entry.get().strip()
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        label = self.label_entry.get().strip()
        
        # Валидация IP
        is_valid, error_msg = Validator.validate_ip(ip)
        if not is_valid:
            self._show_error(error_msg or "Invalid IP")
            return
        
        # Валидация порта
        is_valid, error_msg, port = Validator.validate_port(port_str)
        if not is_valid:
            self._show_error(error_msg or "Invalid port")
            return
        
        # Валидация обязательных полей
        is_valid, error_msg = Validator.validate_required(username, "Username")
        if not is_valid:
            self._show_error(error_msg or "Username required")
            return
        
        is_valid, error_msg = Validator.validate_required(password, "Password")
        if not is_valid:
            self._show_error(error_msg or "Password required")
            return
        
        # Блокировка кнопки во время создания
        self.add_button.configure(state="disabled", text="Adding...")
        
        # Создание проектора
        try:
            logger.info(f"Creating new projector {ip}:{port}")
            new_projector = Projector(
                ip=ip,
                port=port,
                login=username,
                password=password,
                label=label if label else ip,
                id=0  # ID будет установлен контроллером
            )
            
            # Получить информацию о проекторе
            await new_projector.get_info()
            
            # Вызвать callback
            self.on_add(new_projector)
            
            logger.info(f"Successfully added projector {new_projector.label}")
            
            # Закрыть окно
            self.window.destroy()
            
        except Exception as e:
            logger.error(f"Error creating projector: {e}")
            self._show_error(f"Connection error: {str(e)}")
            self.add_button.configure(state="normal", text="Add Projector")

"""
Вспомогательные утилиты для работы с асинхронными операциями.
"""
import asyncio
from functools import wraps
from typing import Callable, Any, Optional
from utils.logger import setup_logger

logger = setup_logger(__name__)


def handle_async_errors(
    error_message: str,
    on_error: Optional[Callable] = None,
    log_action: bool = True
):
    """
    Декоратор для обработки ошибок в асинхронных методах.
    
    Args:
        error_message: Шаблон сообщения об ошибке (может содержать {})
        on_error: Callback функция, вызываемая при ошибке
        log_action: Логировать ли начало действия
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(self, *args, **kwargs) -> Any:
            action_name = func.__name__.replace('_async_', '').replace('_', ' ')
            
            try:
                if log_action and hasattr(self, 'projector'):
                    logger.info(f"{action_name.capitalize()} for {self.projector.label}")
                
                result = await func(self, *args, **kwargs)
                return result
                
            except asyncio.TimeoutError:
                if hasattr(self, 'projector'):
                    logger.error(f"Timeout while {action_name} for {self.projector.label}")
                else:
                    logger.error(f"Timeout while {action_name}")
                
                if on_error:
                    on_error(self)
                    
            except Exception as e:
                if hasattr(self, 'projector'):
                    logger.error(f"Error {action_name} for {self.projector.label}: {e}")
                else:
                    logger.error(f"Error {action_name}: {e}")
                
                if on_error:
                    on_error(self)
        
        return wrapper
    return decorator


async def execute_with_ui_update(
    coro: Callable,
    ui_update: Optional[Callable] = None,
    error_callback: Optional[Callable] = None
):
    """
    Выполнить асинхронную операцию с обновлением UI.
    
    Args:
        coro: Корутина для выполнения
        ui_update: Функция обновления UI после успешного выполнения
        error_callback: Callback при ошибке
    """
    try:
        await coro()
        if ui_update:
            ui_update()
    except Exception as e:
        logger.error(f"Error in async operation: {e}")
        if error_callback:
            error_callback()


def run_async(coro):
    """Запустить корутину как задачу."""
    return asyncio.create_task(coro)

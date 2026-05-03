"""
OSC-сервер на oscpy. Слушает UDP в собственном потоке, диспетчеризует
события в asyncio-loop основного приложения через call_soon_threadsafe.

Адресация:
- /shutter/open/<room>   — открыть шаттер на проекторе с IP, оканчивающимся на <room>
- /shutter/close/<room>  — закрыть шаттер
- /shutter/group/open    — открыть на всех проекторах из группы
- /shutter/group/close   — закрыть на всех проекторах из группы

Совместимо с TouchOSC и Resolume Arena. Фильтрация по MESSAGE_TYPE_BUTTON
(значение 3) сохранена для совместимости с TouchOSC, но если клиент шлёт
сообщения без аргументов (Resolume), они тоже принимаются.
"""
import asyncio
from collections import defaultdict
from typing import Callable, Dict, List, Optional

from oscpy.server import OSCThreadServer

from config import OSCConfig
from core.constants import OSCMessages
from utils.logger import setup_logger

logger = setup_logger(__name__)


class OSCEvent:
    """Имена событий OSC. Используются с OSCController.on/.off."""
    SHUTTER_OPEN = "shutter_open"      # (room: str)
    SHUTTER_CLOSE = "shutter_close"    # (room: str)
    GROUP_OPEN = "group_open"          # ()
    GROUP_CLOSE = "group_close"        # ()


Handler = Callable[..., None]


class OSCController:
    """OSC-сервер с pub/sub-API, безопасным для asyncio."""

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
    ) -> None:
        self.host = host if host is not None else OSCConfig.HOST
        self.port = port if port is not None else OSCConfig.PORT
        self._server: Optional[OSCThreadServer] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._handlers: Dict[str, List[Handler]] = defaultdict(list)

    # ---- Подписка ----

    def on(self, event: str, handler: Handler) -> None:
        """Добавить обработчик события. Вызовется в asyncio-loop."""
        self._handlers[event].append(handler)

    def off(self, event: str, handler: Handler) -> None:
        """Снять обработчик."""
        if handler in self._handlers[event]:
            self._handlers[event].remove(handler)

    # ---- Жизненный цикл ----

    async def start(self) -> None:
        """Запустить сервер. Привязывается к asyncio-loop вызывающего."""
        self._loop = asyncio.get_running_loop()
        self._server = OSCThreadServer(default_handler=self._dispatch)
        self._server.listen(address=self.host, port=self.port, default=True)
        logger.info(f"OSC Server started on {self.host}:{self.port}")

    def stop(self) -> None:
        """Остановить сервер. Безопасно вызывать многократно."""
        if self._server is None:
            return
        try:
            self._server.stop_all()
            self._server.terminate_server()
            self._server.join_server()
        except Exception as exc:
            logger.warning(f"Error stopping OSC server: {exc}")
        finally:
            self._server = None
            logger.info("OSC Server stopped")

    # ---- Диспетчеризация (вызывается из OSC-потока) ----

    def _dispatch(self, address, *args) -> None:
        """Колбэк oscpy. Парсит адрес и эмитит событие в asyncio-loop."""
        addr = address.decode() if isinstance(address, (bytes, bytearray)) else address

        # TouchOSC: 3 = button press. Resolume и др. могут слать без аргументов.
        # Принимаем оба случая; явный button-up (значение 0) отфильтровываем.
        if args and args[0] not in (OSCMessages.MESSAGE_TYPE_BUTTON, 1, 1.0):
            logger.debug(f"OSC: ignoring {addr} args={args}")
            return

        if addr.startswith('/shutter/group/open'):
            logger.info("OSC: group open")
            self._emit(OSCEvent.GROUP_OPEN)
        elif addr.startswith('/shutter/group/close'):
            logger.info("OSC: group close")
            self._emit(OSCEvent.GROUP_CLOSE)
        elif addr.startswith('/shutter/open'):
            room = addr.rsplit('/', 1)[-1]
            logger.info(f"OSC: open shutter for room {room}")
            self._emit(OSCEvent.SHUTTER_OPEN, room)
        elif addr.startswith('/shutter/close'):
            room = addr.rsplit('/', 1)[-1]
            logger.info(f"OSC: close shutter for room {room}")
            self._emit(OSCEvent.SHUTTER_CLOSE, room)
        else:
            logger.debug(f"OSC: no route for {addr}")

    def _emit(self, event: str, *args) -> None:
        """Перенести вызов всех подписчиков в основной asyncio-loop."""
        if self._loop is None or self._loop.is_closed():
            return
        for handler in list(self._handlers[event]):
            self._loop.call_soon_threadsafe(_safe_call, handler, args)


def _safe_call(handler: Handler, args: tuple) -> None:
    """Вызов обработчика с глобальным catch — чтобы один сбой не уронил loop."""
    try:
        handler(*args)
    except Exception as exc:
        logger.error(f"OSC handler {handler!r} raised: {exc}", exc_info=True)

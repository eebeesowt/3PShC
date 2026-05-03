"""
Контроллер для работы с OSC сервером.
Обрабатывает OSC сообщения и вызывает соответствующие callback'и.
"""
import asyncio
from typing import Callable, Optional
from pythonosc.osc_server import AsyncIOOSCUDPServer
from pythonosc.dispatcher import Dispatcher
from config import OSCConfig
from lib.constants import OSCMessages
from utils.logger import setup_logger

logger = setup_logger(__name__)


class OSCController:
    """Управление OSC сервером"""

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
    ):
        self.host = host if host is not None else OSCConfig.HOST
        self.port = port if port is not None else OSCConfig.PORT
        self.dispatcher = Dispatcher()
        self.server: Optional[AsyncIOOSCUDPServer] = None
        self.transport = None
        
        # Callback функции (устанавливаются извне)
        self.on_shutter_open: Optional[Callable[[str], None]] = None
        self.on_shutter_close: Optional[Callable[[str], None]] = None
        self.on_group_open: Optional[Callable[[], None]] = None
        self.on_group_close: Optional[Callable[[], None]] = None
        
        self._setup_routes()
    
    def _setup_routes(self):
        """Настроить маршруты OSC"""
        self.dispatcher.map("/shutter/open*", self._handle_shutter_open)
        self.dispatcher.map("/shutter/close*", self._handle_shutter_close)
        self.dispatcher.map("/shutter/group/open", self._handle_group_open)
        self.dispatcher.map("/shutter/group/close", self._handle_group_close)
    
    def _handle_shutter_open(self, address, *args):
        """Обработать команду открытия шаттера"""
        if args and args[0] == OSCMessages.MESSAGE_TYPE_BUTTON:  # Проверка типа сообщения
            room_number = address.split('/')[-1]
            logger.info(f"OSC: Open shutter for room {room_number}")
            if self.on_shutter_open:
                self.on_shutter_open(room_number)
    
    def _handle_shutter_close(self, address, *args):
        """Обработать команду закрытия шаттера"""
        if args and args[0] == OSCMessages.MESSAGE_TYPE_BUTTON:
            room_number = address.split('/')[-1]
            logger.info(f"OSC: Close shutter for room {room_number}")
            if self.on_shutter_close:
                self.on_shutter_close(room_number)
    
    def _handle_group_open(self, address, *args):
        """Обработать команду открытия группы"""
        if args and args[0] == OSCMessages.MESSAGE_TYPE_BUTTON:
            logger.info("OSC: Open group shutters")
            if self.on_group_open:
                self.on_group_open()
    
    def _handle_group_close(self, address, *args):
        """Обработать команду закрытия группы"""
        if args and args[0] == OSCMessages.MESSAGE_TYPE_BUTTON:
            logger.info("OSC: Close group shutters")
            if self.on_group_close:
                self.on_group_close()
    
    async def start(self):
        """Запустить OSC сервер"""
        loop = asyncio.get_running_loop()
        self.server = AsyncIOOSCUDPServer(
            (self.host, self.port),
            self.dispatcher,
            loop  # type: ignore
        )
        self.transport, _ = await self.server.create_serve_endpoint()
        logger.info(f"OSC Server started on {self.host}:{self.port}")
    
    def stop(self):
        """Остановить OSC сервер"""
        if self.transport:
            self.transport.close()
            logger.info("OSC Server stopped")

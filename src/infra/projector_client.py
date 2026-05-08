"""
TCP-транспорт для проекторов Panasonic с MD5-аутентификацией.
Низкий уровень: одно соединение на одну команду, никакой бизнес-логики.
"""
import asyncio
import hashlib
from typing import Optional

from core.constants import ProjectorProtocol, ProjectorResponses
from core.models import ProjectorConfig
from utils.logger import setup_logger

logger = setup_logger(__name__)


class ProjectorClient:
    """Сетевой клиент для одного проектора."""

    def __init__(self, config: ProjectorConfig) -> None:
        self._config = config
        # Panasonic NTCONTROL держит одну control-сессию: параллельные коннекты
        # ловят ER401 / закрытие. Лок сериализует команды на проектор; разные
        # проекторы остаются независимыми. Создаём лениво — иначе на 3.9
        # asyncio.Lock() в sync-__init__ может пожаловаться на отсутствие loop.
        self._send_lock: Optional[asyncio.Lock] = None

    async def send_raw(
        self,
        cmd: str,
        timeout: float = ProjectorProtocol.DEFAULT_TIMEOUT,
    ) -> str:
        """
        Отправить одну команду и вернуть декодированный ответ.

        При таймауте чтения возвращает ProjectorResponses.TIMEOUT (строка).
        При ошибке соединения пробрасывает asyncio.TimeoutError или Exception.

        Сериализован per-projector локом — две одновременные команды на один
        IP не пересекаются (это требование Panasonic NTCONTROL).
        """
        if self._send_lock is None:
            self._send_lock = asyncio.Lock()
        async with self._send_lock:
            return await self._send_unlocked(cmd, timeout)

    async def _send_unlocked(self, cmd: str, timeout: float) -> str:
        writer: Optional[asyncio.StreamWriter] = None
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self._config.ip, self._config.port),
                timeout,
            )
        except Exception as exc:
            logger.warning(
                f"Connection attempt failed for {self._config.ip}:{self._config.port}: {exc}"
            )
            raise asyncio.TimeoutError(
                f"Connection to {self._config.ip}:{self._config.port} timed out"
            ) from exc

        try:
            serv_answer = await asyncio.wait_for(
                reader.read(ProjectorProtocol.INITIAL_BUFFER_SIZE), timeout
            )
            decode_answer = serv_answer.decode()
            rand_num = decode_answer.split(' ')[-1][0:-1]
            auth_data = f'{self._config.login}:{self._config.password}:{rand_num}'
            md5hash = hashlib.md5(auth_data.encode())
            command = (
                md5hash.hexdigest()
                + ProjectorProtocol.PADDING_CHAR
                + ProjectorProtocol.PADDING_CHAR
                + cmd
                + ProjectorProtocol.TERMINATOR
            )
            writer.write(command.encode())
            await writer.drain()
            answ = await asyncio.wait_for(
                reader.read(ProjectorProtocol.RESPONSE_BUFFER_SIZE), timeout
            )
            decode_answer = answ.decode()[2:-1]
        except asyncio.TimeoutError:
            logger.warning(f"Connection timed out for {self._config.ip}")
            decode_answer = ProjectorResponses.TIMEOUT
        except Exception as exc:
            logger.error(f"Connection error for {self._config.ip}: {exc}")
            raise
        finally:
            if writer is not None:
                writer.close()
                await writer.wait_closed()
        return decode_answer

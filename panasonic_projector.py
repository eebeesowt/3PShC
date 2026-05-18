"""
Модуль управления проекторами Panasonic для Isadora Pythoner.

Один файл, только stdlib, без асинхронности — подключается в Pythoner
актор через вход `ext file`.

Содержит:
    - Projector        — один проектор: power / shutter / fade-time.
    - ProjectorGroup   — пакетные операции по списку проекторов
                         параллельно через ThreadPoolExecutor.
    - FADE_TIME_OPTIONS — допустимые значения fade-time (секунды),
                         Panasonic принимает дискретный набор.
    - ProjectorError   — выбрасывается при сетевых сбоях.

Каждый вызов команды на Projector открывает свежее TCP-подключение:
Panasonic выдаёт MD5-nonce при каждом коннекте, поэтому держать
постоянный сокет нельзя.
"""

import hashlib
import logging
import socket
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

DEFAULT_PORT = 1024
DEFAULT_TIMEOUT = 2.0

FADE_TIME_OPTIONS = (0.0, 0.5, 1.0, 1.5, 2.0, 2.5,
                     3.0, 3.5, 4.0, 5.0, 7.0, 10.0)

_TERMINATOR = b'\r'
_PADDING = '00'
_NONCE_BUF = 1024
_RESPONSE_BUF = 256

_CMD_POWER_ON = 'PON'
_CMD_POWER_OFF = 'POF'
_CMD_QUERY_POWER = 'QPW'
_CMD_SHUTTER_OPEN = 'OSH:0'
_CMD_SHUTTER_CLOSE = 'OSH:1'
_CMD_QUERY_SHUTTER = 'QSH'
_CMD_SET_FADE_IN = 'VXX:SEFS1={}'
_CMD_SET_FADE_OUT = 'VXX:SEFS2={}'
_CMD_QUERY_FADE_IN = 'QVX:SEFS1'
_CMD_QUERY_FADE_OUT = 'QVX:SEFS2'

_RESP_POWER_ON = '001'
_RESP_SHUTTER_OPEN = '0'


class ProjectorError(RuntimeError):
    """Ошибка обмена с проектором (таймаут, malformed-ответ, etc.)."""


class Projector:
    """
    Один проектор Panasonic. Объект-конфигурация, без постоянного
    соединения. Все методы синхронные и блокируют до ответа.
    """

    def __init__(self, ip: str, login: str, password: str,
                 port: int = DEFAULT_PORT,
                 timeout: float = DEFAULT_TIMEOUT,
                 label: str = 'None') -> None:
        self.ip = ip
        self.port = port
        self.login = login
        self.password = password
        self.timeout = timeout
        self.label = label or ip

    def send_raw(self, cmd: str) -> str:
        """
        Открыть TCP, авторизоваться по MD5-nonce, отправить `cmd`,
        вернуть ответ без служебных префиксов.

        Пример: send_raw('PON'), send_raw('VXX:SEFS1=0.5').
        """
        try:
            sock = socket.create_connection((self.ip, self.port), self.timeout)
        except OSError as exc:
            raise ProjectorError(
                f'{self.label}: cannot connect to {self.ip}:{self.port} ({exc})'
            ) from exc

        try:
            sock.settimeout(self.timeout)
            try:
                nonce_packet = sock.recv(_NONCE_BUF).decode('ascii', errors='replace')
            except OSError as exc:
                raise ProjectorError(
                    f'{self.label}: timeout reading auth nonce ({exc})'
                ) from exc

            nonce = nonce_packet.split(' ')[-1].rstrip('\r\n')
            if not nonce:
                raise ProjectorError(
                    f'{self.label}: malformed auth packet {nonce_packet!r}'
                )

            md5_hex = hashlib.md5(
                f'{self.login}:{self.password}:{nonce}'.encode('ascii')
            ).hexdigest()

            payload = (md5_hex + _PADDING + cmd).encode('ascii') + _TERMINATOR
            sock.sendall(payload)

            try:
                raw_resp = sock.recv(_RESPONSE_BUF)
            except OSError as exc:
                raise ProjectorError(
                    f'{self.label}: timeout reading response to {cmd!r} ({exc})'
                ) from exc
        finally:
            sock.close()

        text = raw_resp.decode('ascii', errors='replace').strip('\r\n')
        if text.startswith(_PADDING):
            text = text[len(_PADDING):]
        return text

    def power_on(self) -> None:
        self.send_raw(_CMD_POWER_ON)

    def power_off(self) -> None:
        self.send_raw(_CMD_POWER_OFF)

    def power_is_on(self) -> bool:
        return self.send_raw(_CMD_QUERY_POWER) == _RESP_POWER_ON

    def shutter_open(self) -> None:
        self.send_raw(_CMD_SHUTTER_OPEN)

    def shutter_close(self) -> None:
        self.send_raw(_CMD_SHUTTER_CLOSE)

    def shutter_is_open(self) -> bool:
        return self.send_raw(_CMD_QUERY_SHUTTER) == _RESP_SHUTTER_OPEN

    def set_fade_in(self, seconds: float) -> None:
        self.send_raw(_CMD_SET_FADE_IN.format(_coerce_fade(seconds)))

    def set_fade_out(self, seconds: float) -> None:
        self.send_raw(_CMD_SET_FADE_OUT.format(_coerce_fade(seconds)))

    def get_fade_in(self) -> float:
        return _parse_fade(self.send_raw(_CMD_QUERY_FADE_IN))

    def get_fade_out(self) -> float:
        return _parse_fade(self.send_raw(_CMD_QUERY_FADE_OUT))

    def __repr__(self) -> str:
        return f'Projector({self.label!r}, ip={self.ip!r})'


class ProjectorGroup:
    """
    Список проекторов с пакетными операциями.

    Каждый метод раскладывает работу на ThreadPoolExecutor:
    N подключений стартуют параллельно, метод возвращается, когда
    все потоки доехали (успех или исключение). Исключения собираются
    в словарь и логируются — один офлайн-проектор не валит остальных.

    Возвращаемое значение для каждой операции — dict {label: result_or_exception}.
    """

    def __init__(self, projectors) -> None:
        self.projectors = list(projectors)

    def _run_parallel(self, method_name: str, *args) -> dict:
        results = {}
        if not self.projectors:
            return results
        with ThreadPoolExecutor(max_workers=len(self.projectors)) as ex:
            future_to_proj = {
                ex.submit(getattr(p, method_name), *args): p
                for p in self.projectors
            }
            for fut, proj in future_to_proj.items():
                try:
                    results[proj.label] = fut.result()
                except Exception as exc:
                    logger.error('%s: %s%s failed: %s',
                                 proj.label, method_name, args, exc)
                    results[proj.label] = exc
        return results

    def power_on(self) -> dict:
        return self._run_parallel('power_on')

    def power_off(self) -> dict:
        return self._run_parallel('power_off')

    def shutter_open(self) -> dict:
        return self._run_parallel('shutter_open')

    def shutter_close(self) -> dict:
        return self._run_parallel('shutter_close')

    def set_fade_in(self, seconds: float) -> dict:
        return self._run_parallel('set_fade_in', seconds)

    def set_fade_out(self, seconds: float) -> dict:
        return self._run_parallel('set_fade_out', seconds)

    def __len__(self) -> int:
        return len(self.projectors)

    def __iter__(self):
        return iter(self.projectors)


def _coerce_fade(seconds: float) -> float:
    """Округлить до ближайшего значения из FADE_TIME_OPTIONS."""
    return min(FADE_TIME_OPTIONS, key=lambda x: abs(x - seconds))


def _parse_fade(response: str) -> float:
    """Распарсить ответ VXX:SEFSn= в float секунд."""
    value = response.rpartition('=')[2] if '=' in response else response
    try:
        return float(value)
    except ValueError:
        logger.warning('Could not parse fade time from %r', response)
        return 0.0

"""
Тонкий фасад Projector — сохраняет публичный API для существующих UI и сервисов.
Делегирует транспорт в ProjectorClient, команды в ProjectorApi, состояние
хранит в ProjectorState. Эта прослойка существует на время рефакторинга;
прямые потребители постепенно переходят на core/infra напрямую.
"""
from typing import Optional, Tuple

from core.constants import ProjectorProtocol, ProjectorStates
from core.models import ProjectorConfig, ProjectorState
from infra.projector_api import ProjectorApi
from infra.projector_client import ProjectorClient
from utils.logger import setup_logger

logger = setup_logger(__name__)


class Projector:
    # Константы на уровне класса — оставлены для обратной совместимости
    SHUTTER_OPEN = ProjectorStates.SHUTTER_OPEN
    SHUTER_CLOSED = ProjectorStates.SHUTTER_CLOSED  # legacy typo
    SHUTTER_CLOSED = ProjectorStates.SHUTTER_CLOSED

    def __init__(self, ip, port, login, password, label, id) -> None:
        self._config = ProjectorConfig(
            ip=ip,
            port=port,
            login=login,
            password=password,
            label=label if label else ip,
        )
        self._state = ProjectorState()
        self._client = ProjectorClient(self._config)
        self._api = ProjectorApi(self._client, self._state)

        self.id = id
        self.shutter_time_dict = ProjectorStates.SHUTTER_TIME_OPTIONS

    # ----- Конфиг (read-only) -----

    @property
    def ip(self) -> str:
        return self._config.ip

    @property
    def port(self) -> int:
        return self._config.port

    @property
    def login(self) -> str:
        return self._config.login

    @property
    def password(self) -> str:
        return self._config.password

    @property
    def label(self) -> str:
        return self._config.display_label

    @property
    def ip_room_number(self) -> str:
        return self._config.ip_room_number

    # ----- Состояние (mutable, делегируем в _state) -----

    @property
    def power(self) -> Optional[bool]:
        return self._state.power

    @power.setter
    def power(self, value: Optional[bool]) -> None:
        self._state.power = value

    @property
    def shutter(self) -> Optional[bool]:
        return self._state.shutter

    @shutter.setter
    def shutter(self, value: Optional[bool]) -> None:
        self._state.shutter = value

    @property
    def shutter_in_time(self) -> Optional[str]:
        return self._state.shutter_in_time

    @shutter_in_time.setter
    def shutter_in_time(self, value: Optional[str]) -> None:
        self._state.shutter_in_time = value

    @property
    def shutter_out_time(self) -> Optional[str]:
        return self._state.shutter_out_time

    @shutter_out_time.setter
    def shutter_out_time(self, value: Optional[str]) -> None:
        self._state.shutter_out_time = value

    @property
    def group(self) -> bool:
        return self._state.group

    @group.setter
    def group(self, value: bool) -> None:
        self._state.group = value

    @property
    def state(self) -> ProjectorState:
        return self._state

    @property
    def config(self) -> ProjectorConfig:
        return self._config

    @property
    def api(self) -> ProjectorApi:
        return self._api

    # ----- Транспорт (legacy API) -----

    async def send_cmd(self, cmd: str, timeout: float = ProjectorProtocol.DEFAULT_TIMEOUT) -> str:
        return await self._client.send_raw(cmd, timeout=timeout)

    # ----- Высокоуровневые команды (делегация в ProjectorApi) -----

    async def get_info(self) -> None:
        await self._api.refresh_info()

    async def power_on(self) -> None:
        await self._api.power_on()

    async def power_off(self) -> None:
        await self._api.power_off()

    async def shutter_open(self) -> None:
        await self._api.shutter_open()

    async def shutter_close(self) -> None:
        await self._api.shutter_close()

    async def set_shutter_in(self, shutter_time: str) -> None:
        await self._api.set_shutter_in(shutter_time)

    async def set_shutter_out(self, shutter_time: str) -> None:
        await self._api.set_shutter_out(shutter_time)

    async def lens_home(self) -> None:
        await self._api.lens_home()

    async def lens_shift_h(self, direction: str, speed: str = 'normal') -> None:
        await self._api.lens_shift_h(direction, speed)

    async def lens_shift_v(self, direction: str, speed: str = 'normal') -> None:
        await self._api.lens_shift_v(direction, speed)

    async def lens_focus(self, direction: str, speed: str = 'normal') -> None:
        await self._api.lens_focus(direction, speed)

    async def lens_zoom(self, direction: str, speed: str = 'normal') -> None:
        await self._api.lens_zoom(direction, speed)

    async def get_lens_position(self) -> Tuple[Optional[str], Optional[str]]:
        return await self._api.get_lens_position()

    async def set_lens_position(
        self,
        h_value: Optional[int] = None,
        v_value: Optional[int] = None,
    ) -> None:
        await self._api.set_lens_position(h_value=h_value, v_value=v_value)

    async def get_aspect_ratio(self) -> str:
        return await self._api.get_aspect_ratio()

    async def set_aspect_ratio(self, ratio: str) -> None:
        await self._api.set_aspect_ratio(ratio)

    async def get_test_pattern(self) -> str:
        return await self._api.get_test_pattern()

    async def set_test_pattern(self, pattern_name: str) -> None:
        await self._api.set_test_pattern(pattern_name)

    async def get_installation_mode(self) -> str:
        return await self._api.get_installation_mode()

    async def set_installation_mode(self, mode_name: str) -> None:
        await self._api.set_installation_mode(mode_name)

    async def apply_saved_settings(self, settings: dict) -> None:
        await self._api.apply_saved_settings(settings)

    def debug_info(self) -> None:
        info = f"""
    IP--------{self.ip}
    PORT------{self.port}
    LOGIN-----{self.login}
    PASSWORD--{self.password}
    LABEL-----{self.label}
    ID--------{self.id}
    POWER-----{self.power}
    GROUP-----{self.group}
    SHUTTER---{self.shutter}
    SHUTTER_IN---{self.shutter_in_time}
    SHUTTER_OUT---{self.shutter_out_time}
        """
        logger.debug(info)

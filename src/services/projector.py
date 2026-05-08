"""
Тонкий фасад Projector — единый mutable-handle, которым оперируют UI и
сервисы. Делегирует транспорт в ProjectorClient, команды в ProjectorApi,
состояние хранит в ProjectorState.
"""
from typing import Optional, Tuple

from core.constants import ProjectorStates
from core.models import ProjectorConfig, ProjectorState
from infra.projector_api import ProjectorApi
from infra.projector_client import ProjectorClient


class Projector:
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
        self._api = ProjectorApi(self._config, self._client, self._state)

        self.id = id

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

    # ----- Идентификация -----

    @property
    def model(self) -> Optional[str]:
        return self._state.model

    @property
    def serial(self) -> Optional[str]:
        return self._state.serial

    @property
    def firmware(self) -> Optional[str]:
        return self._state.firmware

    @property
    def family(self) -> str:
        """'RZ' / 'RQ' / 'unknown' — выводится из state.model."""
        return ProjectorStates.detect_family(self._state.model or '')

    @property
    def input_profile(self) -> str:
        """'DIRECT_RZ' / 'SDM_RQ25' / 'HYBRID_RQ7' / 'UNKNOWN' — определяет
        список физически доступных входов на этой модели."""
        return ProjectorStates.detect_input_profile(self._state.model or '')

    @property
    def config(self) -> ProjectorConfig:
        return self._config

    @property
    def api(self) -> ProjectorApi:
        return self._api

    # ----- Высокоуровневые команды (делегация в ProjectorApi) -----

    async def get_info(self) -> None:
        await self._api.refresh_info()

    async def refresh_identity(self) -> None:
        """Принудительно обновить model/serial/firmware. Обычно делается лениво
        в refresh_info при первом успехе; вызывайте напрямую, чтобы перезапросить.
        """
        await self._api.refresh_identity()

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

    # ----- Source / Freeze / OSD / Geometry -----

    async def get_input_source(self) -> str:
        return await self._api.get_input_source()

    async def set_input_source(self, name: str) -> None:
        await self._api.set_input_source(name)

    async def get_freeze(self) -> Optional[bool]:
        return await self._api.get_freeze()

    async def set_freeze(self, frozen: bool) -> None:
        await self._api.set_freeze(frozen)

    async def get_osd(self) -> Optional[bool]:
        return await self._api.get_osd()

    async def set_osd(self, on: bool) -> None:
        await self._api.set_osd(on)

    async def get_geometry(self) -> str:
        return await self._api.get_geometry()

    async def set_geometry(self, mode_name: str) -> None:
        await self._api.set_geometry(mode_name)

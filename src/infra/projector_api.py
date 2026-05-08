"""
Высокоуровневые команды управления проектором.
Поверх ProjectorClient (транспорт) и ProjectorState (модель).
"""
import asyncio
from typing import Optional, Tuple

from core.constants import (
    ProjectorCommands,
    ProjectorProtocol,
    ProjectorResponses,
    ProjectorStates,
)
from core.models import LensPosition, ProjectorConfig, ProjectorState
from infra.projector_client import ProjectorClient
from utils.logger import setup_logger

logger = setup_logger(__name__)


class ProjectorApi:
    """Команды протокола Panasonic, обновляющие ProjectorState."""

    def __init__(
        self,
        config: ProjectorConfig,
        client: ProjectorClient,
        state: ProjectorState,
    ) -> None:
        self._config = config
        self._client = client
        self._state = state

    @property
    def label(self) -> str:
        return self._config.display_label

    # --- Базовое состояние ---

    async def refresh_info(self) -> None:
        """Обновить power/shutter/shutter_in/out из проектора.

        Дополнительно: при первом успешном вызове подтягивает идентификацию
        (model/serial/firmware) — она не меняется в рантайме, поэтому опрос
        делается один раз и кешируется в state.
        """
        try:
            power = await self._client.send_raw(ProjectorCommands.QUERY_POWER)
        except Exception as exc:
            logger.error(f"Error getting power state for {self.label}: {exc}")
            return

        if power == ProjectorResponses.POWER_ON:
            self._state.power = True
            shutter = await self._client.send_raw(ProjectorCommands.QUERY_SHUTTER)
            if shutter == ProjectorResponses.SHUTTER_OPEN:
                self._state.shutter = ProjectorStates.SHUTTER_OPEN
            elif shutter == ProjectorResponses.SHUTTER_CLOSED:
                self._state.shutter = ProjectorStates.SHUTTER_CLOSED
        elif power == ProjectorResponses.POWER_OFF:
            self._state.power = False
        else:
            raise ValueError(f"Unknown power state: {power}")

        get_in = await self._client.send_raw(ProjectorCommands.QUERY_SHUTTER_IN)
        in_parts = get_in.split('=')
        self._state.shutter_in_time = in_parts[1] if len(in_parts) > 1 else 'None'

        get_out = await self._client.send_raw(ProjectorCommands.QUERY_SHUTTER_OUT)
        out_parts = get_out.split('=')
        self._state.shutter_out_time = out_parts[1] if len(out_parts) > 1 else 'None'

        if not self._state.identity_attempted:
            await self.refresh_identity()

    @staticmethod
    def _is_valid_response(resp: str) -> bool:
        """Ответ полезный, если не пуст, не 'ER*' (unsupported) и не таймаут."""
        if not resp:
            return False
        upper = resp.upper()
        return not upper.startswith('ER') and resp != ProjectorResponses.TIMEOUT

    async def refresh_identity(self) -> None:
        """Запросить QID (model), QSN (serial), QVX:SVRS0 или SVRSE (firmware).
        Тихо игнорирует частичные ошибки — поля либо заполняются, либо
        остаются None. По завершению (даже при провале) ставит
        identity_attempted=True, чтобы refresh_info не повторял запрос.
        """
        try:
            try:
                model = await self._client.send_raw(ProjectorCommands.QUERY_MODEL)
                model = model.strip()
                if self._is_valid_response(model):
                    self._state.model = model
            except Exception as exc:
                logger.warning(f"Could not read model for {self.label}: {exc}")

            try:
                serial = await self._client.send_raw(ProjectorCommands.QUERY_SERIAL)
                serial = serial.strip()
                if self._is_valid_response(serial):
                    self._state.serial = serial
            except Exception as exc:
                logger.warning(f"Could not read serial for {self.label}: {exc}")

            # Firmware: SVRS0 на RZ120/RQ25K, SVRSE на RQ7-series. Пробуем SVRS0
            # первым — если ER или Timeout, падаем на SVRSE.
            for cmd in (ProjectorCommands.QUERY_FIRMWARE_MAIN,
                        ProjectorCommands.QUERY_FIRMWARE_GENERIC):
                try:
                    fw = await self._client.send_raw(cmd)
                except Exception as exc:
                    logger.warning(f"Firmware query {cmd} failed for {self.label}: {exc}")
                    continue
                fw = fw.strip()
                if self._is_valid_response(fw):
                    # 'SVRS0=1.00.01' / 'SVRSE=1.00' → правая часть.
                    self._state.firmware = fw.split('=')[-1] if '=' in fw else fw
                    break

            if self._state.model:
                family = ProjectorStates.detect_family(self._state.model)
                profile = ProjectorStates.detect_input_profile(self._state.model)
                logger.info(
                    f"Identified {self.label}: model={self._state.model} "
                    f"serial={self._state.serial} fw={self._state.firmware} "
                    f"family={family} input_profile={profile}"
                )
        finally:
            self._state.identity_attempted = True

    # --- Питание ---

    async def power_on(self) -> None:
        await self._client.send_raw(ProjectorCommands.POWER_ON)
        self._state.power = True

    async def power_off(self) -> None:
        await self._client.send_raw(ProjectorCommands.POWER_OFF)
        self._state.power = False

    # --- Шаттер ---

    async def shutter_open(self) -> None:
        await self._client.send_raw(ProjectorCommands.SHUTTER_OPEN)
        self._state.shutter = ProjectorStates.SHUTTER_OPEN

    async def shutter_close(self) -> None:
        await self._client.send_raw(ProjectorCommands.SHUTTER_CLOSE)
        self._state.shutter = ProjectorStates.SHUTTER_CLOSED

    async def set_shutter_in(self, shutter_time: str) -> None:
        await self._client.send_raw(
            ProjectorCommands.SET_SHUTTER_IN.format(shutter_time)
        )

    async def set_shutter_out(self, shutter_time: str) -> None:
        await self._client.send_raw(
            ProjectorCommands.SET_SHUTTER_OUT.format(shutter_time)
        )

    # --- Объектив ---

    async def lens_home(self) -> None:
        await self._client.send_raw(ProjectorCommands.LENS_HOME)

    async def lens_shift_h(self, direction: str, speed: str = 'normal') -> None:
        cmd_map = {
            ('plus', 'slow'): ProjectorCommands.LENS_SHIFT_H_SLOW_PLUS,
            ('minus', 'slow'): ProjectorCommands.LENS_SHIFT_H_SLOW_MINUS,
            ('plus', 'normal'): ProjectorCommands.LENS_SHIFT_H_NORMAL_PLUS,
            ('minus', 'normal'): ProjectorCommands.LENS_SHIFT_H_NORMAL_MINUS,
            ('plus', 'fast'): ProjectorCommands.LENS_SHIFT_H_FAST_PLUS,
            ('minus', 'fast'): ProjectorCommands.LENS_SHIFT_H_FAST_MINUS,
        }
        await self._client.send_raw(cmd_map[(direction, speed)])

    async def lens_shift_v(self, direction: str, speed: str = 'normal') -> None:
        cmd_map = {
            ('plus', 'slow'): ProjectorCommands.LENS_SHIFT_V_SLOW_PLUS,
            ('minus', 'slow'): ProjectorCommands.LENS_SHIFT_V_SLOW_MINUS,
            ('plus', 'normal'): ProjectorCommands.LENS_SHIFT_V_NORMAL_PLUS,
            ('minus', 'normal'): ProjectorCommands.LENS_SHIFT_V_NORMAL_MINUS,
            ('plus', 'fast'): ProjectorCommands.LENS_SHIFT_V_FAST_PLUS,
            ('minus', 'fast'): ProjectorCommands.LENS_SHIFT_V_FAST_MINUS,
        }
        await self._client.send_raw(cmd_map[(direction, speed)])

    async def lens_focus(self, direction: str, speed: str = 'normal') -> None:
        cmd_map = {
            ('plus', 'slow'): ProjectorCommands.LENS_FOCUS_SLOW_PLUS,
            ('minus', 'slow'): ProjectorCommands.LENS_FOCUS_SLOW_MINUS,
            ('plus', 'normal'): ProjectorCommands.LENS_FOCUS_NORMAL_PLUS,
            ('minus', 'normal'): ProjectorCommands.LENS_FOCUS_NORMAL_MINUS,
            ('plus', 'fast'): ProjectorCommands.LENS_FOCUS_FAST_PLUS,
            ('minus', 'fast'): ProjectorCommands.LENS_FOCUS_FAST_MINUS,
        }
        await self._client.send_raw(cmd_map[(direction, speed)])

    async def lens_zoom(self, direction: str, speed: str = 'normal') -> None:
        cmd_map = {
            ('plus', 'slow'): ProjectorCommands.LENS_ZOOM_SLOW_PLUS,
            ('minus', 'slow'): ProjectorCommands.LENS_ZOOM_SLOW_MINUS,
            ('plus', 'normal'): ProjectorCommands.LENS_ZOOM_NORMAL_PLUS,
            ('minus', 'normal'): ProjectorCommands.LENS_ZOOM_NORMAL_MINUS,
            ('plus', 'fast'): ProjectorCommands.LENS_ZOOM_FAST_PLUS,
            ('minus', 'fast'): ProjectorCommands.LENS_ZOOM_FAST_MINUS,
        }
        await self._client.send_raw(cmd_map[(direction, speed)])

    async def get_lens_position(self) -> Tuple[Optional[str], Optional[str]]:
        """Получить и закэшировать позицию H/V в сыром формате '+00200'."""
        h_raw = await self._client.send_raw(ProjectorCommands.QUERY_LENS_H_POSITION)
        v_raw = await self._client.send_raw(ProjectorCommands.QUERY_LENS_V_POSITION)
        h_pos = h_raw.split('=')[-1] if '=' in h_raw else h_raw
        v_pos = v_raw.split('=')[-1] if '=' in v_raw else v_raw
        self._state.lens_position = LensPosition(h=h_pos, v=v_pos)
        return h_pos, v_pos

    async def set_lens_position(
        self,
        h_value: Optional[int] = None,
        v_value: Optional[int] = None,
    ) -> None:
        if h_value is not None and v_value is not None:
            position_str = f"{h_value:+06d}{v_value:+06d}"
            await self._client.send_raw(
                ProjectorCommands.SET_LENS_POSITION_HV.format(position_str)
            )
        elif h_value is not None:
            await self._client.send_raw(
                ProjectorCommands.SET_LENS_H_POSITION.format(f"{h_value:+06d}")
            )
        elif v_value is not None:
            await self._client.send_raw(
                ProjectorCommands.SET_LENS_V_POSITION.format(f"{v_value:+06d}")
            )

    async def wait_for_lens_settle(
        self,
        max_seconds: float = ProjectorProtocol.LENS_HOME_SETTLE_MAX_SECONDS,
        poll_interval: float = ProjectorProtocol.LENS_HOME_POLL_INTERVAL,
    ) -> None:
        """
        Ждать стабилизации линзы (после lens_home или set_lens_position).

        Опрашивает get_lens_position с интервалом poll_interval.
        Считает линзу стабильной при двух одинаковых последовательных ответах.
        Возвращается, когда линза стабилизировалась или истёк max_seconds.
        Заменяет старый open-loop sleep(12).
        """
        loop = asyncio.get_event_loop()
        deadline = loop.time() + max_seconds
        previous: Optional[Tuple[Optional[str], Optional[str]]] = None

        while loop.time() < deadline:
            try:
                current = await self.get_lens_position()
            except Exception as exc:
                logger.warning(f"Lens settle poll failed for {self.label}: {exc}")
                await asyncio.sleep(poll_interval)
                continue

            if previous is not None and current == previous and all(current):
                logger.debug(f"Lens settled for {self.label} at {current}")
                return
            previous = current
            await asyncio.sleep(poll_interval)

        logger.warning(
            f"Lens settle timeout ({max_seconds}s) for {self.label} — продолжаем"
        )

    # --- Соотношение сторон / тестовый паттерн / установка ---

    async def get_aspect_ratio(self) -> str:
        result = await self._client.send_raw(ProjectorCommands.QUERY_ASPECT_RATIO)
        self._state.display_settings.aspect_ratio = result
        return result

    async def set_aspect_ratio(self, ratio: str) -> None:
        cmd_map = {
            '16:10': ProjectorCommands.SET_ASPECT_RATIO_16_10,
            '16:9': ProjectorCommands.SET_ASPECT_RATIO_16_9,
            '4:3': ProjectorCommands.SET_ASPECT_RATIO_4_3,
        }
        if ratio not in cmd_map:
            raise ValueError(
                f"Invalid aspect ratio: {ratio}. Must be '16:10', '16:9', or '4:3'"
            )
        await self._client.send_raw(cmd_map[ratio])

    async def get_test_pattern(self) -> str:
        result = await self._client.send_raw(ProjectorCommands.QUERY_TEST_PATTERN)
        self._state.display_settings.test_pattern = result
        return result

    async def set_test_pattern(self, pattern_name: str) -> None:
        if pattern_name not in ProjectorStates.TEST_PATTERNS:
            raise ValueError(f"Invalid test pattern: {pattern_name}")
        pattern_code = ProjectorStates.TEST_PATTERNS[pattern_name]
        await self._client.send_raw(
            ProjectorCommands.SET_TEST_PATTERN.format(pattern_code)
        )

    async def get_installation_mode(self) -> str:
        result = await self._client.send_raw(ProjectorCommands.QUERY_INSTALLATION)
        self._state.display_settings.installation_mode = result
        return result

    async def set_installation_mode(self, mode_name: str) -> None:
        if mode_name not in ProjectorStates.INSTALLATION_MODES:
            raise ValueError(f"Invalid installation mode: {mode_name}")
        mode_code = ProjectorStates.INSTALLATION_MODES[mode_name]
        cmd = ProjectorCommands.SET_INSTALLATION.format(mode_code)
        logger.debug(f"Setting installation mode for {self.label}: {cmd}")
        await self._client.send_raw(cmd)

    # --- Источник сигнала / Freeze / OSD / Geometry ---

    async def get_input_source(self) -> str:
        """Вернуть сабкод (e.g. 'HD1') либо сырой ответ, если не распознан."""
        result = await self._client.send_raw(ProjectorCommands.QUERY_INPUT)
        return result.strip()

    async def set_input_source(self, name: str) -> None:
        if name not in ProjectorStates.INPUT_SOURCES:
            raise ValueError(f"Invalid input source: {name}")
        code = ProjectorStates.INPUT_SOURCES[name]
        await self._client.send_raw(ProjectorCommands.SET_INPUT.format(code))

    async def get_freeze(self) -> Optional[bool]:
        result = await self._client.send_raw(ProjectorCommands.QUERY_FREEZE)
        result = result.strip()
        if result == '0':
            return False
        if result == '1':
            return True
        return None

    async def set_freeze(self, frozen: bool) -> None:
        cmd = ProjectorCommands.FREEZE_ON if frozen else ProjectorCommands.FREEZE_OFF
        await self._client.send_raw(cmd)

    async def get_osd(self) -> Optional[bool]:
        result = await self._client.send_raw(ProjectorCommands.QUERY_OSD)
        result = result.strip()
        if result == '0':
            return False
        if result == '1':
            return True
        return None

    async def set_osd(self, on: bool) -> None:
        cmd = ProjectorCommands.OSD_ON if on else ProjectorCommands.OSD_OFF
        await self._client.send_raw(cmd)

    async def get_geometry(self) -> str:
        """Сырой код от QVX:GMMI0 (например '+00000' или 'GMMI0=+00000')."""
        result = await self._client.send_raw(ProjectorCommands.QUERY_GEOMETRY)
        return result.split('=')[-1].strip() if '=' in result else result.strip()

    async def set_geometry(self, mode_name: str) -> None:
        if mode_name not in ProjectorStates.GEOMETRY_MODES:
            raise ValueError(f"Invalid geometry mode: {mode_name}")
        code = ProjectorStates.GEOMETRY_MODES[mode_name]
        await self._client.send_raw(ProjectorCommands.SET_GEOMETRY.format(code))

    # --- Высокоуровневые сценарии ---

    async def apply_saved_settings(self, settings: dict) -> None:
        """
        Применить сохранённые настройки: сбросить линзу в home, дождаться
        стабилизации, применить aspect/installation/lens position.
        """
        try:
            logger.info(f"Applying saved settings for {self.label}")

            logger.info(f"Resetting lens to home position for {self.label}")
            await self.lens_home()
            await self.wait_for_lens_settle()

            display_settings = settings.get('display_settings', {})

            if 'aspect_ratio' in display_settings:
                aspect_ratio = display_settings['aspect_ratio']
                logger.info(f"Setting aspect ratio to {aspect_ratio}")
                await self.set_aspect_ratio(aspect_ratio)

            if 'installation_mode' in display_settings:
                installation_mode = display_settings['installation_mode']
                logger.info(f"Setting installation mode to {installation_mode}")
                await self.set_installation_mode(installation_mode)

            lens_settings = settings.get('lens_settings', {})
            h_position = lens_settings.get('h_position')
            v_position = lens_settings.get('v_position')

            if h_position and v_position and h_position != '---' and v_position != '---':
                logger.info(
                    f"Setting lens position to H:{h_position}, V:{v_position}"
                )
                h_int = int(h_position)
                v_int = int(v_position)
                await self.set_lens_position(h_value=h_int, v_value=v_int)

            logger.info(f"Successfully applied saved settings for {self.label}")
        except Exception as exc:
            logger.error(f"Error applying saved settings for {self.label}: {exc}")
            raise

    def snapshot_settings_dict(self) -> dict:
        """
        Сериализовать display_settings + lens_position в формат файла настроек.
        Преобразует сырые коды (например, aspect '0' → '16:10') в человеко-
        читаемые имена. Используется SceneService при сохранении.
        """
        ds = self._state.display_settings
        lp = self._state.lens_position

        aspect_ratio = ProjectorStates.ASPECT_RATIO_BY_CODE.get(
            ds.aspect_ratio or '', '16:9'
        )

        installation_mode = 'Front/Desk'
        if ds.installation_mode is not None:
            for name, code in ProjectorStates.INSTALLATION_MODES.items():
                if ds.installation_mode == code:
                    installation_mode = name
                    break

        return {
            'lens_settings': {
                # '---' — sentinel: apply_saved_settings пропустит шаг и не уведёт
                # линзу в (0,0), если опрос не удался.
                'h_position': lp.h if lp.h else '---',
                'v_position': lp.v if lp.v else '---',
            },
            'display_settings': {
                'aspect_ratio': aspect_ratio,
                'installation_mode': installation_mode,
            },
        }

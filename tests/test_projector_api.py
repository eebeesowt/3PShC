"""Тесты на ProjectorApi — фиксируют sentinel '---' в snapshot и behavior
fallback'а identity. Без сети: ProjectorClient мокаем.
"""
import asyncio
from typing import List, Optional
from unittest.mock import patch

import pytest

from core.constants import ProjectorCommands, ProjectorResponses
from core.models import LensPosition, ProjectorConfig, ProjectorState
from infra.projector_api import ProjectorApi
from infra.projector_client import ProjectorClient


class _FakeClient:
    """Прим. ProjectorClient: возвращает заранее заданные ответы по cmd."""

    def __init__(self, responses: dict):
        self.responses = responses
        self.calls: List[str] = []

    async def send_raw(self, cmd: str, timeout: float = 2.0) -> str:
        self.calls.append(cmd)
        if cmd not in self.responses:
            return ProjectorResponses.TIMEOUT
        result = self.responses[cmd]
        if isinstance(result, Exception):
            raise result
        return result


def _make_api(responses: Optional[dict] = None):
    config = ProjectorConfig(
        ip='192.168.1.10', port=1024, login='admin', password='pwd', label='X',
    )
    state = ProjectorState()
    client = _FakeClient(responses or {})
    api = ProjectorApi(config, client, state)
    return api, state, client


def test_snapshot_uses_dashes_sentinel_when_lens_unknown():
    """Главное: при неудачном опросе линзы snapshot пишет '---', а не '0' —
    иначе apply_saved_settings уведёт линзу в (0,0)."""
    api, state, _ = _make_api()
    # state.lens_position по умолчанию пуст (h=None, v=None)
    snap = api.snapshot_settings_dict()
    assert snap['lens_settings']['h_position'] == '---'
    assert snap['lens_settings']['v_position'] == '---'


def test_snapshot_keeps_real_lens_values():
    api, state, _ = _make_api()
    state.lens_position = LensPosition(h='+00200', v='-00100')
    snap = api.snapshot_settings_dict()
    assert snap['lens_settings']['h_position'] == '+00200'
    assert snap['lens_settings']['v_position'] == '-00100'


def test_refresh_identity_falls_back_from_svrs0_to_svrse():
    """RZ120: SVRS0 работает. RQ7: SVRS0 → ER, fallback на SVRSE."""
    api, state, client = _make_api({
        ProjectorCommands.QUERY_MODEL: 'RQ7L',
        ProjectorCommands.QUERY_SERIAL: 'SW0101234',
        ProjectorCommands.QUERY_FIRMWARE_MAIN: 'ER401',  # RQ7 не знает SVRS0
        ProjectorCommands.QUERY_FIRMWARE_GENERIC: 'SVRSE=1.00',
    })
    asyncio.run(api.refresh_identity())
    assert state.model == 'RQ7L'
    assert state.serial == 'SW0101234'
    assert state.firmware == '1.00'
    assert state.identity_attempted is True


def test_refresh_identity_skips_timeout_for_firmware():
    """Если SVRS0 даёт Timeout — не пишем 'Timeout' в state.firmware."""
    api, state, _ = _make_api({
        ProjectorCommands.QUERY_MODEL: 'RZ120',
        ProjectorCommands.QUERY_SERIAL: 'SN1',
        ProjectorCommands.QUERY_FIRMWARE_MAIN: ProjectorResponses.TIMEOUT,
        ProjectorCommands.QUERY_FIRMWARE_GENERIC: ProjectorResponses.TIMEOUT,
    })
    asyncio.run(api.refresh_identity())
    assert state.model == 'RZ120'
    assert state.firmware is None
    assert state.identity_attempted is True


def test_refresh_identity_marks_attempted_even_on_full_failure():
    """После полного провала повторный refresh_info не должен снова дёргать QID."""
    err = Exception("connection refused")
    api, state, _ = _make_api({
        ProjectorCommands.QUERY_MODEL: err,
        ProjectorCommands.QUERY_SERIAL: err,
        ProjectorCommands.QUERY_FIRMWARE_MAIN: err,
        ProjectorCommands.QUERY_FIRMWARE_GENERIC: err,
    })
    asyncio.run(api.refresh_identity())
    assert state.model is None
    assert state.identity_attempted is True


def test_set_aspect_ratio_uses_vsf_not_vsp():
    """Защита от регрессии: команда set_aspect_ratio шлёт VSF:* (как в PDF),
    а не старый битый VSP:*."""
    api, _, client = _make_api({})
    asyncio.run(api.set_aspect_ratio('16:9'))
    assert client.calls == ['VSF:1']


def test_set_input_source_serializes_dm1_codes():
    api, _, client = _make_api({})
    asyncio.run(api.set_input_source('SLOT: 12G SDI (SDM)'))
    assert client.calls == ['IIS:DM1,SD1']


def test_set_geometry_corner_correction():
    api, _, client = _make_api({})
    asyncio.run(api.set_geometry('Corner Correction'))
    assert client.calls == ['VXX:GMMI0=+00010']


def test_get_freeze_parses_bare_zero_one():
    api, _, _ = _make_api({ProjectorCommands.QUERY_FREEZE: '1'})
    result = asyncio.run(api.get_freeze())
    assert result is True

    api2, _, _ = _make_api({ProjectorCommands.QUERY_FREEZE: '0'})
    assert asyncio.run(api2.get_freeze()) is False


def test_get_osd_parses_bare_zero_one():
    api, _, _ = _make_api({ProjectorCommands.QUERY_OSD: '0'})
    assert asyncio.run(api.get_osd()) is False


# ---- Corner correction ----


def test_set_corner_offset_serializes_register_and_value():
    api, _, client = _make_api({})
    asyncio.run(api.set_corner_offset('UL_V', 250))
    assert client.calls == ['VXX:GMFI1=+00250']


def test_set_corner_offset_negative_value():
    api, _, client = _make_api({})
    asyncio.run(api.set_corner_offset('LL_V', -150))
    assert client.calls == ['VXX:GMFI3=-00150']


def test_set_corner_offset_caches_in_state():
    api, state, _ = _make_api({})
    asyncio.run(api.set_corner_offset('UL_H', 480))
    assert state.corners['UL_H'] == 480


def test_set_corner_offset_rejects_bad_id():
    api, _, _ = _make_api({})
    import pytest
    with pytest.raises(ValueError):
        asyncio.run(api.set_corner_offset('BOGUS', 0))


def test_get_corner_offset_parses_response():
    api, state, _ = _make_api({'QVX:GMFI2': 'GMFI2=+00075'})
    value = asyncio.run(api.get_corner_offset('UR_V'))
    assert value == 75
    assert state.corners['UR_V'] == 75


def test_get_corner_offset_handles_negative():
    api, _, _ = _make_api({'QVX:GMFI7': 'GMFI7=-00200'})
    assert asyncio.run(api.get_corner_offset('UR_H')) == -200


def test_get_corner_offset_returns_none_on_er():
    api, _, _ = _make_api({'QVX:GMFI1': 'ER401'})
    assert asyncio.run(api.get_corner_offset('UL_V')) is None


def test_get_all_corners_iterates_all_registers():
    responses = {
        f'QVX:{reg}': f'{reg}={"+00010"}'
        for reg in ('GMFI1', 'GMFI2', 'GMFI3', 'GMFI4', 'GMFI5',
                    'GMFI6', 'GMFI7', 'GMFI8', 'GMFI9', 'GMFIA')
    }
    api, state, _ = _make_api(responses)
    snapshot = asyncio.run(api.get_all_corners())
    assert len(snapshot) == 10
    assert state.corners['UL_V'] == 10
    assert state.corners['LIN_H'] == 10


def test_set_corner_test_grid_on_off():
    api, _, client = _make_api({})
    asyncio.run(api.set_corner_test_grid(True))
    asyncio.run(api.set_corner_test_grid(False))
    assert client.calls == ['VXX:GMCIA=+00001', 'VXX:GMCIA=+00000']


def test_snapshot_includes_geometry_corners_when_non_zero():
    api, state, _ = _make_api({})
    state.corners['UL_V'] = 200
    state.corners['UR_V'] = 0  # ноль — не сохраняется
    state.corners['LR_H'] = -100
    snap = api.snapshot_settings_dict()
    assert 'geometry_corners' in snap
    assert snap['geometry_corners'] == {'UL_V': 200, 'LR_H': -100}


def test_snapshot_omits_geometry_corners_when_all_zero():
    api, state, _ = _make_api({})
    state.corners['UL_V'] = 0
    snap = api.snapshot_settings_dict()
    assert 'geometry_corners' not in snap


def test_apply_saved_settings_restores_corners():
    """apply_saved_settings должен включить Corner Correction режим
    и применить все сохранённые offsets."""
    # Минимальный набор ответов, чтобы дойти до corner-блока без падений
    responses = {
        ProjectorCommands.QUERY_LENS_H_POSITION: 'LNSI7=+00000',
        ProjectorCommands.QUERY_LENS_V_POSITION: 'LNSI8=+00000',
    }
    api, state, client = _make_api(responses)
    state.identity_attempted = True  # пропускаем identity-fetch

    # Заглушка для wait_for_lens_settle, чтобы тест не висел 15 секунд
    async def _no_settle(*args, **kwargs):
        return
    api.wait_for_lens_settle = _no_settle  # type: ignore[assignment]

    settings = {
        'lens_settings': {'h_position': '---', 'v_position': '---'},
        'display_settings': {},
        'geometry_corners': {'UL_V': 100, 'LR_H': -50, 'LIN_V': 5},
    }
    asyncio.run(api.apply_saved_settings(settings))

    # Должны увидеть set_geometry → CC + три set_corner
    assert 'VXX:GMMI0=+00010' in client.calls   # активация Corner Correction
    assert 'VXX:GMFI1=+00100' in client.calls   # UL_V
    assert 'VXX:GMFI9=-00050' in client.calls   # LR_H
    assert 'VXX:GMFI5=+00005' in client.calls   # LIN_V


def test_apply_saved_settings_no_corners_section_skips_geometry():
    """Если geometry_corners не задан — режим Corner Correction не активируется."""
    responses = {}
    api, state, client = _make_api(responses)
    state.identity_attempted = True

    async def _no_settle(*args, **kwargs):
        return
    api.wait_for_lens_settle = _no_settle  # type: ignore[assignment]

    settings = {
        'lens_settings': {'h_position': '---', 'v_position': '---'},
        'display_settings': {},
    }
    asyncio.run(api.apply_saved_settings(settings))

    # set_geometry CC не должен быть отправлен
    assert 'VXX:GMMI0=+00010' not in client.calls

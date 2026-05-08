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

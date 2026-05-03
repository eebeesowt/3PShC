"""Smoke-тесты scene_repository — io роундтрип, schema_version, депрекейт TXT."""
import asyncio
import json
import os
import tempfile

import pytest

from infra.scene_repository import SCHEMA_VERSION, save_scene_to_json
from lib.projector import Projector


def _make_projector(ip="192.168.1.10", label="Stage 1"):
    return Projector(
        ip=ip, port=1024, login="admin", password="pwd", label=label, id=1
    )


def test_save_scene_writes_schema_version(tmp_path):
    path = str(tmp_path / "scene.json")
    save_scene_to_json(path, (800, 600), [(_make_projector(), 0, 0, {})])

    with open(path) as f:
        data = json.load(f)

    assert data["schema_version"] == SCHEMA_VERSION
    assert data["window_size"] == {"width": 800, "height": 600}
    assert data["projectors"][0]["ip"] == "192.168.1.10"


def test_save_scene_to_txt_is_rejected(tmp_path):
    path = str(tmp_path / "scene.txt")
    with pytest.raises(ValueError, match="TXT scene format saving"):
        save_scene_to_json(path, (800, 600), [(_make_projector(), 0, 0, {})])


def test_settings_payload_roundtrip(tmp_path):
    """Сохранённые settings круглым ходом возвращаются из JSON."""
    settings = {
        "lens_settings": {"h_position": "+00200", "v_position": "+00100"},
        "display_settings": {"aspect_ratio": "16:9", "installation_mode": "Front/Desk"},
    }
    path = str(tmp_path / "scene.json")
    save_scene_to_json(path, (1024, 768), [(_make_projector(), 5, 7, settings)])

    with open(path) as f:
        data = json.load(f)

    proj = data["projectors"][0]
    assert proj["position"] == {"x": 5, "y": 7}
    assert proj["settings"] == settings

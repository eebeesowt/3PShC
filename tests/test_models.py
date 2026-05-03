"""Smoke-тесты для core/models — никаких внешних зависимостей."""
from core.models import (
    DisplaySettings,
    LensPosition,
    ProjectorConfig,
    ProjectorEntry,
    ProjectorState,
    Scene,
)


def test_projector_config_is_frozen():
    config = ProjectorConfig(
        ip="192.168.1.10",
        port=1024,
        login="admin",
        password="pwd",
        label="Stage Left",
    )
    assert config.ip == "192.168.1.10"
    assert config.ip_room_number == "10"
    assert config.display_label == "Stage Left"


def test_projector_config_display_label_falls_back_to_ip():
    config = ProjectorConfig(
        ip="10.0.0.50", port=1024, login="a", password="b", label=""
    )
    assert config.display_label == "10.0.0.50"


def test_projector_state_defaults_are_clean():
    state = ProjectorState()
    assert state.power is None
    assert state.shutter is None
    assert state.group is False
    assert isinstance(state.lens_position, LensPosition)
    assert isinstance(state.display_settings, DisplaySettings)


def test_scene_default_schema_version_is_one():
    scene = Scene()
    assert scene.schema_version == 1
    assert scene.window_size is None
    assert scene.projectors == []


def test_projector_entry_has_default_settings():
    config = ProjectorConfig(
        ip="1.2.3.4", port=1024, login="a", password="b", label="x"
    )
    entry = ProjectorEntry(config=config, x=10, y=20)
    assert entry.settings == {}

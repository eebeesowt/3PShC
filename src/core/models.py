"""
Модели данных приложения. Чистые dataclass'ы без I/O и UI.
"""
from dataclasses import dataclass, field
from typing import Any, List, Optional, Tuple


@dataclass(frozen=True)
class ProjectorConfig:
    """Сетевые параметры подключения к проектору. Неизменяемая часть."""
    ip: str
    port: int
    login: str
    password: str
    label: str = ""

    @property
    def ip_room_number(self) -> str:
        """Последний октет IP — используется в OSC-роутинге."""
        return self.ip.split('.')[-1]

    @property
    def display_label(self) -> str:
        return self.label if self.label else self.ip


@dataclass
class LensPosition:
    """Позиция линзы в сыром формате протокола (например, '+00200')."""
    h: Optional[str] = None
    v: Optional[str] = None


@dataclass
class DisplaySettings:
    """Настройки отображения в сыром формате протокола."""
    aspect_ratio: Optional[str] = None
    installation_mode: Optional[str] = None
    test_pattern: Optional[str] = None


@dataclass
class ProjectorState:
    """
    Изменяемое состояние проектора. Single source of truth для
    Projector facade и UI.
    """
    power: Optional[bool] = None
    shutter: Optional[bool] = None
    shutter_in_time: Optional[str] = None
    shutter_out_time: Optional[str] = None
    group: bool = False
    lens_position: LensPosition = field(default_factory=LensPosition)
    display_settings: DisplaySettings = field(default_factory=DisplaySettings)
    # Идентификация (заполняется однократно при первом успешном refresh_info).
    model: Optional[str] = None
    serial: Optional[str] = None
    firmware: Optional[str] = None
    # Флаг «попытка опросить QID/QSN/SVRS уже была» — чтобы refresh_info не
    # спамил identity-запросами на устройстве, где QID всегда отвечает ER.
    identity_attempted: bool = False


@dataclass
class ProjectorEntry:
    """Запись о проекторе в сцене: конфиг + позиция на холсте + настройки."""
    config: ProjectorConfig
    x: int
    y: int
    settings: dict = field(default_factory=dict)


@dataclass
class Scene:
    """Сцена: размер окна и список проекторов с их позициями и настройками."""
    window_size: Optional[Tuple[int, int]] = None
    projectors: List[ProjectorEntry] = field(default_factory=list)
    schema_version: int = 1

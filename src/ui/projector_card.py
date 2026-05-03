"""
Карточка одного проектора в DearPyGui. Каждая — отдельное DPG-окно
(`dpg.window`) с pos=[x,y]; перемещение работает «из коробки» — DPG
позволяет таскать окна за заголовок.
"""
from typing import Callable, Optional, Tuple

import dearpygui.dearpygui as dpg

from core.constants import ProjectorStates
from services.projector import Projector
from ui.dpg_theme import ButtonThemes, Palette
from utils.logger import setup_logger

logger = setup_logger(__name__)


CARD_WIDTH = 280
CARD_HEIGHT = 165


class ProjectorCard:
    """UI-карточка проектора."""

    def __init__(
        self,
        projector: Projector,
        on_remove: Callable[["ProjectorCard"], None],
        on_open_settings: Callable[["ProjectorCard"], None],
        on_shutter: Callable[["ProjectorCard", bool], None],
        on_set_shutter_in: Callable[["ProjectorCard", str], None],
        on_set_shutter_out: Callable[["ProjectorCard", str], None],
    ) -> None:
        self.projector = projector
        self._on_remove = on_remove
        self._on_open_settings = on_open_settings
        self._on_shutter = on_shutter
        self._on_set_in = on_set_shutter_in
        self._on_set_out = on_set_shutter_out

        # DPG tags. Используем uuid чтобы не было коллизий при перезагрузке сцены.
        self.window_tag = dpg.generate_uuid()
        self._power_dot_tag = dpg.generate_uuid()
        self._status_tag = dpg.generate_uuid()
        self._group_checkbox_tag = dpg.generate_uuid()
        self._shutter_in_tag = dpg.generate_uuid()
        self._shutter_out_tag = dpg.generate_uuid()

        self._build()

    # ---- Сборка UI ----

    def _build(self) -> None:
        with dpg.window(
            label=self.projector.label,
            tag=self.window_tag,
            pos=[10, 10],
            width=CARD_WIDTH,
            height=CARD_HEIGHT,
            no_collapse=True,
            no_resize=True,
            on_close=self._handle_window_close,
        ):
            # Верхняя строка: индикатор питания + статус шаттера + ⚙
            with dpg.group(horizontal=True):
                dpg.add_text("●", tag=self._power_dot_tag, color=self._power_color())
                dpg.add_text(
                    self._status_text(),
                    tag=self._status_tag,
                    color=self._status_color(),
                )
                dpg.add_spacer(width=20)
                btn = dpg.add_button(label="Settings", callback=self._handle_settings)
                dpg.bind_item_theme(btn, ButtonThemes.get('info'))

            dpg.add_separator()

            # Кнопки шаттера
            with dpg.group(horizontal=True):
                open_btn = dpg.add_button(
                    label="Open",
                    width=120, height=34,
                    callback=lambda: self._on_shutter(self, True),
                )
                dpg.bind_item_theme(open_btn, ButtonThemes.get('primary'))
                close_btn = dpg.add_button(
                    label="Close",
                    width=120, height=34,
                    callback=lambda: self._on_shutter(self, False),
                )
                dpg.bind_item_theme(close_btn, ButtonThemes.get('danger'))

            # Время вкл/выкл шаттера
            shutter_options = [str(v) for v in ProjectorStates.SHUTTER_TIME_OPTIONS]
            with dpg.group(horizontal=True):
                dpg.add_text("In:")
                dpg.add_combo(
                    items=shutter_options,
                    default_value=str(self.projector.shutter_in_time or shutter_options[0]),
                    width=70,
                    tag=self._shutter_in_tag,
                    callback=lambda s, v: self._on_set_in(self, v),
                )
                dpg.add_text("Out:")
                dpg.add_combo(
                    items=shutter_options,
                    default_value=str(self.projector.shutter_out_time or shutter_options[0]),
                    width=70,
                    tag=self._shutter_out_tag,
                    callback=lambda s, v: self._on_set_out(self, v),
                )

            with dpg.group(horizontal=True):
                dpg.add_checkbox(label="Group", tag=self._group_checkbox_tag)
                dpg.add_spacer(width=80)
                rm_btn = dpg.add_button(
                    label="Remove",
                    callback=self._handle_remove,
                )
                dpg.bind_item_theme(rm_btn, ButtonThemes.get('danger_dark'))

    # ---- Колбэки DPG ----

    def _handle_settings(self) -> None:
        self._on_open_settings(self)

    def _handle_remove(self) -> None:
        self.destroy()
        self._on_remove(self)

    def _handle_window_close(self) -> None:
        # Кнопка × в заголовке окна — тот же путь что и Remove
        self._on_remove(self)

    # ---- Индикаторы ----

    def _power_color(self) -> tuple:
        if self.projector.power is None:
            return Palette.STATUS_UNKNOWN
        return Palette.STATUS_ON if self.projector.power else Palette.STATUS_OFF

    def _status_text(self) -> str:
        if self.projector.shutter is None:
            return "Unknown"
        return "Closed" if self.projector.shutter else "Open"

    def _status_color(self) -> tuple:
        if self.projector.shutter is None:
            return Palette.STATUS_UNKNOWN
        return Palette.STATUS_OFF if self.projector.shutter else Palette.STATUS_ON

    # ---- Public API ----

    def update_power_status(self) -> None:
        if dpg.does_item_exist(self._power_dot_tag):
            dpg.configure_item(self._power_dot_tag, color=self._power_color())

    def update_shutter_status(self) -> None:
        if dpg.does_item_exist(self._status_tag):
            dpg.configure_item(
                self._status_tag,
                default_value=self._status_text(),
                color=self._status_color(),
            )

    def show_error_status(self) -> None:
        if dpg.does_item_exist(self._status_tag):
            dpg.configure_item(self._status_tag, default_value="Error",
                               color=Palette.DANGER_DARK)

    def is_in_group(self) -> bool:
        if not dpg.does_item_exist(self._group_checkbox_tag):
            return False
        return bool(dpg.get_value(self._group_checkbox_tag))

    def get_position(self) -> Tuple[int, int]:
        if not dpg.does_item_exist(self.window_tag):
            return (0, 0)
        pos = dpg.get_item_pos(self.window_tag)
        return (int(pos[0]), int(pos[1]))

    def set_position(self, x: int, y: int) -> None:
        if dpg.does_item_exist(self.window_tag):
            dpg.set_item_pos(self.window_tag, [x, y])

    def destroy(self) -> None:
        if dpg.does_item_exist(self.window_tag):
            dpg.delete_item(self.window_tag)

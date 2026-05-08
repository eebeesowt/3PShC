"""
DearPyGui-виджеты для управления объективом. Скорость выбирается один раз
радио-переключателем; стрелки читают её через speed_provider() при клике —
так число кнопок сократилось с 21 до 9.

API колбэков сохраняем тот же (callback(speed)) — ProjectorApi ждёт
'slow'/'normal'/'fast'. direction ('plus'/'minus') зашит в имя callback.
"""
from typing import Callable

import dearpygui.dearpygui as dpg

from ui.dpg_theme import ButtonThemes


class LensSpeed:
    SLOW = 'slow'
    NORMAL = 'normal'
    FAST = 'fast'


SpeedCallback = Callable[[str], None]
SpeedProvider = Callable[[], str]


def build_speed_selector(parent: int, default: str = LensSpeed.NORMAL) -> int:
    """Сегмент выбора скорости (slow/normal/fast). Возвращает tag —
    settings_dialog читает его через dpg.get_value() и передаёт в callbacks.
    """
    tag = dpg.generate_uuid()
    with dpg.group(parent=parent, horizontal=True):
        dpg.add_text("Speed:")
        dpg.add_radio_button(
            items=[LensSpeed.SLOW, LensSpeed.NORMAL, LensSpeed.FAST],
            default_value=default,
            horizontal=True,
            tag=tag,
        )
    return tag


def build_shift_pad(
    parent: int,
    on_h_plus: SpeedCallback,
    on_h_minus: SpeedCallback,
    on_v_plus: SpeedCallback,
    on_v_minus: SpeedCallback,
    on_home: Callable[[], None],
    speed_provider: SpeedProvider,
) -> None:
    """Крест 3×3: пусто/↑/пусто, ←/Home/→, пусто/↓/пусто."""
    dpg.add_text("SHIFT", parent=parent)
    with dpg.table(parent=parent, header_row=False, no_pad_innerX=True,
                   no_pad_outerX=True, policy=dpg.mvTable_SizingFixedFit):
        for _ in range(3):
            dpg.add_table_column()

        with dpg.table_row():
            dpg.add_spacer(width=52)
            _btn(label="↑", w=52, h=40, kind='info',
                 callback=lambda: on_v_plus(speed_provider()))
            dpg.add_spacer(width=52)

        with dpg.table_row():
            _btn(label="←", w=52, h=40, kind='info',
                 callback=lambda: on_h_minus(speed_provider()))
            home_btn = dpg.add_button(label="Home", width=52, height=40,
                                      callback=lambda: on_home())
            dpg.bind_item_theme(home_btn, ButtonThemes.get('primary'))
            _btn(label="→", w=52, h=40, kind='info',
                 callback=lambda: on_h_plus(speed_provider()))

        with dpg.table_row():
            dpg.add_spacer(width=52)
            _btn(label="↓", w=52, h=40, kind='info',
                 callback=lambda: on_v_minus(speed_provider()))
            dpg.add_spacer(width=52)


def build_directional_bar(
    parent: int,
    title: str,
    left_label: str,
    right_label: str,
    on_minus: SpeedCallback,
    on_plus: SpeedCallback,
    speed_provider: SpeedProvider,
) -> None:
    """Линейка: title | left_label [-] [+] right_label."""
    with dpg.group(parent=parent, horizontal=True):
        dpg.add_text(f"{title}:")
        dpg.add_spacer(width=8)
        dpg.add_text(left_label)
        _btn(label="-", w=42, h=28, kind='success',
             callback=lambda: on_minus(speed_provider()))
        _btn(label="+", w=42, h=28, kind='success',
             callback=lambda: on_plus(speed_provider()))
        dpg.add_text(right_label)


def _btn(label: str, w: int, h: int, kind: str, callback: Callable) -> int:
    btn = dpg.add_button(label=label, width=w, height=h, callback=callback)
    dpg.bind_item_theme(btn, ButtonThemes.get(kind))
    return btn

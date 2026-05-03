"""
DearPyGui-виджеты для управления объективом: крест Shift, бары Focus и Zoom.
Каждая кнопка вызывает callback(direction, speed) — direction 'plus'/'minus',
speed 'slow'/'normal'/'fast'.
"""
from typing import Callable

import dearpygui.dearpygui as dpg

from ui.dpg_theme import ButtonThemes


class LensSpeed:
    SLOW = 'slow'
    NORMAL = 'normal'
    FAST = 'fast'


SpeedCallback = Callable[[str], None]


def build_shift_cross(
    parent: int,
    on_h_plus: SpeedCallback,
    on_h_minus: SpeedCallback,
    on_v_plus: SpeedCallback,
    on_v_minus: SpeedCallback,
    on_home: Callable[[], None],
) -> None:
    """Крест 5×5 с центральной кнопкой Home. Рисуется внутри parent."""
    dpg.add_text("SHIFT", parent=parent)

    with dpg.table(parent=parent, header_row=False, no_pad_innerX=True,
                   no_pad_outerX=True, policy=dpg.mvTable_SizingFixedFit) as table:
        for _ in range(3):
            dpg.add_table_column()

        # Row 1: empty | up-fast | empty
        with dpg.table_row():
            dpg.add_spacer(width=55)
            with dpg.group():
                _btn(parent=None, label="▲▲", w=55, h=28, kind='info',
                     callback=lambda: on_v_plus(LensSpeed.FAST))
                _btn(parent=None, label="▲", w=55, h=28, kind='info',
                     callback=lambda: on_v_plus(LensSpeed.NORMAL))
                _btn(parent=None, label="△", w=55, h=22, kind='info',
                     callback=lambda: on_v_plus(LensSpeed.SLOW))
            dpg.add_spacer(width=55)

        # Row 2: H minus row | Home | H plus row
        with dpg.table_row():
            with dpg.group(horizontal=True):
                _btn(parent=None, label="◀◀", w=40, h=55, kind='info',
                     callback=lambda: on_h_minus(LensSpeed.FAST))
                _btn(parent=None, label="◀", w=40, h=55, kind='info',
                     callback=lambda: on_h_minus(LensSpeed.NORMAL))
                _btn(parent=None, label="◁", w=30, h=55, kind='info',
                     callback=lambda: on_h_minus(LensSpeed.SLOW))
            home_btn = dpg.add_button(label="Home", width=55, height=55,
                                      callback=lambda: on_home())
            dpg.bind_item_theme(home_btn, ButtonThemes.get('primary'))
            with dpg.group(horizontal=True):
                _btn(parent=None, label="▷", w=30, h=55, kind='info',
                     callback=lambda: on_h_plus(LensSpeed.SLOW))
                _btn(parent=None, label="▶", w=40, h=55, kind='info',
                     callback=lambda: on_h_plus(LensSpeed.NORMAL))
                _btn(parent=None, label="▶▶", w=40, h=55, kind='info',
                     callback=lambda: on_h_plus(LensSpeed.FAST))

        # Row 3: empty | down stack | empty
        with dpg.table_row():
            dpg.add_spacer(width=55)
            with dpg.group():
                _btn(parent=None, label="▽", w=55, h=22, kind='info',
                     callback=lambda: on_v_minus(LensSpeed.SLOW))
                _btn(parent=None, label="▼", w=55, h=28, kind='info',
                     callback=lambda: on_v_minus(LensSpeed.NORMAL))
                _btn(parent=None, label="▼▼", w=55, h=28, kind='info',
                     callback=lambda: on_v_minus(LensSpeed.FAST))
            dpg.add_spacer(width=55)


def build_directional_bar(
    parent: int,
    title: str,
    left_label: str,
    right_label: str,
    on_minus: SpeedCallback,
    on_plus: SpeedCallback,
) -> None:
    """Линейный ряд из 6 кнопок (fast/normal/slow | slow/normal/fast)."""
    dpg.add_text(title, parent=parent)
    with dpg.group(parent=parent, horizontal=True):
        dpg.add_text(left_label)
        _btn(parent=None, label="◀◀", w=42, h=28, kind='success',
             callback=lambda: on_minus(LensSpeed.FAST))
        _btn(parent=None, label="◀", w=42, h=28, kind='success',
             callback=lambda: on_minus(LensSpeed.NORMAL))
        _btn(parent=None, label="◁", w=32, h=28, kind='success',
             callback=lambda: on_minus(LensSpeed.SLOW))
        dpg.add_spacer(width=14)
        _btn(parent=None, label="▷", w=32, h=28, kind='success',
             callback=lambda: on_plus(LensSpeed.SLOW))
        _btn(parent=None, label="▶", w=42, h=28, kind='success',
             callback=lambda: on_plus(LensSpeed.NORMAL))
        _btn(parent=None, label="▶▶", w=42, h=28, kind='success',
             callback=lambda: on_plus(LensSpeed.FAST))
        dpg.add_text(right_label)


def _btn(parent, label: str, w: int, h: int, kind: str, callback: Callable) -> int:
    """Создать кнопку с темой. parent=None — текущий контейнер DPG."""
    if parent is None:
        btn = dpg.add_button(label=label, width=w, height=h, callback=callback)
    else:
        btn = dpg.add_button(label=label, width=w, height=h,
                             callback=callback, parent=parent)
    dpg.bind_item_theme(btn, ButtonThemes.get(kind))
    return btn

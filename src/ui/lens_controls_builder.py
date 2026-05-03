"""
DEPRECATED. Re-export для обратной совместимости.
Новый код должен использовать классы из ui.lens_cross:
LensShiftCross, FocusControls, ZoomControls, LensSpeed.
"""
from ui.lens_cross import (  # noqa: F401
    FocusControls,
    LensShiftCross,
    LensSpeed,
    ZoomControls,
)


# Адаптер для legacy API LensControlsBuilder.create_*. Не использовать в новом коде.
class LensControlsBuilder:
    @staticmethod
    def create_lens_shift_cross(
        parent,
        on_shift_h_plus,
        on_shift_h_minus,
        on_shift_v_plus,
        on_shift_v_minus,
        on_lens_home,
    ):
        widget = LensShiftCross(
            parent,
            on_shift_h_plus=on_shift_h_plus,
            on_shift_h_minus=on_shift_h_minus,
            on_shift_v_plus=on_shift_v_plus,
            on_shift_v_minus=on_shift_v_minus,
            on_lens_home=on_lens_home,
        )
        widget.grid(row=0, column=0, padx=10, sticky="n")
        return widget

    @staticmethod
    def create_focus_controls(parent, on_focus_plus, on_focus_minus):
        widget = FocusControls(parent, on_minus=on_focus_minus, on_plus=on_focus_plus)
        widget.pack(pady=(0, 10))
        return widget

    @staticmethod
    def create_zoom_controls(parent, on_zoom_plus, on_zoom_minus):
        widget = ZoomControls(parent, on_minus=on_zoom_minus, on_plus=on_zoom_plus)
        widget.pack()
        return widget

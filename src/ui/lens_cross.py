"""
Виджеты управления линзой: крест Shift с Home, регулировки Focus и Zoom.
Заменяет статический LensControlsBuilder на нормальные классы CTkFrame.
"""
import customtkinter as ctk
from typing import Callable

from theme import Theme
from ui.widget_factory import WidgetFactory


class LensSpeed:
    """Скорости управления объективом."""
    SLOW = 'slow'
    NORMAL = 'normal'
    FAST = 'fast'


SpeedCallback = Callable[[str], None]


class LensShiftCross(ctk.CTkFrame):
    """Крест Lens Shift (вверх/вниз/влево/вправо) с центральной кнопкой Home."""

    def __init__(
        self,
        parent,
        on_shift_h_plus: SpeedCallback,
        on_shift_h_minus: SpeedCallback,
        on_shift_v_plus: SpeedCallback,
        on_shift_v_minus: SpeedCallback,
        on_lens_home: Callable[[], None],
        **kwargs,
    ) -> None:
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._on_shift_h_plus = on_shift_h_plus
        self._on_shift_h_minus = on_shift_h_minus
        self._on_shift_v_plus = on_shift_v_plus
        self._on_shift_v_minus = on_shift_v_minus
        self._on_lens_home = on_lens_home
        self._build()

    def _build(self) -> None:
        title = ctk.CTkLabel(self, text="↔️ SHIFT", font=Theme.FONT_NORMAL)
        title.pack(pady=(0, 5))

        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack()
        for col in (0, 1, 2):
            grid.grid_columnconfigure(col, weight=0)

        self._build_vertical_column(
            grid, row=0, callback=self._on_shift_v_plus,
            labels=(("▲\n▲", LensSpeed.FAST),
                    ("▲", LensSpeed.NORMAL),
                    ("△", LensSpeed.SLOW)),
        )

        self._build_horizontal_row(
            grid, row=1, col=0, callback=self._on_shift_h_minus,
            labels=(("◀◀", LensSpeed.FAST),
                    ("◀", LensSpeed.NORMAL),
                    ("◁", LensSpeed.SLOW)),
        )

        home_btn = WidgetFactory.create_action_button(
            grid, text="⌂", command=self._on_lens_home,
            button_type='primary', width=55, height=55,
        )
        home_btn.grid(row=1, column=1, padx=2, pady=2)

        self._build_horizontal_row(
            grid, row=1, col=2, callback=self._on_shift_h_plus,
            labels=(("▷", LensSpeed.SLOW),
                    ("▶", LensSpeed.NORMAL),
                    ("▶▶", LensSpeed.FAST)),
        )

        self._build_vertical_column(
            grid, row=2, callback=self._on_shift_v_minus,
            labels=(("▽", LensSpeed.SLOW),
                    ("▼", LensSpeed.NORMAL),
                    ("▼\n▼", LensSpeed.FAST)),
        )

    def _build_vertical_column(self, parent, row: int, callback: SpeedCallback, labels) -> None:
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.grid(row=row, column=1, padx=2, pady=2)
        for text, speed in labels:
            WidgetFactory.create_action_button(
                container, text=text,
                command=lambda s=speed: callback(s),
                button_type='info', width=35, height=55,
            ).pack(pady=1)

    def _build_horizontal_row(self, parent, row: int, col: int, callback: SpeedCallback, labels) -> None:
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.grid(row=row, column=col, padx=2, pady=2)
        for text, speed in labels:
            WidgetFactory.create_action_button(
                container, text=text,
                command=lambda s=speed: callback(s),
                button_type='info', width=55, height=35,
            ).pack(side="left", padx=1)


class _DirectionalControls(ctk.CTkFrame):
    """Базовый класс для FocusControls и ZoomControls."""
    TITLE: str = ""
    LEFT_LABEL: str = ""
    RIGHT_LABEL: str = ""

    def __init__(
        self,
        parent,
        on_minus: SpeedCallback,
        on_plus: SpeedCallback,
        **kwargs,
    ) -> None:
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._on_minus = on_minus
        self._on_plus = on_plus
        self._build()

    def _build(self) -> None:
        title = ctk.CTkLabel(self, text=self.TITLE, font=Theme.FONT_NORMAL)
        title.pack(pady=(0, 5))

        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(pady=(0, 10))

        ctk.CTkLabel(grid, text=self.LEFT_LABEL, font=Theme.FONT_NORMAL).grid(
            row=0, column=0, columnspan=3, pady=(0, 3)
        )
        ctk.CTkLabel(grid, text=self.RIGHT_LABEL, font=Theme.FONT_NORMAL).grid(
            row=0, column=3, columnspan=3, pady=(0, 3)
        )

        # Minus side: fast (col 0), normal (col 1), slow (col 2)
        for col, (text, speed) in enumerate((
            ("◀◀", LensSpeed.FAST),
            ("◀", LensSpeed.NORMAL),
            ("◁", LensSpeed.SLOW),
        )):
            WidgetFactory.create_action_button(
                grid, text=text,
                command=lambda s=speed: self._on_minus(s),
                button_type='success', width=55, height=35,
            ).grid(row=1, column=col, padx=1)

        # Plus side: slow (col 3), normal (col 4), fast (col 5)
        for offset, (text, speed) in enumerate((
            ("▷", LensSpeed.SLOW),
            ("▶", LensSpeed.NORMAL),
            ("▶▶", LensSpeed.FAST),
        )):
            WidgetFactory.create_action_button(
                grid, text=text,
                command=lambda s=speed: self._on_plus(s),
                button_type='success', width=55, height=35,
            ).grid(row=1, column=3 + offset, padx=1)


class FocusControls(_DirectionalControls):
    TITLE = "🎯 FOCUS"
    LEFT_LABEL = "◀ Near"
    RIGHT_LABEL = "Far ▶"


class ZoomControls(_DirectionalControls):
    TITLE = "🔍 ZOOM"
    LEFT_LABEL = "◀ Out"
    RIGHT_LABEL = "In ▶"

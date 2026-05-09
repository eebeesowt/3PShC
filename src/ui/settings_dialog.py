"""
Диалог настроек проектора на DearPyGui. Tabs: Lens / Source / Display / Info.
Все async-задачи запускаются через переданный run_task — обычно это
AppWindow._create_task — чтобы они отменились при общем shutdown.
"""
from typing import Any, Callable, Coroutine, Optional

import dearpygui.dearpygui as dpg

from core.constants import ProjectorStates
from infra.settings_repository import (
    load_projector_settings,
    save_projector_settings,
)
from services.projector import Projector
from ui.dpg_theme import ButtonThemes, Palette
from ui.lens_widgets import (
    LensSpeed,
    build_directional_bar,
    build_shift_pad,
    build_speed_selector,
)
from utils.logger import setup_logger

logger = setup_logger(__name__)


RunTask = Callable[[Coroutine[Any, Any, Any], str], Any]


class ProjectorSettingsDialog:
    """Окно настроек одного проектора."""

    def __init__(
        self,
        projector: Projector,
        run_task: RunTask,
        on_close: Optional[Callable[["ProjectorSettingsDialog"], None]] = None,
    ) -> None:
        self.projector = projector
        self._run_task = run_task
        self._on_close = on_close

        self.window_tag = dpg.generate_uuid()
        self._h_pos_tag = dpg.generate_uuid()
        self._v_pos_tag = dpg.generate_uuid()
        self._aspect_tag = dpg.generate_uuid()
        self._installation_tag = dpg.generate_uuid()
        self._test_pattern_tag = dpg.generate_uuid()
        self._input_tag = dpg.generate_uuid()
        self._freeze_tag = dpg.generate_uuid()
        self._osd_tag = dpg.generate_uuid()
        self._geometry_tag = dpg.generate_uuid()
        self._model_tag = dpg.generate_uuid()
        self._serial_tag = dpg.generate_uuid()
        self._firmware_tag = dpg.generate_uuid()
        self._family_tag = dpg.generate_uuid()
        self._profile_tag = dpg.generate_uuid()
        # Corner correction
        self._corner_panel_tag = dpg.generate_uuid()
        self._corner_step_tag = dpg.generate_uuid()
        self._corner_grid_tag = dpg.generate_uuid()
        # 10 read-out лейблов для текущих corner offsets (UL_V, UR_V, ..., LIN_H)
        self._corner_value_tags: dict = {
            cid: dpg.generate_uuid()
            for cid in ProjectorStates.CORNER_REGISTERS
        }
        self._speed_tag: int = 0

        self._build()
        self._refresh_all()

    def _build(self) -> None:
        with dpg.window(
            label=f"Settings: {self.projector.label}",
            tag=self.window_tag,
            modal=True,
            width=520,
            height=440,
            on_close=self.close,
        ):
            with dpg.tab_bar():
                with dpg.tab(label="Lens"):
                    self._build_lens_tab()
                with dpg.tab(label="Source"):
                    self._build_source_tab()
                with dpg.tab(label="Display"):
                    self._build_display_tab()
                with dpg.tab(label="Info"):
                    self._build_info_tab()

            dpg.add_separator()
            with dpg.group(horizontal=True):
                save_btn = dpg.add_button(label="Save Settings", width=180, height=32,
                                          callback=self._on_save_settings)
                dpg.bind_item_theme(save_btn, ButtonThemes.get('success'))
                load_btn = dpg.add_button(label="Load & Apply", width=180, height=32,
                                          callback=self._on_load_settings)
                dpg.bind_item_theme(load_btn, ButtonThemes.get('warning'))
                close_btn = dpg.add_button(label="Close", width=120, height=32,
                                           callback=self.close)
                dpg.bind_item_theme(close_btn, ButtonThemes.get('danger'))

    def _build_lens_tab(self) -> None:
        with dpg.group():
            speed_group = dpg.add_group()
            self._speed_tag = build_speed_selector(speed_group)
            dpg.add_separator()

            shift_group = dpg.add_group()
            build_shift_pad(
                shift_group,
                on_h_plus=self._on_h_plus,
                on_h_minus=self._on_h_minus,
                on_v_plus=self._on_v_plus,
                on_v_minus=self._on_v_minus,
                on_home=self._on_lens_home,
                speed_provider=self._current_speed,
            )
            dpg.add_separator()
            focus_group = dpg.add_group()
            build_directional_bar(
                focus_group, title="FOCUS",
                left_label="Near", right_label="Far",
                on_minus=self._on_focus_minus, on_plus=self._on_focus_plus,
                speed_provider=self._current_speed,
            )
            zoom_group = dpg.add_group()
            build_directional_bar(
                zoom_group, title="ZOOM",
                left_label="Out", right_label="In",
                on_minus=self._on_zoom_minus, on_plus=self._on_zoom_plus,
                speed_provider=self._current_speed,
            )

    def _current_speed(self) -> str:
        if self._speed_tag and dpg.does_item_exist(self._speed_tag):
            return dpg.get_value(self._speed_tag) or LensSpeed.NORMAL
        return LensSpeed.NORMAL

    def _build_display_tab(self) -> None:
        with dpg.group():
            dpg.add_text("Aspect Ratio")
            dpg.add_combo(
                items=["16:10", "16:9", "4:3"],
                default_value="16:9",
                tag=self._aspect_tag,
                width=140,
                callback=lambda s, v: self._set_aspect(v),
            )
            dpg.add_separator()
            dpg.add_text("Installation Mode")
            dpg.add_combo(
                items=list(ProjectorStates.INSTALLATION_MODES.keys()),
                default_value="Front/Desk",
                tag=self._installation_tag,
                width=200,
                callback=lambda s, v: self._set_installation(v),
            )
            dpg.add_separator()
            dpg.add_text("Geometry")
            dpg.add_combo(
                items=list(ProjectorStates.GEOMETRY_MODES.keys()),
                default_value="Off",
                tag=self._geometry_tag,
                width=200,
                callback=lambda s, v: self._on_geometry_change(v),
            )
            # Corner correction sub-panel — показывается только когда выбран
            # режим Corner Correction. configure_item(show=...) — DPG-способ
            # показывать/прятать без пересборки.
            with dpg.group(tag=self._corner_panel_tag, show=False):
                self._build_corner_panel()
            dpg.add_separator()
            dpg.add_text("Test Pattern")
            initial_patterns = list(
                ProjectorStates.test_patterns_for_model(
                    self.projector.model or ''
                ).keys()
            )
            dpg.add_combo(
                items=initial_patterns,
                default_value="Off",
                tag=self._test_pattern_tag,
                width=200,
                callback=lambda s, v: self._set_test_pattern(v),
            )

    def _build_source_tab(self) -> None:
        with dpg.group():
            dpg.add_text("Input Source")
            # Если модель уже известна (повторное открытие диалога) — фильтруем
            # под её input profile. Если нет — показываем все, перестроим в
            # _async_refresh_identity после QID.
            initial_items = list(
                ProjectorStates.input_sources_for_model(
                    self.projector.model or ''
                ).keys()
            )
            dpg.add_combo(
                items=initial_items,
                default_value="HDMI1",
                tag=self._input_tag,
                width=240,
                callback=lambda s, v: self._set_input(v),
            )
            dpg.add_separator()
            dpg.add_checkbox(
                label="Freeze (стоп-кадр)",
                tag=self._freeze_tag,
                callback=lambda s, v: self._set_freeze(v),
            )
            dpg.add_separator()
            # default_value=False — нейтральный pending-стейт; реальное значение
            # подтянет _async_refresh_osd. Не врём пользователю про ON.
            dpg.add_checkbox(
                label="On-Screen Display",
                tag=self._osd_tag,
                default_value=False,
                callback=lambda s, v: self._set_osd(v),
            )
            dpg.add_text(
                "OSD off — убирает меню/баннеры из проекции.",
                color=Palette.TEXT_MUTED,
            )

    def _build_corner_panel(self) -> None:
        """2x2 пэд углов + Linearity H/V + Step + чекбокс калибровочной сетки.
        Sign convention: '↑'/'←' → -step, '↓'/'→' → +step (см. constants.py).
        """
        dpg.add_text("Corner Correction", color=Palette.PRIMARY)
        with dpg.group(horizontal=True):
            dpg.add_text("Step:")
            dpg.add_radio_button(
                items=['1', '10', '50', '100'],
                default_value='10',
                tag=self._corner_step_tag,
                horizontal=True,
            )
            dpg.add_spacer(width=20)
            dpg.add_checkbox(
                label="Show test grid",
                tag=self._corner_grid_tag,
                callback=self._toggle_corner_grid,
            )

        # 2x2 углов через таблицу
        with dpg.table(header_row=False,
                       no_pad_innerX=True, no_pad_outerX=True,
                       policy=dpg.mvTable_SizingFixedFit):
            dpg.add_table_column()
            dpg.add_table_column()
            with dpg.table_row():
                self._build_corner_cell('Upper Left',  'UL')
                self._build_corner_cell('Upper Right', 'UR')
            with dpg.table_row():
                self._build_corner_cell('Lower Left',  'LL')
                self._build_corner_cell('Lower Right', 'LR')

        # Линейность
        with dpg.group(horizontal=True):
            dpg.add_text("Linearity V:")
            self._add_btn("-", lambda: self._adjust_corner('LIN_V', -1), 'info', w=32)
            self._add_btn("+", lambda: self._adjust_corner('LIN_V', +1), 'info', w=32)
            dpg.add_text(
                self._format_value(self.projector.state.corners.get('LIN_V', 0)),
                tag=self._corner_value_tags['LIN_V'],
                color=Palette.PRIMARY,
            )
            dpg.add_spacer(width=20)
            dpg.add_text("Linearity H:")
            self._add_btn("-", lambda: self._adjust_corner('LIN_H', -1), 'info', w=32)
            self._add_btn("+", lambda: self._adjust_corner('LIN_H', +1), 'info', w=32)
            dpg.add_text(
                self._format_value(self.projector.state.corners.get('LIN_H', 0)),
                tag=self._corner_value_tags['LIN_H'],
                color=Palette.PRIMARY,
            )

        reset_btn = dpg.add_button(
            label="Reset all corners",
            callback=self._reset_all_corners,
            width=180, height=26,
        )
        dpg.bind_item_theme(reset_btn, ButtonThemes.get('warning'))

    def _build_corner_cell(self, label: str, prefix: str) -> None:
        """Один угол: лейбл + 4 кнопки (V↑/V↓ и H←/H→) + текущие H/V значения."""
        v_id, h_id = f"{prefix}_V", f"{prefix}_H"
        with dpg.group():
            dpg.add_text(label, color=Palette.TEXT_PRIMARY)
            with dpg.group(horizontal=True):
                dpg.add_text("V")
                self._add_btn("↑", lambda v=v_id: self._adjust_corner(v, -1), 'info', w=32)
                self._add_btn("↓", lambda v=v_id: self._adjust_corner(v, +1), 'info', w=32)
                dpg.add_text(
                    self._format_value(self.projector.state.corners.get(v_id, 0)),
                    tag=self._corner_value_tags[v_id],
                    color=Palette.PRIMARY,
                )
            with dpg.group(horizontal=True):
                dpg.add_text("H")
                self._add_btn("←", lambda h=h_id: self._adjust_corner(h, -1), 'info', w=32)
                self._add_btn("→", lambda h=h_id: self._adjust_corner(h, +1), 'info', w=32)
                dpg.add_text(
                    self._format_value(self.projector.state.corners.get(h_id, 0)),
                    tag=self._corner_value_tags[h_id],
                    color=Palette.PRIMARY,
                )

    @staticmethod
    def _format_value(v: int) -> str:
        return f"{v:+d}"

    def _add_btn(self, label, callback, theme, w=40):
        btn = dpg.add_button(label=label, callback=callback, width=w, height=24)
        dpg.bind_item_theme(btn, ButtonThemes.get(theme))
        return btn

    def _build_info_tab(self) -> None:
        with dpg.group():
            dpg.add_text("Lens Position")
            with dpg.group(horizontal=True):
                dpg.add_text("Horizontal:")
                dpg.add_text("---", tag=self._h_pos_tag, color=Palette.PRIMARY)
            with dpg.group(horizontal=True):
                dpg.add_text("Vertical:  ")
                dpg.add_text("---", tag=self._v_pos_tag, color=Palette.PRIMARY)
            refresh = dpg.add_button(label="Refresh Position",
                                     callback=lambda: self._refresh_lens_position())
            dpg.bind_item_theme(refresh, ButtonThemes.get('warning'))

            dpg.add_separator()
            dpg.add_text("Projector Info")
            for key, value in [
                ("Label:", self.projector.label),
                ("IP:", self.projector.ip),
                ("Port:", str(self.projector.port)),
                ("Room:", self.projector.ip_room_number),
            ]:
                with dpg.group(horizontal=True):
                    dpg.add_text(key)
                    dpg.add_text(str(value), color=Palette.PRIMARY)

            with dpg.group(horizontal=True):
                dpg.add_text("Model:")
                dpg.add_text(self.projector.model or "---",
                             tag=self._model_tag, color=Palette.PRIMARY)
            with dpg.group(horizontal=True):
                dpg.add_text("Family:")
                dpg.add_text(self.projector.family,
                             tag=self._family_tag, color=Palette.PRIMARY)
            with dpg.group(horizontal=True):
                dpg.add_text("Input profile:")
                dpg.add_text(self.projector.input_profile,
                             tag=self._profile_tag, color=Palette.PRIMARY)
            with dpg.group(horizontal=True):
                dpg.add_text("Serial:")
                dpg.add_text(self.projector.serial or "---",
                             tag=self._serial_tag, color=Palette.PRIMARY)
            with dpg.group(horizontal=True):
                dpg.add_text("Firmware:")
                dpg.add_text(self.projector.firmware or "---",
                             tag=self._firmware_tag, color=Palette.PRIMARY)
            refresh_id = dpg.add_button(label="Refresh Identity",
                                        callback=lambda: self._refresh_identity())
            dpg.bind_item_theme(refresh_id, ButtonThemes.get('warning'))

    # ---- Lens callbacks ----

    def _on_lens_home(self) -> None:
        self._dispatch(self.projector.lens_home(), "lens home")

    def _on_h_plus(self, speed: str) -> None:
        self._dispatch(self.projector.lens_shift_h('plus', speed),
                       f"shift right {speed}")

    def _on_h_minus(self, speed: str) -> None:
        self._dispatch(self.projector.lens_shift_h('minus', speed),
                       f"shift left {speed}")

    def _on_v_plus(self, speed: str) -> None:
        self._dispatch(self.projector.lens_shift_v('plus', speed),
                       f"shift up {speed}")

    def _on_v_minus(self, speed: str) -> None:
        self._dispatch(self.projector.lens_shift_v('minus', speed),
                       f"shift down {speed}")

    def _on_focus_plus(self, speed: str) -> None:
        self._dispatch(self.projector.lens_focus('plus', speed),
                       f"focus far {speed}")

    def _on_focus_minus(self, speed: str) -> None:
        self._dispatch(self.projector.lens_focus('minus', speed),
                       f"focus near {speed}")

    def _on_zoom_plus(self, speed: str) -> None:
        self._dispatch(self.projector.lens_zoom('plus', speed),
                       f"zoom in {speed}")

    def _on_zoom_minus(self, speed: str) -> None:
        self._dispatch(self.projector.lens_zoom('minus', speed),
                       f"zoom out {speed}")

    def _dispatch(self, coro, name: str) -> None:
        async def _run():
            await coro
            await self._async_refresh_lens_position()
        self._run_task(_run(), f"{name} {self.projector.label}")

    # ---- Display callbacks ----

    def _set_aspect(self, value: str) -> None:
        self._run_task(
            self.projector.set_aspect_ratio(value),
            f"set aspect {self.projector.label}",
        )

    def _set_installation(self, value: str) -> None:
        self._run_task(
            self.projector.set_installation_mode(value),
            f"set installation {self.projector.label}",
        )

    def _set_test_pattern(self, value: str) -> None:
        self._run_task(
            self.projector.set_test_pattern(value),
            f"set test pattern {self.projector.label}",
        )

    def _on_geometry_change(self, value: str) -> None:
        """Сетит режим геометрии на проекторе и показывает/прячет corner pad."""
        self._run_task(
            self.projector.set_geometry(value),
            f"set geometry {self.projector.label}",
        )
        is_cc = (value == 'Corner Correction')
        if dpg.does_item_exist(self._corner_panel_tag):
            dpg.configure_item(self._corner_panel_tag, show=is_cc)
        # При активации Corner Correction подтягиваем актуальные offsets, чтобы
        # текстовые лейблы и логика +/- стартовали с реальных значений.
        if is_cc:
            self._run_task(self._async_refresh_corners(), "refresh corners")

    # ---- Corner correction handlers ----

    def _adjust_corner(self, corner_id: str, sign: int) -> None:
        """+sign шлёт абсолютное value = current + step*sign к проектору.
        Знак универсальный: ↑/← = -1, ↓/→ = +1 (см. constants.py)."""
        try:
            step = int(dpg.get_value(self._corner_step_tag))
        except (TypeError, ValueError):
            step = 10
        delta = sign * step
        current = self.projector.state.corners.get(corner_id, 0)
        new_value = current + delta

        async def _run():
            await self.projector.set_corner_offset(corner_id, new_value)
            self._update_corner_label(corner_id)

        self._run_task(
            _run(), f"corner {corner_id} {'+' if sign > 0 else '-'}{step}"
        )

    def _toggle_corner_grid(self, sender, value: bool) -> None:
        self._run_task(
            self.projector.set_corner_test_grid(value),
            f"corner grid {self.projector.label}",
        )

    def _reset_all_corners(self) -> None:
        async def _run():
            for cid in ProjectorStates.CORNER_REGISTERS:
                try:
                    await self.projector.set_corner_offset(cid, 0)
                except Exception as exc:
                    logger.warning(f"Reset {cid} failed: {exc}")
                self._update_corner_label(cid)
        self._run_task(_run(), f"reset corners {self.projector.label}")

    def _update_corner_label(self, corner_id: str) -> None:
        tag = self._corner_value_tags.get(corner_id)
        if tag is None or not dpg.does_item_exist(tag):
            return
        value = self.projector.state.corners.get(corner_id, 0)
        dpg.set_value(tag, f"{value:+d}")

    def _set_input(self, value: str) -> None:
        self._run_task(
            self.projector.set_input_source(value),
            f"set input {self.projector.label}",
        )

    def _set_freeze(self, value: bool) -> None:
        self._run_task(
            self.projector.set_freeze(value),
            f"set freeze {self.projector.label}",
        )

    def _set_osd(self, value: bool) -> None:
        self._run_task(
            self.projector.set_osd(value),
            f"set osd {self.projector.label}",
        )

    # ---- Refresh ----

    def _refresh_all(self) -> None:
        self._refresh_lens_position()
        self._run_task(self._async_refresh_aspect(), "refresh aspect")
        self._run_task(self._async_refresh_installation(), "refresh installation")
        self._run_task(self._async_refresh_test_pattern(), "refresh test pattern")
        self._run_task(self._async_refresh_input(), "refresh input")
        self._run_task(self._async_refresh_freeze(), "refresh freeze")
        self._run_task(self._async_refresh_osd(), "refresh osd")
        self._run_task(self._async_refresh_geometry(), "refresh geometry")
        # Идентичность кешируется, поэтому повторный запрос — no-op для уже
        # известных моделей. Но мы хотим обновить UI и перестроить input combo.
        self._refresh_identity()

    def _refresh_identity(self) -> None:
        self._run_task(self._async_refresh_identity(), "refresh identity")

    async def _async_refresh_identity(self) -> None:
        try:
            await self.projector.refresh_identity()
        except Exception as exc:
            logger.warning(f"Could not refresh identity: {exc}")
            return
        if dpg.does_item_exist(self._model_tag):
            dpg.set_value(self._model_tag, self.projector.model or "---")
        if dpg.does_item_exist(self._serial_tag):
            dpg.set_value(self._serial_tag, self.projector.serial or "---")
        if dpg.does_item_exist(self._firmware_tag):
            dpg.set_value(self._firmware_tag, self.projector.firmware or "---")
        if dpg.does_item_exist(self._family_tag):
            dpg.set_value(self._family_tag, self.projector.family)
        if dpg.does_item_exist(self._profile_tag):
            dpg.set_value(self._profile_tag, self.projector.input_profile)
        # После определения модели — пересобираем список входов и test-паттернов
        # под её профиль. Если текущее значение комбо ушло из нового списка —
        # сбрасываем на первый элемент, иначе DPG показывает висящий текст,
        # которого нет в дропдауне.
        if dpg.does_item_exist(self._input_tag):
            items = list(
                ProjectorStates.input_sources_for_model(
                    self.projector.model or ''
                ).keys()
            )
            dpg.configure_item(self._input_tag, items=items)
            self._reset_combo_if_orphan(self._input_tag, items)
        if dpg.does_item_exist(self._test_pattern_tag):
            patterns = list(
                ProjectorStates.test_patterns_for_model(
                    self.projector.model or ''
                ).keys()
            )
            dpg.configure_item(self._test_pattern_tag, items=patterns)
            self._reset_combo_if_orphan(self._test_pattern_tag, patterns)

    @staticmethod
    def _reset_combo_if_orphan(tag: int, items: list) -> None:
        """Если текущее value комбо отсутствует в новом items — сбрасываем
        на первый элемент. Защита от висящего текста после фильтра под профиль.
        """
        if not items or not dpg.does_item_exist(tag):
            return
        current = dpg.get_value(tag)
        if current not in items:
            dpg.set_value(tag, items[0])

    def _refresh_lens_position(self) -> None:
        self._run_task(self._async_refresh_lens_position(), "refresh lens position")

    async def _async_refresh_lens_position(self) -> None:
        try:
            h, v = await self.projector.get_lens_position()
        except Exception as exc:
            logger.warning(f"Could not read lens position: {exc}")
            return
        if dpg.does_item_exist(self._h_pos_tag):
            dpg.set_value(self._h_pos_tag, h or "---")
        if dpg.does_item_exist(self._v_pos_tag):
            dpg.set_value(self._v_pos_tag, v or "---")

    async def _async_refresh_aspect(self) -> None:
        try:
            code = await self.projector.get_aspect_ratio()
        except Exception as exc:
            logger.warning(f"Could not read aspect: {exc}")
            return
        ratio = ProjectorStates.ASPECT_RATIO_BY_CODE.get(code)
        if ratio and dpg.does_item_exist(self._aspect_tag):
            dpg.set_value(self._aspect_tag, ratio)

    async def _async_refresh_installation(self) -> None:
        try:
            code = await self.projector.get_installation_mode()
        except Exception as exc:
            logger.warning(f"Could not read installation: {exc}")
            return
        for name, c in ProjectorStates.INSTALLATION_MODES.items():
            if c == code and dpg.does_item_exist(self._installation_tag):
                dpg.set_value(self._installation_tag, name)
                return

    async def _async_refresh_test_pattern(self) -> None:
        try:
            code = await self.projector.get_test_pattern()
        except Exception as exc:
            logger.warning(f"Could not read test pattern: {exc}")
            return
        for name, c in ProjectorStates.TEST_PATTERNS.items():
            if c == code and dpg.does_item_exist(self._test_pattern_tag):
                dpg.set_value(self._test_pattern_tag, name)
                return

    async def _async_refresh_input(self) -> None:
        try:
            code = await self.projector.get_input_source()
        except Exception as exc:
            logger.warning(f"Could not read input: {exc}")
            return
        name = ProjectorStates.INPUT_SOURCE_BY_CODE.get(code)
        if name and dpg.does_item_exist(self._input_tag):
            dpg.set_value(self._input_tag, name)

    async def _async_refresh_freeze(self) -> None:
        try:
            value = await self.projector.get_freeze()
        except Exception as exc:
            logger.warning(f"Could not read freeze: {exc}")
            return
        if value is not None and dpg.does_item_exist(self._freeze_tag):
            dpg.set_value(self._freeze_tag, value)

    async def _async_refresh_osd(self) -> None:
        try:
            value = await self.projector.get_osd()
        except Exception as exc:
            logger.warning(f"Could not read osd: {exc}")
            return
        if value is not None and dpg.does_item_exist(self._osd_tag):
            dpg.set_value(self._osd_tag, value)

    async def _async_refresh_geometry(self) -> None:
        try:
            code = await self.projector.get_geometry()
        except Exception as exc:
            logger.warning(f"Could not read geometry: {exc}")
            return
        name = ProjectorStates.GEOMETRY_BY_CODE.get(code)
        if name and dpg.does_item_exist(self._geometry_tag):
            dpg.set_value(self._geometry_tag, name)
        # Если на проекторе уже Corner Correction — показываем corner pad и
        # подтягиваем актуальные offsets, чтобы +/- стартовали с правильных
        # значений.
        is_cc = (name == 'Corner Correction')
        if dpg.does_item_exist(self._corner_panel_tag):
            dpg.configure_item(self._corner_panel_tag, show=is_cc)
        if is_cc:
            await self._async_refresh_corners()

    async def _async_refresh_corners(self) -> None:
        try:
            await self.projector.get_all_corners()
        except Exception as exc:
            logger.warning(f"Could not read corners: {exc}")
            return
        for cid in ProjectorStates.CORNER_REGISTERS:
            self._update_corner_label(cid)

    # ---- Save / Load ----

    def _on_save_settings(self) -> None:
        self._run_task(self._async_save(), "save projector settings")

    async def _async_save(self) -> None:
        # Сначала обновим UI текущей позицией линзы — иначе в JSON попадёт
        # стейл-значение или '---' (если пользователь не жал Refresh).
        await self._async_refresh_lens_position()
        # Если пользователь успел закрыть окно — не пишем (теги уже удалены).
        if not dpg.does_item_exist(self.window_tag):
            logger.info(f"Save aborted for {self.projector.label}: dialog closed")
            return
        for tag in (self._h_pos_tag, self._v_pos_tag,
                    self._aspect_tag, self._installation_tag):
            if not dpg.does_item_exist(tag):
                logger.info(f"Save aborted for {self.projector.label}: tag missing")
                return
        ok = save_projector_settings(
            projector_ip=self.projector.ip,
            h_position=dpg.get_value(self._h_pos_tag),
            v_position=dpg.get_value(self._v_pos_tag),
            aspect_ratio=dpg.get_value(self._aspect_tag),
            installation_mode=dpg.get_value(self._installation_tag),
        )
        logger.info(f"Save settings {self.projector.label}: {'ok' if ok else 'fail'}")

    def _on_load_settings(self) -> None:
        self._run_task(self._async_load_apply(), "load and apply projector settings")

    async def _async_load_apply(self) -> None:
        settings = load_projector_settings(self.projector.ip)
        if settings is None:
            logger.warning(f"No saved settings for {self.projector.label}")
            return
        await self.projector.apply_saved_settings(settings)
        await self._async_refresh_lens_position()
        await self._async_refresh_aspect()
        await self._async_refresh_installation()
        logger.info(f"Settings applied for {self.projector.label}")

    def close(self) -> None:
        if dpg.does_item_exist(self.window_tag):
            dpg.delete_item(self.window_tag)
        if self._on_close is not None:
            try:
                self._on_close(self)
            except Exception as exc:
                logger.warning(f"on_close callback raised: {exc}")

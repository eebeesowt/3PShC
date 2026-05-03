"""
Диалог настроек проектора на DearPyGui. Tabs: Lens / Display / Info.
Все async-задачи запускаются через переданный run_task — обычно это
AppWindow._create_task — чтобы они отменились при общем shutdown.
"""
from typing import Any, Callable, Coroutine

import dearpygui.dearpygui as dpg

from core.constants import ProjectorStates
from infra.settings_repository import (
    load_projector_settings,
    save_projector_settings,
)
from services.projector import Projector
from ui.dpg_theme import ButtonThemes, Palette
from ui.lens_widgets import build_directional_bar, build_shift_cross
from utils.logger import setup_logger

logger = setup_logger(__name__)


RunTask = Callable[[Coroutine[Any, Any, Any], str], Any]


class ProjectorSettingsDialog:
    """Окно настроек одного проектора."""

    def __init__(self, projector: Projector, run_task: RunTask) -> None:
        self.projector = projector
        self._run_task = run_task

        self.window_tag = dpg.generate_uuid()
        self._h_pos_tag = dpg.generate_uuid()
        self._v_pos_tag = dpg.generate_uuid()
        self._aspect_tag = dpg.generate_uuid()
        self._installation_tag = dpg.generate_uuid()
        self._test_pattern_tag = dpg.generate_uuid()

        self._build()
        self._refresh_all()

    def _build(self) -> None:
        with dpg.window(
            label=f"Settings: {self.projector.label}",
            tag=self.window_tag,
            modal=True,
            width=720,
            height=560,
            on_close=self.close,
        ):
            with dpg.tab_bar():
                with dpg.tab(label="Lens"):
                    self._build_lens_tab()
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
            shift_group = dpg.add_group()
            build_shift_cross(
                shift_group,
                on_h_plus=self._on_h_plus,
                on_h_minus=self._on_h_minus,
                on_v_plus=self._on_v_plus,
                on_v_minus=self._on_v_minus,
                on_home=self._on_lens_home,
            )
            dpg.add_separator()
            focus_group = dpg.add_group()
            build_directional_bar(
                focus_group, title="FOCUS",
                left_label="Near", right_label="Far",
                on_minus=self._on_focus_minus, on_plus=self._on_focus_plus,
            )
            zoom_group = dpg.add_group()
            build_directional_bar(
                zoom_group, title="ZOOM",
                left_label="Out", right_label="In",
                on_minus=self._on_zoom_minus, on_plus=self._on_zoom_plus,
            )

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
            dpg.add_text("Test Pattern")
            dpg.add_combo(
                items=list(ProjectorStates.TEST_PATTERNS.keys()),
                default_value="Off",
                tag=self._test_pattern_tag,
                width=200,
                callback=lambda s, v: self._set_test_pattern(v),
            )

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

    # ---- Refresh ----

    def _refresh_all(self) -> None:
        self._refresh_lens_position()
        self._run_task(self._async_refresh_aspect(), "refresh aspect")
        self._run_task(self._async_refresh_installation(), "refresh installation")
        self._run_task(self._async_refresh_test_pattern(), "refresh test pattern")

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

    # ---- Save / Load ----

    def _on_save_settings(self) -> None:
        self._run_task(self._async_save(), "save projector settings")

    async def _async_save(self) -> None:
        try:
            await self.projector.get_lens_position()
        except Exception:
            pass
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

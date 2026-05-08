"""
Диалог «Add Projector» на DearPyGui. Модальное окно с полями
IP / Port / Login / Password / Label и валидацией.
"""
from typing import Callable, Optional

import dearpygui.dearpygui as dpg

from config import ProjectorConfig as ProjConfig
from services.projector import Projector
from ui.dpg_theme import ButtonThemes, Palette
from utils.logger import setup_logger
from utils.validator import Validator

logger = setup_logger(__name__)


class AddProjectorDialog:
    """Модальное окно создания нового проектора."""

    def __init__(
        self,
        on_add: Callable[[Projector], None],
        on_close: Optional[Callable[["AddProjectorDialog"], None]] = None,
    ) -> None:
        self.on_add = on_add
        self._on_close = on_close
        self.window_tag = dpg.generate_uuid()
        self._ip_tag = dpg.generate_uuid()
        self._port_tag = dpg.generate_uuid()
        self._login_tag = dpg.generate_uuid()
        self._password_tag = dpg.generate_uuid()
        self._label_tag = dpg.generate_uuid()
        self._error_tag = dpg.generate_uuid()
        self._build()

    def _build(self) -> None:
        with dpg.window(
            label="Add Projector",
            tag=self.window_tag,
            modal=True,
            no_resize=True,
            width=380,
            height=320,
            on_close=self.close,
        ):
            with dpg.group(horizontal=True):
                dpg.add_text("IP:", indent=4)
                dpg.add_input_text(tag=self._ip_tag, width=200, hint="10.0.0.10")
            with dpg.group(horizontal=True):
                dpg.add_text("Port:", indent=4)
                dpg.add_input_text(
                    tag=self._port_tag, width=200,
                    default_value=str(ProjConfig.DEFAULT_PORT),
                )
            with dpg.group(horizontal=True):
                dpg.add_text("Login:", indent=4)
                dpg.add_input_text(tag=self._login_tag, width=200,
                                   default_value="admin1")
            with dpg.group(horizontal=True):
                dpg.add_text("Password:", indent=4)
                dpg.add_input_text(tag=self._password_tag, width=200,
                                   default_value="panasonic", password=True)
            with dpg.group(horizontal=True):
                dpg.add_text("Label:", indent=4)
                dpg.add_input_text(tag=self._label_tag, width=200,
                                   hint="(optional)")

            dpg.add_separator()
            dpg.add_text("", tag=self._error_tag, color=Palette.DANGER_DARK)

            with dpg.group(horizontal=True):
                add_btn = dpg.add_button(label="Add", width=160, height=32,
                                         callback=self._submit)
                dpg.bind_item_theme(add_btn, ButtonThemes.get('primary'))
                cancel_btn = dpg.add_button(label="Cancel", width=160, height=32,
                                            callback=self.close)
                dpg.bind_item_theme(cancel_btn, ButtonThemes.get('danger'))

    def _submit(self) -> None:
        ip = dpg.get_value(self._ip_tag).strip()
        port_str = dpg.get_value(self._port_tag).strip()
        login = dpg.get_value(self._login_tag).strip()
        password = dpg.get_value(self._password_tag)
        label = dpg.get_value(self._label_tag).strip()

        ok, err = Validator.validate_ip(ip)
        if not ok:
            self._show_error(err or "Invalid IP")
            return
        ok, err, port = Validator.validate_port(port_str)
        if not ok:
            self._show_error(err or "Invalid port")
            return
        ok, err = Validator.validate_required(login, "Login")
        if not ok:
            self._show_error(err or "Login required")
            return

        try:
            projector = Projector(
                ip=ip, port=port, login=login, password=password,
                label=label or ip, id=0,
            )
        except Exception as exc:
            logger.error(f"Could not create projector: {exc}")
            self._show_error(str(exc))
            return

        self.on_add(projector)
        self.close()

    def _show_error(self, msg: str) -> None:
        if dpg.does_item_exist(self._error_tag):
            dpg.set_value(self._error_tag, msg)

    def close(self) -> None:
        if dpg.does_item_exist(self.window_tag):
            dpg.delete_item(self.window_tag)
        if self._on_close is not None:
            try:
                self._on_close(self)
            except Exception as exc:
                logger.warning(f"on_close callback raised: {exc}")

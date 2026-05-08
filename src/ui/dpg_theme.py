"""
DearPyGui-темы и палитра. Заменяет CustomTkinter-тему на нативные
mvThemeColor/mvThemeStyle. Создаются один раз при старте приложения.
"""
import os
import sys
from typing import List, Optional

import dearpygui.dearpygui as dpg

from utils.logger import setup_logger

logger = setup_logger(__name__)


class Palette:
    """RGBA-палитра в формате DPG (кортежи 0–255)."""
    BACKGROUND = (35, 35, 40, 255)
    SURFACE = (50, 50, 56, 255)
    SURFACE_ALT = (60, 60, 68, 255)
    BORDER = (80, 80, 88, 255)

    PRIMARY = (4, 167, 119, 255)
    PRIMARY_HOVER = (3, 143, 102, 255)
    DANGER = (220, 117, 143, 255)
    DANGER_HOVER = (197, 104, 126, 255)
    DANGER_DARK = (242, 67, 51, 255)
    DANGER_DARK_HOVER = (217, 59, 43, 255)
    SUCCESS = (114, 155, 121, 255)
    SUCCESS_HOVER = (101, 138, 108, 255)
    SUCCESS_DARK = (93, 156, 89, 255)
    SUCCESS_DARK_HOVER = (79, 135, 76, 255)
    INFO = (113, 169, 247, 255)
    INFO_HOVER = (96, 152, 222, 255)
    WARNING = (255, 219, 181, 255)
    WARNING_HOVER = (255, 228, 196, 255)

    TEXT_PRIMARY = (235, 235, 240, 255)
    TEXT_SECONDARY = (20, 20, 22, 255)
    TEXT_MUTED = (150, 150, 158, 255)

    STATUS_ON = (76, 209, 55, 255)
    STATUS_OFF = (220, 60, 60, 255)
    STATUS_UNKNOWN = (130, 130, 138, 255)


def install_global_theme() -> int:
    """Создать и применить глобальную тему. Возвращает её id."""
    with dpg.theme() as theme_id:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, Palette.BACKGROUND)
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg, Palette.SURFACE)
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, Palette.SURFACE_ALT)
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, Palette.BORDER)
            dpg.add_theme_color(dpg.mvThemeCol_Border, Palette.BORDER)
            dpg.add_theme_color(dpg.mvThemeCol_Text, Palette.TEXT_PRIMARY)
            dpg.add_theme_color(dpg.mvThemeCol_TextDisabled, Palette.TEXT_MUTED)
            dpg.add_theme_color(dpg.mvThemeCol_TitleBg, Palette.SURFACE_ALT)
            dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, Palette.PRIMARY)
            dpg.add_theme_color(dpg.mvThemeCol_Header, Palette.PRIMARY)
            dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, Palette.PRIMARY_HOVER)
            dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, Palette.PRIMARY_HOVER)
            dpg.add_theme_color(dpg.mvThemeCol_Button, Palette.SURFACE_ALT)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, Palette.BORDER)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, Palette.PRIMARY)
            dpg.add_theme_color(dpg.mvThemeCol_Tab, Palette.SURFACE_ALT)
            dpg.add_theme_color(dpg.mvThemeCol_TabHovered, Palette.PRIMARY_HOVER)
            dpg.add_theme_color(dpg.mvThemeCol_TabActive, Palette.PRIMARY)
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 4.0)
            dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 6.0)
            dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 6.0)
            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 8, 4)
            dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 8, 6)
    dpg.bind_theme(theme_id)
    return theme_id


def make_button_theme(fg: tuple, hover: tuple, text: tuple = Palette.TEXT_PRIMARY) -> int:
    """Создать тему отдельной кнопки с заданными цветами."""
    with dpg.theme() as theme_id:
        with dpg.theme_component(dpg.mvButton):
            dpg.add_theme_color(dpg.mvThemeCol_Button, fg)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, hover)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, hover)
            dpg.add_theme_color(dpg.mvThemeCol_Text, text)
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 4.0)
    return theme_id


class ButtonThemes:
    """Лениво созданные темы кнопок. Доступ только после create_context()."""
    _cache: dict = {}

    @classmethod
    def get(cls, kind: str) -> int:
        if kind in cls._cache:
            return cls._cache[kind]
        recipe = {
            'primary': (Palette.PRIMARY, Palette.PRIMARY_HOVER, Palette.TEXT_PRIMARY),
            'danger': (Palette.DANGER, Palette.DANGER_HOVER, Palette.TEXT_PRIMARY),
            'danger_dark': (Palette.DANGER_DARK, Palette.DANGER_DARK_HOVER, Palette.TEXT_PRIMARY),
            'success': (Palette.SUCCESS, Palette.SUCCESS_HOVER, Palette.TEXT_PRIMARY),
            'success_dark': (Palette.SUCCESS_DARK, Palette.SUCCESS_DARK_HOVER, Palette.TEXT_PRIMARY),
            'info': (Palette.INFO, Palette.INFO_HOVER, Palette.TEXT_PRIMARY),
            'warning': (Palette.WARNING, Palette.WARNING_HOVER, Palette.TEXT_SECONDARY),
        }[kind]
        theme_id = make_button_theme(*recipe)
        cls._cache[kind] = theme_id
        return theme_id

    @classmethod
    def reset(cls) -> None:
        """Очистить кэш — обязательно при destroy_context()."""
        cls._cache.clear()


# ---- Шрифт ----

def _font_candidates() -> List[str]:
    """Кандидаты системных TTF с поддержкой стрелок и кириллицы."""
    if sys.platform == "darwin":
        return [
            "/System/Library/Fonts/SFNS.ttf",
            "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
            "/System/Library/Fonts/Geneva.ttf",
        ]
    if sys.platform == "win32":
        return [
            "C:/Windows/Fonts/segoeui.ttf",
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/tahoma.ttf",
        ]
    return [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/TTF/DejaVuSans.ttf",
    ]


def install_default_font(size: int = 16) -> Optional[int]:
    """Загрузить TTF с глифами стрелок (U+2190–21FF), геометрических фигур
    (U+25A0–25FF) и кириллицы. DPG по умолчанию подгружает только Latin, поэтому
    дополнительные диапазоны нужно регистрировать явно — иначе ↑↓←→ и кириллица
    рендерятся как «?».
    """
    path = next((p for p in _font_candidates() if os.path.exists(p)), None)
    if path is None:
        logger.warning("No system TTF found; arrows and Cyrillic will render as '?'")
        return None

    with dpg.font_registry():
        with dpg.font(path, size) as font_id:
            dpg.add_font_range_hint(dpg.mvFontRangeHint_Default)
            dpg.add_font_range_hint(dpg.mvFontRangeHint_Cyrillic)
            dpg.add_font_range(0x2190, 0x21FF)  # arrows
            dpg.add_font_range(0x2500, 0x25FF)  # box drawing + geometric (●▲▼)
    dpg.bind_font(font_id)
    logger.info(f"Loaded UI font: {path}")
    return font_id

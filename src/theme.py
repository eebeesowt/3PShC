"""
Система тем и цветов для приложения.
Централизованное управление стилями CustomTkinter.
"""


class Theme:
    """Цветовая схема приложения"""
    
    # Основные цвета
    PRIMARY = "#04A777"
    PRIMARY_HOVER = "#038f66"
    
    DANGER = "#DC758F"
    DANGER_HOVER = "#c5687e"
    
    DANGER_DARK = "#F24333"
    DANGER_DARK_HOVER = "#d93b2b"
    
    WARNING = "#FFDBB5"
    WARNING_HOVER = "#ffe4c4"
    
    INFO = "#71A9F7"
    INFO_HOVER = "#6098de"
    
    SUCCESS = "#729B79"
    SUCCESS_HOVER = "#658a6c"
    
    SUCCESS_DARK = "#5D9C59"
    SUCCESS_DARK_HOVER = "#4f874c"
    
    DARK = "#14453D"
    DARK_HOVER = "#103932"
    
    ERROR_BG = "#DF2E38"
    ERROR_HOVER = "#c52730"
    
    # Фон и границы
    BACKGROUND = "#363537"
    CANVAS_BG = "#938BA1"
    
    # Текст
    TEXT_PRIMARY = "white"
    TEXT_SECONDARY = "black"
    TEXT_GRAY = "gray"
    
    # Индикаторы состояния
    STATUS_ONLINE = "green"
    STATUS_OFFLINE = "red"
    STATUS_UNKNOWN = "gray"
    STATUS_ERROR = "#000000"
    
    # Статусы питания
    POWER_ON_COLOR = "green"
    POWER_OFF_COLOR = "red"
    POWER_UNKNOWN_COLOR = "gray"
    
    # Статусы шаттера
    SHUTTER_OPEN_COLOR = "green"
    SHUTTER_CLOSED_COLOR = "red"
    SHUTTER_UNKNOWN_COLOR = "gray"
    
    # Шрифты
    FONT_TITLE = ("Helvetica", 12, "bold")
    FONT_NORMAL = ("Helvetica", 10)
    FONT_STATUS = ("Arial", 10)


class AppConfig:
    """Настройки приложения"""
    
    # Размеры окна
    WINDOW_WIDTH = 566
    WINDOW_HEIGHT = 400
    WINDOW_TITLE = "3P Shutter Control"
    
    # Размеры виджетов
    BUTTON_WIDTH_SMALL = 30
    BUTTON_WIDTH_MEDIUM = 60
    BUTTON_WIDTH_NORMAL = 100
    BUTTON_WIDTH_LARGE = 120
    BUTTON_WIDTH_XLARGE = 150
    
    BUTTON_HEIGHT_SMALL = 25
    BUTTON_HEIGHT_NORMAL = 28
    
    # Отступы
    PADDING_SMALL = 2
    PADDING_MEDIUM = 5
    PADDING_LARGE = 10
    
    # Позиционирование проекторов
    PROJECTOR_OFFSET_X = 10
    PROJECTOR_OFFSET_Y = 10
    PROJECTOR_SPACING_X = 250
    PROJECTOR_SPACING_Y = 100
    
    # Сетка
    GRID_IPADX = 7
    GRID_IPADY = 7

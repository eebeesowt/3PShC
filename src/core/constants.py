"""
Константы протокола Panasonic и параметры приложения.
Чистый модуль без зависимостей от I/O или UI.
"""


class ProjectorCommands:
    """Команды управления проектором"""

    # Команды питания
    POWER_ON = 'PON'
    POWER_OFF = 'POF'
    QUERY_POWER = 'QPW'

    # Команды шаттера
    SHUTTER_OPEN = 'OSH:0'
    SHUTTER_CLOSE = 'OSH:1'
    QUERY_SHUTTER = 'QSH'

    # Команды времени шаттера
    QUERY_SHUTTER_IN = 'QVX:SEFS1'
    QUERY_SHUTTER_OUT = 'QVX:SEFS2'
    SET_SHUTTER_IN = 'VXX:SEFS1={}'
    SET_SHUTTER_OUT = 'VXX:SEFS2={}'

    # Команды управления объективом (Lens)
    LENS_HOME = 'VXX:LNSI1=+00001'

    # Lens Shift Horizontal
    LENS_SHIFT_H_SLOW_PLUS = 'VXX:LNSI2=+00000'
    LENS_SHIFT_H_SLOW_MINUS = 'VXX:LNSI2=+00001'
    LENS_SHIFT_H_NORMAL_PLUS = 'VXX:LNSI2=+00100'
    LENS_SHIFT_H_NORMAL_MINUS = 'VXX:LNSI2=+00101'
    LENS_SHIFT_H_FAST_PLUS = 'VXX:LNSI2=+00200'
    LENS_SHIFT_H_FAST_MINUS = 'VXX:LNSI2=+00201'

    # Lens Shift Vertical
    LENS_SHIFT_V_SLOW_PLUS = 'VXX:LNSI3=+00000'
    LENS_SHIFT_V_SLOW_MINUS = 'VXX:LNSI3=+00001'
    LENS_SHIFT_V_NORMAL_PLUS = 'VXX:LNSI3=+00100'
    LENS_SHIFT_V_NORMAL_MINUS = 'VXX:LNSI3=+00101'
    LENS_SHIFT_V_FAST_PLUS = 'VXX:LNSI3=+00200'
    LENS_SHIFT_V_FAST_MINUS = 'VXX:LNSI3=+00201'

    # Lens Focus
    LENS_FOCUS_SLOW_PLUS = 'VXX:LNSI4=+00000'
    LENS_FOCUS_SLOW_MINUS = 'VXX:LNSI4=+00001'
    LENS_FOCUS_NORMAL_PLUS = 'VXX:LNSI4=+00100'
    LENS_FOCUS_NORMAL_MINUS = 'VXX:LNSI4=+00101'
    LENS_FOCUS_FAST_PLUS = 'VXX:LNSI4=+00200'
    LENS_FOCUS_FAST_MINUS = 'VXX:LNSI4=+00201'

    # Lens Zoom
    LENS_ZOOM_SLOW_PLUS = 'VXX:LNSI5=+00000'
    LENS_ZOOM_SLOW_MINUS = 'VXX:LNSI5=+00001'
    LENS_ZOOM_NORMAL_PLUS = 'VXX:LNSI5=+00100'
    LENS_ZOOM_NORMAL_MINUS = 'VXX:LNSI5=+00101'
    LENS_ZOOM_FAST_PLUS = 'VXX:LNSI5=+00200'
    LENS_ZOOM_FAST_MINUS = 'VXX:LNSI5=+00201'

    # Lens Position Queries and Set
    QUERY_LENS_H_POSITION = 'QVX:LNSI7'
    QUERY_LENS_V_POSITION = 'QVX:LNSI8'
    QUERY_LENS_POSITION_HV = 'QVX:LNSSB'
    SET_LENS_H_POSITION = 'VXX:LNSI7={}'
    SET_LENS_V_POSITION = 'VXX:LNSI8={}'
    SET_LENS_POSITION_HV = 'VXX:LNSSB={}'

    # Screen Setting - Aspect Ratio
    QUERY_ASPECT_RATIO = 'QSF'
    SET_ASPECT_RATIO_16_10 = 'VSP:0'
    SET_ASPECT_RATIO_16_9 = 'VSP:1'
    SET_ASPECT_RATIO_4_3 = 'VSP:2'

    # Test Pattern
    QUERY_TEST_PATTERN = 'QTS'
    SET_TEST_PATTERN = 'OTS:{}'
    TEST_PATTERN_OFF = 'OTS:00'
    TEST_PATTERN_WHITE = 'OTS:01'
    TEST_PATTERN_BLACK = 'OTS:02'
    TEST_PATTERN_WINDOW = 'OTS:05'
    TEST_PATTERN_REVERSED_WINDOW = 'OTS:06'
    TEST_PATTERN_CROSS_HATCH = 'OTS:07'
    TEST_PATTERN_COLOR_BAR_V = 'OTS:08'
    TEST_PATTERN_CONVERGENCE = 'OTS:11'
    TEST_PATTERN_COLOR_BAR_SIDE = 'OTS:51'
    TEST_PATTERN_16_9_4_3 = 'OTS:59'
    TEST_PATTERN_FOCUS_RED = 'OTS:70'
    TEST_PATTERN_FOCUS_GREEN = 'OTS:71'
    TEST_PATTERN_FOCUS_BLUE = 'OTS:72'
    TEST_PATTERN_FOCUS_CYAN = 'OTS:73'
    TEST_PATTERN_FOCUS_MAGENTA = 'OTS:74'
    TEST_PATTERN_FOCUS_YELLOW = 'OTS:75'
    TEST_PATTERN_FOCUS = 'OTS:78'

    # Projection Method & Installation
    QUERY_INSTALLATION = 'QSP'
    SET_INSTALLATION = 'OIL:{}'


class ProjectorResponses:
    """Ответы проектора"""

    POWER_ON = '001'
    POWER_OFF = '000'

    SHUTTER_OPEN = '0'
    SHUTTER_CLOSED = '1'

    TIMEOUT = 'Timeout'


class ProjectorProtocol:
    """Параметры низкоуровневого протокола"""

    PADDING_CHAR = chr(48)
    TERMINATOR = chr(13)

    DEFAULT_TIMEOUT = 2
    INITIAL_BUFFER_SIZE = 1024
    RESPONSE_BUFFER_SIZE = 21

    # Polling-параметры для apply_saved_settings.
    # Заменяет старый open-loop sleep(12) — ждём, пока два последовательных
    # запроса позиции линзы вернут одно и то же значение, либо до таймаута.
    LENS_HOME_SETTLE_MAX_SECONDS = 15.0
    LENS_HOME_POLL_INTERVAL = 1.0


class ProjectorStates:
    """Состояния проектора и опции"""

    SHUTTER_OPEN = False
    SHUTTER_CLOSED = True

    SHUTTER_TIME_OPTIONS = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5,
                            3.0, 3.5, 4.0, 5.0, 7.0, 10.0]

    TEST_PATTERNS = {
        'Off': '00',
        'White': '01',
        'Black': '02',
        'Window': '05',
        'Reversed Window': '06',
        'Cross Hatch': '07',
        'Color Bar V': '08',
        'Convergence': '11',
        'Color Bar Side': '51',
        '16:9/4:3': '59',
        'Focus Red': '70',
        'Focus Green': '71',
        'Focus Blue': '72',
        'Focus Cyan': '73',
        'Focus Magenta': '74',
        'Focus Yellow': '75',
        'Focus': '78',
    }

    INSTALLATION_MODES = {
        'Front/Desk': '0',
        'Rear/Desk': '1',
        'Front/Ceiling': '2',
        'Rear/Ceiling': '3',
        'Front/Auto': '4',
        'Rear/Auto': '5',
    }

    ASPECT_RATIO_BY_CODE = {'0': '16:10', '1': '16:9', '2': '4:3'}


class OSCMessages:
    """Типы OSC сообщений"""

    MESSAGE_TYPE_BUTTON = 3

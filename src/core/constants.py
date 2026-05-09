"""
Константы протокола Panasonic и параметры приложения.
Чистый модуль без зависимостей от I/O или UI.
"""
import re


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
    SET_ASPECT_RATIO_16_10 = 'VSF:0'
    SET_ASPECT_RATIO_16_9 = 'VSF:1'
    SET_ASPECT_RATIO_4_3 = 'VSF:2'

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

    # Input Select (IIS:*) и query
    QUERY_INPUT = 'QIN'
    SET_INPUT = 'IIS:{}'

    # Freeze (стоп-кадр)
    QUERY_FREEZE = 'QFZ'
    FREEZE_OFF = 'OFZ:0'
    FREEZE_ON = 'OFZ:1'

    # On Screen Display
    QUERY_OSD = 'QOS'
    OSD_OFF = 'OOS:0'
    OSD_ON = 'OOS:1'

    # Geometry (VXX:GMMI0): off / keystone / curved / corner correction
    QUERY_GEOMETRY = 'QVX:GMMI0'
    SET_GEOMETRY = 'VXX:GMMI0={}'

    # Corner correction — set/query шаблоны для VXX:GMFI{1..A}.
    # Конкретные регистры — в ProjectorStates.CORNER_REGISTERS.
    SET_CORNER = 'VXX:{reg}={val}'
    QUERY_CORNER = 'QVX:{reg}'
    # Calibration test grid поверх изображения (VXX:GMCIA=+00000/+00001).
    QUERY_CORNER_TESTGRID = 'QVX:GMCIA'
    CORNER_TESTGRID_OFF = 'VXX:GMCIA=+00000'
    CORNER_TESTGRID_ON = 'VXX:GMCIA=+00001'

    # Идентификация — общий callback во всех PDF (RZ120 / RQ25K / RQ7-series).
    QUERY_MODEL = 'QID'           # → 'RZ120', 'RQ25K', 'SRQ25KC', 'RQ7L', ...
    QUERY_SERIAL = 'QSN'          # → 'SW0101234'
    # Firmware: RZ120/RQ25K знают SVRS0; RQ7-series — только SVRSE; RQ25K знает
    # оба. ProjectorApi.refresh_identity() пробует SVRS0, при ER — SVRSE.
    QUERY_FIRMWARE_MAIN = 'QVX:SVRS0'      # main firmware на RZ/RQ25K
    QUERY_FIRMWARE_GENERIC = 'QVX:SVRSE'   # единый ответ на RQ7-series


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
    # 256 хватает для самых длинных типовых ответов: firmware-строка
    # 'SVRS0=01.05.00/01.04.01' (~24 байт) + headers, lens-position
    # 'LNSSB=-02480-03200', сериийник 'SW0101234'. 21-байтовый буфер
    # обрезал firmware на старых ревизиях прошивки.
    RESPONSE_BUFFER_SIZE = 256

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

    # Универсальные паттерны (есть на всех 3 ревизиях PDF) + профиль-специфичные.
    # 'Convergence' (OTS:11) — есть только на RZ120; на RQ25K/RQ7 проектор
    # ответит ER401. 'Focus Level *' (OTS:32/33/34) — есть только на RQ25K и
    # RQ7-series. Фильтрация — через test_patterns_for_model().
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
        'Focus Level 0%': '32',
        'Focus Level 50%': '33',
        'Focus Level 100%': '34',
    }
    _TEST_PATTERN_RZ_ONLY = {'Convergence'}
    _TEST_PATTERN_MODERN_ONLY = {'Focus Level 0%', 'Focus Level 50%', 'Focus Level 100%'}

    INSTALLATION_MODES = {
        'Front/Desk': '0',
        'Rear/Desk': '1',
        'Front/Ceiling': '2',
        'Rear/Ceiling': '3',
        'Front/Auto': '4',
        'Rear/Auto': '5',
    }

    ASPECT_RATIO_BY_CODE = {'0': '16:10', '1': '16:9', '2': '4:3'}

    # Источники сигнала. Имена в комбо UI → сабкод протокола (после IIS:).
    # Реальная развилка проходит не по серии (RZ vs RQ), а по «стилю входов»:
    #   - DIRECT: классические входы напрямую (PT-RZ120, PT-RZ970, PT-RQ7L,
    #     PT-RQ22K, PT-RQ32K, PT-RQ50K и др.) — IIS:HD1, IIS:SD1, IIS:DL1.
    #   - SDM:    SDM-слот, появился в линейке 2022-2023 (PT-RQ25K/RQ18K/RZ24K
    #     /RZ17K и SRQ/SRZ-варианты) — IIS:DM1,SD1 / DM1,DL1 / DM1,WP1 / TP1.
    # Если выбрать «не свой» вход, проектор ответит ER401, в логе будет видно.
    INPUT_SOURCES = {
        # Universal — есть и в DIRECT, и в SDM
        'HDMI1': 'HD1',
        'HDMI2': 'HD2',
        'DisplayPort': 'DP1',
        # DIRECT-style (RZ120, RZ970, RQ7L, RQ22K, RQ32K, RQ50K, …)
        'SDI1 (direct)': 'SD1',
        'Digital Link (direct)': 'DL1',
        'DVI-D (direct)': 'DVI',
        'COMPUTER1/RGB1 (direct)': 'RG1',
        'COMPUTER2/RGB2 (direct)': 'RG2',
        # SDM SLOT (RQ25K/RQ18K/RZ24K/RZ17K и SR*-варианты)
        'SLOT: 12G SDI (SDM)': 'DM1,SD1',
        'SLOT: Digital Link (SDM)': 'DM1,DL1',
        'SLOT: PressIT (SDM)': 'DM1,WP1',
        'SLOT: 3rd Party (SDM)': 'DM1,TP1',
    }
    INPUT_SOURCE_BY_CODE = {code: name for name, code in INPUT_SOURCES.items()}

    # Geometry mode для VXX:GMMI0 (только наиболее ходовые в полевой работе).
    GEOMETRY_MODES = {
        'Off': '+00000',
        'Keystone': '+00001',
        'Curved': '+00002',
        'Corner Correction': '+00010',
    }
    GEOMETRY_BY_CODE = {code: name for name, code in GEOMETRY_MODES.items()}

    # Corner correction registers (VXX:GMFI{1..A}). Sign convention: «+» во ВСЕХ
    # регистрах двигает соответствующий угол ВНИЗ (для V) или ВПРАВО (для H);
    # «-» — наоборот. Поэтому UI-кнопки ↑/↓/←/→ дают -/+ независимо от угла.
    # Допустимые диапазоны различаются по моделям (RZ120 ±300, RQ7 до ±960
    # на H), поэтому клиппинг — на стороне проектора (он ответит ER при
    # выходе за диапазон).
    CORNER_REGISTERS = {
        'UL_V': 'GMFI1',  # Upper Left vertical
        'UR_V': 'GMFI2',  # Upper Right vertical
        'LL_V': 'GMFI3',  # Lower Left vertical
        'LR_V': 'GMFI4',  # Lower Right vertical
        'LIN_V': 'GMFI5', # Linearity vertical
        'UL_H': 'GMFI6',  # Upper Left horizontal
        'UR_H': 'GMFI7',  # Upper Right horizontal
        'LL_H': 'GMFI8',  # Lower Left horizontal
        'LR_H': 'GMFI9',  # Lower Right horizontal
        'LIN_H': 'GMFIA', # Linearity horizontal
    }

    # Семьи моделей — для отображения в Info-табе. Не используется для
    # фильтрации входов (см. INPUT_PROFILE_* ниже): для входов важна не серия,
    # а модельный ряд (RZ24K с SDM ≠ RZ120 без SDM).
    FAMILY_RZ = 'RZ'
    FAMILY_RQ = 'RQ'
    FAMILY_UNKNOWN = 'unknown'

    @classmethod
    def detect_family(cls, model: str) -> str:
        """'RZ' / 'RQ' / 'unknown' — высокоуровневая метка для UI."""
        if not model:
            return cls.FAMILY_UNKNOWN
        m = model.upper()
        if 'RQ' in m:
            return cls.FAMILY_RQ
        if 'RZ' in m:
            return cls.FAMILY_RZ
        return cls.FAMILY_UNKNOWN

    # ---- Input profiles ----
    # Реальный набор входов зависит не от RZ/RQ, а от поколения железа:
    #
    #   DIRECT_RZ — классические прямые входы. Семейства:
    #       PT-RZ120, PT-RZ970, PT-RQ22K, PT-RQ32K, PT-RQ50K, PT-RQ13K и др.
    #       Имеют HDMI direct, SDI direct, DL direct, DVI, RGB1/RGB2.
    #
    #   SDM_RQ25 — все входы только через SDM-слот. Серия 2022-2023:
    #       PT-RQ25K, PT-RQ18K, PT-RZ24K, PT-RZ17K и SR-варианты.
    #       PDF: rq25k_series_command_en_cn_ja.pdf
    #
    #   HYBRID_RQ7 — гибрид: HDMI и Digital Link напрямую + SDM-слот.
    #       PT-RZ7/RZ6/RQ7/RQ6 (включая суффиксы L/LBEJ и т.п.).
    #       PDF: PT-RQ7_series_command_en_cn_ja.pdf
    #
    #   UNKNOWN — неизвестная модель: показываем весь список.
    PROFILE_DIRECT_RZ = 'DIRECT_RZ'
    PROFILE_SDM_RQ25 = 'SDM_RQ25'
    PROFILE_HYBRID_RQ7 = 'HYBRID_RQ7'
    PROFILE_UNKNOWN = 'UNKNOWN'

    INPUT_PROFILES = {
        PROFILE_DIRECT_RZ: [
            'HDMI1', 'HDMI2',
            'SDI1 (direct)', 'Digital Link (direct)',
            'DVI-D (direct)',
            'COMPUTER1/RGB1 (direct)', 'COMPUTER2/RGB2 (direct)',
        ],
        PROFILE_SDM_RQ25: [
            'HDMI1', 'HDMI2', 'DisplayPort',
            'SLOT: 12G SDI (SDM)', 'SLOT: Digital Link (SDM)',
            'SLOT: PressIT (SDM)', 'SLOT: 3rd Party (SDM)',
        ],
        PROFILE_HYBRID_RQ7: [
            'HDMI1', 'HDMI2',
            'Digital Link (direct)',
            'SLOT: 12G SDI (SDM)', 'SLOT: Digital Link (SDM)',
            'SLOT: PressIT (SDM)', 'SLOT: 3rd Party (SDM)',
        ],
        # PROFILE_UNKNOWN заполняется в input_sources_for_model — все ключи.
    }

    # Порядок важен: сначала самые специфичные (с явными цифрами модельного ряда).
    _PROFILE_PATTERNS = [
        (PROFILE_SDM_RQ25, re.compile(r'(?<![0-9])(?:RQ25|RQ18|RZ24|RZ17)(?![0-9])', re.I)),
        (PROFILE_HYBRID_RQ7, re.compile(r'(?<![0-9])(?:R[QZ][67])(?![0-9])', re.I)),
        (PROFILE_DIRECT_RZ, re.compile(r'R[QZ]\d+', re.I)),
    ]

    @classmethod
    def detect_input_profile(cls, model: str) -> str:
        """Определить профиль входов по строке от QID.
        Принимает 'RZ120', 'RQ25K', 'SRQ25KC', 'RQ7L', 'RQ7LBEJ', etc.
        """
        if not model:
            return cls.PROFILE_UNKNOWN
        for profile, regex in cls._PROFILE_PATTERNS:
            if regex.search(model):
                return profile
        return cls.PROFILE_UNKNOWN

    @classmethod
    def input_sources_for_model(cls, model: str) -> dict:
        """Вернуть словарь {имя: код} для модели. Неизвестная модель → все входы."""
        profile = cls.detect_input_profile(model)
        if profile == cls.PROFILE_UNKNOWN:
            return dict(cls.INPUT_SOURCES)
        names = cls.INPUT_PROFILES[profile]
        return {n: cls.INPUT_SOURCES[n] for n in names if n in cls.INPUT_SOURCES}

    @classmethod
    def test_patterns_for_model(cls, model: str) -> dict:
        """Test-паттерны под профиль модели:
          - DIRECT_RZ (RZ120 и т.п.): есть Convergence (OTS:11), нет Focus Level.
          - SDM_RQ25 (RQ25K/RZ24K-серия): нет Convergence, есть Focus Level 0/50/100%
            (OTS:32/33/34) — подтверждено по rq25k_series_command_en_cn_ja.pdf.
          - HYBRID_RQ7 (RZ7/RZ6/RQ7/RQ6): нет ни Convergence, ни Focus Level —
            у RQ7-серии другой набор (OTS:87 Circle, OTS:A1..A4 User), которые
            мы пока не выводим в комбо.
          - UNKNOWN: показываем весь набор.
        """
        profile = cls.detect_input_profile(model)
        if profile == cls.PROFILE_UNKNOWN:
            return dict(cls.TEST_PATTERNS)
        if profile == cls.PROFILE_DIRECT_RZ:
            excluded = cls._TEST_PATTERN_MODERN_ONLY
        elif profile == cls.PROFILE_SDM_RQ25:
            excluded = cls._TEST_PATTERN_RZ_ONLY
        else:  # HYBRID_RQ7 — исключаем оба набора
            excluded = cls._TEST_PATTERN_RZ_ONLY | cls._TEST_PATTERN_MODERN_ONLY
        return {n: c for n, c in cls.TEST_PATTERNS.items() if n not in excluded}

"""
Константы для протокола связи с проекторами Panasonic.
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


class ProjectorResponses:
    """Ответы проектора"""
    
    # Состояния питания
    POWER_ON = '001'
    POWER_OFF = '000'
    
    # Состояния шаттера
    SHUTTER_OPEN = '0'
    SHUTTER_CLOSED = '1'
    
    # Ошибки
    TIMEOUT = 'Timeout'


class ProjectorProtocol:
    """Параметры протокола"""
    
    # ASCII коды для формирования команды
    PADDING_CHAR = chr(48)  # '0'
    TERMINATOR = chr(13)     # '\r' (carriage return)
    
    # Таймауты
    DEFAULT_TIMEOUT = 2
    
    # Размеры буферов
    INITIAL_BUFFER_SIZE = 1024
    RESPONSE_BUFFER_SIZE = 21


class ProjectorStates:
    """Состояния проектора"""
    
    SHUTTER_OPEN = False
    SHUTTER_CLOSED = True
    
    SHUTTER_TIME_OPTIONS = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 
                           3.0, 3.5, 4.0, 5.0, 7.0, 10.0]


class OSCMessages:
    """Типы OSC сообщений"""
    
    MESSAGE_TYPE_BUTTON = 3  # Тип сообщения для кнопки

"""
Re-export константных модулей из core/constants для обратной совместимости.
Новый код должен импортировать напрямую из core.constants.
"""
from core.constants import (  # noqa: F401
    OSCMessages,
    ProjectorCommands,
    ProjectorProtocol,
    ProjectorResponses,
    ProjectorStates,
)

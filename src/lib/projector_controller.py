"""
DEPRECATED. Re-export для обратной совместимости.
Новый код должен импортировать ProjectorService из services.projector_service.
"""
from services.projector_service import ProjectorService as ProjectorController  # noqa: F401

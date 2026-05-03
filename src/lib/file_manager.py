"""
DEPRECATED. Re-export для обратной совместимости.
Новый код:
- сцены: infra.scene_repository.load_scene / save_scene_to_json
- настройки проектора: infra.settings_repository.{load,save,delete}_projector_settings
"""
from infra.scene_repository import (  # noqa: F401
    SCHEMA_VERSION,
    load_scene,
    save_scene_to_json,
)
from infra.settings_repository import (  # noqa: F401
    create_projector_settings_dict,
    delete_projector_settings,
    get_settings_file_path,
    load_projector_settings,
    save_projector_settings,
)

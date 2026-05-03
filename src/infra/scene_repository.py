"""
Репозиторий сцен: загрузка/сохранение JSON, поддержка legacy TXT
с warning при загрузке (сохранение в TXT удалено).

Сцена — это набор проекторов с позициями на холсте и сохранёнными
настройками линзы/дисплея. Загрузка делает initial network probe
через Projector.get_info() параллельно для всех проекторов.
"""
import asyncio
import json
from typing import List, Optional, Tuple

from lib.projector import Projector
from utils.logger import setup_logger

logger = setup_logger(__name__)

SCHEMA_VERSION = 1

# Тип строки сцены, используется в публичном API:
# (projector, x, y, settings_dict)
SceneEntry = Tuple[Projector, int, int, dict]
WindowSize = Tuple[int, int]


async def load_scene(
    file_path: str,
) -> Tuple[Optional[WindowSize], List[SceneEntry]]:
    """
    Загрузить сцену из файла. Авто-детект формата по расширению.
    Создаёт Projector-объекты и параллельно запрашивает их состояние.

    Возвращает (window_size, [(projector, x, y, settings), ...]).
    При ошибке чтения файла — (None, []).
    """
    if file_path.lower().endswith('.txt'):
        logger.warning(
            f"TXT scene format is deprecated and will be removed in a future "
            f"version. Re-save as .json: {file_path}"
        )
        return await _load_txt(file_path)
    return await _load_json(file_path)


def save_scene_to_json(
    file_path: str,
    window_size: WindowSize,
    entries: List[SceneEntry],
) -> None:
    """Сохранить сцену в JSON. TXT-сохранение не поддерживается."""
    if file_path.lower().endswith('.txt'):
        raise ValueError(
            "TXT scene format saving has been removed. Save the scene as .json."
        )

    width, height = window_size
    data = {
        'schema_version': SCHEMA_VERSION,
        'window_size': {'width': width, 'height': height},
        'projectors': [
            {
                'ip': projector.ip,
                'port': projector.port,
                'username': projector.login,
                'password': projector.password,
                'label': projector.label,
                'position': {'x': x, 'y': y},
                'settings': settings,
            }
            for projector, x, y, settings in entries
        ],
    }

    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved {len(entries)} projectors to {file_path}")
    except Exception as exc:
        logger.error(f"Error while saving scene: {exc}")
        raise


# ---- Внутренняя реализация ----


async def _load_json(
    file_path: str,
) -> Tuple[Optional[WindowSize], List[SceneEntry]]:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return None, []
    except json.JSONDecodeError as exc:
        logger.error(f"Invalid JSON format in {file_path}: {exc}")
        return None, []
    except Exception as exc:
        logger.error(f"Error while reading {file_path}: {exc}")
        return None, []

    schema_version = data.get('schema_version', 0)
    if schema_version > SCHEMA_VERSION:
        logger.warning(
            f"Scene schema_version={schema_version} is newer than supported "
            f"({SCHEMA_VERSION}). Loading with best-effort compatibility."
        )

    window_size = _extract_window_size(data.get('window_size'))

    pending: List[SceneEntry] = []
    for proj_data in data.get('projectors', []):
        try:
            projector = _build_projector_from_dict(proj_data, len(pending) + 1)
            x = proj_data['position']['x']
            y = proj_data['position']['y']
            settings = proj_data.get('settings', {})
            pending.append((projector, x, y, settings))
        except KeyError as exc:
            logger.error(f"Missing required field in projector data: {exc}")
            continue
        except Exception as exc:
            logger.error(
                f"Error creating projector {proj_data.get('ip', 'unknown')}: {exc}"
            )
            continue

    entries = await _fetch_initial_states(pending)
    logger.info(f"Loaded {len(entries)} projectors from {file_path}")
    return window_size, entries


async def _load_txt(
    file_path: str,
) -> Tuple[Optional[WindowSize], List[SceneEntry]]:
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return None, []
    except Exception as exc:
        logger.error(f"Error while reading {file_path}: {exc}")
        return None, []

    window_size: Optional[WindowSize] = None
    if lines:
        try:
            width, height = map(int, lines[0].strip().split(','))
            window_size = (width, height)
            logger.info(f"Window size: {width}x{height}")
        except ValueError:
            logger.warning("Invalid window size format; skipping.")

    pending: List[SceneEntry] = []
    for line in lines[1:]:
        parts = line.strip().split(',')
        if len(parts) != 7:
            logger.warning(f"Invalid line format: {line}")
            continue

        ip, port, username, password, label, x_str, y_str = parts
        try:
            projector = Projector(
                ip=ip,
                port=int(port),
                login=username,
                password=password,
                label=label,
                id=len(pending) + 1,
            )
            pending.append((projector, int(x_str), int(y_str), {}))
        except Exception as exc:
            logger.error(f"Error creating projector {ip}: {exc}")
            continue

    entries = await _fetch_initial_states(pending)
    logger.info(f"Loaded {len(entries)} projectors from {file_path}")
    return window_size, entries


def _extract_window_size(raw) -> Optional[WindowSize]:
    if not raw:
        return None
    width = raw.get('width')
    height = raw.get('height')
    if width and height:
        logger.info(f"Window size: {width}x{height}")
        return (width, height)
    return None


def _build_projector_from_dict(proj_data: dict, default_id: int) -> Projector:
    return Projector(
        ip=proj_data['ip'],
        port=proj_data['port'],
        login=proj_data['username'],
        password=proj_data['password'],
        label=proj_data['label'],
        id=default_id,
    )


async def _fetch_initial_states(pending: List[SceneEntry]) -> List[SceneEntry]:
    """Параллельно запросить get_info() и отбросить недоступные проекторы."""
    if not pending:
        return []

    tasks = [
        asyncio.create_task(projector.get_info())
        for projector, _, _, _ in pending
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    entries: List[SceneEntry] = []
    for (projector, x, y, settings), result in zip(pending, results):
        if isinstance(result, Exception):
            logger.error(f"Error connecting to projector {projector.ip}: {result}")
            continue
        logger.info(f"Loaded projector {projector.label} ({projector.ip})")
        entries.append((projector, x, y, settings))

    for idx, (projector, *_) in enumerate(entries, start=1):
        projector.id = idx

    return entries

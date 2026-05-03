# Simple Panasonic Projector Shutter Control via LAN Control Commands

Управление группами проекторов Panasonic по LAN: шаттер (`OSH`), питание (`PON/POF`),
позиция/фокус/зум линзы (`VXX:LNS*`), aspect ratio, installation mode, тестовые
паттерны. Дистанционное управление по OSC из Resolume Arena, TouchOSC и др.

Тестировалось на Panasonic PT-RZ970, PT-RZ120. Документация команд — в `doc/`.

## Стек

- **UI:** [DearPyGui](https://github.com/hoffstadt/DearPyGui) — нативный GPU-ускоренный фреймворк.
- **OSC:** [oscpy](https://github.com/kivy/oscpy) — быстрый OSC-сервер, работает в отдельном потоке.
- **Сеть:** asyncio + TCP-клиент с MD5-handshake (требование протокола Panasonic).
- **Python:** 3.9+

## Установка

```bash
python -m venv venv
source venv/bin/activate
pip install -r req.txt
# или: pip install -e ".[dev]"   # с pytest
```

## Запуск

```bash
python src/app.py
```

## Конфигурация (env vars)

| Переменная | По умолчанию | Описание |
|---|---|---|
| `PSHC_OSC_HOST` | `127.0.0.1` | OSC bind address |
| `PSHC_OSC_PORT` | `7001` | OSC bind port |
| `PSHC_PROJECTOR_PORT` | `1024` | TCP-порт проектора по умолчанию |
| `PSHC_PROJECTOR_TIMEOUT` | `2` | Таймаут TCP-соединения, сек |
| `PSHC_SETTINGS_DIR` | `src/data/settings` | Где хранятся настройки проекторов |
| `PSHC_LOGS_DIR` | `src/logs` | Где хранится `app.log` |

## OSC-роуты

```
/shutter/open/<room>     — открыть шаттер на проекторе с IP, оканчивающимся на <room>
/shutter/close/<room>    — закрыть шаттер
/shutter/group/open      — открыть на всех проекторах из группы
/shutter/group/close     — закрыть на всех проекторах из группы
```

Пример: `/shutter/open/13` откроет шаттер на проекторе с IP `*.13` (например, `10.101.10.13`),
если он добавлен в приложении.

## Форматы файлов сцен

### JSON (рекомендуется)

```json
{
  "schema_version": 1,
  "window_size": {"width": 1200, "height": 800},
  "projectors": [
    {
      "ip": "10.101.10.126", "port": 1024,
      "username": "admin1", "password": "panasonic",
      "label": "Stage L",
      "position": {"x": 50, "y": 50},
      "settings": {
        "lens_settings": {"h_position": "+00200", "v_position": "+00100"},
        "display_settings": {"aspect_ratio": "16:10", "installation_mode": "Front/Desk"}
      }
    }
  ]
}
```

При загрузке сцены настройки (lens position, aspect ratio, installation mode)
применяются автоматически: сначала линза в Home, ожидание стабилизации
(polling), затем выставление позиции.

### TXT (legacy, deprecated)

```
width,height
IP,PORT,USERNAME,PASSWORD,LABEL,X,Y
...
```

Загрузка работает с предупреждением; сохранение в TXT отключено — пересохраните как `.json`.

## Тесты

```bash
pytest                          # все
pytest tests/test_osc_server.py # только OSC
```

## Структура проекта

См. `CLAUDE.md` — там подробное описание слоёв и архитектуры.

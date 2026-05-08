# Simple Panasonic Projector Shutter Control via LAN Control Commands

Управление группами проекторов Panasonic по LAN: шаттер (`OSH`), питание (`PON/POF`),
позиция/фокус/зум линзы (`VXX:LNS*`), aspect ratio (`VSF`), installation mode (`OIL`),
тестовые паттерны (`OTS`), выбор входа (`IIS`), Freeze (`OFZ`), OSD (`OOS`),
геометрия (`VXX:GMMI0`), идентификация модели (`QID`/`QSN`).
Дистанционное управление по OSC из Resolume Arena, TouchOSC и др.

Поддерживаются три модельных линейки Panasonic NTCONTROL (с авто-детектом по `QID`):

- **DIRECT_RZ** — PT-RZ120, RZ970, RQ22K, RQ32K, RQ50K, RQ13K и старые. Прямые входы
  (HDMI/DVI/SDI/Digital Link/RGB), тест-паттерн `Convergence` (OTS:11).
- **SDM_RQ25** — PT-RQ25K, RQ18K, RZ24K, RZ17K + SR-варианты (2022-2023).
  Все входы кроме HDMI/DisplayPort идут через SDM-слот (`DM1,SD1` и пр.),
  тест-паттерны `Focus Level 0/50/100%`.
- **HYBRID_RQ7** — PT-RZ7/RZ6/RQ7/RQ6 (включая PT-RQ7L, PT-RQ7LBEJ).
  HDMI и Digital Link напрямую, плюс SDM-слот.

UI-комбо «Input Source» и «Test Pattern» автоматически фильтруются под модель —
не выберешь то, чего на проекторе физически нет.

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
pytest                                      # все 62 теста
pytest tests/test_osc_server.py             # OSC pub/sub
pytest tests/test_constants.py              # детектор моделей и фильтры профилей
pytest tests/test_projector_api.py          # snapshot, identity, set/get команды
pytest tests/test_projector_client_lock.py  # сериализация per-projector
```

## Сборка standalone-приложения (PyInstaller)

Один исполняемый файл / `.app` бандл — собирается на каждой целевой OS отдельно
(кросс-сборку не делаем). Из репо-рут:

```bash
pip install pyinstaller

# macOS — .app в dist/
pyinstaller --windowed --name "3PShC" \
  --collect-submodules dearpygui --collect-submodules oscpy \
  --hidden-import tkinter \
  --paths src \
  src/app.py

# Windows 11 — single .exe в dist\
pyinstaller --onefile --windowed --name "3PShC" ^
  --collect-submodules dearpygui --collect-submodules oscpy ^
  --hidden-import tkinter ^
  --paths src ^
  src\app.py
```

Подробнее — см. [`doc/USAGE.md`](doc/USAGE.md), раздел «Сборка standalone-сборок».

## Документация

- [`doc/USAGE.md`](doc/USAGE.md) — пользовательский гайд: workflow, OSC, профили
  моделей, troubleshooting, сборка standalone.
- [`CLAUDE.md`](CLAUDE.md) — архитектура слоёв, runtime model, профили входов.
- `doc/*.pdf` — оригинальные команды Panasonic (RZ120, RQ25K-серия, RQ7-серия).

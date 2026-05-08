# 3P Shutter Control — Руководство пользователя

Приложение управляет проекторами Panasonic по LAN: шаттер, питание,
позиция/фокус/зум линзы, aspect ratio, installation mode, тестовые
паттерны, выбор входа, Freeze (стоп-кадр), On-Screen Display, геометрия.
Авто-детект модели через `QID` подстраивает список входов под линейку.
Работает локально через GUI и удалённо через OSC (Resolume Arena, TouchOSC).

> Установка и стек — см. [`README.md`](../README.md).
> Архитектура и слои — см. [`CLAUDE.md`](../CLAUDE.md).

## Главное окно

```
┌─ File ─ All ──────────────────────────────────────────────────┐  ← меню-бар
│ [Open Group] [Close Group]  [Refresh]                          │  ← быстрый доступ
│                                                                │
│  ┌─ Projector A ─┐   ┌─ Projector B ─┐                        │
│  │ ● Open  Settings ☐ Group           ...                      │  ← карточки
│  │ [ Open ] [ Close ]                                          │
│  │ In: 1.0  Out: 1.0                                           │
│  └─────────────┘   └─────────────┘                            │
└────────────────────────────────────────────────────────────────┘
```

- **File → Add Projector...** — добавить проектор по IP/паролю.
- **File → Load/Save Scene...** — загрузить/сохранить файл сцены (см. ниже).
- **All → Power On/Off all** — питание всех проекторов сразу.
- **Open Group / Close Group** — управление шаттерами тех проекторов,
  у которых отмечен чекбокс **Group**. Эти же действия дублируются OSC-роутами.
- **Refresh** — обновить power/shutter-статусы у всех проекторов.

### Карточка проектора

- **● цветная точка** — питание: зелёная = ON, красная = OFF, серая = неизвестно.
- **Open / Close** — управление шаттером данного проектора.
- **In / Out** — длительность fade-перехода шаттера (значения из протокола Panasonic).
- **Group** — включить проектор в группу (Open Group / Close Group).
- **Settings** — открыть диалог настроек (см. ниже).
- **Перетаскивание** — карточку можно тащить за заголовок; позиция сохраняется в сцене.
- **Закрыть × в заголовке** — удалить проектор из приложения.

## Workflow: первая сцена

1. **File → Add Projector**: введите IP, порт (по умолчанию 1024), логин/пароль
   (`admin1` / `panasonic` для большинства Panasonic из коробки), произвольный label.
2. Расставьте карточки на холсте — это будет визуальный план зала.
3. **Settings** на каждой: выставьте aspect, installation, позицию линзы (через
   крест и Focus/Zoom). Скорость сдвига выбирается переключателем **Speed** сверху.
4. **Settings → Save Settings** — сохранить настройки данного проектора в файл
   `data/settings/projector_<ip>.json` (для быстрого восстановления вне сцены).
5. **File → Save Scene...** — сохранить весь набор проекторов вместе с позициями
   и текущими настройками в `.json`-файл.

При следующем запуске: **File → Load Scene...** — приложение восстановит проекторы
с их позициями и автоматически применит сохранённые настройки (lens home →
ожидание стабилизации → aspect/installation/lens position).

## Диалог Settings

Четыре вкладки:

- **Lens** — выбираете скорость (`slow`/`normal`/`fast`) и нажимаете
  стрелки: ←/↑/↓/→ для shift, Home — в центральное положение, Focus/Zoom — `-/+`.
- **Source** — выбор входа (HDMI1/HDMI2/DisplayPort/SLOT-входы и т.п.; список
  фильтруется под определённую `QID` модель проектора), чекбокс **Freeze**
  (стоп-кадр для безболезненной перенастройки в Resolume на лету) и чекбокс
  **On-Screen Display** (выключите перед шоу, чтобы меню не лезло в проекцию).
- **Display** — Aspect Ratio (`16:10`/`16:9`/`4:3`), Installation Mode
  (Front/Rear × Desk/Ceiling/Auto), **Geometry** (Off / Keystone / Curved /
  Corner Correction — типично выключают перед мэппингом в Resolume),
  Test Pattern (фильтруется под профиль модели — у RQ25-серии есть Focus
  Level 0/50/100%, у RZ120 — Convergence).
- **Info** — текущие H/V позиции линзы, сетевые параметры, плюс
  **Model / Family / Input profile / Serial / Firmware** с кнопкой
  **Refresh Identity** для повторного `QID/QSN/SVRS*`.

Внизу окна:
- **Save Settings** — сохранить per-projector файл (lens position + display).
- **Load & Apply** — загрузить сохранённый файл и применить.
- **Close** — закрыть диалог (изменения, применённые кнопками, остаются на проекторе).

### Профили моделей

Список входов и тест-паттернов в комбо подстраивается под `QID` модели:

| Profile | Модели | Входы | Особые тест-паттерны |
|---|---|---|---|
| **DIRECT_RZ** | PT-RZ120, RZ970, RQ22K, RQ32K, RQ50K, RQ13K, FRZ120C | HDMI1/2, SDI direct, DL direct, DVI-D, RGB1/RGB2 | Convergence (OTS:11) |
| **SDM_RQ25** | PT-RQ25K, RQ18K, RZ24K, RZ17K + SR-варианты | HDMI1/2, DisplayPort, SLOT: 12G SDI / DL / PressIT / 3rd Party | Focus Level 0/50/100% |
| **HYBRID_RQ7** | PT-RZ7/RZ6/RQ7/RQ6 (включая RQ7L, RQ7LBEJ) | HDMI1/2, Digital Link direct, SLOT: 12G SDI / DL / PressIT / 3rd Party | (только универсальные) |
| **UNKNOWN** | модель не распознана | весь список | весь набор |

Если выбрать вход, которого на проекторе физически нет — проектор ответит
`ER401`, в логе появится строка с ошибкой; UI продолжит работать.

## OSC-управление

OSC-сервер слушает `127.0.0.1:7001` (переопределяется через
`PSHC_OSC_HOST` / `PSHC_OSC_PORT`).

### Роуты

| Адрес | Эффект |
|---|---|
| `/shutter/open/<room>` | Открыть шаттер на проекторе с IP `*.<room>` |
| `/shutter/close/<room>` | Закрыть шаттер |
| `/shutter/group/open` | Open Group (все с галочкой Group) |
| `/shutter/group/close` | Close Group |

`<room>` — последний октет IP. Например, `/shutter/open/13` сработает на
проекторе с IP `10.101.10.13`, если он добавлен в приложении.

### Resolume Arena

В Resolume → Preferences → OSC → `Output enabled: ✓`, IP `127.0.0.1`, Port `7001`.
В колонках/клипах привяжите шорткат к нужному адресу.

### TouchOSC

В шаблоне на кнопку повесьте OSC Send с адресом `/shutter/open/13` (или нужным
номером). Приложение принимает сообщения без аргументов (Resolume) и любые
truthy-значения (TouchOSC присылает `1` на нажатие); button-release (`0`)
игнорируется, чтобы не было двойного срабатывания.

## Конфигурация через env vars

| Переменная | По умолчанию |
|---|---|
| `PSHC_OSC_HOST` | `127.0.0.1` |
| `PSHC_OSC_PORT` | `7001` |
| `PSHC_PROJECTOR_PORT` | `1024` |
| `PSHC_PROJECTOR_TIMEOUT` | `2` (сек) |
| `PSHC_SETTINGS_DIR` | `src/data/settings` |
| `PSHC_LOGS_DIR` | `src/logs` |

## Форматы файлов

- **`.json`** (рекомендуется) — сцена с `schema_version: 1`, размером окна
  и списком проекторов с позицией и сохранёнными настройками. Пример —
  [`doc/scene_example.json`](scene_example.json).
- **`.txt`** (legacy) — загрузка работает с warning-логом, сохранение отключено.
  Пересохраните любую старую сцену как `.json`.
- **`data/settings/projector_<ip>.json`** — отдельный файл per-projector,
  пишется кнопкой **Save Settings**. Не входит в сцену, но загружается через
  **Load & Apply** в диалоге Settings.

## Логи

Все события дублируются в `src/logs/app.log` (директорию переопределяет
`PSHC_LOGS_DIR`). При проблемах смотрите туда — там будут полные ошибки сети,
ответы протокола, OSC-роуты.

## Типовые проблемы

| Симптом | Причина / решение |
|---|---|
| Карточка добавилась, но `●` серая, статус `Unknown` | Проектор недоступен по сети или не отвечает на TCP-порт. Проверьте `ping <ip>`, порт 1024 (или `PSHC_PROJECTOR_PORT`), логин/пароль. |
| Open/Close не реагирует, в логах `Connection timed out` | Проектор выключен из розетки / в standby без LAN-стандби / firewall режет TCP. |
| OSC не работает | Проверьте `PSHC_OSC_HOST/PORT`. Для приёма извне поставьте `PSHC_OSC_HOST=0.0.0.0`. В логах при каждом OSC-сообщении должен появляться `OSC: open shutter for room ...`. |
| `Scene loaded 0 projectors` | При загрузке сцены делается network probe; недоступные проекторы выкидываются. Включите проекторы и пересохраните, либо добавьте вручную. |
| Lens settle timeout (15s) | После lens home / set position приложение ждёт стабилизации позиции (два одинаковых ответа подряд). Если объектив очень медленный или есть механическая проблема, увеличьте `LENS_HOME_SETTLE_MAX_SECONDS` в `core/constants.py`. |
| В UI на стрелках `?` | Системный TTF не нашёлся (см. `install_default_font` в `ui/dpg_theme.py`). На Linux установите `dejavu-fonts` или укажите свой путь. |
| Info-таб показывает `Family: unknown`, `Input profile: UNKNOWN` | Опрос `QID` упал или модель не распознаётся регэкспом. Проверьте лог — там строка `Identified ... model=...`. Если модель — что-то экзотическое, добавьте паттерн в `_PROFILE_PATTERNS` в `core/constants.py`. |
| Выбираете SLOT-вход, проектор отвечает `ER401` | Профиль определился неправильно или на SDM-слоте нет нужного модуля. Проверьте `Input profile` в Info-табе и физическую конфигурацию SLOT'а на проекторе. |
| Source/Display комбо обновляются медленно при открытии Settings | Все 9 параллельных query идут под per-projector lock'ом (Panasonic не любит параллельные сессии). Если проектор отвечает медленно — каждый запрос до `PSHC_PROJECTOR_TIMEOUT` секунд. |

## Тесты

```bash
pytest                                      # все 62 теста (~0.3с)
pytest tests/test_osc_server.py             # OSC pub/sub
pytest tests/test_scene_repository.py       # JSON/TXT loading
pytest tests/test_constants.py              # детектор моделей и фильтр профилей
pytest tests/test_projector_api.py          # snapshot, identity, set/get команды
pytest tests/test_projector_client_lock.py  # сериализация транзакций
```

UI-тестов в pytest нет (DPG требует main-thread + display); для ручной
проверки UI запускайте `tests/_smoke_ui.py`.

## Сборка standalone (PyInstaller)

Цель: один исполняемый файл (Win11) или `.app`-бандл (macOS), без
необходимости ставить Python и зависимости на целевой машине.

> Кросс-сборка не делается — каждую целевую OS собирайте на ней самой
> (например, .exe — на Win11, .app — на macOS).

### macOS (.app)

```bash
# на любой Mac с целевой архитектурой (Intel или Apple Silicon)
python -m venv venv && source venv/bin/activate
pip install -r req.txt pyinstaller

pyinstaller --windowed --name "3PShC" \
  --collect-submodules dearpygui --collect-submodules oscpy \
  --hidden-import tkinter \
  --paths src \
  src/app.py

# Готовый бандл: dist/3PShC.app
open dist/3PShC.app    # smoke-проверка
```

Каркас (`--windowed`) скрывает консоль; `--collect-submodules` подтягивает
DPG-движок и oscpy-биндинги (без них PyInstaller иногда промахивается с
динамическими импортами); `--hidden-import tkinter` нужен для системных
file-диалогов (Open/Save Scene).

Для распространения вне dev-машины подпишите бандл (`codesign`) и
отправьте на нотаризацию Apple — иначе Gatekeeper будет ругаться при
первом запуске:

```bash
codesign --deep --force --sign "Developer ID Application: <Name>" dist/3PShC.app
xcrun notarytool submit dist/3PShC.app.zip --keychain-profile <profile> --wait
```

### Windows 11 (.exe)

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r req.txt pyinstaller

pyinstaller --onefile --windowed --name "3PShC" `
  --collect-submodules dearpygui --collect-submodules oscpy `
  --hidden-import tkinter `
  --paths src `
  src\app.py

# Готовый файл: dist\3PShC.exe
.\dist\3PShC.exe
```

`--onefile` пакует всё в один `.exe` (минус: первая запуск ~2-3 секунды на
распаковку; плюс: один файл удобнее раздавать). Если важна скорость старта,
уберите `--onefile` и копируйте всю папку `dist/3PShC/`.

Для подписи (опционально): `signtool sign /f mycert.pfx /p PASS /tr <timestamp_url> /td sha256 dist\3PShC.exe`.

### Хранение настроек у пользователя

Билд по умолчанию пишет настройки в относительные пути от exe (`src/data/...`),
но для standalone лучше переопределить через env vars:

- `PSHC_SETTINGS_DIR=%APPDATA%\3PShC\settings` (Windows) или `~/Library/Application Support/3PShC/settings` (macOS)
- `PSHC_LOGS_DIR=%APPDATA%\3PShC\logs` или `~/Library/Logs/3PShC`

Это можно обернуть в shortcut/launcher-скрипт, который выставит env и запустит exe.

### Иконка

PyInstaller принимает `--icon path/to/icon.icns` (macOS) или `--icon path/to/icon.ico`
(Windows). Заранее сконвертируйте PNG в нужный формат (`iconutil` на Mac,
`magick convert` на Win).

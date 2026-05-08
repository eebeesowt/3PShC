# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install (use either)
pip install -r req.txt
pip install -e ".[dev]"          # also pulls pytest

# Run the app (from repo root)
python src/app.py

# Tests (pytest auto-discovers, with src on PYTHONPATH via pyproject.toml)
pytest
pytest tests/test_osc_server.py
pytest tests/test_models.py::test_projector_config_is_frozen
```

There is no linter / type-checker / formatter wired into the project.

## Configuration via env vars

Defined in `src/config.py`, read at import time:

- `PSHC_OSC_HOST` / `PSHC_OSC_PORT` — OSC bind (defaults `127.0.0.1:7001`)
- `PSHC_PROJECTOR_PORT` / `PSHC_PROJECTOR_TIMEOUT` — TCP defaults
- `PSHC_SETTINGS_DIR` / `PSHC_LOGS_DIR` — file locations

## Architecture

The codebase uses a four-layer architecture. UI is built on **DearPyGui**;
OSC uses **oscpy**. The previous CustomTkinter / python-osc stack and the
`lib/` shim layer have been removed.

```
src/
  app.py                  # Bootstrap: wires services, OSC, AppWindow; runs asyncio
  config.py               # env-driven config (OSCConfig, ProjectorConfig, Paths)
  core/                   # PURE — no I/O, no UI
    models.py             # ProjectorConfig (frozen), ProjectorState, LensPosition,
                          # DisplaySettings, Scene, ProjectorEntry. ProjectorState
                          # holds runtime identity (model/serial/firmware) +
                          # identity_attempted flag для ленивого refresh.
    constants.py          # Panasonic protocol strings, INPUT_PROFILES (DIRECT_RZ
                          # / SDM_RQ25 / HYBRID_RQ7), TEST_PATTERNS с per-model
                          # фильтром, detect_input_profile() для матча модели.
  infra/                  # I/O boundary
    projector_client.py   # TCP+MD5 transport — fresh connection per command
                          # (Panasonic auth nonce is per-connect). Per-instance
                          # asyncio.Lock сериализует команды на один проектор —
                          # без него параллельные refresh'ы ловят ER401.
    projector_api.py      # High-level commands on (client, state); owns
                          # wait_for_lens_settle (polling, replaces sleep(12)),
                          # refresh_identity (QID/QSN/SVRS0→SVRSE fallback) и
                          # сеттеры для input/freeze/OSD/geometry/aspect/lens.
    scene_repository.py   # Scene load/save (JSON schema_version=1; TXT load-only,
                          # logged as deprecated; saving TXT raises)
    settings_repository.py# Per-projector JSON in PSHC_SETTINGS_DIR
    osc_server.py         # OSCController on oscpy.OSCThreadServer; pub/sub via
                          # .on(OSCEvent.X, handler); thread→asyncio bridge via
                          # loop.call_soon_threadsafe
  services/
    projector.py          # Projector facade — wraps Config+State+Client+Api;
                          # this is the handle UI code passes around
    projector_service.py  # Owns the list of Projector instances and group ops
    scene_service.py      # Snapshots live state from each Projector before save
  ui/                     # DearPyGui
    app_window.py         # Root controller. Owns DPG context lifecycle
                          # (create_context → install_default_font →
                          # install_global_theme → create_viewport →
                          # setup_dearpygui → viewport_menu_bar + toolbar →
                          # show_viewport → render-loop → destroy_context).
                          # Subscribes to OSC events. Tracks every async op
                          # via _create_task for graceful shutdown.
    projector_card.py     # Per-projector "card" — each is a top-level dpg.window
                          # with pos=[x,y]; drag works natively (DPG window can
                          # be moved by dragging the title bar)
    add_projector_dialog.py    # Modal dpg.window. Принимает on_close callback,
                          #   AppWindow удаляет диалог из _open_dialogs при close.
    settings_dialog.py    # Modal dpg.window с табами Lens / Source / Display /
                          #   Info. Source: Input combo (фильтруется по
                          #   input_profile модели), Freeze, OSD. Display:
                          #   Aspect, Installation, Geometry, Test Pattern
                          #   (тоже фильтр по profile). Info: model/serial/
                          #   firmware/family/input_profile + Refresh Identity.
                          #   _reset_combo_if_orphan сбрасывает текущее value
                          #   комбо, если оно ушло из items после фильтра.
    lens_widgets.py       # build_speed_selector (radio slow/normal/fast) +
                          # build_shift_pad (3×3 крест: ↑/↓/←/→/Home) +
                          # build_directional_bar (linear -/+ для focus/zoom).
                          # Скорость выбирается один раз сверху, стрелки
                          # читают её через speed_provider при клике.
    dpg_theme.py          # Palette + install_global_theme + install_default_font
                          # (грузит SFNS/Arial Unicode/DejaVu c глифами стрелок
                          # U+25xx и кириллицы) + ButtonThemes cache
    file_dialogs.py       # System Open/Save via tkinter.filedialog wrapped in
                          # asyncio.to_thread (DPG's built-in file dialog is
                          # not native-looking; tk runs as a one-shot, no
                          # mainloop)
  utils/
    logger.py             # setup_logger(__name__) — console + Paths.LOGS_DIR/app.log
    validator.py          # IP / port validation
  data/settings/          # Per-projector saved settings (created on demand)
  logs/                   # app.log (gitignored)
```

### Runtime model

- **Single asyncio event loop.** `AppWindow.run()` interleaves
  `dpg.render_dearpygui_frame()` with `await asyncio.sleep(1/60)`. DPG
  callbacks fire inside `render_dearpygui_frame()` in this same coroutine,
  so `asyncio.create_task(...)` from a button callback works directly.
- **OSC thread bridging.** `OSCThreadServer` runs in its own thread. Its
  default_handler parses the address and calls `_emit(event, *args)`, which
  uses `loop.call_soon_threadsafe(handler, *args)` to dispatch back to the
  asyncio loop. Every handler is wrapped in `_safe_call` so one bad
  subscriber can't kill the loop.
- **Task tracking.** `AppWindow._create_task(coro, description)` adds the
  task to a tracked set and logs unhandled exceptions on done. On shutdown
  every pending task is cancelled and awaited.
- **Projector transport.** `ProjectorClient.send_raw` opens a TCP
  connection, reads the auth nonce, computes `md5(login:password:nonce)`,
  sends `<md5>00<cmd>\r`, reads the reply. One command = one connection
  (Panasonic protocol requirement). Команды per-projector сериализованы
  через `asyncio.Lock` (lazy init): параллельные TCP к одному IP ловят
  ER401, лок их выстраивает в очередь; разные проекторы остаются
  независимыми.
- **Lens settle.** `apply_saved_settings` does lens home → polls
  `get_lens_position` until two consecutive samples match (max 15s,
  interval 1s) → applies aspect/installation/lens position. Replaces an
  older `asyncio.sleep(12)` open loop. Snapshot линзы пишет sentinel
  `'---'` при неудаче опроса, чтобы при последующем apply не уйти в (0,0).
- **Identity refresh.** При первом успешном `refresh_info` подтягивается
  `model/serial/firmware` через `QID`, `QSN`, `QVX:SVRS0`/`QVX:SVRSE`
  (RZ120/RQ25K знают SVRS0; RQ7-серия — только SVRSE). Флаг
  `state.identity_attempted` ставится в `finally` — повторный refresh не
  спамит запросами на устройстве, где QID отвечает `ER`.

### Семьи моделей и input profiles

`detect_input_profile(model)` → `DIRECT_RZ` / `SDM_RQ25` / `HYBRID_RQ7` /
`UNKNOWN`. Это драйвит фильтр UI-комбо «Input Source» и «Test Pattern»:

- **DIRECT_RZ** (PT-RZ120, RZ970, RQ22K, RQ32K, RQ50K, RQ13K, FRZ120C):
  HDMI1/2 + прямые SDI/DL/DVI/RGB. Test pattern содержит `Convergence` (OTS:11).
- **SDM_RQ25** (PT-RQ25K, RQ18K, RZ24K, RZ17K и SR-варианты): HDMI1/2,
  DisplayPort, и все SDI/DL/PressIT/3rd Party — через SDM-слот (`DM1,*`
  префикс). Test pattern содержит `Focus Level 0/50/100%` (OTS:32/33/34),
  но не `Convergence`.
- **HYBRID_RQ7** (PT-RZ7/RZ6/RQ7/RQ6, включая `PT-RQ7L`/`PT-RQ7LBEJ`):
  HDMI1/2 direct, Digital Link direct, плюс SDM-слот. Нет ни DisplayPort,
  ни DVI/RGB. Test pattern исключает И `Convergence`, И `Focus Level`.
- **UNKNOWN**: модель не распознана — комбо показывает все варианты.

Профили — read-only по `state.model`; никакой ручной настройки. Смотрите
`Projector.input_profile` и `ProjectorStates.input_sources_for_model(...)`.

### Scene file formats

- JSON (canonical, `schema_version: 1`): `window_size`, list of projectors
  with `position` and per-projector `settings`. See `doc/scene_example.json`.
- TXT (legacy): `width,height` then `IP,PORT,USERNAME,PASSWORD,LABEL,X,Y`.
  Loading still works but logs a deprecation warning; saving raises.

## Conventions

- Always log via `utils.logger.setup_logger(__name__)`. The project removed
  `print` calls during refactor; do not reintroduce them.
- Russian docstrings/comments — keep that style when editing existing modules.
- The `Projector` facade in `services/projector.py` is the single mutable
  handle used everywhere outside `infra/`. Its `.api` exposes `ProjectorApi`
  and `.state` / `.config` the underlying dataclasses. Don't duplicate
  state on the facade.
- DPG items are referenced by tag — use `dpg.generate_uuid()` to avoid
  collisions when scenes are reloaded. Always guard `configure_item`/
  `set_value` with `dpg.does_item_exist(tag)` because dialogs may be
  closed while async refresh tasks are still in flight.
- Each per-projector card is its own top-level `dpg.window` with
  `pos=[x,y]`. To get the saved position back, call `dpg.get_item_pos(tag)`.

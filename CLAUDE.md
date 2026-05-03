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
                          # DisplaySettings, Scene, ProjectorEntry
    constants.py          # Panasonic protocol strings + OSCMessages
  infra/                  # I/O boundary
    projector_client.py   # TCP+MD5 transport — fresh connection per command
                          # (Panasonic auth nonce is per-connect)
    projector_api.py      # High-level commands on (client, state); owns
                          # wait_for_lens_settle (polling, replaces sleep(12))
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
                          # (create_context → install_global_theme →
                          # create_viewport → setup_dearpygui → show_viewport →
                          # render-loop → destroy_context). Subscribes to OSC
                          # events. Tracks every async op via _create_task for
                          # graceful shutdown.
    projector_card.py     # Per-projector "card" — each is a top-level dpg.window
                          # with pos=[x,y]; drag works natively (DPG window can
                          # be moved by dragging the title bar)
    add_projector_dialog.py    # Modal dpg.window
    settings_dialog.py    # Modal dpg.window with Lens/Display/Info tabs
    lens_widgets.py       # build_shift_cross / build_directional_bar
    dpg_theme.py          # Palette + install_global_theme + ButtonThemes cache
    file_dialogs.py       # System Open/Save via tkinter.filedialog wrapped in
                          # asyncio.to_thread (DPG's built-in file dialog is
                          # not native-looking; tk runs as a one-shot, no
                          # mainloop)
  utils/
    logger.py             # setup_logger(__name__) — console + src/logs/app.log
    async_helpers.py      # @handle_async_errors decorator
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
  (Panasonic protocol requirement).
- **Lens settle.** `apply_saved_settings` does lens home → polls
  `get_lens_position` until two consecutive samples match (max 15s,
  interval 1s) → applies aspect/installation/lens position. Replaces an
  older `asyncio.sleep(12)` open loop.

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

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
pytest tests/test_models.py
pytest tests/test_models.py::test_projector_config_is_frozen
```

There is no linter / type-checker / formatter wired into the project. Run scripts from the repo root so relative imports inside `src/` resolve correctly.

## Configuration via env vars

Defined in `src/config.py` and read at import time:

- `PSHC_OSC_HOST` / `PSHC_OSC_PORT` — OSC server bind (defaults `127.0.0.1:7001`)
- `PSHC_PROJECTOR_PORT` / `PSHC_PROJECTOR_TIMEOUT` — TCP defaults for projectors
- `PSHC_SETTINGS_DIR` / `PSHC_LOGS_DIR` — file locations

## Architecture

The codebase was recently restructured into a layered architecture; `src/lib/` now holds only thin re-export shims kept for backward compatibility — new code should import directly from `core/`, `infra/`, `services/`.

```
src/
  app.py                  # 27-line bootstrap: builds services and runs MainWindow
  config.py               # env-driven config (OSCConfig, ProjectorConfig, Paths)
  theme.py                # Theme/AppConfig — colors, fonts, layout sizes
  core/                   # PURE — no I/O, no UI
    models.py             # ProjectorConfig (frozen), ProjectorState, LensPosition,
                          # DisplaySettings, Scene, ProjectorEntry
    constants.py          # ProjectorCommands / Responses / Protocol / States,
                          # OSCMessages — Panasonic protocol strings
  infra/                  # I/O boundary
    projector_client.py   # TCP+MD5 transport: send_raw() opens a fresh connection
                          # per command (Panasonic auth nonce is per-connect)
    projector_api.py      # High-level commands operating on a (client, state) pair;
                          # owns wait_for_lens_settle (polling, replaces sleep(12))
    scene_repository.py   # Scene load/save (JSON schema_version=1; TXT load-only,
                          # logged as deprecated; save_scene_to_txt removed)
    settings_repository.py# Per-projector JSON in PSHC_SETTINGS_DIR/projector_<ip>.json
  services/               # Orchestration, no UI
    projector_service.py  # Owns the list of Projector instances and group ops
    scene_service.py      # Snapshots live state from each Projector before saving
  ui/                     # CustomTkinter
    main_window.py        # MainWindow.run() drives Tk via root.update() +
                          # await asyncio.sleep(0.01); _create_task tracks every
                          # async op for graceful shutdown
    projector_frame.py    # Per-projector tile (drag, shutter buttons, status)
    projector_settings_dialog.py  # Tabbed lens/display/info dialog
    lens_cross.py         # LensShiftCross / FocusControls / ZoomControls
    add_projector_dialog.py
    widget_factory.py     # Themed CTk widget helpers
    lens_controls_builder.py  # DEPRECATED shim — use ui/lens_cross.py
  lib/                    # DEPRECATED shims — re-export from core/infra/services
    projector.py          # Projector facade still used by services & UI; wraps
                          # ProjectorConfig + ProjectorState + ProjectorClient
                          # + ProjectorApi (legacy `Projector.SHUTER_CLOSED` typo
                          # is preserved on purpose for back-compat)
    constants.py, file_manager.py, osc_controller.py, projector_controller.py
  utils/
    logger.py             # setup_logger(__name__) — console + src/logs/app.log
    async_helpers.py      # @handle_async_errors decorator, run_async helper
    validator.py          # IP / port validation
  data/settings/          # Per-projector saved settings (created on demand)
  logs/                   # app.log
```

### Runtime model

- Single asyncio event loop. UI is CustomTkinter; `MainWindow.run()` interleaves
  `root.update()` with `asyncio.sleep(0.01)`. Async work is launched via
  `_create_task(coro, description)` which adds it to a tracked set so
  `_async_shutdown` can cancel everything when the window closes.
- `ProjectorClient.send_raw` opens a TCP connection, reads the auth nonce,
  computes `md5(login:password:nonce)`, sends `<md5>00<cmd>\r`, reads the reply.
  One command = one connection — required by the Panasonic protocol.
- OSC server (`lib/osc_controller.py`) routes `/shutter/open*`, `/shutter/close*`,
  `/shutter/group/{open,close}` to callbacks set by `MainWindow`. The room number
  is the last octet of the projector IP (`ProjectorConfig.ip_room_number`).
- `apply_saved_settings`: lens home → `wait_for_lens_settle` (polls
  `get_lens_position` until two consecutive samples match, max 15s) → set
  aspect / installation / lens position. This replaces an older
  `asyncio.sleep(12)` open loop.

### Scene file formats

- JSON (canonical, `schema_version: 1`): includes `window_size`, list of
  projectors with `position` and per-projector `settings` (lens + display).
  See `doc/scene_example.json`.
- TXT (legacy): `width,height` then `IP,PORT,USERNAME,PASSWORD,LABEL,X,Y` per
  line. Loading still works but logs a deprecation warning; saving raises
  `ValueError`.

## Conventions

- Always log via `utils.logger.setup_logger(__name__)` — the project removed
  `print` calls during the refactor; do not reintroduce them.
- Docstrings and inline comments are in Russian; keep that style when editing
  existing modules.
- New code should depend on `core`/`infra`/`services` directly rather than the
  `lib/` shims, so the shims can be deleted later.
- The `Projector` facade in `lib/projector.py` is the single mutable handle
  used by services and UI; its `.api` exposes `ProjectorApi` and `.state` /
  `.config` the underlying dataclasses. Don't duplicate state on the facade.

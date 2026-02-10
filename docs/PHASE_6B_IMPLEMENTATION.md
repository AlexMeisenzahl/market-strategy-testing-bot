# Phase 6B — System UX & Configuration (Implementation Summary)

## Constraints followed

- **No execution engine or strategy logic changes**
- **No process start/stop/restart** — dashboard does not start or stop the engine; all copy and links state that the engine is run via terminal (e.g. `python run_bot.py`)
- **Live trading gated** — switching to Live requires typing `LIVE` in a confirmation box; Set to Paper has no gate
- **Single canonical credential store** — **SecureConfigManager** only. All UI writes go through `/api/settings/data-sources` (POST) and `/api/settings/integrations` (GET). The legacy database APIKey table is not used for writes from the new System & Settings UI

## What was implemented

### 1. Centralized System & Settings UI

- **Route:** `/system-settings`
- **Template:** `dashboard/templates/system_settings.html`
- **Sections:**
  - **Restart notice** — Global banner: changes take effect after restarting the engine; dashboard does not start/stop the process
  - **Trading mode** — Current mode (Paper/Live), Set to Paper, Set to Live with confirmation (type LIVE), live warning when active
  - **API keys & integrations** — List from SecureConfigManager (masked only), “Used by” labels, Test and Update per service, inline save with merge so partial updates keep existing values
  - **Strategy defaults** — Scaffolding: “Configure in config.yaml”
  - **Execution settings** — Scaffolding: no UI control; engine/config control
  - **System updates** — Current version, Check for updates, restart required note
  - **Advanced** — Collapsed by default; “Dangerous / developer”; no process control

### 2. Canonical API key storage (SecureConfigManager)

- **Read:** `GET /api/settings/integrations` returns all integrations with **masked** credentials and dependency labels (no raw secrets).
- **Write:** `POST /api/settings/data-sources` with `service` and `credentials`. Backend **merges** with existing credentials so partial updates (e.g. only `api_key`) do not wipe other fields.
- **Test:** `POST /api/settings/test-connection` with `service` (and optional `credentials`); uses saved credentials if not provided.
- **Services:** polymarket, crypto, telegram, email. All stored in `config/credentials.json` (encrypted) via SecureConfigManager. No UI writes to the database `api_keys` table from this page.

### 3. Trading mode UX

- **GET /api/settings/trading-mode** — Returns `mode`, `paper_trading`, `requires_restart`, `warning` (when live).
- **POST /api/settings/set-trading-mode** — Body: `mode` (`paper` | `live`), and for `live`: `confirm_phrase` must be `"LIVE"`. Response includes `requires_restart: true` and message to restart the engine.
- **UI:** Badge for current mode, live warning when active, “Set to Live” opens confirmation box; “Confirm enable Live” only sends if input is `LIVE`. Restart notice shown globally and in success message.

### 4. Restart and limitations

- Restart notice at top of System & Settings and in trading-mode success message.
- Strategy defaults and execution settings state that config/engine control behavior and no in-dashboard process control.
- Advanced section states that process start/stop/restart are not available from the UI.

### 5. Link from dashboard

- On the **System** page (main dashboard), “System & Settings” link added to open `/system-settings` for configuration, trading mode, and API keys.

## Files touched

- `dashboard/routes/data_sources_api.py` — Added `GET /api/settings/integrations` (masked list + dependencies); save handler merges with existing credentials.
- `dashboard/app.py` — Added `GET /system-settings` → `system_settings.html`.
- `dashboard/templates/system_settings.html` — New template (trading mode, integrations, scaffolding, updates, advanced).
- `dashboard/templates/index.html` — System page: added “System & Settings” link and short description.

## Security notes

- API keys and secrets are only ever sent to the server in POST body (save/test); they are not logged in the added code.
- List/integrations endpoints return only masked values (e.g. `****` + last 4–6 chars).
- Sensitive inputs use `type="password"` where appropriate; placeholders say “Leave blank to keep existing”.

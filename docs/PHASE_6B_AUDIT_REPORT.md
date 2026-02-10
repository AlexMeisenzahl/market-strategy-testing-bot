# Phase 6B — Audit Report: System Configuration, API Keys, and Operational Controls

**Scope:** README, codebase, and PR documentation.  
**Purpose:** Audit only. No UI proposals. No code changes.  
**Date:** 2026-02-10.

---

## 1. System configuration

### 1.1 Configuration files and sources

| Item | Location | Referenced in |
|------|----------|----------------|
| Primary config | `config.yaml` (project root) | README, config.example.yaml, dashboard, run_bot, config_loader, utils/config_validator |
| Example / template | `config.example.yaml` | README, SETUP, docs (configuration, deployment, user_guide), PRs (PR8, PR20D, MERGE_*, etc.) |
| Env override | `.env` (optional), `load_dotenv` in config_loader | ConfigLoader, NEW_FEATURES (NOAA_API_KEY), .env.example |
| Config loader | `config/config_loader.py` | `get_config(config_path="config.yaml")`; precedence: ENV > YAML > DEFAULTS |

### 1.2 Config structure (from config.example.yaml and docs)

- **Safety:** `paper_trading` (bool), `kill_switch` (bool). README and docs state paper_trading must stay true; kill_switch stops bot when true.
- **Trading parameters:** `max_trade_size`, `min_profit_margin`, `max_trades_per_hour`, `max_trades_per_day`.
- **Data sources:** `data_sources.crypto_prices` (primary/fallback), `data_sources.polymarket` (method, cache_ttl).
- **Polymarket:** `polymarket.api` (enabled, base_url, rate_limit, timeout, retry_attempts), `polymarket.market_filters`.
- **Markets:** `markets_to_watch` (list).
- **API behavior:** `api_timeout_seconds`, `max_retries`, `request_delay_seconds`, `rate_limit_*`, `auto_pause_on_connection_loss`.
- **Notifications:** `notifications` (desktop, email, telegram with event_types, rate_limiting, quiet_hours); legacy `desktop_notifications`, `sound_alerts`.
- **Notification triggers:** `notification_triggers` (high_value_opportunity, api_connection_loss, daily_profit_milestone).
- **Telegram:** `telegram` (enabled, bot_token, chat_id).
- **Email:** `email` (enabled, from_email, to_email, smtp_*, password).
- **Risk:** `max_daily_loss`, `max_total_loss`, `circuit_breaker_*`.
- **Logging:** `log_level`, `log_retention_days`.
- **Dashboard:** `dashboard` (port, debug, trades_per_page, opportunities_per_page).
- **Crypto APIs:** `crypto_apis` (coingecko, binance, coinbase with base_url, rate_limit, cache), `crypto_symbols`.
- **Price alerts:** `price_alerts` (enabled, check_interval_seconds, alerts list).
- **Strategies:** `strategies.<name>` (enabled, strategy-specific params); e.g. `weather_trading.noaa_api_key` (env placeholder `${NOAA_API_KEY}`), others without keys.
- **Exchanges:** `exchanges` (polymarket, etc.).

### 1.3 Where config is read or written

- **Read:** `config_loader.get_config()`, `dashboard.services.config_manager` (ConfigManager), `run_bot.py` (YAML load), `utils/config_validator`, `telegram_bot`, `strategies`, `services/settings_manager.py`, `services/emergency_kill_switch.py` (Config.set/get for kill switch state).
- **Written:** Dashboard app.py has routes that write `config.yaml` (e.g. notification settings, strategy settings, trading mode toggle/set). ConfigManager updates config. Emergency kill switch uses DB/Config for active state, not necessarily config.yaml for kill_switch flag.

### 1.4 Config validation

- `utils/config_validator.py`: Validates structure, `paper_trading`, `kill_switch` (type and warning when true). Referenced in docs (configuration.md, TROUBLESHOOTING, PR20H).
- No single “config schema” document; config.example.yaml and docs are the de facto reference.

---

## 2. API keys and credentials

### 2.1 Credential storage (two systems)

| System | Location | Used by | Masking |
|--------|----------|---------|--------|
| **SecureConfigManager** | `config/credentials.json` (encrypted), `config/encryption.key` (Fernet) | run_bot (polymarket, crypto clients), dashboard routes data_sources_api, GET /api/keys (list_services + get_masked_credentials) | `get_masked_credentials(service)` returns ****+last6 for sensitive fields |
| **Database (APIKey)** | `data/trading.db` → table `api_keys` (exchange, api_key_encrypted, api_secret_encrypted, passphrase_encrypted, is_connected, last_tested) | dashboard app.py: /api/keys/list, /api/keys/test, /api/keys/save | List endpoint returns masked_key (helper), has_key, has_secret; raw values not sent in list |

- **Sensitive field names** (SecureConfigManager): api_key, api_secret, bot_token, password, app_password, secret, private_key.
- **Credentials file security:** chmod 0o600 on key file and credentials file (Unix). Docs (SETUP, FAQ) say do not commit `config/credentials.json` or `config/encryption.key`.

### 2.2 Services that use API keys or secrets (from README, API_KEYS.md, code)

| Service / integration | Config / storage | Keys / secrets | Referenced in |
|----------------------|------------------|----------------|---------------|
| **Polymarket** | SecureConfigManager "polymarket", or config | api_key (optional for public) | run_bot PolymarketClient, data_sources_api, API_KEYS.md, clients/polymarket_client |
| **Crypto (CoinGecko, Binance, etc.)** | SecureConfigManager "crypto" | api_key (optional for CoinGecko) | run_bot CoinGeckoClient, data_sources_api, API_KEYS.md, config.example crypto_apis |
| **Telegram** | config.yaml `telegram.bot_token`, `telegram.chat_id`; or SecureConfigManager "telegram" | bot_token, chat_id | telegram_bot, notification_service, notifier, settings_models, API_KEYS.md |
| **Email** | config or SecureConfigManager "email" | password (app password), smtp_*, from_email, to_email | notifications, data_sources_api (masked), API_KEYS.md |
| **Exchange API keys (UI)** | Database APIKey model | api_key, api_secret (per exchange: binance, polymarket, coinbase, kraken) | dashboard api_keys.html, app.py /api/keys/list, test, save; database.models.APIKey |
| **Weather (NOAA)** | config `strategies.weather_trading.noaa_api_key` or env `NOAA_API_KEY` | noaa_api_key | strategies/weather_trading, utils/weather_api, NEW_FEATURES |
| **Kalshi** | exchanges/kalshi_client | config.api_key | kalshi_client.py |

### 2.3 API endpoints that touch credentials

- **GET /api/settings/data-sources** (data_sources_api): Returns masked credentials only (get_masked_credentials for polymarket, crypto, telegram, email).
- **POST /api/settings/data-sources**: Saves credentials via SecureConfigManager.save_api_credentials(service, credentials); no logging of body in route (credentials could be in request body).
- **POST /api/settings/test-connection**: Receives or loads credentials, passes to clients for test; credentials in memory/request.
- **GET /api/keys/list** (app.py): Returns list with masked_key, has_key, has_secret (no raw api_key_encrypted or api_secret_encrypted in response).
- **GET /api/keys** (app.py): Uses list_services + get_masked_credentials; returns masked only.
- **POST /api/keys/test** (app.py): Request body can contain exchange, api_key, api_secret; code comment says “Do not log api_key or api_secret”; no logging of body.
- **POST /api/keys/save** (app.py): Request body contains api_key, api_secret; no logging of keys; stores via APIKey.save_key (exchange, api_key, api_secret) — comment says “in production use SecureConfigManager or encrypt before DB”.
- **Settings export (app.py):** Redaction in place for api_key in channel and bot_token in config when exporting (lines 2168–2176).
- **Duplicate routes:** Multiple /api/keys/test and /api/settings and /api/keys routes exist in app.py (different line numbers); behavior may differ (e.g. one uses SecureConfigManager, one uses APIKey).

### 2.4 Where credentials could be logged or exposed

- **SecureConfigManager:** Uses print() for errors in _load_credentials and _save_credentials; could be switched to logger without including credential values.
- **run_bot:** Uses get_api_credentials and passes to clients; no evidence of logging the credential values.
- **data_sources_api test_connection:** Credentials come from request or get_api_credentials; not logged in the route.
- **audit_logger (services/audit_logger.py):** Lists "api_key", "bot_token" among redacted keys (line 300–301); suggests audit logs are intended to redact these.
- **Database APIKey:** get_all() returns full rows including api_key_encrypted and api_secret_encrypted; list_api_keys in app.py now returns only masked representation. Any other caller of APIKey.get_all() could expose raw values if sent to frontend or logs.

### 2.5 Dependency visibility (strategy ↔ key)

- **Documented in API_KEYS.md:** CoinGecko (crypto), Polymarket (market data), Telegram (notifications), Email (alerts). No single “strategy → key” matrix in docs.
- **Code:** run_bot uses polymarket and crypto credentials for market/client setup; telegram/email for notifications. Weather strategy uses noaa_api_key. Kalshi client uses api_key from config.
- **Dashboard:** No existing API or UI that lists “which strategies depend on which keys.” Phase 6B previously added API_KEY_DEPENDENCIES in app.py (not re-auditing that change here; audit is of current/referenced state). If present, it is a static map for UI only.

---

## 3. Operational controls

### 3.1 Bot process control (start / stop / restart)

- **README / docs:** Bot started via `python bot.py` or `python run_bot.py`; stop via Ctrl+C or `kill_switch: true` in config.
- **Dashboard routes (app.py):**  
  - `POST /api/bot/start`, `POST /api/bot/stop`, `POST /api/bot/restart`  
  - Implementations only update in-memory `bot_status` (e.g. last_restart); comment says “This would trigger bot start” (not implemented). No subprocess or process manager call to start/stop the engine.
- **Bot status:** `GET /api/bot/status` prefers engine state (state/bot_state.json); fallback is process scan for main.py/run_bot.py/bot.py. Returns control_disabled: true and control_note that engine runs via python main.py and TUI (python bot.py) for pause/resume.
- **Conclusion:** Start/stop/restart from dashboard are non-functional for actually starting/stopping the process; they only update in-memory state. Real control is terminal or config (kill_switch).

### 3.2 Trading mode (paper vs live)

- **Config:** `paper_trading: true` (default) in config.yaml. README and docs strongly warn not to set to false without understanding.
- **Dashboard (app.py):**  
  - `GET /api/settings/trading-mode`: Returns mode, paper_trading, requires_restart, warning (implemented in Phase 6B).  
  - `POST /api/settings/set-trading-mode`: Accepts mode and confirm_phrase; for live requires confirm_phrase === "LIVE"; writes config.yaml.  
  - `POST /api/settings/toggle-mode`: Legacy toggle; flips paper_trading in config and saves. No confirmation step.
- **ConfigLoader defaults:** paper_trading True; feature_real_trading False.
- **Risk:** Toggle and set-trading-mode both write config.yaml. No in-app indication of “takes effect after restart” on all code paths unless explicitly returned in set-trading-mode response.

### 3.3 Kill switch and emergency controls

- **Config file:** `kill_switch: false` in config.example.yaml; documented as “set to true to stop immediately.”
- **Emergency service:** `services/emergency_kill_switch.py` — activate/deactivate kill switch; uses Config (database/config store) for kill_switch_active, reason, activated_at, activated_by. Sets emergency_disabled on strategies in DB.
- **Dashboard routes (emergency_bp):**  
  - `GET /api/emergency/kill-switch/status`  
  - `POST /api/emergency/kill-switch/activate` (body: reason, close_positions, activated_by)  
  - `POST /api/emergency/kill-switch/deactivate` (body: admin_password)  
  - `GET /api/emergency/health/summary`  
  - `POST /api/emergency/strategy/pause`, resume, enable, disable (strategy_name, reason)
- **PR20L / docs:** Position closing on kill switch noted as not implemented; health/summary and strategy pause/resume/enable/disable are implemented.

### 3.4 System updates and version

- **VersionManager (version_manager.py):** Reads VERSION file, can fetch latest release from GitHub (AlexMeisenzahl/market-strategy-testing-bot), get_current_version, set_current_version, update history in logs/update_history.json.
- **UpdateService (services/update_service.py):** Lock file, backups, pre_flight_checks, perform_update, get_progress, rollback, unlock. Used by dashboard update routes.
- **Dashboard routes (app.py):**  
  - `GET /api/update/check`  
  - `GET /api/update/history`  
  - `POST /api/update/start`  
  - `GET /api/update/progress`  
  - `POST /api/update/cancel`  
  - `POST /api/update/rollback`
- **Docs:** AUTO_UPDATE_IMPLEMENTATION.md, UPDATE_FAILURE_GUIDE.md, PRE_UPDATE_CHECKLIST.md, scripts/emergency_rollback.sh. Self-update is implemented; UI may or may not expose all of these endpoints.

### 3.5 Strategy enable/disable and pause

- **Config:** strategies.<name>.enabled in config.yaml.
- **Dashboard:** PUT /api/settings/strategies updates strategy settings (config_manager).
- **Emergency routes:** strategy pause/resume/enable/disable operate on DB (Strategy model: enabled, auto_disabled, emergency_disabled, disable_reason). So two layers: config (per strategy enabled) and DB (runtime enable/disable/pause). Which one the execution engine respects depends on run_bot/strategy_manager.

---

## 4. Summary tables

### 4.1 Configuration surface

| Area | Source of truth | Writable from dashboard | Requires restart / re-run |
|------|-----------------|--------------------------|----------------------------|
| paper_trading, kill_switch | config.yaml | Yes (toggle-mode, set-trading-mode) | Config change; engine typically needs restart to re-read |
| Notifications (desktop, email, telegram) | config.yaml | Yes (settings/notifications) | Unclear from code |
| Strategy enabled/params | config.yaml | Yes (settings/strategies) | Unclear |
| Data source credentials | config/credentials.json (SecureConfigManager) | Yes (data-sources POST) | run_bot reads at startup |
| Exchange keys (Binance, etc.) | data/trading.db (APIKey) | Yes (keys/save) | Depends on how engine loads keys |
| Dashboard port, debug | config dashboard section | Possible via settings/config | Dashboard restart |

### 4.2 API keys and integrations referenced

| Integration | Key/secret | Stored in | Masked in API |
|-------------|------------|-----------|----------------|
| Polymarket | api_key (optional) | SecureConfigManager or config | Yes (data-sources GET, get_masked) |
| Crypto (CoinGecko, etc.) | api_key (optional) | SecureConfigManager | Yes |
| Telegram | bot_token, chat_id | config or SecureConfigManager | Yes (data-sources); export redacts bot_token |
| Email | password, smtp_* | config or SecureConfigManager | Yes (masked); export redacts |
| Binance/Polymarket/Coinbase/Kraken (UI) | api_key, api_secret | DB (api_keys) | Yes in /api/keys/list (masked_key) |
| NOAA (weather) | noaa_api_key | config / env | Not in credential store; in strategy config |
| Kalshi | api_key | config (exchanges) | Not audited in dashboard |

### 4.3 Operational control endpoints

| Control | Method | Route | Actually changes process/config |
|---------|--------|-------|----------------------------------|
| Bot status | GET | /api/bot/status | No; reads state or process list |
| Bot start | POST | /api/bot/start | No; in-memory only |
| Bot stop | POST | /api/bot/stop | No; in-memory only |
| Bot restart | POST | /api/bot/restart | No; in-memory only |
| Trading mode | GET | /api/settings/trading-mode | No |
| Trading mode | POST | /api/settings/set-trading-mode | Yes; config.yaml |
| Trading mode (legacy) | POST | /api/settings/toggle-mode | Yes; config.yaml |
| Kill switch status | GET | /api/emergency/kill-switch/status | No |
| Kill switch activate | POST | /api/emergency/kill-switch/activate | Yes; DB/Config + strategy flags |
| Kill switch deactivate | POST | /api/emergency/kill-switch/deactivate | Yes |
| Strategy pause/resume/enable/disable | POST | /api/emergency/strategy/* | Yes; DB Strategy |
| Update check | GET | /api/update/check | No |
| Update start | POST | /api/update/start | Yes; background update |
| Update progress | GET | /api/update/progress | No |
| Update cancel/rollback | POST | /api/update/cancel, rollback | Yes |

---

## 5. Gaps and risks (factual)

- **Dual credential systems:** SecureConfigManager (config/credentials.json) vs database APIKey (api_keys table). Dashboard uses both; run_bot uses SecureConfigManager for polymarket/crypto. Saving from api_keys UI does not use SecureConfigManager (per comment in save handler).
- **APIKey storage:** save_key in database.models stores api_key and api_secret in columns named api_key_encrypted/api_secret_encrypted but the save route passes plain values; encryption at rest is not confirmed in the model implementation.
- **Multiple overlapping routes:** Several /api/keys/* and /api/settings/* and /api/keys/test definitions in app.py; different behaviors (e.g. list from DB vs list from SecureConfigManager) can confuse which backend is authoritative.
- **Trading mode:** Legacy toggle has no confirmation; set-trading-mode has confirmation for live. Both write config; “requires restart” is stated in set-trading-mode response but not necessarily in UI or for toggle.
- **Process control:** Bot start/stop/restart in dashboard do not start/stop the engine process; docs and control_note state that engine is run from terminal.
- **Kill switch:** Config kill_switch (file) vs emergency_kill_switch (DB/Config state). Engine must read both or one; behavior under “kill_switch: true” in config vs “kill switch activated” via API is not re-verified here.
- **Credentials in logs:** SecureConfigManager uses print() on errors; audit_logger redacts api_key/bot_token. No evidence of logging raw secrets in key/save/test routes; risk is any future log of request body or get_all() rows.

---

**End of audit. No UI or code changes proposed. Awaiting approval before Phase 6B implementation.**

# Phase 7C: Secure Configuration & API Key Finalization

**Objective:** One credential system, one trading-mode path, zero ambiguous configuration writes. Configuration and credentials are singular, secure, and manageable from the dashboard without weakening Phase 7A safety.

---

## 1. Canonical API Key System

**Chosen system: SecureConfigManager only.**

| Aspect | Detail |
|--------|--------|
| **Storage** | `config/credentials.json` (encrypted via Fernet), key in `config/encryption.key` |
| **Backend** | `services/secure_config_manager.SecureConfigManager` |
| **Used by** | `run_bot.py` (polymarket, crypto), dashboard System & Settings UI |

**All UI writes go to one system only:**

- **List (read):** `GET /api/settings/integrations` — returns masked credentials and "used by" hints. Implemented in `dashboard/routes/data_sources_api.py`.
- **Write:** `POST /api/settings/data-sources` — body: `{ "service": "polymarket"|"crypto"|"telegram"|"email", "credentials": { ... } }`. Merges with existing credentials (partial updates supported). Implemented in `data_sources_api.save_data_sources()`.
- **Test:** `POST /api/settings/test-connection` — body: `{ "service": "...", "credentials": {...} }` (optional; uses saved if omitted). Implemented in `data_sources_api.test_connection()`.

**DB `api_keys` (database APIKey model):**

- **Status:** Deprecated for writes. No UI or API may write credentials to the database.
- **Read-only:** Retained only for backward compatibility where code still reads; no new writes.
- **Legacy routes:** `/api/keys/list`, `/api/keys/save`, `/api/keys/test` (the ones that wrote to DB or were duplicates) now return **410 Gone** with a JSON body pointing to System & Settings and the canonical endpoints above.

**Backward-compatible read-only:**

- `GET /api/keys` — Proxies to SecureConfigManager: returns list of services with masked credentials (same canonical source as integrations).
- `GET /api/keys/dependencies` — Read-only; returns which strategies/integrations use which keys.

---

## 2. Route & Storage Cleanup

**Consolidated / deprecated:**

| Old / duplicate | Action |
|-----------------|--------|
| `POST /api/settings/toggle-mode` | **Removed.** No confirmation; ambiguous with `set-trading-mode`. Use only `GET /api/settings/trading-mode` and `POST /api/settings/set-trading-mode`. |
| `POST /api/keys` (provider + key) | **Removed.** Called non-existent `set_api_key`; writes go to `POST /api/settings/data-sources` only. |
| `POST /api/keys/test` (multiple definitions) | **Removed** (4 duplicate handlers). Canonical test: `POST /api/settings/test-connection`. |
| `GET /api/keys/list` (DB) | **Deprecated.** Returns 410; use `GET /api/settings/integrations`. |
| `POST /api/keys/save` (DB) | **Deprecated.** Returns 410; use `POST /api/settings/data-sources`. |
| `POST /api/keys/test` (DB or other) | **Deprecated.** Returns 410; use `POST /api/settings/test-connection`. |

**Canonical config/credentials routes (no ambiguous write paths):**

| Purpose | Method | Path | Notes |
|---------|--------|------|--------|
| List integrations (masked) | GET | `/api/settings/integrations` | SecureConfigManager only |
| Save credentials | POST | `/api/settings/data-sources` | Only write path for credentials |
| Test connection | POST | `/api/settings/test-connection` | Only test path |
| Data sources (legacy shape) | GET | `/api/settings/data-sources` | Masked; read-only |
| Data mode | GET | `/api/settings/data-mode` | Read-only |

Other `/api/settings/*` routes (e.g. notifications, strategies, config, reset, export, import) are unchanged and do not duplicate credential write paths.

---

## 3. Trading Mode Cleanup

**Single explicit, gated path:**

| Action | Endpoint | Behavior |
|--------|----------|----------|
| Read current mode | `GET /api/settings/trading-mode` | Returns `mode`, `paper_trading`, `requires_restart`, `warning`. |
| Set mode | `POST /api/settings/set-trading-mode` | Body: `mode` (`paper` \| `live`). For `live`, body must include `confirm_phrase: "LIVE"`. Writes `config.yaml`. Returns `requires_restart: true`. |

**Removed:**

- `POST /api/settings/toggle-mode` — Legacy toggle with no confirmation. Removed so there is no way to switch to live without explicit confirmation.

**Paper → live:** Still disabled for actual execution (Phase 7A: execution gate requires `paper_trading: true`). Changing to live only updates config; no execution controls added.

---

## 4. Restart Semantics

Config fields in the System & Settings UI are labeled so behavior matches user expectations:

| Section | Label | Behavior |
|---------|--------|----------|
| Trading mode | **Restart required** | Engine reads `config.yaml` at startup; change takes effect after restart. |
| API keys & integrations | **Restart required** | Credentials read by engine at startup; new credentials take effect after restart. |
| Strategy defaults | **Restart required** + **Informational only** | Config edited outside dashboard; engine reads at startup. |
| Execution settings | **Informational only** | No editable execution controls; engine control via dashboard or `python main.py`. |
| System updates | **Restart required after update** | Update runs in background; restart required after update. |
| Advanced | **Informational only** | No execution controls. |

No "hot-reload" credential or trading-mode paths exist; all such changes require engine restart.

---

## 5. UI Scope (Allowed)

- API key management UI: System & Settings → "API keys & integrations" (masked inputs, test connection, update per service).
- Legacy `/api_keys` page: Shows deprecation notice and link to System & Settings; no credential inputs.
- Dependency hints: "Used by X strategies" shown in integrations list (from `data_sources_api.INTEGRATION_DEPENDENCIES`).
- **No execution controls** (Phase 7A unchanged).

---

## 6. Exit Condition

- **One credential system:** SecureConfigManager. All credential writes go through `POST /api/settings/data-sources`.
- **One trading-mode toggle:** Only `POST /api/settings/set-trading-mode` (with confirmation for live). No legacy toggle.
- **Zero ambiguous configuration writes:** Duplicate and DB-write routes removed or return 410 with canonical redirect.

**Code references:**

- Credential read/write/test: `dashboard/routes/data_sources_api.py`, `services/secure_config_manager.py`.
- Trading mode: `dashboard/app.py` — `get_trading_mode()`, `set_trading_mode()`; no `toggle_trading_mode()`.
- Deprecated key routes: `dashboard/app.py` — `list_api_keys()`, `save_api_key_deprecated()`, `test_api_key_deprecated()` (410); `get_api_keys()` (read-only proxy), `get_key_dependencies()` (read-only).

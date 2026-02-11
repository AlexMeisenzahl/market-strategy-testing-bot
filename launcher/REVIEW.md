# Launcher code review

Review focused on: process leaks, cross-platform behavior, update races, and half-running states.

---

## 1. Process-leak risks

| Risk | Status | Notes |
|------|--------|--------|
| **Port timeout** | Fixed | Previously: engine + dashboard were started but if `wait_for_port` timed out, we showed Error and returned without stopping them. Now `_cleanup_and_error()` stops both and clears refs. |
| **Exception in _start_worker** | Fixed | Any exception after starting engine/dashboard now goes through `_cleanup_and_error()` so both processes are stopped and refs cleared. |
| **Force-quit launcher** | Accepted | If the launcher is killed (e.g. SIGKILL, or “Force Quit”) without running `_on_close`, engine and dashboard can keep running. Normal close runs `_on_close` → `_stop()` → `release_lock()`. Mitigation: document “quit via window close” or add an optional atexit handler that tries to kill children by PID (stored in lock file). |

---

## 2. Cross-platform inconsistencies

| Area | Behavior |
|------|----------|
| **Single-instance check** | Windows: `OpenProcess(0x100000)`; Unix: `os.kill(pid, 0)`. Both only test “process exists”. |
| **Lock file** | If `portalocker` is available (project dependency), we use an exclusive file lock so two instances can’t both acquire. Without it, we fall back to PID-file only (small race on double start). |
| **Open Logs** | Windows: `os.startfile(path)`; macOS: `open path`; else: `xdg-open` (Linux). Spec is macOS + Windows; Linux is best-effort. |
| **Subprocess** | Windows: `CREATE_NO_WINDOW` so no extra console. Unix: no flag. |
| **Terminate** | `Popen.terminate()`: SIGTERM on Unix, `TerminateProcess` on Windows. Same API. |

Unused imports (`signal`, `ttk`) were removed.

---

## 3. Update race conditions

| Scenario | Handling |
|----------|----------|
| **Two launchers at once** | `acquire_lock()` uses portalocker (if present) for an exclusive lock before writing PID; second instance gets `LockException` and exits. Without portalocker, a small race remains (both may pass the “stale PID” check and both write). |
| **Start vs Update** | “Check for Updates” → “Pull and restart” runs `_do_update_flow()` on the main (GUI) thread and is modal via messagebox; user can’t click Start during that. |
| **Launch-time update** | Same: update prompt and `_do_update_flow()` run before `mainloop()`, so no concurrent Start. |

No update logic runs on a background thread; no races between update and start.

---

## 4. Half-running scenarios

| Scenario | Handling |
|---------|----------|
| **Engine started, dashboard fails to start** | We call `stop_processes(self.engine_proc, None)` and set `self.engine_proc = None`. No orphan engine. |
| **Both started, port never ready** | We call `_cleanup_and_error(...)`: stop both, clear both refs, show error. No half-running. |
| **Any exception in _start_worker** | `except` calls `_cleanup_and_error(str(e))`: stop both, clear both refs. No half-running. |
| **User clicks Restart** | `_restart` → `_stop()` (stops both, clears refs) → after 500 ms `_start()`. If port is still in use, Start shows error and does not start new processes; previous ones are already stopped. |

All failure paths during start now stop and clear engine and dashboard so the bot is never left half-running under launcher control.

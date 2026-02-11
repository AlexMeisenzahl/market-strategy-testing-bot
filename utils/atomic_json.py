"""
Atomic JSON file I/O with cross-platform locking and corruption recovery.

- Write to temp file in same directory, flush + fsync, then os.replace for atomic swap.
- Use portalocker for cross-platform file locking (macOS, Linux, Windows).
- On load failure: log error, attempt fallback to last known good (e.g. .backup), fail safely.
- Validate required keys on load; attempt safe repair or default fallback on missing keys.
"""

import json
import os
import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)

try:
    import portalocker
except ImportError:
    portalocker = None  # type: ignore


# Default required keys for bot_state schema (can be overridden per call)
BOT_STATE_REQUIRED_KEYS: Set[str] = {
    "balance",
    "last_update",
    "positions",
    "status",
    "trading",
}


def _fsync_dir(path: Path) -> None:
    """Sync directory to ensure rename is durable (POSIX). No-op on Windows if not supported."""
    try:
        fd = os.open(str(path.parent), os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    except OSError:
        pass


def atomic_write_json(
    path: Path,
    data: Any,
    *,
    indent: int = 2,
    backup_path: Optional[Path] = None,
) -> None:
    """
    Write JSON atomically: temp file in same directory, flush + fsync, then os.replace.
    Optionally keep a backup copy before replacing. Validates data is serializable.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.parent / (path.name + ".tmp." + str(os.getpid()))
    try:
        payload = json.dumps(data, indent=indent)
    except (TypeError, ValueError) as e:
        logger.error("atomic_write_json: cannot serialize data: %s", e)
        raise
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(payload)
            f.flush()
            os.fsync(f.fileno())
        _fsync_dir(path)
        if backup_path is not None and path.exists():
            try:
                with open(path, "r", encoding="utf-8") as src:
                    content = src.read()
                with open(backup_path, "w", encoding="utf-8") as dst:
                    dst.write(content)
                    dst.flush()
                    os.fsync(dst.fileno())
            except OSError as e:
                logger.warning("atomic_write_json: backup failed: %s", e)
        os.replace(tmp, path)
    except Exception:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass
        raise
    finally:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass


def load_json(
    path: Path,
    default: Any = None,
    *,
    required_keys: Optional[Set[str]] = None,
    backup_path: Optional[Path] = None,
    repair_with_defaults: Optional[Callable[[Dict], Dict]] = None,
) -> Any:
    """
    Load JSON with corruption recovery and optional schema validation.
    - On JSON error: log detail, try backup_path if provided, else return default.
    - If required_keys given and missing: log error, run repair_with_defaults if provided, else return default.
    """
    path = Path(path)
    default = default if default is not None else {}
    required_keys = required_keys or set()
    backup_path = backup_path or path.parent / (path.name + ".backup")

    def _load(p: Path) -> Optional[Any]:
        try:
            if not p.exists():
                return None
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.error("load_json: invalid JSON in %s: %s", p, e)
            return None
        except OSError as e:
            logger.error("load_json: read error %s: %s", p, e)
            return None

    data = _load(path)
    if data is None and backup_path != path and backup_path.exists():
        logger.warning("load_json: falling back to backup %s", backup_path)
        data = _load(backup_path)

    if data is None:
        return default

    if required_keys and isinstance(data, dict):
        missing = required_keys - set(data.keys())
        if missing:
            logger.error("load_json: missing required keys %s in %s", missing, path)
            if repair_with_defaults:
                try:
                    data = repair_with_defaults(data)
                    if required_keys - set(data.keys()):
                        return default
                except Exception as e:
                    logger.error("load_json: repair failed: %s", e)
                    return default
            else:
                return default

    return data


def locked_load_json(
    path: Path,
    default: Any = None,
    *,
    required_keys: Optional[Set[str]] = None,
    backup_path: Optional[Path] = None,
    repair_with_defaults: Optional[Callable[[Dict], Dict]] = None,
    timeout: float = 10.0,
) -> Any:
    """
    Load JSON with shared (read) lock. Use when another process may be writing.
    Falls back to load_json without lock if portalocker is not installed.
    """
    if not portalocker:
        return load_json(
            path,
            default,
            required_keys=required_keys,
            backup_path=backup_path,
            repair_with_defaults=repair_with_defaults,
        )
    path = Path(path)
    if not path.exists():
        return default if default is not None else {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            portalocker.lock(f, portalocker.LOCK_SH, timeout=timeout)
            try:
                data = json.load(f)
            finally:
                portalocker.unlock(f)
        if required_keys and isinstance(data, dict):
            missing = required_keys - set(data.keys())
            if missing:
                logger.error("locked_load_json: missing required keys %s", missing)
                if repair_with_defaults:
                    try:
                        data = repair_with_defaults(data)
                    except Exception:
                        return default if default is not None else {}
                else:
                    return default if default is not None else {}
        return data
    except (json.JSONDecodeError, OSError) as e:
        logger.error("locked_load_json: %s", e)
        return load_json(
            path,
            default,
            required_keys=required_keys,
            backup_path=backup_path,
            repair_with_defaults=repair_with_defaults,
        )
    except portalocker.LockException:
        logger.warning("locked_load_json: lock timeout on %s", path)
        return load_json(
            path,
            default,
            required_keys=required_keys,
            backup_path=backup_path,
            repair_with_defaults=repair_with_defaults,
        )


def locked_write_json(
    path: Path,
    data: Any,
    *,
    indent: int = 2,
    backup_path: Optional[Path] = None,
    timeout: float = 10.0,
) -> None:
    """
    Write JSON atomically with exclusive lock during write.
    Uses atomic_write_json for the actual write; lock is held on a separate lock file.
    """
    path = Path(path)
    lock_path = path.parent / (path.name + ".lock")
    path.parent.mkdir(parents=True, exist_ok=True)
    if portalocker:
        try:
            with open(lock_path, "a") as lf:
                portalocker.lock(lf, portalocker.LOCK_EX, timeout=timeout)
                try:
                    atomic_write_json(
                        path,
                        data,
                        indent=indent,
                        backup_path=backup_path,
                    )
                finally:
                    portalocker.unlock(lf)
        except portalocker.LockException:
            logger.warning("locked_write_json: lock timeout on %s", lock_path)
            atomic_write_json(
                path,
                data,
                indent=indent,
                backup_path=backup_path,
            )
    else:
        atomic_write_json(
            path,
            data,
            indent=indent,
            backup_path=backup_path,
        )


def bot_state_repair(data: Dict[str, Any]) -> Dict[str, Any]:
    """Safe repair for bot_state: ensure required keys exist with safe defaults."""
    from datetime import datetime, timezone

    defaults = {
        "balance": 0.0,
        "last_update": datetime.now(timezone.utc).isoformat(),
        "positions": [],
        "status": "stopped",
        "trading": {
            "opportunities_found": 0,
            "trades_executed": 0,
            "paper_profit": 0.0,
        },
        "connection": data.get("connection") or {"healthy": False, "response_time_ms": 0},
        "rate_limit": data.get("rate_limit") or {"usage_pct": 0, "remaining": 0, "reset_seconds": 0},
        "runtime_seconds": data.get("runtime_seconds", 0),
    }
    for k, v in defaults.items():
        if k not in data:
            data[k] = v
    return data

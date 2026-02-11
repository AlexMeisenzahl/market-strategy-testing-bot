"""
Dashboard route blueprints and startup validation.

Refactor summary (prevents duplicate endpoint crashes):
- Routes are split into blueprints: core, journal, settings, strategies, system
  (plus existing config_api, leaderboard, emergency, data_sources_api).
- Every route specifies an explicit endpoint= (e.g. endpoint="journal_save_entry").
  Flask does not allow dots in endpoint names; use underscores (core_health, journal_save_entry).
- No two routes may share the same endpoint. If the same view serves multiple URLs,
  each URL must have a unique endpoint (e.g. core_health and core_health_api).
- validate_no_duplicate_endpoints(app) runs after all blueprints are registered
  and raises RuntimeError with a clear message if any duplicate is found.
- Blueprint modules: core, journal, settings, strategies, system (each defines the blueprint;
  routes are registered on these blueprints in app.py). They are registered at the end of app.py.

This prevents future route collisions because: (1) namespacing by blueprint and
explicit endpoint names make accidental duplicates obvious; (2) startup validation
fails fast before any request is served.
"""

from flask import Flask


def validate_no_duplicate_endpoints(app: Flask) -> None:
    """
    Validate that no two registered routes share the same endpoint name.
    Call this after all blueprints are registered. Fails fast with a clear error.
    """
    seen: dict[str, str] = {}
    for rule in app.url_map.iter_rules():
        endpoint = rule.endpoint
        if endpoint in seen:
            raise RuntimeError(
                f"Duplicate Flask endpoint '{endpoint}'. "
                f"First rule: {seen[endpoint]}, second rule: {rule.rule}. "
                "Every @route must specify a unique endpoint= (e.g. endpoint='journal_save_entry')."
            )
        seen[endpoint] = rule.rule

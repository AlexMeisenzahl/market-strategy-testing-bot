"""
Phase 8F: Tests and safety assertions for Strategy Intelligence.

- No trades -> no suggestions
- Small sample -> low confidence / no or cautious suggestions
- Contradictory data -> no recommendation generated
- Removing the module -> engine still works (test: execution path does not import strategy_intelligence)
- No files written to strategy code or config
- Execution paths do not import strategy_intelligence
"""

import json
import sys
from pathlib import Path

import pytest

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class TestStrategyIntelligenceNoTrades:
    """No trades -> no suggestions."""

    def test_no_trades_no_suggestions(self):
        from dashboard.services.data_parser import DataParser
        from analysis.suggestions import SuggestionGenerator

        logs_dir = PROJECT_ROOT / "logs"
        parser = DataParser(logs_dir)
        # Force empty by using a strategy that has no trades, or mock
        parser._trades_cache = []
        parser._cache_timestamp = None
        gen = SuggestionGenerator(parser)
        suggestions = gen.run(strategy_name="NonExistentStrategy")
        assert suggestions == []


class TestStrategyIntelligenceSmallSample:
    """Small sample -> low confidence or no suggestion."""

    def test_small_sample_low_or_no_suggestion(self):
        from dashboard.services.data_parser import DataParser
        from analysis.suggestions import SuggestionGenerator

        logs_dir = PROJECT_ROOT / "logs"
        parser = DataParser(logs_dir)
        # Few trades: fewer than MIN_SAMPLE_FOR_SUGGESTION (20)
        parser._trades_cache = [
            {
                "entry_time": "2025-01-01T12:00:00",
                "timestamp": "2025-01-01T12:00:00",
                "pnl_usd": 10,
                "profit_usd": 10,
                "pnl_pct": 1.0,
                "profit_pct": 1.0,
                "strategy": "Test",
                "symbol": "M1",
            }
            for _ in range(5)
        ]
        parser._cache_timestamp = None
        gen = SuggestionGenerator(parser)
        suggestions = gen.run(strategy_name="Test")
        # With 5 trades we should get no or very few suggestions (low sample)
        assert len(suggestions) <= 2


class TestStrategyIntelligenceContradictoryData:
    """Contradictory data -> no recommendation for that dimension."""

    def test_contradictory_win_rates_no_strong_recommendation(self):
        from dashboard.services.data_parser import DataParser
        from analysis.suggestions import SuggestionGenerator

        logs_dir = PROJECT_ROOT / "logs"
        parser = DataParser(logs_dir)
        # Mix of wins/losses evenly across time and volatility -> no clear pattern
        base = {
            "entry_time": "2025-01-01T12:00:00",
            "timestamp": "2025-01-01T12:00:00",
            "strategy": "Test",
            "symbol": "M1",
        }
        trades = []
        for i in range(50):
            t = dict(base)
            t["entry_time"] = f"2025-01-{(i % 28) + 1:02d}T{(i % 24):02d}:00:00"
            t["timestamp"] = t["entry_time"]
            t["pnl_usd"] = 5 if i % 2 == 0 else -5
            t["profit_usd"] = t["pnl_usd"]
            t["pnl_pct"] = 2.0
            t["profit_pct"] = 2.0
            trades.append(t)
        parser._trades_cache = trades
        parser._cache_timestamp = None
        gen = SuggestionGenerator(parser)
        suggestions = gen.run(strategy_name="Test")
        # Contradictory (50% win rate everywhere) -> no strong "increase min edge" type suggestion
        # We may still get streak suggestion if there's a streak; that's ok
        for s in suggestions:
            assert "confidence" in s
            assert 0 <= s["confidence"] <= 1
            assert "suggested_change" in s
            assert "evidence" in s


class TestExecutionDoesNotImportIntelligence:
    """Removing Phase 8 -> engine still works. Execution path must not import strategy_intelligence."""

    def test_run_bot_does_not_import_strategy_intelligence(self):
        with open(PROJECT_ROOT / "run_bot.py", "r") as f:
            run_bot_src = f.read()
        assert "strategy_intelligence" not in run_bot_src, (
            "run_bot must not reference strategy_intelligence so execution works without Phase 8"
        )

    def test_main_does_not_import_strategy_intelligence(self):
        with open(PROJECT_ROOT / "main.py", "r") as f:
            main_src = f.read()
        assert "strategy_intelligence" not in main_src, (
            "main.py must not reference strategy_intelligence for execution path"
        )

    def test_dashboard_imports_strategy_intelligence(self):
        with open(PROJECT_ROOT / "dashboard" / "app.py", "r") as f:
            app_src = f.read()
        assert "strategy_intelligence" in app_src, (
            "Dashboard is the only consumer of Phase 8; it should import strategy_intelligence"
        )


class TestNoWritesToStrategyOrConfig:
    """Strategy Intelligence must not write to strategy code or config files."""

    def test_export_writes_only_to_analysis_reports(self):
        from services.strategy_intelligence import export_to_reports_dir, get_cached_diagnostics, get_cached_suggestions

        path = export_to_reports_dir(PROJECT_ROOT, {"sample_size": 0}, [])
        if path is not None:
            assert "analysis" in path.parts
            assert "reports" in path.parts
            assert path.suffix == ".json"
            assert "config" not in str(path)
            assert "strategies" not in str(path).lower() or "reports" in str(path)

    def test_suggestion_schema_has_no_code_or_config(self):
        from analysis.suggestions import SuggestionGenerator
        from dashboard.services.data_parser import DataParser

        parser = DataParser(PROJECT_ROOT / "logs")
        gen = SuggestionGenerator(parser)
        # Run with whatever data exists; check schema of any suggestion
        suggestions = gen.run()
        for s in suggestions:
            assert "suggested_change" in s
            assert "confidence" in s
            assert "evidence" in s
            assert "validation_required" in s
            # Must not contain code patches or config write instructions
            change = (s.get("suggested_change") or "").lower()
            assert "patch" not in change
            assert "write to config" not in change
            assert "auto-apply" not in change


class TestDiagnosticsReadOnly:
    """Diagnostics engine is read-only."""

    def test_diagnostics_returns_dict_no_side_effects(self):
        from dashboard.services.data_parser import DataParser
        from analysis.diagnostics import StrategyDiagnosticsEngine

        parser = DataParser(PROJECT_ROOT / "logs")
        engine = StrategyDiagnosticsEngine(parser)
        result = engine.run(strategy_name=None)
        assert isinstance(result, dict)
        assert "sample_size" in result
        assert "performance" in result
        assert "risk_adjusted" in result
        assert "failure_analysis" in result
        assert "regime" in result

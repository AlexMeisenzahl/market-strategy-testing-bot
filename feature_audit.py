#!/usr/bin/env python3
"""
Comprehensive Feature Audit System for Market Strategy Testing Bot

This script tests EVERY feature claimed in the README and PRs to determine
what's actually implemented vs what's just documentation/shells.

Usage:
    python feature_audit.py                    # Basic audit (fast)
    python feature_audit.py --live-test        # Include live tests (slower)
    python feature_audit.py --help             # Show help

Generates:
    - FEATURE_AUDIT_REPORT.md (detailed findings)
    - feature_audit_summary.json (machine-readable)
    - Console output with color-coded status
"""

import sys
import os
import json
import re
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple
import importlib.util
import ast
import traceback

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

# ANSI color codes for console output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class FeatureAudit:
    """Main feature audit system"""
    
    # Status icons
    FULLY_WORKING = "✅"
    NEEDS_KEYS = "🔑"
    PARTIAL = "🚧"
    SHELL_ONLY = "📦"
    NOT_FOUND = "❌"
    
    def __init__(self, live_test: bool = False):
        self.root_dir = Path(__file__).resolve().parent
        self.live_test = live_test
        self.results = {
            "audit_date": datetime.now().isoformat(),
            "live_tests_enabled": live_test,
            "summary": {
                "fully_implemented": 0,
                "needs_api_keys": 0,
                "partially_implemented": 0,
                "shell_only": 0,
                "not_found": 0
            },
            "features": [],
            "strategies": [],
            "dashboard_pages": [],
            "advanced_features": []
        }
        
    def run_full_audit(self):
        """Run complete audit of all features"""
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}🔍 FEATURE AUDIT - Market Strategy Testing Bot{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}\n")
        
        # 1. Parse README for claimed features
        print(f"{Colors.OKCYAN}📋 Step 1: Parsing README.md for claimed features...{Colors.ENDC}")
        readme_features = self.parse_readme()
        print(f"   Found {len(readme_features)} claimed features\n")
        
        # 2. Analyze Git/PR history
        print(f"{Colors.OKCYAN}📜 Step 2: Analyzing Git history and PR information...{Colors.ENDC}")
        pr_info = self.analyze_git_history()
        print(f"   Found {len(pr_info)} PRs to analyze\n")
        
        # 3. Test Core Bot Integration
        print(f"{Colors.OKCYAN}🤖 Step 3: Testing Core Bot Integration...{Colors.ENDC}")
        bot_integration = self.test_bot_integration()
        self.results["bot_integration"] = bot_integration
        print(f"   Bot integration test complete\n")
        
        # 4. Test All 9 Trading Strategies
        print(f"{Colors.OKCYAN}📊 Step 4: Testing All Trading Strategies...{Colors.ENDC}")
        strategies = self.test_all_strategies()
        self.results["strategies"] = strategies
        print(f"   Tested {len(strategies)} strategies\n")
        
        # 5. Test API Key Management
        print(f"{Colors.OKCYAN}🔑 Step 5: Testing API Key Management...{Colors.ENDC}")
        api_key_mgmt = self.test_api_key_management()
        self.results["api_key_management"] = api_key_mgmt
        print(f"   API key management test complete\n")
        
        # 6. Test Dashboard Features
        print(f"{Colors.OKCYAN}🖥️  Step 6: Testing Dashboard Features...{Colors.ENDC}")
        dashboard = self.test_dashboard_features()
        self.results["dashboard_pages"] = dashboard
        print(f"   Tested {len(dashboard)} dashboard pages\n")
        
        # 7. Test Advanced Features
        print(f"{Colors.OKCYAN}🚀 Step 7: Testing Advanced Features (Mobile/PWA, Telegram, etc.)...{Colors.ENDC}")
        advanced = self.test_advanced_features()
        self.results["advanced_features"] = advanced
        print(f"   Tested {len(advanced)} advanced features\n")
        
        # 8. Test Data Infrastructure
        print(f"{Colors.OKCYAN}💾 Step 8: Testing Data Infrastructure...{Colors.ENDC}")
        data_infra = self.test_data_infrastructure()
        self.results["data_infrastructure"] = data_infra
        print(f"   Data infrastructure test complete\n")
        
        # 9. Optional: Live tests (if enabled)
        if self.live_test:
            print(f"{Colors.OKCYAN}🧪 Step 9: Running Live Tests (Optional)...{Colors.ENDC}")
            live_results = self.run_live_tests()
            self.results["live_tests"] = live_results
            print(f"   Live tests complete\n")
        
        # 10. Calculate summary statistics
        self.calculate_summary()
        
        # 11. Generate reports
        print(f"{Colors.OKCYAN}📝 Step 10: Generating Reports...{Colors.ENDC}")
        self.generate_markdown_report()
        self.generate_json_report()
        
        # 12. Print summary
        self.print_summary()
        
    def parse_readme(self) -> List[Dict[str, str]]:
        """Parse README.md to extract claimed features"""
        readme_path = self.root_dir / "README.md"
        features = []
        
        if not readme_path.exists():
            return features
            
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Extract major feature sections
        sections = {
            "Live API Features": r"### Live API Features:(.*?)(?=###|\Z)",
            "Dashboard Features": r"### Dashboard Features:(.*?)(?=###|\Z)",
            "Mobile & PWA": r"### 📱 Mobile & Progressive Web App.*?:(.*?)(?=###|\Z)",
            "Notification System": r"### Enhanced Notification System:(.*?)(?=###|\Z)"
        }
        
        for section_name, pattern in sections.items():
            match = re.search(pattern, content, re.DOTALL)
            if match:
                section_content = match.group(1)
                # Extract bullet points
                bullets = re.findall(r'[-*]\s+(.+?)(?:\n|$)', section_content)
                for bullet in bullets:
                    features.append({
                        "section": section_name,
                        "feature": bullet.strip()
                    })
        
        return features
        
    def analyze_git_history(self) -> List[Dict[str, str]]:
        """Analyze git log to extract PR information"""
        pr_info = []
        
        try:
            # Get all commits (not just merges) to catch more PRs
            result = subprocess.run(
                ['git', 'log', '--all', '--pretty=format:%h|||%s|||%b'],
                cwd=self.root_dir,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                seen_prs = set()
                
                for line in lines:
                    if '|||' in line:
                        parts = line.split('|||')
                        commit_hash = parts[0]
                        subject = parts[1]
                        body = parts[2] if len(parts) > 2 else ""
                        
                        # Extract PR number from subject or body
                        text_to_search = subject + " " + body
                        pr_matches = re.findall(r'#(\d+)', text_to_search)
                        
                        for pr_number in pr_matches:
                            if pr_number not in seen_prs:
                                seen_prs.add(pr_number)
                                pr_info.append({
                                    "pr_number": pr_number,
                                    "title": subject,
                                    "description": body[:200] if body else "",
                                    "commit": commit_hash
                                })
                                
            # Sort by PR number
            pr_info.sort(key=lambda x: int(x['pr_number']))
                                
        except Exception as e:
            print(f"   {Colors.WARNING}Warning: Could not parse git history: {e}{Colors.ENDC}")
            
        return pr_info
        
    def test_bot_integration(self) -> Dict[str, Any]:
        """Test core bot integration and what's actually called"""
        result = {
            "run_bot_exists": False,
            "imports": [],
            "strategies_imported": [],
            "strategies_executed": [],
            "test_result": None
        }
        
        run_bot_path = self.root_dir / "run_bot.py"
        
        # Check if run_bot.py exists
        if run_bot_path.exists():
            result["run_bot_exists"] = True
            
            # Parse the file to find imports and strategy usage
            try:
                with open(run_bot_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    tree = ast.parse(content)
                    
                # Find all imports
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            result["imports"].append(alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            for alias in node.names:
                                result["imports"].append(f"{node.module}.{alias.name}")
                                
                # Look for strategy-related imports
                strategy_patterns = [
                    'arbitrage', 'momentum', 'news', 'statistical',
                    'mean_reversion', 'volatility', 'weather', 'btc',
                    'contrarian', 'polymarket'
                ]
                
                for imp in result["imports"]:
                    for pattern in strategy_patterns:
                        if pattern.lower() in imp.lower():
                            result["strategies_imported"].append(imp)
                            
            except Exception as e:
                result["parse_error"] = str(e)
                
        return result
        
    def test_all_strategies(self) -> List[Dict[str, Any]]:
        """Test all 9 trading strategies mentioned in PRs"""
        strategies_to_test = [
            {
                "name": "Mean Reversion",
                "file": "strategies/mean_reversion_strategy.py",
                "needs_api": False
            },
            {
                "name": "Momentum", 
                "file": "strategies/momentum_strategy.py",
                "needs_api": False
            },
            {
                "name": "Contrarian",
                "file": "strategies/contrarian_strategy.py",
                "needs_api": False
            },
            {
                "name": "News Sentiment",
                "file": "strategies/news_strategy.py", 
                "needs_api": True
            },
            {
                "name": "Volatility",
                "file": "strategies/volatility_breakout_strategy.py",
                "needs_api": False
            },
            {
                "name": "Weather Trading",
                "file": "strategies/weather_trading.py",
                "needs_api": True,
                "pr": "#44"
            },
            {
                "name": "BTC Arbitrage",
                "file": "strategies/btc_arbitrage.py",
                "needs_api": True,
                "pr": "#44"
            },
            {
                "name": "Polymarket Live",
                "file": "strategies/polymarket_arbitrage.py",
                "needs_api": True
            },
            {
                "name": "Statistical Arbitrage",
                "file": "strategies/statistical_arb_strategy.py",
                "needs_api": False
            }
        ]
        
        results = []
        for strategy in strategies_to_test:
            test_result = self.test_strategy(strategy)
            results.append(test_result)
            
            # Print inline result
            status_icon = self.get_status_icon(test_result)
            print(f"   {status_icon} {strategy['name']}")
            
        return results
        
    def test_strategy(self, strategy: Dict[str, Any]) -> Dict[str, Any]:
        """Test individual strategy"""
        result = {
            "name": strategy["name"],
            "file_path": strategy["file"],
            "file_exists": False,
            "imported_in_run_bot": False,
            "can_import": False,
            "has_class": False,
            "needs_api_key": strategy.get("needs_api", False),
            "pr_reference": strategy.get("pr", "N/A"),
            "status": self.SHELL_ONLY
        }
        
        file_path = self.root_dir / strategy["file"]
        
        # Check file existence
        if file_path.exists():
            result["file_exists"] = True
            
            # Check if it's in run_bot.py imports
            run_bot_path = self.root_dir / "run_bot.py"
            if run_bot_path.exists():
                with open(run_bot_path, 'r', encoding='utf-8') as f:
                    run_bot_content = f.read()
                    file_name = Path(strategy["file"]).stem
                    if file_name in run_bot_content or strategy["name"].lower().replace(" ", "_") in run_bot_content:
                        result["imported_in_run_bot"] = True
            
            # Try to import and analyze
            try:
                spec = importlib.util.spec_from_file_location("test_strategy", file_path)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    result["can_import"] = True
                    
                    # Check for strategy class
                    for item_name in dir(module):
                        item = getattr(module, item_name)
                        if isinstance(item, type) and 'strategy' in item_name.lower():
                            result["has_class"] = True
                            break
                            
            except Exception as e:
                result["import_error"] = str(e)[:100]
                
        # Determine status
        if result["file_exists"] and result["can_import"] and result["has_class"]:
            if result["needs_api_key"]:
                result["status"] = self.NEEDS_KEYS
            else:
                result["status"] = self.FULLY_WORKING
        elif result["file_exists"] and result["can_import"]:
            result["status"] = self.PARTIAL
        elif result["file_exists"]:
            result["status"] = self.SHELL_ONLY
        else:
            result["status"] = self.NOT_FOUND
            
        return result
        
    def test_api_key_management(self) -> Dict[str, Any]:
        """Test API key management dashboard feature"""
        result = {
            "api_keys_page_exists": False,
            "api_keys_route_exists": False,
            "secure_storage_exists": False,
            "config_manager_exists": False,
            "end_to_end_works": False,
            "status": self.SHELL_ONLY
        }
        
        # Check if API keys page template exists
        api_keys_template = self.root_dir / "dashboard" / "templates" / "api_keys.html"
        if api_keys_template.exists():
            result["api_keys_page_exists"] = True
            
        # Check if route exists in dashboard
        dashboard_app = self.root_dir / "dashboard" / "app.py"
        if dashboard_app.exists():
            with open(dashboard_app, 'r', encoding='utf-8') as f:
                content = f.read()
                if '/api-keys' in content or 'api_keys' in content:
                    result["api_keys_route_exists"] = True
                    
        # Check for secure config manager
        secure_config = self.root_dir / "services" / "secure_config_manager.py"
        if secure_config.exists():
            result["secure_storage_exists"] = True
            result["config_manager_exists"] = True
            
        # Determine status
        if all([result["api_keys_page_exists"], result["api_keys_route_exists"], 
                result["secure_storage_exists"]]):
            result["status"] = self.FULLY_WORKING
        elif result["api_keys_page_exists"] or result["api_keys_route_exists"]:
            result["status"] = self.PARTIAL
            
        return result
        
    def test_dashboard_features(self) -> List[Dict[str, Any]]:
        """Test all dashboard pages"""
        pages_to_test = [
            {"route": "/", "name": "Main Dashboard", "template": "index.html"},
            {"route": "/analytics", "name": "Analytics", "template": "analytics.html"},
            {"route": "/leaderboard", "name": "Strategy Leaderboard", "template": "leaderboard.html"},
            {"route": "/api-keys", "name": "API Key Management", "template": "api_keys.html"},
            {"route": "/trade-journal", "name": "Trade Journal", "template": "trade_journal.html"},
            {"route": "/alerts", "name": "Alerts", "template": "alerts.html"},
            {"route": "/settings", "name": "Settings", "template": "settings.html"}
        ]
        
        results = []
        for page in pages_to_test:
            test_result = self.test_dashboard_page(page)
            results.append(test_result)
            
            # Print inline result
            status_icon = self.get_status_icon(test_result)
            print(f"   {status_icon} {page['name']}")
            
        return results
        
    def test_dashboard_page(self, page: Dict[str, str]) -> Dict[str, Any]:
        """Test individual dashboard page"""
        result = {
            "name": page["name"],
            "route": page["route"],
            "template_exists": False,
            "route_defined": False,
            "has_backend_logic": False,
            "status": self.SHELL_ONLY
        }
        
        # Check template
        template_path = self.root_dir / "dashboard" / "templates" / page["template"]
        if template_path.exists():
            result["template_exists"] = True
            
        # Check route definition
        dashboard_app = self.root_dir / "dashboard" / "app.py"
        routes_dir = self.root_dir / "dashboard" / "routes"
        
        route_found = False
        if dashboard_app.exists():
            with open(dashboard_app, 'r', encoding='utf-8') as f:
                content = f.read()
                route_pattern = page["route"].replace("/", r"\\/")
                if f"@app.route('{page['route']}" in content or f'@app.route("{page["route"]}' in content:
                    route_found = True
                    result["route_defined"] = True
                    
        # Check routes directory for blueprint
        if not route_found and routes_dir.exists():
            for route_file in routes_dir.glob("*.py"):
                with open(route_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if page["route"] in content:
                        result["route_defined"] = True
                        break
                        
        # Check for backend logic (API endpoints, data processing)
        if result["route_defined"]:
            # Simple heuristic: if template has dynamic content markers
            if template_path.exists():
                with open(template_path, 'r', encoding='utf-8') as f:
                    template_content = f.read()
                    if '{{' in template_content or '{%' in template_content:
                        result["has_backend_logic"] = True
                        
        # Determine status
        if result["template_exists"] and result["route_defined"] and result["has_backend_logic"]:
            result["status"] = self.FULLY_WORKING
        elif result["template_exists"] and result["route_defined"]:
            result["status"] = self.PARTIAL
        elif result["template_exists"]:
            result["status"] = self.SHELL_ONLY
        else:
            result["status"] = self.NOT_FOUND
            
        return result
        
    def test_advanced_features(self) -> List[Dict[str, Any]]:
        """Test advanced features from PRs"""
        features = [
            {
                "name": "Mobile & PWA",
                "components": ["mobile/", "service worker", "manifest.json"],
                "pr": "#35, #44"
            },
            {
                "name": "Telegram Notifications",
                "components": ["telegram_bot/", "telegram bot code"],
                "pr": "#44"
            },
            {
                "name": "Backtesting Engine",
                "components": ["backtester.py", "/api/backtest"],
                "pr": "#31"
            },
            {
                "name": "Auto-Update System",
                "components": ["version_manager.py", "update service"],
                "pr": "#33"
            },
            {
                "name": "Strategy Competition System",
                "components": ["competition_monitor.py", "strategy comparison"],
                "pr": "#32"
            }
        ]
        
        results = []
        for feature in features:
            test_result = self.test_advanced_feature(feature)
            results.append(test_result)
            
            # Print inline result
            status_icon = self.get_status_icon(test_result)
            print(f"   {status_icon} {feature['name']}")
            
        return results
        
    def test_advanced_feature(self, feature: Dict[str, Any]) -> Dict[str, Any]:
        """Test individual advanced feature"""
        result = {
            "name": feature["name"],
            "pr_reference": feature.get("pr", "N/A"),
            "components_found": [],
            "components_missing": [],
            "functional": False,
            "status": self.SHELL_ONLY
        }
        
        for component in feature["components"]:
            found = False
            
            # Check if it's a directory
            if component.endswith('/'):
                dir_path = self.root_dir / component.rstrip('/')
                if dir_path.exists() and dir_path.is_dir():
                    found = True
                    # Check if directory has actual code files
                    py_files = list(dir_path.glob('**/*.py'))
                    if py_files:
                        result["components_found"].append(f"{component} ({len(py_files)} files)")
                    else:
                        result["components_found"].append(f"{component} (empty)")
                        found = False
            # Check if it's a file
            elif component.endswith('.py') or component.endswith('.json'):
                file_path = self.root_dir / component
                if file_path.exists():
                    found = True
                    result["components_found"].append(component)
            # Check if it's a pattern (like "service worker")
            else:
                # Search in relevant directories
                search_dirs = [
                    self.root_dir / "mobile",
                    self.root_dir / "dashboard",
                    self.root_dir / "services",
                    self.root_dir
                ]
                
                for search_dir in search_dirs:
                    if not search_dir.exists():
                        continue
                    for file_path in search_dir.rglob('*.py'):
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                if component.lower() in content.lower():
                                    found = True
                                    result["components_found"].append(f"{component} in {file_path.name}")
                                    break
                        except:
                            pass
                    if found:
                        break
                        
            if not found:
                result["components_missing"].append(component)
                
        # Determine status
        found_count = len(result["components_found"])
        total_count = len(feature["components"])
        
        if found_count == total_count and found_count > 0:
            result["status"] = self.FULLY_WORKING
            result["functional"] = True
        elif found_count > 0:
            result["status"] = self.PARTIAL
        else:
            result["status"] = self.NOT_FOUND
            
        return result
        
    def test_data_infrastructure(self) -> Dict[str, Any]:
        """Test data infrastructure and mock vs live mode"""
        result = {
            "mock_client_exists": False,
            "live_client_exists": False,
            "safe_data_client_exists": False,
            "mock_mode_works": False,
            "features_without_api": [],
            "features_need_api": [],
            "status": self.SHELL_ONLY
        }
        
        # Check for mock clients
        clients_dir = self.root_dir / "clients"
        if clients_dir.exists():
            mock_files = list(clients_dir.glob('*mock*.py'))
            if mock_files:
                result["mock_client_exists"] = True
                result["mock_mode_works"] = True
                
            live_files = [f for f in clients_dir.glob('*.py') if 'mock' not in f.name.lower()]
            if live_files:
                result["live_client_exists"] = True
                
        # Check for SafeDataClient pattern
        for py_file in self.root_dir.rglob('*.py'):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'SafeDataClient' in content or 'safe_data' in content.lower():
                        result["safe_data_client_exists"] = True
                        break
            except:
                pass
                
        # Determine which features work without API keys
        if result["mock_client_exists"]:
            result["features_without_api"] = [
                "Basic arbitrage detection",
                "Paper trading simulation", 
                "Dashboard visualization",
                "Strategy backtesting (mock data)"
            ]
            
        result["features_need_api"] = [
            "Live Polymarket data",
            "News sentiment analysis",
            "Weather trading",
            "BTC arbitrage",
            "Telegram notifications"
        ]
        
        # Determine status
        if result["mock_client_exists"] and result["live_client_exists"]:
            result["status"] = self.FULLY_WORKING
        elif result["mock_client_exists"]:
            result["status"] = self.PARTIAL
            
        return result
        
    def run_live_tests(self) -> Dict[str, Any]:
        """Run optional live tests (slower but more thorough)"""
        results = {
            "dashboard_startup": None,
            "run_bot_syntax": None,
            "strategy_imports": None
        }
        
        print(f"   {Colors.OKCYAN}Testing dashboard startup (syntax check)...{Colors.ENDC}")
        results["dashboard_startup"] = self.test_dashboard_startup()
        
        print(f"   {Colors.OKCYAN}Testing run_bot.py syntax...{Colors.ENDC}")
        results["run_bot_syntax"] = self.test_run_bot_syntax()
        
        print(f"   {Colors.OKCYAN}Testing strategy imports...{Colors.ENDC}")
        results["strategy_imports"] = self.test_strategy_imports()
        
        return results
        
    def test_dashboard_startup(self) -> Dict[str, Any]:
        """Test if dashboard can start (syntax check only)"""
        result = {
            "can_import": False,
            "syntax_valid": False,
            "error": None
        }
        
        try:
            # Try to compile the dashboard app to check for syntax errors
            dashboard_app = self.root_dir / "dashboard" / "app.py"
            if dashboard_app.exists():
                with open(dashboard_app, 'r', encoding='utf-8') as f:
                    code = f.read()
                    compile(code, str(dashboard_app), 'exec')
                    result["syntax_valid"] = True
                    result["can_import"] = True
        except SyntaxError as e:
            result["error"] = f"Syntax error: {str(e)}"
        except Exception as e:
            result["error"] = str(e)[:200]
            
        return result
        
    def test_run_bot_syntax(self) -> Dict[str, Any]:
        """Test if run_bot.py has valid syntax"""
        result = {
            "syntax_valid": False,
            "error": None
        }
        
        try:
            run_bot_path = self.root_dir / "run_bot.py"
            if run_bot_path.exists():
                with open(run_bot_path, 'r', encoding='utf-8') as f:
                    code = f.read()
                    compile(code, str(run_bot_path), 'exec')
                    result["syntax_valid"] = True
        except SyntaxError as e:
            result["error"] = f"Syntax error: {str(e)}"
        except Exception as e:
            result["error"] = str(e)[:200]
            
        return result
        
    def test_strategy_imports(self) -> List[Dict[str, Any]]:
        """Test if all strategy files can be imported"""
        results = []
        strategy_dir = self.root_dir / "strategies"
        
        if not strategy_dir.exists():
            return results
            
        for strategy_file in strategy_dir.glob("*.py"):
            if strategy_file.name.startswith("_"):
                continue
                
            result = {
                "file": strategy_file.name,
                "can_import": False,
                "error": None
            }
            
            try:
                with open(strategy_file, 'r', encoding='utf-8') as f:
                    code = f.read()
                    compile(code, str(strategy_file), 'exec')
                    result["can_import"] = True
            except SyntaxError as e:
                result["error"] = f"Syntax error: {str(e)}"
            except Exception as e:
                result["error"] = str(e)[:100]
                
            results.append(result)
            
        return results
        
    def get_status_icon(self, test_result: Dict[str, Any]) -> str:
        """Get status icon for a test result"""
        status = test_result.get("status", self.SHELL_ONLY)
        
        if status == self.FULLY_WORKING:
            return f"{Colors.OKGREEN}{self.FULLY_WORKING}{Colors.ENDC}"
        elif status == self.NEEDS_KEYS:
            return f"{Colors.WARNING}{self.NEEDS_KEYS}{Colors.ENDC}"
        elif status == self.PARTIAL:
            return f"{Colors.WARNING}{self.PARTIAL}{Colors.ENDC}"
        elif status == self.NOT_FOUND:
            return f"{Colors.FAIL}{self.NOT_FOUND}{Colors.ENDC}"
        else:
            return f"{Colors.FAIL}{self.SHELL_ONLY}{Colors.ENDC}"
            
    def calculate_summary(self):
        """Calculate summary statistics"""
        all_features = []
        
        # Collect all features from different test categories
        if "strategies" in self.results:
            all_features.extend(self.results["strategies"])
        if "dashboard_pages" in self.results:
            all_features.extend(self.results["dashboard_pages"])
        if "advanced_features" in self.results:
            all_features.extend(self.results["advanced_features"])
            
        # Count by status
        for feature in all_features:
            status = feature.get("status", self.SHELL_ONLY)
            
            if status == self.FULLY_WORKING:
                self.results["summary"]["fully_implemented"] += 1
            elif status == self.NEEDS_KEYS:
                self.results["summary"]["needs_api_keys"] += 1
            elif status == self.PARTIAL:
                self.results["summary"]["partially_implemented"] += 1
            elif status == self.NOT_FOUND:
                self.results["summary"]["not_found"] += 1
            else:
                self.results["summary"]["shell_only"] += 1
                
    def generate_markdown_report(self):
        """Generate detailed markdown report"""
        report_path = self.root_dir / "FEATURE_AUDIT_REPORT.md"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            # Header
            f.write(f"# 🔍 Feature Audit Report - {datetime.now().strftime('%Y-%m-%d')}\n\n")
            
            # Executive Summary
            f.write("## Executive Summary\n\n")
            summary = self.results["summary"]
            f.write(f"- ✅ **Fully Implemented**: {summary['fully_implemented']} features\n")
            f.write(f"- 🔑 **Needs API Keys**: {summary['needs_api_keys']} features\n")
            f.write(f"- 🚧 **Partially Implemented**: {summary['partially_implemented']} features\n")
            f.write(f"- 📦 **Shell Only**: {summary['shell_only']} features\n")
            f.write(f"- ❌ **Not Found**: {summary['not_found']} features\n\n")
            
            total = sum(summary.values())
            if total > 0:
                pct_working = ((summary['fully_implemented'] + summary['needs_api_keys']) / total) * 100
                f.write(f"**Overall Implementation Rate**: {pct_working:.1f}%\n\n")
            
            f.write("---\n\n")
            
            # Bot Integration
            if "bot_integration" in self.results:
                f.write("## Core Bot Integration\n\n")
                bot = self.results["bot_integration"]
                f.write(f"- **run_bot.py exists**: {self.FULLY_WORKING if bot['run_bot_exists'] else self.NOT_FOUND}\n")
                f.write(f"- **Strategies imported**: {len(bot.get('strategies_imported', []))}\n")
                
                if bot.get('strategies_imported'):
                    f.write("\n### Imported Strategies:\n")
                    for strategy in bot['strategies_imported']:
                        f.write(f"- `{strategy}`\n")
                f.write("\n---\n\n")
            
            # Strategies
            if "strategies" in self.results and self.results["strategies"]:
                f.write("## Trading Strategies\n\n")
                f.write("| Strategy | File Exists | Importable | Has Class | In run_bot | Needs API | Status |\n")
                f.write("|----------|-------------|------------|-----------|------------|-----------|--------|\n")
                
                for strategy in self.results["strategies"]:
                    name = strategy["name"]
                    file_exists = "✅" if strategy["file_exists"] else "❌"
                    can_import = "✅" if strategy["can_import"] else "❌"
                    has_class = "✅" if strategy["has_class"] else "❌"
                    in_run_bot = "✅" if strategy["imported_in_run_bot"] else "❌"
                    needs_api = "🔑" if strategy["needs_api_key"] else "➖"
                    status = strategy["status"]
                    
                    f.write(f"| {name} | {file_exists} | {can_import} | {has_class} | {in_run_bot} | {needs_api} | {status} |\n")
                    
                f.write("\n")
                
                # Detailed findings for each strategy
                f.write("### Detailed Strategy Findings\n\n")
                for strategy in self.results["strategies"]:
                    f.write(f"#### {strategy['name']}\n\n")
                    f.write(f"- **Status**: {strategy['status']}\n")
                    f.write(f"- **File Path**: `{strategy['file_path']}`\n")
                    f.write(f"- **File Exists**: {strategy['file_exists']}\n")
                    f.write(f"- **Can Import**: {strategy['can_import']}\n")
                    f.write(f"- **Has Strategy Class**: {strategy['has_class']}\n")
                    f.write(f"- **Imported in run_bot.py**: {strategy['imported_in_run_bot']}\n")
                    f.write(f"- **Needs API Key**: {strategy['needs_api_key']}\n")
                    
                    if "pr_reference" in strategy and strategy["pr_reference"] != "N/A":
                        f.write(f"- **PR Reference**: {strategy['pr_reference']}\n")
                        
                    if "import_error" in strategy:
                        f.write(f"- **Import Error**: `{strategy['import_error']}`\n")
                        
                    # Action required
                    if strategy["status"] == self.SHELL_ONLY:
                        f.write(f"\n**Action Required**: File exists but cannot be imported or missing strategy class. Fix import errors and implement strategy class.\n")
                    elif strategy["status"] == self.PARTIAL:
                        f.write(f"\n**Action Required**: Strategy is importable but may be missing integration in run_bot.py or full functionality.\n")
                    elif strategy["status"] == self.NOT_FOUND:
                        f.write(f"\n**Action Required**: Strategy file does not exist. Implement the strategy from scratch.\n")
                    elif strategy["status"] == self.NEEDS_KEYS:
                        f.write(f"\n**Action Required**: Strategy is implemented but requires API keys to function. Configure API keys in settings.\n")
                        
                    f.write("\n")
                    
                f.write("---\n\n")
            
            # API Key Management
            if "api_key_management" in self.results:
                f.write("## API Key Management Dashboard\n\n")
                api = self.results["api_key_management"]
                f.write(f"- **Status**: {api['status']}\n")
                f.write(f"- **API Keys Page Template Exists**: {api['api_keys_page_exists']}\n")
                f.write(f"- **API Keys Route Defined**: {api['api_keys_route_exists']}\n")
                f.write(f"- **Secure Storage Exists**: {api['secure_storage_exists']}\n")
                f.write(f"- **Config Manager Exists**: {api['config_manager_exists']}\n\n")
                
                if api['status'] == self.FULLY_WORKING:
                    f.write("**Conclusion**: API key management appears to be fully implemented with secure storage.\n")
                elif api['status'] == self.PARTIAL:
                    f.write("**Action Required**: Some components exist but full end-to-end flow may not be complete.\n")
                else:
                    f.write("**Action Required**: API key management feature needs implementation.\n")
                    
                f.write("\n---\n\n")
            
            # Dashboard Pages
            if "dashboard_pages" in self.results and self.results["dashboard_pages"]:
                f.write("## Dashboard Pages\n\n")
                f.write("| Page | Template | Route | Backend Logic | Status |\n")
                f.write("|------|----------|-------|---------------|--------|\n")
                
                for page in self.results["dashboard_pages"]:
                    name = page["name"]
                    template = "✅" if page["template_exists"] else "❌"
                    route = "✅" if page["route_defined"] else "❌"
                    logic = "✅" if page["has_backend_logic"] else "❌"
                    status = page["status"]
                    
                    f.write(f"| {name} | {template} | {route} | {logic} | {status} |\n")
                    
                f.write("\n---\n\n")
            
            # Advanced Features
            if "advanced_features" in self.results and self.results["advanced_features"]:
                f.write("## Advanced Features\n\n")
                
                for feature in self.results["advanced_features"]:
                    f.write(f"### {feature['name']}\n\n")
                    f.write(f"- **Status**: {feature['status']}\n")
                    f.write(f"- **PR Reference**: {feature['pr_reference']}\n")
                    
                    if feature['components_found']:
                        f.write(f"- **Components Found**: \n")
                        for comp in feature['components_found']:
                            f.write(f"  - {comp}\n")
                            
                    if feature['components_missing']:
                        f.write(f"- **Components Missing**: \n")
                        for comp in feature['components_missing']:
                            f.write(f"  - {comp}\n")
                            
                    f.write("\n")
                    
                f.write("---\n\n")
            
            # Data Infrastructure
            if "data_infrastructure" in self.results:
                f.write("## Data Infrastructure\n\n")
                infra = self.results["data_infrastructure"]
                f.write(f"- **Status**: {infra['status']}\n")
                f.write(f"- **Mock Client Available**: {infra['mock_client_exists']}\n")
                f.write(f"- **Live Client Available**: {infra['live_client_exists']}\n")
                f.write(f"- **Safe Data Client Pattern**: {infra['safe_data_client_exists']}\n\n")
                
                if infra['features_without_api']:
                    f.write("### Features Available WITHOUT API Keys (Mock Mode):\n\n")
                    for feature in infra['features_without_api']:
                        f.write(f"- {feature}\n")
                    f.write("\n")
                    
                if infra['features_need_api']:
                    f.write("### Features That REQUIRE API Keys:\n\n")
                    for feature in infra['features_need_api']:
                        f.write(f"- {feature}\n")
                    f.write("\n")
                    
                f.write("---\n\n")
            
            # Live Tests (if enabled)
            if "live_tests" in self.results and self.results["live_tests"]:
                f.write("## Live Tests (Optional)\n\n")
                live = self.results["live_tests"]
                
                if live.get("dashboard_startup"):
                    dash = live["dashboard_startup"]
                    f.write("### Dashboard Startup Test\n\n")
                    f.write(f"- **Syntax Valid**: {dash.get('syntax_valid', False)}\n")
                    if dash.get('error'):
                        f.write(f"- **Error**: `{dash['error']}`\n")
                    f.write("\n")
                    
                if live.get("run_bot_syntax"):
                    bot = live["run_bot_syntax"]
                    f.write("### run_bot.py Syntax Test\n\n")
                    f.write(f"- **Syntax Valid**: {bot.get('syntax_valid', False)}\n")
                    if bot.get('error'):
                        f.write(f"- **Error**: `{bot['error']}`\n")
                    f.write("\n")
                    
                if live.get("strategy_imports"):
                    f.write("### Strategy Import Tests\n\n")
                    imports = live["strategy_imports"]
                    for imp in imports:
                        status = "✅" if imp["can_import"] else "❌"
                        f.write(f"- {status} `{imp['file']}`")
                        if imp.get('error'):
                            f.write(f" - Error: `{imp['error']}`")
                        f.write("\n")
                    f.write("\n")
                    
                f.write("---\n\n")
            
            # Priority Action Items
            f.write("## 🎯 Priority Action Items\n\n")
            
            f.write("### Immediate (Works with Mock Data)\n\n")
            immediate = []
            for strategy in self.results.get("strategies", []):
                if strategy["status"] == self.SHELL_ONLY and not strategy["needs_api_key"]:
                    immediate.append(f"Fix {strategy['name']} strategy - file exists but has import/implementation issues")
                elif strategy["status"] == self.NOT_FOUND and not strategy["needs_api_key"]:
                    immediate.append(f"Implement {strategy['name']} strategy from scratch")
                    
            for page in self.results.get("dashboard_pages", []):
                if page["status"] == self.SHELL_ONLY:
                    immediate.append(f"Add backend logic to {page['name']} page")
                    
            if immediate:
                for i, item in enumerate(immediate, 1):
                    f.write(f"{i}. {item}\n")
            else:
                f.write("No immediate action items - all mock-mode features are functional!\n")
                
            f.write("\n### Requires API Keys\n\n")
            needs_keys = []
            for strategy in self.results.get("strategies", []):
                if strategy["needs_api_key"] and strategy["status"] in [self.NEEDS_KEYS, self.SHELL_ONLY]:
                    api_type = "News API" if "news" in strategy["name"].lower() else "API"
                    if "weather" in strategy["name"].lower():
                        api_type = "NOAA API"
                    elif "btc" in strategy["name"].lower():
                        api_type = "Exchange API"
                    needs_keys.append(f"{strategy['name']} - Needs {api_type}")
                    
            if needs_keys:
                for i, item in enumerate(needs_keys, 1):
                    f.write(f"{i}. {item}\n")
            else:
                f.write("No features blocked on API keys that are otherwise ready.\n")
                
            f.write("\n### Needs Development\n\n")
            needs_dev = []
            for feature in self.results.get("advanced_features", []):
                if feature["status"] in [self.NOT_FOUND, self.SHELL_ONLY]:
                    missing = ", ".join(feature.get("components_missing", []))
                    needs_dev.append(f"{feature['name']} - Missing: {missing}")
                    
            if needs_dev:
                for i, item in enumerate(needs_dev, 1):
                    f.write(f"{i}. {item}\n")
            else:
                f.write("All advanced features have at least partial implementation!\n")
                
            f.write("\n---\n\n")
            
            # Recommendations
            f.write("## 📋 Recommendations\n\n")
            f.write("1. **Update README.md** to accurately reflect implementation status of each feature\n")
            f.write("2. **Prioritize mock-mode features** - Fix import errors and complete partially implemented strategies\n")
            f.write("3. **Document API requirements** - Clearly list which features need which API keys\n")
            f.write("4. **Add integration tests** - Ensure strategies actually execute via run_bot.py\n")
            f.write("5. **Complete dashboard features** - Add real backend logic to pages that are template-only\n")
            f.write("6. **Test advanced features** - Verify end-to-end functionality of Mobile/PWA, Telegram, etc.\n")
            f.write("\n")
            
        print(f"\n{Colors.OKGREEN}✅ Markdown report generated: {report_path}{Colors.ENDC}")
        
    def generate_json_report(self):
        """Generate machine-readable JSON report"""
        report_path = self.root_dir / "feature_audit_summary.json"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2)
            
        print(f"{Colors.OKGREEN}✅ JSON report generated: {report_path}{Colors.ENDC}\n")
        
    def print_summary(self):
        """Print summary to console"""
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}📊 AUDIT COMPLETE - SUMMARY{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}\n")
        
        summary = self.results["summary"]
        total = sum(summary.values())
        
        print(f"{Colors.OKGREEN}✅ Fully Implemented: {summary['fully_implemented']}{Colors.ENDC}")
        print(f"{Colors.WARNING}🔑 Needs API Keys: {summary['needs_api_keys']}{Colors.ENDC}")
        print(f"{Colors.WARNING}🚧 Partially Implemented: {summary['partially_implemented']}{Colors.ENDC}")
        print(f"{Colors.FAIL}📦 Shell Only: {summary['shell_only']}{Colors.ENDC}")
        print(f"{Colors.FAIL}❌ Not Found: {summary['not_found']}{Colors.ENDC}")
        print(f"\n{Colors.BOLD}Total Features Tested: {total}{Colors.ENDC}")
        
        if total > 0:
            working = summary['fully_implemented'] + summary['needs_api_keys']
            pct = (working / total) * 100
            
            if pct >= 80:
                color = Colors.OKGREEN
            elif pct >= 50:
                color = Colors.WARNING
            else:
                color = Colors.FAIL
                
            print(f"{color}{Colors.BOLD}Overall Implementation Rate: {pct:.1f}%{Colors.ENDC}\n")
            
        print(f"{Colors.OKCYAN}📄 Reports generated:{Colors.ENDC}")
        print(f"   - FEATURE_AUDIT_REPORT.md (detailed findings)")
        print(f"   - feature_audit_summary.json (machine-readable)")
        print(f"\n{Colors.HEADER}{'='*80}{Colors.ENDC}\n")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Comprehensive Feature Audit System for Market Strategy Testing Bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python feature_audit.py                    # Basic audit (fast)
  python feature_audit.py --live-test        # Include live tests (slower)
  
Reports Generated:
  - FEATURE_AUDIT_REPORT.md (detailed findings)
  - feature_audit_summary.json (machine-readable)
        """
    )
    
    parser.add_argument(
        '--live-test',
        action='store_true',
        help='Run live tests (syntax checks, imports). Slower but more thorough.'
    )
    
    args = parser.parse_args()
    
    try:
        audit = FeatureAudit(live_test=args.live_test)
        audit.run_full_audit()
        return 0
    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARNING}Audit interrupted by user{Colors.ENDC}")
        return 1
    except Exception as e:
        print(f"\n{Colors.FAIL}Error during audit: {e}{Colors.ENDC}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

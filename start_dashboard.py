#!/usr/bin/env python3
"""
Quick Start Script for Market Strategy Testing Bot Dashboard

This script helps users quickly set up and run the web dashboard.
"""

import sys
import os
from pathlib import Path
import subprocess

# Add project root to Python path FIRST
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))


def print_banner():
    """Print welcome banner"""
    print("\n" + "=" * 70)
    print("🚀 Market Strategy Testing Bot - Dashboard Quick Start")
    print("=" * 70 + "\n")


def check_python_version():
    """Check if Python version is adequate"""
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8 or higher is required")
        print(f"   Current version: {sys.version}")
        print("\n   Please upgrade Python: https://www.python.org/downloads/")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True


def check_dependencies():
    """Check if required dependencies are installed"""
    print("\n📦 Checking dependencies...")

    required = ["flask", "flask_cors", "yaml"]
    missing = []

    for package in required:
        try:
            __import__(package)
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} - NOT INSTALLED")
            missing.append(package)

    if missing:
        print(f"\n❌ Missing dependencies: {', '.join(missing)}")
        print("\n   Install with: pip install -r requirements.txt")
        return False

    return True


def check_config():
    """Check if config file exists"""
    print("\n📝 Checking configuration...")

    config_path = Path("config.yaml")
    example_path = Path("config.example.yaml")

    if not config_path.exists():
        print("   ❌ config.yaml not found")

        if example_path.exists():
            print(
                "\n   Would you like to create config.yaml from the example? (y/n): ",
                end="",
            )
            response = input().lower().strip()

            if response == "y":
                try:
                    import shutil

                    shutil.copy(example_path, config_path)
                    print("   ✅ Created config.yaml from example")
                    print("\n   ⚠️  Please edit config.yaml to add your settings")
                    return True
                except Exception as e:
                    print(f"   ❌ Error creating config: {e}")
                    return False
            else:
                print("\n   Please create config.yaml manually")
                return False
        else:
            print("   ❌ config.example.yaml not found")
            return False
    else:
        print("   ✅ config.yaml exists")
        return True


def create_logs_directory():
    """Create logs directory if it doesn't exist"""
    logs_dir = Path("logs")
    if not logs_dir.exists():
        logs_dir.mkdir()
        print("   ✅ Created logs directory")
    return True


def start_dashboard():
    """Start the Flask dashboard"""
    print("\n🎯 Starting dashboard server...")
    print("\n" + "-" * 70)

    try:
        # Import and run dashboard
        from dashboard.app import app

        app.run(host="0.0.0.0", port=5000, debug=False)
    except KeyboardInterrupt:
        print("\n\n👋 Dashboard stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting dashboard: {e}")
        import traceback

        traceback.print_exc()
        return False

    return True


def main():
    """Main function"""
    print_banner()

    # Check Python version
    if not check_python_version():
        sys.exit(1)

    # Check dependencies
    if not check_dependencies():
        print("\n💡 Tip: Install dependencies with:")
        print("   pip install -r requirements.txt")
        sys.exit(1)

    # Check config
    if not check_config():
        sys.exit(1)

    # Create logs directory
    create_logs_directory()

    print("\n" + "=" * 70)
    print("✅ All checks passed!")
    print("=" * 70)

    # Start dashboard
    if not start_dashboard():
        sys.exit(1)


if __name__ == "__main__":
    main()

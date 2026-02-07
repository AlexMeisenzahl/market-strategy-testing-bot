#!/usr/bin/env python3
"""
Quick Start Script - Launch the bot with web dashboard

This is a convenience script that ensures all dependencies are installed
and starts the bot with the web dashboard enabled.
"""

import sys
import os
import subprocess

def check_dependencies():
    """Check if required dependencies are installed"""
    print("🔍 Checking dependencies...")
    
    required_packages = [
        'flask', 'flask_cors', 'yaml', 'rich', 'requests'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"❌ Missing dependencies: {', '.join(missing)}")
        print("\n📦 Installing missing dependencies...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("✅ Dependencies installed!")
    else:
        print("✅ All dependencies installed!")

def check_config():
    """Check if config.yaml exists"""
    if not os.path.exists('config.yaml'):
        print("❌ config.yaml not found!")
        print("Please make sure you're running this from the project directory.")
        sys.exit(1)
    
    print("✅ Configuration file found!")

def main():
    """Main entry point"""
    print("=" * 60)
    print("🚀 Market Strategy Testing Bot - Quick Start")
    print("=" * 60)
    print()
    
    # Check dependencies
    check_dependencies()
    print()
    
    # Check config
    check_config()
    print()
    
    # Import and run bot
    print("🎯 Starting bot with web dashboard...")
    print("📊 Dashboard will be available at: http://localhost:5000")
    print()
    print("Press Ctrl+C to stop the bot")
    print("-" * 60)
    print()
    
    try:
        from bot import main as bot_main
        bot_main()
    except KeyboardInterrupt:
        print("\n\n👋 Bot stopped by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()

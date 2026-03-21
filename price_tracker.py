"""
E-commerce Price Tracker - Main Entry Point

Real-world application for tracking e-commerce product prices.
Demonstrates practical business value and freelance potential.
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path
project_root = Path(__file__).parent
src_path = project_root / 'src'
sys.path.insert(0, str(src_path))

from src.cli.price_tracker_cli import main

if __name__ == "__main__":
    main()

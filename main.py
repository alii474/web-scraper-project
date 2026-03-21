"""
Main entry point for the Advanced Web Scraper

This module provides the main CLI interface and serves as the entry point
for the entire application.
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path
project_root = Path(__file__).parent
src_path = project_root / 'src'
sys.path.insert(0, str(src_path))

from src.cli.advanced_cli import main

if __name__ == "__main__":
    main()

"""
Multi-Site Web Scraper - Main Entry Point

Entry point for the multi-site web scraper with automatic website detection
and data normalization capabilities.
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path
project_root = Path(__file__).parent
src_path = project_root / 'src'
sys.path.insert(0, str(src_path))

from src.cli.multi_site_cli import main

if __name__ == "__main__":
    main()

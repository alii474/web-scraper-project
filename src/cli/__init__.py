# src/cli/__init__.py
"""
CLI components.

This module contains command-line interface functionality including:
- Advanced CLI with argparse
- Comprehensive argument handling
- Progress reporting
- Error handling
"""

from .advanced_cli import ScraperCLI, main

__all__ = [
    'ScraperCLI',
    'main'
]

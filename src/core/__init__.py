# src/core/__init__.py
"""
Core scraping engine components.

This module contains the main scraping functionality including:
- Smart scraping engine with intelligent features
- Advanced web scraper with Selenium support
- User-agent rotation and proxy management
- Exponential backoff retry mechanisms
"""

from .engine import SmartScrapingEngine, ConcurrentScrapingEngine
from .scraper import AdvancedWebScraper, SeleniumDriver

__all__ = [
    'SmartScrapingEngine',
    'ConcurrentScrapingEngine',
    'AdvancedWebScraper',
    'SeleniumDriver'
]

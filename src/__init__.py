# Advanced Web Scraper - __init__.py files

# src/__init__.py
"""
Advanced Web Scraper Package

A production-level web scraping framework with intelligent features:
- Smart scraping engine with user-agent rotation
- Exponential backoff retry mechanism
- Proxy support and robots.txt compliance
- Advanced pagination and automation
- Multiple storage formats (CSV, Excel, JSON, SQLite)
- Professional logging and monitoring
- CLI interface with comprehensive options
- Selenium support for dynamic websites
- Data visualization with matplotlib
- Scheduling functionality
- Flask web application
"""

__version__ = "2.0.0"
__author__ = "Advanced Web Scraper Team"
__email__ = "contact@advancedscraper.com"

from .core.engine import SmartScrapingEngine, ConcurrentScrapingEngine
from .core.scraper import AdvancedWebScraper
from .parsers.data_parser import AdvancedDataParser
from .storage.advanced_storage import AdvancedStorageManager
from .utils.config import CONFIG, ScraperConfig
from .utils.logger import get_logger, ScraperLogger
from .utils.visualization import DataVisualizer
from .utils.scheduler import scheduler, schedule_scraping
from .cli.advanced_cli import ScraperCLI

__all__ = [
    'SmartScrapingEngine',
    'ConcurrentScrapingEngine', 
    'AdvancedWebScraper',
    'AdvancedDataParser',
    'AdvancedStorageManager',
    'CONFIG',
    'ScraperConfig',
    'get_logger',
    'ScraperLogger',
    'DataVisualizer',
    'scheduler',
    'schedule_scraping',
    'ScraperCLI'
]

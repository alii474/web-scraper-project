"""
Advanced Web Scraper Configuration

This module contains all configuration settings for the web scraper.
Follows clean architecture principles with environment-based configuration.
"""

import os
from pathlib import Path
from typing import Dict, List, Any
import json

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"
LOGS_DIR = PROJECT_ROOT / "logs"
CONFIG_DIR = PROJECT_ROOT / "config"

# Create directories if they don't exist
for directory in [DATA_DIR, OUTPUT_DIR, LOGS_DIR, CONFIG_DIR]:
    directory.mkdir(exist_ok=True)

class ScraperConfig:
    """
    Configuration class for the web scraper.
    Centralizes all settings and provides easy access to configuration values.
    """
    
    # HTTP Configuration
    DEFAULT_HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'DNT': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
    }
    
    # User-Agent rotation for avoiding detection
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0',
    ]
    
    # Request Configuration
    DEFAULT_TIMEOUT = 30  # seconds
    MAX_RETRIES = 3
    INITIAL_RETRY_DELAY = 1  # seconds
    MAX_RETRY_DELAY = 16  # seconds (exponential backoff)
    
    # Pagination Configuration
    DEFAULT_MAX_PAGES = 5
    PAGE_DELAY_MIN = 1.0  # seconds
    PAGE_DELAY_MAX = 3.0  # seconds
    
    # Data Processing Configuration
    BATCH_SIZE = 100  # Process data in batches for large datasets
    REMOVE_DUPLICATES = True
    VALIDATE_DATA = True
    
    # Storage Configuration
    SUPPORTED_FORMATS = ['csv', 'excel', 'json', 'sqlite']
    DEFAULT_FORMATS = ['csv', 'excel']
    TIMESTAMP_FILES = True
    
    # Logging Configuration
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
    LOG_FILE = LOGS_DIR / 'scraper.log'
    LOG_MAX_SIZE = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5
    
    # Selenium Configuration (for dynamic websites)
    SELENIUM_ENABLED = True
    SELENIUM_HEADLESS = True
    SELENIUM_TIMEOUT = 30
    SELENIUM_IMPLICIT_WAIT = 10
    
    # Proxy Configuration
    PROXY_ENABLED = False
    PROXY_LIST = []  # Add proxies in format: ['http://proxy1:port', 'http://proxy2:port']
    PROXY_ROTATION = True
    
    # Scheduling Configuration
    SCHEDULING_ENABLED = True
    DEFAULT_SCHEDULE_INTERVAL = 60  # minutes
    
    # Visualization Configuration
    VISUALIZATION_ENABLED = True
    CHART_STYLE = 'seaborn-v0_8'
    CHART_DPI = 300
    CHART_FIGSIZE = (12, 8)
    
    # Site-specific configurations
    SITE_PRESETS = {
        'books.toscrape.com': {
            'base_url': 'http://books.toscrape.com/',
            'pagination_pattern': 'catalogue/page-{page}.html',
            'item_selector': 'article.product_pod',
            'fields': {
                'title': 'h3 a::attr(title)',
                'price': 'p.price_color::text',
                'rating': 'p.star-rating::attr(class)',
                'availability': 'p.instock.availability::text',
                'url': 'h3 a::attr(href)'
            },
            'delay_range': (1.0, 2.0),
            'max_pages': 50
        },
        'quotes.toscrape.com': {
            'base_url': 'http://quotes.toscrape.com/',
            'pagination_pattern': 'page/{page}/',
            'item_selector': 'div.quote',
            'fields': {
                'quote': 'span.text::text',
                'author': 'small.author::text',
                'tags': 'div.tags a.tag::text'
            },
            'delay_range': (0.5, 1.5),
            'max_pages': 10
        }
    }
    
    @classmethod
    def get_user_agent(cls) -> str:
        """Get a random user agent from the list."""
        import random
        return random.choice(cls.USER_AGENTS)
    
    @classmethod
    def get_site_config(cls, url: str) -> Dict[str, Any]:
        """Get site-specific configuration based on URL."""
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
        
        # Remove www. prefix for matching
        if domain.startswith('www.'):
            domain = domain[4:]
        
        return cls.SITE_PRESETS.get(domain, {})
    
    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """Convert configuration to dictionary for JSON serialization."""
        config_dict = {}
        for attr_name in dir(cls):
            if not attr_name.startswith('_') and not callable(getattr(cls, attr_name)):
                value = getattr(cls, attr_name)
                if not isinstance(value, (type, Path)):
                    config_dict[attr_name] = value
        return config_dict
    
    @classmethod
    def save_to_file(cls, filename: str = 'scraper_config.json'):
        """Save configuration to JSON file."""
        config_path = CONFIG_DIR / filename
        with open(config_path, 'w') as f:
            json.dump(cls.to_dict(), f, indent=2, default=str)
        return config_path
    
    @classmethod
    def load_from_file(cls, filename: str = 'scraper_config.json'):
        """Load configuration from JSON file."""
        config_path = CONFIG_DIR / filename
        if config_path.exists():
            with open(config_path, 'r') as f:
                config_data = json.load(f)
                # Update class attributes with loaded data
                for key, value in config_data.items():
                    if hasattr(cls, key):
                        setattr(cls, key, value)
        return config_path

# Environment-based configuration overrides
def load_env_config():
    """Load configuration from environment variables."""
    config = ScraperConfig()
    
    # Override with environment variables if present
    config.LOG_LEVEL = os.getenv('SCRAPER_LOG_LEVEL', config.LOG_LEVEL)
    config.DEFAULT_TIMEOUT = int(os.getenv('SCRAPER_TIMEOUT', str(config.DEFAULT_TIMEOUT)))
    config.MAX_RETRIES = int(os.getenv('SCRAPER_MAX_RETRIES', str(config.MAX_RETRIES)))
    config.PROXY_ENABLED = os.getenv('SCRAPER_PROXY_ENABLED', 'false').lower() == 'true'
    config.SELENIUM_ENABLED = os.getenv('SCRAPER_SELENIUM_ENABLED', 'true').lower() == 'true'
    
    return config

# Initialize configuration
CONFIG = load_env_config()

"""
E-commerce Price Tracker Configuration

Configuration for tracking product prices across multiple e-commerce sites.
Includes site-specific configurations, price alerts, and monitoring settings.
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

class PriceTrackerConfig:
    """
    Configuration for E-commerce Price Tracker.
    
    Features:
    - Multi-site price tracking
    - Price drop alerts
    - Historical price data
    - Product availability monitoring
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
    DEFAULT_TIMEOUT = 30
    MAX_RETRIES = 3
    INITIAL_RETRY_DELAY = 1
    MAX_RETRY_DELAY = 16
    
    # Price Tracking Configuration
    DEFAULT_CHECK_INTERVAL = 3600  # 1 hour in seconds
    PRICE_CHANGE_THRESHOLD = 5.0  # 5% price change threshold for alerts
    MAX_PRICE_HISTORY_DAYS = 90
    
    # Pagination Configuration
    DEFAULT_MAX_PAGES = 5
    PAGE_DELAY_MIN = 2.0
    PAGE_DELAY_MAX = 5.0
    
    # Data Processing Configuration
    BATCH_SIZE = 100
    REMOVE_DUPLICATES = True
    VALIDATE_DATA = True
    
    # Storage Configuration
    SUPPORTED_FORMATS = ['csv', 'excel', 'json', 'sqlite']
    DEFAULT_FORMATS = ['csv', 'excel', 'sqlite']
    TIMESTAMP_FILES = True
    
    # Logging Configuration
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
    LOG_MAX_SIZE = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5
    
    # Selenium Configuration
    SELENIUM_ENABLED = True
    SELENIUM_HEADLESS = True
    SELENIUM_TIMEOUT = 30
    SELENIUM_IMPLICIT_WAIT = 10
    
    # Price Alert Configuration
    ALERT_ENABLED = True
    ALERT_EMAIL_ENABLED = False
    ALERT_WEBHOOK_ENABLED = False
    PRICE_DROP_ALERTS = True
    PRICE_INCREASE_ALERTS = False
    AVAILABILITY_ALERTS = True
    
    # E-commerce Site Configurations
    ECOMMERCE_SITES = {
        'amazon': {
            'base_url': 'https://www.amazon.com',
            'search_url_pattern': 'https://www.amazon.com/s?k={query}&page={page}',
            'product_url_pattern': 'https://www.amazon.com/dp/{asin}',
            'item_selector': 'div[data-component-type="s-search-result"]',
            'fields': {
                'title': 'h2 a span::text',
                'price': 'span.a-price-whole::text, span.a-price-fraction::text',
                'original_price': 'span.a-price.a-text-price span.a-offscreen::text',
                'rating': 'span.a-icon-alt::attr(aria-label)',
                'reviews_count': 'span.a-size-base::text',
                'availability': 'span.a-color-price::text',
                'url': 'h2 a::attr(href)',
                'image': 'img.s-image::attr(src)',
                'brand': 'h2 a span::text',
                'asin': 'div::attr(data-asin)'
            },
            'delay_range': (2.0, 4.0),
            'max_pages': 10,
            'requires_selenium': True
        },
        
        'ebay': {
            'base_url': 'https://www.ebay.com',
            'search_url_pattern': 'https://www.ebay.com/sch/i.html?_nkw={query}&_pgn={page}',
            'item_selector': 'div.s-item__container',
            'fields': {
                'title': 'div.s-item__title span::text',
                'price': 'span.s-item__price::text',
                'original_price': 'span.s-item__original-price::text',
                'rating': 'div.clipped span::attr(aria-label)',
                'reviews_count': 'span.s-item__reviews-count::text',
                'availability': 'span.s-item__availability span::text',
                'url': 'a.s-item__link::attr(href)',
                'image': 'div.s-item__image-section img::attr(src)',
                'brand': 'span.s-item__brand::text',
                'item_id': 'div::attr(data-itemid)'
            },
            'delay_range': (1.5, 3.0),
            'max_pages': 5,
            'requires_selenium': False
        },
        
        'books.toscrape.com': {
            'base_url': 'http://books.toscrape.com/',
            'search_url_pattern': 'http://books.toscrape.com/catalogue/category/books_1/page-{page}.html',
            'item_selector': 'article.product_pod',
            'fields': {
                'title': 'h3 a::attr(title)',
                'price': 'p.price_color::text',
                'original_price': 'p.price_color::text',  # No original price on this site
                'rating': 'p.star-rating::attr(class)',
                'reviews_count': '',  # Not available
                'availability': 'p.instock.availability::text',
                'url': 'h3 a::attr(href)',
                'image': 'div.image_container img::attr(src)',
                'brand': '',  # Not available
                'isbn': ''  # Not available
            },
            'delay_range': (1.0, 2.0),
            'max_pages': 50,
            'requires_selenium': False
        }
    }
    
    # Price Analysis Configuration
    PRICE_ANALYSIS = {
        'moving_average_days': [7, 14, 30],
        'volatility_threshold': 15.0,  # 15% price volatility
        'trend_analysis_enabled': True,
        'seasonal_analysis_enabled': True
    }
    
    @classmethod
    def get_user_agent(cls) -> str:
        """Get a random user agent from the list."""
        import random
        return random.choice(cls.USER_AGENTS)
    
    @classmethod
    def get_site_config(cls, site_name: str) -> Dict[str, Any]:
        """Get site-specific configuration."""
        return cls.ECOMMERCE_SITES.get(site_name, {})
    
    @classmethod
    def get_all_sites(cls) -> List[str]:
        """Get list of all configured e-commerce sites."""
        return list(cls.ECOMMERCE_SITES.keys())
    
    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        config_dict = {}
        for attr_name in dir(cls):
            if not attr_name.startswith('_') and not callable(getattr(cls, attr_name)):
                value = getattr(cls, attr_name)
                if not isinstance(value, (type, Path)):
                    config_dict[attr_name] = value
        return config_dict
    
    @classmethod
    def save_to_file(cls, filename: str = 'price_tracker_config.json'):
        """Save configuration to JSON file."""
        config_path = CONFIG_DIR / filename
        with open(config_path, 'w') as f:
            json.dump(cls.to_dict(), f, indent=2, default=str)
        return config_path
    
    @classmethod
    def load_from_file(cls, filename: str = 'price_tracker_config.json'):
        """Load configuration from JSON file."""
        config_path = CONFIG_DIR / filename
        if config_path.exists():
            with open(config_path, 'r') as f:
                config_data = json.load(f)
                for key, value in config_data.items():
                    if hasattr(cls, key):
                        setattr(cls, key, value)
        return config_path

# Environment-based configuration overrides
def load_env_config():
    """Load configuration from environment variables."""
    config = PriceTrackerConfig()
    
    config.LOG_LEVEL = os.getenv('PRICE_TRACKER_LOG_LEVEL', config.LOG_LEVEL)
    config.DEFAULT_TIMEOUT = int(os.getenv('PRICE_TRACKER_TIMEOUT', str(config.DEFAULT_TIMEOUT)))
    config.MAX_RETRIES = int(os.getenv('PRICE_TRACKER_MAX_RETRIES', str(config.MAX_RETRIES)))
    config.DEFAULT_CHECK_INTERVAL = int(os.getenv('PRICE_TRACKER_CHECK_INTERVAL', str(config.DEFAULT_CHECK_INTERVAL)))
    config.ALERT_ENABLED = os.getenv('PRICE_TRACKER_ALERT_ENABLED', 'true').lower() == 'true'
    
    return config

# Initialize configuration
CONFIG = load_env_config()

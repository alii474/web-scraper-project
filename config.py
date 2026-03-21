# config.py
import os
from pathlib import Path

# Project configuration
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"

# Create directories
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# Scraping configuration
DEFAULT_CONFIG = {
    'base_url': 'http://books.toscrape.com/',
    'default_pages': 1,
    'delay': 1.0,
    'timeout': 10,
    'retries': 3,
    'headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
}

# Export configuration
EXPORT_CONFIG = {
    'csv_encoding': 'utf-8',
    'excel_engine': 'openpyxl',
    'date_format': '%Y%m%d_%H%M%S'
}

"""
Multi-Site Web Scraper - Core Engine

Advanced scraper that supports multiple websites with automatic detection
and data normalization. Uses configuration-driven approach for flexibility.
"""

import json
import time
import random
import re
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from urllib.parse import urljoin, urlparse
from datetime import datetime
import requests
from bs4 import BeautifulSoup

from ..utils.logger import get_logger


class MultiSiteScraper:
    """
    Multi-site web scraper with automatic website detection and data normalization.
    
    Features:
    - Automatic website detection from URL
    - Configuration-driven scraping
    - Data normalization to common format
    - Flexible field mapping
    - Error handling and retry logic
    """
    
    def __init__(self, config_file: str = "config.json"):
        """
        Initialize the multi-site scraper.
        
        Args:
            config_file: Path to configuration file
        """
        self.logger = get_logger('multi_site_scraper')
        self.config = self._load_config(config_file)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': random.choice(self.config['global_settings']['user_agents'])
        })
        
        # Statistics
        self.stats = {
            'total_scraped': 0,
            'sites_scraped': {},
            'errors': 0,
            'start_time': datetime.now()
        }
    
    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        try:
            config_path = Path(config_file)
            if not config_path.exists():
                self.logger.error(f"Configuration file not found: {config_file}")
                return {}
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            self.logger.info(f"Loaded configuration for {len(config['websites'])} websites")
            return config
        
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            return {}
    
    def detect_website(self, url: str) -> Optional[str]:
        """
        Detect which website configuration to use based on URL.
        
        Args:
            url: URL to analyze
        
        Returns:
            Website key from configuration or None
        """
        domain = urlparse(url).netloc.lower()
        
        # Direct domain match
        for site_key in self.config['websites']:
            if site_key in domain:
                return site_key
        
        # Partial domain match
        for site_key, site_config in self.config['websites'].items():
            site_domain = urlparse(site_config['base_url']).netloc.lower()
            if site_domain in domain or domain in site_domain:
                return site_key
        
        return None
    
    def scrape_url(self, url: str, max_pages: int = None) -> List[Dict[str, Any]]:
        """
        Scrape data from a URL using the appropriate website configuration.
        
        Args:
            url: URL to scrape
            max_pages: Maximum number of pages to scrape
        
        Returns:
            List of normalized data items
        """
        website_key = self.detect_website(url)
        
        if not website_key:
            self.logger.error(f"No configuration found for URL: {url}")
            return []
        
        website_config = self.config['websites'][website_key]
        self.logger.info(f"Detected website: {website_config['name']} ({website_key})")
        
        # Update statistics
        if website_key not in self.stats['sites_scraped']:
            self.stats['sites_scraped'][website_key] = 0
        self.stats['sites_scraped'][website_key] += 1
        
        # Scrape using website-specific scraper
        scraper = WebsiteScraper(website_key, website_config, self.session)
        return scraper.scrape(url, max_pages)
    
    def scrape_multiple_urls(self, urls: List[str], max_pages: int = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Scrape multiple URLs and group results by website.
        
        Args:
            urls: List of URLs to scrape
            max_pages: Maximum number of pages per URL
        
        Returns:
            Dictionary with website keys as keys and scraped data as values
        """
        results = {}
        
        for url in urls:
            try:
                website_key = self.detect_website(url)
                if not website_key:
                    self.logger.warning(f"Skipping unsupported URL: {url}")
                    continue
                
                if website_key not in results:
                    results[website_key] = []
                
                scraped_data = self.scrape_url(url, max_pages)
                results[website_key].extend(scraped_data)
                
                # Add delay between requests
                delay = random.uniform(1.0, 2.0)
                time.sleep(delay)
            
            except Exception as e:
                self.logger.error(f"Failed to scrape {url}: {e}")
                self.stats['errors'] += 1
        
        return results
    
    def normalize_data(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalize scraped data to common format.
        
        Args:
            raw_data: Raw scraped data from multiple sites
        
        Returns:
            Normalized data in common format
        """
        normalized = []
        common_fields = self.config['global_settings']['output_format']['common_fields']
        
        for item in raw_data:
            normalized_item = {
                'scraped_at': datetime.now().isoformat(),
                'source': item.get('source', 'unknown'),
                'category': item.get('category', 'unknown')
            }
            
            # Map common fields
            for field in common_fields:
                if field in item:
                    normalized_item[field] = item[field]
                else:
                    # Try to find alternative field names
                    normalized_item[field] = self._find_field_value(field, item)
            
            # Add all other fields
            for key, value in item.items():
                if key not in normalized_item:
                    normalized_item[key] = value
            
            normalized.append(normalized_item)
        
        return normalized
    
    def _find_field_value(self, target_field: str, item: Dict[str, Any]) -> Any:
        """Find value for a target field using alternative field names."""
        field_mappings = {
            'price': ['price', 'cost', 'amount', 'value'],
            'rating': ['rating', 'score', 'stars', 'points'],
            'author': ['author', 'author_name', 'posted_by', 'creator'],
            'description': ['description', 'summary', 'content', 'tags', 'quote_tags']
        }
        
        if target_field in field_mappings:
            for alt_field in field_mappings[target_field]:
                if alt_field in item and item[alt_field]:
                    return item[alt_field]
        
        return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get scraping statistics."""
        runtime = datetime.now() - self.stats['start_time']
        
        return {
            'total_scraped': self.stats['total_scraped'],
            'sites_scraped': self.stats['sites_scraped'],
            'errors': self.stats['errors'],
            'runtime_seconds': runtime.total_seconds(),
            'success_rate': (self.stats['total_scraped'] / (self.stats['total_scraped'] + self.stats['errors']) * 100) if (self.stats['total_scraped'] + self.stats['errors']) > 0 else 0
        }


class WebsiteScraper:
    """
    Website-specific scraper with configuration-driven field extraction.
    """
    
    def __init__(self, website_key: str, config: Dict[str, Any], session: requests.Session):
        """
        Initialize website scraper.
        
        Args:
            website_key: Website identifier
            config: Website configuration
            session: Requests session
        """
        self.website_key = website_key
        self.config = config
        self.session = session
        self.logger = get_logger(f'scraper_{website_key}')
        
        # Update session headers if specified
        if 'headers' in config:
            self.session.headers.update(config['headers'])
    
    def scrape(self, url: str, max_pages: int = None) -> List[Dict[str, Any]]:
        """
        Scrape data from the website.
        
        Args:
            url: URL to scrape
            max_pages: Maximum number of pages
        
        Returns:
            List of scraped items
        """
        if not max_pages:
            max_pages = self.config['pagination'].get('max_pages', 3)
        
        all_items = []
        
        for page in range(1, max_pages + 1):
            try:
                # Construct page URL
                page_url = self._get_page_url(url, page)
                
                # Fetch page
                response = self.session.get(page_url, timeout=30)
                
                if response.status_code != 200:
                    self.logger.warning(f"HTTP {response.status_code} for {page_url}")
                    break
                
                # Parse HTML
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract items
                items = self._extract_items(soup)
                
                if not items:
                    self.logger.info(f"No items found on page {page}")
                    break
                
                # Add metadata
                for item in items:
                    item['source'] = self.config['name']
                    item['category'] = self.config['category']
                    item['page_number'] = page
                
                all_items.extend(items)
                
                self.logger.info(f"Scraped {len(items)} items from page {page}")
                
                # Add delay
                delay_range = self.config.get('delay', {'min': 1.0, 'max': 2.0})
                delay = random.uniform(delay_range['min'], delay_range['max'])
                time.sleep(delay)
            
            except Exception as e:
                self.logger.error(f"Error scraping page {page}: {e}")
                break
        
        return all_items
    
    def _get_page_url(self, base_url: str, page: int) -> str:
        """Construct page URL based on pagination pattern."""
        if 'search_url_pattern' in self.config:
            pattern = self.config['search_url_pattern']
            # Handle different pagination patterns
            if '{start}' in pattern and self.config.get('pagination', {}).get('start_pattern') == 'increment':
                # Indeed-style pagination (0, 10, 20, 30...)
                start = (page - 1) * 10
                return pattern.format(start=start)
            else:
                # Standard page-based pagination (1, 2, 3...)
                return pattern.format(page=page)
        
        # For simple pagination
        if page == 1:
            return base_url
        
        # Try to add page parameter
        separator = '&' if '?' in base_url else '?'
        return f"{base_url}{separator}page={page}"
    
    def _extract_items(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract items from the page."""
        items = []
        
        # Get item selector
        item_selector = self.config['item_selector']
        item_elements = soup.select(item_selector)
        
        if not item_elements:
            self.logger.warning(f"No items found with selector: {item_selector}")
            return items
        
        # Extract data from each item
        for item_element in item_elements:
            try:
                item_data = self._extract_item_data(item_element)
                if item_data:
                    items.append(item_data)
            except Exception as e:
                self.logger.error(f"Error extracting item data: {e}")
        
        return items
    
    def _extract_item_data(self, item_element) -> Optional[Dict[str, Any]]:
        """Extract data from a single item element."""
        item_data = {}
        fields_config = self.config['fields']
        
        # Check for sub-selector first
        if 'sub_selector' in self.config:
            sub_element = item_element.select_one(self.config['sub_selector'])
            if sub_element:
                item_element = sub_element
        
        # Extract each field
        for field_name, field_config in fields_config.items():
            try:
                value = self._extract_field_value(item_element, field_config)
                
                if value is not None:
                    # Use custom field name if specified
                    output_field = field_config.get('field_name', field_name)
                    item_data[output_field] = value
            
            except Exception as e:
                self.logger.warning(f"Failed to extract field {field_name}: {e}")
        
        # Check required fields
        required_fields = [k for k, v in fields_config.items() if v.get('required', False)]
        missing_required = [field for field in required_fields if field not in item_data]
        
        if missing_required:
            self.logger.debug(f"Missing required fields: {missing_required}")
            return None
        
        return item_data
    
    def _extract_field_value(self, element, field_config: Dict[str, Any]) -> Any:
        """Extract value for a specific field."""
        selector = field_config['selector']
        attribute = field_config.get('attribute', 'text')
        
        # Find element(s)
        if field_config.get('multiple', False):
            elements = element.select(selector)
            values = []
            for elem in elements:
                value = self._get_element_value(elem, attribute)
                if value:
                    values.append(value)
            return values
        else:
            elem = element.select_one(selector)
            if elem:
                return self._get_element_value(elem, attribute)
        
        return None
    
    def _get_element_value(self, element, attribute: str) -> Any:
        """Get value from element based on attribute type."""
        if attribute == 'text':
            value = element.get_text(strip=True)
        else:
            value = element.get(attribute)
        
        if not value:
            return None
        
        # Apply transformations
        value = self._apply_transformations(value)
        
        # Apply cleaning
        value = self._apply_cleaning(value)
        
        # Apply extraction
        value = self._apply_extraction(value)
        
        return value
    
    def _apply_transformations(self, value: str) -> str:
        """Apply transformations to the value."""
        # Handle absolute URL transformation
        if isinstance(value, str) and value.startswith(('http://', 'https://')):
            return value
        elif isinstance(value, str) and (value.startswith('/') or value.startswith('../')):
            return urljoin('http://', value)
        
        return value
    
    def _apply_cleaning(self, value: str) -> str:
        """Apply cleaning operations to the value."""
        if not value:
            return value
        
        # Strip quotes
        if isinstance(value, str):
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            elif value.startswith("'") and value.endswith("'"):
                value = value[1:-1]
            
            # Clean whitespace
            value = ' '.join(value.split())
        
        return value
    
    def _apply_extraction(self, value: str) -> Union[str, int, float]:
        """Apply data extraction operations."""
        if not isinstance(value, str):
            return value
        
        # Extract numbers
        # Extract price numbers
        price_match = re.search(r'[\d,]+\.?\d*', value.replace('£', '').replace('$', ''))
        if price_match:
            try:
                return float(price_match.group().replace(',', ''))
            except ValueError:
                pass
        
        # Extract integers
        int_match = re.search(r'\d+', value)
        if int_match:
            try:
                return int(int_match.group())
            except ValueError:
                pass
        
        return value

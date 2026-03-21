"""
E-commerce Price Tracker - Core Engine

Advanced price tracking system for e-commerce websites.
Monitors product prices, availability, and sends alerts on price changes.
"""

import time
import random
import requests
from typing import Dict, List, Any, Optional, Union
from urllib.parse import urljoin, urlparse
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
from datetime import datetime, timedelta

from ..utils.logger import get_logger, performance_logger
from ..utils.price_tracker_config import CONFIG


class PriceTrackerEngine:
    """
    Advanced price tracking engine for e-commerce websites.
    
    Features:
    - Multi-site price monitoring
    - Price change detection
    - Availability tracking
    - Historical price data
    - Alert system integration
    """
    
    def __init__(self, sites: List[str] = None, check_interval: int = None):
        """
        Initialize the price tracker engine.
        
        Args:
            sites: List of e-commerce sites to track
            check_interval: Check interval in seconds
        """
        self.logger = get_logger('price_tracker')
        self.performance_logger = performance_logger
        
        # Configuration
        self.sites = sites or ['books.toscrape.com']  # Start with demo site
        self.check_interval = check_interval or CONFIG.DEFAULT_CHECK_INTERVAL
        
        # Session management
        self.session = requests.Session()
        self.session.headers.update(CONFIG.DEFAULT_HEADERS)
        
        # Statistics
        self.stats = {
            'total_checks': 0,
            'price_changes': 0,
            'availability_changes': 0,
            'errors': 0,
            'last_check': None,
            'start_time': datetime.now()
        }
        
        # Price history storage
        self.price_history = {}
        self.availability_history = {}
        
        # Alert system
        self.price_alerts = []
        self.availability_alerts = []
    
    def check_product_price(self, url: str, site_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Check price for a single product.
        
        Args:
            url: Product URL
            site_config: Site-specific configuration
        
        Returns:
            Product data with price information
        """
        try:
            start_time = time.time()
            
            # Fetch page
            response = self.session.get(url, timeout=CONFIG.DEFAULT_TIMEOUT)
            
            if response.status_code != 200:
                self.logger.warning(f"HTTP {response.status_code} for {url}")
                return None
            
            # Parse HTML
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.content, 'lxml')
            
            # Extract product data
            product_data = self._extract_product_data(soup, site_config, url)
            
            if product_data:
                # Add metadata
                product_data['checked_at'] = datetime.now().isoformat()
                product_data['source_url'] = url
                product_data['site'] = site_config.get('name', 'unknown')
                
                # Check for price changes
                self._check_price_changes(product_data)
                self._check_availability_changes(product_data)
                
                # Store in history
                self._store_price_history(product_data)
                
                self.stats['total_checks'] += 1
                self.stats['last_check'] = datetime.now()
                
                load_time = time.time() - start_time
                self.performance_logger.log_timing("price_check", load_time)
            
            return product_data
        
        except Exception as e:
            self.logger.error(f"Failed to check price for {url}: {e}")
            self.stats['errors'] += 1
            return None
    
    def _extract_product_data(self, soup, site_config: Dict[str, Any], url: str) -> Optional[Dict[str, Any]]:
        """Extract product data from HTML."""
        try:
            item_selector = site_config.get('item_selector')
            if not item_selector:
                self.logger.error("No item selector in site configuration")
                return None
            
            # Find product container
            container = soup.select_one(item_selector)
            if not container:
                self.logger.warning(f"Product container not found for {url}")
                return None
            
            product_data = {}
            fields_config = site_config.get('fields', {})
            
            # Extract each field
            for field_name, field_selector in fields_config.items():
                if not field_selector:
                    continue
                
                try:
                    # Handle multiple selectors (comma-separated)
                    if ',' in field_selector:
                        selectors = field_selector.split(',')
                        value = None
                        for selector in selectors:
                            selector = selector.strip()
                            if '::attr(' in selector:
                                # Attribute selector
                                attr_name = selector.split('::attr(')[1].rstrip(')')
                                elem = container.select_one(selector.split('::attr(')[0])
                                if elem:
                                    value = elem.get(attr_name)
                            else:
                                # Text selector
                                elem = container.select_one(selector)
                                if elem:
                                    value = elem.get_text(strip=True)
                            if value:
                                break
                    else:
                        # Single selector
                        if '::attr(' in field_selector:
                            # Attribute selector
                            attr_name = field_selector.split('::attr(')[1].rstrip(')')
                            elem = container.select_one(field_selector.split('::attr(')[0])
                            if elem:
                                value = elem.get(attr_name)
                        else:
                            # Text selector
                            elem = container.select_one(field_selector)
                            if elem:
                                value = elem.get_text(strip=True)
                    
                    product_data[field_name] = value
                
                except Exception as e:
                    self.logger.warning(f"Failed to extract {field_name}: {e}")
                    product_data[field_name] = None
            
            # Clean and process data
            product_data = self._clean_product_data(product_data)
            
            return product_data
        
        except Exception as e:
            self.logger.error(f"Failed to extract product data: {e}")
            return None
    
    def _clean_product_data(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and process extracted product data."""
        # Clean price
        if 'price' in product_data and product_data['price']:
            product_data['price'] = self._clean_price(product_data['price'])
        
        # Clean original price
        if 'original_price' in product_data and product_data['original_price']:
            product_data['original_price'] = self._clean_price(product_data['original_price'])
        
        # Clean rating
        if 'rating' in product_data and product_data['rating']:
            product_data['rating'] = self._clean_rating(product_data['rating'])
        
        # Clean availability
        if 'availability' in product_data and product_data['availability']:
            product_data['availability'] = self._clean_availability(product_data['availability'])
        
        # Make URL absolute
        if 'url' in product_data and product_data['url']:
            if not product_data['url'].startswith(('http://', 'https://')):
                product_data['url'] = urljoin('https://www.amazon.com', product_data['url'])
        
        return product_data
    
    def _clean_price(self, price_text: str) -> Optional[float]:
        """Clean and convert price text to float."""
        if not price_text:
            return None
        
        try:
            import re
            # Remove currency symbols and clean text
            cleaned = re.sub(r'[^\d.,]', '', str(price_text))
            
            # Handle different decimal formats
            if ',' in cleaned and '.' in cleaned:
                parts = cleaned.rsplit(',', 1)
                cleaned = parts[0].replace(',', '') + '.' + parts[1]
            elif ',' in cleaned:
                cleaned = cleaned.replace(',', '.')
            
            return float(cleaned)
        
        except (ValueError, TypeError):
            return None
    
    def _clean_rating(self, rating_text: str) -> Optional[str]:
        """Clean rating text."""
        if not rating_text:
            return None
        
        # Extract numeric rating from text
        import re
        match = re.search(r'(\d+\.?\d*)', str(rating_text))
        if match:
            return match.group(1)
        return rating_text
    
    def _clean_availability(self, availability_text: str) -> str:
        """Clean availability text."""
        if not availability_text:
            return "Unknown"
        
        availability = str(availability_text).lower().strip()
        
        # Determine availability status
        if any(word in availability for word in ['in stock', 'available', 'ready to ship']):
            return "In Stock"
        elif any(word in availability for word in ['out of stock', 'unavailable', 'sold out']):
            return "Out of Stock"
        elif any(word in availability for word in ['limited', 'few left', 'low stock']):
            return "Limited Stock"
        else:
            return "Unknown"
    
    def _check_price_changes(self, product_data: Dict[str, Any]):
        """Check for price changes and create alerts."""
        product_id = self._get_product_id(product_data)
        current_price = product_data.get('price')
        
        if not current_price:
            return
        
        # Get previous price
        previous_price = None
        if product_id in self.price_history:
            history = self.price_history[product_id]
            if history:
                previous_price = history[-1].get('price')
        
        if previous_price and previous_price != current_price:
            # Calculate price change
            price_change = current_price - previous_price
            price_change_percent = (price_change / previous_price) * 100
            
            # Determine if alert is needed
            alert_needed = False
            alert_type = "price_change"
            
            if price_change < 0 and abs(price_change_percent) >= CONFIG.PRICE_CHANGE_THRESHOLD:
                alert_needed = True
                alert_type = "price_drop"
            elif price_change > 0 and CONFIG.PRICE_INCREASE_ALERTS:
                alert_needed = True
                alert_type = "price_increase"
            
            if alert_needed:
                alert = {
                    'type': alert_type,
                    'product_id': product_id,
                    'title': product_data.get('title', 'Unknown Product'),
                    'previous_price': previous_price,
                    'current_price': current_price,
                    'price_change': price_change,
                    'price_change_percent': price_change_percent,
                    'url': product_data.get('url'),
                    'timestamp': datetime.now().isoformat()
                }
                
                self.price_alerts.append(alert)
                self.stats['price_changes'] += 1
                
                self.logger.info(f"Price {alert_type}: {product_data.get('title')} - "
                               f"£{previous_price:.2f} → £{current_price:.2f} ({price_change_percent:+.1f}%)")
    
    def _check_availability_changes(self, product_data: Dict[str, Any]):
        """Check for availability changes and create alerts."""
        product_id = self._get_product_id(product_data)
        current_availability = product_data.get('availability', 'Unknown')
        
        # Get previous availability
        previous_availability = None
        if product_id in self.availability_history:
            history = self.availability_history[product_id]
            if history:
                previous_availability = history[-1]
        
        if previous_availability and previous_availability != current_availability:
            # Create availability alert
            alert = {
                'type': 'availability_change',
                'product_id': product_id,
                'title': product_data.get('title', 'Unknown Product'),
                'previous_availability': previous_availability,
                'current_availability': current_availability,
                'url': product_data.get('url'),
                'timestamp': datetime.now().isoformat()
            }
            
            self.availability_alerts.append(alert)
            self.stats['availability_changes'] += 1
            
            self.logger.info(f"Availability change: {product_data.get('title')} - "
                           f"{previous_availability} → {current_availability}")
    
    def _get_product_id(self, product_data: Dict[str, Any]) -> str:
        """Generate unique product ID."""
        # Use URL as primary identifier
        url = product_data.get('url', '')
        title = product_data.get('title', '')
        
        # Create hash from URL and title
        id_string = f"{url}_{title}"
        return hashlib.md5(id_string.encode()).hexdigest()
    
    def _store_price_history(self, product_data: Dict[str, Any]):
        """Store product data in history."""
        product_id = self._get_product_id(product_data)
        
        # Store price history
        if product_id not in self.price_history:
            self.price_history[product_id] = []
        
        price_entry = {
            'price': product_data.get('price'),
            'original_price': product_data.get('original_price'),
            'timestamp': product_data.get('checked_at'),
            'url': product_data.get('url')
        }
        
        self.price_history[product_id].append(price_entry)
        
        # Limit history size
        max_entries = CONFIG.MAX_PRICE_HISTORY_DAYS * 24  # Assuming hourly checks
        if len(self.price_history[product_id]) > max_entries:
            self.price_history[product_id] = self.price_history[product_id][-max_entries:]
        
        # Store availability history
        if product_id not in self.availability_history:
            self.availability_history[product_id] = []
        
        availability_entry = product_data.get('availability', 'Unknown')
        self.availability_history[product_id].append(availability_entry)
        
        # Limit availability history
        if len(self.availability_history[product_id]) > max_entries:
            self.availability_history[product_id] = self.availability_history[product_id][-max_entries:]
    
    def track_products(self, product_urls: List[str], site_name: str = None) -> List[Dict[str, Any]]:
        """
        Track multiple products.
        
        Args:
            product_urls: List of product URLs to track
            site_name: Site name for configuration
        
        Returns:
            List of product data
        """
        if site_name:
            site_config = CONFIG.get_site_config(site_name)
            site_config['name'] = site_name
        else:
            # Auto-detect site from URL
            site_config = self._auto_detect_site_config(product_urls[0] if product_urls else '')
        
        if not site_config:
            self.logger.error(f"No configuration found for site: {site_name}")
            return []
        
        results = []
        
        for url in product_urls:
            try:
                # Add delay between requests
                if results:
                    delay = random.uniform(*site_config.get('delay_range', (2.0, 4.0)))
                    time.sleep(delay)
                
                product_data = self.check_product_price(url, site_config)
                if product_data:
                    results.append(product_data)
            
            except Exception as e:
                self.logger.error(f"Failed to track product {url}: {e}")
        
        return results
    
    def _auto_detect_site_config(self, url: str) -> Dict[str, Any]:
        """Auto-detect site configuration from URL."""
        domain = urlparse(url).netloc.lower()
        
        for site_name, site_config in CONFIG.ECOMMERCE_SITES.items():
            if site_name in domain or domain in site_config.get('base_url', ''):
                config = site_config.copy()
                config['name'] = site_name
                return config
        
        return {}
    
    def get_price_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent price alerts."""
        return self.price_alerts[-limit:] if self.price_alerts else []
    
    def get_availability_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent availability alerts."""
        return self.availability_alerts[-limit:] if self.availability_alerts else []
    
    def get_product_price_history(self, product_id: str) -> List[Dict[str, Any]]:
        """Get price history for a specific product."""
        return self.price_history.get(product_id, [])
    
    def get_price_trends(self, product_id: str, days: int = 30) -> Dict[str, Any]:
        """
        Analyze price trends for a product.
        
        Args:
            product_id: Product ID
            days: Number of days to analyze
        
        Returns:
            Price trend analysis
        """
        history = self.get_product_price_history(product_id)
        
        if not history:
            return {}
        
        # Filter by date
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_history = [
            entry for entry in history 
            if datetime.fromisoformat(entry['timestamp']) > cutoff_date
        ]
        
        if not recent_history:
            return {}
        
        prices = [entry['price'] for entry in recent_history if entry['price']]
        
        if not prices:
            return {}
        
        # Calculate trend statistics
        avg_price = sum(prices) / len(prices)
        min_price = min(prices)
        max_price = max(prices)
        
        # Simple trend detection
        if len(prices) >= 2:
            price_change = prices[-1] - prices[0]
            trend = "increasing" if price_change > 0 else "decreasing" if price_change < 0 else "stable"
        else:
            trend = "insufficient_data"
        
        return {
            'product_id': product_id,
            'period_days': days,
            'data_points': len(prices),
            'average_price': avg_price,
            'min_price': min_price,
            'max_price': max_price,
            'price_range': max_price - min_price,
            'current_price': prices[-1] if prices else None,
            'trend': trend,
            'volatility': ((max_price - min_price) / avg_price * 100) if avg_price > 0 else 0
        }
    
    def get_tracker_stats(self) -> Dict[str, Any]:
        """Get tracker statistics."""
        runtime = datetime.now() - self.stats['start_time']
        
        return {
            'total_checks': self.stats['total_checks'],
            'price_changes': self.stats['price_changes'],
            'availability_changes': self.stats['availability_changes'],
            'errors': self.stats['errors'],
            'tracked_products': len(self.price_history),
            'price_alerts': len(self.price_alerts),
            'availability_alerts': len(self.availability_alerts),
            'last_check': self.stats['last_check'].isoformat() if self.stats['last_check'] else None,
            'runtime_seconds': runtime.total_seconds(),
            'checks_per_hour': self.stats['total_checks'] / (runtime.total_seconds() / 3600) if runtime.total_seconds() > 0 else 0
        }

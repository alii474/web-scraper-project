"""
Advanced Web Scraper with Selenium Support

Main scraper class that combines all components into a cohesive system.
Supports both static and dynamic websites with intelligent fallback.
"""

import time
from typing import Dict, List, Any, Optional, Union
from urllib.parse import urljoin, urlparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import random

from ..core.engine import SmartScrapingEngine, ConcurrentScrapingEngine
from ..parsers.data_parser import AdvancedDataParser, ParsedItem
from ..storage.advanced_storage import AdvancedStorageManager
from ..utils.logger import get_logger, performance_logger
from ..utils.config import CONFIG


class SeleniumDriver:
    """Manages Selenium WebDriver with intelligent configuration."""
    
    def __init__(self, headless: bool = True, timeout: int = 30):
        """
        Initialize Selenium driver.
        
        Args:
            headless: Whether to run in headless mode
            timeout: Default timeout for waits
        """
        self.logger = get_logger('selenium_driver')
        self.headless = headless
        self.timeout = timeout
        self.driver = None
        
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
    
    def start(self):
        """Start the WebDriver."""
        try:
            options = Options()
            
            if self.headless:
                options.add_argument('--headless')
            
            # Performance and compatibility options
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-web-security')
            options.add_argument('--disable-features=VizDisplayCompositor')
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-plugins')
            options.add_argument('--disable-images')  # Faster loading
            options.add_argument('--disable-javascript')  # Can be enabled if needed
            
            # Set window size
            options.add_argument('--window-size=1920,1080')
            
            # Use random user agent
            options.add_argument(f'--user-agent={CONFIG.get_user_agent()}')
            
            # Create driver
            self.driver = webdriver.Chrome(options=options)
            self.driver.set_page_load_timeout(self.timeout)
            
            self.logger.info("Selenium WebDriver started successfully")
        
        except Exception as e:
            self.logger.error(f"Failed to start Selenium WebDriver: {e}")
            raise
    
    def stop(self):
        """Stop the WebDriver."""
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info("Selenium WebDriver stopped")
            except Exception as e:
                self.logger.error(f"Error stopping WebDriver: {e}")
            finally:
                self.driver = None
    
    def get_page_source(self, url: str, wait_for: str = None) -> Optional[str]:
        """
        Get page source with optional wait condition.
        
        Args:
            url: URL to fetch
            wait_for: CSS selector to wait for
        
        Returns:
            Page source HTML or None
        """
        if not self.driver:
            self.logger.error("WebDriver not started")
            return None
        
        try:
            self.logger.info(f"Loading page with Selenium: {url}")
            start_time = time.time()
            
            # Load page
            self.driver.get(url)
            
            # Wait for specific element if provided
            if wait_for:
                try:
                    WebDriverWait(self.driver, self.timeout).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, wait_for))
                    )
                except TimeoutException:
                    self.logger.warning(f"Timeout waiting for element: {wait_for}")
            
            # Additional wait for page to settle
            time.sleep(random.uniform(1, 3))
            
            # Get page source
            page_source = self.driver.page_source
            load_time = time.time() - start_time
            
            self.performance_logger.log_timing("selenium_page_load", load_time)
            self.logger.info(f"Page loaded in {load_time:.2f}s")
            
            return page_source
        
        except WebDriverException as e:
            self.logger.error(f"Selenium error loading {url}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error with Selenium: {e}")
            return None
    
    def execute_script(self, script: str) -> Any:
        """Execute JavaScript in the browser."""
        if self.driver:
            return self.driver.execute_script(script)
        return None
    
    def scroll_page(self):
        """Scroll the page to trigger lazy loading."""
        if self.driver:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)


class AdvancedWebScraper:
    """
    Advanced web scraper with intelligent fallback between requests and Selenium.
    
    Features:
    - Automatic detection of static vs dynamic content
    - Intelligent fallback mechanisms
    - Concurrent scraping support
    - Comprehensive error handling
    - Performance monitoring
    """
    
    def __init__(self, 
                 use_selenium: bool = None,
                 max_pages: int = None,
                 concurrent: bool = False,
                 rate_limit: float = 1.0):
        """
        Initialize the advanced web scraper.
        
        Args:
            use_selenium: Force Selenium usage (auto-detect if None)
            max_pages: Maximum pages to scrape
            concurrent: Enable concurrent scraping
            rate_limit: Rate limiting delay
        """
        self.logger = get_logger('advanced_scraper')
        self.performance_logger = performance_logger
        
        # Configuration
        self.use_selenium = use_selenium
        self.max_pages = max_pages or CONFIG.DEFAULT_MAX_PAGES
        self.concurrent = concurrent
        self.rate_limit = rate_limit
        
        # Initialize components
        self.engine = ConcurrentScrapingEngine() if concurrent else SmartScrapingEngine()
        self.parser = AdvancedDataParser()
        self.storage = AdvancedStorageManager()
        
        # Selenium driver (lazy initialization)
        self.selenium_driver = None
        
        # Statistics
        self.stats = {
            'pages_scraped': 0,
            'items_scraped': 0,
            'selenium_used': 0,
            'requests_used': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None
        }
    
    def _should_use_selenium(self, url: str, sample_response: str = None) -> bool:
        """
        Determine if Selenium should be used for this URL.
        
        Args:
            url: Target URL
            sample_response: Sample HTML response
        
        Returns:
            True if Selenium should be used
        """
        if self.use_selenium is not None:
            return self.use_selenium
        
        # Check for known dynamic sites
        dynamic_indicators = [
            'react', 'angular', 'vue.js', 'ember', 'backbone',
            'spa', 'single-page', 'dynamic', 'ajax', 'xhr'
        ]
        
        url_lower = url.lower()
        if any(indicator in url_lower for indicator in dynamic_indicators):
            return True
        
        # Check sample response for JavaScript content
        if sample_response:
            js_indicators = [
                'data-react', 'ng-', 'vue-', 'data-ember',
                'onclick', 'onload', 'script src', 'javascript:',
                'require.js', 'webpack', 'bundle'
            ]
            
            sample_lower = sample_response.lower()
            js_count = sum(1 for indicator in js_indicators if indicator in sample_lower)
            
            # If many JavaScript indicators, use Selenium
            if js_count >= 3:
                return True
        
        return False
    
    def _get_selenium_driver(self) -> SeleniumDriver:
        """Get or create Selenium driver."""
        if not self.selenium_driver:
            self.selenium_driver = SeleniumDriver(
                headless=CONFIG.SELENIUM_HEADLESS,
                timeout=CONFIG.SELENIUM_TIMEOUT
            )
            self.selenium_driver.start()
        
        return self.selenium_driver
    
    def _fetch_page(self, url: str, use_selenium: bool = None) -> Optional[str]:
        """
        Fetch page content using appropriate method.
        
        Args:
            url: URL to fetch
            use_selenium: Force Selenium usage
        
        Returns:
            Page HTML or None
        """
        # Determine if Selenium should be used
        if use_selenium is None:
            # First try with requests
            response = self.engine.fetch(url)
            
            if response and response.status_code == 200:
                if self._should_use_selenium(url, response.text):
                    self.logger.info("Dynamic content detected, switching to Selenium")
                    selenium_driver = self._get_selenium_driver()
                    html = selenium_driver.get_page_source(url)
                    self.stats['selenium_used'] += 1
                    return html
                else:
                    self.stats['requests_used'] += 1
                    return response.text
            else:
                # Requests failed, try Selenium as fallback
                self.logger.info("Requests failed, trying Selenium fallback")
                selenium_driver = self._get_selenium_driver()
                html = selenium_driver.get_page_source(url)
                self.stats['selenium_used'] += 1
                return html
        else:
            # Force the specified method
            if use_selenium:
                selenium_driver = self._get_selenium_driver()
                html = selenium_driver.get_page_source(url)
                self.stats['selenium_used'] += 1
                return html
            else:
                response = self.engine.fetch(url)
                self.stats['requests_used'] += 1
                return response.text if response else None
    
    def _get_pagination_urls(self, base_url: str, site_config: Dict[str, Any]) -> List[str]:
        """
        Generate pagination URLs.
        
        Args:
            base_url: Base URL
            site_config: Site configuration
        
        Returns:
            List of pagination URLs
        """
        urls = [base_url]
        pagination_pattern = site_config.get('pagination_pattern')
        
        if not pagination_pattern:
            return urls
        
        max_pages = site_config.get('max_pages', self.max_pages)
        
        for page in range(2, min(max_pages + 1, self.max_pages + 1)):
            page_url = pagination_pattern.format(page=page)
            
            # Make URL absolute if needed
            if not page_url.startswith(('http://', 'https://')):
                page_url = urljoin(base_url, page_url)
            
            urls.append(page_url)
        
        return urls
    
    def scrape_url(self, url: str, max_pages: int = None, 
                   formats: List[str] = None, output_filename: str = None) -> Dict[str, Any]:
        """
        Scrape a single URL with pagination support.
        
        Args:
            url: URL to scrape
            max_pages: Maximum pages to scrape
            formats: Output formats
            output_filename: Custom output filename
        
        Returns:
            Scraping results
        """
        start_time = time.time()
        self.stats['start_time'] = start_time
        
        self.logger.log_scraping_start(url, max_pages or self.max_pages)
        
        try:
            # Get site configuration
            site_config = CONFIG.get_site_config(url)
            
            # Generate pagination URLs
            max_pages_to_scrape = min(max_pages or self.max_pages, site_config.get('max_pages', self.max_pages))
            urls = self._get_pagination_urls(url, site_config)[:max_pages_to_scrape]
            
            self.logger.info(f"Will scrape {len(urls)} pages")
            
            # Scrape pages
            all_items = []
            
            if self.concurrent and len(urls) > 1:
                # Concurrent scraping
                html_pages = []
                page_urls = []
                
                for page_url in urls:
                    html = self._fetch_page(page_url)
                    if html:
                        html_pages.append(html)
                        page_urls.append(page_url)
                
                # Parse all pages
                all_items = self.parser.parse_multiple_pages(html_pages, page_urls, site_config)
            else:
                # Sequential scraping
                for i, page_url in enumerate(urls):
                    self.logger.info(f"Scraping page {i+1}/{len(urls)}: {page_url}")
                    
                    html = self._fetch_page(page_url)
                    if html:
                        items = self.parser.parse_html(html, page_url, site_config)
                        all_items.extend(items)
                        self.stats['pages_scraped'] += 1
                    else:
                        self.logger.error(f"Failed to fetch page: {page_url}")
                        self.stats['errors'] += 1
                    
                    # Rate limiting between pages
                    if i < len(urls) - 1:
                        delay = random.uniform(*site_config.get('delay_range', (1.0, 3.0)))
                        time.sleep(delay)
            
            # Remove duplicates if enabled
            if CONFIG.REMOVE_DUPLICATES:
                original_count = len(all_items)
                # Use storage manager for deduplication
                storage_results = self.storage.save_items(
                    all_items, 
                    formats=[],  # Don't save, just deduplicate
                    remove_duplicates=True
                )
                duplicates_removed = original_count - storage_results['stats']['items_saved']
                self.logger.info(f"Removed {duplicates_removed} duplicates")
            
            # Save data
            if formats:
                storage_results = self.storage.save_items(
                    all_items, 
                    formats=formats, 
                    filename=output_filename,
                    remove_duplicates=CONFIG.REMOVE_DUPLICATES
                )
            else:
                storage_results = {'saved_files': [], 'stats': {}}
            
            # Update statistics
            self.stats['items_scraped'] = len(all_items)
            self.stats['end_time'] = time.time()
            duration = self.stats['end_time'] - self.stats['start_time']
            
            # Log completion
            self.logger.log_scraping_end(len(all_items), duration)
            
            # Prepare results
            results = {
                'url': url,
                'pages_scraped': self.stats['pages_scraped'],
                'items_scraped': len(all_items),
                'duplicates_removed': storage_results['stats'].get('duplicates_removed', 0),
                'processing_time': duration,
                'saved_files': storage_results['saved_files'],
                'formats_used': formats or [],
                'stats': self.stats.copy(),
                'items': all_items[:5],  # Return first 5 items as sample
                'site_config': site_config
            }
            
            return results
        
        except Exception as e:
            self.logger.log_error_with_context(e, {'url': url})
            self.stats['errors'] += 1
            self.stats['end_time'] = time.time()
            raise
        
        finally:
            # Cleanup Selenium driver if used
            if self.selenium_driver:
                self.selenium_driver.stop()
                self.selenium_driver = None
    
    def scrape_multiple_urls(self, urls: List[str], **kwargs) -> List[Dict[str, Any]]:
        """
        Scrape multiple URLs.
        
        Args:
            urls: List of URLs to scrape
            **kwargs: Additional scraping arguments
        
        Returns:
            List of scraping results
        """
        results = []
        
        for url in urls:
            try:
                result = self.scrape_url(url, **kwargs)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Failed to scrape {url}: {e}")
                results.append({
                    'url': url,
                    'error': str(e),
                    'items_scraped': 0
                })
        
        return results
    
    def get_scraping_stats(self) -> Dict[str, Any]:
        """Get comprehensive scraping statistics."""
        stats = self.stats.copy()
        
        if stats['start_time'] and stats['end_time']:
            stats['total_duration'] = stats['end_time'] - stats['start_time']
            stats['items_per_second'] = stats['items_scraped'] / stats['total_duration']
        
        stats['engine_stats'] = self.engine.get_stats()
        stats['storage_stats'] = self.storage.get_storage_stats()
        
        return stats
    
    def reset_stats(self):
        """Reset scraping statistics."""
        self.stats = {
            'pages_scraped': 0,
            'items_scraped': 0,
            'selenium_used': 0,
            'requests_used': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None
        }
        self.engine.reset_stats()
    
    def close(self):
        """Cleanup resources."""
        if self.selenium_driver:
            self.selenium_driver.stop()
        
        self.engine.close()
        self.logger.info("Advanced scraper closed")

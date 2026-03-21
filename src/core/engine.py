"""
Advanced Smart Scraping Engine

Core scraping functionality with intelligent features:
- User-agent rotation
- Exponential backoff retry mechanism
- Proxy support
- Rate limiting
- Request session management
"""

import time
import random
import requests
from typing import Optional, Dict, List, Any, Union
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib

from ..utils.logger import get_logger, performance_logger
from ..utils.config import CONFIG


class UserAgentRotator:
    """Rotates user agents to avoid detection."""
    
    def __init__(self, user_agents: List[str] = None):
        self.user_agents = user_agents or CONFIG.USER_AGENTS
        self.current_index = 0
        self.lock = threading.Lock()
    
    def get_user_agent(self) -> str:
        """Get next user agent in rotation."""
        with self.lock:
            user_agent = self.user_agents[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.user_agents)
            return user_agent
    
    def get_random_user_agent(self) -> str:
        """Get random user agent."""
        return random.choice(self.user_agents)


class ProxyRotator:
    """Manages proxy rotation for requests."""
    
    def __init__(self, proxy_list: List[str] = None):
        self.proxy_list = proxy_list or CONFIG.PROXY_LIST
        self.current_index = 0
        self.failed_proxies = set()
        self.lock = threading.Lock()
    
    def get_proxy(self) -> Optional[Dict[str, str]]:
        """Get next proxy in rotation."""
        if not self.proxy_list or not CONFIG.PROXY_ENABLED:
            return None
        
        with self.lock:
            # Try to find a working proxy
            attempts = 0
            while attempts < len(self.proxy_list):
                proxy = self.proxy_list[self.current_index]
                self.current_index = (self.current_index + 1) % len(self.proxy_list)
                
                if proxy not in self.failed_proxies:
                    return {'http': proxy, 'https': proxy}
                
                attempts += 1
            
            # All proxies failed, reset and try again
            self.failed_proxies.clear()
            return {'http': self.proxy_list[0], 'https': self.proxy_list[0]}
    
    def mark_proxy_failed(self, proxy: str):
        """Mark proxy as failed."""
        with self.lock:
            self.failed_proxies.add(proxy)


class RetryHandler:
    """Handles retry logic with exponential backoff."""
    
    @staticmethod
    def exponential_backoff(attempt: int, base_delay: float = 1.0, max_delay: float = 60.0) -> float:
        """
        Calculate exponential backoff delay.
        
        Args:
            attempt: Current attempt number
            base_delay: Base delay in seconds
            max_delay: Maximum delay in seconds
        
        Returns:
            Delay in seconds
        """
        delay = base_delay * (2 ** attempt)
        return min(delay, max_delay)
    
    @staticmethod
    def should_retry(response: Optional[requests.Response], exception: Optional[Exception]) -> bool:
        """
        Determine if request should be retried.
        
        Args:
            response: HTTP response object
            exception: Exception that occurred
        
        Returns:
            True if should retry
        """
        if exception:
            # Retry on network errors
            return isinstance(exception, (requests.ConnectionError, 
                                        requests.Timeout, 
                                        requests.RequestException))
        
        if response:
            # Retry on server errors and some client errors
            return response.status_code in [429, 500, 502, 503, 504]
        
        return False


class RobotsTxtChecker:
    """Handles robots.txt compliance."""
    
    def __init__(self):
        self.parsers = {}  # Cache for robots.txt parsers
        self.lock = threading.Lock()
    
    def can_fetch(self, url: str, user_agent: str = '*') -> bool:
        """
        Check if URL can be fetched according to robots.txt.
        
        Args:
            url: URL to check
            user_agent: User agent string
        
        Returns:
            True if URL can be fetched
        """
        try:
            parsed_url = urlparse(url)
            domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            with self.lock:
                if domain not in self.parsers:
                    robots_url = f"{domain}/robots.txt"
                    parser = RobotFileParser()
                    parser.set_url(robots_url)
                    
                    try:
                        parser.read()
                        self.parsers[domain] = parser
                    except Exception:
                        # If robots.txt can't be fetched, allow access
                        self.parsers[domain] = None
                
                parser = self.parsers[domain]
                if parser is None:
                    return True
                
                return parser.can_fetch(user_agent, url)
        
        except Exception:
            # If anything goes wrong, allow access
            return True


class SmartScrapingEngine:
    """
    Advanced scraping engine with intelligent features.
    
    Features:
    - User-agent rotation
    - Exponential backoff retry
    - Proxy support
    - Rate limiting
    - Robots.txt compliance
    - Session management
    """
    
    def __init__(self, 
                 user_agents: List[str] = None,
                 proxy_list: List[str] = None,
                 respect_robots: bool = True,
                 rate_limit_delay: float = 1.0):
        """
        Initialize the smart scraping engine.
        
        Args:
            user_agents: List of user agents for rotation
            proxy_list: List of proxies for rotation
            respect_robots: Whether to respect robots.txt
            rate_limit_delay: Base delay between requests
        """
        self.logger = get_logger('scraping_engine')
        self.performance_logger = performance_logger
        
        # Initialize components
        self.ua_rotator = UserAgentRotator(user_agents)
        self.proxy_rotator = ProxyRotator(proxy_list)
        self.retry_handler = RetryHandler()
        self.robots_checker = RobotsTxtChecker() if respect_robots else None
        
        # Session management
        self.session = requests.Session()
        self.rate_limit_delay = rate_limit_delay
        self.last_request_time = 0
        
        # Statistics
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'retries': 0,
            'proxies_used': 0
        }
        
        # Setup session
        self._setup_session()
    
    def _setup_session(self):
        """Setup the requests session with default settings."""
        self.session.headers.update(CONFIG.DEFAULT_HEADERS)
        
        # Configure retry strategy for the session
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        retry_strategy = Retry(
            total=CONFIG.MAX_RETRIES,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def _rate_limit(self):
        """Implement rate limiting between requests."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit_delay:
            wait_time = self.rate_limit_delay - time_since_last
            self.performance_logger.log_rate_limit(
                "rate_limiting", wait_time, 
                delay=self.rate_limit_delay
            )
            time.sleep(wait_time)
        
        self.last_request_time = time.time()
    
    def _prepare_request_kwargs(self) -> Dict[str, Any]:
        """Prepare request kwargs with user agent and proxy."""
        kwargs = {
            'timeout': CONFIG.DEFAULT_TIMEOUT,
            'headers': {
                'User-Agent': self.ua_rotator.get_user_agent()
            }
        }
        
        # Add proxy if available
        proxy = self.proxy_rotator.get_proxy()
        if proxy:
            kwargs['proxies'] = proxy
            self.stats['proxies_used'] += 1
        
        return kwargs
    
    def fetch(self, url: str, method: str = 'GET', **kwargs) -> Optional[requests.Response]:
        """
        Fetch URL with intelligent retry and error handling.
        
        Args:
            url: URL to fetch
            method: HTTP method
            **kwargs: Additional request arguments
        
        Returns:
            Response object or None if failed
        """
        # Check robots.txt
        if self.robots_checker and not self.robots_checker.can_fetch(url):
            self.logger.warning(f"URL blocked by robots.txt: {url}")
            return None
        
        # Rate limiting
        self._rate_limit()
        
        # Merge request kwargs
        request_kwargs = self._prepare_request_kwargs()
        request_kwargs.update(kwargs)
        
        self.stats['total_requests'] += 1
        
        # Retry logic
        for attempt in range(CONFIG.MAX_RETRIES):
            try:
                start_time = time.time()
                
                response = self.session.request(method, url, **request_kwargs)
                
                response_time = time.time() - start_time
                self.performance_logger.log_timing("http_request", response_time)
                
                # Log request
                self.logger.log_request(url, response.status_code, response_time)
                
                if response.status_code == 200:
                    self.stats['successful_requests'] += 1
                    return response
                elif self.retry_handler.should_retry(response, None):
                    wait_time = self.retry_handler.exponential_backoff(attempt)
                    self.logger.warning(
                        f"Request failed (HTTP {response.status_code}), "
                        f"retrying in {wait_time:.2f}s"
                    )
                    time.sleep(wait_time)
                    self.stats['retries'] += 1
                else:
                    self.logger.error(f"Request failed: HTTP {response.status_code}")
                    break
            
            except Exception as e:
                self.logger.log_error_with_context(e, {'url': url, 'attempt': attempt + 1})
                
                if self.retry_handler.should_retry(None, e):
                    wait_time = self.retry_handler.exponential_backoff(attempt)
                    time.sleep(wait_time)
                    self.stats['retries'] += 1
                else:
                    break
        
        self.stats['failed_requests'] += 1
        return None
    
    def fetch_multiple(self, urls: List[str], max_workers: int = 5) -> List[Optional[requests.Response]]:
        """
        Fetch multiple URLs concurrently.
        
        Args:
            urls: List of URLs to fetch
            max_workers: Maximum number of concurrent workers
        
        Returns:
            List of response objects
        """
        responses = [None] * len(urls)
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all requests
            future_to_index = {
                executor.submit(self.fetch, url): i 
                for i, url in enumerate(urls)
            }
            
            # Collect responses as they complete
            for future in as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    responses[index] = future.result()
                except Exception as e:
                    self.logger.error(f"Failed to fetch URL {urls[index]}: {e}")
                    responses[index] = None
        
        return responses
    
    def get_stats(self) -> Dict[str, Any]:
        """Get scraping statistics."""
        stats = self.stats.copy()
        stats['success_rate'] = (
            stats['successful_requests'] / stats['total_requests'] 
            if stats['total_requests'] > 0 else 0
        )
        return stats
    
    def reset_stats(self):
        """Reset scraping statistics."""
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'retries': 0,
            'proxies_used': 0
        }
    
    def close(self):
        """Close the session and cleanup resources."""
        self.session.close()


class ConcurrentScrapingEngine(SmartScrapingEngine):
    """
    Enhanced scraping engine with advanced concurrency features.
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.request_semaphore = threading.Semaphore(10)  # Limit concurrent requests
    
    def fetch_with_semaphore(self, url: str, **kwargs) -> Optional[requests.Response]:
        """Fetch URL with semaphore control."""
        with self.request_semaphore:
            return self.fetch(url, **kwargs)
    
    def fetch_batch(self, urls: List[str], batch_size: int = 50) -> List[Optional[requests.Response]]:
        """
        Fetch URLs in batches to manage memory and rate limiting.
        
        Args:
            urls: List of URLs to fetch
            batch_size: Size of each batch
        
        Returns:
            List of response objects
        """
        all_responses = []
        
        for i in range(0, len(urls), batch_size):
            batch_urls = urls[i:i + batch_size]
            batch_responses = self.fetch_multiple(batch_urls)
            all_responses.extend(batch_responses)
            
            # Add delay between batches
            if i + batch_size < len(urls):
                time.sleep(self.rate_limit_delay * 2)
        
        return all_responses

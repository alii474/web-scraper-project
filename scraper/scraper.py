import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import logging
import json
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse
import re
from pathlib import Path

class WebScraper:
    """
    Professional Web Scraper for extracting structured data from websites.

    Features:
    - Modular design with separate functions for fetching, parsing, saving
    - Comprehensive error handling and logging
    - Pagination support with automatic page detection
    - Browser-like headers to avoid blocking
    - Data cleaning and validation
    - Multiple export formats (CSV, Excel)
    - CLI interface for easy usage
    """

    def __init__(self, base_url: str = "http://books.toscrape.com/", delay: float = 1.0):
        """
        Initialize the web scraper with configuration.

        Args:
            base_url: Base URL of the website to scrape
            delay: Delay between requests in seconds
        """
        self.base_url = base_url
        self.delay = delay
        self.session = requests.Session()

        # Setup logging
        self.setup_logging()

        # Browser-like headers to avoid blocking
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

        self.session.headers.update(self.headers)

    def setup_logging(self):
        """Setup logging configuration for tracking scraping progress."""
        logging.basicConfig(
            filename='logs/scraper.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Also log to console
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        formatter = logging.Formatter('%(levelname)s: %(message)s')
        console.setFormatter(formatter)
        logging.getLogger().addHandler(console)

        self.logger = logging.getLogger(__name__)

    def fetch_page(self, url: str, retries: int = 3) -> Optional[BeautifulSoup]:
        """
        Fetch a webpage and return parsed BeautifulSoup object.

        Args:
            url: URL to fetch
            retries: Number of retry attempts

        Returns:
            BeautifulSoup object if successful, None if failed
        """
        for attempt in range(retries):
            try:
                self.logger.info(f"Fetching: {url} (attempt {attempt + 1})")
                response = self.session.get(url, timeout=10)

                if response.status_code == 200:
                    self.logger.info(f"Successfully fetched: {url}")
                    return BeautifulSoup(response.content, 'lxml')
                else:
                    self.logger.warning(f"HTTP {response.status_code} for {url}")

            except requests.RequestException as e:
                self.logger.error(f"Request failed for {url}: {e}")

            if attempt < retries - 1:
                wait_time = self.delay * (attempt + 1)
                self.logger.info(f"Waiting {wait_time}s before retry...")
                time.sleep(wait_time)

        self.logger.error(f"Failed to fetch {url} after {retries} attempts")
        return None

    def extract_book_data(self, soup: BeautifulSoup) -> List[Dict]:
        """
        Extract book data from a page's BeautifulSoup object.

        Args:
            soup: BeautifulSoup object of the page

        Returns:
            List of dictionaries containing book data
        """
        books = []

        # Find all book containers
        book_containers = soup.find_all('article', class_='product_pod')

        for container in book_containers:
            try:
                book_data = {}

                # Extract title
                title_elem = container.find('h3').find('a')
                book_data['title'] = title_elem['title'] if title_elem and 'title' in title_elem.attrs else title_elem.text.strip()

                # Extract price
                price_elem = container.find('p', class_='price_color')
                book_data['price'] = self.clean_price(price_elem.text.strip()) if price_elem else None

                # Extract rating
                rating_elem = container.find('p', class_='star-rating')
                book_data['rating'] = self.extract_rating(rating_elem) if rating_elem else None

                # Extract availability
                availability_elem = container.find('p', class_='instock availability')
                book_data['availability'] = availability_elem.text.strip() if availability_elem else "Unknown"

                # Extract book URL
                if title_elem and 'href' in title_elem.attrs:
                    book_data['url'] = urljoin(self.base_url, title_elem['href'])

                books.append(book_data)

            except Exception as e:
                self.logger.error(f"Error extracting book data: {e}")
                continue

        return books

    def clean_price(self, price_text: str) -> float:
        """
        Clean and convert price text to float.

        Args:
            price_text: Raw price text (e.g., "£51.77")

        Returns:
            Cleaned price as float
        """
        # Remove currency symbols and clean text
        cleaned = re.sub(r'[^\d.,]', '', price_text)
        # Handle European decimal format (comma as decimal separator)
        if ',' in cleaned and '.' in cleaned:
            # Assume last comma is decimal separator
            parts = cleaned.rsplit(',', 1)
            cleaned = parts[0].replace(',', '') + '.' + parts[1]
        elif ',' in cleaned:
            # Replace comma with dot for decimal
            cleaned = cleaned.replace(',', '.')

        try:
            return float(cleaned)
        except ValueError:
            self.logger.warning(f"Could not convert price: {price_text}")
            return 0.0

    def extract_rating(self, rating_elem) -> str:
        """
        Extract star rating from rating element.

        Args:
            rating_elem: BeautifulSoup element containing rating

        Returns:
            Rating as string (e.g., "Four", "Five")
        """
        if rating_elem:
            classes = rating_elem.get('class', [])
            for cls in classes:
                if cls in ['One', 'Two', 'Three', 'Four', 'Five']:
                    return cls
        return "No rating"

    def scrape_multiple_pages(self, start_page: int = 1, max_pages: int = 5) -> List[Dict]:
        """
        Scrape multiple pages of book listings.

        Args:
            start_page: Page number to start from
            max_pages: Maximum number of pages to scrape

        Returns:
            List of all book data from scraped pages
        """
        all_books = []

        for page_num in range(start_page, start_page + max_pages):
            if page_num == 1:
                page_url = self.base_url
            else:
                page_url = f"{self.base_url}catalogue/page-{page_num}.html"

            self.logger.info(f"Scraping page {page_num}: {page_url}")

            soup = self.fetch_page(page_url)
            if not soup:
                self.logger.warning(f"Skipping page {page_num} due to fetch failure")
                continue

            page_books = self.extract_book_data(soup)
            self.logger.info(f"Found {len(page_books)} books on page {page_num}")

            if not page_books:
                self.logger.info(f"No more books found on page {page_num}, stopping pagination")
                break

            all_books.extend(page_books)

            # Respectful delay between requests
            if page_num < start_page + max_pages - 1:
                time.sleep(self.delay)

        return all_books

    def clean_data(self, books: List[Dict]) -> pd.DataFrame:
        """
        Clean and validate scraped data.

        Args:
            books: List of book dictionaries

        Returns:
            Cleaned pandas DataFrame
        """
        df = pd.DataFrame(books)

        # Handle missing values
        df = df.fillna({
            'title': 'Unknown Title',
            'price': 0.0,
            'rating': 'No rating',
            'availability': 'Unknown',
            'url': ''
        })

        # Clean text fields
        df['title'] = df['title'].str.strip()
        df['availability'] = df['availability'].str.strip()

        # Ensure price is numeric
        df['price'] = pd.to_numeric(df['price'], errors='coerce').fillna(0.0)

        # Add metadata
        df['scraped_at'] = pd.Timestamp.now()
        df['source_url'] = self.base_url

        return df

    def save_data(self, df: pd.DataFrame, filename: str = "books_data"):
        """
        Save data to CSV and Excel formats.

        Args:
            df: DataFrame to save
            filename: Base filename (without extension)
        """
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")

        # Save to CSV
        csv_path = f"data/{filename}_{timestamp}.csv"
        df.to_csv(csv_path, index=False, encoding='utf-8')
        self.logger.info(f"Data saved to CSV: {csv_path}")

        # Save to Excel
        excel_path = f"data/{filename}_{timestamp}.xlsx"
        df.to_excel(excel_path, index=False, engine='openpyxl')
        self.logger.info(f"Data saved to Excel: {excel_path}")

        return csv_path, excel_path

    def scrape_books(self, pages: int = 1) -> Tuple[pd.DataFrame, str, str]:
        """
        Main method to scrape books and save data.

        Args:
            pages: Number of pages to scrape

        Returns:
            Tuple of (DataFrame, csv_path, excel_path)
        """
        self.logger.info(f"Starting book scraping for {pages} pages from {self.base_url}")

        # Scrape data
        books = self.scrape_multiple_pages(max_pages=pages)

        if not books:
            self.logger.error("No books found!")
            return pd.DataFrame(), "", ""

        self.logger.info(f"Total books scraped: {len(books)}")

        # Clean data
        df = self.clean_data(books)
        self.logger.info(f"Data cleaned. Shape: {df.shape}")

        # Save data
        csv_path, excel_path = self.save_data(df)

        self.logger.info("Scraping completed successfully!")
        return df, csv_path, excel_path

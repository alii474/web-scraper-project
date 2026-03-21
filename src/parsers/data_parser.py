"""
Advanced Data Parser Module

Handles parsing of HTML content with support for multiple websites,
data validation, and intelligent field extraction.
"""

import re
from typing import Dict, List, Any, Optional, Union, Callable
from urllib.parse import urljoin, urlparse
import json
from bs4 import BeautifulSoup, Tag
from dataclasses import dataclass
from datetime import datetime

from ..utils.logger import get_logger
from ..utils.config import CONFIG


@dataclass
class ParsedItem:
    """Represents a parsed data item with metadata."""
    data: Dict[str, Any]
    source_url: str
    parsed_at: datetime
    parser_version: str = "1.0"
    confidence_score: float = 1.0


class FieldExtractor:
    """Extracts specific fields from HTML elements."""
    
    def __init__(self):
        self.logger = get_logger('field_extractor')
        
        # Predefined extractors for common data types
        self.extractors = {
            'text': self._extract_text,
            'href': self._extract_href,
            'src': self._extract_src,
            'attr': self._extract_attribute,
            'price': self._extract_price,
            'rating': self._extract_rating,
            'date': self._extract_date,
            'number': self._extract_number,
            'image_url': self._extract_image_url
        }
    
    def extract_field(self, element: Tag, selector: str, extractor_type: str = 'text', **kwargs) -> Any:
        """
        Extract field from HTML element.
        
        Args:
            element: BeautifulSoup element
            selector: CSS selector
            extractor_type: Type of extraction
            **kwargs: Additional parameters
        
        Returns:
            Extracted value
        """
        try:
            # Find element using selector
            if '::' in selector:
                # Handle pseudo-selectors (e.g., 'a::attr(href)')
                base_selector, pseudo = selector.split('::')
                target_element = element.select_one(base_selector)
                
                if not target_element:
                    return None
                
                if pseudo.startswith('attr('):
                    attr_name = pseudo[5:-1]  # Extract attribute name
                    return target_element.get(attr_name)
                elif pseudo == 'text':
                    return target_element.get_text(strip=True)
                else:
                    return None
            else:
                target_element = element.select_one(selector)
                
                if not target_element:
                    return None
            
            # Use appropriate extractor
            if extractor_type in self.extractors:
                return self.extractors[extractor_type](target_element, **kwargs)
            else:
                return target_element.get_text(strip=True)
        
        except Exception as e:
            self.logger.error(f"Failed to extract field {selector}: {e}")
            return None
    
    def _extract_text(self, element: Tag, **kwargs) -> str:
        """Extract clean text from element."""
        text = element.get_text(strip=True)
        return self._clean_text(text)
    
    def _extract_href(self, element: Tag, **kwargs) -> Optional[str]:
        """Extract href attribute and make absolute URL."""
        href = element.get('href')
        if href:
            base_url = kwargs.get('base_url')
            if base_url and not href.startswith(('http://', 'https://')):
                return urljoin(base_url, href)
        return href
    
    def _extract_src(self, element: Tag, **kwargs) -> Optional[str]:
        """Extract src attribute and make absolute URL."""
        src = element.get('src')
        if src:
            base_url = kwargs.get('base_url')
            if base_url and not src.startswith(('http://', 'https://')):
                return urljoin(base_url, src)
        return src
    
    def _extract_attribute(self, element: Tag, attr_name: str, **kwargs) -> Optional[str]:
        """Extract specific attribute."""
        return element.get(attr_name)
    
    def _extract_price(self, element: Tag, **kwargs) -> Optional[float]:
        """Extract and clean price value."""
        text = element.get_text(strip=True)
        
        # Remove currency symbols and clean
        price_text = re.sub(r'[^\d.,]', '', text)
        
        # Handle different decimal formats
        if ',' in price_text and '.' in price_text:
            # Assume last comma is decimal separator
            parts = price_text.rsplit(',', 1)
            price_text = parts[0].replace(',', '') + '.' + parts[1]
        elif ',' in price_text:
            # Replace comma with dot for decimal
            price_text = price_text.replace(',', '.')
        
        try:
            return float(price_text)
        except ValueError:
            return None
    
    def _extract_rating(self, element: Tag, **kwargs) -> Optional[str]:
        """Extract rating from class or text."""
        # Check class attributes for rating
        classes = element.get('class', [])
        for cls in classes:
            if cls.lower() in ['one', 'two', 'three', 'four', 'five']:
                return cls.capitalize()
        
        # Check text content
        text = element.get_text(strip=True).lower()
        if any(word in text for word in ['one', 'two', 'three', 'four', 'five']):
            for word in ['five', 'four', 'three', 'two', 'one']:
                if word in text:
                    return word.capitalize()
        
        return None
    
    def _extract_date(self, element: Tag, **kwargs) -> Optional[datetime]:
        """Extract date from text."""
        text = element.get_text(strip=True)
        
        # Common date formats
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',
            r'\d{2}/\d{2}/\d{4}',
            r'\d{2}-\d{2}-\d{4}',
            r'\w+ \d{1,2}, \d{4}'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    date_str = match.group()
                    # Try to parse with different formats
                    for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d-%m-%Y', '%B %d, %Y']:
                        try:
                            return datetime.strptime(date_str, fmt)
                        except ValueError:
                            continue
                except Exception:
                    continue
        
        return None
    
    def _extract_number(self, element: Tag, **kwargs) -> Optional[float]:
        """Extract numeric value from text."""
        text = element.get_text(strip=True)
        match = re.search(r'[\d,.]+', text.replace(',', ''))
        if match:
            try:
                return float(match.group())
            except ValueError:
                return None
        return None
    
    def _extract_image_url(self, element: Tag, **kwargs) -> Optional[str]:
        """Extract image URL from src attribute."""
        src = element.get('src')
        if src:
            base_url = kwargs.get('base_url')
            if base_url and not src.startswith(('http://', 'https://')):
                return urljoin(base_url, src)
        return src
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s\-.,!?;:()[\]{}"\'/\\]', '', text)
        
        return text.strip()


class DataValidator:
    """Validates and normalizes parsed data."""
    
    def __init__(self):
        self.logger = get_logger('data_validator')
        
        # Validation rules for different field types
        self.validation_rules = {
            'required': lambda x: x is not None and str(x).strip() != '',
            'url': lambda x: x is None or self._is_valid_url(x),
            'email': lambda x: x is None or self._is_valid_email(x),
            'price': lambda x: x is None or (isinstance(x, (int, float)) and x >= 0),
            'rating': lambda x: x is None or x in ['One', 'Two', 'Three', 'Four', 'Five'],
            'number': lambda x: x is None or isinstance(x, (int, float))
        }
    
    def validate_item(self, item: Dict[str, Any], schema: Dict[str, List[str]]) -> Dict[str, Any]:
        """
        Validate a data item against a schema.
        
        Args:
            item: Data item to validate
            schema: Validation schema with field rules
        
        Returns:
            Validated and normalized item
        """
        validated_item = item.copy()
        errors = []
        
        for field, rules in schema.items():
            value = item.get(field)
            
            for rule in rules:
                if rule in self.validation_rules:
                    if not self.validation_rules[rule](value):
                        errors.append(f"Field '{field}' failed validation rule '{rule}'")
                        
                        # Apply default or normalization
                        if rule == 'required' and not value:
                            validated_item[field] = None
                        elif rule == 'price' and value is not None:
                            try:
                                validated_item[field] = float(str(value).replace(',', '').replace('£', '$'))
                            except ValueError:
                                validated_item[field] = 0.0
        
        if errors:
            self.logger.warning(f"Validation errors: {errors}")
        
        return validated_item
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid."""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    def _is_valid_email(self, email: str) -> bool:
        """Check if email is valid."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))


class AdvancedDataParser:
    """
    Advanced data parser with support for multiple websites,
    intelligent field extraction, and data validation.
    """
    
    def __init__(self):
        self.logger = get_logger('data_parser')
        self.field_extractor = FieldExtractor()
        self.data_validator = DataValidator()
        
        # Site-specific parsing configurations
        self.site_configs = CONFIG.SITE_PRESETS
    
    def parse_html(self, html: str, url: str, site_config: Dict[str, Any] = None) -> List[ParsedItem]:
        """
        Parse HTML content and extract data items.
        
        Args:
            html: HTML content to parse
            url: Source URL
            site_config: Site-specific configuration
        
        Returns:
            List of parsed items
        """
        try:
            soup = BeautifulSoup(html, 'lxml')
            
            # Use site config or try to detect site
            if not site_config:
                site_config = CONFIG.get_site_config(url)
            
            if not site_config:
                self.logger.warning(f"No configuration found for URL: {url}")
                return []
            
            # Find item containers
            item_selector = site_config.get('item_selector')
            if not item_selector:
                self.logger.error("No item selector in site configuration")
                return []
            
            items = soup.select(item_selector)
            self.logger.info(f"Found {len(items)} items on page: {url}")
            
            parsed_items = []
            for item_element in items:
                parsed_item = self._parse_item(item_element, url, site_config)
                if parsed_item:
                    parsed_items.append(parsed_item)
            
            return parsed_items
        
        except Exception as e:
            self.logger.log_error_with_context(e, {'url': url, 'html_length': len(html)})
            return []
    
    def _parse_item(self, element: Tag, source_url: str, site_config: Dict[str, Any]) -> Optional[ParsedItem]:
        """
        Parse a single item element.
        
        Args:
            element: HTML element for the item
            source_url: Source URL
            site_config: Site configuration
        
        Returns:
            Parsed item or None if failed
        """
        try:
            item_data = {}
            fields_config = site_config.get('fields', {})
            
            # Extract each field
            for field_name, field_config in fields_config.items():
                if isinstance(field_config, str):
                    selector = field_config
                    extractor_type = 'text'
                elif isinstance(field_config, dict):
                    selector = field_config.get('selector')
                    extractor_type = field_config.get('type', 'text')
                else:
                    continue
                
                value = self.field_extractor.extract_field(
                    element, selector, extractor_type, base_url=source_url
                )
                item_data[field_name] = value
            
            # Validate data if enabled
            if CONFIG.VALIDATE_DATA:
                schema = self._create_validation_schema(site_config)
                item_data = self.data_validator.validate_item(item_data, schema)
            
            # Create parsed item
            parsed_item = ParsedItem(
                data=item_data,
                source_url=source_url,
                parsed_at=datetime.now(),
                confidence_score=self._calculate_confidence_score(item_data)
            )
            
            return parsed_item
        
        except Exception as e:
            self.logger.error(f"Failed to parse item: {e}")
            return None
    
    def _create_validation_schema(self, site_config: Dict[str, Any]) -> Dict[str, List[str]]:
        """Create validation schema from site configuration."""
        schema = {}
        fields_config = site_config.get('fields', {})
        
        for field_name, field_config in fields_config.items():
            rules = []
            
            # Add rules based on field name
            if 'url' in field_name.lower():
                rules.append('url')
            elif 'price' in field_name.lower():
                rules.extend(['required', 'price'])
            elif 'rating' in field_name.lower():
                rules.append('rating')
            elif 'email' in field_name.lower():
                rules.append('email')
            elif field_name in ['title', 'name']:
                rules.append('required')
            
            schema[field_name] = rules
        
        return schema
    
    def _calculate_confidence_score(self, item_data: Dict[str, Any]) -> float:
        """
        Calculate confidence score for parsed item based on data completeness.
        
        Args:
            item_data: Parsed item data
        
        Returns:
            Confidence score between 0 and 1
        """
        if not item_data:
            return 0.0
        
        # Count non-null fields
        non_null_fields = sum(1 for value in item_data.values() if value is not None and str(value).strip())
        total_fields = len(item_data)
        
        if total_fields == 0:
            return 0.0
        
        return non_null_fields / total_fields
    
    def parse_multiple_pages(self, html_pages: List[str], urls: List[str], 
                           site_config: Dict[str, Any] = None) -> List[ParsedItem]:
        """
        Parse multiple HTML pages.
        
        Args:
            html_pages: List of HTML contents
            urls: List of corresponding URLs
            site_config: Site configuration
        
        Returns:
            List of all parsed items
        """
        all_items = []
        
        for html, url in zip(html_pages, urls):
            items = self.parse_html(html, url, site_config)
            all_items.extend(items)
        
        return all_items
    
    def get_supported_sites(self) -> List[str]:
        """Get list of supported sites."""
        return list(self.site_configs.keys())
    
    def add_site_config(self, domain: str, config: Dict[str, Any]):
        """
        Add new site configuration.
        
        Args:
            domain: Domain name
            config: Site configuration
        """
        self.site_configs[domain] = config
        self.logger.info(f"Added configuration for site: {domain}")

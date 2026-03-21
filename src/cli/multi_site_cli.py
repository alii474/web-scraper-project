"""
Multi-Site Scraper CLI

Command-line interface for the multi-site web scraper.
Supports scraping multiple websites with automatic detection and data normalization.
"""

import argparse
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

from ..core.multi_site_scraper import MultiSiteScraper
from ..utils.logger import get_logger
from ..storage.advanced_storage import AdvancedStorageManager
from ..utils.visualization import DataVisualizer


class MultiSiteScraperCLI:
    """
    Command-line interface for the multi-site web scraper.
    
    Features:
    - Multi-site scraping with automatic detection
    - Data normalization and combination
    - Flexible output formats
    - Statistics and reporting
    """
    
    def __init__(self):
        self.logger = get_logger('multi_site_cli')
        self.storage = AdvancedStorageManager()
        self.visualizer = DataVisualizer()
    
    def create_parser(self) -> argparse.ArgumentParser:
        """Create the argument parser."""
        parser = argparse.ArgumentParser(
            description="Multi-Site Web Scraper - Extract data from multiple websites",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Scrape single URL
  python multi_site_scraper.py --url "http://books.toscrape.com/"
  
  # Scrape multiple URLs from file
  python multi_site_scraper.py --file urls.txt --max-pages 3
  
  # Scrape specific websites
  python multi_site_scraper.py --sites books.toscrape.com,quotes.toscrape.com
  
  # Normalize and combine data
  python multi_site_scraper.py --file urls.txt --normalize --output combined_data
  
  # Generate statistics
  python multi_site_scraper.py --stats --config config.json
            """
        )
        
        # Input options
        input_group = parser.add_mutually_exclusive_group()
        input_group.add_argument('--url', type=str, help='Single URL to scrape')
        input_group.add_argument('--file', type=str, help='File containing URLs (one per line)')
        input_group.add_argument('--sites', type=str, help='Comma-separated list of sites to scrape')
        input_group.add_argument('--stats', action='store_true', help='Show statistics only')
        
        # Add --list-sites as a separate option (not in the mutually exclusive group)
        parser.add_argument('--list-sites', action='store_true', 
                          help='List all configured websites')
        
        # Scraping options
        parser.add_argument('--max-pages', type=int, default=3, 
                          help='Maximum pages to scrape per URL (default: 3)')
        parser.add_argument('--delay', type=float, default=1.0, 
                          help='Delay between requests in seconds (default: 1.0)')
        parser.add_argument('--timeout', type=int, default=30, 
                          help='Request timeout in seconds (default: 30)')
        
        # Output options
        parser.add_argument('--output', type=str, help='Output filename prefix')
        parser.add_argument('--formats', nargs='+', 
                          choices=['csv', 'excel', 'json', 'sqlite'], 
                          default=['csv', 'excel'], help='Output formats')
        parser.add_argument('--normalize', action='store_true', 
                          help='Normalize data to common format')
        parser.add_argument('--combine', action='store_true', 
                          help='Combine all data into single dataset')
        
        # Configuration
        parser.add_argument('--config', type=str, default='config.json', 
                          help='Configuration file path')
        
        # Visualization
        parser.add_argument('--visualize', action='store_true', 
                          help='Generate data visualizations')
        
        return parser
    
    def load_urls_from_file(self, file_path: str) -> List[str]:
        """Load URLs from file."""
        try:
            path = Path(file_path)
            if not path.exists():
                self.logger.error(f"File not found: {file_path}")
                return []
            
            with open(path, 'r', encoding='utf-8') as f:
                urls = [line.strip() for line in f 
                       if line.strip() and not line.startswith('#')]
            
            self.logger.info(f"Loaded {len(urls)} URLs from {file_path}")
            return urls
        
        except Exception as e:
            self.logger.error(f"Failed to load URLs from file: {e}")
            return []
    
    def scrape_single_url(self, scraper: MultiSiteScraper, url: str, max_pages: int) -> List[Dict[str, Any]]:
        """Scrape a single URL."""
        self.logger.info(f"Scraping URL: {url}")
        
        try:
            results = scraper.scrape_url(url, max_pages)
            
            if results:
                self.logger.info(f"Successfully scraped {len(results)} items from {url}")
            else:
                self.logger.warning(f"No items scraped from {url}")
            
            return results
        
        except Exception as e:
            self.logger.error(f"Failed to scrape {url}: {e}")
            return []
    
    def scrape_multiple_urls(self, scraper: MultiSiteScraper, urls: List[str], max_pages: int) -> Dict[str, List[Dict[str, Any]]]:
        """Scrape multiple URLs."""
        self.logger.info(f"Scraping {len(urls)} URLs")
        
        try:
            results = scraper.scrape_multiple_urls(urls, max_pages)
            
            total_items = sum(len(items) for items in results.values())
            self.logger.info(f"Successfully scraped {total_items} items from {len(results)} websites")
            
            return results
        
        except Exception as e:
            self.logger.error(f"Failed to scrape multiple URLs: {e}")
            return {}
    
    def scrape_specific_sites(self, scraper: MultiSiteScraper, sites: List[str], max_pages: int) -> Dict[str, List[Dict[str, Any]]]:
        """Scrape specific websites."""
        self.logger.info(f"Scraping {len(sites)} specific websites")
        
        results = {}
        
        for site in sites:
            try:
                # Get base URL from config
                config = scraper.config['websites'].get(site)
                if not config:
                    self.logger.warning(f"Site not found in config: {site}")
                    continue
                
                base_url = config['base_url']
                self.logger.info(f"Scraping site: {site} ({base_url})")
                
                site_results = scraper.scrape_url(base_url, max_pages)
                results[site] = site_results
                
                self.logger.info(f"Scraped {len(site_results)} items from {site}")
                
                # Add delay between sites
                import time
                time.sleep(2)
            
            except Exception as e:
                self.logger.error(f"Failed to scrape site {site}: {e}")
        
        return results
    
    def normalize_and_combine_data(self, results: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Normalize and combine data from multiple sites."""
        all_data = []
        
        for site, items in results.items():
            if items:
                # Add site info to each item
                for item in items:
                    item['source_site'] = site
                    item['scraped_at'] = datetime.now().isoformat()
                
                all_data.extend(items)
        
        if not all_data:
            return []
        
        # Normalize data
        scraper = MultiSiteScraper()
        normalized_data = scraper.normalize_data(all_data)
        
        self.logger.info(f"Normalized {len(normalized_data)} items from {len(results)} sites")
        return normalized_data
    
    def save_results(self, results: Dict[str, List[Dict[str, Any]]] or List[Dict[str, Any]], 
                    output_prefix: str, formats: List[str], normalize: bool = False):
        """Save results to files."""
        if isinstance(results, dict):
            # Multiple sites - save separately or combined
            if normalize:
                # Normalize and combine
                combined_data = self.normalize_and_combine_data(results)
                self._save_data(combined_data, output_prefix, formats)
            else:
                # Save each site separately
                for site, items in results.items():
                    if items:
                        site_prefix = f"{output_prefix}_{site}"
                        self._save_data(items, site_prefix, formats)
        else:
            # Single list of items
            self._save_data(results, output_prefix, formats)
    
    def _save_data(self, data: List[Dict[str, Any]], prefix: str, formats: List[str]):
        """Save data to specified formats."""
        if not data:
            self.logger.warning("No data to save")
            return
        
        try:
            # Convert to storage format
            from ..parsers.data_parser import ParsedItem
            parsed_items = []
            
            for item in data:
                parsed_item = ParsedItem(
                    data=item,
                    source_url=item.get('url', ''),
                    parsed_at=datetime.now(),
                    confidence_score=1.0
                )
                parsed_items.append(parsed_item)
            
            # Save using storage manager
            storage_results = self.storage.save_items(parsed_items, formats, prefix)
            
            if storage_results['saved_files']:
                self.logger.info(f"Data saved to {len(storage_results['saved_files'])} files:")
                for file_path in storage_results['saved_files']:
                    self.logger.info(f"  - {file_path}")
        
        except Exception as e:
            self.logger.error(f"Failed to save data: {e}")
    
    def generate_visualizations(self, data: List[Dict[str, Any]], output_prefix: str):
        """Generate data visualizations."""
        if not data:
            self.logger.warning("No data available for visualization")
            return
        
        try:
            import pandas as pd
            
            # Convert to DataFrame
            df = pd.DataFrame(data)
            
            if df.empty:
                self.logger.warning("Empty DataFrame for visualization")
                return
            
            # Create visualization
            viz_file = self.visualizer.create_comprehensive_analysis(
                df, 
                f"{output_prefix}_visualization"
            )
            
            self.logger.info(f"Visualization saved: {viz_file}")
        
        except Exception as e:
            self.logger.error(f"Failed to generate visualizations: {e}")
    
    def show_statistics(self, scraper: MultiSiteScraper):
        """Show scraping statistics."""
        stats = scraper.get_statistics()
        
        print("\n📊 MULTI-SITE SCRAPER STATISTICS:")
        print(f"  Total Items Scraped: {stats['total_scraped']}")
        print(f"  Sites Scraped: {len(stats['sites_scraped'])}")
        print(f"  Errors: {stats['errors']}")
        print(f"  Runtime: {stats['runtime_seconds']:.1f} seconds")
        print(f"  Success Rate: {stats['success_rate']:.1f}%")
        
        if stats['sites_scraped']:
            print(f"\n📈 BY WEBSITE:")
            for site, count in stats['sites_scraped'].items():
                print(f"  {site}: {count} items")
    
    def list_configured_sites(self, scraper: MultiSiteScraper):
        """List all configured websites."""
        websites = scraper.config.get('websites', {})
        
        print("\n🌐 CONFIGURED WEBSITES:")
        for site_key, config in websites.items():
            print(f"  {site_key}:")
            print(f"    Name: {config.get('name', 'Unknown')}")
            print(f"    Category: {config.get('category', 'Unknown')}")
            print(f"    Base URL: {config.get('base_url', 'N/A')}")
            print(f"    Max Pages: {config.get('pagination', {}).get('max_pages', 'N/A')}")
            print()
    
    def run(self, args: List[str] = None) -> int:
        """Run the CLI application."""
        parser = self.create_parser()
        parsed_args = parser.parse_args(args)
        
        try:
            # Initialize scraper
            scraper = MultiSiteScraper(parsed_args.config)
            
            if not scraper.config:
                self.logger.error("Failed to load configuration")
                return 1
            
            # List sites if requested
            if parsed_args.list_sites:
                self.list_configured_sites(scraper)
                return 0
            
            # Show statistics if requested
            if parsed_args.stats:
                self.show_statistics(scraper)
                return 0
            
            # Check if we have any scraping input
            if not any([parsed_args.url, parsed_args.file, parsed_args.sites]):
                print("❌ Please specify --url, --file, or --sites to start scraping")
                parser.print_help()
                return 1
            
            # Generate output prefix
            if not parsed_args.output:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_prefix = f"multi_site_scrape_{timestamp}"
            else:
                output_prefix = parsed_args.output
            
            # Scrape based on input type
            results = {}
            
            if parsed_args.url:
                # Single URL
                results = self.scrape_single_url(scraper, parsed_args.url, parsed_args.max_pages)
            
            elif parsed_args.file:
                # Multiple URLs from file
                urls = self.load_urls_from_file(parsed_args.file)
                if urls:
                    results = self.scrape_multiple_urls(scraper, urls, parsed_args.max_pages)
            
            elif parsed_args.sites:
                # Specific websites
                sites = [site.strip() for site in parsed_args.sites.split(',')]
                results = self.scrape_specific_sites(scraper, sites, parsed_args.max_pages)
            
            # Save results
            if results:
                if isinstance(results, list):
                    # Single list of results
                    self.save_results(results, output_prefix, parsed_args.formats, parsed_args.normalize)
                    
                    # Generate visualizations if requested
                    if parsed_args.visualize:
                        self.generate_visualizations(results, output_prefix)
                else:
                    # Dictionary of results by site
                    self.save_results(results, output_prefix, parsed_args.formats, parsed_args.normalize)
                    
                    # Generate visualizations for combined data
                    if parsed_args.visualize and parsed_args.normalize:
                        combined_data = self.normalize_and_combine_data(results)
                        self.generate_visualizations(combined_data, output_prefix)
                
                # Show final statistics
                self.show_statistics(scraper)
                
                print(f"\n✅ Scraping completed successfully!")
                print(f"📁 Output prefix: {output_prefix}")
                print(f"📊 Formats: {', '.join(parsed_args.formats)}")
                
            else:
                print("❌ No data was scraped")
                return 1
            
            return 0
        
        except KeyboardInterrupt:
            print("\n⏹️  Scraping stopped by user")
            return 130
        except Exception as e:
            self.logger.error(f"Scraping failed: {e}")
            print(f"\n❌ Error: {e}")
            return 1


def main():
    """Main entry point for the multi-site scraper CLI."""
    cli = MultiSiteScraperCLI()
    exit_code = cli.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

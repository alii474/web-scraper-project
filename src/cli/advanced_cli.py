"""
Advanced CLI Interface for Web Scraper

Professional command-line interface with argparse, comprehensive options,
and intelligent argument handling.
"""

import argparse
import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import time
from datetime import datetime

from ..core.scraper import AdvancedWebScraper
from ..utils.logger import get_logger, setup_logging
from ..utils.config import CONFIG
from ..utils.visualization import DataVisualizer


class ScraperCLI:
    """
    Advanced command-line interface for the web scraper.
    
    Features:
    - Comprehensive argument parsing
    - Progress reporting
    - Error handling
    - Multiple output formats
    - Scheduling support
    """
    
    def __init__(self):
        self.logger = get_logger('cli')
        self.visualizer = DataVisualizer()
        
    def create_parser(self) -> argparse.ArgumentParser:
        """Create the argument parser with all options."""
        parser = argparse.ArgumentParser(
            description="Advanced Web Scraper - Production-level scraping tool",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Basic scraping
  python main.py http://books.toscrape.com/
  
  # Advanced scraping with options
  python main.py http://books.toscrape.com/ --pages 5 --formats csv excel json
  
  # Use Selenium for dynamic content
  python main.py https://example.com --selenium --headless
  
  # Schedule scraping every 30 minutes
  python main.py http://books.toscrape.com/ --schedule 30
  
  # Scrape multiple URLs
  python main.py url1.txt url2.txt --batch --concurrent
  
  # Custom configuration
  python main.py http://books.toscrape.com/ --config custom.json --output my_data
            """
        )
        
        # Positional arguments
        parser.add_argument(
            'url',
            nargs='?',
            help='URL to scrape or file containing URLs'
        )
        
        # Core scraping options
        core_group = parser.add_argument_group('Core Scraping Options')
        core_group.add_argument(
            '--pages', '-p',
            type=int,
            default=CONFIG.DEFAULT_MAX_PAGES,
            help=f'Number of pages to scrape (default: {CONFIG.DEFAULT_MAX_PAGES})'
        )
        core_group.add_argument(
            '--formats', '-f',
            nargs='+',
            choices=['csv', 'excel', 'json', 'sqlite'],
            default=CONFIG.DEFAULT_FORMATS,
            help='Output formats (default: csv excel)'
        )
        core_group.add_argument(
            '--output', '-o',
            type=str,
            help='Custom output filename (without extension)'
        )
        core_group.add_argument(
            '--no-dedup',
            action='store_true',
            help='Disable duplicate removal'
        )
        
        # Advanced options
        advanced_group = parser.add_argument_group('Advanced Options')
        advanced_group.add_argument(
            '--selenium',
            action='store_true',
            help='Force use of Selenium WebDriver'
        )
        advanced_group.add_argument(
            '--no-selenium',
            action='store_true',
            help='Disable Selenium WebDriver'
        )
        advanced_group.add_argument(
            '--headless',
            action='store_true',
            default=CONFIG.SELENIUM_HEADLESS,
            help='Run Selenium in headless mode'
        )
        advanced_group.add_argument(
            '--concurrent',
            action='store_true',
            help='Enable concurrent scraping'
        )
        advanced_group.add_argument(
            '--rate-limit',
            type=float,
            default=1.0,
            help='Rate limiting delay between requests (seconds)'
        )
        advanced_group.add_argument(
            '--timeout',
            type=int,
            default=CONFIG.DEFAULT_TIMEOUT,
            help='Request timeout (seconds)'
        )
        
        # Proxy and authentication
        proxy_group = parser.add_argument_group('Proxy & Authentication')
        proxy_group.add_argument(
            '--proxy',
            type=str,
            help='Proxy URL (e.g., http://proxy:port)'
        )
        proxy_group.add_argument(
            '--proxy-file',
            type=str,
            help='File containing list of proxies'
        )
        proxy_group.add_argument(
            '--user-agent',
            type=str,
            help='Custom user agent string'
        )
        proxy_group.add_argument(
            '--headers',
            type=str,
            help='JSON file containing custom headers'
        )
        
        # Scheduling options
        schedule_group = parser.add_argument_group('Scheduling')
        schedule_group.add_argument(
            '--schedule',
            type=int,
            help='Schedule scraping every X minutes'
        )
        schedule_group.add_argument(
            '--max-runs',
            type=int,
            help='Maximum number of scheduled runs (default: infinite)'
        )
        
        # Batch processing
        batch_group = parser.add_argument_group('Batch Processing')
        batch_group.add_argument(
            '--batch',
            action='store_true',
            help='Treat URL as file containing multiple URLs'
        )
        batch_group.add_argument(
            '--batch-delay',
            type=float,
            default=5.0,
            help='Delay between batch URLs (seconds)'
        )
        
        # Visualization and analysis
        viz_group = parser.add_argument_group('Visualization & Analysis')
        viz_group.add_argument(
            '--visualize', '-v',
            action='store_true',
            help='Generate data visualizations'
        )
        viz_group.add_argument(
            '--stats',
            action='store_true',
            help='Show detailed statistics'
        )
        viz_group.add_argument(
            '--sample',
            type=int,
            default=5,
            help='Number of sample items to display (default: 5)'
        )
        
        # Configuration
        config_group = parser.add_argument_group('Configuration')
        config_group.add_argument(
            '--config',
            type=str,
            help='Path to configuration JSON file'
        )
        config_group.add_argument(
            '--save-config',
            type=str,
            help='Save current configuration to file'
        )
        
        # Logging options
        log_group = parser.add_argument_group('Logging')
        log_group.add_argument(
            '--log-level',
            choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
            default=CONFIG.LOG_LEVEL,
            help='Logging level (default: INFO)'
        )
        log_group.add_argument(
            '--log-file',
            type=str,
            help='Custom log file path'
        )
        log_group.add_argument(
            '--quiet', '-q',
            action='store_true',
            help='Suppress console output'
        )
        log_group.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose logging'
        )
        
        return parser
    
    def load_urls_from_file(self, file_path: str) -> List[str]:
        """
        Load URLs from file.
        
        Args:
            file_path: Path to file containing URLs
        
        Returns:
            List of URLs
        """
        try:
            path = Path(file_path)
            if not path.exists():
                self.logger.error(f"URL file not found: {file_path}")
                return []
            
            with open(path, 'r', encoding='utf-8') as f:
                urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            
            self.logger.info(f"Loaded {len(urls)} URLs from {file_path}")
            return urls
        
        except Exception as e:
            self.logger.error(f"Failed to load URLs from file: {e}")
            return []
    
    def load_config(self, config_path: str) -> Dict[str, Any]:
        """
        Load configuration from JSON file.
        
        Args:
            config_path: Path to configuration file
        
        Returns:
            Configuration dictionary
        """
        try:
            path = Path(config_path)
            if not path.exists():
                self.logger.warning(f"Config file not found: {config_path}")
                return {}
            
            with open(path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            self.logger.info(f"Loaded configuration from {config_path}")
            return config
        
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            return {}
    
    def save_config(self, config_path: str, args: argparse.Namespace):
        """
        Save current configuration to JSON file.
        
        Args:
            config_path: Path to save configuration
            args: Parsed arguments
        """
        try:
            config = {
                'pages': args.pages,
                'formats': args.formats,
                'output': args.output,
                'no_dedup': args.no_dedup,
                'selenium': args.selenium,
                'no_selenium': args.no_selenium,
                'headless': args.headless,
                'concurrent': args.concurrent,
                'rate_limit': args.rate_limit,
                'timeout': args.timeout,
                'proxy': args.proxy,
                'user_agent': args.user_agent,
                'schedule': args.schedule,
                'batch': args.batch,
                'visualize': args.visualize,
                'stats': args.stats,
                'log_level': args.log_level,
                'saved_at': datetime.now().isoformat()
            }
            
            path = Path(config_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            
            self.logger.info(f"Configuration saved to {config_path}")
        
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
    
    def display_results(self, result: Dict[str, Any], args: argparse.Namespace):
        """
        Display scraping results.
        
        Args:
            result: Scraping result
            args: Command-line arguments
        """
        print("\n" + "="*60)
        print("🔥 SCRAPING RESULTS")
        print("="*60)
        
        print(f"📍 URL: {result['url']}")
        print(f"📄 Pages scraped: {result['pages_scraped']}")
        print(f"📦 Items scraped: {result['items_scraped']}")
        
        if result.get('duplicates_removed', 0) > 0:
            print(f"🗑️  Duplicates removed: {result['duplicates_removed']}")
        
        print(f"⏱️  Processing time: {result['processing_time']:.2f}s")
        
        if result.get('selenium_used', 0) > 0:
            print(f"🌐 Selenium requests: {result['selenium_used']}")
        
        if result.get('requests_used', 0) > 0:
            print(f"📡 HTTP requests: {result['requests_used']}")
        
        if result['saved_files']:
            print(f"\n💾 Saved files:")
            for file_path in result['saved_files']:
                print(f"   📄 {file_path}")
        
        # Display sample items
        if args.sample > 0 and result.get('items'):
            print(f"\n📋 Sample items (first {args.sample}):")
            for i, item in enumerate(result['items'][:args.sample]):
                print(f"\n  {i+1}. {item.data.get('title', 'N/A')}")
                if 'price' in item.data:
                    print(f"     💰 Price: {item.data['price']}")
                if 'rating' in item.data:
                    print(f"     ⭐ Rating: {item.data['rating']}")
                print(f"     🔗 URL: {item.source_url}")
        
        # Display detailed statistics
        if args.stats and 'stats' in result:
            stats = result['stats']
            print(f"\n📊 Detailed Statistics:")
            print(f"   Items per second: {stats.get('items_per_second', 0):.2f}")
            print(f"   Success rate: {stats.get('success_rate', 0):.2%}")
            print(f"   Retries: {stats.get('retries', 0)}")
            print(f"   Errors: {stats.get('errors', 0)}")
    
    def run_scheduled_scraping(self, args: argparse.Namespace):
        """
        Run scraping on schedule.
        
        Args:
            args: Parsed arguments
        """
        interval_minutes = args.schedule
        max_runs = args.max_runs or float('inf')
        
        print(f"🕐 Starting scheduled scraping every {interval_minutes} minutes")
        print(f"🔄 Maximum runs: {'Unlimited' if max_runs == float('inf') else max_runs}")
        
        run_count = 0
        
        try:
            while run_count < max_runs:
                run_count += 1
                print(f"\n🚀 Scheduled run #{run_count}")
                
                try:
                    result = self.run_single_scrape(args)
                    self.display_results(result, args)
                except Exception as e:
                    self.logger.error(f"Scheduled run #{run_count} failed: {e}")
                
                if run_count < max_runs:
                    print(f"\n⏳ Next run in {interval_minutes} minutes...")
                    time.sleep(interval_minutes * 60)
        
        except KeyboardInterrupt:
            print(f"\n⏹️  Scheduled scraping stopped by user after {run_count} runs")
        except Exception as e:
            self.logger.error(f"Scheduled scraping failed: {e}")
    
    def run_single_scrape(self, args: argparse.Namespace) -> Dict[str, Any]:
        """
        Run a single scraping operation.
        
        Args:
            args: Parsed arguments
        
        Returns:
            Scraping result
        """
        # Initialize scraper
        scraper = AdvancedWebScraper(
            use_selenium=args.selenium if args.selenium else (False if args.no_selenium else None),
            max_pages=args.pages,
            concurrent=args.concurrent,
            rate_limit=args.rate_limit
        )
        
        try:
            if args.batch:
                # Batch processing
                urls = self.load_urls_from_file(args.url)
                if not urls:
                    raise ValueError("No URLs loaded from batch file")
                
                results = []
                for i, url in enumerate(urls):
                    print(f"\n📄 Scraping URL {i+1}/{len(urls)}: {url}")
                    
                    result = scraper.scrape_url(
                        url,
                        max_pages=args.pages,
                        formats=args.formats,
                        output_filename=args.output
                    )
                    results.append(result)
                    
                    # Delay between batch URLs
                    if i < len(urls) - 1:
                        time.sleep(args.batch_delay)
                
                # Combine results
                combined_result = {
                    'url': f"Batch: {len(urls)} URLs",
                    'pages_scraped': sum(r['pages_scraped'] for r in results),
                    'items_scraped': sum(r['items_scraped'] for r in results),
                    'processing_time': sum(r['processing_time'] for r in results),
                    'saved_files': [f for r in results for f in r['saved_files']],
                    'formats_used': args.formats,
                    'items': [item for r in results for item in r['items'][:2]]
                }
                
                return combined_result
            else:
                # Single URL scraping
                return scraper.scrape_url(
                    args.url,
                    max_pages=args.pages,
                    formats=args.formats,
                    output_filename=args.output
                )
        
        finally:
            scraper.close()
    
    def run(self, args: List[str] = None) -> int:
        """
        Run the CLI application.
        
        Args:
            args: Command-line arguments (None for sys.argv)
        
        Returns:
            Exit code
        """
        parser = self.create_parser()
        parsed_args = parser.parse_args(args)
        
        # Setup logging
        log_level = 'DEBUG' if parsed_args.verbose else parsed_args.log_level
        setup_logging(log_level, parsed_args.log_file)
        
        if parsed_args.quiet:
            # Suppress console output
            logger = get_logger()
            logger.logger.handlers[0].setLevel(logging.CRITICAL)
        
        # Load configuration if specified
        if parsed_args.config:
            config = self.load_config(parsed_args.config)
            # Update args with config values
            for key, value in config.items():
                if hasattr(parsed_args, key) and getattr(parsed_args, key) is None:
                    setattr(parsed_args, key, value)
        
        # Save configuration if requested
        if parsed_args.save_config:
            self.save_config(parsed_args.save_config, parsed_args)
            return 0
        
        # Validate arguments
        if not parsed_args.url:
            parser.error("URL is required")
        
        # Display banner
        print("🔥 ADVANCED WEB SCRAPER")
        print("=" * 40)
        print(f"🎯 Target: {parsed_args.url}")
        print(f"📄 Pages: {parsed_args.pages}")
        print(f"💾 Formats: {', '.join(parsed_args.formats)}")
        print(f"🌐 Selenium: {'Enabled' if parsed_args.selenium else 'Auto-detect'}")
        print(f"⚡ Concurrent: {'Enabled' if parsed_args.concurrent else 'Disabled'}")
        print("-" * 40)
        
        try:
            # Run scraping
            if parsed_args.schedule:
                self.run_scheduled_scraping(parsed_args)
            else:
                result = self.run_single_scrape(parsed_args)
                self.display_results(result, parsed_args)
                
                # Generate visualizations if requested
                if parsed_args.visualize and result.get('items'):
                    print(f"\n🎨 Generating visualizations...")
                    # Convert ParsedItem to DataFrame for visualization
                    import pandas as pd
                    items_data = [item.data for item in result['items']]
                    df = pd.DataFrame(items_data)
                    
                    if not df.empty:
                        viz_file = self.visualizer.create_comprehensive_analysis(
                            df, 
                            parsed_args.output or 'scraped_data'
                        )
                        print(f"📊 Visualization saved: {viz_file}")
            
            return 0
        
        except KeyboardInterrupt:
            print("\n⏹️  Scraping interrupted by user")
            return 130
        except Exception as e:
            self.logger.error(f"Scraping failed: {e}")
            print(f"\n❌ Error: {e}")
            return 1


def main():
    """Main entry point for the CLI application."""
    cli = ScraperCLI()
    exit_code = cli.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

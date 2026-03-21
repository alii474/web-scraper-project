"""
E-commerce Price Tracker CLI

Command-line interface for the price tracking system.
Provides commands for tracking products, monitoring prices, and managing alerts.
"""

import argparse
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any

from ..core.price_tracker_engine import PriceTrackerEngine
from ..utils.logger import get_logger, setup_logging
from ..utils.price_tracker_config import CONFIG
from ..storage.advanced_storage import AdvancedStorageManager
from ..utils.visualization import DataVisualizer


class PriceTrackerCLI:
    """
    Command-line interface for the E-commerce Price Tracker.
    
    Features:
    - Product tracking commands
    - Price monitoring
    - Alert management
    - Data export
    - Visualization
    """
    
    def __init__(self):
        self.logger = get_logger('price_tracker_cli')
        self.visualizer = DataVisualizer()
        self.storage = AdvancedStorageManager()
        
    def create_parser(self) -> argparse.ArgumentParser:
        """Create the argument parser."""
        parser = argparse.ArgumentParser(
            description="E-commerce Price Tracker - Monitor product prices and get alerts",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Track single product
  python price_tracker.py track --url "https://www.amazon.com/dp/B08N5WRWNW"
  
  # Track multiple products from file
  python price_tracker.py track --file products.txt --site amazon
  
  # Monitor prices continuously
  python price_tracker.py monitor --interval 3600 --file products.txt
  
  # Get price alerts
  python price_tracker.py alerts --type price --limit 10
  
  # View price history
  python price_tracker.py history --product-id "abc123" --days 30
  
  # Export data
  python price_tracker.py export --format csv --output prices.csv
            """
        )
        
        subparsers = parser.add_subparsers(dest='command', help='Available commands')
        
        # Track command
        track_parser = subparsers.add_parser('track', help='Track product prices')
        track_parser.add_argument('--url', type=str, help='Product URL to track')
        track_parser.add_argument('--file', type=str, help='File containing product URLs')
        track_parser.add_argument('--site', type=str, help='E-commerce site (amazon, ebay, etc.)')
        track_parser.add_argument('--output', type=str, help='Output file prefix')
        track_parser.add_argument('--formats', nargs='+', choices=['csv', 'excel', 'json', 'sqlite'], 
                                 default=['csv', 'excel'], help='Output formats')
        
        # Monitor command
        monitor_parser = subparsers.add_parser('monitor', help='Monitor prices continuously')
        monitor_parser.add_argument('--file', type=str, required=True, help='File containing product URLs')
        monitor_parser.add_argument('--site', type=str, help='E-commerce site')
        monitor_parser.add_argument('--interval', type=int, default=3600, help='Check interval in seconds')
        monitor_parser.add_argument('--duration', type=int, help='Monitoring duration in hours')
        monitor_parser.add_argument('--alerts', action='store_true', help='Enable price alerts')
        
        # Alerts command
        alerts_parser = subparsers.add_parser('alerts', help='View price and availability alerts')
        alerts_parser.add_argument('--type', choices=['price', 'availability', 'all'], 
                                  default='all', help='Alert type to show')
        alerts_parser.add_argument('--limit', type=int, default=20, help='Number of alerts to show')
        alerts_parser.add_argument('--export', type=str, help='Export alerts to file')
        
        # History command
        history_parser = subparsers.add_parser('history', help='View price history')
        history_parser.add_argument('--product-id', type=str, help='Product ID')
        history_parser.add_argument('--days', type=int, default=30, help='Number of days to analyze')
        history_parser.add_argument('--trends', action='store_true', help='Show price trends')
        
        # Export command
        export_parser = subparsers.add_parser('export', help='Export tracking data')
        export_parser.add_argument('--format', choices=['csv', 'excel', 'json'], 
                                  default='csv', help='Export format')
        export_parser.add_argument('--output', type=str, help='Output filename')
        export_parser.add_argument('--days', type=int, default=30, help='Days of data to export')
        
        # Stats command
        stats_parser = subparsers.add_parser('stats', help='Show tracking statistics')
        stats_parser.add_argument('--detailed', action='store_true', help='Show detailed statistics')
        
        # Demo command
        demo_parser = subparsers.add_parser('demo', help='Run demo with sample products')
        demo_parser.add_argument('--site', type=str, default='books.toscrape.com', help='Demo site')
        demo_parser.add_argument('--pages', type=int, default=2, help='Number of pages to scrape')
        demo_parser.add_argument('--visualize', action='store_true', help='Generate visualizations')
        
        return parser
    
    def load_urls_from_file(self, file_path: str) -> List[str]:
        """Load URLs from file."""
        try:
            path = Path(file_path)
            if not path.exists():
                self.logger.error(f"File not found: {file_path}")
                return []
            
            with open(path, 'r', encoding='utf-8') as f:
                urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            
            self.logger.info(f"Loaded {len(urls)} URLs from {file_path}")
            return urls
        
        except Exception as e:
            self.logger.error(f"Failed to load URLs from file: {e}")
            return []
    
    def track_command(self, args):
        """Execute track command."""
        urls = []
        
        if args.url:
            urls = [args.url]
        elif args.file:
            urls = self.load_urls_from_file(args.file)
        else:
            self.logger.error("Either --url or --file must be specified")
            return
        
        if not urls:
            self.logger.error("No URLs to track")
            return
        
        # Initialize tracker
        tracker = PriceTrackerEngine()
        
        try:
            # Track products
            self.logger.info(f"Tracking {len(urls)} product(s)...")
            results = tracker.track_products(urls, args.site)
            
            if not results:
                self.logger.warning("No product data retrieved")
                return
            
            # Display results
            self.display_tracking_results(results)
            
            # Save data
            if args.formats:
                self.save_tracking_data(results, args.formats, args.output)
            
            # Show alerts
            alerts = tracker.get_price_alerts()
            if alerts:
                self.display_alerts(alerts[:5])
            
            # Show statistics
            stats = tracker.get_tracker_stats()
            self.display_stats(stats)
        
        except Exception as e:
            self.logger.error(f"Tracking failed: {e}")
    
    def monitor_command(self, args):
        """Execute monitor command."""
        urls = self.load_urls_from_file(args.file)
        
        if not urls:
            self.logger.error("No URLs to monitor")
            return
        
        # Initialize tracker
        tracker = PriceTrackerEngine()
        
        self.logger.info(f"Starting continuous monitoring of {len(urls)} products")
        self.logger.info(f"Check interval: {args.interval} seconds")
        
        if args.duration:
            self.logger.info(f"Monitoring duration: {args.duration} hours")
            end_time = datetime.now() + timedelta(hours=args.duration)
        else:
            end_time = None
        
        try:
            check_count = 0
            while True:
                check_count += 1
                self.logger.info(f"Check #{check_count} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Track products
                results = tracker.track_products(urls, args.site)
                
                # Show alerts
                if args.alerts:
                    price_alerts = tracker.get_price_alerts(limit=5)
                    availability_alerts = tracker.get_availability_alerts(limit=5)
                    
                    if price_alerts or availability_alerts:
                        print("\n🚨 NEW ALERTS:")
                        self.display_alerts(price_alerts[:3] + availability_alerts[:3])
                
                # Check if duration exceeded
                if end_time and datetime.now() >= end_time:
                    self.logger.info(f"Monitoring completed after {args.duration} hours")
                    break
                
                # Wait for next check
                self.logger.info(f"Next check in {args.interval} seconds...")
                time.sleep(args.interval)
        
        except KeyboardInterrupt:
            self.logger.info("Monitoring stopped by user")
        except Exception as e:
            self.logger.error(f"Monitoring failed: {e}")
    
    def alerts_command(self, args):
        """Execute alerts command."""
        tracker = PriceTrackerEngine()
        
        if args.type == 'price' or args.type == 'all':
            price_alerts = tracker.get_price_alerts(args.limit)
            if price_alerts:
                print(f"\n💰 PRICE ALERTS ({len(price_alerts)} recent):")
                self.display_alerts(price_alerts)
            else:
                print("No price alerts found")
        
        if args.type == 'availability' or args.type == 'all':
            availability_alerts = tracker.get_availability_alerts(args.limit)
            if availability_alerts:
                print(f"\n📦 AVAILABILITY ALERTS ({len(availability_alerts)} recent):")
                self.display_alerts(availability_alerts)
            else:
                print("No availability alerts found")
        
        # Export alerts if requested
        if args.export:
            all_alerts = tracker.get_price_alerts() + tracker.get_availability_alerts()
            self.export_alerts(all_alerts, args.export)
    
    def history_command(self, args):
        """Execute history command."""
        tracker = PriceTrackerEngine()
        
        if args.product_id:
            # Show specific product history
            history = tracker.get_product_price_history(args.product_id)
            
            if history:
                print(f"\n📈 PRICE HISTORY FOR PRODUCT {args.product_id}:")
                for entry in history[-20:]:  # Show last 20 entries
                    timestamp = entry['timestamp']
                    price = entry['price']
                    print(f"  {timestamp}: £{price:.2f}" if price else f"  {timestamp}: No price")
                
                # Show trends if requested
                if args.trends:
                    trends = tracker.get_price_trends(args.product_id, args.days)
                    if trends:
                        print(f"\n📊 PRICE TRENDS (Last {args.days} days):")
                        print(f"  Average Price: £{trends['average_price']:.2f}")
                        print(f"  Price Range: £{trends['min_price']:.2f} - £{trends['max_price']:.2f}")
                        print(f"  Current Price: £{trends['current_price']:.2f}")
                        print(f"  Trend: {trends['trend']}")
                        print(f"  Volatility: {trends['volatility']:.1f}%")
            else:
                print(f"No history found for product {args.product_id}")
        else:
            # Show summary of all tracked products
            print(f"\n📊 TRACKED PRODUCTS: {len(tracker.price_history)}")
            for product_id, history in list(tracker.price_history.items())[:10]:
                if history:
                    latest = history[-1]
                    print(f"  {product_id[:8]}...: £{latest['price']:.2f} ({latest['timestamp']})")
    
    def export_command(self, args):
        """Execute export command."""
        # This would require database integration for full functionality
        print(f"Export functionality would be implemented with database integration")
        print(f"Format: {args.format}, Output: {args.output}, Days: {args.days}")
    
    def stats_command(self, args):
        """Execute stats command."""
        tracker = PriceTrackerEngine()
        stats = tracker.get_tracker_stats()
        
        print("\n📊 PRICE TRACKER STATISTICS:")
        print(f"  Total Checks: {stats['total_checks']}")
        print(f"  Price Changes: {stats['price_changes']}")
        print(f"  Availability Changes: {stats['availability_changes']}")
        print(f"  Errors: {stats['errors']}")
        print(f"  Tracked Products: {stats['tracked_products']}")
        print(f"  Price Alerts: {stats['price_alerts']}")
        print(f"  Availability Alerts: {stats['availability_alerts']}")
        print(f"  Runtime: {stats['runtime_seconds']:.1f} seconds")
        print(f"  Checks per Hour: {stats['checks_per_hour']:.1f}")
        
        if args.detailed:
            print(f"\n📈 DETAILED ANALYSIS:")
            if stats['price_changes'] > 0:
                print(f"  Price Change Rate: {(stats['price_changes']/stats['total_checks']*100):.1f}%")
            if stats['tracked_products'] > 0:
                print(f"  Alerts per Product: {stats['price_alerts']/stats['tracked_products']:.1f}")
    
    def demo_command(self, args):
        """Execute demo command."""
        self.logger.info(f"Running demo on {args.site} for {args.pages} pages")
        
        # Initialize tracker
        tracker = PriceTrackerEngine()
        
        # Get site configuration
        site_config = CONFIG.get_site_config(args.site)
        if not site_config:
            self.logger.error(f"No configuration found for site: {args.site}")
            return
        
        # Generate demo URLs (for books.toscrape.com)
        if args.site == 'books.toscrape.com':
            urls = [f"http://books.toscrape.com/catalogue/page-{i}.html" 
                   for i in range(1, args.pages + 1)]
        else:
            self.logger.error("Demo only available for books.toscrape.com")
            return
        
        try:
            # Track products
            results = tracker.track_products(urls, args.site)
            
            if results:
                print(f"\n🎯 DEMO RESULTS:")
                print(f"  Products Found: {len(results)}")
                
                prices_with_data = [r['price'] for r in results if r['price']]
                if prices_with_data:
                    price_min = min(prices_with_data)
                    price_max = max(prices_with_data)
                    print(f"  Price Range: £{price_min:.2f} - £{price_max:.2f}")
                    avg_price = sum(prices_with_data) / len(prices_with_data)
                    print(f"  Average Price: £{avg_price:.2f}")
                
                # Show sample products
                print(f"\n📋 SAMPLE PRODUCTS:")
                for i, product in enumerate(results[:5]):
                    print(f"  {i+1}. {product.get('title', 'N/A')}")
                    print(f"     💰 Price: £{product.get('price', 0):.2f}")
                    print(f"     ⭐ Rating: {product.get('rating', 'N/A')}")
                    print(f"     📦 Availability: {product.get('availability', 'N/A')}")
                
                # Save data
                self.save_tracking_data(results, ['csv', 'excel'], f"demo_{args.site}")
                
                # Generate visualizations if requested
                if args.visualize:
                    self.generate_price_visualizations(results)
                
                # Show statistics
                stats = tracker.get_tracker_stats()
                self.display_stats(stats)
            else:
                print("No products found in demo")
        
        except Exception as e:
            self.logger.error(f"Demo failed: {e}")
    
    def display_tracking_results(self, results: List[Dict[str, Any]]):
        """Display tracking results."""
        print(f"\n🎯 TRACKING RESULTS:")
        print(f"  Products Tracked: {len(results)}")
        
        # Price statistics
        prices = [r['price'] for r in results if r.get('price')]
        if prices:
            print(f"  Price Range: £{min(prices):.2f} - £{max(prices):.2f}")
            print(f"  Average Price: £{sum(prices)/len(prices):.2f}")
        
        # Availability
        availability = [r.get('availability', 'Unknown') for r in results]
        in_stock = sum(1 for a in availability if a == 'In Stock')
        print(f"  In Stock: {in_stock}/{len(results)}")
    
    def display_alerts(self, alerts: List[Dict[str, Any]]):
        """Display alerts."""
        for alert in alerts:
            if alert['type'] in ['price_drop', 'price_increase', 'price_change']:
                change_type = "📉" if alert['type'] == 'price_drop' else "📈" if alert['type'] == 'price_increase' else "🔄"
                print(f"  {change_type} {alert['title']}")
                print(f"     £{alert['previous_price']:.2f} → £{alert['current_price']:.2f} ({alert['price_change_percent']:+.1f}%)")
            elif alert['type'] == 'availability_change':
                print(f"  📦 {alert['title']}")
                print(f"     {alert['previous_availability']} → {alert['current_availability']}")
            print(f"     🕐 {alert['timestamp']}")
            print()
    
    def display_stats(self, stats: Dict[str, Any]):
        """Display statistics."""
        print(f"\n📊 STATISTICS:")
        print(f"  Total Checks: {stats['total_checks']}")
        print(f"  Price Changes: {stats['price_changes']}")
        print(f"  Tracked Products: {stats['tracked_products']}")
        print(f"  Runtime: {stats['runtime_seconds']:.1f}s")
    
    def save_tracking_data(self, results: List[Dict[str, Any]], formats: List[str], output_prefix: str = None):
        """Save tracking data."""
        if not output_prefix:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_prefix = f"price_tracker_{timestamp}"
        
        # Convert to storage format
        from ..parsers.data_parser import ParsedItem
        parsed_items = []
        
        for result in results:
            item = ParsedItem(
                data=result,
                source_url=result.get('url', ''),
                parsed_at=datetime.now(),
                confidence_score=1.0
            )
            parsed_items.append(item)
        
        # Save using storage manager
        storage_results = self.storage.save_items(parsed_items, formats, output_prefix)
        
        if storage_results['saved_files']:
            print(f"\n💾 Data saved:")
            for file_path in storage_results['saved_files']:
                print(f"  📄 {file_path}")
    
    def generate_price_visualizations(self, results: List[Dict[str, Any]]):
        """Generate price visualizations."""
        try:
            import pandas as pd
            
            # Convert to DataFrame
            df = pd.DataFrame(results)
            
            if 'price' in df.columns and not df.empty:
                viz_file = self.visualizer.create_comprehensive_analysis(
                    df, 
                    f"price_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                )
                print(f"\n🎨 Visualization saved: {viz_file}")
        
        except Exception as e:
            self.logger.error(f"Failed to generate visualizations: {e}")
    
    def export_alerts(self, alerts: List[Dict[str, Any]], filename: str):
        """Export alerts to file."""
        try:
            with open(filename, 'w') as f:
                json.dump(alerts, f, indent=2)
            print(f"\n💾 Alerts exported to: {filename}")
        
        except Exception as e:
            self.logger.error(f"Failed to export alerts: {e}")
    
    def run(self, args: List[str] = None) -> int:
        """Run the CLI application."""
        parser = self.create_parser()
        parsed_args = parser.parse_args(args)
        
        # Setup logging
        setup_logging('INFO')
        
        if not parsed_args.command:
            parser.print_help()
            return 1
        
        try:
            # Execute command
            if parsed_args.command == 'track':
                self.track_command(parsed_args)
            elif parsed_args.command == 'monitor':
                self.monitor_command(parsed_args)
            elif parsed_args.command == 'alerts':
                self.alerts_command(parsed_args)
            elif parsed_args.command == 'history':
                self.history_command(parsed_args)
            elif parsed_args.command == 'export':
                self.export_command(parsed_args)
            elif parsed_args.command == 'stats':
                self.stats_command(parsed_args)
            elif parsed_args.command == 'demo':
                self.demo_command(parsed_args)
            
            return 0
        
        except KeyboardInterrupt:
            print("\n⏹️  Operation stopped by user")
            return 130
        except Exception as e:
            self.logger.error(f"Command failed: {e}")
            print(f"\n❌ Error: {e}")
            return 1


def main():
    """Main entry point for the price tracker CLI."""
    import time
    cli = PriceTrackerCLI()
    exit_code = cli.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

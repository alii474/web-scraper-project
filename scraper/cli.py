# scraper/cli.py
import argparse
import sys
from .scraper import WebScraper
from .visualization import DataVisualizer
import logging

def create_visualizations(df, filename_prefix):
    """
    Create and save data visualizations.
    
    Args:
        df: DataFrame with book data
        filename_prefix: Prefix for output filenames
    """
    visualizer = DataVisualizer()
    visualizer.create_comprehensive_analysis(df, filename_prefix)

def main():
    parser = argparse.ArgumentParser(
        description="Professional Web Scraper for Books",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --pages 3
  python main.py --url http://books.toscrape.com/ --pages 2 --visualize
  python main.py --pages 1 --delay 2.0
        """
    )
    
    parser.add_argument(
        '--url',
        type=str,
        default='http://books.toscrape.com/',
        help='Base URL to scrape (default: http://books.toscrape.com/)'
    )
    
    parser.add_argument(
        '--pages',
        type=int,
        default=1,
        help='Number of pages to scrape (default: 1)'
    )
    
    parser.add_argument(
        '--delay',
        type=float,
        default=1.0,
        help='Delay between requests in seconds (default: 1.0)'
    )
    
    parser.add_argument(
        '--visualize',
        action='store_true',
        help='Generate data visualizations after scraping'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='books_data',
        help='Output filename prefix (default: books_data)'
    )
    
    args = parser.parse_args()
    
    print("🔥 Professional Web Scraper")
    print("=" * 40)
    print(f"Target URL: {args.url}")
    print(f"Pages to scrape: {args.pages}")
    print(f"Delay between requests: {args.delay}s")
    print(f"Visualizations: {'Enabled' if args.visualize else 'Disabled'}")
    print("-" * 40)
    
    try:
        # Initialize scraper
        scraper = WebScraper(args.url, args.delay)
        
        # Scrape data
        df, csv_path, excel_path = scraper.scrape_books(args.pages)
        
        if df.empty:
            print("❌ No data was scraped. Please check the logs for details.")
            sys.exit(1)
        
        # Display results
        print("\n📈 Scraping Results:")
        print(f"Total books scraped: {len(df)}")
        print(f"Columns: {', '.join(df.columns.tolist())}")
        print(f"\n💾 Files saved:")
        print(f"CSV: {csv_path}")
        print(f"Excel: {excel_path}")
        
        # Display sample data
        print(f"\n📋 Sample Data (first 5 rows):")
        print(df.head().to_string(index=False))
        
        # Price statistics
        print(f"\n💰 Price Statistics:")
        print(f"Average price: £{df['price'].mean():.2f}")
        print(f"Minimum price: £{df['price'].min():.2f}")
        print(f"Maximum price: £{df['price'].max():.2f}")
        
        # Generate visualizations if requested
        if args.visualize and len(df) > 0:
            print("\n🎨 Generating visualizations...")
            create_visualizations(df, args.output)
        
        print("\n✅ Scraping completed successfully!")
        
    except KeyboardInterrupt:
        print("\n⏹️  Scraping interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

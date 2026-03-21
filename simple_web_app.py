"""
Simple Web Scraper - Working Flask App

A simplified, working web interface for the web scraper.
"""

from flask import Flask, render_template, request, jsonify, send_file
import json
import threading
import time
import sys
import os
from pathlib import Path
from datetime import datetime
import uuid

# Add src directory to Python path
project_root = Path(__file__).parent
src_path = project_root / 'src'
sys.path.insert(0, str(src_path))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'simple-scraper-secret-key'

# Global variables for tracking
active_scrapes = {}
scrape_results = {}
scrape_history = []

class SimpleScraper:
    """Simple scraper for web interface."""
    
    def __init__(self):
        self.logger = self._setup_logger()
    
    def _setup_logger(self):
        """Setup simple logger."""
        import logging
        logging.basicConfig(level=logging.INFO)
        return logging.getLogger('simple_scraper')
    
    def scrape_url(self, url, max_pages=3):
        """Simple scraping function."""
        try:
            import requests
            from bs4 import BeautifulSoup
            
            results = []
            
            for page in range(1, max_pages + 1):
                try:
                    # For books.toscrape.com
                    if 'books.toscrape.com' in url:
                        page_url = f"http://books.toscrape.com/catalogue/page-{page}.html"
                    else:
                        page_url = url
                    
                    response = requests.get(page_url, timeout=30)
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # Extract books
                        books = soup.find_all('article', class_='product_pod')
                        
                        for book in books:
                            title = book.h3.a['title'] if book.h3 and book.h3.a else 'Unknown'
                            price_text = book.find('p', class_='price_color').text if book.find('p', class_='price_color') else '0.00'
                            price = float(price_text.replace('£', '').strip())
                            rating = book.find('p', class_='star-rating')['class'][-1] if book.find('p', class_='star-rating') else 'Unknown'
                            availability = book.find('p', class_='instock availability').text.strip() if book.find('p', class_='instock availability') else 'Unknown'
                            
                            book_url = book.h3.a['href'] if book.h3 and book.h3.a else ''
                            if book_url and not book_url.startswith('http'):
                                book_url = f"http://books.toscrape.com/{book_url}"
                            
                            results.append({
                                'title': title,
                                'price': price,
                                'rating': rating,
                                'availability': availability,
                                'url': book_url,
                                'scraped_at': datetime.now().isoformat()
                            })
                    
                    # Add delay
                    time.sleep(1)
                    
                except Exception as e:
                    self.logger.error(f"Error scraping page {page}: {e}")
            
            return {
                'status': 'success',
                'items_scraped': len(results),
                'pages_scraped': max_pages,
                'results': results,
                'processing_time': 0
            }
            
        except Exception as e:
            self.logger.error(f"Scraping failed: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'items_scraped': 0,
                'pages_scraped': 0,
                'results': []
            }

# Global scraper instance
scraper = SimpleScraper()

@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('simple_index.html')

@app.route('/scrape', methods=['POST'])
def start_scraping():
    """Start a new scraping operation."""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('url'):
            return jsonify({'error': 'URL is required'}), 400
        
        # Generate scrape ID
        scrape_id = str(uuid.uuid4())
        
        # Store initial status
        active_scrapes[scrape_id] = {
            'url': data['url'],
            'status': 'running',
            'started_at': datetime.now().isoformat(),
            'progress': 0,
            'pages_scraped': 0,
            'items_found': 0
        }
        
        # Start scraping in background thread
        def scrape_background():
            try:
                # Update status
                active_scrapes[scrape_id]['status'] = 'running'
                
                # Run scraping
                max_pages = int(data.get('max_pages', 3))
                result = scraper.scrape_url(data['url'], max_pages)
                
                # Store result
                scrape_results[scrape_id] = {
                    'status': 'completed' if result['status'] == 'success' else 'error',
                    'result': result,
                    'completed_at': datetime.now().isoformat()
                }
                
                # Update history
                scrape_history.append({
                    'scrape_id': scrape_id,
                    'url': data['url'],
                    'status': result['status'],
                    'pages_scraped': result['pages_scraped'],
                    'items_scraped': result['items_scraped'],
                    'timestamp': datetime.now().isoformat()
                })
                
                # Remove from active
                if scrape_id in active_scrapes:
                    del active_scrapes[scrape_id]
                
                print(f"Web scraping completed: {scrape_id}")
            
            except Exception as e:
                # Store error
                scrape_results[scrape_id] = {
                    'status': 'error',
                    'error': str(e),
                    'completed_at': datetime.now().isoformat()
                }
                
                # Update history
                scrape_history.append({
                    'scrape_id': scrape_id,
                    'url': data['url'],
                    'status': 'error',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
                
                # Remove from active
                if scrape_id in active_scrapes:
                    del active_scrapes[scrape_id]
                
                print(f"Web scraping failed: {scrape_id} - {e}")
        
        # Start background thread
        thread = threading.Thread(target=scrape_background)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'scrape_id': scrape_id,
            'status': 'started',
            'message': 'Scraping started successfully'
        })
    
    except Exception as e:
        print(f"Failed to start scraping: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/scrape/<scrape_id>/status')
def get_scrape_status(scrape_id):
    """Get status of a scraping operation."""
    if scrape_id in active_scrapes:
        return jsonify(active_scrapes[scrape_id])
    elif scrape_id in scrape_results:
        return jsonify(scrape_results[scrape_id])
    else:
        return jsonify({'error': 'Scrape not found'}), 404

@app.route('/scrapes')
def list_scrapes():
    """List all scraping operations."""
    all_scrapes = {}
    all_scrapes.update(active_scrapes)
    all_scrapes.update(scrape_results)
    
    # Calculate statistics
    stats = {
        'total_count': len(all_scrapes),
        'active_count': len(active_scrapes),
        'completed_count': len([s for s in scrape_results.values() if s['status'] == 'completed']),
        'error_count': len([s for s in scrape_results.values() if s['status'] == 'error'])
    }
    
    return jsonify({
        'scrapes': all_scrapes,
        'stats': stats
    })

@app.route('/history')
def get_history():
    """Get scraping history."""
    return jsonify({'history': scrape_history[-20:]})  # Last 20 items

@app.route('/stats')
def get_statistics():
    """Get comprehensive statistics."""
    all_scrapes = {}
    all_scrapes.update(active_scrapes)
    all_scrapes.update(scrape_results)
    
    # Calculate success rate
    completed = len([s for s in scrape_results.values() if s['status'] == 'completed'])
    total = len(scrape_results)
    success_rate = (completed / total * 100) if total > 0 else 0
    
    # Calculate total items
    total_items = sum(s['result']['items_scraped'] for s in scrape_results.values() 
                     if s['status'] == 'completed' and 'result' in s)
    
    return jsonify({
        'scraping_stats': {
            'total_scrapes': len(all_scrapes),
            'active_scrapes': len(active_scrapes),
            'completed_scrapes': completed,
            'success_rate': success_rate,
            'total_items': total_items
        }
    })

@app.route('/download/<filename>')
def download_file(filename):
    """Download a file."""
    try:
        file_path = Path('output') / filename
        
        if not file_path.exists():
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(file_path, as_attachment=True)
    
    except Exception as e:
        print(f"Failed to download file: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0',
        'active_scrapes': len(active_scrapes)
    })

if __name__ == '__main__':
    # Create directories if they don't exist
    Path('output').mkdir(exist_ok=True)
    Path('logs').mkdir(exist_ok=True)
    Path('templates').mkdir(exist_ok=True)
    
    print("🚀 Starting Simple Web Scraper Application")
    print("📱 Open your browser and go to: http://localhost:5000")
    print("🎯 Happy Scraping!")
    
    app.run(host='0.0.0.0', port=5000, debug=True)

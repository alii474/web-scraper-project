"""
Professional Web Scraper - Flask Web Application

Beautiful, modern web interface for the advanced web scraper.
Features real-time scraping, progress tracking, and data visualization.
"""

from flask import Flask, render_template, request, jsonify, send_file, flash, redirect, url_for
from flask_cors import CORS
import json
import threading
import time
import sys
import os
from pathlib import Path
from datetime import datetime
import pandas as pd
import uuid

# Add src directory to Python path
project_root = Path(__file__).parent
src_path = project_root / 'src'
sys.path.insert(0, str(src_path))

# Import our scraper components
from src.core.scraper import AdvancedWebScraper
from src.storage.advanced_storage import AdvancedStorageManager
from src.utils.logger import get_logger
from src.utils.config import CONFIG

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
CORS(app)

# Initialize components
logger = get_logger('web_app')
storage = AdvancedStorageManager()

# Global variables for tracking
active_scrapes = {}
scrape_results = {}
scrape_history = []

class WebScrapingManager:
    """Manages scraping operations for the web interface."""
    
    def __init__(self):
        self.active_scrapes = {}
        self.results = {}
        self.history = []
    
    def start_scraping(self, url, options):
        """Start a new scraping operation."""
        scrape_id = str(uuid.uuid4())
        
        # Store initial status
        self.active_scrapes[scrape_id] = {
            'url': url,
            'status': 'starting',
            'started_at': datetime.now().isoformat(),
            'progress': 0,
            'pages_scraped': 0,
            'items_found': 0,
            'options': options
        }
        
        # Start scraping in background thread
        def scrape_background():
            try:
                # Update status
                self.active_scrapes[scrape_id]['status'] = 'running'
                
                # Initialize scraper
                scraper = AdvancedWebScraper(
                    use_selenium=options.get('selenium', False),
                    max_pages=options.get('max_pages', 5),
                    concurrent=options.get('concurrent', False),
                    rate_limit=options.get('rate_limit', 1.0)
                )
                
                # Run scraping
                result = scraper.scrape_url(
                    url,
                    max_pages=options.get('max_pages', 5),
                    formats=options.get('formats', ['csv', 'excel']),
                    output_filename=options.get('output_filename')
                )
                
                # Store result
                self.results[scrape_id] = {
                    'status': 'completed',
                    'result': result,
                    'completed_at': datetime.now().isoformat()
                }
                
                # Update history
                self.history.append({
                    'scrape_id': scrape_id,
                    'url': url,
                    'status': 'completed',
                    'pages_scraped': result['pages_scraped'],
                    'items_scraped': result['items_scraped'],
                    'timestamp': datetime.now().isoformat()
                })
                
                # Remove from active
                if scrape_id in self.active_scrapes:
                    del self.active_scrapes[scrape_id]
                
                logger.info(f"Web scraping completed: {scrape_id}")
            
            except Exception as e:
                # Store error
                self.results[scrape_id] = {
                    'status': 'error',
                    'error': str(e),
                    'completed_at': datetime.now().isoformat()
                }
                
                # Update history
                self.history.append({
                    'scrape_id': scrape_id,
                    'url': url,
                    'status': 'error',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
                
                # Remove from active
                if scrape_id in self.active_scrapes:
                    del self.active_scrapes[scrape_id]
                
                logger.error(f"Web scraping failed: {scrape_id} - {e}")
            
            finally:
                scraper.close()
        
        # Start background thread
        thread = threading.Thread(target=scrape_background)
        thread.daemon = True
        thread.start()
        
        return scrape_id
    
    def get_scrape_status(self, scrape_id):
        """Get status of a scraping operation."""
        if scrape_id in self.active_scrapes:
            return self.active_scrapes[scrape_id]
        elif scrape_id in self.results:
            return self.results[scrape_id]
        else:
            return None
    
    def get_all_scrapes(self):
        """Get all scraping operations."""
        all_scrapes = {}
        all_scrapes.update(self.active_scrapes)
        all_scrapes.update(self.results)
        return all_scrapes
    
    def get_history(self, limit=50):
        """Get scraping history."""
        return self.history[-limit:]

# Global scraping manager
scraping_manager = WebScrapingManager()

@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('index.html')

@app.route('/scrape', methods=['POST'])
def start_scraping():
    """Start a new scraping operation."""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('url'):
            return jsonify({'error': 'URL is required'}), 400
        
        # Extract options
        options = {
            'max_pages': int(data.get('max_pages', 5)),
            'formats': data.get('formats', ['csv', 'excel']),
            'selenium': data.get('selenium', False),
            'concurrent': data.get('concurrent', False),
            'rate_limit': float(data.get('rate_limit', 1.0)),
            'output_filename': data.get('output_filename')
        }
        
        # Start scraping
        scrape_id = scraping_manager.start_scraping(data['url'], options)
        
        return jsonify({
            'scrape_id': scrape_id,
            'status': 'started',
            'message': 'Scraping started successfully'
        })
    
    except Exception as e:
        logger.error(f"Failed to start scraping: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/scrape/<scrape_id>/status')
def get_scrape_status(scrape_id):
    """Get status of a scraping operation."""
    status = scraping_manager.get_scrape_status(scrape_id)
    
    if status:
        return jsonify(status)
    else:
        return jsonify({'error': 'Scrape not found'}), 404

@app.route('/scrapes')
def list_scrapes():
    """List all scraping operations."""
    all_scrapes = scraping_manager.get_all_scrapes()
    
    # Calculate statistics
    stats = {
        'total_count': len(all_scrapes),
        'active_count': len(scraping_manager.active_scrapes),
        'completed_count': len([s for s in scraping_manager.results.values() if s['status'] == 'completed']),
        'error_count': len([s for s in scraping_manager.results.values() if s['status'] == 'error'])
    }
    
    return jsonify({
        'scrapes': all_scrapes,
        'stats': stats
    })

@app.route('/history')
def get_history():
    """Get scraping history."""
    history = scraping_manager.get_history()
    return jsonify({'history': history})

@app.route('/data')
def get_scraped_data():
    """Get scraped data from database."""
    try:
        limit = request.args.get('limit', type=int)
        source_url = request.args.get('source_url')
        
        items = storage.sqlite_storage.load(limit=limit, source_url=source_url)
        
        # Convert to JSON-serializable format
        data = []
        for item in items:
            item_dict = {
                'data': item.data,
                'source_url': item.source_url,
                'parsed_at': item.parsed_at.isoformat(),
                'confidence_score': item.confidence_score
            }
            data.append(item_dict)
        
        return jsonify({
            'data': data,
            'total_count': len(data)
        })
    
    except Exception as e:
        logger.error(f"Failed to get data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/stats')
def get_statistics():
    """Get comprehensive statistics."""
    try:
        # Storage stats
        storage_stats = storage.get_storage_stats()
        
        # Scraping stats
        all_scrapes = scraping_manager.get_all_scrapes()
        recent_scrapes = scraping_manager.get_history(10)
        
        # Calculate success rate
        completed = len([s for s in scraping_manager.results.values() if s['status'] == 'completed'])
        total = len(scraping_manager.results)
        success_rate = (completed / total * 100) if total > 0 else 0
        
        return jsonify({
            'storage_stats': storage_stats,
            'scraping_stats': {
                'total_scrapes': len(all_scrapes),
                'active_scrapes': len(scraping_manager.active_scrapes),
                'completed_scrapes': completed,
                'success_rate': success_rate
            },
            'recent_scrapes': recent_scrapes
        })
    
    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
def download_file(filename):
    """Download a file."""
    try:
        file_path = Path('output') / filename
        
        if not file_path.exists():
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(file_path, as_attachment=True)
    
    except Exception as e:
        logger.error(f"Failed to download file: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/visualize')
def create_visualization():
    """Create data visualization."""
    try:
        # Get data from database
        items = storage.sqlite_storage.load(limit=1000)
        
        if not items:
            return jsonify({'error': 'No data available for visualization'}), 400
        
        # Convert to DataFrame
        df_data = [item.data for item in items]
        df = pd.DataFrame(df_data)
        
        if df.empty:
            return jsonify({'error': 'No data available for visualization'}), 400
        
        # Create visualization
        from src.utils.visualization import DataVisualizer
        visualizer = DataVisualizer()
        
        viz_file = visualizer.create_comprehensive_analysis(
            df, 
            f"web_visualization_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        
        return jsonify({
            'visualization_file': viz_file,
            'message': 'Visualization created successfully'
        })
    
    except Exception as e:
        logger.error(f"Failed to create visualization: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/config')
def get_config():
    """Get current configuration."""
    return jsonify({
        'default_max_pages': CONFIG.DEFAULT_MAX_PAGES,
        'supported_formats': CONFIG.SUPPORTED_FORMATS,
        'default_formats': CONFIG.DEFAULT_FORMATS,
        'selenium_enabled': CONFIG.SELENIUM_ENABLED,
        'default_rate_limit': 1.0
    })

@app.route('/health')
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '2.0.0',
        'active_scrapes': len(scraping_manager.active_scrapes)
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Page not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Create directories if they don't exist
    Path('output').mkdir(exist_ok=True)
    Path('logs').mkdir(exist_ok=True)
    
    print("🚀 Starting Web Scraper Application")
    print("📱 Open your browser and go to: http://localhost:5000")
    print("🎯 Happy Scraping!")
    
    app.run(host='0.0.0.0', port=5000, debug=True)

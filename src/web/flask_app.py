"""
Flask Web Application for Web Scraper

Provides a web interface for the advanced web scraper.
Includes API endpoints, dashboard, and real-time monitoring.
"""

from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import json
import threading
from pathlib import Path
from datetime import datetime
import pandas as pd

from ..core.scraper import AdvancedWebScraper
from ..storage.advanced_storage import AdvancedStorageManager
from ..utils.scheduler import scheduler
from ..utils.logger import get_logger
from ..utils.config import CONFIG
from ..utils.visualization import DataVisualizer


def create_app():
    """Create and configure Flask application."""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your-secret-key-here'
    
    # Enable CORS
    CORS(app)
    
    # Initialize components
    logger = get_logger('flask_app')
    storage = AdvancedStorageManager()
    visualizer = DataVisualizer()
    
    # Global variables for tracking
    active_scrapes = {}
    scrape_results = {}
    
    @app.route('/')
    def index():
        """Main dashboard page."""
        return render_template('dashboard.html')
    
    @app.route('/api/scrape', methods=['POST'])
    def start_scraping():
        """Start a new scraping operation."""
        try:
            data = request.get_json()
            
            # Validate required fields
            if not data.get('url'):
                return jsonify({'error': 'URL is required'}), 400
            
            # Generate scrape ID
            scrape_id = f"scrape_{int(datetime.now().timestamp())}"
            
            # Start scraping in background thread
            def scrape_background():
                try:
                    # Initialize scraper
                    scraper = AdvancedWebScraper(
                        use_selenium=data.get('selenium'),
                        max_pages=data.get('max_pages', CONFIG.DEFAULT_MAX_PAGES),
                        concurrent=data.get('concurrent', False),
                        rate_limit=data.get('rate_limit', 1.0)
                    )
                    
                    # Run scraping
                    result = scraper.scrape_url(
                        data['url'],
                        max_pages=data.get('max_pages', CONFIG.DEFAULT_MAX_PAGES),
                        formats=data.get('formats', CONFIG.DEFAULT_FORMATS),
                        output_filename=data.get('output_filename')
                    )
                    
                    # Store result
                    scrape_results[scrape_id] = {
                        'status': 'completed',
                        'result': result,
                        'completed_at': datetime.now().isoformat()
                    }
                    
                    # Remove from active scrapes
                    if scrape_id in active_scrapes:
                        del active_scrapes[scrape_id]
                    
                    logger.info(f"Scraping completed: {scrape_id}")
                
                except Exception as e:
                    # Store error
                    scrape_results[scrape_id] = {
                        'status': 'error',
                        'error': str(e),
                        'completed_at': datetime.now().isoformat()
                    }
                    
                    # Remove from active scrapes
                    if scrape_id in active_scrapes:
                        del active_scrapes[scrape_id]
                    
                    logger.error(f"Scraping failed: {scrape_id} - {e}")
                
                finally:
                    scraper.close()
            
            # Add to active scrapes
            active_scrapes[scrape_id] = {
                'url': data['url'],
                'started_at': datetime.now().isoformat(),
                'status': 'running'
            }
            
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
            logger.error(f"Failed to start scraping: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/scrape/<scrape_id>/status', methods=['GET'])
    def get_scrape_status(scrape_id):
        """Get status of a scraping operation."""
        if scrape_id in active_scrapes:
            return jsonify({
                'scrape_id': scrape_id,
                'status': 'running',
                'started_at': active_scrapes[scrape_id]['started_at'],
                'url': active_scrapes[scrape_id]['url']
            })
        elif scrape_id in scrape_results:
            return jsonify(scrape_results[scrape_id])
        else:
            return jsonify({'error': 'Scrape not found'}), 404
    
    @app.route('/api/scrapes', methods=['GET'])
    def list_scrapes():
        """List all scraping operations."""
        all_scrapes = {}
        
        # Add active scrapes
        all_scrapes.update(active_scrapes)
        
        # Add completed scrapes
        all_scrapes.update(scrape_results)
        
        return jsonify({
            'scrapes': all_scrapes,
            'total_count': len(all_scrapes),
            'active_count': len(active_scrapes),
            'completed_count': len([s for s in scrape_results.values() if s['status'] == 'completed']),
            'error_count': len([s for s in scrape_results.values() if s['status'] == 'error'])
        })
    
    @app.route('/api/schedule', methods=['POST'])
    def schedule_scraping():
        """Schedule a new scraping job."""
        try:
            data = request.get_json()
            
            # Validate required fields
            if not data.get('url'):
                return jsonify({'error': 'URL is required'}), 400
            
            if not data.get('schedule_pattern'):
                return jsonify({'error': 'Schedule pattern is required'}), 400
            
            # Add job to scheduler
            job_id = scheduler.add_job(
                url=data['url'],
                schedule_pattern=data['schedule_pattern'],
                scraper_config={
                    'max_pages': data.get('max_pages', CONFIG.DEFAULT_MAX_PAGES),
                    'formats': data.get('formats', CONFIG.DEFAULT_FORMATS),
                    'concurrent': data.get('concurrent', False),
                    'rate_limit': data.get('rate_limit', 1.0)
                },
                max_runs=data.get('max_runs')
            )
            
            return jsonify({
                'job_id': job_id,
                'status': 'scheduled',
                'message': 'Job scheduled successfully'
            })
        
        except Exception as e:
            logger.error(f"Failed to schedule job: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/schedule/<job_id>', methods=['GET'])
    def get_job_status(job_id):
        """Get status of a scheduled job."""
        job_status = scheduler.get_job_status(job_id)
        
        if job_status:
            return jsonify(job_status)
        else:
            return jsonify({'error': 'Job not found'}), 404
    
    @app.route('/api/schedule/<job_id>/pause', methods=['POST'])
    def pause_job(job_id):
        """Pause a scheduled job."""
        if scheduler.pause_job(job_id):
            return jsonify({'status': 'paused'})
        else:
            return jsonify({'error': 'Job not found'}), 404
    
    @app.route('/api/schedule/<job_id>/resume', methods=['POST'])
    def resume_job(job_id):
        """Resume a paused scheduled job."""
        if scheduler.resume_job(job_id):
            return jsonify({'status': 'resumed'})
        else:
            return jsonify({'error': 'Job not found'}), 404
    
    @app.route('/api/schedule/<job_id>/remove', methods=['DELETE'])
    def remove_job(job_id):
        """Remove a scheduled job."""
        if scheduler.remove_job(job_id):
            return jsonify({'status': 'removed'})
        else:
            return jsonify({'error': 'Job not found'}), 404
    
    @app.route('/api/schedule', methods=['GET'])
    def list_scheduled_jobs():
        """List all scheduled jobs."""
        jobs = scheduler.get_all_jobs()
        stats = scheduler.get_scheduler_stats()
        
        return jsonify({
            'jobs': jobs,
            'stats': stats
        })
    
    @app.route('/api/data', methods=['GET'])
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
    
    @app.route('/api/stats', methods=['GET'])
    def get_statistics():
        """Get comprehensive statistics."""
        try:
            # Storage stats
            storage_stats = storage.get_storage_stats()
            
            # Scheduler stats
            scheduler_stats = scheduler.get_scheduler_stats()
            
            # Recent scrapes
            recent_scrapes = list(scrape_results.values())[-10:]
            
            return jsonify({
                'storage_stats': storage_stats,
                'scheduler_stats': scheduler_stats,
                'active_scrapes': len(active_scrapes),
                'recent_scrapes': recent_scrapes
            })
        
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/visualize', methods=['POST'])
    def create_visualization():
        """Create data visualization."""
        try:
            data = request.get_json()
            
            # Get data from database
            items = storage.sqlite_storage.load(limit=data.get('limit', 1000))
            
            if not items:
                return jsonify({'error': 'No data available for visualization'}), 400
            
            # Convert to DataFrame
            df_data = [item.data for item in items]
            df = pd.DataFrame(df_data)
            
            # Create visualization
            viz_file = visualizer.create_comprehensive_analysis(
                df, 
                data.get('filename_prefix', 'web_visualization')
            )
            
            return jsonify({
                'visualization_file': viz_file,
                'message': 'Visualization created successfully'
            })
        
        except Exception as e:
            logger.error(f"Failed to create visualization: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/download/<filename>')
    def download_file(filename):
        """Download a file."""
        try:
            file_path = Path(CONFIG.OUTPUT_DIR) / filename
            
            if not file_path.exists():
                return jsonify({'error': 'File not found'}), 404
            
            return send_file(file_path, as_attachment=True)
        
        except Exception as e:
            logger.error(f"Failed to download file: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/config', methods=['GET'])
    def get_config():
        """Get current configuration."""
        return jsonify(CONFIG.to_dict())
    
    @app.route('/api/config', methods=['POST'])
    def update_config():
        """Update configuration."""
        try:
            data = request.get_json()
            
            # Update configuration (simplified)
            for key, value in data.items():
                if hasattr(CONFIG, key):
                    setattr(CONFIG, key, value)
            
            # Save configuration
            CONFIG.save_to_file()
            
            return jsonify({'status': 'updated'})
        
        except Exception as e:
            logger.error(f"Failed to update config: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/health')
    def health_check():
        """Health check endpoint."""
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0'
        })
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Endpoint not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {error}")
        return jsonify({'error': 'Internal server error'}), 500
    
    return app


def run_web_app(host='0.0.0.0', port=5000, debug=False):
    """
    Run the Flask web application.
    
    Args:
        host: Host to bind to
        port: Port to bind to
        debug: Enable debug mode
    """
    app = create_app()
    
    # Start scheduler
    scheduler.start()
    
    try:
        app.run(host=host, port=port, debug=debug)
    finally:
        # Stop scheduler
        scheduler.stop()


if __name__ == '__main__':
    run_web_app(debug=True)

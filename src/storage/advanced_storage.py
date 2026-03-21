"""
Advanced Storage Module

Handles data storage in multiple formats with automatic deduplication,
timestamp management, and database operations.
"""

import sqlite3
import csv
import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import hashlib
from dataclasses import dataclass, asdict
import pickle

from ..utils.logger import get_logger
from ..utils.config import CONFIG
from ..parsers.data_parser import ParsedItem


@dataclass
class StorageStats:
    """Storage operation statistics."""
    records_processed: int
    records_inserted: int
    records_updated: int
    records_skipped: int
    duplicates_found: int
    processing_time: float


class DataDeduplicator:
    """Handles duplicate detection and removal."""
    
    def __init__(self):
        self.logger = get_logger('deduplicator')
        self.seen_hashes = set()
    
    def generate_hash(self, item: Dict[str, Any]) -> str:
        """
        Generate hash for item to detect duplicates.
        
        Args:
            item: Data item
        
        Returns:
            SHA256 hash
        """
        # Create a deterministic string representation
        item_str = json.dumps(item, sort_keys=True, default=str)
        return hashlib.sha256(item_str.encode()).hexdigest()
    
    def is_duplicate(self, item: Dict[str, Any]) -> bool:
        """
        Check if item is duplicate.
        
        Args:
            item: Data item
        
        Returns:
            True if duplicate
        """
        item_hash = self.generate_hash(item)
        is_dup = item_hash in self.seen_hashes
        
        if not is_dup:
            self.seen_hashes.add(item_hash)
        
        return is_dup
    
    def remove_duplicates(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicates from list of items.
        
        Args:
            items: List of data items
        
        Returns:
            List without duplicates
        """
        unique_items = []
        duplicates = 0
        
        for item in items:
            if not self.is_duplicate(item):
                unique_items.append(item)
            else:
                duplicates += 1
        
        self.logger.info(f"Removed {duplicates} duplicates from {len(items)} items")
        return unique_items
    
    def reset(self):
        """Reset the deduplicator."""
        self.seen_hashes.clear()


class CSVStorage:
    """CSV file storage handler."""
    
    def __init__(self, output_dir: Path = None):
        self.logger = get_logger('csv_storage')
        self.output_dir = output_dir or Path(__file__).parent.parent.parent / "output"
        self.output_dir.mkdir(exist_ok=True)
    
    def save(self, items: List[ParsedItem], filename: str = None) -> Path:
        """
        Save items to CSV file.
        
        Args:
            items: List of parsed items
            filename: Custom filename
        
        Returns:
            Path to saved file
        """
        if not items:
            self.logger.warning("No items to save to CSV")
            return None
        
        # Generate filename
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data_{timestamp}.csv"
        
        if not filename.endswith('.csv'):
            filename += '.csv'
        
        file_path = self.output_dir / filename
        
        try:
            # Convert items to DataFrame
            data = []
            for item in items:
                row = item.data.copy()
                row.update({
                    'source_url': item.source_url,
                    'parsed_at': item.parsed_at.isoformat(),
                    'confidence_score': item.confidence_score
                })
                data.append(row)
            
            df = pd.DataFrame(data)
            
            # Save to CSV
            df.to_csv(file_path, index=False, encoding='utf-8')
            
            self.logger.info(f"Saved {len(items)} items to CSV: {file_path}")
            return file_path
        
        except Exception as e:
            self.logger.error(f"Failed to save CSV: {e}")
            raise
    
    def load(self, file_path: Path) -> List[ParsedItem]:
        """
        Load items from CSV file.
        
        Args:
            file_path: Path to CSV file
        
        Returns:
            List of parsed items
        """
        try:
            df = pd.read_csv(file_path, encoding='utf-8')
            
            items = []
            for _, row in df.iterrows():
                # Extract item data
                item_data = row.to_dict()
                
                # Extract metadata
                source_url = item_data.pop('source_url', '')
                parsed_at = datetime.fromisoformat(item_data.pop('parsed_at', datetime.now().isoformat()))
                confidence_score = item_data.pop('confidence_score', 1.0)
                
                item = ParsedItem(
                    data=item_data,
                    source_url=source_url,
                    parsed_at=parsed_at,
                    confidence_score=confidence_score
                )
                items.append(item)
            
            self.logger.info(f"Loaded {len(items)} items from CSV: {file_path}")
            return items
        
        except Exception as e:
            self.logger.error(f"Failed to load CSV: {e}")
            return []


class ExcelStorage:
    """Excel file storage handler."""
    
    def __init__(self, output_dir: Path = None):
        self.logger = get_logger('excel_storage')
        self.output_dir = output_dir or Path(__file__).parent.parent.parent / "output"
        self.output_dir.mkdir(exist_ok=True)
    
    def save(self, items: List[ParsedItem], filename: str = None) -> Path:
        """
        Save items to Excel file.
        
        Args:
            items: List of parsed items
            filename: Custom filename
        
        Returns:
            Path to saved file
        """
        if not items:
            self.logger.warning("No items to save to Excel")
            return None
        
        # Generate filename
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data_{timestamp}.xlsx"
        
        if not filename.endswith('.xlsx'):
            filename += '.xlsx'
        
        file_path = self.output_dir / filename
        
        try:
            # Convert items to DataFrame
            data = []
            for item in items:
                row = item.data.copy()
                row.update({
                    'source_url': item.source_url,
                    'parsed_at': item.parsed_at.isoformat(),
                    'confidence_score': item.confidence_score
                })
                data.append(row)
            
            df = pd.DataFrame(data)
            
            # Save to Excel
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Data')
                
                # Add summary sheet
                summary_data = {
                    'Metric': ['Total Records', 'Average Confidence', 'Unique Sources'],
                    'Value': [
                        len(items),
                        sum(item.confidence_score for item in items) / len(items),
                        len(set(item.source_url for item in items))
                    ]
                }
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, index=False, sheet_name='Summary')
            
            self.logger.info(f"Saved {len(items)} items to Excel: {file_path}")
            return file_path
        
        except Exception as e:
            self.logger.error(f"Failed to save Excel: {e}")
            raise


class JSONStorage:
    """JSON file storage handler."""
    
    def __init__(self, output_dir: Path = None):
        self.logger = get_logger('json_storage')
        self.output_dir = output_dir or Path(__file__).parent.parent.parent / "output"
        self.output_dir.mkdir(exist_ok=True)
    
    def save(self, items: List[ParsedItem], filename: str = None) -> Path:
        """
        Save items to JSON file.
        
        Args:
            items: List of parsed items
            filename: Custom filename
        
        Returns:
            Path to saved file
        """
        if not items:
            self.logger.warning("No items to save to JSON")
            return None
        
        # Generate filename
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data_{timestamp}.json"
        
        if not filename.endswith('.json'):
            filename += '.json'
        
        file_path = self.output_dir / filename
        
        try:
            # Convert items to serializable format
            data = {
                'metadata': {
                    'total_items': len(items),
                    'exported_at': datetime.now().isoformat(),
                    'confidence_avg': sum(item.confidence_score for item in items) / len(items),
                    'sources': list(set(item.source_url for item in items))
                },
                'items': []
            }
            
            for item in items:
                item_dict = {
                    'data': item.data,
                    'source_url': item.source_url,
                    'parsed_at': item.parsed_at.isoformat(),
                    'confidence_score': item.confidence_score
                }
                data['items'].append(item_dict)
            
            # Save to JSON
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Saved {len(items)} items to JSON: {file_path}")
            return file_path
        
        except Exception as e:
            self.logger.error(f"Failed to save JSON: {e}")
            raise


class SQLiteStorage:
    """SQLite database storage handler."""
    
    def __init__(self, db_path: Path = None):
        self.logger = get_logger('sqlite_storage')
        self.db_path = db_path or Path(__file__).parent.parent.parent / "data" / 'scraper_data.db'
        self.db_path.parent.mkdir(exist_ok=True)
        
        # Initialize database
        self._init_database()
    
    def _init_database(self):
        """Initialize database tables."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create main data table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS scraped_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        data_hash TEXT UNIQUE,
                        source_url TEXT,
                        parsed_at TEXT,
                        confidence_score REAL,
                        data_json TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create indexes
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_source_url ON scraped_data(source_url)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_parsed_at ON scraped_data(parsed_at)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_data_hash ON scraped_data(data_hash)')
                
                conn.commit()
        
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            raise
    
    def save(self, items: List[ParsedItem]) -> StorageStats:
        """
        Save items to SQLite database.
        
        Args:
            items: List of parsed items
        
        Returns:
            Storage statistics
        """
        start_time = datetime.now()
        stats = StorageStats(
            records_processed=len(items),
            records_inserted=0,
            records_updated=0,
            records_skipped=0,
            duplicates_found=0,
            processing_time=0.0
        )
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for item in items:
                    # Generate data hash
                    data_hash = hashlib.sha256(
                        json.dumps(item.data, sort_keys=True, default=str).encode()
                    ).hexdigest()
                    
                    # Check if already exists
                    cursor.execute(
                        'SELECT id FROM scraped_data WHERE data_hash = ?',
                        (data_hash,)
                    )
                    existing = cursor.fetchone()
                    
                    if existing:
                        stats.duplicates_found += 1
                        stats.records_skipped += 1
                        continue
                    
                    # Insert new record
                    cursor.execute('''
                        INSERT INTO scraped_data 
                        (data_hash, source_url, parsed_at, confidence_score, data_json)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        data_hash,
                        item.source_url,
                        item.parsed_at.isoformat(),
                        item.confidence_score,
                        json.dumps(item.data, default=str)
                    ))
                    
                    stats.records_inserted += 1
                
                conn.commit()
        
        except Exception as e:
            self.logger.error(f"Failed to save to database: {e}")
            raise
        
        finally:
            stats.processing_time = (datetime.now() - start_time).total_seconds()
        
        self.logger.info(f"Saved {stats.records_inserted} items to database in {stats.processing_time:.2f}s")
        return stats
    
    def load(self, limit: int = None, source_url: str = None) -> List[ParsedItem]:
        """
        Load items from database.
        
        Args:
            limit: Maximum number of items to load
            source_url: Filter by source URL
        
        Returns:
            List of parsed items
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = 'SELECT data_json, source_url, parsed_at, confidence_score FROM scraped_data'
                params = []
                
                if source_url:
                    query += ' WHERE source_url = ?'
                    params.append(source_url)
                
                query += ' ORDER BY created_at DESC'
                
                if limit:
                    query += ' LIMIT ?'
                    params.append(limit)
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                items = []
                for row in rows:
                    data_json, source_url, parsed_at, confidence_score = row
                    
                    item = ParsedItem(
                        data=json.loads(data_json),
                        source_url=source_url,
                        parsed_at=datetime.fromisoformat(parsed_at),
                        confidence_score=confidence_score
                    )
                    items.append(item)
                
                self.logger.info(f"Loaded {len(items)} items from database")
                return items
        
        except Exception as e:
            self.logger.error(f"Failed to load from database: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total records
                cursor.execute('SELECT COUNT(*) FROM scraped_data')
                total_records = cursor.fetchone()[0]
                
                # Unique sources
                cursor.execute('SELECT COUNT(DISTINCT source_url) FROM scraped_data')
                unique_sources = cursor.fetchone()[0]
                
                # Average confidence
                cursor.execute('SELECT AVG(confidence_score) FROM scraped_data')
                avg_confidence = cursor.fetchone()[0] or 0
                
                # Date range
                cursor.execute('SELECT MIN(parsed_at), MAX(parsed_at) FROM scraped_data')
                date_range = cursor.fetchone()
                
                return {
                    'total_records': total_records,
                    'unique_sources': unique_sources,
                    'average_confidence': avg_confidence,
                    'date_range': date_range,
                    'database_size': self.db_path.stat().st_size
                }
        
        except Exception as e:
            self.logger.error(f"Failed to get database stats: {e}")
            return {}


class AdvancedStorageManager:
    """
    Advanced storage manager supporting multiple formats and automatic deduplication.
    """
    
    def __init__(self, output_dir: Path = None):
        self.logger = get_logger('storage_manager')
        self.output_dir = output_dir or Path(__file__).parent.parent.parent / "output"
        self.deduplicator = DataDeduplicator()
        
        # Initialize storage handlers
        self.csv_storage = CSVStorage(self.output_dir)
        self.excel_storage = ExcelStorage(self.output_dir)
        self.json_storage = JSONStorage(self.output_dir)
        self.sqlite_storage = SQLiteStorage()
        
        # Statistics
        self.stats = {
            'total_saved': 0,
            'total_duplicates': 0,
            'storage_operations': 0
        }
    
    def save_items(self, items: List[ParsedItem], formats: List[str] = None, 
                   filename: str = None, remove_duplicates: bool = True) -> Dict[str, Any]:
        """
        Save items to multiple formats.
        
        Args:
            items: List of parsed items
            formats: List of formats to save (csv, excel, json, sqlite)
            filename: Custom filename (for file-based formats)
            remove_duplicates: Whether to remove duplicates
        
        Returns:
            Results dictionary with file paths and statistics
        """
        if not items:
            self.logger.warning("No items to save")
            return {'saved_files': [], 'stats': {}}
        
        start_time = datetime.now()
        results = {'saved_files': [], 'stats': {}}
        
        # Remove duplicates if enabled
        if remove_duplicates:
            original_count = len(items)
            items = self.deduplicator.remove_duplicates([item.data for item in items])
            duplicates_removed = original_count - len(items)
            
            # Recreate ParsedItem objects
            parsed_items = []
            for i, item_data in enumerate(items):
                if i < len(items):
                    parsed_items.append(ParsedItem(
                        data=item_data,
                        source_url=items[i].get('source_url', ''),
                        parsed_at=datetime.now(),
                        confidence_score=1.0
                    ))
            items = parsed_items
            
            self.stats['total_duplicates'] += duplicates_removed
        else:
            parsed_items = items
        
        # Use default formats if none specified
        if not formats:
            formats = CONFIG.DEFAULT_FORMATS
        
        # Save to each format
        for format_type in formats:
            try:
                if format_type == 'csv':
                    file_path = self.csv_storage.save(parsed_items, filename)
                    if file_path:
                        results['saved_files'].append(str(file_path))
                
                elif format_type == 'excel':
                    file_path = self.excel_storage.save(parsed_items, filename)
                    if file_path:
                        results['saved_files'].append(str(file_path))
                
                elif format_type == 'json':
                    file_path = self.json_storage.save(parsed_items, filename)
                    if file_path:
                        results['saved_files'].append(str(file_path))
                
                elif format_type == 'sqlite':
                    db_stats = self.sqlite_storage.save(parsed_items)
                    results['stats']['database'] = db_stats
                
                else:
                    self.logger.warning(f"Unsupported format: {format_type}")
            
            except Exception as e:
                self.logger.error(f"Failed to save to {format_type}: {e}")
        
        # Update statistics
        processing_time = (datetime.now() - start_time).total_seconds()
        self.stats['total_saved'] += len(parsed_items)
        self.stats['storage_operations'] += 1
        
        results['stats'] = {
            'items_saved': len(parsed_items),
            'duplicates_removed': duplicates_removed if remove_duplicates else 0,
            'processing_time': processing_time,
            'formats_used': formats
        }
        
        self.logger.info(f"Saved {len(parsed_items)} items to {len(results['saved_files'])} files")
        return results
    
    def load_items(self, format_type: str, file_path: Path = None) -> List[ParsedItem]:
        """
        Load items from storage.
        
        Args:
            format_type: Storage format
            file_path: Path to file (for file-based formats)
        
        Returns:
            List of parsed items
        """
        try:
            if format_type == 'csv':
                return self.csv_storage.load(file_path)
            elif format_type == 'sqlite':
                return self.sqlite_storage.load()
            else:
                self.logger.error(f"Loading not supported for format: {format_type}")
                return []
        
        except Exception as e:
            self.logger.error(f"Failed to load from {format_type}: {e}")
            return []
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        db_stats = self.sqlite_storage.get_stats()
        
        return {
            'storage_stats': self.stats,
            'database_stats': db_stats,
            'output_directory': str(self.output_dir)
        }

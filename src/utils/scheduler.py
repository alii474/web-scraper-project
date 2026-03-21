"""
Scheduling Module for Automated Scraping

Provides scheduling functionality with the schedule library.
Supports multiple schedule patterns and error handling.
"""

import schedule
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
import json
from pathlib import Path

from ..utils.logger import get_logger
from ..utils.config import CONFIG


class ScrapingJob:
    """Represents a scheduled scraping job."""
    
    def __init__(self, job_id: str, url: str, schedule_pattern: str, 
                 scraper_config: Dict[str, Any], max_runs: Optional[int] = None):
        """
        Initialize scraping job.
        
        Args:
            job_id: Unique job identifier
            url: URL to scrape
            schedule_pattern: Schedule pattern (e.g., "every 30 minutes")
            scraper_config: Scraper configuration
            max_runs: Maximum number of runs (None for infinite)
        """
        self.job_id = job_id
        self.url = url
        self.schedule_pattern = schedule_pattern
        self.scraper_config = scraper_config
        self.max_runs = max_runs
        
        # Runtime statistics
        self.run_count = 0
        self.success_count = 0
        self.error_count = 0
        self.last_run = None
        self.next_run = None
        self.created_at = datetime.now()
        self.is_active = True
        
        # Results storage
        self.run_history = []
    
    def should_run(self) -> bool:
        """Check if job should run based on max_runs limit."""
        if self.max_runs is None:
            return True
        return self.run_count < self.max_runs
    
    def record_run(self, success: bool, result: Dict[str, Any] = None, error: str = None):
        """
        Record a job run.
        
        Args:
            success: Whether the run was successful
            result: Run result (if successful)
            error: Error message (if failed)
        """
        self.run_count += 1
        self.last_run = datetime.now()
        
        if success:
            self.success_count += 1
        else:
            self.error_count += 1
        
        # Store in history
        run_record = {
            'run_number': self.run_count,
            'timestamp': self.last_run.isoformat(),
            'success': success,
            'result': result,
            'error': error
        }
        
        self.run_history.append(run_record)
        
        # Keep only last 100 runs
        if len(self.run_history) > 100:
            self.run_history = self.run_history[-100:]
    
    def get_success_rate(self) -> float:
        """Get success rate as percentage."""
        if self.run_count == 0:
            return 0.0
        return (self.success_count / self.run_count) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary for serialization."""
        return {
            'job_id': self.job_id,
            'url': self.url,
            'schedule_pattern': self.schedule_pattern,
            'scraper_config': self.scraper_config,
            'max_runs': self.max_runs,
            'run_count': self.run_count,
            'success_count': self.success_count,
            'error_count': self.error_count,
            'success_rate': self.get_success_rate(),
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'next_run': self.next_run.isoformat() if self.next_run else None,
            'created_at': self.created_at.isoformat(),
            'is_active': self.is_active
        }


class ScrapingScheduler:
    """
    Advanced scheduler for automated web scraping.
    
    Features:
    - Multiple schedule patterns
    - Job management
    - Error handling
    - Statistics tracking
    - Persistent storage
    """
    
    def __init__(self):
        self.logger = get_logger('scheduler')
        self.jobs: Dict[str, ScrapingJob] = {}
        self.running = False
        self.scheduler_thread = None
        
        # Storage for job persistence
        self.jobs_file = Path(__file__).parent.parent.parent / "config" / "scheduled_jobs.json"
        
        # Load existing jobs
        self.load_jobs()
    
    def add_job(self, url: str, schedule_pattern: str, 
                scraper_config: Dict[str, Any] = None, 
                max_runs: Optional[int] = None,
                job_id: str = None) -> str:
        """
        Add a new scheduled scraping job.
        
        Args:
            url: URL to scrape
            schedule_pattern: Schedule pattern (e.g., "every 30 minutes")
            scraper_config: Scraper configuration
            max_runs: Maximum number of runs
            job_id: Custom job ID (auto-generated if None)
        
        Returns:
            Job ID
        """
        if job_id is None:
            job_id = f"job_{int(time.time())}_{len(self.jobs)}"
        
        if job_id in self.jobs:
            raise ValueError(f"Job with ID '{job_id}' already exists")
        
        # Default scraper config
        if scraper_config is None:
            scraper_config = {
                'max_pages': CONFIG.DEFAULT_MAX_PAGES,
                'formats': CONFIG.DEFAULT_FORMATS,
                'rate_limit': 1.0
            }
        
        # Create job
        job = ScrapingJob(job_id, url, schedule_pattern, scraper_config, max_runs)
        self.jobs[job_id] = job
        
        # Schedule the job
        self._schedule_job(job)
        
        # Save jobs
        self.save_jobs()
        
        self.logger.info(f"Added scheduled job: {job_id} for {url} ({schedule_pattern})")
        return job_id
    
    def _schedule_job(self, job: ScrapingJob):
        """Schedule a job using the schedule library."""
        # Parse schedule pattern and set up schedule
        pattern = job.schedule_pattern.lower()
        
        if pattern.startswith('every'):
            # Extract interval and unit
            parts = pattern.split()
            if len(parts) >= 3:
                interval = int(parts[1])
                unit = parts[2]
                
                if unit.startswith('minute'):
                    schedule.every(interval).minutes.do(self._run_job, job.job_id)
                elif unit.startswith('hour'):
                    schedule.every(interval).hours.do(self._run_job, job.job_id)
                elif unit.startswith('day'):
                    schedule.every(interval).days.do(self._run_job, job.job_id)
                else:
                    raise ValueError(f"Unsupported time unit: {unit}")
            else:
                raise ValueError(f"Invalid schedule pattern: {pattern}")
        
        elif pattern.startswith('daily'):
            # Daily at specific time
            if 'at' in pattern:
                time_part = pattern.split('at')[1].strip()
                schedule.every().day.at(time_part).do(self._run_job, job.job_id)
            else:
                schedule.every().day.do(self._run_job, job.job_id)
        
        elif pattern.startswith('weekly'):
            # Weekly on specific day
            if 'on' in pattern:
                day_part = pattern.split('on')[1].strip()
                day_map = {
                    'monday': schedule.every().monday,
                    'tuesday': schedule.every().tuesday,
                    'wednesday': schedule.every().wednesday,
                    'thursday': schedule.every().thursday,
                    'friday': schedule.every().friday,
                    'saturday': schedule.every().saturday,
                    'sunday': schedule.every().sunday
                }
                
                day_name = day_part.lower()
                if day_name in day_map:
                    day_map[day_name].do(self._run_job, job.job_id)
                else:
                    raise ValueError(f"Invalid day: {day_name}")
            else:
                schedule.every().week.do(self._run_job, job.job_id)
        
        else:
            raise ValueError(f"Unsupported schedule pattern: {pattern}")
        
        self.logger.info(f"Scheduled job {job.job_id}: {pattern}")
    
    def _run_job(self, job_id: str):
        """
        Execute a scheduled job.
        
        Args:
            job_id: Job ID to run
        """
        # Import here to avoid circular import
        from ..core.scraper import AdvancedWebScraper
        
        if job_id not in self.jobs:
            self.logger.error(f"Job not found: {job_id}")
            return
        
        job = self.jobs[job_id]
        
        if not job.is_active or not job.should_run():
            self.logger.info(f"Skipping job {job_id}: inactive or max runs reached")
            return
        
        self.logger.info(f"Running scheduled job: {job_id}")
        
        try:
            # Initialize scraper
            scraper = AdvancedWebScraper(**job.scraper_config)
            
            # Run scraping
            result = scraper.scrape_url(
                job.url,
                max_pages=job.scraper_config.get('max_pages', CONFIG.DEFAULT_MAX_PAGES),
                formats=job.scraper_config.get('formats', CONFIG.DEFAULT_FORMATS)
            )
            
            # Record successful run
            job.record_run(success=True, result=result)
            
            self.logger.info(f"Job {job_id} completed successfully: "
                           f"{result['items_scraped']} items scraped")
            
            # Cleanup
            scraper.close()
        
        except Exception as e:
            # Record failed run
            job.record_run(success=False, error=str(e))
            self.logger.error(f"Job {job_id} failed: {e}")
        
        finally:
            # Update next run time
            job.next_run = self._get_next_run_time(job)
            
            # Save jobs
            self.save_jobs()
    
    def _get_next_run_time(self, job: ScrapingJob) -> Optional[datetime]:
        """Get next scheduled run time for a job."""
        # This is a simplified implementation
        # In practice, you'd need to integrate with schedule library's internal timing
        if job.should_run():
            return datetime.now() + timedelta(minutes=30)  # Default to 30 minutes
        return None
    
    def remove_job(self, job_id: str) -> bool:
        """
        Remove a scheduled job.
        
        Args:
            job_id: Job ID to remove
        
        Returns:
            True if job was removed
        """
        if job_id not in self.jobs:
            return False
        
        # Cancel the job (schedule library doesn't have direct cancel method)
        # This is a limitation - in practice, you might need to track jobs differently
        del self.jobs[job_id]
        
        # Save jobs
        self.save_jobs()
        
        self.logger.info(f"Removed scheduled job: {job_id}")
        return True
    
    def pause_job(self, job_id: str) -> bool:
        """
        Pause a scheduled job.
        
        Args:
            job_id: Job ID to pause
        
        Returns:
            True if job was paused
        """
        if job_id not in self.jobs:
            return False
        
        self.jobs[job_id].is_active = False
        self.save_jobs()
        
        self.logger.info(f"Paused scheduled job: {job_id}")
        return True
    
    def resume_job(self, job_id: str) -> bool:
        """
        Resume a paused scheduled job.
        
        Args:
            job_id: Job ID to resume
        
        Returns:
            True if job was resumed
        """
        if job_id not in self.jobs:
            return False
        
        self.jobs[job_id].is_active = True
        self.save_jobs()
        
        self.logger.info(f"Resumed scheduled job: {job_id}")
        return True
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of a specific job.
        
        Args:
            job_id: Job ID
        
        Returns:
            Job status dictionary
        """
        if job_id not in self.jobs:
            return None
        
        return self.jobs[job_id].to_dict()
    
    def get_all_jobs(self) -> List[Dict[str, Any]]:
        """Get status of all jobs."""
        return [job.to_dict() for job in self.jobs.values()]
    
    def get_job_history(self, job_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get run history for a job.
        
        Args:
            job_id: Job ID
            limit: Maximum number of records to return
        
        Returns:
            List of run records
        """
        if job_id not in self.jobs:
            return []
        
        return self.jobs[job_id].run_history[-limit:]
    
    def start(self):
        """Start the scheduler."""
        if self.running:
            self.logger.warning("Scheduler is already running")
            return
        
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        self.logger.info("Scheduler started")
    
    def stop(self):
        """Stop the scheduler."""
        if not self.running:
            self.logger.warning("Scheduler is not running")
            return
        
        self.running = False
        
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        
        self.logger.info("Scheduler stopped")
    
    def _run_scheduler(self):
        """Main scheduler loop."""
        self.logger.info("Scheduler thread started")
        
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(1)  # Check every second
            except Exception as e:
                self.logger.error(f"Scheduler error: {e}")
                time.sleep(5)  # Wait longer on error
    
    def save_jobs(self):
        """Save jobs to file for persistence."""
        try:
            jobs_data = {
                'jobs': [job.to_dict() for job in self.jobs.values()],
                'saved_at': datetime.now().isoformat()
            }
            
            with open(self.jobs_file, 'w') as f:
                json.dump(jobs_data, f, indent=2)
        
        except Exception as e:
            self.logger.error(f"Failed to save jobs: {e}")
    
    def load_jobs(self):
        """Load jobs from file."""
        try:
            if not self.jobs_file.exists():
                return
            
            with open(self.jobs_file, 'r') as f:
                jobs_data = json.load(f)
            
            for job_dict in jobs_data.get('jobs', []):
                # Reconstruct job object
                job = ScrapingJob(
                    job_id=job_dict['job_id'],
                    url=job_dict['url'],
                    schedule_pattern=job_dict['schedule_pattern'],
                    scraper_config=job_dict['scraper_config'],
                    max_runs=job_dict['max_runs']
                )
                
                # Restore runtime data
                job.run_count = job_dict['run_count']
                job.success_count = job_dict['success_count']
                job.error_count = job_dict['error_count']
                job.created_at = datetime.fromisoformat(job_dict['created_at'])
                job.is_active = job_dict['is_active']
                
                if job_dict['last_run']:
                    job.last_run = datetime.fromisoformat(job_dict['last_run'])
                
                if job_dict['next_run']:
                    job.next_run = datetime.fromisoformat(job_dict['next_run'])
                
                self.jobs[job.job_id] = job
                
                # Reschedule the job
                if job.is_active and job.should_run():
                    self._schedule_job(job)
            
            self.logger.info(f"Loaded {len(self.jobs)} scheduled jobs")
        
        except Exception as e:
            self.logger.error(f"Failed to load jobs: {e}")
    
    def get_scheduler_stats(self) -> Dict[str, Any]:
        """Get scheduler statistics."""
        total_jobs = len(self.jobs)
        active_jobs = sum(1 for job in self.jobs.values() if job.is_active)
        total_runs = sum(job.run_count for job in self.jobs.values())
        total_success = sum(job.success_count for job in self.jobs.values())
        
        return {
            'total_jobs': total_jobs,
            'active_jobs': active_jobs,
            'inactive_jobs': total_jobs - active_jobs,
            'total_runs': total_runs,
            'total_success': total_success,
            'total_errors': total_runs - total_success,
            'overall_success_rate': (total_success / total_runs * 100) if total_runs > 0 else 0,
            'scheduler_running': self.running
        }


# Global scheduler instance
scheduler = ScrapingScheduler()


def schedule_scraping(url: str, pattern: str, **kwargs) -> str:
    """
    Convenience function to schedule scraping.
    
    Args:
        url: URL to scrape
        pattern: Schedule pattern
        **kwargs: Additional job configuration
    
    Returns:
        Job ID
    """
    return scheduler.add_job(url, pattern, **kwargs)


def start_scheduler():
    """Start the global scheduler."""
    scheduler.start()


def stop_scheduler():
    """Stop the global scheduler."""
    scheduler.stop()

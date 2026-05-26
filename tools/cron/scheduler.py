"""
LEGIONGASPER v2.0 - Cron Scheduler Tool
OpenClaw-compatible scheduled workflows
Coded by DEATH LEGION Team (DEMO X HEXA)
"""

import asyncio
import schedule
import time
from typing import Callable, Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from threading import Thread
import uuid

@dataclass
class ScheduledJob:
    """Scheduled job definition"""
    id: str
    name: str
    schedule: str  # cron-like expression
    task: Callable
    enabled: bool = True
    last_run: Optional[str] = None
    next_run: Optional[str] = None
    run_count: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

class CronScheduler:
    """Workflow scheduler with cron-like syntax"""
    
    def __init__(self):
        self.jobs: Dict[str, ScheduledJob] = {}
        self._running = False
        self._thread: Optional[Thread] = None
        
    def add_job(self, name: str, schedule_expr: str, 
                task: Callable, enabled: bool = True) -> str:
        """Add a scheduled job
        
        Schedule expressions:
        - "every 10 minutes"
        - "every hour"
        - "every day at 10:30"
        - "monday at 09:00"
        """
        job_id = str(uuid.uuid4())[:8]
        
        job = ScheduledJob(
            id=job_id,
            name=name,
            schedule=schedule_expr,
            task=task,
            enabled=enabled
        )
        
        self.jobs[job_id] = job
        
        if enabled:
            self._schedule_job(job)
        
        return job_id
    
    def _schedule_job(self, job: ScheduledJob):
        """Parse schedule expression and add to scheduler"""
        expr = job.schedule.lower()
        
        try:
            if "every" in expr:
                if "minute" in expr:
                    minutes = int(expr.split()[1]) if len(expr.split()) > 1 else 1
                    schedule.every(minutes).minutes.do(self._run_job, job.id)
                elif "hour" in expr:
                    hours = int(expr.split()[1]) if len(expr.split()) > 1 else 1
                    schedule.every(hours).hours.do(self._run_job, job.id)
                elif "day" in expr:
                    if "at" in expr:
                        time_str = expr.split("at")[-1].strip()
                        schedule.every().day.at(time_str).do(self._run_job, job.id)
                    else:
                        schedule.every().day.do(self._run_job, job.id)
            elif "monday" in expr:
                time_str = expr.split("at")[-1].strip() if "at" in expr else "09:00"
                schedule.every().monday.at(time_str).do(self._run_job, job.id)
            elif "tuesday" in expr:
                time_str = expr.split("at")[-1].strip() if "at" in expr else "09:00"
                schedule.every().tuesday.at(time_str).do(self._run_job, job.id)
            elif "wednesday" in expr:
                time_str = expr.split("at")[-1].strip() if "at" in expr else "09:00"
                schedule.every().wednesday.at(time_str).do(self._run_job, job.id)
            elif "thursday" in expr:
                time_str = expr.split("at")[-1].strip() if "at" in expr else "09:00"
                schedule.every().thursday.at(time_str).do(self._run_job, job.id)
            elif "friday" in expr:
                time_str = expr.split("at")[-1].strip() if "at" in expr else "09:00"
                schedule.every().friday.at(time_str).do(self._run_job, job.id)
            elif "saturday" in expr:
                time_str = expr.split("at")[-1].strip() if "at" in expr else "09:00"
                schedule.every().saturday.at(time_str).do(self._run_job, job.id)
            elif "sunday" in expr:
                time_str = expr.split("at")[-1].strip() if "at" in expr else "09:00"
                schedule.every().sunday.at(time_str).do(self._run_job, job.id)
        except Exception as e:
            print(f"Error scheduling job {job.name}: {e}")
    
    def _run_job(self, job_id: str):
        """Execute scheduled job"""
        job = self.jobs.get(job_id)
        if not job or not job.enabled:
            return
        
        try:
            job.last_run = datetime.now().isoformat()
            job.run_count += 1
            
            if asyncio.iscoroutinefunction(job.task):
                asyncio.create_task(job.task())
            else:
                job.task()
        except Exception as e:
            print(f"Error running job {job.name}: {e}")
    
    def start(self):
        """Start scheduler in background thread"""
        if self._running:
            return
        
        self._running = True
        self._thread = Thread(target=self._run_scheduler, daemon=True)
        self._thread.start()
    
    def _run_scheduler(self):
        """Run scheduler loop"""
        while self._running:
            schedule.run_pending()
            time.sleep(1)
    
    def stop(self):
        """Stop scheduler"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
    
    def enable_job(self, job_id: str) -> bool:
        """Enable a job"""
        if job_id in self.jobs:
            self.jobs[job_id].enabled = True
            return True
        return False
    
    def disable_job(self, job_id: str) -> bool:
        """Disable a job"""
        if job_id in self.jobs:
            self.jobs[job_id].enabled = False
            return True
        return False
    
    def remove_job(self, job_id: str) -> bool:
        """Remove a job"""
        if job_id in self.jobs:
            del self.jobs[job_id]
            return True
        return False
    
    def list_jobs(self) -> List[Dict[str, Any]]:
        """List all jobs"""
        return [
            {
                "id": job.id,
                "name": job.name,
                "schedule": job.schedule,
                "enabled": job.enabled,
                "last_run": job.last_run,
                "run_count": job.run_count,
                "created_at": job.created_at
            }
            for job in self.jobs.values()
        ]

# Global scheduler instance
_default_scheduler = CronScheduler()

def schedule_job(name: str, schedule_expr: str, task: Callable, **kwargs) -> str:
    """Schedule a new job"""
    return _default_scheduler.add_job(name, schedule_expr, task, **kwargs)

def start_scheduler():
    """Start the scheduler"""
    _default_scheduler.start()

def stop_scheduler():
    """Stop the scheduler"""
    _default_scheduler.stop()

def list_jobs() -> List[Dict[str, Any]]:
    """List all scheduled jobs"""
    return _default_scheduler.list_jobs()

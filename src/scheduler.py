import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from checker_runner import run_all_active_checkers

scheduler = None

def start_scheduler():
    """Start the background scheduler for periodic checker execution"""
    global scheduler
    
    if scheduler is not None:
        return  # Already started
    
    scheduler = BackgroundScheduler()
    
    # Schedule checker execution every minute
    scheduler.add_job(
        func=run_all_active_checkers,
        trigger=IntervalTrigger(minutes=1),
        id='checker_execution',
        name='Execute CTF Checkers',
        replace_existing=True
    )
    
    scheduler.start()
    logging.info("Background scheduler started - checkers will run every minute")

def stop_scheduler():
    """Stop the background scheduler"""
    global scheduler
    if scheduler:
        scheduler.shutdown()
        scheduler = None
        logging.info("Background scheduler stopped")

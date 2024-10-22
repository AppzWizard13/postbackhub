from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from django.conf import settings
import logging
import requests
import atexit

logger = logging.getLogger(__name__)

def self_ping():
    try:
        response = requests.get('https://postback-hub.onrender.com/')
        logger.info(f"Health check response: {response.status_code}")
        print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>", response.status_code)
    except Exception as e:
        logger.error(f"Error in self_ping: {e}")
        print("--------------------------------------------------")

def start():
    scheduler = BackgroundScheduler()
    scheduler.add_job(self_ping, IntervalTrigger(seconds=60))  # Run every 3 seconds
    scheduler.start()
    logger.info("Scheduler started.")
    
    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())

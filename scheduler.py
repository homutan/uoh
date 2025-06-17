import logging
from apscheduler.schedulers.background import BackgroundScheduler
import requests

scheduler = BackgroundScheduler()


def force_update():
    _ = requests.post("http://localhost:5000/update")


def initialize_scheduler(logger: logging.Logger):
    logger.info("Intializing scheduler")
    _ = scheduler.add_job(func=force_update, trigger="interval", minutes=30)
    scheduler.start()


def shutdown_scheduler(logger: logging.Logger):
    logger.info("Stopping scheduler")
    if scheduler.running:
        scheduler.shutdown()

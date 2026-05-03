from flask_apscheduler import APScheduler
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from datetime import datetime
import logging

# Configure logger
logger = logging.getLogger(__name__)


class SchedulerConfig:
    """Configuration for APScheduler."""
    SCHEDULER_API_ENABLED = True
    SCHEDULER_TIMEZONE = "UTC"


scheduler = APScheduler()


def job_executed_listener(event):
    """Listener for successful job execution."""
    logger.info(f"[SCHEDULER EVENT] Job '{event.job_id}' executed successfully at {datetime.now()}")
    # Suppress redundant APScheduler success logs for polling as we now have custom brief logs
    if event.job_id != 'gateway_device_polling':
        print(f"[SCHEDULER EVENT] Job '{event.job_id}' executed successfully")


def job_error_listener(event):
    """Listener for job execution errors."""
    logger.error(f"[SCHEDULER EVENT] Job '{event.job_id}' failed at {datetime.now()}. Exception: {event.exception}")
    print(f"[SCHEDULER EVENT] Job '{event.job_id}' FAILED with exception: {event.exception}")


def init_scheduler(app):
    """
    Initialize and start the scheduler with the Flask app.
    
    Args:
        app: Flask application instance
    """
    app.config.from_object(SchedulerConfig())
    
    # Import scheduled tasks
    from esp32OTA.scheduled_tasks import register_scheduled_tasks
    
    # Initialize scheduler with app
    scheduler.init_app(app)
    
    # Register event listeners
    scheduler.add_listener(job_executed_listener, EVENT_JOB_EXECUTED)
    scheduler.add_listener(job_error_listener, EVENT_JOB_ERROR)
    logger.info("[SCHEDULER] Event listeners registered")
    print("[SCHEDULER] Event listeners registered for job monitoring")
    
    # Register all scheduled tasks
    register_scheduled_tasks(scheduler)
    
    # Start the scheduler
    scheduler.start()
    logger.info("[SCHEDULER] Scheduler started successfully")
    print("[SCHEDULER] Scheduler started successfully")
    
    # Manually trigger the gateway polling task immediately after start
    try:
        from esp32OTA.Services.GatewayService import GatewayService
        print("[SCHEDULER] Executing initial Gateway poll...")
        GatewayService.poll_devices()
    except Exception as e:
        logger.error(f"[SCHEDULER] Failed to run initial poll: {str(e)}")
    
    return scheduler

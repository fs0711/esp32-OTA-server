from flask_apscheduler import APScheduler
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from datetime import datetime
import logging
import os

# Configure logger
logger = logging.getLogger(__name__)


class SchedulerConfig:
    """Configuration for APScheduler with Redis jobstore."""
    SCHEDULER_API_ENABLED = True
    SCHEDULER_TIMEZONE = "UTC"
    
    # Redis configuration for distributed locking
    REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
    REDIS_DB = int(os.environ.get('REDIS_DB', 0))
    
    # Configure jobstores with Redis
    SCHEDULER_JOBSTORES = {
        'default': RedisJobStore(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB
        )
    }
    
    # Configure executors
    SCHEDULER_EXECUTORS = {
        'default': ThreadPoolExecutor(20)
    }
    
    # Job defaults to prevent duplicate execution
    SCHEDULER_JOB_DEFAULTS = {
        'coalesce': True,  # Combine multiple pending executions into one
        'max_instances': 1,  # Only one instance of each job can run at a time
        'misfire_grace_time': 30  # Grace time in seconds for late-running jobs
    }


scheduler = APScheduler()


def job_executed_listener(event):
    """Listener for successful job execution."""
    logger.info(f"[SCHEDULER EVENT] Job '{event.job_id}' executed successfully at {datetime.now()}")
    print(f"[SCHEDULER EVENT] Job '{event.job_id}' executed successfully")


def job_error_listener(event):
    """Listener for job execution errors."""
    logger.error(f"[SCHEDULER EVENT] Job '{event.job_id}' failed at {datetime.now()}. Exception: {event.exception}")
    print(f"[SCHEDULER EVENT] Job '{event.job_id}' FAILED with exception: {event.exception}")


def init_scheduler(app):
    """
    Initialize and start the scheduler with the Flask app using Redis for distributed locking.
    This prevents multiple Gunicorn workers from running the same scheduled tasks simultaneously.
    
    Args:
        app: Flask application instance
    """
    try:
        app.config.from_object(SchedulerConfig())
        
        logger.info(f"[SCHEDULER] Connecting to Redis at {SchedulerConfig.REDIS_HOST}:{SchedulerConfig.REDIS_PORT}")
        print(f"[SCHEDULER] Connecting to Redis at {SchedulerConfig.REDIS_HOST}:{SchedulerConfig.REDIS_PORT}")
        
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
        logger.info("[SCHEDULER] Scheduler started successfully with Redis jobstore")
        print("[SCHEDULER] Scheduler started successfully with Redis jobstore (preventing duplicate executions)")
        
        return scheduler
        
    except Exception as e:
        logger.error(f"[SCHEDULER] Failed to initialize scheduler: {str(e)}")
        print(f"[SCHEDULER] ERROR: Failed to initialize scheduler - {str(e)}")
        print("[SCHEDULER] Make sure Redis server is running: redis-server")
        raise

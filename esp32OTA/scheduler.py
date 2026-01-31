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
    SCHEDULER_EXECUTORS = { using Redis for distributed locking.
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
        raisepp):
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
    
    return scheduler

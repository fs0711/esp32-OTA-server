from flask_apscheduler import APScheduler


class SchedulerConfig:
    """Configuration for APScheduler."""
    SCHEDULER_API_ENABLED = True
    SCHEDULER_TIMEZONE = "UTC"


scheduler = APScheduler()


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
    
    # Register all scheduled tasks
    register_scheduled_tasks(scheduler)
    
    # Start the scheduler
    scheduler.start()
    
    return scheduler

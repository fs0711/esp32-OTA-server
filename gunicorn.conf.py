import os

# Set environment variable for the application
os.environ["APP_ENVIRONMENT"] = "STAGING"

bind = "unix:esp32ota.sock"
workers = 10
timeout = 300
accesslog = "/var/log/esp32ota/access.log"
errorlog = "/var/log/esp32ota/error.log"
umask = 7

# Post-fork hook to enable scheduler only in one worker
def post_fork(server, worker):
    """Enable scheduler only in worker 1 to prevent duplicate task execution."""
    if worker.age == 0:  # First worker spawned
        os.environ["SCHEDULER_ENABLED"] = "true"
        server.log.info(f"Scheduler ENABLED in worker {worker.pid}")
    else:
        os.environ["SCHEDULER_ENABLED"] = "false"
        server.log.info(f"Scheduler DISABLED in worker {worker.pid}")
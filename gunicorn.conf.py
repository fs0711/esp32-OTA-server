import os
import fcntl

# Set environment variable for the application
os.environ["APP_ENVIRONMENT"] = "STAGING"

bind = "unix:esp32ota.sock"
workers = 10
timeout = 300
accesslog = "/var/log/esp32ota/access.log"
errorlog = "/var/log/esp32ota/error.log"
umask = 7

# Lock file to ensure only one worker enables scheduler
SCHEDULER_LOCK_FILE = "/tmp/esp32ota_scheduler.lock"

# Pre-fork hook to clean up lock file on master start
def on_starting(server):
    """Clean up lock file when master process starts."""
    if os.path.exists(SCHEDULER_LOCK_FILE):
        os.remove(SCHEDULER_LOCK_FILE)
    server.log.info("Cleaned up scheduler lock file")

# Post-fork hook to enable scheduler only in one worker
def post_fork(server, worker):
    """Enable scheduler only in the first worker to prevent duplicate task execution."""
    try:
        # Try to create and lock the file exclusively
        lock_fd = os.open(SCHEDULER_LOCK_FILE, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        os.write(lock_fd, str(worker.pid).encode())
        os.close(lock_fd)
        
        # This worker got the lock - enable scheduler
        os.environ["SCHEDULER_ENABLED"] = "true"
        server.log.info(f"✓ Scheduler ENABLED in worker PID: {worker.pid}")
        
    except FileExistsError:
        # Lock file already exists - another worker has scheduler
        os.environ["SCHEDULER_ENABLED"] = "false"
        server.log.info(f"✗ Scheduler DISABLED in worker PID: {worker.pid}")
        
    except Exception as e:
        # Error occurred - disable scheduler to be safe
        os.environ["SCHEDULER_ENABLED"] = "false"
        server.log.error(f"Error in post_fork for worker {worker.pid}: {e}")
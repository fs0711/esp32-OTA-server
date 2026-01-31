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
WORKER_STATUS_FILE = "/tmp/esp32ota_workers.json"

# Pre-fork hook to clean up files on master start
def on_starting(server):
    """Clean up lock and status files when master process starts."""
    if os.path.exists(SCHEDULER_LOCK_FILE):
        os.remove(SCHEDULER_LOCK_FILE)
    if os.path.exists(WORKER_STATUS_FILE):
        os.remove(WORKER_STATUS_FILE)
    server.log.info("Cleaned up scheduler lock and worker status files")

# Post-fork hook to enable scheduler only in one worker
def post_fork(server, worker):
    """Enable scheduler only in the first worker to prevent duplicate task execution."""
    import json
    from datetime import datetime
    
    scheduler_enabled = False
    
    try:
        # Try to create and lock the file exclusively
        lock_fd = os.open(SCHEDULER_LOCK_FILE, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        os.write(lock_fd, str(worker.pid).encode())
        os.close(lock_fd)
        
        # This worker got the lock - enable scheduler
        os.environ["SCHEDULER_ENABLED"] = "true"
        scheduler_enabled = True
        server.log.info(f"✓ Scheduler ENABLED in worker PID: {worker.pid}")
        
    except FileExistsError:
        # Lock file already exists - another worker has scheduler
        os.environ["SCHEDULER_ENABLED"] = "false"
        server.log.info(f"✗ Scheduler DISABLED in worker PID: {worker.pid}")
        
    except Exception as e:
        # Error occurred - disable scheduler to be safe
        os.environ["SCHEDULER_ENABLED"] = "false"
        server.log.error(f"Error in post_fork for worker {worker.pid}: {e}")
    
    # Write worker status to JSON file
    try:
        workers_data = {}
        if os.path.exists(WORKER_STATUS_FILE):
            with open(WORKER_STATUS_FILE, 'r') as f:
                workers_data = json.load(f)
        
        workers_data[str(worker.pid)] = {
            'pid': worker.pid,
            'scheduler_enabled': scheduler_enabled,
            'started_at': datetime.now().isoformat()
        }
        
        with open(WORKER_STATUS_FILE, 'w') as f:
            json.dump(workers_data, f, indent=2)
            
    except Exception as e:
        server.log.error(f"Failed to write worker status: {e}")
# Framework imports
from flask import Flask, jsonify
from flask_moment import Moment
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_mail import Mail
# Local imports
from esp32OTA.generic.database import initialize_db
from esp32OTA.config import config


def register_scripts():
    from esp32OTA.scripts import run_scripts
    run_scripts(execute_create_admin_user_if_not_exists=True)
    # Routing
    import esp32OTA.urls


# application objects
app = Flask(__name__)
CORS(app)
app.config["MONGODB_HOST"] = config.MONGO_DB_URI
app.config["UPLOAD_FOLDER"] = config.upload_files_path
initialize_db(app)
moment = Moment(app)
bcrypt = Bcrypt(app)
app.config.update(config.MAIL_SETTINGS)
mail = Mail(app)
register_scripts()

# Initialize scheduler for background tasks (only in designated worker)
import os
from esp32OTA.scheduler import init_scheduler, scheduler

if os.environ.get('SCHEDULER_ENABLED', 'false').lower() == 'true':
    init_scheduler(app)
    print(f"[SCHEDULER] Initialized in worker PID: {os.getpid()}")
else:
    print(f"[SCHEDULER] Skipped initialization in worker PID: {os.getpid()}")

# Scheduler status endpoint
@app.route('/scheduler/status', methods=['GET'])
def scheduler_status():
    """Get the current status of the scheduler and all scheduled jobs."""
    import os
    import json
    from datetime import datetime
    
    current_worker_pid = os.getpid()
    scheduler_enabled_here = os.environ.get('SCHEDULER_ENABLED', 'false').lower() == 'true'
    
    # Read all workers status from file
    workers_status = []
    worker_status_file = '/tmp/esp32ota_workers.json'
    
    try:
        if os.path.exists(worker_status_file):
            with open(worker_status_file, 'r') as f:
                workers_data = json.load(f)
                for pid, info in workers_data.items():
                    workers_status.append({
                        'pid': info['pid'],
                        'scheduler_enabled': info['scheduler_enabled'],
                        'started_at': info['started_at'],
                        'is_current_worker': info['pid'] == current_worker_pid
                    })
    except Exception as e:
        pass  # Continue even if reading fails
    
    # Get scheduler jobs info if this worker has scheduler enabled
    jobs_info = []
    scheduler_info = None
    
    if scheduler_enabled_here:
        try:
            jobs = scheduler.get_jobs()
            for job in jobs:
                jobs_info.append({
                    'id': job.id,
                    'name': job.name,
                    'next_run_time': str(job.next_run_time) if job.next_run_time else None,
                    'trigger': str(job.trigger),
                    'pending': job.pending
                })
            
            scheduler_info = {
                'running': scheduler.running,
                'state': scheduler.state,
                'total_jobs': len(jobs),
                'jobs': jobs_info
            }
        except Exception as e:
            scheduler_info = {'error': str(e)}
    
    return jsonify({
        'status': 'success',
        'current_worker_pid': current_worker_pid,
        'scheduler_enabled_in_current_worker': scheduler_enabled_here,
        'total_workers': len(workers_status),
        'workers': sorted(workers_status, key=lambda x: x['pid']),
        'scheduler': scheduler_info
    }), 200
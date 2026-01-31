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
    
    if os.environ.get('SCHEDULER_ENABLED', 'false').lower() != 'true':
        return jsonify({
            'status': 'info',
            'message': 'Scheduler not initialized in this worker',
            'worker_pid': os.getpid(),
            'scheduler_enabled': False
        }), 200
    
    try:
        jobs = scheduler.get_jobs()
        jobs_info = []
        for job in jobs:
            jobs_info.append({
                'id': job.id,
                'name': job.name,
                'next_run_time': str(job.next_run_time) if job.next_run_time else None,
                'trigger': str(job.trigger),
                'pending': job.pending
            })
        
        return jsonify({
            'status': 'success',
            'worker_pid': os.getpid(),
            'scheduler_enabled': True,
            'scheduler_running': scheduler.running,
            'scheduler_state': scheduler.state,
            'total_jobs': len(jobs),
            'jobs': jobs_info
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'worker_pid': os.getpid()
        }), 500
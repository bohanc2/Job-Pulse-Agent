"""
Ascendo AI Community Jobs - Main Application
Provides intelligent job aggregation service for field service community
"""

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from models.database import init_db, get_jobs, add_job_source, get_job_sources, get_refresh_status, delete_job_source
from data_collectors.collector_manager import CollectorManager
from scheduler import SchedulerManager
from ai_service import AIService

load_dotenv()

app = Flask(__name__)
CORS(app)

# Initialize components
init_db()
collector_manager = CollectorManager()
scheduler = SchedulerManager(collector_manager)
ai_service = AIService(os.getenv('OPENAI_API_KEY'))

# Auto-initialize default data source if none exists and Adzuna credentials are available
def initialize_default_source():
    """Initialize default Adzuna API source if no sources exist
    
    Returns:
        bool: True if a new source was created, False otherwise
    """
    sources = get_job_sources()
    if len(sources) == 0:
        # Check if Adzuna credentials are available
        adzuna_app_id = os.getenv('ADZUNA_APP_ID')
        adzuna_app_key = os.getenv('ADZUNA_APP_KEY')
        
        if adzuna_app_id and adzuna_app_key:
            try:
                # Check if keyword rotation is enabled
                use_keyword_rotation = os.getenv('ADZUNA_USE_KEYWORD_ROTATION', 'true').lower() == 'true'
                
                if use_keyword_rotation:
                    # Create a single "all" source - scheduler will handle keyword rotation
                    print("No data sources found. Creating default Adzuna API source with keyword rotation enabled...")
                    add_job_source('api', 'all', 'Adzuna - All Jobs (Keyword Rotation)')
                    print("Default Adzuna API source created successfully with keyword rotation")
                else:
                    # Create a default Adzuna API source to fetch all jobs
                    print("No data sources found. Creating default Adzuna API source...")
                    add_job_source('api', 'all', 'Adzuna - All Jobs')
                    print("Default Adzuna API source created successfully")
                return True
            except Exception as e:
                print(f"Warning: Could not create default data source: {e}")
                return False
        else:
            print("Warning: No data sources found and Adzuna credentials not configured.")
            print("Please add data sources via Admin Settings or set ADZUNA_APP_ID and ADZUNA_APP_KEY environment variables.")
            return False
    return False

# Initialize default source on startup
new_source_created = initialize_default_source()

# Start scheduler for production (gunicorn) environment
# Check if we're running under gunicorn (production) or directly (development)
# In production, gunicorn will import this module, so we need to start scheduler here
# Note: For multi-worker setups, each worker will have its own scheduler instance
# This is acceptable as APScheduler BackgroundScheduler is thread-safe per process
if not scheduler.scheduler.running:
    try:
        scheduler.start()
        print("Scheduler started")
        
        # Trigger initial data collection immediately if sources exist
        # This ensures data is available right after deployment
        import threading
        import time
        
        def trigger_initial_collection():
            """Trigger initial collection after a short delay to allow app to fully start"""
            # Wait a bit for database and app to be ready
            time.sleep(5)
            sources = get_job_sources()
            if len(sources) > 0:
                print("Starting initial data collection from configured sources...")
                print(f"Found {len(sources)} data source(s) to collect from")
                try:
                    total = collector_manager.collect_all()
                    print(f"Initial data collection completed. Collected {total} jobs in total")
                except Exception as e:
                    print(f"Initial data collection failed: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print("No data sources found. Skipping initial collection.")
        
        # Always trigger initial collection in background thread
        # This works for both production and development
        thread = threading.Thread(target=trigger_initial_collection, daemon=True)
        thread.start()
        print("Initial data collection thread started (will execute in 5 seconds)")
    except Exception as e:
        print(f"Warning: Could not start scheduler: {e}")
        import traceback
        traceback.print_exc()

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/api/jobs')
def api_jobs():
    """Get jobs list API"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search', '', type=str)
    location = request.args.get('location', '', type=str)
    level = request.args.get('level', '', type=str)  # entry, mid, senior
    pay = request.args.get('pay', '', type=str)  # minimum salary threshold
    
    jobs, total = get_jobs(page=page, per_page=per_page, search=search, location=location, level=level, pay=pay)
    
    return jsonify({
        'jobs': jobs,
        'total': total,
        'page': page,
        'per_page': per_page
    })

@app.route('/api/refresh-status')
def api_refresh_status():
    """Get refresh status"""
    status = get_refresh_status()
    return jsonify(status)

@app.route('/api/debug/jobs-count')
def api_debug_jobs_count():
    """Debug endpoint to check job count in database"""
    from models.database import SessionLocal, Job
    session = SessionLocal()
    try:
        total_jobs = session.query(Job).count()
        active_jobs = session.query(Job).filter(Job.is_active == True).count()
        inactive_jobs = session.query(Job).filter(Job.is_active == False).count()
        
        # Get a sample of jobs
        sample_jobs = session.query(Job).filter(Job.is_active == True).limit(5).all()
        sample = [{
            'id': j.id,
            'title': j.title[:50] if j.title else None,
            'company': j.company,
            'is_active': j.is_active
        } for j in sample_jobs]
        
        return jsonify({
            'total_jobs': total_jobs,
            'active_jobs': active_jobs,
            'inactive_jobs': inactive_jobs,
            'sample_jobs': sample
        })
    finally:
        session.close()

@app.route('/api/sources', methods=['GET'])
def api_get_sources():
    """Get all data sources"""
    sources = get_job_sources()
    return jsonify({'sources': sources})

@app.route('/api/sources', methods=['POST'])
def api_add_source():
    """Add new data source"""
    data = request.json
    source_type = data.get('type')  # rss, url, api
    source_url = data.get('url')
    source_name = data.get('name', '')
    
    if not source_type:
        return jsonify({'error': 'Missing required parameters'}), 400
    
    # For API type, allow empty URL to fetch all jobs
    if source_type == 'api' and not source_url:
        source_url = 'all'  # Use 'all' as placeholder for fetching all jobs
    
    try:
        source_id = add_job_source(source_type, source_url, source_name)
        # Try to collect immediately
        collector_manager.collect_from_source(source_type, source_url, source_name)
        return jsonify({'success': True, 'source_id': source_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sources/<int:source_id>', methods=['DELETE'])
def api_delete_source(source_id):
    """Delete a data source"""
    try:
        success = delete_job_source(source_id)
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Source not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/refresh-now', methods=['POST'])
def api_refresh_now():
    """Manually trigger immediate refresh (non-blocking)"""
    import threading
    
    def run_collection():
        """Run data collection in background thread"""
        try:
            collector_manager.collect_all()
            print("Manual refresh completed successfully")
        except Exception as e:
            print(f"Manual refresh failed: {e}")
            import traceback
            traceback.print_exc()
    
    # Start collection in background thread to avoid worker timeout
    thread = threading.Thread(target=run_collection, daemon=True)
    thread.start()
    
    # Return immediately to avoid blocking the HTTP request
    return jsonify({
        'success': True, 
        'message': 'Refresh started in background. Check logs for progress.'
    })

@app.route('/api/ai-recommendations', methods=['POST'])
def api_ai_recommendations():
    """Get AI recommended jobs"""
    data = request.json
    user_profile = data.get('profile', {})
    
    try:
        recommendations = ai_service.get_recommendations(user_profile)
        return jsonify({'recommendations': recommendations})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Development mode: start scheduler if not already started
    if not scheduler.scheduler.running:
        scheduler.start()
    
    # Collect data immediately on startup (only in development)
    # In production, let the scheduler handle it
    if os.getenv('FLASK_ENV') != 'production':
        print("Starting initial data collection...")
        collector_manager.collect_all()
    
    # Get port from environment variable (for cloud platforms like Render)
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') != 'production'
    
    print("Starting Flask application...")
    app.run(debug=debug, host='0.0.0.0', port=port)


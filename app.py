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

# Start scheduler for production (gunicorn) environment
# Check if we're running under gunicorn (production) or directly (development)
# In production, gunicorn will import this module, so we need to start scheduler here
# Note: For multi-worker setups, each worker will have its own scheduler instance
# This is acceptable as APScheduler BackgroundScheduler is thread-safe per process
if not scheduler.scheduler.running:
    try:
        scheduler.start()
        print("Scheduler started")
    except Exception as e:
        print(f"Warning: Could not start scheduler: {e}")

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
    """Manually trigger immediate refresh"""
    try:
        collector_manager.collect_all()
        return jsonify({'success': True, 'message': 'Refresh successful'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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


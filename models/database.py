"""
Database models and management
"""

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean, or_, and_, not_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()

class Job(Base):
    """Job position model"""
    __tablename__ = 'jobs'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(500), nullable=False)
    company = Column(String(200))
    location = Column(String(200))
    description = Column(Text)
    url = Column(String(1000), unique=True)
    source = Column(String(100))  # rss, url, api
    source_name = Column(String(200))
    level = Column(String(50))  # individual, senior, executive
    posted_date = Column(DateTime)
    collected_date = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

class JobSource(Base):
    """Data source model"""
    __tablename__ = 'job_sources'
    
    id = Column(Integer, primary_key=True)
    type = Column(String(50), nullable=False)  # rss, url, api
    url = Column(String(1000), nullable=False)
    name = Column(String(200))
    is_active = Column(Boolean, default=True)
    created_date = Column(DateTime, default=datetime.utcnow)

class RefreshStatus(Base):
    """Refresh status model"""
    __tablename__ = 'refresh_status'
    
    id = Column(Integer, primary_key=True)
    last_refresh = Column(DateTime, default=datetime.utcnow)
    jobs_count = Column(Integer, default=0)
    sources_count = Column(Integer, default=0)
    api_limit_reached = Column(Boolean, default=False)  # Track if API limit was reached
    api_limit_date = Column(DateTime)  # Date when limit was reached (for daily reset)

# Database initialization
# Support both SQLite (development) and PostgreSQL (production)
database_url = os.getenv('DATABASE_URL')

if database_url:
    # Production: PostgreSQL (from environment variable)
    # Render provides DATABASE_URL automatically
    # Convert postgres:// to postgresql:// for SQLAlchemy compatibility
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    # Configure connection pool for PostgreSQL to handle SSL errors
    # pool_pre_ping: Test connections before using them to handle stale connections
    # pool_recycle: Recycle connections after 1 hour to prevent SSL errors
    # pool_size: Number of connections to maintain
    # max_overflow: Additional connections that can be created
    engine = create_engine(
        database_url,
        echo=False,
        pool_pre_ping=True,  # Test connections before using (fixes SSL errors)
        pool_recycle=3600,   # Recycle connections after 1 hour
        pool_size=5,         # Maintain 5 connections
        max_overflow=10,     # Allow up to 10 additional connections
        connect_args={
            "connect_timeout": 10,
            "sslmode": "require"  # Ensure SSL is used
        }
    )
else:
    # Development: SQLite
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database.db')
    engine = create_engine(f'sqlite:///{db_path}', echo=False)

SessionLocal = sessionmaker(bind=engine)

def init_db():
    """Initialize database"""
    Base.metadata.create_all(engine)
    
    # Migrate existing tables: add new columns if they don't exist
    session = SessionLocal()
    try:
        from sqlalchemy import inspect, text
        
        inspector = inspect(engine)
        try:
            columns = [col['name'] for col in inspector.get_columns('refresh_status')]
        except Exception:
            # Table doesn't exist yet, will be created by create_all
            columns = []
        
        db_url = os.getenv('DATABASE_URL', '')
        is_postgresql = db_url and ('postgresql' in db_url or 'postgres' in db_url)
        
        # Add api_limit_reached column if it doesn't exist
        if 'api_limit_reached' not in columns:
            try:
                if is_postgresql:
                    # PostgreSQL - check if column exists first
                    result = session.execute(text("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name='refresh_status' AND column_name='api_limit_reached'
                    """))
                    if not result.fetchone():
                        session.execute(text('ALTER TABLE refresh_status ADD COLUMN api_limit_reached BOOLEAN DEFAULT FALSE'))
                        session.commit()
                        print("Added api_limit_reached column to refresh_status table")
                else:
                    # SQLite
                    session.execute(text('ALTER TABLE refresh_status ADD COLUMN api_limit_reached BOOLEAN DEFAULT 0'))
                    session.commit()
                    print("Added api_limit_reached column to refresh_status table")
            except Exception as e:
                print(f"Warning: Could not add api_limit_reached column (may already exist): {e}")
                session.rollback()
        
        # Add api_limit_date column if it doesn't exist
        if 'api_limit_date' not in columns:
            try:
                if is_postgresql:
                    # PostgreSQL - check if column exists first
                    result = session.execute(text("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name='refresh_status' AND column_name='api_limit_date'
                    """))
                    if not result.fetchone():
                        session.execute(text('ALTER TABLE refresh_status ADD COLUMN api_limit_date TIMESTAMP'))
                        session.commit()
                        print("Added api_limit_date column to refresh_status table")
                else:
                    # SQLite
                    session.execute(text('ALTER TABLE refresh_status ADD COLUMN api_limit_date DATETIME'))
                    session.commit()
                    print("Added api_limit_date column to refresh_status table")
            except Exception as e:
                print(f"Warning: Could not add api_limit_date column (may already exist): {e}")
                session.rollback()
    except Exception as e:
        print(f"Warning: Could not check/migrate refresh_status table: {e}")
        try:
            session.rollback()
        except:
            pass
    
    # Create default refresh status record
    try:
        if session.query(RefreshStatus).count() == 0:
            status = RefreshStatus()
            session.add(status)
            session.commit()
    except Exception as e:
        print(f"Warning: Could not create default refresh status: {e}")
        session.rollback()
    finally:
        session.close()

def get_jobs(page=1, per_page=20, search='', location='', level='', pay=''):
    """Get jobs list"""
    session = SessionLocal()
    try:
        query = session.query(Job).filter(Job.is_active == True)
        
        # Search in title and company only (not description) with whole word matching
        if search:
            # Split search terms and match each as whole word
            search_terms = search.strip().split()
            db_url = os.getenv('DATABASE_URL', '')
            is_postgresql = db_url and ('postgresql' in db_url or 'postgres' in db_url)
            
            from sqlalchemy import text
            
            search_conditions = []
            for term in search_terms:
                if not term:
                    continue
                term_lower = term.lower()
                
                if is_postgresql:
                    # PostgreSQL: Use regex word boundary \y for whole word matching
                    # \y matches word boundaries (start/end of word)
                    # Escape special regex characters in the search term
                    import re
                    term_escaped = re.escape(term_lower)
                    regex_pattern = f'\\y{term_escaped}\\y'
                    # Only search in title and company, NOT description
                    search_conditions.append(
                        (Job.title.op('~*')(regex_pattern)) |
                        (Job.company.op('~*')(regex_pattern))
                    )
                else:
                    # SQLite: Use LIKE with word boundaries
                    # Match whole word by checking for word boundaries (space, punctuation, start, end)
                    # Escape special LIKE characters in the search term
                    term_escaped = term_lower.replace('%', '\\%').replace('_', '\\_')
                    
                    # Patterns to match whole word:
                    # 1. Word at start of string
                    # 2. Word at end of string  
                    # 3. Word with space before and after
                    # 4. Exact match (single word)
                    start_pattern = f'{term_escaped} %'
                    end_pattern = f'% {term_escaped}'
                    middle_pattern = f'% {term_escaped} %'
                    exact_pattern = term_escaped
                    
                    # Only search in title and company, NOT description
                    search_conditions.append(
                        (Job.title.ilike(start_pattern)) |
                        (Job.title.ilike(end_pattern)) |
                        (Job.title.ilike(middle_pattern)) |
                        (Job.title.ilike(exact_pattern)) |
                        (Job.company.ilike(start_pattern)) |
                        (Job.company.ilike(end_pattern)) |
                        (Job.company.ilike(middle_pattern)) |
                        (Job.company.ilike(exact_pattern))
                    )
            
            # All search terms must be present (AND condition)
            if search_conditions:
                from sqlalchemy import and_
                query = query.filter(and_(*search_conditions))
        
        # Search in location field separately with whole word matching
        if location:
            location_terms = location.strip().split()
            db_url = os.getenv('DATABASE_URL', '')
            is_postgresql = db_url and ('postgresql' in db_url or 'postgres' in db_url)
            
            location_conditions = []
            for term in location_terms:
                if not term:
                    continue
                term_lower = term.lower()
                
                if is_postgresql:
                    # PostgreSQL: Use regex word boundary
                    import re
                    term_escaped = re.escape(term_lower)
                    regex_pattern = f'\\y{term_escaped}\\y'
                    location_conditions.append(Job.location.op('~*')(regex_pattern))
                else:
                    # SQLite: Use LIKE with word boundaries
                    term_escaped = term_lower.replace('%', '\\%').replace('_', '\\_')
                    
                    start_pattern = f'{term_escaped} %'
                    end_pattern = f'% {term_escaped}'
                    middle_pattern = f'% {term_escaped} %'
                    exact_pattern = term_escaped
                    
                    location_conditions.append(
                        (Job.location.ilike(start_pattern)) |
                        (Job.location.ilike(end_pattern)) |
                        (Job.location.ilike(middle_pattern)) |
                        (Job.location.ilike(exact_pattern))
                    )
            
            # All location terms must be present (AND condition)
            if location_conditions:
                from sqlalchemy import and_
                query = query.filter(and_(*location_conditions))
        
        if level:
            if level == 'entry':
                # Entry Level: intern, new graduate, entry level
                # Check both level field and title/description content
                query = query.filter(
                    or_(
                        Job.level == 'entry',
                        Job.title.ilike('%intern%'),
                        Job.title.ilike('%internship%'),
                        Job.title.ilike('%new graduate%'),
                        Job.title.ilike('%entry level%'),
                        Job.title.ilike('%entry-level%'),
                        Job.description.ilike('%intern%'),
                        Job.description.ilike('%new graduate%'),
                        Job.description.ilike('%entry level%'),
                        Job.description.ilike('%entry-level%')
                    )
                )
            elif level == 'mid':
                # Mid-level: all jobs that don't have 'senior' and are not entry level
                # This includes jobs with level='mid', level='individual', or level is NULL
                query = query.filter(
                    and_(
                        ~or_(
                            Job.title.ilike('%senior%'),
                            Job.title.ilike('%sr.%'),
                            Job.title.ilike('%intern%'),
                            Job.title.ilike('%internship%'),
                            Job.title.ilike('%new graduate%'),
                            Job.title.ilike('%entry level%'),
                            Job.title.ilike('%entry-level%'),
                            Job.description.ilike('%senior%'),
                            Job.description.ilike('%intern%'),
                            Job.description.ilike('%new graduate%'),
                            Job.description.ilike('%entry level%'),
                            Job.description.ilike('%entry-level%')
                        ),
                        ~or_(
                            Job.level == 'entry',
                            Job.level == 'senior'
                        )
                    )
                )
            elif level == 'senior':
                # Senior Level: jobs with 'senior' in title or description, or level='senior'
                query = query.filter(
                    or_(
                        Job.level == 'senior',
                        Job.title.ilike('%senior%'),
                        Job.title.ilike('%sr.%'),
                        Job.description.ilike('%senior%')
                    )
                )
        
        # Filter by minimum salary if specified
        if pay:
            try:
                min_salary = int(pay)
                if min_salary > 0:
                    # Search for salary information in description
                    # Simplified pattern matching for better performance
                    if min_salary >= 100000:
                        # For $100k+, look for 100k, 150k, 200k, etc.
                        query = query.filter(
                            or_(
                                Job.description.ilike('%$100%'),
                                Job.description.ilike('%$150%'),
                                Job.description.ilike('%$200%'),
                                Job.description.ilike('%100k%'),
                                Job.description.ilike('%150k%'),
                                Job.description.ilike('%200k%'),
                                Job.description.ilike('%100,000%'),
                                Job.description.ilike('%150,000%'),
                                Job.description.ilike('%200,000%')
                            )
                        )
                    elif min_salary >= 50000:
                        # For $50k+, look for 50k-99k and above
                        query = query.filter(
                            or_(
                                Job.description.ilike('%$50%'),
                                Job.description.ilike('%$60%'),
                                Job.description.ilike('%$70%'),
                                Job.description.ilike('%$80%'),
                                Job.description.ilike('%$90%'),
                                Job.description.ilike('%$100%'),
                                Job.description.ilike('%50k%'),
                                Job.description.ilike('%60k%'),
                                Job.description.ilike('%70k%'),
                                Job.description.ilike('%80k%'),
                                Job.description.ilike('%90k%'),
                                Job.description.ilike('%100k%'),
                                Job.description.ilike('%50,000%'),
                                Job.description.ilike('%60,000%'),
                                Job.description.ilike('%70,000%'),
                                Job.description.ilike('%80,000%'),
                                Job.description.ilike('%90,000%'),
                                Job.description.ilike('%100,000%')
                            )
                        )
                    elif min_salary >= 10000:
                        # For $10k+, look for 10k-49k and above
                        query = query.filter(
                            or_(
                                Job.description.ilike('%$10%'),
                                Job.description.ilike('%$20%'),
                                Job.description.ilike('%$30%'),
                                Job.description.ilike('%$40%'),
                                Job.description.ilike('%$50%'),
                                Job.description.ilike('%10k%'),
                                Job.description.ilike('%20k%'),
                                Job.description.ilike('%30k%'),
                                Job.description.ilike('%40k%'),
                                Job.description.ilike('%50k%'),
                                Job.description.ilike('%10,000%'),
                                Job.description.ilike('%20,000%'),
                                Job.description.ilike('%30,000%'),
                                Job.description.ilike('%40,000%'),
                                Job.description.ilike('%50,000%')
                            )
                        )
                # For $0, don't filter (show all jobs)
            except (ValueError, Exception) as e:
                pass  # Invalid pay value, ignore
        
        total = query.count()
        # Sort by collected_date (update time) descending, then by posted_date as secondary sort
        jobs = query.order_by(Job.collected_date.desc(), Job.posted_date.desc()).offset((page - 1) * per_page).limit(per_page).all()
        
        jobs_list = [{
            'id': job.id,
            'title': job.title,
            'company': job.company,
            'location': job.location,
            'description': job.description[:500] if job.description else '',
            'url': job.url,
            'source': job.source,
            'source_name': job.source_name,
            'level': job.level,
            'posted_date': job.posted_date.isoformat() if job.posted_date else None,
            'collected_date': job.collected_date.isoformat() if job.collected_date else None
        } for job in jobs]
        
        return jobs_list, total
    finally:
        session.close()

def add_job(title, company, location, description, url, source, source_name, level=None, posted_date=None):
    """Add or update job in database"""
    session = SessionLocal()
    try:
        # Check if already exists by URL (unique identifier)
        existing = session.query(Job).filter(Job.url == url).first()
        if existing:
            # Update existing record with latest information
            existing.title = title
            existing.company = company
            existing.location = location
            existing.description = description
            existing.level = level or existing.level
            # Update posted_date if new one is provided and more recent
            if posted_date:
                if not existing.posted_date or (existing.posted_date and posted_date > existing.posted_date):
                    existing.posted_date = posted_date
            existing.is_active = True
            existing.collected_date = datetime.utcnow()  # Update collection timestamp
            session.commit()
            return 'updated'
        else:
            # Create new record
            job = Job(
                title=title,
                company=company,
                location=location,
                description=description,
                url=url,
                source=source,
                source_name=source_name,
                level=level,
                posted_date=posted_date
            )
            session.add(job)
            session.commit()
            return 'created'
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

def add_job_source(source_type, url, name=''):
    """Add data source"""
    session = SessionLocal()
    try:
        source = JobSource(type=source_type, url=url, name=name)
        session.add(source)
        session.commit()
        return source.id
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

def get_job_sources():
    """Get all data sources"""
    session = SessionLocal()
    try:
        sources = session.query(JobSource).filter(JobSource.is_active == True).all()
        return [{
            'id': s.id,
            'type': s.type,
            'url': s.url,
            'name': s.name,
            'created_date': s.created_date.isoformat() if s.created_date else None
        } for s in sources]
    finally:
        session.close()

def delete_job_source(source_id):
    """Delete or deactivate a data source and all related jobs"""
    session = SessionLocal()
    try:
        source = session.query(JobSource).filter(JobSource.id == source_id).first()
        if source:
            # Deactivate all jobs from this source
            # Match by source_name (which can be either name or url based on how it was saved)
            # In collector_manager, source_name is set as: source_name or source_url
            # So we need to match both possibilities
            
            # Build matching conditions: match by name if exists, or by url
            match_conditions = []
            if source.name:
                match_conditions.append(Job.source_name == source.name)
            match_conditions.append(Job.source_name == source.url)
            
            # Also match by source type to be more precise
            related_jobs = session.query(Job).filter(
                or_(*match_conditions),
                Job.source == source.type,
                Job.is_active == True
            ).all()
            
            jobs_deactivated = 0
            for job in related_jobs:
                job.is_active = False
                jobs_deactivated += 1
            
            # Soft delete the source by setting is_active to False
            source.is_active = False
            
            session.commit()
            logger.info(f"Deleted source {source_id} ({source.name or source.url}) and deactivated {jobs_deactivated} related jobs")
            return True
        return False
    except Exception as e:
        session.rollback()
        logger.error(f"Error deleting source {source_id}: {e}")
        raise e
    finally:
        session.close()

def update_refresh_status():
    """Update refresh status"""
    session = SessionLocal()
    try:
        status = session.query(RefreshStatus).first()
        if not status:
            status = RefreshStatus()
            session.add(status)
        
        status.last_refresh = datetime.utcnow()
        status.jobs_count = session.query(Job).filter(Job.is_active == True).count()
        status.sources_count = session.query(JobSource).filter(JobSource.is_active == True).count()
        session.commit()
    finally:
        session.close()

def get_unique_companies_count():
    """Get count of unique active companies"""
    session = SessionLocal()
    try:
        from sqlalchemy import func, distinct
        count = session.query(func.count(distinct(Job.company))).filter(
            Job.is_active == True,
            Job.company.isnot(None),
            Job.company != ''
        ).scalar()
        return count or 0
    finally:
        session.close()

def get_refresh_status():
    """Get refresh status with retry logic for connection errors"""
    from sqlalchemy.exc import OperationalError
    max_retries = 3
    
    for attempt in range(max_retries):
        session = SessionLocal()
        try:
            status = session.query(RefreshStatus).first()
            companies_count = get_unique_companies_count()
            
            # Check if API limit should be reset (new day)
            if status and status.api_limit_reached and status.api_limit_date:
                limit_date = status.api_limit_date.date()
                today = datetime.utcnow().date()
                if limit_date < today:
                    # New day, reset the limit
                    status.api_limit_reached = False
                    status.api_limit_date = None
                    session.commit()
            
            if status:
                return {
                    'last_refresh': status.last_refresh.isoformat() if status.last_refresh else None,
                    'jobs_count': status.jobs_count,
                    'sources_count': status.sources_count,
                    'companies_count': companies_count,
                    'api_limit_reached': status.api_limit_reached if status else False,
                    'api_limit_date': status.api_limit_date.isoformat() if status and status.api_limit_date else None
                }
            return {
                'last_refresh': None,
                'jobs_count': 0,
                'sources_count': 0,
                'companies_count': companies_count,
                'api_limit_reached': False,
                'api_limit_date': None
            }
        except OperationalError as e:
            # Handle SSL/connection errors with retry
            session.close()
            if attempt < max_retries - 1:
                import time
                time.sleep(0.5 * (attempt + 1))  # Exponential backoff
                continue
            else:
                # Last attempt failed, return default values
                print(f"Warning: Database connection error after {max_retries} attempts: {e}")
                return {
                    'last_refresh': None,
                    'jobs_count': 0,
                    'sources_count': 0,
                    'companies_count': 0,
                    'api_limit_reached': False,
                    'api_limit_date': None
                }
        except Exception as e:
            session.close()
            print(f"Error getting refresh status: {e}")
            return {
                'last_refresh': None,
                'jobs_count': 0,
                'sources_count': 0,
                'companies_count': 0,
                'api_limit_reached': False,
                'api_limit_date': None
            }
        finally:
            try:
                session.close()
            except:
                pass

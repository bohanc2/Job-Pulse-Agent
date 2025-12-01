"""
AI Service
Uses OpenAI API for job classification, recommendations, and intelligent analysis
"""

import openai
import logging
import json
from models.database import get_jobs

logger = logging.getLogger(__name__)

class AIService:
    """AI Service class"""
    
    def __init__(self, api_key=None):
        if api_key:
            self.client = openai.OpenAI(api_key=api_key)
        else:
            self.client = None
            logger.warning("OpenAI API key not set, AI features will be unavailable")
    
    def classify_job(self, title, description):
        """Classify job position using AI"""
        if not self.client:
            return self._simple_classify(title, description)
        
        try:
            prompt = f"""
            Please analyze the following job position and determine its level:
            Title: {title}
            Description: {description[:500]}
            
            Please return JSON in the following format:
            {{
                "level": "individual" or "senior" or "executive",
                "category": "field service related category",
                "skills": ["skill1", "skill2", "skill3"]
            }}
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a professional HR analyst specializing in field service job positions."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=200
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
        except Exception as e:
            logger.error(f"AI classification failed: {e}")
            return self._simple_classify(title, description)
    
    def get_recommendations(self, user_profile):
        """Get job recommendations based on user profile"""
        if not self.client:
            # Use simple recommendation algorithm when AI is unavailable
            return self._simple_recommendations(user_profile)
        
        try:
            # Get all jobs
            jobs, _ = get_jobs(page=1, per_page=100, search='')
            
            if not jobs:
                return []
            
            # Build user profile summary
            profile_summary = f"""
            Experience: {user_profile.get('experience', 'Unknown')}
            Skills: {', '.join(user_profile.get('skills', []))}
            Job Level: {user_profile.get('level', 'individual')}
            Location Preference: {user_profile.get('location', 'Any')}
            """
            
            jobs_summary = "\n".join([
                f"- {job['title']} at {job['company']} ({job['location']})"
                for job in jobs[:20]
            ])
            
            prompt = f"""
            Based on the following user profile, recommend the top 5 most suitable jobs from the job list:
            
            User Profile:
            {profile_summary}
            
            Job List:
            {jobs_summary}
            
            Please return JSON format with recommended job IDs and reasons.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a professional career advisor helping field service professionals find suitable job opportunities."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=500
            )
            
            result = json.loads(response.choices[0].message.content)
            return result.get('recommendations', [])
        except Exception as e:
            logger.error(f"AI recommendation failed: {e}")
            return self._simple_recommendations(user_profile)
    
    def _simple_recommendations(self, user_profile):
        """Simple recommendation algorithm (when AI is unavailable)"""
        try:
            # Get all jobs
            jobs, _ = get_jobs(page=1, per_page=50, search='')
            
            if not jobs:
                return []
            
            user_level = user_profile.get('level', 'individual')
            user_skills = [s.lower() for s in user_profile.get('skills', [])]
            user_location = user_profile.get('location', '').lower()
            
            # Score jobs based on level match and keywords
            scored_jobs = []
            for job in jobs:
                score = 0
                
                # Level matching
                if job.get('level') == user_level:
                    score += 10
                elif user_level == 'senior' and job.get('level') == 'executive':
                    score += 5
                elif user_level == 'individual' and job.get('level') == 'senior':
                    score += 3
                
                # Keyword matching in title and description
                job_text = (job.get('title', '') + ' ' + job.get('description', '')).lower()
                for skill in user_skills:
                    if skill in job_text:
                        score += 2
                
                # Location matching
                if user_location and user_location in job.get('location', '').lower():
                    score += 5
                
                scored_jobs.append({
                    'job_id': job.get('id'),
                    'score': score,
                    'reason': f"Matches your {user_level} level profile"
                })
            
            # Sort by score and return top 5
            scored_jobs.sort(key=lambda x: x['score'], reverse=True)
            return scored_jobs[:5]
        except Exception as e:
            logger.error(f"Simple recommendation failed: {e}")
            return []
    
    def _simple_classify(self, title, description):
        """Simple classification method (when AI is unavailable)"""
        text = (title + ' ' + description).lower()
        
        if any(word in text for word in ['senior', 'sr.', 'lead', 'principal', 'director', 'vp']):
            level = 'senior'
        elif any(word in text for word in ['executive', 'chief', 'ceo', 'cto', 'cfo']):
            level = 'executive'
        else:
            level = 'individual'
        
        return {
            'level': level,
            'category': 'field_service',
            'skills': []
        }

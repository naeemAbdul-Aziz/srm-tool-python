# session.py - handles user session management for the student result management system

from datetime import datetime, timedelta
from logger import get_logger

logger = get_logger(__name__)

class SessionManager:
    """manage user sessions and session-specific data"""
    
    def __init__(self):
        self.current_session = None
        self.session_data = {}
        logger.info("session manager initialized")
    
    def create_session(self, username, role, user_data=None):
        """create a new user session"""
        self.current_session = {
            'username': username,
            'role': role,
            'login_time': datetime.now(),
            'user_data': user_data or {},
            'session_id': f"{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        }
        logger.info(f"session created for {username} ({role}) at {self.current_session['login_time']}")
        return self.current_session['session_id']
    
    def get_current_session(self):
        """get the current active session"""
        return self.current_session
    
    def get_current_user(self):
        """get current user info"""
        if self.current_session:
            return {
                'username': self.current_session['username'],
                'role': self.current_session['role'],
                'user_data': self.current_session.get('user_data', {})
            }
        return None
    
    def is_logged_in(self):
        """check if user is currently logged in"""
        return self.current_session is not None
    
    def is_admin(self):
        """check if current user is admin"""
        return self.current_session and self.current_session['role'] == 'admin'
    
    def is_student(self):
        """check if current user is student"""
        return self.current_session and self.current_session['role'] == 'student'
    
    def get_session_duration(self):
        """get session duration in minutes"""
        if self.current_session:
            duration = datetime.now() - self.current_session['login_time']
            return duration.total_seconds() / 60
        return 0
    
    def update_user_data(self, key, value):
        """update session user data"""
        if self.current_session:
            self.current_session['user_data'][key] = value
            logger.debug(f"session data updated: {key} = {value}")
    
    def get_user_data(self, key, default=None):
        """get session user data"""
        if self.current_session:
            return self.current_session['user_data'].get(key, default)
        return default
    
    def clear_session(self):
        """clear the current session"""
        if self.current_session:
            username = self.current_session['username']
            duration = self.get_session_duration()
            logger.info(f"session cleared for {username} after {duration:.1f} minutes")
            self.current_session = None
        else:
            logger.debug("no active session to clear")

# global session manager instance
session_manager = SessionManager()

# legacy support for backward compatibility
current_user = {
    "username": None,
    "role": None
}

def set_user(username, role):
    """legacy function - creates session and sets user"""
    current_user["username"] = username
    current_user["role"] = role
    session_manager.create_session(username, role)
    logger.info(f"legacy session set for {username} ({role})")

def get_user():
    """legacy function - returns current user info"""
    return current_user

def clear_user():
    """legacy function - clears current user and session"""
    current_user["username"] = None
    current_user["role"] = None
    session_manager.clear_session()
    logger.info("legacy session cleared")

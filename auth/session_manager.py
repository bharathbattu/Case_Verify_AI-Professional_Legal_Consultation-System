"""
Session Management for Case-Verify AI
"""
import streamlit as st
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from database.models import UserSession, User
from database.connection import SessionLocal
import uuid

def require_auth(func):
    """Decorator to require authentication for a function"""
    def wrapper(*args, **kwargs):
        session_manager = SessionManager()
        if not session_manager.is_authenticated():
            st.warning("Please login to access this feature.")
            return None
        return func(*args, **kwargs)
    return wrapper

class SessionManager:
    """Manages user sessions and state"""
    
    def __init__(self):
        self.session_timeout = timedelta(hours=24)  # 24 hour session timeout
    
    def create_session(self, user_id: int, user_agent: str = None, ip_address: str = None) -> str:
        """Create a new user session"""
        db = SessionLocal()
        try:
            # Generate session token
            session_token = str(uuid.uuid4())
            
            # Create session record
            session = UserSession(
                user_id=user_id,
                session_token=session_token,
                expires_at=datetime.utcnow() + self.session_timeout,
                user_agent=user_agent,
                ip_address=ip_address,
                device_info={'created_from': 'streamlit_app'}
            )
            
            db.add(session)
            db.commit()
            
            # Store in Streamlit session state
            st.session_state['session_token'] = session_token
            st.session_state['user_id'] = user_id
            st.session_state['authentication_status'] = True
            
            return session_token
            
        except Exception as e:
            db.rollback()
            st.error(f"Error creating session: {str(e)}")
            return None
        finally:
            db.close()
    
    def create_session_by_username(self, username: str) -> bool:
        """Create session by username (convenience method)"""
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.username == username).first()
            if user:
                session_token = self.create_session(user.id)
                return session_token is not None
            return False
        finally:
            db.close()
    
    def validate_session(self, session_token: str) -> Optional[User]:
        """Validate session and return user if valid"""
        db = SessionLocal()
        try:
            session = db.query(UserSession).filter(
                UserSession.session_token == session_token,
                UserSession.is_active == True,
                UserSession.expires_at > datetime.utcnow()
            ).first()
            
            if session:
                # Get user
                user = db.query(User).filter(User.id == session.user_id).first()
                if user and user.is_active:
                    return user
            
            return None
            
        except Exception as e:
            st.error(f"Error validating session: {str(e)}")
            return None
        finally:
            db.close()
    
    def end_session(self, session_token: str = None):
        """End user session"""
        if not session_token and 'session_token' in st.session_state:
            session_token = st.session_state['session_token']
        
        if not session_token:
            return
        
        db = SessionLocal()
        try:
            session = db.query(UserSession).filter(
                UserSession.session_token == session_token
            ).first()
            
            if session:
                session.is_active = False
                db.commit()
            
            # Clear Streamlit session state
            self.clear_session_state()
            
        except Exception as e:
            db.rollback()
            st.error(f"Error ending session: {str(e)}")
        finally:
            db.close()
    
    def clear_session_state(self):
        """Clear Streamlit session state"""
        keys_to_clear = [
            'session_token', 'user_id', 'username', 'authentication_status',
            'name', 'user_role', 'current_user'
        ]
        
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
    
    def extend_session(self, session_token: str) -> bool:
        """Extend session expiry"""
        db = SessionLocal()
        try:
            session = db.query(UserSession).filter(
                UserSession.session_token == session_token,
                UserSession.is_active == True
            ).first()
            
            if session:
                session.expires_at = datetime.utcnow() + self.session_timeout
                db.commit()
                return True
            
            return False
            
        except Exception as e:
            db.rollback()
            st.error(f"Error extending session: {str(e)}")
            return False
        finally:
            db.close()
    
    def get_active_sessions(self, user_id: int) -> list:
        """Get all active sessions for a user"""
        db = SessionLocal()
        try:
            sessions = db.query(UserSession).filter(
                UserSession.user_id == user_id,
                UserSession.is_active == True,
                UserSession.expires_at > datetime.utcnow()
            ).all()
            
            return sessions
            
        except Exception as e:
            st.error(f"Error getting active sessions: {str(e)}")
            return []
        finally:
            db.close()
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        db = SessionLocal()
        try:
            expired_sessions = db.query(UserSession).filter(
                UserSession.expires_at < datetime.utcnow()
            ).all()
            
            for session in expired_sessions:
                session.is_active = False
            
            db.commit()
            return len(expired_sessions)
            
        except Exception as e:
            db.rollback()
            st.error(f"Error cleaning up sessions: {str(e)}")
            return 0
        finally:
            db.close()
    
    def get_session_info(self, session_token: str) -> Optional[Dict[str, Any]]:
        """Get session information"""
        db = SessionLocal()
        try:
            session = db.query(UserSession).filter(
                UserSession.session_token == session_token
            ).first()
            
            if session:
                return {
                    'user_id': session.user_id,
                    'created_at': session.created_at,
                    'expires_at': session.expires_at,
                    'is_active': session.is_active,
                    'ip_address': session.ip_address,
                    'user_agent': session.user_agent,
                    'device_info': session.device_info
                }
            
            return None
            
        except Exception as e:
            st.error(f"Error getting session info: {str(e)}")
            return None
        finally:
            db.close()
    
    @staticmethod
    def require_auth(func):
        """Decorator to require authentication for functions"""
        def wrapper(*args, **kwargs):
            if 'authentication_status' not in st.session_state or not st.session_state['authentication_status']:
                st.warning("Please login to access this feature.")
                st.stop()
            return func(*args, **kwargs)
        return wrapper
    
    @staticmethod
    def require_role(required_role: str):
        """Decorator to require specific role"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                if 'user_role' not in st.session_state:
                    st.error("User role not found. Please login again.")
                    st.stop()
                
                user_role = st.session_state.get('user_role', '')
                
                # Admin can access everything
                if user_role == 'admin':
                    return func(*args, **kwargs)
                
                # Check specific role
                if user_role != required_role:
                    st.error(f"Access denied. Required role: {required_role}")
                    st.stop()
                
                return func(*args, **kwargs)
            return wrapper
        return decorator

def init_session_state():
    """Initialize session state variables"""
    session_vars = {
        'authentication_status': None,
        'name': None,
        'username': None,
        'user_id': None,
        'user_role': None,
        'session_token': None,
        'current_user': None
    }
    
    for key, default_value in session_vars.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

def is_authenticated() -> bool:
    """Check if user is authenticated"""
    return st.session_state.get('authentication_status', False) == True

def get_current_user() -> Optional[User]:
    """Get current authenticated user"""
    return st.session_state.get('current_user', None)

def get_current_user_id() -> Optional[int]:
    """Get current user ID"""
    return st.session_state.get('user_id', None)

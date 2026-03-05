# Authentication package initialization
import logging

logger = logging.getLogger(__name__)

# Flag to prevent repeated logging
_auth_status_logged = False

try:
    # Import production authentication system
    from .authenticator import Authenticator, get_authenticator, register_user, get_user_info
    from .user_manager import UserManager
    from .session_manager import SessionManager, require_auth
    
    __all__ = [
        'Authenticator', 'get_authenticator', 'register_user', 'get_user_info',
        'UserManager', 'SessionManager', 'require_auth'
    ]
    if not _auth_status_logged:
        logger.info("Full auth module imported successfully")
        _auth_status_logged = True
    
except Exception as e:
    if not _auth_status_logged:
        logger.warning("Full auth import failed (%s). Loading simplified fallback.", e)
        _auth_status_logged = True
    
    try:
        # Fallback to simplified authentication (development only)
        from .simple_auth import get_authenticator, register_user, get_user_info
        
        class UserManager:
            """Simplified UserManager fallback"""
            def __init__(self):
                pass
        
        class SessionManager:
            """Simplified SessionManager fallback"""
            def __init__(self):
                pass
                
            def is_authenticated(self):
                import streamlit as st
                return st.session_state.get('authentication_status', False)
                
            def create_session_by_username(self, username):
                import streamlit as st
                st.session_state['username'] = username
                st.session_state['authentication_status'] = True
                
            def destroy_session(self):
                import streamlit as st
                for key in ['authentication_status', 'username', 'name', 'user_id']:
                    if key in st.session_state:
                        del st.session_state[key]
        
        def require_auth(*args, **kwargs):
            """Simplified auth decorator"""
            def decorator(func):
                def wrapper(*a, **kw):
                    import streamlit as st
                    if not st.session_state.get('authentication_status', False):
                        st.warning("Please log in to access this feature.")
                        return None
                    return func(*a, **kw)
                return wrapper
            return decorator
        
        __all__ = [
            'get_authenticator', 'register_user', 'get_user_info',
            'UserManager', 'SessionManager', 'require_auth'
        ]
        
    except Exception as e2:
        logger.error("Even simplified auth failed: %s. Using minimal fallback.", e2)
        
        def get_authenticator():
            """Minimal fallback authenticator"""
            return None
        
        def register_user(*args, **kwargs):
            raise NotImplementedError("Authentication not available - missing dependencies")
        
        def get_user_info(*args, **kwargs):
            return None
        
        class UserManager:
            """Minimal fallback UserManager"""
            def __init__(self):
                pass
        
        class SessionManager:
            """Minimal fallback SessionManager"""
            def __init__(self):
                pass
                
            def is_authenticated(self):
                return False
                
            def create_session_by_username(self, username):
                pass
                
            def destroy_session(self):
                pass
        
        def require_auth(*args, **kwargs):
            """Minimal fallback auth decorator"""
            def decorator(func):
                return func
            return decorator
        
        __all__ = [
            'get_authenticator', 'register_user', 'get_user_info',
            'UserManager', 'SessionManager', 'require_auth'
        ]

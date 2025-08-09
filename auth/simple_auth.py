"""
Simplified authentication for Case-Verify AI
Temporary module to avoid database dependencies during development
"""
import streamlit as st

class SimpleAuthenticator:
    """Simple authentication system without database"""
    
    def __init__(self):
        """Initialize the authenticator"""
        self.users = {
            "demo": "demo123",  # Simple demo user
            "admin": "admin123"
        }
        
    def login(self, username: str, password: str) -> bool:
        """Login a user with username and password"""
        if username in self.users and self.users[username] == password:
            # Store user info in session state
            st.session_state['authentication_status'] = True
            st.session_state['username'] = username
            st.session_state['name'] = username.title()
            st.session_state['user_id'] = hash(username)
            return True
        return False
    
    def logout(self):
        """Logout the current user"""
        for key in ['authentication_status', 'username', 'name', 'user_id']:
            if key in st.session_state:
                del st.session_state[key]

def get_authenticator():
    """Get the authenticator instance"""
    return SimpleAuthenticator()

def register_user(username: str, email: str, password: str, full_name: str = "", organization: str = ""):
    """Register a new user (simplified version)"""
    # For now, just return success
    return True

def get_user_info(username: str):
    """Get user information by username (simplified)"""
    return {
        'id': hash(username),
        'username': username,
        'email': f"{username}@example.com",
        'full_name': username.title(),
        'organization': "Demo Organization",
        'role': "user",
        'is_active': True,
        'created_at': "2024-01-01",
        'last_login': None
    }

"""
User Management System for Case-Verify AI
"""
import streamlit as st
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from database.models import User, Case, Analysis
from database.connection import SessionLocal
from passlib.hash import bcrypt

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return bcrypt.hash(password)

class UserManager:
    """Manages user operations and database interactions"""
    
    def __init__(self):
        self.db = SessionLocal()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()
    
    def create_user(self, username: str, email: str, password: str, 
                   full_name: Optional[str] = None, phone: Optional[str] = None, 
                   organization: Optional[str] = None, role: str = 'user') -> bool:
        """Create a new user"""
        try:
            # Check if user already exists
            if self.get_user_by_username(username) or self.get_user_by_email(email):
                return False
            
            new_user = User(
                username=username,
                email=email,
                hashed_password=hash_password(password),
                full_name=full_name,
                phone=phone,
                organization=organization,
                role=role,
                is_active=True,
                is_verified=False
            )
            
            self.db.add(new_user)
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            st.error(f"Error creating user: {str(e)}")
            return False
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        return self.db.query(User).filter(User.username == username).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.db.query(User).filter(User.email == email).first()
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def update_user(self, user_id: int, **kwargs) -> bool:
        """Update user information"""
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return False
            
            for key, value in kwargs.items():
                if hasattr(user, key) and value is not None:
                    if key == 'password':
                        user.hashed_password = hash_password(value)
                    else:
                        setattr(user, key, value)
            
            user.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            st.error(f"Error updating user: {str(e)}")
            return False
    
    def delete_user(self, user_id: int) -> bool:
        """Delete a user (soft delete by setting is_active to False)"""
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return False
            
            user.is_active = False
            user.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            st.error(f"Error deleting user: {str(e)}")
            return False
    
    def get_all_users(self, active_only: bool = True) -> List[User]:
        """Get all users"""
        query = self.db.query(User)
        if active_only:
            query = query.filter(User.is_active == True)
        return query.all()
    
    def get_user_statistics(self, user_id: int) -> Dict[str, Any]:
        """Get user statistics"""
        user = self.get_user_by_id(user_id)
        if not user:
            return {}
        
        try:
            total_cases = self.db.query(Case).filter(Case.user_id == user_id).count()
            active_cases = self.db.query(Case).filter(
                Case.user_id == user_id,
                Case.status.in_(['draft', 'analyzed'])
            ).count()
            completed_cases = self.db.query(Case).filter(
                Case.user_id == user_id,
                Case.status.in_(['filed', 'closed'])
            ).count()
            
            total_analyses = self.db.query(Analysis).join(Case).filter(
                Case.user_id == user_id
            ).count()
            
            return {
                'total_cases': total_cases,
                'active_cases': active_cases,
                'completed_cases': completed_cases,
                'total_analyses': total_analyses,
                'join_date': user.created_at.strftime('%Y-%m-%d') if user.created_at else None,
                'last_login': user.last_login.strftime('%Y-%m-%d %H:%M') if user.last_login else 'Never'
            }
            
        except Exception as e:
            st.error(f"Error getting user statistics: {str(e)}")
            return {}
    
    def verify_user(self, user_id: int) -> bool:
        """Verify a user account"""
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return False
            
            user.is_verified = True
            user.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            st.error(f"Error verifying user: {str(e)}")
            return False
    
    def change_user_role(self, user_id: int, new_role: str) -> bool:
        """Change user role"""
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return False
            
            user.role = new_role
            user.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            st.error(f"Error changing user role: {str(e)}")
            return False
    
    def search_users(self, query: str) -> List[User]:
        """Search users by username, email, or full name"""
        search_pattern = f"%{query}%"
        return self.db.query(User).filter(
            (User.username.ilike(search_pattern)) |
            (User.email.ilike(search_pattern)) |
            (User.full_name.ilike(search_pattern))
        ).filter(User.is_active == True).all()
    
    def get_users_by_role(self, role: str) -> List[User]:
        """Get users by role"""
        return self.db.query(User).filter(
            User.role == role,
            User.is_active == True
        ).all()
    
    def update_last_login(self, user_id: int):
        """Update user's last login timestamp"""
        try:
            user = self.get_user_by_id(user_id)
            if user:
                user.last_login = datetime.now(timezone.utc)
                self.db.commit()
        except Exception as e:
            self.db.rollback()
            st.error(f"Error updating last login: {str(e)}")

class UserProfile:
    """User profile management"""
    
    @staticmethod
    def display_profile_form(user: User):
        """Display user profile edit form"""
        with st.form("profile_form"):
            st.subheader("👤 User Profile")
            
            col1, col2 = st.columns(2)
            
            with col1:
                full_name = st.text_input("Full Name", value=user.full_name or "")
                email = st.text_input("Email", value=user.email, disabled=True)
                phone = st.text_input("Phone", value=user.phone or "")
            
            with col2:
                organization = st.text_input("Organization", value=user.organization or "")
                role = st.selectbox("Role", 
                                   options=['user', 'lawyer', 'admin'], 
                                   value=user.role, 
                                   disabled=True)
                username = st.text_input("Username", value=user.username, disabled=True)
            
            # Password change section
            st.subheader("🔒 Change Password")
            new_password = st.text_input("New Password", type="password")
            confirm_password = st.text_input("Confirm New Password", type="password")
            
            submitted = st.form_submit_button("Update Profile")
            
            if submitted:
                with UserManager() as user_manager:
                    update_data = {
                        'full_name': full_name,
                        'phone': phone,
                        'organization': organization
                    }
                    
                    if new_password and new_password == confirm_password:
                        update_data['password'] = new_password
                    elif new_password and new_password != confirm_password:
                        st.error("Passwords do not match!")
                        return False
                    
                    if user_manager.update_user(user.id, **update_data):
                        st.success("Profile updated successfully!")
                        st.rerun()
                        return True
                    else:
                        st.error("Failed to update profile!")
                        return False

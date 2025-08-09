"""
User Dashboard Component for Case-Verify AI
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List
from database.models import User, Case, Analysis
from database.connection import SessionLocal
from auth.session_manager import get_current_user_id, get_current_user, require_auth
from auth.user_manager import UserManager, UserProfile
from components.case_history import CaseManager

class UserDashboard:
    """User dashboard with overview and quick actions"""
    
    @staticmethod
    @require_auth
    def display_dashboard():
        """Display main user dashboard"""
        st.title("📊 Dashboard")
        
        user = get_current_user()
        user_id = get_current_user_id()
        
        if not user or not user_id:
            st.error("User not found. Please login again.")
            return
        
        # Welcome message
        st.markdown(f"### Welcome back, {user.full_name or user.username}! 👋")
        st.markdown("---")
        
        # Quick stats
        UserDashboard._display_quick_stats(user_id)
        
        st.markdown("---")
        
        # Recent activity and quick actions
        col1, col2 = st.columns([2, 1])
        
        with col1:
            UserDashboard._display_recent_cases(user_id)
        
        with col2:
            UserDashboard._display_quick_actions()
            st.markdown("---")
            UserDashboard._display_upcoming_deadlines(user_id)
        
        st.markdown("---")
        
        # Charts and analytics
        UserDashboard._display_analytics(user_id)
    
    @staticmethod
    def _display_quick_stats(user_id: int):
        """Display quick statistics cards"""
        with CaseManager() as case_manager:
            stats = case_manager.get_case_statistics(user_id)
        
        if not stats:
            st.info("No cases found. Create your first case to see statistics.")
            return
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric(
                label="📁 Total Cases",
                value=stats.get('total_cases', 0),
                delta=f"+{stats.get('recent_cases', 0)} this month"
            )
        
        with col2:
            st.metric(
                label="📝 Draft Cases", 
                value=stats.get('draft_cases', 0)
            )
        
        with col3:
            st.metric(
                label="🔍 Analyzed Cases",
                value=stats.get('analyzed_cases', 0)
            )
        
        with col4:
            st.metric(
                label="📤 Filed Cases",
                value=stats.get('filed_cases', 0)
            )
        
        with col5:
            st.metric(
                label="✅ Closed Cases",
                value=stats.get('closed_cases', 0)
            )
    
    @staticmethod
    def _display_recent_cases(user_id: int):
        """Display recent cases"""
        st.subheader("📋 Recent Cases")
        
        with CaseManager() as case_manager:
            recent_cases = case_manager.get_user_cases(user_id, limit=5)
        
        if not recent_cases:
            st.info("No recent cases found.")
            return
        
        for case in recent_cases:
            with st.container():
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.markdown(f"**{case.title}**")
                    st.caption(f"Type: {case.case_type or 'Not specified'}")
                
                with col2:
                    # Status badge
                    status_colors = {
                        'draft': '🟡',
                        'analyzed': '🔵', 
                        'filed': '🟢',
                        'closed': '⚫'
                    }
                    status_icon = status_colors.get(case.status, '⚪')
                    st.markdown(f"{status_icon} **{case.status.upper()}**")
                
                with col3:
                    days_ago = (datetime.now() - case.created_at).days if case.created_at else 0
                    st.caption(f"{days_ago} days ago")
                    
                    if case.days_remaining is not None:
                        if case.days_remaining < 30:
                            st.error(f"⚠️ {case.days_remaining} days left")
                        elif case.days_remaining < 90:
                            st.warning(f"📅 {case.days_remaining} days left")
                        else:
                            st.info(f"📅 {case.days_remaining} days left")
                
                st.divider()
    
    @staticmethod
    def _display_quick_actions():
        """Display quick action buttons"""
        st.subheader("🚀 Quick Actions")
        
        if st.button("➕ New Case Analysis", type="primary", use_container_width=True):
            st.switch_page("app.py")
        
        if st.button("📁 View All Cases", use_container_width=True):
            st.session_state['show_case_history'] = True
        
        if st.button("📊 Export Data", use_container_width=True):
            st.session_state['show_export_interface'] = True
        
        if st.button("👤 Edit Profile", use_container_width=True):
            st.session_state['show_profile_edit'] = True
        
        if st.button("📈 View Analytics", use_container_width=True):
            st.session_state['show_analytics'] = True
    
    @staticmethod
    def _display_upcoming_deadlines(user_id: int):
        """Display upcoming case deadlines"""
        st.subheader("⏰ Upcoming Deadlines")
        
        with CaseManager() as case_manager:
            # Get cases with remaining days
            cases = case_manager.get_user_cases(user_id)
            urgent_cases = [
                case for case in cases 
                if case.days_remaining is not None and case.days_remaining <= 90
            ]
            
            # Sort by days remaining
            urgent_cases.sort(key=lambda x: x.days_remaining or float('inf'))
        
        if not urgent_cases:
            st.success("✅ No urgent deadlines")
            return
        
        for case in urgent_cases[:3]:  # Show top 3 urgent cases
            days = case.days_remaining
            
            if days < 0:
                st.error(f"🚨 **{case.title}** - Expired {abs(days)} days ago")
            elif days <= 7:
                st.error(f"🚨 **{case.title}** - {days} days left")
            elif days <= 30:
                st.warning(f"⚠️ **{case.title}** - {days} days left")
            else:
                st.info(f"📅 **{case.title}** - {days} days left")
    
    @staticmethod
    def _display_analytics(user_id: int):
        """Display analytics charts"""
        st.subheader("📈 Analytics Overview")
        
        with CaseManager() as case_manager:
            cases = case_manager.get_user_cases(user_id)
        
        if not cases:
            st.info("No data available for analytics.")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Status distribution
            status_data = {}
            for case in cases:
                status_data[case.status] = status_data.get(case.status, 0) + 1
            
            if status_data:
                st.markdown("**Case Status Distribution**")
                status_df = pd.DataFrame(
                    list(status_data.items()), 
                    columns=['Status', 'Count']
                )
                st.bar_chart(status_df.set_index('Status'))
        
        with col2:
            # Priority distribution
            priority_data = {}
            for case in cases:
                priority_data[case.priority] = priority_data.get(case.priority, 0) + 1
            
            if priority_data:
                st.markdown("**Priority Distribution**")
                priority_df = pd.DataFrame(
                    list(priority_data.items()),
                    columns=['Priority', 'Count']
                )
                st.bar_chart(priority_df.set_index('Priority'))
        
        # Cases over time
        if len(cases) > 1:
            st.markdown("**Cases Created Over Time**")
            
            # Group by month
            monthly_data = {}
            for case in cases:
                if case.created_at:
                    month_key = case.created_at.strftime('%Y-%m')
                    monthly_data[month_key] = monthly_data.get(month_key, 0) + 1
            
            if monthly_data:
                monthly_df = pd.DataFrame(
                    list(monthly_data.items()),
                    columns=['Month', 'Cases Created']
                )
                monthly_df['Month'] = pd.to_datetime(monthly_df['Month'])
                monthly_df = monthly_df.sort_values('Month')
                
                st.line_chart(monthly_df.set_index('Month'))
    
    @staticmethod
    @require_auth
    def display_profile_page():
        """Display user profile management page"""
        st.title("👤 User Profile")
        st.markdown("---")
        
        user = get_current_user()
        if not user:
            st.error("User not found. Please login again.")
            return
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            # User info card
            st.markdown("### User Information")
            st.markdown(f"**Username:** {user.username}")
            st.markdown(f"**Email:** {user.email}")
            st.markdown(f"**Role:** {user.role.title()}")
            st.markdown(f"**Member Since:** {user.created_at.strftime('%Y-%m-%d') if user.created_at else 'Unknown'}")
            st.markdown(f"**Last Login:** {user.last_login.strftime('%Y-%m-%d %H:%M') if user.last_login else 'Never'}")
            st.markdown(f"**Status:** {'✅ Active' if user.is_active else '❌ Inactive'}")
            st.markdown(f"**Verified:** {'✅ Yes' if user.is_verified else '⚠️ Pending'}")
        
        with col2:
            # Profile edit form
            UserProfile.display_profile_form(user)
        
        st.markdown("---")
        
        # User statistics
        with UserManager() as user_manager:
            stats = user_manager.get_user_statistics(user.id)
        
        if stats:
            st.markdown("### Account Statistics")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Cases", stats.get('total_cases', 0))
            
            with col2:
                st.metric("Active Cases", stats.get('active_cases', 0))
            
            with col3:
                st.metric("Completed Cases", stats.get('completed_cases', 0))
            
            with col4:
                st.metric("Total Analyses", stats.get('total_analyses', 0))
    
    @staticmethod
    def display_admin_dashboard():
        """Display admin dashboard (for admin users only)"""
        user = get_current_user()
        
        if not user or user.role != 'admin':
            st.error("Access denied. Admin privileges required.")
            return
        
        st.title("🔧 Admin Dashboard")
        st.markdown("---")
        
        # System overview
        UserDashboard._display_system_overview()
        
        st.markdown("---")
        
        # User management
        col1, col2 = st.columns(2)
        
        with col1:
            UserDashboard._display_user_management()
        
        with col2:
            UserDashboard._display_system_actions()
    
    @staticmethod
    def _display_system_overview():
        """Display system-wide statistics for admin"""
        st.subheader("📊 System Overview")
        
        db = SessionLocal()
        try:
            # Count statistics
            total_users = db.query(User).count()
            active_users = db.query(User).filter(User.is_active == True).count()
            total_cases = db.query(Case).count()
            total_analyses = db.query(Analysis).count()
            
            # Recent activity
            recent_users = db.query(User).filter(
                User.created_at >= datetime.now() - timedelta(days=30)
            ).count()
            
            recent_cases = db.query(Case).filter(
                Case.created_at >= datetime.now() - timedelta(days=30)
            ).count()
            
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric("Total Users", total_users, delta=f"+{recent_users} this month")
            
            with col2:
                st.metric("Active Users", active_users)
            
            with col3:
                st.metric("Total Cases", total_cases, delta=f"+{recent_cases} this month")
            
            with col4:
                st.metric("Total Analyses", total_analyses)
            
            with col5:
                # Calculate system health score
                health_score = min(100, (active_users / max(total_users, 1)) * 100)
                st.metric("System Health", f"{health_score:.0f}%")
        
        except Exception as e:
            st.error(f"Error loading system statistics: {str(e)}")
        finally:
            db.close()
    
    @staticmethod
    def _display_user_management():
        """Display user management section"""
        st.subheader("👥 User Management")
        
        with UserManager() as user_manager:
            users = user_manager.get_all_users()
        
        if not users:
            st.info("No users found.")
            return
        
        # User list with actions
        for user in users[:5]:  # Show first 5 users
            with st.container():
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.markdown(f"**{user.username}** ({user.email})")
                    st.caption(f"Role: {user.role} | Joined: {user.created_at.strftime('%Y-%m-%d') if user.created_at else 'Unknown'}")
                
                with col2:
                    status_color = "🟢" if user.is_active else "🔴"
                    verified_status = "✅" if user.is_verified else "⚠️"
                    st.markdown(f"{status_color} {verified_status}")
                
                with col3:
                    if st.button(f"Manage", key=f"manage_{user.id}"):
                        st.session_state[f'manage_user_{user.id}'] = True
                
                st.divider()
        
        if len(users) > 5:
            st.info(f"Showing 5 of {len(users)} users. Use full user management for complete list.")
    
    @staticmethod
    def _display_system_actions():
        """Display system actions for admin"""
        st.subheader("⚙️ System Actions")
        
        if st.button("🔄 Refresh System Cache", use_container_width=True):
            st.success("System cache refreshed!")
        
        if st.button("📊 Generate System Report", use_container_width=True):
            st.info("System report generation initiated...")
        
        if st.button("🗄️ Database Maintenance", use_container_width=True):
            st.info("Database maintenance scheduled...")
        
        if st.button("👥 User Management", use_container_width=True):
            st.session_state['show_full_user_management'] = True
        
        if st.button("📈 System Analytics", use_container_width=True):
            st.session_state['show_system_analytics'] = True

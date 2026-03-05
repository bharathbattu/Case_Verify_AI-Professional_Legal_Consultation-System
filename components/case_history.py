"""
Case History and Management Component for Case-Verify AI
"""
import streamlit as st
import pandas as pd
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, timezone
from database.models import Case, Analysis, User
from database.connection import SessionLocal
from auth.session_manager import get_current_user_id, require_auth
from sanitize import esc

class CaseManager:
    """Manages case operations and database interactions"""
    
    def __init__(self):
        self.db = SessionLocal()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()
    
    def create_case(self, user_id: int, facts: str, relief_sought: str, 
                   pin_code: str, title: str = None, case_type: str = None,
                   case_category: str = None, priority: str = 'medium') -> Optional[Case]:
        """Create a new case"""
        try:
            new_case = Case(
                user_id=user_id,
                title=title or f"Case {datetime.now().strftime('%Y%m%d_%H%M%S')}",
                facts=facts,
                relief_sought=relief_sought,
                pin_code=pin_code,
                case_type=case_type,
                case_category=case_category,
                priority=priority,
                status='draft',
                tags=[]
            )
            
            self.db.add(new_case)
            self.db.commit()
            self.db.refresh(new_case)
            return new_case
            
        except Exception as e:
            self.db.rollback()
            st.error(f"Error creating case: {str(e)}")
            return None
    
    def get_case_by_id(self, case_id: int) -> Optional[Case]:
        """Get case by ID"""
        return self.db.query(Case).filter(Case.id == case_id).first()
    
    def get_user_cases(self, user_id: int, status: str = None, 
                      limit: int = None, offset: int = 0) -> List[Case]:
        """Get cases for a specific user with optional pagination.
        
        P-05: Added ``offset`` parameter for paginated queries.
        """
        query = self.db.query(Case).filter(Case.user_id == user_id)
        
        if status:
            query = query.filter(Case.status == status)
        
        query = query.order_by(Case.created_at.desc())
        
        if offset:
            query = query.offset(offset)
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def count_user_cases(self, user_id: int, status: str = None) -> int:
        """Return total case count for a user (P-05: pagination support)."""
        query = self.db.query(Case).filter(Case.user_id == user_id)
        if status:
            query = query.filter(Case.status == status)
        return query.count()
    
    def update_case(self, case_id: int, **kwargs) -> bool:
        """Update case information"""
        try:
            case = self.get_case_by_id(case_id)
            if not case:
                return False
            
            for key, value in kwargs.items():
                if hasattr(case, key) and value is not None:
                    setattr(case, key, value)
            
            case.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            st.error(f"Error updating case: {str(e)}")
            return False
    
    def delete_case(self, case_id: int) -> bool:
        """Delete a case"""
        try:
            case = self.get_case_by_id(case_id)
            if not case:
                return False
            
            self.db.delete(case)
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            st.error(f"Error deleting case: {str(e)}")
            return False
    
    def duplicate_case(self, case_id: int, user_id: int) -> Optional[Case]:
        """Duplicate an existing case"""
        try:
            original_case = self.get_case_by_id(case_id)
            if not original_case:
                return None
            
            duplicated_case = Case(
                user_id=user_id,
                title=f"{original_case.title} (Copy)",
                facts=original_case.facts,
                relief_sought=original_case.relief_sought,
                pin_code=original_case.pin_code,
                case_type=original_case.case_type,
                case_category=original_case.case_category,
                priority=original_case.priority,
                status='draft',
                tags=original_case.tags.copy() if original_case.tags else []
            )
            
            self.db.add(duplicated_case)
            self.db.commit()
            self.db.refresh(duplicated_case)
            return duplicated_case
            
        except Exception as e:
            self.db.rollback()
            st.error(f"Error duplicating case: {str(e)}")
            return None
    
    def search_cases(self, user_id: int, query: str) -> List[Case]:
        """Search cases by title, facts, or relief sought"""
        search_pattern = f"%{query}%"
        return self.db.query(Case).filter(
            Case.user_id == user_id,
            (Case.title.ilike(search_pattern)) |
            (Case.facts.ilike(search_pattern)) |
            (Case.relief_sought.ilike(search_pattern))
        ).order_by(Case.created_at.desc()).all()
    
    def get_case_statistics(self, user_id: int) -> Dict[str, Any]:
        """Get case statistics for a user"""
        try:
            total_cases = self.db.query(Case).filter(Case.user_id == user_id).count()
            
            draft_cases = self.db.query(Case).filter(
                Case.user_id == user_id,
                Case.status == 'draft'
            ).count()
            
            analyzed_cases = self.db.query(Case).filter(
                Case.user_id == user_id,
                Case.status == 'analyzed'
            ).count()
            
            filed_cases = self.db.query(Case).filter(
                Case.user_id == user_id,
                Case.status == 'filed'
            ).count()
            
            closed_cases = self.db.query(Case).filter(
                Case.user_id == user_id,
                Case.status == 'closed'
            ).count()
            
            recent_cases = self.db.query(Case).filter(
                Case.user_id == user_id,
                Case.created_at >= datetime.now() - timedelta(days=30)
            ).count()
            
            return {
                'total_cases': total_cases,
                'draft_cases': draft_cases,
                'analyzed_cases': analyzed_cases,
                'filed_cases': filed_cases,
                'closed_cases': closed_cases,
                'recent_cases': recent_cases
            }
            
        except Exception as e:
            st.error(f"Error getting case statistics: {str(e)}")
            return {}

class CaseHistory:
    """Case History UI Component"""
    
    def render(self):
        """Public entry point called from app.py tab interface."""
        self.display_case_history()
    
    @staticmethod
    @require_auth
    def display_case_history():
        """Display case history interface"""
        st.header("📁 Case History")
        
        user_id = get_current_user_id()
        if not user_id:
            st.error("User not found. Please login again.")
            return
        
        with CaseManager() as case_manager:
            # Display statistics
            stats = case_manager.get_case_statistics(user_id)
            
            if stats:
                col1, col2, col3, col4, col5 = st.columns(5)
                with col1:
                    st.metric("Total Cases", stats['total_cases'])
                with col2:
                    st.metric("Draft", stats['draft_cases'])
                with col3:
                    st.metric("Analyzed", stats['analyzed_cases'])
                with col4:
                    st.metric("Filed", stats['filed_cases'])
                with col5:
                    st.metric("Recent (30d)", stats['recent_cases'])
            
            # Search and filter section
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                search_query = st.text_input("🔍 Search cases", placeholder="Search by title, facts, or relief...")
            
            with col2:
                status_filter = st.selectbox("Status Filter", 
                                           options=['All', 'draft', 'analyzed', 'filed', 'closed'])
            
            with col3:
                sort_order = st.selectbox("Sort by", 
                                        options=['Newest First', 'Oldest First', 'Title A-Z'])
            
            # --- Pagination settings (P-05) ---
            PAGE_SIZE = 10

            # Get cases based on filters
            if search_query:
                # Search returns all matches; paginate client-side
                all_cases = case_manager.search_cases(user_id, search_query)

                # Sort
                if sort_order == 'Oldest First':
                    all_cases.sort(key=lambda x: x.created_at)
                elif sort_order == 'Title A-Z':
                    all_cases.sort(key=lambda x: x.title or '')
                else:
                    all_cases.sort(key=lambda x: x.created_at, reverse=True)

                total_cases = len(all_cases)
                total_pages = max(1, (total_cases + PAGE_SIZE - 1) // PAGE_SIZE)
                current_page = st.session_state.get("ch_page", 1)
                current_page = min(current_page, total_pages)
                start_idx = (current_page - 1) * PAGE_SIZE
                cases = all_cases[start_idx : start_idx + PAGE_SIZE]
            else:
                status = None if status_filter == 'All' else status_filter
                total_cases = case_manager.count_user_cases(user_id, status=status)
                total_pages = max(1, (total_cases + PAGE_SIZE - 1) // PAGE_SIZE)
                current_page = st.session_state.get("ch_page", 1)
                current_page = min(current_page, total_pages)
                offset = (current_page - 1) * PAGE_SIZE
                cases = case_manager.get_user_cases(
                    user_id, status=status, limit=PAGE_SIZE, offset=offset
                )

                # Sort (DB already sorts newest-first; adjust for user choice)
                if sort_order == 'Oldest First':
                    cases.sort(key=lambda x: x.created_at)
                elif sort_order == 'Title A-Z':
                    cases.sort(key=lambda x: x.title or '')

            # Display cases
            if not cases:
                st.info("No cases found. Create your first case to get started!")
                return

            st.caption(f"Showing page **{current_page}** of **{total_pages}** ({total_cases} cases)")

            # Cases list
            for case in cases:
                CaseHistory._display_case_card(case, case_manager)

            # --- Pagination controls ---
            if total_pages > 1:
                pcol1, pcol2, pcol3 = st.columns([1, 2, 1])
                with pcol1:
                    if current_page > 1:
                        if st.button("◀ Previous", key="ch_prev"):
                            st.session_state["ch_page"] = current_page - 1
                            st.rerun()
                with pcol2:
                    new_page = st.number_input(
                        "Page", min_value=1, max_value=total_pages,
                        value=current_page, step=1, key="ch_page_input",
                        label_visibility="collapsed",
                    )
                    if new_page != current_page:
                        st.session_state["ch_page"] = new_page
                        st.rerun()
                with pcol3:
                    if current_page < total_pages:
                        if st.button("Next ▶", key="ch_next"):
                            st.session_state["ch_page"] = current_page + 1
                            st.rerun()
    
    @staticmethod
    def _display_case_card(case: Case, case_manager: CaseManager):
        """Display individual case card"""
        with st.container():
            # Status color mapping
            status_colors = {
                'draft': '#FFA500',      # Orange
                'analyzed': '#4169E1',   # Blue
                'filed': '#32CD32',      # Green
                'closed': '#808080'      # Gray
            }
            
            status_color = status_colors.get(case.status, '#000000')
            
            # Case header
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            
            with col1:
                st.markdown(f"### {case.title}")
                st.markdown(f"**Case Type:** {case.case_type or 'Not specified'}")
            
            with col2:
                st.markdown(f"<span style='color: {esc(status_color)}; font-weight: bold;'>●</span> **{esc(case.status.upper())}**", 
                           unsafe_allow_html=True)
                st.markdown(f"**Priority:** {case.priority}")
            
            with col3:
                st.markdown(f"**Created:** {case.created_at.strftime('%Y-%m-%d')}")
                if case.limitation_period:
                    st.markdown(f"**Limitation:** {case.limitation_period}")
            
            with col4:
                if case.confidence_score:
                    st.metric("Confidence", f"{case.confidence_score:.1f}/10")
                if case.days_remaining is not None:
                    days_color = 'red' if case.days_remaining < 30 else 'orange' if case.days_remaining < 90 else 'green'
                    st.markdown(f"<span style='color: {esc(days_color)}; font-weight: bold;'>Days Left: {esc(case.days_remaining)}</span>", 
                               unsafe_allow_html=True)
            
            # Case details (expandable)
            with st.expander("View Details"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Facts:**")
                    st.text_area("", value=case.facts, height=100, disabled=True, key=f"facts_{case.id}")
                    
                    if case.court_suggestion:
                        st.markdown(f"**Court Suggestion:** {case.court_suggestion}")
                
                with col2:
                    st.markdown("**Relief Sought:**")
                    st.text_area("", value=case.relief_sought, height=100, disabled=True, key=f"relief_{case.id}")
                    
                    st.markdown(f"**PIN Code:** {case.pin_code}")
                    
                    if case.tags:
                        st.markdown("**Tags:**")
                        for tag in case.tags:
                            st.markdown(
                                f'<span style="display:inline-block;background:#e0e0e0;border-radius:12px;'
                                f'padding:2px 10px;margin:2px 4px 2px 0;font-size:0.85em;">{tag}</span>',
                                unsafe_allow_html=True,
                            )
            
            # Action buttons
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                if st.button("📝 Edit", key=f"edit_{case.id}"):
                    st.session_state[f'edit_case_{case.id}'] = True
            
            with col2:
                if st.button("📋 Duplicate", key=f"duplicate_{case.id}"):
                    duplicated = case_manager.duplicate_case(case.id, case.user_id)
                    if duplicated:
                        st.success(f"Case duplicated successfully!")
                        st.rerun()
            
            with col3:
                if st.button("📊 Analyze", key=f"analyze_{case.id}"):
                    st.session_state['analyze_case_id'] = case.id
                    st.switch_page("pages/analysis.py")
            
            with col4:
                if st.button("📄 Export", key=f"export_{case.id}"):
                    st.session_state['export_case_id'] = case.id
            
            with col5:
                if st.button("🗑️ Delete", key=f"delete_{case.id}", type="secondary"):
                    if st.session_state.get(f'confirm_delete_{case.id}', False):
                        if case_manager.delete_case(case.id):
                            st.success("Case deleted successfully!")
                            st.rerun()
                    else:
                        st.session_state[f'confirm_delete_{case.id}'] = True
                        st.warning("Click again to confirm deletion")
            
            # Edit form (if edit button was clicked)
            if st.session_state.get(f'edit_case_{case.id}', False):
                CaseHistory._display_edit_form(case, case_manager)
            
            st.divider()
    
    @staticmethod
    def _display_edit_form(case: Case, case_manager: CaseManager):
        """Display case edit form"""
        with st.form(f"edit_case_form_{case.id}"):
            st.subheader("Edit Case")
            
            col1, col2 = st.columns(2)
            
            with col1:
                title = st.text_input("Title", value=case.title)
                case_type = st.text_input("Case Type", value=case.case_type or "")
                priority = st.selectbox("Priority", 
                                      options=['low', 'medium', 'high', 'urgent'],
                                      index=['low', 'medium', 'high', 'urgent'].index(case.priority))
            
            with col2:
                pin_code = st.text_input("PIN Code", value=case.pin_code)
                status = st.selectbox("Status",
                                    options=['draft', 'analyzed', 'filed', 'closed'],
                                    index=['draft', 'analyzed', 'filed', 'closed'].index(case.status))
                case_category = st.text_input("Category", value=case.case_category or "")
            
            facts = st.text_area("Facts", value=case.facts, height=150)
            relief_sought = st.text_area("Relief Sought", value=case.relief_sought, height=100)
            
            # Tags input
            tags_input = st.text_input("Tags (comma-separated)", 
                                     value=', '.join(case.tags) if case.tags else "")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("💾 Save Changes", type="primary"):
                    tags = [tag.strip() for tag in tags_input.split(',') if tag.strip()]
                    
                    update_data = {
                        'title': title,
                        'facts': facts,
                        'relief_sought': relief_sought,
                        'pin_code': pin_code,
                        'case_type': case_type,
                        'case_category': case_category,
                        'priority': priority,
                        'status': status,
                        'tags': tags
                    }
                    
                    if case_manager.update_case(case.id, **update_data):
                        st.success("Case updated successfully!")
                        del st.session_state[f'edit_case_{case.id}']
                        st.rerun()
                    else:
                        st.error("Failed to update case!")
            
            with col2:
                if st.form_submit_button("❌ Cancel"):
                    del st.session_state[f'edit_case_{case.id}']
                    st.rerun()

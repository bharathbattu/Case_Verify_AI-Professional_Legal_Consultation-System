"""
Export Interface Component for Case-Verify AI
"""
import streamlit as st
import io
from datetime import datetime
from typing import List, Optional
from database.models import Case, Analysis, User
from database.connection import SessionLocal
from auth.session_manager import get_current_user_id, get_current_user, require_auth
from components.case_history import CaseManager
from exports.pdf_generator import PDFGenerator
from exports.excel_exporter import ExcelExporter

class ExportInterface:
    """Export interface for generating reports and data exports"""
    
    def render(self):
        """Public entry point called from app.py tab interface."""
        self.display_export_interface()
    
    @staticmethod
    @require_auth
    def display_export_interface():
        """Display main export interface"""
        st.header("📄 Export & Reports")
        st.markdown("Generate professional reports and export your case data in various formats.")
        st.markdown("---")
        
        user_id = get_current_user_id()
        user = get_current_user()
        
        if not user_id or not user:
            st.error("User not found. Please login again.")
            return
        
        # Export options tabs
        tab1, tab2, tab3 = st.tabs(["📑 PDF Reports", "📊 Excel Export", "📋 Bulk Export"])
        
        with tab1:
            ExportInterface._display_pdf_export_options(user_id, user)
        
        with tab2:
            ExportInterface._display_excel_export_options(user_id, user)
        
        with tab3:
            ExportInterface._display_bulk_export_options(user_id, user)
    
    @staticmethod
    def _display_pdf_export_options(user_id: int, user: User):
        """Display PDF export options"""
        st.subheader("📑 Generate PDF Reports")
        st.markdown("Create professional legal case analysis reports in PDF format.")
        
        # Get user's cases
        with CaseManager() as case_manager:
            cases = case_manager.get_user_cases(user_id)
        
        if not cases:
            st.info("No cases available for export.")
            return
        
        # Single case report
        st.markdown("### Single Case Report")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            selected_case_id = st.selectbox(
                "Select Case for PDF Report",
                options=[case.id for case in cases],
                format_func=lambda x: next((case.title for case in cases if case.id == x), f"Case {x}"),
                key="pdf_single_case"
            )
        
        with col2:
            include_analysis = st.checkbox("Include AI Analysis", value=True, key="pdf_include_analysis")
        
        if st.button("📄 Generate PDF Report", type="primary", key="generate_single_pdf"):
            ExportInterface._generate_single_case_pdf(selected_case_id, user, include_analysis)
        
        st.markdown("---")
        
        # Multiple cases report
        st.markdown("### Multiple Cases Report")
        
        case_options = {case.id: case.title for case in cases}
        selected_cases = st.multiselect(
            "Select Cases for Bulk PDF Report",
            options=list(case_options.keys()),
            format_func=lambda x: case_options[x],
            key="pdf_multiple_cases"
        )
        
        if selected_cases:
            st.info(f"Selected {len(selected_cases)} cases for bulk report")
            
            if st.button("📄 Generate Bulk PDF Report", type="primary", key="generate_bulk_pdf"):
                ExportInterface._generate_bulk_pdf(selected_cases, user)
    
    @staticmethod
    def _generate_single_case_pdf(case_id: int, user: User, include_analysis: bool = True):
        """Generate PDF for single case"""
        try:
            with st.spinner("Generating PDF report..."):
                # Get case and analysis data
                with CaseManager() as case_manager:
                    case = case_manager.get_case_by_id(case_id)
                
                if not case:
                    st.error("Case not found.")
                    return
                
                # Get latest analysis if requested
                analysis = None
                if include_analysis:
                    db = SessionLocal()
                    try:
                        analysis = db.query(Analysis).filter(
                            Analysis.case_id == case_id
                        ).order_by(Analysis.created_at.desc()).first()
                    finally:
                        db.close()
                
                # Generate PDF
                pdf_generator = PDFGenerator()
                pdf_buffer = pdf_generator.generate_case_report(case, analysis, user)
                
                # Provide download
                filename = f"case_report_{case.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                
                st.download_button(
                    label="📥 Download PDF Report",
                    data=pdf_buffer.getvalue(),
                    file_name=filename,
                    mime="application/pdf",
                    type="primary"
                )
                
                st.success("✅ PDF report generated successfully!")
        
        except Exception as e:
            st.error(f"❌ Error generating PDF: {str(e)}")
    
    @staticmethod
    def _generate_bulk_pdf(case_ids: List[int], user: User):
        """Generate bulk PDF for multiple cases"""
        try:
            with st.spinner("Generating bulk PDF report..."):
                # Get cases
                cases = []
                with CaseManager() as case_manager:
                    for case_id in case_ids:
                        case = case_manager.get_case_by_id(case_id)
                        if case:
                            cases.append(case)
                
                if not cases:
                    st.error("No valid cases found.")
                    return
                
                # Generate PDF
                pdf_generator = PDFGenerator()
                pdf_buffer = pdf_generator.generate_bulk_report(cases, user)
                
                # Provide download
                filename = f"bulk_report_{len(cases)}_cases_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                
                st.download_button(
                    label="📥 Download Bulk PDF Report",
                    data=pdf_buffer.getvalue(),
                    file_name=filename,
                    mime="application/pdf",
                    type="primary"
                )
                
                st.success(f"✅ Bulk PDF report generated for {len(cases)} cases!")
        
        except Exception as e:
            st.error(f"❌ Error generating bulk PDF: {str(e)}")
    
    @staticmethod
    def _display_excel_export_options(user_id: int, user: User):
        """Display Excel export options"""
        st.subheader("📊 Excel Data Export")
        st.markdown("Export case data to Excel format for analysis and record-keeping.")
        
        # Get user's cases
        with CaseManager() as case_manager:
            cases = case_manager.get_user_cases(user_id)
        
        if not cases:
            st.info("No cases available for export.")
            return
        
        # Export options
        col1, col2 = st.columns(2)
        
        with col1:
            export_type = st.radio(
                "Export Type",
                options=["All Cases", "Filtered Cases", "Single Case"],
                key="excel_export_type"
            )
        
        with col2:
            include_details = st.checkbox("Include Detailed Analysis", value=True, key="excel_include_details")
        
        # Filter options for filtered export
        if export_type == "Filtered Cases":
            st.markdown("#### Filter Options")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                status_filter = st.multiselect(
                    "Status",
                    options=['draft', 'analyzed', 'filed', 'closed'],
                    default=['draft', 'analyzed', 'filed', 'closed'],
                    key="excel_status_filter"
                )
            
            with col2:
                priority_filter = st.multiselect(
                    "Priority", 
                    options=['low', 'medium', 'high', 'urgent'],
                    default=['low', 'medium', 'high', 'urgent'],
                    key="excel_priority_filter"
                )
            
            with col3:
                date_range = st.date_input(
                    "Date Range",
                    value=[],
                    key="excel_date_range"
                )
            
            # Apply filters
            filtered_cases = [
                case for case in cases
                if case.status in status_filter 
                and case.priority in priority_filter
            ]
            
            if date_range and len(date_range) == 2:
                start_date, end_date = date_range
                filtered_cases = [
                    case for case in filtered_cases
                    if case.created_at and start_date <= case.created_at.date() <= end_date
                ]
            
            st.info(f"Filtered cases: {len(filtered_cases)} of {len(cases)}")
            cases_to_export = filtered_cases
        
        elif export_type == "Single Case":
            selected_case_id = st.selectbox(
                "Select Case",
                options=[case.id for case in cases],
                format_func=lambda x: next((case.title for case in cases if case.id == x), f"Case {x}"),
                key="excel_single_case"
            )
            cases_to_export = [case for case in cases if case.id == selected_case_id]
        
        else:  # All Cases
            cases_to_export = cases
        
        # Generate Excel export
        if st.button("📊 Generate Excel Export", type="primary", key="generate_excel"):
            ExportInterface._generate_excel_export(cases_to_export, user, include_details, export_type)
    
    @staticmethod
    def _generate_excel_export(cases: List[Case], user: User, include_details: bool, export_type: str):
        """Generate Excel export"""
        try:
            with st.spinner("Generating Excel export..."):
                excel_exporter = ExcelExporter()
                
                if len(cases) == 1 and export_type == "Single Case":
                    # Single case detailed export
                    case = cases[0]
                    
                    # Get analysis if needed
                    analysis = None
                    if include_details:
                        db = SessionLocal()
                        try:
                            analysis = db.query(Analysis).filter(
                                Analysis.case_id == case.id
                            ).order_by(Analysis.created_at.desc()).first()
                        finally:
                            db.close()
                    
                    excel_buffer = excel_exporter.export_single_case_to_excel(case, analysis)
                    filename = f"case_{case.id}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                
                else:
                    # Multiple cases export
                    excel_buffer = excel_exporter.export_cases_to_excel(cases, user)
                    filename = f"cases_export_{len(cases)}_items_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                
                # Provide download
                st.download_button(
                    label="📥 Download Excel File",
                    data=excel_buffer.getvalue(),
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary"
                )
                
                st.success(f"✅ Excel export generated for {len(cases)} cases!")
        
        except Exception as e:
            st.error(f"❌ Error generating Excel export: {str(e)}")
    
    @staticmethod
    def _display_bulk_export_options(user_id: int, user: User):
        """Display bulk export options"""
        st.subheader("📋 Bulk Export Options")
        st.markdown("Export multiple formats and comprehensive data packages.")
        
        # Get user's cases
        with CaseManager() as case_manager:
            cases = case_manager.get_user_cases(user_id)
        
        if not cases:
            st.info("No cases available for export.")
            return
        
        st.markdown("### Export Package Options")
        
        col1, col2 = st.columns(2)
        
        with col1:
            export_pdf = st.checkbox("📄 Include PDF Reports", value=True, key="bulk_export_pdf")
            export_excel = st.checkbox("📊 Include Excel Data", value=True, key="bulk_export_excel")
        
        with col2:
            export_summary = st.checkbox("📋 Include Summary Report", value=True, key="bulk_export_summary")
            export_analytics = st.checkbox("📈 Include Analytics Charts", value=False, key="bulk_export_analytics")
        
        # Export scope
        st.markdown("### Export Scope")
        
        scope_option = st.radio(
            "Select data to export",
            options=["All My Cases", "Recent Cases (Last 30 days)", "Custom Selection"],
            key="bulk_export_scope"
        )
        
        if scope_option == "Recent Cases (Last 30 days)":
            from datetime import timedelta
            recent_date = datetime.now() - timedelta(days=30)
            cases_to_export = [
                case for case in cases 
                if case.created_at and case.created_at >= recent_date
            ]
            st.info(f"Found {len(cases_to_export)} recent cases")
        
        elif scope_option == "Custom Selection":
            case_options = {case.id: f"{case.title} ({case.status})" for case in cases}
            selected_case_ids = st.multiselect(
                "Select specific cases",
                options=list(case_options.keys()),
                format_func=lambda x: case_options[x],
                key="bulk_custom_selection"
            )
            cases_to_export = [case for case in cases if case.id in selected_case_ids]
            
            if selected_case_ids:
                st.info(f"Selected {len(cases_to_export)} cases")
        
        else:  # All My Cases
            cases_to_export = cases
        
        # Export options summary
        if cases_to_export:
            st.markdown("### Export Summary")
            
            export_items = []
            if export_pdf:
                export_items.append("📄 PDF Reports")
            if export_excel:
                export_items.append("📊 Excel Data")
            if export_summary:
                export_items.append("📋 Summary Report")
            if export_analytics:
                export_items.append("📈 Analytics Charts")
            
            st.info(f"Will export {len(cases_to_export)} cases with: {', '.join(export_items)}")
            
            if st.button("🚀 Generate Complete Export Package", type="primary", key="generate_bulk_package"):
                ExportInterface._generate_bulk_package(
                    cases_to_export, user, export_pdf, export_excel, 
                    export_summary, export_analytics
                )
    
    @staticmethod
    def _generate_bulk_package(cases: List[Case], user: User, include_pdf: bool, 
                              include_excel: bool, include_summary: bool, include_analytics: bool):
        """Generate complete export package"""
        try:
            st.info("🚀 Generating complete export package...")
            
            # Progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            generated_files = []
            
            # Generate PDF reports
            if include_pdf:
                status_text.text("📄 Generating PDF reports...")
                progress_bar.progress(0.25)
                
                try:
                    pdf_generator = PDFGenerator()
                    pdf_buffer = pdf_generator.generate_bulk_report(cases, user)
                    
                    filename = f"bulk_pdf_report_{len(cases)}_cases_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                    
                    st.download_button(
                        label="📥 Download PDF Report",
                        data=pdf_buffer.getvalue(),
                        file_name=filename,
                        mime="application/pdf",
                        key="download_bulk_pdf"
                    )
                    
                    generated_files.append("PDF Report")
                except Exception as e:
                    st.warning(f"⚠️ PDF generation failed: {str(e)}")
            
            # Generate Excel export
            if include_excel:
                status_text.text("📊 Generating Excel export...")
                progress_bar.progress(0.50)
                
                try:
                    excel_exporter = ExcelExporter()
                    excel_buffer = excel_exporter.export_cases_to_excel(cases, user)
                    
                    filename = f"bulk_excel_export_{len(cases)}_cases_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                    
                    st.download_button(
                        label="📥 Download Excel Export",
                        data=excel_buffer.getvalue(),
                        file_name=filename,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="download_bulk_excel"
                    )
                    
                    generated_files.append("Excel Export")
                except Exception as e:
                    st.warning(f"⚠️ Excel generation failed: {str(e)}")
            
            # Generate summary report
            if include_summary:
                status_text.text("📋 Generating summary report...")
                progress_bar.progress(0.75)
                
                # Create summary text
                summary_content = ExportInterface._generate_summary_text(cases, user)
                
                st.download_button(
                    label="📥 Download Summary Report",
                    data=summary_content,
                    file_name=f"summary_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                    key="download_bulk_summary"
                )
                
                generated_files.append("Summary Report")
            
            # Complete
            progress_bar.progress(1.0)
            status_text.text("✅ Export package generated successfully!")
            
            st.success(f"🎉 Export package complete! Generated: {', '.join(generated_files)}")
            st.balloons()
        
        except Exception as e:
            st.error(f"❌ Error generating export package: {str(e)}")
    
    @staticmethod
    def _generate_summary_text(cases: List[Case], user: User) -> str:
        """Generate summary text report"""
        summary = f"""
CASE-VERIFY AI - EXPORT SUMMARY REPORT
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
User: {user.full_name or user.username} ({user.email})

=== OVERVIEW ===
Total Cases: {len(cases)}

Status Breakdown:
"""
        
        # Count by status
        status_counts = {}
        priority_counts = {}
        
        for case in cases:
            status_counts[case.status] = status_counts.get(case.status, 0) + 1
            priority_counts[case.priority] = priority_counts.get(case.priority, 0) + 1
        
        for status, count in status_counts.items():
            summary += f"- {status.title()}: {count}\n"
        
        summary += f"\nPriority Breakdown:\n"
        for priority, count in priority_counts.items():
            summary += f"- {priority.title()}: {count}\n"
        
        summary += f"\n=== CASE DETAILS ===\n"
        
        for i, case in enumerate(cases, 1):
            summary += f"""
{i}. {case.title}
   Status: {case.status}
   Priority: {case.priority}
   Type: {case.case_type or 'Not specified'}
   Created: {case.created_at.strftime('%Y-%m-%d') if case.created_at else 'Unknown'}
   Limitation: {case.limitation_period or 'Not determined'}
   Days Remaining: {case.days_remaining if case.days_remaining is not None else 'Not calculated'}
   
   Facts: {case.facts[:200]}{'...' if len(case.facts) > 200 else ''}
   
   Relief: {case.relief_sought[:200]}{'...' if len(case.relief_sought) > 200 else ''}
   
"""
        
        summary += f"""
=== DISCLAIMER ===
This report is generated by Case-Verify AI for informational purposes only.
It should not be considered as professional legal advice.
Always consult with qualified legal practitioners for legal decisions.

Report generated by Case-Verify AI - www.caseverify.ai
"""
        
        return summary

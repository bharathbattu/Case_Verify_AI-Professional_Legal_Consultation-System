"""
PDF Report Generator for Case-Verify AI
"""
import io
from datetime import datetime
from typing import Dict, Any, List, Optional
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart
# Note: matplotlib and seaborn available for future chart generation if needed
# import matplotlib.pyplot as plt
# import seaborn as sns
from database.models import Case, Analysis, User

class PDFGenerator:
    """Professional PDF report generator for legal case analysis"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def setup_custom_styles(self):
        """Setup custom paragraph styles"""
        # Title style
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=20,
            spaceAfter=30,
            textColor=colors.HexColor('#1e2951'),
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        # Header style
        self.header_style = ParagraphStyle(
            'CustomHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            textColor=colors.HexColor('#722f37'),
            fontName='Helvetica-Bold'
        )
        
        # Subheader style
        self.subheader_style = ParagraphStyle(
            'CustomSubHeader',
            parent=self.styles['Heading3'],
            fontSize=12,
            spaceAfter=8,
            textColor=colors.HexColor('#002147'),
            fontName='Helvetica-Bold'
        )
        
        # Body style
        self.body_style = ParagraphStyle(
            'CustomBody',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            alignment=TA_JUSTIFY,
            fontName='Helvetica'
        )
        
        # Warning style
        self.warning_style = ParagraphStyle(
            'Warning',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.red,
            fontName='Helvetica-Bold',
            borderWidth=1,
            borderColor=colors.red,
            leftIndent=10,
            rightIndent=10,
            spaceAfter=10
        )
    
    def generate_case_report(self, case: Case, analysis: Analysis = None, 
                           user: User = None) -> io.BytesIO:
        """Generate comprehensive case analysis report"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        story = []
        
        # Header
        story.extend(self._create_header(case, user))
        story.append(Spacer(1, 20))
        
        # Case Summary
        story.extend(self._create_case_summary(case))
        story.append(Spacer(1, 15))
        
        # Analysis Results
        if analysis:
            story.extend(self._create_analysis_section(analysis))
            story.append(Spacer(1, 15))
        
        # Legal Assessment
        story.extend(self._create_legal_assessment(case, analysis))
        story.append(Spacer(1, 15))
        
        # Recommendations
        story.extend(self._create_recommendations(case, analysis))
        story.append(Spacer(1, 15))
        
        # Footer/Disclaimer
        story.extend(self._create_footer())
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    def _create_header(self, case: Case, user: User = None) -> List:
        """Create PDF header"""
        elements = []
        
        # Title
        elements.append(Paragraph("CASE-VERIFY AI", self.title_style))
        elements.append(Paragraph("Legal Case Analysis Report", self.header_style))
        
        # Report info table
        report_data = [
            ['Report Generated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            ['Case ID:', str(case.id)],
            ['Case Title:', case.title or 'Untitled Case'],
        ]
        
        if user:
            report_data.append(['Prepared for:', user.full_name or user.username])
        
        report_table = Table(report_data, colWidths=[2*inch, 4*inch])
        report_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0'))
        ]))
        
        elements.append(report_table)
        return elements
    
    def _create_case_summary(self, case: Case) -> List:
        """Create case summary section"""
        elements = []
        
        elements.append(Paragraph("CASE SUMMARY", self.header_style))
        
        # Case details table
        case_data = [
            ['Case Type:', case.case_type or 'Not specified'],
            ['Case Category:', case.case_category or 'Not specified'],
            ['Priority Level:', case.priority.upper()],
            ['Current Status:', case.status.upper()],
            ['PIN Code:', case.pin_code],
            ['Created Date:', case.created_at.strftime('%Y-%m-%d')],
        ]
        
        if case.limitation_period:
            case_data.append(['Limitation Period:', case.limitation_period])
        
        if case.court_suggestion:
            case_data.append(['Recommended Court:', case.court_suggestion])
        
        if case.days_remaining is not None:
            urgency_color = colors.red if case.days_remaining < 30 else colors.orange if case.days_remaining < 90 else colors.green
            days_remaining_text = f"{case.days_remaining} days"
            case_data.append(['Days Remaining:', days_remaining_text])
        
        case_table = Table(case_data, colWidths=[2*inch, 4*inch])
        table_style = TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8f9fa'))
        ])
        
        # Apply urgency color to days remaining row if it exists
        if case.days_remaining is not None:
            days_row = len(case_data) - 1  # Last row is days remaining
            table_style.add('TEXTCOLOR', (1, days_row), (1, days_row), urgency_color)
            table_style.add('FONTNAME', (1, days_row), (1, days_row), 'Helvetica-Bold')
        
        case_table.setStyle(table_style)
        
        elements.append(case_table)
        elements.append(Spacer(1, 10))
        
        # Facts section
        elements.append(Paragraph("Facts of the Case:", self.subheader_style))
        elements.append(Paragraph(case.facts, self.body_style))
        elements.append(Spacer(1, 10))
        
        # Relief sought section
        elements.append(Paragraph("Relief Sought:", self.subheader_style))
        elements.append(Paragraph(case.relief_sought, self.body_style))
        
        return elements
    
    def _create_analysis_section(self, analysis: Analysis) -> List:
        """Create AI analysis section"""
        elements = []
        
        elements.append(Paragraph("AI ANALYSIS RESULTS", self.header_style))
        
        # Analysis metadata
        analysis_data = [
            ['Analysis Type:', analysis.analysis_type or 'Standard'],
            ['AI Model Used:', analysis.ai_model_used or 'Gemini'],
            ['Analysis Date:', analysis.created_at.strftime('%Y-%m-%d %H:%M:%S')],
            ['Processing Time:', f"{analysis.processing_time:.2f} seconds" if analysis.processing_time else 'N/A'],
        ]
        
        if analysis.confidence_score:
            analysis_data.append(['Confidence Score:', f"{analysis.confidence_score:.1f}/10"])
        
        if analysis.tokens_used:
            analysis_data.append(['Tokens Used:', str(analysis.tokens_used)])
        
        analysis_table = Table(analysis_data, colWidths=[2*inch, 4*inch])
        analysis_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f4fd'))
        ]))
        
        elements.append(analysis_table)
        elements.append(Spacer(1, 15))
        
        # Detailed analysis results
        if analysis.legal_reasoning:
            elements.append(Paragraph("Legal Reasoning:", self.subheader_style))
            elements.append(Paragraph(analysis.legal_reasoning, self.body_style))
            elements.append(Spacer(1, 10))
        
        # Case classification
        if analysis.case_classification:
            elements.append(Paragraph("Case Classification:", self.subheader_style))
            classification_text = self._format_json_data(analysis.case_classification)
            elements.append(Paragraph(classification_text, self.body_style))
            elements.append(Spacer(1, 10))
        
        # Cost estimation
        if analysis.cost_estimation:
            elements.append(Paragraph("Cost Estimation:", self.subheader_style))
            cost_text = self._format_json_data(analysis.cost_estimation)
            elements.append(Paragraph(cost_text, self.body_style))
            elements.append(Spacer(1, 10))
        
        # Timeline prediction
        if analysis.timeline_prediction:
            elements.append(Paragraph("Timeline Prediction:", self.subheader_style))
            timeline_text = self._format_json_data(analysis.timeline_prediction)
            elements.append(Paragraph(timeline_text, self.body_style))
        
        return elements
    
    def _create_legal_assessment(self, case: Case, analysis: Analysis = None) -> List:
        """Create legal assessment section"""
        elements = []
        
        elements.append(Paragraph("LEGAL ASSESSMENT", self.header_style))
        
        # Limitation analysis
        if case.limitation_period:
            elements.append(Paragraph("Limitation Period Analysis:", self.subheader_style))
            limitation_text = f"The applicable limitation period for this case is {case.limitation_period}."
            
            if case.days_remaining is not None:
                if case.days_remaining < 0:
                    limitation_text += f" <strong>WARNING: The limitation period has expired {abs(case.days_remaining)} days ago.</strong>"
                elif case.days_remaining < 30:
                    limitation_text += f" <strong>URGENT: Only {case.days_remaining} days remaining to file the case.</strong>"
                elif case.days_remaining < 90:
                    limitation_text += f" <strong>CAUTION: {case.days_remaining} days remaining to file the case.</strong>"
                else:
                    limitation_text += f" You have {case.days_remaining} days remaining to file the case."
            
            elements.append(Paragraph(limitation_text, self.body_style))
            elements.append(Spacer(1, 10))
        
        # Court jurisdiction
        if case.court_suggestion:
            elements.append(Paragraph("Recommended Court:", self.subheader_style))
            court_text = f"Based on the case details and jurisdiction, the recommended court is: {case.court_suggestion}"
            elements.append(Paragraph(court_text, self.body_style))
            elements.append(Spacer(1, 10))
        
        # Success probability
        if analysis and analysis.success_probability:
            elements.append(Paragraph("Success Probability:", self.subheader_style))
            success_text = self._format_json_data(analysis.success_probability)
            elements.append(Paragraph(success_text, self.body_style))
        
        return elements
    
    def _create_recommendations(self, case: Case, analysis: Analysis = None) -> List:
        """Create recommendations section"""
        elements = []
        
        elements.append(Paragraph("RECOMMENDATIONS", self.header_style))
        
        # Alternative remedies
        if analysis and analysis.alternative_remedies:
            elements.append(Paragraph("Alternative Legal Remedies:", self.subheader_style))
            remedies_text = self._format_json_data(analysis.alternative_remedies)
            elements.append(Paragraph(remedies_text, self.body_style))
            elements.append(Spacer(1, 10))
        
        # General recommendations
        recommendations = [
            "1. Ensure all relevant documents are properly organized and authenticated.",
            "2. Consider consulting with a qualified legal practitioner for detailed guidance.",
            "3. File the case within the limitation period to avoid dismissal on procedural grounds.",
            "4. Prepare witness statements and evidence in advance.",
            "5. Consider alternative dispute resolution methods if applicable."
        ]
        
        elements.append(Paragraph("General Recommendations:", self.subheader_style))
        for rec in recommendations:
            elements.append(Paragraph(rec, self.body_style))
        
        return elements
    
    def _create_footer(self) -> List:
        """Create PDF footer with disclaimer"""
        elements = []
        
        elements.append(Spacer(1, 20))
        elements.append(Paragraph("IMPORTANT DISCLAIMER", self.header_style))
        
        disclaimer_text = """
        This report is generated by Case-Verify AI, an educational tool designed to provide preliminary legal guidance. 
        The analysis and recommendations contained herein are based on artificial intelligence processing and should not 
        be considered as professional legal advice. Always consult with a qualified legal practitioner before making 
        any legal decisions or filing any cases in court. The developers and operators of Case-Verify AI disclaim any 
        liability for decisions made based on this report.
        """
        
        elements.append(Paragraph(disclaimer_text, self.warning_style))
        
        # Footer info
        footer_text = f"Generated by Case-Verify AI on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | www.caseverify.ai"
        footer_style = ParagraphStyle(
            'Footer',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_CENTER
        )
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(footer_text, footer_style))
        
        return elements
    
    def _format_json_data(self, data: Dict[str, Any]) -> str:
        """Format JSON data for display in PDF"""
        if not data:
            return "No data available"
        
        formatted_text = ""
        for key, value in data.items():
            if isinstance(value, dict):
                formatted_text += f"<strong>{key.replace('_', ' ').title()}:</strong><br/>"
                for sub_key, sub_value in value.items():
                    formatted_text += f"  • {sub_key.replace('_', ' ').title()}: {sub_value}<br/>"
            elif isinstance(value, list):
                formatted_text += f"<strong>{key.replace('_', ' ').title()}:</strong><br/>"
                for item in value:
                    formatted_text += f"  • {item}<br/>"
            else:
                formatted_text += f"<strong>{key.replace('_', ' ').title()}:</strong> {value}<br/>"
        
        return formatted_text
    
    def generate_bulk_report(self, cases: List[Case], user: User = None) -> io.BytesIO:
        """Generate bulk report for multiple cases"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        story = []
        
        # Bulk report header
        story.append(Paragraph("CASE-VERIFY AI", self.title_style))
        story.append(Paragraph("Bulk Case Analysis Report", self.header_style))
        story.append(Spacer(1, 20))
        
        # Summary statistics
        story.extend(self._create_bulk_summary(cases, user))
        story.append(PageBreak())
        
        # Individual case summaries
        for i, case in enumerate(cases):
            if i > 0:
                story.append(PageBreak())
            
            story.append(Paragraph(f"CASE {i+1}: {case.title}", self.header_style))
            story.extend(self._create_case_summary(case))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    def _create_bulk_summary(self, cases: List[Case], user: User = None) -> List:
        """Create summary for bulk report"""
        elements = []
        
        elements.append(Paragraph("SUMMARY OVERVIEW", self.header_style))
        
        # Statistics
        total_cases = len(cases)
        status_counts = {}
        priority_counts = {}
        
        for case in cases:
            status_counts[case.status] = status_counts.get(case.status, 0) + 1
            priority_counts[case.priority] = priority_counts.get(case.priority, 0) + 1
        
        # Summary table
        summary_data = [
            ['Total Cases:', str(total_cases)],
            ['Report Date:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
        ]
        
        if user:
            summary_data.append(['User:', user.full_name or user.username])
        
        # Add status breakdown
        for status, count in status_counts.items():
            summary_data.append([f'{status.title()} Cases:', str(count)])
        
        summary_table = Table(summary_data, colWidths=[2*inch, 4*inch])
        summary_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f8ff'))
        ]))
        
        elements.append(summary_table)
        return elements

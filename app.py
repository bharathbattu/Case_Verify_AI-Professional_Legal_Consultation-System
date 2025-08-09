"""
Case-Verify AI - Phase 3.3 Enhanced Application with User Management
"""
# Load environment variables first
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from agent import analyse, get_language_text, LANGUAGE_SUPPORT, AI_ENABLED
from document_processor import display_document_upload_interface, DOCUMENT_CSS
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Phase 3.3 imports
try:
    from auth import get_authenticator, register_user
    from auth import SessionManager
    from components.case_history import CaseHistory
    from components.user_dashboard import UserDashboard
    from components.export_interface import ExportInterface
    PHASE_3_3_AVAILABLE = True
    logger.info("Phase 3.3 features loaded successfully")
except Exception as e:  # Catch broader exceptions (e.g., SyntaxError/null byte) and fallback cleanly
    PHASE_3_3_AVAILABLE = False
    logger.info(f"Phase 3.3 features not available, running in basic mode: {e}")
    # Provide a minimal stub to satisfy references when advanced auth components are unavailable
    class SessionManager:
        def __init__(self):
            pass
        def is_authenticated(self) -> bool:
            return False

def require_authentication(func):
    """Simple authentication decorator"""
    def wrapper(*args, **kwargs):
        session_manager = SessionManager()
        if not session_manager.is_authenticated():
            st.warning("Please log in to access this feature.")
            return None
        return func(*args, **kwargs)
    return wrapper

# Configure logging was moved up above imports

st.set_page_config(
    page_title="Case-Verify AI", 
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def render_user_management_interface(session_manager):
    """Render user management and authentication interface"""
    if not session_manager.is_authenticated():
        # Login/Register Interface
        tab_login, tab_register = st.tabs(["🔐 Login", "📝 Register"])
        
        with tab_login:
            st.markdown("#### Login to Case-Verify AI")
            authenticator = get_authenticator()
            
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Login")
                
                if submitted:
                    if authenticator.login(username, password):
                        session_manager.create_session_by_username(username)
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
        
        with tab_register:
            st.markdown("#### Register New User")
            with st.form("register_form"):
                reg_username = st.text_input("Username")
                reg_email = st.text_input("Email")
                reg_password = st.text_input("Password", type="password")
                reg_confirm = st.text_input("Confirm Password", type="password")
                reg_full_name = st.text_input("Full Name")
                reg_organization = st.text_input("Organization (Optional)")
                
                submitted = st.form_submit_button("Register")
                
                if submitted:
                    if reg_password != reg_confirm:
                        st.error("Passwords do not match")
                    elif len(reg_password) < 6:
                        st.error("Password must be at least 6 characters")
                    else:
                        try:
                            register_user(
                                username=reg_username,
                                email=reg_email,
                                password=reg_password,
                                full_name=reg_full_name,
                                organization=reg_organization
                            )
                            st.success("Registration successful! Please login.")
                        except Exception as e:
                            st.error(f"Registration failed: {e}")
    else:
        # User Dashboard
        st.markdown("#### User Dashboard")
        user_dashboard = UserDashboard()
        user_dashboard.render()
        
        # Logout button
        if st.button("🚪 Logout"):
            session_manager.destroy_session()
            st.rerun()

def main():
    """Main application function"""
    # Add CSS styling
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=Inter:wght@400;500;600;700&display=swap');
        
        :root {
            --court-navy: #1e2951;
            --legal-burgundy: #722f37;
            --government-blue: #002147;
            --justice-gold: #b8860b;
            --parchment: #fdf6e3;
            --judicial-gray: #4a5568;
            --law-black: #2d3748;
            --official-white: #ffffff;
        }
        
        .stApp {
            background: linear-gradient(135deg, var(--parchment) 0%, #f8f4e6 50%, #f1efeb 100%);
            font-family: 'Inter', sans-serif;
            color: var(--law-black);
        }
        
        .main-header {
            text-align: center;
            font-family: 'Playfair Display', serif;
            font-size: 2.5rem;
            font-weight: 700;
            color: var(--court-navy);
            text-shadow: 2px 2px 4px rgba(30, 41, 81, 0.3);
            margin: 1rem 0;
            padding: 1rem;
            background: linear-gradient(135deg, var(--justice-gold), #daa520);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .sub-header {
            text-align: center;
            font-family: 'Inter', sans-serif;
            font-size: 1.1rem;
            font-weight: 500;
            color: var(--judicial-gray);
            margin-bottom: 2rem;
            letter-spacing: 0.5px;
        }
        
        .case-number {
            text-align: center;
            font-family: 'Inter', sans-serif;
            font-size: 0.9rem;
            font-weight: 600;
            color: var(--government-blue);
            background: var(--official-white);
            padding: 0.8rem;
            border-radius: 8px;
            border: 2px solid var(--justice-gold);
            margin: 1rem 0;
            box-shadow: 0 2px 6px rgba(30, 41, 81, 0.15);
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Add document processing CSS
    st.markdown(DOCUMENT_CSS, unsafe_allow_html=True)
    
    st.markdown('<div class="main-header">⚖️ CASE VERIFICATION REPORT</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Legal Limitation Period Analysis • Indian Jurisdiction</div>', unsafe_allow_html=True)
    
    # Phase 3.3 - Tabbed Interface
    if PHASE_3_3_AVAILABLE:
        # Initialize session manager
        session_manager = SessionManager()
        
        # Create tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "🔍 Case Analysis", 
            "👤 User Management", 
            "📊 Case History", 
            "📋 Export Reports"
        ])
        
        with tab1:
            # Original Case Analysis Interface
            st.markdown("### Legal Case Analysis")
            render_case_analysis_interface()
        
        with tab2:
            # User Management Interface
            st.markdown("### User Management System")
            render_user_management_interface(session_manager)
        
        with tab3:
            # Case History Interface  
            st.markdown("### Case History & Management")
            if session_manager.is_authenticated():
                case_history = CaseHistory()
                case_history.render()
            else:
                st.warning("Please login to access case history.")
        
        with tab4:
            # Export Interface
            st.markdown("### Export Reports & Data")
            if session_manager.is_authenticated():
                export_interface = ExportInterface()
                export_interface.render()
            else:
                st.warning("Please login to access export features.")
    else:
        # Fallback to original single interface
        st.info("Running in basic mode. Phase 3.3 user management features not available.")
        render_case_analysis_interface()

def format_analysis_result(result):
    """Format the analysis result into a professional legal consultation report."""
    if not result:
        return "No analysis result available."
    
    import datetime
    
    # Get comprehensive analysis data
    verdict = result.get('verdict', 'Analysis Complete')
    days_left = result.get('days_left', 0)
    limitation = result.get('limitation', 'Not Specified')
    deadline = result.get('deadline', 'Not Determined')
    confidence = result.get('confidence_score', 0)
    reasoning = result.get('legal_reasoning', 'Legal analysis based on provided facts')
    court_info = result.get('court', {})
    applicable_sections = result.get('applicable_sections', [])
    
    # Professional consultation fields
    practical_advice = result.get('practical_advice', ['Consult with a qualified lawyer and gather all relevant documents'])
    case_strength = result.get('case_strength', 'Assessment depends on evidence quality and legal merits')
    timeline = result.get('estimated_timeline', '6-24 months typically for court proceedings')
    costs = result.get('likely_costs', 'Legal costs vary based on case complexity')
    strategic_recommendations = result.get('strategic_recommendations', ['Seek professional legal advice'])
    precedent_references = result.get('precedent_references', ['Relevant case law to be researched'])
    risk_factors = result.get('risk_factors', ['General litigation risks apply'])
    
    # Format practical advice properly
    if isinstance(practical_advice, list):
        practical_advice_formatted = "  \n".join([f"• {advice.lstrip('0123456789. ')}" for advice in practical_advice])
    else:
        practical_advice_formatted = practical_advice
    
    # Format strategic recommendations
    if isinstance(strategic_recommendations, list):
        strategic_recommendations_formatted = "  \n".join([f"• {rec.lstrip('0123456789. ')}" for rec in strategic_recommendations])
    else:
        strategic_recommendations_formatted = strategic_recommendations
        
    # Format precedent references
    if isinstance(precedent_references, list):
        precedent_references_formatted = "  \n".join([f"• {ref.lstrip('0123456789. ')}" for ref in precedent_references])
    else:
        precedent_references_formatted = precedent_references
        
    # Format risk factors
    if isinstance(risk_factors, list):
        risk_factors_formatted = "  \n".join([f"• {risk.lstrip('0123456789. ')}" for risk in risk_factors])
    else:
        risk_factors_formatted = risk_factors
    
    # Determine case status and styling
    is_within_limitation = days_left > 0
    status_icon = "✅" if is_within_limitation else "⚠️"
    status_color = "#1e3a8a" if is_within_limitation else "#dc2626"
    urgency_level = "IMMEDIATE ACTION REQUIRED" if days_left <= 7 and is_within_limitation else "HIGH PRIORITY" if days_left <= 30 and is_within_limitation else "STANDARD PROCESSING" if is_within_limitation else "LIMITATION REVIEW REQUIRED"
    
    # Format court information
    court_name = court_info.get('name', 'Appropriate Jurisdiction Court')
    court_jurisdiction = court_info.get('jurisdiction', 'As per territorial jurisdiction')
    
    # Format applicable sections with better structure
    sections_text = ""
    if applicable_sections:
        sections_text = f"\n**📋 APPLICABLE LEGAL PROVISIONS:**\n"
        for section in applicable_sections[:5]:  # Limit to 5 sections
            sections_text += f"• {section}\n"
    
    # Professional legal consultation report format
    formatted_result = f"""
<div style="background: linear-gradient(135deg, #f8fafc, #e2e8f0); border: 3px solid {status_color}; border-radius: 15px; padding: 25px; margin: 20px 0; box-shadow: 0 8px 25px rgba(0,0,0,0.1);">

<div style="text-align: center; background: {status_color}; color: white; padding: 20px; border-radius: 10px; margin-bottom: 25px;">
<h2 style="margin: 0; font-family: 'Georgia', serif;">⚖️ LEGAL CONSULTATION REPORT</h2>
<h4 style="margin: 10px 0 0 0; font-weight: normal; opacity: 0.9;">Professional Legal Analysis & Strategic Guidance</h4>
</div>

---

## {status_icon} **EXECUTIVE SUMMARY**

<div style="background: linear-gradient(135deg, #e0f2fe, #b3e5fc); border-left: 5px solid #0277bd; padding: 20px; border-radius: 8px; margin: 15px 0;">
<h4 style="margin: 0 0 10px 0; color: #01579b;">📊 CASE STATUS OVERVIEW</h4>
<table style="width: 100%; border-collapse: collapse;">
<tr><td style="padding: 8px; font-weight: bold; width: 40%;">Legal Position:</td><td style="padding: 8px;"><strong>{verdict}</strong></td></tr>
<tr><td style="padding: 8px; font-weight: bold;">Limitation Status:</td><td style="padding: 8px;"><strong>{days_left} days remaining</strong></td></tr>
<tr><td style="padding: 8px; font-weight: bold;">Filing Deadline:</td><td style="padding: 8px;"><strong>{deadline}</strong></td></tr>
<tr><td style="padding: 8px; font-weight: bold;">Priority Level:</td><td style="padding: 8px; color: {status_color};"><strong>{urgency_level}</strong></td></tr>
<tr><td style="padding: 8px; font-weight: bold;">Analysis Confidence:</td><td style="padding: 8px;"><strong>{confidence}/10</strong></td></tr>
</table>
</div>

---

## **I. LEGAL ANALYSIS & REASONING**

<div style="background: #fafafa; border: 1px solid #e1e5e9; padding: 20px; border-radius: 8px; margin: 15px 0;">
<h4 style="margin: 0 0 15px 0; color: #2d3748;">📖 Professional Legal Assessment</h4>
{reasoning}
</div>

{sections_text}

---

## **II. JURISDICTION & PROCEDURAL GUIDANCE**

<div style="background: #f0f9ff; border: 1px solid #0ea5e9; padding: 20px; border-radius: 8px; margin: 15px 0;">
<h4 style="margin: 0 0 15px 0; color: #0c4a6e;">🏛️ Court Jurisdiction Analysis</h4>
<strong>Recommended Forum:</strong> {court_name}  
<strong>Territorial Jurisdiction:</strong> {court_jurisdiction}  
<strong>Case Category:</strong> {result.get('ai_analysis', {}).get('cause_identified', 'Civil/Commercial Matter')}  
<br><br>
<strong>Procedural Notes:</strong> {result.get('jurisdiction_notes', 'File in appropriate court based on territorial and pecuniary jurisdiction')}
</div>

---

## **III. STRATEGIC CONSULTATION**

<div style="background: #f0fdf4; border: 1px solid #22c55e; padding: 20px; border-radius: 8px; margin: 15px 0;">
<h4 style="margin: 0 0 15px 0; color: #15803d;">💡 Professional Recommendations</h4>
{practical_advice_formatted}
</div>

<div style="background: #fefce8; border: 1px solid #eab308; padding: 20px; border-radius: 8px; margin: 15px 0;">
<h4 style="margin: 0 0 15px 0; color: #a16207;">🎯 Strategic Litigation Plan</h4>
{strategic_recommendations_formatted}
</div>

---

## **IV. CASE ASSESSMENT MATRIX**

<div style="background: #fdf2f8; border: 1px solid #ec4899; padding: 20px; border-radius: 8px; margin: 15px 0;">
<table style="width: 100%; border-collapse: collapse;">
<tr style="background: #f3f4f6;"><th style="padding: 12px; text-align: left; border: 1px solid #d1d5db;">Assessment Parameter</th><th style="padding: 12px; text-align: left; border: 1px solid #d1d5db;">Professional Evaluation</th></tr>
<tr><td style="padding: 12px; border: 1px solid #d1d5db; font-weight: bold;">Case Strength</td><td style="padding: 12px; border: 1px solid #d1d5db;">{case_strength}</td></tr>
<tr><td style="padding: 12px; border: 1px solid #d1d5db; font-weight: bold;">Estimated Timeline</td><td style="padding: 12px; border: 1px solid #d1d5db;">{timeline}</td></tr>
<tr><td style="padding: 12px; border: 1px solid #d1d5db; font-weight: bold;">Financial Implications</td><td style="padding: 12px; border: 1px solid #d1d5db;">{costs}</td></tr>
</table>
</div>

---

## **V. RISK ANALYSIS & MITIGATION**

<div style="background: #fef2f2; border: 1px solid #ef4444; padding: 20px; border-radius: 8px; margin: 15px 0;">
<h4 style="margin: 0 0 15px 0; color: #dc2626;">⚠️ Risk Factors & Mitigation Strategies</h4>
{risk_factors_formatted}
</div>

---

## **VI. LEGAL PRECEDENTS & AUTHORITIES**

<div style="background: #f8fafc; border: 1px solid #64748b; padding: 20px; border-radius: 8px; margin: 15px 0;">
<h4 style="margin: 0 0 15px 0; color: #475569;">📚 Relevant Case Law & Statutory Guidance</h4>
{precedent_references_formatted}
</div>

---

## **VII. IMMEDIATE ACTION PLAN**"""

    # Add specific action plan based on urgency
    if is_within_limitation:
        if days_left <= 7:
            formatted_result += f"""

<div style="background: linear-gradient(135deg, #fef3c7, #fde68a); border: 3px solid #f59e0b; padding: 20px; border-radius: 10px; margin: 15px 0;">
<h4 style="margin: 0 0 15px 0; color: #92400e;">🚨 CRITICAL TIMELINE - IMMEDIATE ACTION REQUIRED</h4>
<strong>Days Remaining:</strong> {days_left} days  
<strong>Priority Actions:</strong>
• Draft and file petition immediately within {days_left} days
• Gather all supporting documents and evidence today
• Engage qualified legal counsel without any delay
• Arrange court fees and complete filing formalities
• Prepare witness statements and documentary evidence
</div>"""
        elif days_left <= 30:
            formatted_result += f"""

<div style="background: linear-gradient(135deg, #dbeafe, #bfdbfe); border: 3px solid #3b82f6; padding: 20px; border-radius: 10px; margin: 15px 0;">
<h4 style="margin: 0 0 15px 0; color: #1e40af;">⚡ HIGH PRIORITY - EXPEDITED PREPARATION</h4>
<strong>Days Remaining:</strong> {days_left} days  
<strong>Strategic Actions:</strong>
• Begin comprehensive legal document drafting
• Systematically collect and organize all evidence
• Retain experienced legal counsel for case strategy
• Conduct detailed legal research and precedent analysis
• Prepare comprehensive witness statements
</div>"""
        else:
            formatted_result += f"""

<div style="background: linear-gradient(135deg, #dcfce7, #bbf7d0); border: 3px solid #22c55e; padding: 20px; border-radius: 10px; margin: 15px 0;">
<h4 style="margin: 0 0 15px 0; color: #15803d;">✅ ADEQUATE TIME AVAILABLE - STRATEGIC PREPARATION</h4>
<strong>Days Remaining:</strong> {days_left} days  
<strong>Comprehensive Approach:</strong>
• Conduct thorough legal research and case law analysis
• Engage in comprehensive evidence collection and documentation
• Consider alternative dispute resolution mechanisms
• Obtain multiple legal opinions for strategy optimization
• Prepare detailed case timeline and documentation
</div>"""
    else:
        formatted_result += f"""

<div style="background: linear-gradient(135deg, #fee2e2, #fecaca); border: 3px solid #ef4444; padding: 20px; border-radius: 10px; margin: 15px 0;">
<h4 style="margin: 0 0 15px 0; color: #dc2626;">⚠️ LIMITATION CONCERNS - SPECIALIZED CONSULTATION REQUIRED</h4>
<strong>Status:</strong> Limitation period issues require immediate attention  
<strong>Urgent Measures:</strong>
• Immediate consultation with limitation law specialist
• Explore condonation of delay applications under Section 5 Limitation Act
• Review for continuing cause of action or saved limitation periods
• Consider alternative legal remedies and fresh cause of action
• Assess prospects for challenging limitation computation
</div>"""

    # Professional conclusion
    formatted_result += f"""

---

<div style="background: linear-gradient(135deg, #e0f2fe, #b3e5fc); border: 2px solid #0277bd; padding: 25px; border-radius: 12px; margin: 20px 0;">
<h4 style="margin: 0 0 15px 0; color: #01579b; text-align: center;">📋 PROFESSIONAL CONSULTATION SUMMARY</h4>

**Analysis Methodology:** {"AI-Enhanced Legal Research & Precedent Analysis" if confidence >= 8 else "Comprehensive Legal Framework Analysis"}  
**Confidence Level:** {confidence}/10 (Professional Grade Assessment)  
**Assessment Date:** {result.get('ai_analysis', {}).get('date_reasoning', 'Based on comprehensive factual and legal analysis')}  

<div style="background: #fff3e0; border-left: 4px solid #ff9800; padding: 15px; margin: 15px 0; border-radius: 5px;">
<strong>🔒 LEGAL DISCLAIMER:</strong> This consultation report is prepared based on information provided and general legal principles. For specific legal strategy, court representation, and detailed case preparation, engage qualified legal counsel licensed to practice in the relevant jurisdiction. This analysis serves as preliminary guidance and does not constitute attorney-client relationship.
</div>

<div style="text-align: center; margin-top: 20px; color: #64748b; font-style: italic;">
<strong>Prepared by: Case-Verify AI Legal Consultation System</strong><br>
<strong>Report Generation: </strong>{datetime.datetime.now().strftime('%d %B %Y at %I:%M %p')}
</div>
</div>

</div>
"""
    
    return formatted_result
    
    # Determine case status and styling
    is_within_limitation = days_left > 0
    status_icon = "✅" if is_within_limitation else "⚠️"
    status_color = "#28a745" if is_within_limitation else "#dc3545"
    urgency_level = "HIGH PRIORITY" if days_left <= 30 and is_within_limitation else "MODERATE" if is_within_limitation else "CRITICAL REVIEW REQUIRED"
    
    # Format court information
    court_name = court_info.get('name', 'Appropriate Jurisdiction Court')
    court_jurisdiction = court_info.get('jurisdiction', 'As per territorial jurisdiction')
    
    # Format applicable sections
    sections_text = ""
    if applicable_sections:
        sections_text = f"\n**📋 Applicable Legal Provisions:**\n"
        for section in applicable_sections[:5]:  # Limit to 5 sections
            sections_text += f"• {section}\n"
    
    # Enhanced professional formatting
    formatted_result = f"""
<div style="border: 2px solid {status_color}; border-radius: 12px; padding: 20px; margin: 15px 0; background: linear-gradient(135deg, #f8f9fa, #e9ecef);">

### {status_icon} **LEGAL CASE ANALYSIS REPORT**

<div style="background: {status_color}; color: white; padding: 12px; border-radius: 8px; margin: 10px 0;">
<h4 style="margin: 0; text-align: center;">📊 CASE STATUS: {verdict}</h4>
</div>

---

#### **⏰ LIMITATION ANALYSIS**
| **Parameter** | **Details** |
|---------------|-------------|
| **Days Remaining** | **{days_left} days** |
| **Legal Deadline** | **{deadline}** |
| **Limitation Period** | {limitation} |
| **Urgency Level** | **{urgency_level}** |

---

#### **�️ JURISDICTION & FORUM**
- **Recommended Court**: {court_name}
- **Territorial Jurisdiction**: {court_jurisdiction}
- **Case Category**: {result.get('ai_analysis', {}).get('cause_identified', 'General Civil Matter')}

---

#### **📖 LEGAL REASONING & ANALYSIS**
{reasoning}

{sections_text}

---

#### **💡 PRACTICAL ANALYSIS & GUIDANCE**

**🎯 Practical Advice:**  
{practical_advice_formatted}

**💪 Case Strength Assessment:**  
{result.get('case_strength', 'Case strength depends on evidence quality and legal merits')}

**⏰ Estimated Timeline:**  
{result.get('estimated_timeline', '6-24 months depending on court workload and case complexity')}

**💰 Likely Costs:**  
{result.get('likely_costs', '₹50,000 - ₹2,00,000 depending on case complexity and court level')}

---

#### **⚖️ PROFESSIONAL RECOMMENDATIONS**

"""

    # Add specific recommendations based on status
    if is_within_limitation:
        if days_left <= 7:
            formatted_result += """
<div style="background: #fff3cd; border: 2px solid #ffc107; padding: 15px; border-radius: 8px; margin: 10px 0;">
<strong>🚨 IMMEDIATE ACTION REQUIRED</strong><br>
• File petition within {days_left} days<br>
• Gather all supporting documents immediately<br>
• Engage legal counsel without delay<br>
• Prepare court fees and filing requirements
</div>
""".format(days_left=days_left)
        elif days_left <= 30:
            formatted_result += """
<div style="background: #d1ecf1; border: 2px solid #17a2b8; padding: 15px; border-radius: 8px; margin: 10px 0;">
<strong>⚡ URGENT PREPARATION NEEDED</strong><br>
• Begin drafting legal documents<br>
• Collect and organize evidence<br>
• Consult with qualified legal counsel<br>
• Review case precedents and legal strategy
</div>
""".format(days_left=days_left)
        else:
            formatted_result += """
<div style="background: #d4edda; border: 2px solid #28a745; padding: 15px; border-radius: 8px; margin: 10px 0;">
<strong>✅ CASE WITHIN LIMITATION</strong><br>
• Adequate time available for proper case preparation<br>
• Conduct thorough legal research<br>
• Gather comprehensive evidence and documentation<br>
• Consider alternative dispute resolution options
</div>
"""
    else:
        formatted_result += """
<div style="background: #f8d7da; border: 2px solid #dc3545; padding: 15px; border-radius: 8px; margin: 10px 0;">
<strong>⚠️ LIMITATION PERIOD CONCERNS</strong><br>
• Immediate legal consultation required<br>
• Explore condonation of delay options<br>
• Review for any saved limitation grounds<br>
• Consider alternative legal remedies
</div>
"""

    # Add confidence and technical details
    formatted_result += f"""

---

#### **📊 ANALYSIS METRICS**
- **AI Confidence Score**: {confidence}/10 
- **Analysis Method**: {"AI-Enhanced Legal Heuristics" if confidence >= 7 else "Rule-Based Legal Framework"}
- **Date Assessment**: {result.get('ai_analysis', {}).get('date_reasoning', 'Based on factual timeline analysis')}

---

<div style="background: #e7f3ff; border-left: 4px solid #007bff; padding: 15px; margin: 15px 0;">
<strong>📝 DISCLAIMER:</strong> This analysis is based on the information provided and general legal principles. For specific legal advice and strategy, please consult with a qualified legal practitioner familiar with your jurisdiction and case specifics.
</div>

</div>
"""
    
    return formatted_result

def render_case_analysis_interface():
    """Render the original case analysis interface"""
    # Phase 2: Language Selection
    col_lang, col_spacer = st.columns([2, 6])
    with col_lang:
        language = st.selectbox(
            "🌐 Language / भाषा",
            options=["english", "hindi"],
            format_func=lambda x: "English" if x == "english" else "हिन्दी"
        )

    # Generate case number
    import datetime
    case_number = f"CVA-{datetime.datetime.now().strftime('%Y%m%d')}-{datetime.datetime.now().strftime('%H%M%S')}"
    st.markdown(f'<div class="case-number">📋 Case No: {case_number}</div>', unsafe_allow_html=True)

    # AI Status Notice
    if not AI_ENABLED:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #3498db, #2980b9); color: white; padding: 1rem; border-radius: 10px; margin: 1rem 0; border: 2px solid #2980b9;">
            <h4 style="margin: 0;">ℹ️ OFFLINE MODE ACTIVE</h4>
            <p style="margin: 0.5rem 0 0 0; font-size: 0.9em;">AI analysis unavailable. Using intelligent fallback system based on legal heuristics. Results may be less detailed but still legally sound.</p>
        </div>
        """, unsafe_allow_html=True)

    # Document Processing Section
    display_document_upload_interface()

    # Main Analysis Interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Primary Analysis Section
        st.markdown("### 📋 Case Facts")
        facts = st.text_area(
            label="Describe your case facts in detail:",
            value="",
            height=200,
            key="facts",
            placeholder="Example: I lent ₹50,000 to my friend on 15th January 2022. Despite multiple requests, he has not returned the money. We have a written agreement and WhatsApp messages as evidence."
        )
        
        st.markdown("### 📂 Case Type")
        case_type = st.selectbox(
            label="Select the type of legal case:",
            options=[
                "Select Case Type",
                "Civil - Money Recovery", 
                "Civil - Property Dispute",
                "Civil - Contract Breach",
                "Criminal - Cheque Bounce",
                "Criminal - Fraud/Cheating",
                "Family - Divorce/Maintenance",
                "Family - Child Custody",
                "Consumer - Defective Goods/Services",
                "Labour - Employment Dispute",
                "Property - Rent/Lease Issues",
                "Other"
            ],
            key="case_type",
            index=0
        )
        
        st.markdown("### ⚖️ Relief Sought")
        relief = st.text_area(
            label="What legal remedy do you want?", 
            value="",
            height=100,
            key="relief",
            placeholder="Example: I want my money back with interest and compensation for legal expenses."
        )
        
        st.markdown("### 📍 PIN Code")
        pin_code = st.text_input(
            label="Enter your PIN code for jurisdiction:",
            max_chars=6,
            key="pin_code",
            placeholder="e.g., 110001"
        )
        
        # Professional analyze button
        analyze_clicked = st.button(
            "🔍 Analyze Case",
            type="primary",
            use_container_width=True
        )
    
    with col2:
        # Sidebar with professional legal information
        st.markdown("### 📋 CASE DOCUMENTATION")
        st.markdown("""
        **JURISDICTION:** Republic of India  
        **APPLICABLE LAWS:**
        - Limitation Act, 1963
        - Consumer Protection Act, 2019
        - Civil Procedure Code, 1908
        - Arbitration & Conciliation Act, 2015
        
        **COURT HIERARCHY:**
        - Supreme Court of India
        - High Courts (24)
        - District Courts
        - Subordinate Courts
        
        **LIMITATION PERIODS:**
        - Civil Suits: 3 years
        - Consumer Complaints: 2 years
        - Arbitration: 3 years
        - Recovery of Money: 3 years
        """)
    
    # Analysis Results Section
    if analyze_clicked:
        if not facts.strip():
            st.error("⚠️ Please enter case facts to analyze.")
        elif case_type == "Select Case Type":
            st.error("⚠️ Please select a case type.")
        else:
            try:
                with st.spinner("🔍 Analyzing your case..."):
                    # Perform analysis
                    analysis_result = analyse(facts, relief, pin_code, case_type)
                    
                    if analysis_result:
                        # Display results in professional format
                        st.markdown("---")
                        st.markdown('<div class="section-header">📋 Case Analysis Report</div>', unsafe_allow_html=True)
                        
                        # Create columns for structured display
                        col_left, col_right = st.columns([2, 1])
                        
                        with col_left:
                            # Format and display the analysis result
                            formatted_result = format_analysis_result(analysis_result)
                            st.markdown(formatted_result, unsafe_allow_html=True)
                        
                        with col_right:
                            # Analysis metadata
                            st.markdown("### 📊 ANALYSIS METADATA")
                            st.markdown(f"""
                            **Analysis Date:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
                            **Language:** {language.upper()}  
                            **Case ID:** {case_number}  
                            **Status:** ✅ COMPLETED  
                            """)
                            
            except ValueError as e:
                error_message = str(e)
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #f39c12, #e67e22); color: white; padding: 1.5rem; border-radius: 10px; border: 2px solid #e67e22;">
                    <h4 style="margin: 0;">⚠️ INPUT VALIDATION ERROR</h4>
                    <p style="margin: 0.5rem 0 0 0;">{error_message}</p>
                    <p style="margin: 0.5rem 0 0 0; font-size: 0.9em;">Please verify your input and ensure all required fields are completed accurately.</p>
                </div>
                """, unsafe_allow_html=True)
                logger.error(f"Input validation error: {str(e)}")
            except Exception as e:
                error_details = str(e)
                error_type = type(e).__name__
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #e74c3c, #c0392b); color: white; padding: 1.5rem; border-radius: 10px; border: 2px solid #c0392b;">
                    <h4 style="margin: 0;">❌ SYSTEM ERROR</h4>
                    <p style="margin: 0.5rem 0 0 0;">An unexpected error occurred during analysis. Please retry or contact technical support.</p>
                    <details style="margin-top: 1rem;">
                        <summary style="cursor: pointer;">Error Details (for debugging)</summary>
                        <p style="font-family: monospace; font-size: 0.8rem; margin: 0.5rem 0 0 0;">
                            <strong>Type:</strong> {error_type}<br>
                            <strong>Message:</strong> {error_details}
                        </p>
                    </details>
                </div>
                """, unsafe_allow_html=True)
                logger.error(f"System error: {error_type}: {error_details}")
                
                # Try to provide helpful information
                st.info("💡 **Troubleshooting Tips:**\n- Check that all fields are filled correctly\n- Ensure PIN code is valid (6 digits)\n- Try refreshing the page and analyzing again")

    # Professional footer
    st.markdown("""
    <div style="background: linear-gradient(135deg, var(--court-navy), var(--government-blue)); color: var(--official-white); padding: 1.5rem; border-radius: 8px; margin: 2rem 0; box-shadow: 0 2px 8px rgba(30, 41, 81, 0.3); border: 1px solid var(--justice-gold); text-align: center;">
        <p style="margin: 0; line-height: 1.6; font-size: 0.9rem; font-family: 'Inter', sans-serif; font-weight: 500; color: #fef3c7;">
            🏛️ Professional Legal Analysis System | Powered by Advanced AI Technology
        </p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()

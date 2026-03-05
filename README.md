# Case Verify AI - Professional Legal Consultation System

An advanced AI-powered legal assistant for the Indian legal system that generates **professional-grade legal consultation reports**. Transform basic case analysis into comprehensive legal documents with strategic recommendations, precedent references, and risk assessments.

##  Professional Features

###  Professional Legal Consultation Reports
Our system generates sophisticated 7-section legal consultation reports that include:

- ** Executive Summary**: Concise case overview with key findings
- ** Legal Analysis**: Detailed statutory and case law analysis
- ** Jurisdiction Guidance**: Precise court assignment and venue determination
- ** Strategic Consultation**: Actionable legal strategies and recommendations
- ** Case Assessment Matrix**: Structured evaluation of case strength and viability
- ** Risk Analysis**: Comprehensive risk factors and mitigation strategies
- ** Legal Precedents**: Relevant case law and statutory provisions
- ** Immediate Action Plan**: Time-sensitive steps and deadlines

###  Enhanced AI Capabilities
- **Strategic Recommendations**: Senior advocate-level strategic guidance
- **Precedent References**: Relevant case law and legal authorities
- **Risk Factor Analysis**: Comprehensive risk assessment and mitigation
- **Professional Formatting**: Legal document styling with color-coded sections
- **Confidence Scoring**: AI confidence levels (1-10 scale) for transparency

##  Quick Start

### Prerequisites
- Python 3.11 or higher
- Google Gemini API key (Optional - works in offline mode)
- Windows PowerShell or Command Prompt

### Installation

1. **Navigate to project directory:**
   ```bash
   cd d:\case-verify-ai
   ```

2. **Set up virtual environment:**
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1  # PowerShell
   # or
   .\venv\Scripts\activate.bat  # Command Prompt
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment (optional):**
   ```bash
   # Create .env file and add your API key:
   echo GEMINI_API_KEY=your_actual_api_key_here > .env
   
   # Note: Application works perfectly in offline mode without API key
   ```

5. **Initialize database (optional):**
   ```bash
   python init_database.py
   ```

6. **Launch the application:**
   ```bash
   # Option 1: Direct launch
   streamlit run app.py --server.port 8520
   
   # Option 2: Use startup scripts
   .\start_case_verify.ps1  # PowerShell (Recommended)
   .\start_case_verify.bat  # Command Prompt
   ```

7. **Access the application:**
   Open your browser and go to: `http://localhost:8520`

##  System Features

### Core Legal Analysis Engine
-  **Comprehensive Case Coverage**: 60+ case types across 10 legal categories
-  **Professional AI Analysis**: Google Gemini with enhanced legal consultation prompts
-  **Multi-Language Support**: Hindi/English bilingual interface
-  **Legal Provisions Database**: Extensive precedent cases and statutory references
-  **Smart Court Assignment**: Automatic jurisdiction and hierarchy determination
-  **Limitation Calculator**: Precise deadline calculations with legal reasoning
-  **Professional UI**: Legal institution-styled interface with document formatting
-  **Robust Error Handling**: Comprehensive error management with UTF-8 support
-  **Offline Functionality**: Works without internet or API key
-  **Performance Optimized**: Response caching and efficient processing

### Professional Output Format
Our system generates consultation reports that include:

```
 LEGAL CONSULTATION REPORT
═══════════════════════════════

 EXECUTIVE SUMMARY
• Case Type: [Analysis]
• Jurisdiction: [Court Assignment]
• Limitation Status: [Days Remaining]
• Overall Assessment: [Professional Opinion]

 LEGAL ANALYSIS
• Applicable Laws: [Statutory Framework]
• Case Strength: [Professional Assessment]
• Legal Grounds: [Detailed Analysis]

 JURISDICTION GUIDANCE
• Recommended Court: [Specific Court]
• Territorial Jurisdiction: [Geographic Details]
• Pecuniary Jurisdiction: [Financial Limits]

 STRATEGIC CONSULTATION
• Recommended Approach: [Strategy]
• Alternative Options: [Backup Plans]
• Timeline Considerations: [Critical Dates]

 CASE ASSESSMENT MATRIX
• Merits Evaluation: [Structured Analysis]
• Success Probability: [Realistic Assessment]
• Resource Requirements: [Cost/Time Estimates]

 RISK ANALYSIS
• Primary Risks: [Key Concerns]
• Mitigation Strategies: [Risk Management]
• Contingency Planning: [Backup Options]

 LEGAL PRECEDENTS
• Relevant Case Law: [Citations]
• Statutory Provisions: [Legal Framework]
• Supporting Authorities: [References]

 IMMEDIATE ACTION PLAN
• Priority Actions: [Urgent Steps]
• Documentation Required: [Evidence Checklist]
• Filing Deadlines: [Critical Dates]
```

##  Supported Legal Areas

###  Financial & Commercial Law
- ** Money Recovery Claims** - 3 years (Limitation Act, 1963 - Art 54)
- ** Cheque Dishonour Cases** - 3 years (Limitation Act, 1963 - Art 137)
- ** Banking Disputes** - 3 years (Banking Regulation Act, 1949)
- ** Insurance Claims** - 3 years (Insurance Act, 1938)
- ** Corporate Disputes** - 3 years (Companies Act, 2013)
- ** Securities Fraud** - 3 years (SEBI Act, 1992)
- ** Arbitration Matters** - 3 years (Arbitration Act, 2015)
- ** Commercial Fraud** - 3 years (Limitation Act, 1963 - Art 134)

###  Consumer Protection
- ** Consumer Complaints** - 2 years (Consumer Protection Act, 2019)
- ** Medical Negligence** - 2 years (Limitation Act, 1963 - Art 134)
- ** Motor Accident Claims** - 2 years (Motor Vehicles Act, 1988)
- ** Food Adulteration** - 3 years (Food Safety Act, 2006)

###  Family & Matrimonial Law
- ** Divorce Proceedings** - 1 year (Limitation Act, 1963 - Art 120)
- ** Child Custody** - 1 year (Guardian & Wards Act, 1890)
- ** Maintenance Claims** - 1 year (CrPC, 1973 - Section 125)
- ** Property Partition** - 12 years (Limitation Act, 1963 - Art 120)

###  Property & Real Estate
- ** Property Disputes** - 12 years (Limitation Act, 1963 - Art 65)
- ** Rent Control Matters** - 3 years (Limitation Act, 1963 - Art 113)
- ** Land Acquisition** - 3 years (Land Acquisition Act, 2013)
- ** Forest Rights** - 3 years (Forest Rights Act, 2006)

###  Constitutional & Civil Rights
- ** Writ Petitions** - 1 year (Constitution - Article 226)
- ** Public Interest Litigation** - 1 year (Constitution - Article 32)
- ** Habeas Corpus** - No limitation (Constitution - Article 32)
- ** Disability Rights** - 1 year (Rights of PWD Act, 2016)
- ** Senior Citizen Rights** - 1 year (Senior Citizens Act, 2007)

###  Employment & Labor Law
- ** Service Matters** - 1 year (Central Civil Services Rules)
- ** Industrial Disputes** - 1 year (Industrial Disputes Act, 1947)
- ** Provident Fund Claims** - 3 years (EPF Act, 1952)
- ** Gratuity Claims** - 5 years (Payment of Gratuity Act, 1972)
- ** Workmen Compensation** - 2 years (Workmen's Compensation Act, 1923)

###  Environmental Law
- ** Environmental Pollution** - 5 years (Environment Protection Act, 1986)
- ** Air Pollution** - 5 years (Air Pollution Act, 1981)
- ** Noise Pollution** - 2 years (Noise Pollution Rules, 2000)
- ** Water Disputes** - 3 years (Water Disputes Act, 1956)

###  Technology & IP Law
- ** Cybercrime Cases** - 3 years (IT Act, 2000 - Section 77B)
- ** Patent Disputes** - 3 years (Patents Act, 1970)
- ** Trademark Infringement** - 3 years (Trade Marks Act, 1999)
- ** Copyright Violations** - 3 years (Copyright Act, 1957)

###  Criminal & Special Laws
- ** Domestic Violence** - 1 year (Domestic Violence Act, 2005)
- ** Sexual Harassment** - 1 year (Sexual Harassment Act, 2013)
- ** Dowry Harassment** - 3 years (Dowry Prohibition Act, 1961)
- ** SC/ST Atrocity Cases** - 1 year (SC/ST Prevention of Atrocities Act)

###  Tax & Revenue Law
- ** Income Tax Disputes** - 4 years (Income Tax Act, 1961)
- ** GST Disputes** - 3 years (CGST Act, 2017)
- ** Customs Duty** - 5 years (Customs Act, 1962)
- ** Excise Duty** - 5 years (Central Excise Act, 1944)

##  System Architecture

```
User Input (Case Facts, Relief Sought, Location)
    ↓
Professional Streamlit Interface (app.py)
    ↓
Input Validation & Processing
    ↓
Enhanced AI Analysis Engine (agent.py)
    ↓ 
Google Gemini AI + Professional Legal Prompt
    ↓
Legal Rules Database & Jurisdiction Mapping
    ↓
Professional Legal Consultation Report Generation
    ↓
7-Section Formatted Output with Strategic Analysis
```

##  Project Structure

```
case-verify-ai/                    # Clean, optimized project structure
├──  Core Application
│   ├── agent.py                   # Enhanced AI analysis engine with professional prompts
│   ├── app.py                     # Streamlit interface with professional report formatting
│   └── init_database.py           # Database initialization
├──  Configuration
│   ├── requirements.txt           # Python dependencies
│   ├── .env                       # Environment variables (create from example)
│   └── case_verify.db            # SQLite database
├──  Database Layer
│   ├── database/
│   │   ├── __init__.py
│   │   ├── connection.py          # Database connectivity
│   │   └── models.py              # Data models
├──  Authentication System
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── authenticator.py       # Main authentication logic
│   │   ├── session_manager.py     # Session management
│   │   ├── simple_auth.py         # Simple authentication methods
│   │   └── user_manager.py        # User management
├──  Components
│   ├── components/
│   │   ├── __init__.py
│   │   ├── case_history.py        # Case history tracking
│   │   ├── export_interface.py    # Export functionality
│   │   └── user_dashboard.py      # User dashboard
├──  Export System
│   ├── exports/
│   │   ├── __init__.py
│   │   ├── email_sender.py        # Email export functionality
│   │   ├── excel_exporter.py      # Excel export
│   │   └── pdf_generator.py       # PDF generation
├──  Legal Rules Database
│   ├── rules/
│   │   ├── court_hierarchy.json   # Court system mapping
│   │   ├── detailed_provisions.json # Legal provisions database
│   │   ├── forum.json             # Court jurisdiction mappings
│   │   ├── language_support.json  # Multi-language support
│   │   └── limitation.json        # Limitation periods database
├──  Configuration
│   └── config/
│       └── auth_config.yaml       # Authentication configuration
├──  Startup Scripts
│   ├── start_case_verify.ps1      # PowerShell startup script
│   └── start_case_verify.bat      # Batch startup script
└──  Documentation
    └── README.md                  # This comprehensive guide
```

##  Testing & Validation

### Comprehensive Test Suite (441 tests, ≥ 70% coverage)
-  **Unit Tests**: Core functionality — agent, auth, session, user management
-  **Integration Tests**: End-to-end workflow validation
-  **Performance Tests**: Response time and efficiency testing
-  **AI Response Tests**: Mock AI response handling and parsing
-  **Error Handling Tests**: Comprehensive error scenario coverage
-  **Security Tests**: Input sanitization and authentication paths
-  **Observability Tests**: Metrics, health checks, and structured logging

### Run Tests
```bash
# Run full test suite with coverage report
python -m pytest --cov=. --cov-report=term-missing --forceExit --no-coverage -p no:cacheprovider

# Run specific test files
python -m pytest test_agent.py test_auth_init.py test_session_manager.py -v

# Test performance
python -m pytest test_performance.py -v
```

### Coverage Summary
| Module | Coverage |
|---|---|
| `agent.py` | 95% |
| `auth/authenticator.py` | 96% |
| `auth/session_manager.py` | 92% |
| `auth/simple_auth.py` | 98% |
| `auth/user_manager.py` | 81% |
| `database/connection.py` | 100% |
| `database/models.py` | 97% |
| `enhanced_analytics.py` | 91% |
| `metrics.py` | 94% |
| `sanitize.py` | 100% |
| `structured_logging.py` | 100% |
| **Overall** | **70%** |

##  Database Operations & Backup (Op-05)

The application uses **SQLite** (`case_verify.db`) as its primary database. Because SQLite stores the entire database in a single file, backups are straightforward and can be automated with any scheduler (cron, Task Scheduler, etc.).

### Manual Backup

```bash
# SQL dump (portable, human-readable)
sqlite3 case_verify.db .dump > backup_$(date +%Y%m%d).sql

# Binary file copy (fastest — safe only when no writes are in-flight)
cp case_verify.db case_verify_$(date +%Y%m%d).db

# Windows equivalents
sqlite3 case_verify.db .dump > backup_%DATE:~-4,4%%DATE:~-7,2%%DATE:~0,2%.sql
copy case_verify.db case_verify_%DATE:~-4,4%%DATE:~-7,2%%DATE:~0,2%.db
```

### Automated Daily Backup (Linux/macOS cron)

```cron
# Run at 02:00 every day — keep backups in /var/backups/case_verify/
0 2 * * * sqlite3 /opt/case_verify/case_verify.db .dump > /var/backups/case_verify/backup_$(date +\%Y\%m\%d).sql
```

### Automated Daily Backup (Windows Task Scheduler)

Create a `backup_db.bat` script in the project root:

```batch
@echo off
set BACKUP_DIR=C:\Backups\case_verify
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"
sqlite3 case_verify.db .dump > "%BACKUP_DIR%\backup_%DATE:~-4,4%%DATE:~-7,2%%DATE:~0,2%.sql"
```

Then schedule it via **Task Scheduler** to run daily.

### Restore from Backup

```bash
# Restore from SQL dump
sqlite3 case_verify_restored.db < backup_20260101.sql

# Or simply copy the binary backup back
cp case_verify_20260101.db case_verify.db
```

### Recommended Retention Policy
- **Daily** backups retained for **7 days**
- **Weekly** backups retained for **4 weeks**
- **Monthly** backups retained for **6 months**

---

##  Security & Compliance

### Security Features
-  **API Key Protection**: Environment variable storage with .env exclusion
-  **Input Validation**: Comprehensive sanitization and validation
-  **Error Handling**: Secure error messages without data exposure
-  **Session Management**: Secure user session handling
-  **Database Security**: SQLite with proper access controls

### Legal Compliance
-  **Educational Purpose**: Tool for educational and demonstration purposes only
-  **No Legal Advice**: Does not constitute professional legal advice
-  **Professional Consultation**: Always consult qualified lawyers for legal matters

##  Usage Guide

### Basic Workflow
1. **Launch Application**: Run startup script or streamlit command
2. **Enter Case Details**: Provide case facts, relief sought, and location (PIN code)
3. **AI Analysis**: Click "Analyse Case" for professional consultation report
4. **Review Results**: Examine the 7-section professional legal consultation
5. **Strategic Planning**: Use strategic recommendations for case preparation

### Professional Output Example
When you analyze a case, you'll receive a comprehensive report like this:

```
 LEGAL CONSULTATION REPORT
Case Reference: [Auto-generated ID]
Analysis Date: [Current Date]
═══════════════════════════════════════

 EXECUTIVE SUMMARY
The matter pertains to [case type] under [applicable law]. 
Based on preliminary analysis, the case appears [viable/challenging] 
with [X] days remaining for filing. Jurisdiction lies with [specific court].

 LEGAL ANALYSIS
Applicable statutory provisions include [relevant acts and sections].
The case involves [legal issues] and requires [specific documentation].
Precedent analysis indicates [case law support/challenges].

 JURISDICTION GUIDANCE
Recommended Court: [Specific court name and location]
Territorial Jurisdiction: [Geographic boundaries]
Filing Requirements: [Specific procedures and fees]

 STRATEGIC CONSULTATION
Primary Strategy: [Recommended legal approach]
Alternative Approaches: [Backup strategies]
Critical Considerations: [Key factors for success]

 CASE ASSESSMENT MATRIX
Merits Score: [X/10] - [Detailed rationale]
Success Probability: [Percentage] - [Risk factors]
Time Sensitivity: [Critical/Moderate/Low] - [Timeline analysis]

 RISK ANALYSIS
Primary Risks: [Key challenges and obstacles]
Mitigation Strategies: [Risk management approaches]
Contingency Planning: [Alternative courses of action]

 LEGAL PRECEDENTS
Relevant Case Law: [Citations with brief summaries]
Supporting Statutes: [Applicable legal provisions]
Judicial Interpretations: [Key legal principles]

 IMMEDIATE ACTION PLAN
1. [Priority action with deadline]
2. [Document preparation requirements]
3. [Strategic preparation steps]
```

### Advanced Features
- **Multi-language Support**: Switch between Hindi and English
- **Export Options**: PDF, Excel, and email export capabilities
- **Case History**: Track and review previous analyses
- **User Dashboard**: Personalized analysis tracking
- **Offline Mode**: Full functionality without internet connection

##  Development & Contribution

### Development Setup
```bash
# Clone repository
git clone [repository-url]
cd case-verify-ai

# Setup environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run in development mode
streamlit run app.py --server.port 8520
```

### Code Standards
- **Python 3.11+**: Modern Python features and syntax
- **Type Hints**: Use type annotations for clarity
- **Error Handling**: Comprehensive exception management
- **Documentation**: Clear docstrings and comments
- **Testing**: Unit tests for all core functionality

### Contributing Guidelines
1. **Fork the repository** and create feature branch
2. **Write tests** for new functionality
3. **Follow code standards** and existing patterns
4. **Test thoroughly** including edge cases
5. **Submit pull request** with clear description

##  Performance & Optimization

### System Performance
- **Response Time**: < 3 seconds for AI analysis
- **Memory Usage**: Optimized for efficient resource utilization
- **Database**: SQLite for fast local operations
- **Caching**: Intelligent caching for repeated queries
- **Error Recovery**: Graceful fallback systems

### Optimization Features
- **Lazy Loading**: Components loaded on demand
- **Response Caching**: Avoid redundant AI calls
- **Efficient Parsing**: Optimized JSON processing
- **Memory Management**: Automatic cleanup and garbage collection

##  Version History & Roadmap

### Current Version: v2.0 Professional
-  Professional legal consultation reports with 7-section format
-  Enhanced AI prompts for strategic recommendations
-  Clean project structure with optimized file organization
-  Comprehensive testing and validation suite
-  Professional document styling and formatting

### Upcoming Features
-  **Advanced Analytics**: Case success prediction algorithms
-  **Document Generator**: Auto-generate legal documents
-  **API Development**: RESTful API for integration
-  **Cloud Deployment**: Scalable cloud hosting options
-  **Mobile App**: Native mobile application
-  **Legal Research**: Integrated case law research tools

##  Important Legal Disclaimer

**This tool is for educational and demonstration purposes only.**

-  **Not Legal Advice**: Does not constitute professional legal advice
-  **Consult Professionals**: Always consult qualified lawyers for legal matters
-  **Educational Tool**: Designed for learning and case preparation assistance
-  **No Liability**: Users assume full responsibility for legal decisions
-  **Verification Required**: All analysis should be independently verified

##  Support & Contact

### Getting Help
- **Documentation**: This comprehensive README
- **Issues**: Report bugs via GitHub issues
- **Questions**: Create discussion threads for queries
- **Contributions**: Submit pull requests for improvements

### Technical Support
- **System Requirements**: Python 3.11+, Windows/Linux/Mac
- **Dependencies**: All requirements listed in requirements.txt
- **Troubleshooting**: Check logs and error messages
- **Performance**: Monitor resource usage and optimization

---

**Built with for the Indian Legal System**

*Professional legal consultation powered by AI technology*

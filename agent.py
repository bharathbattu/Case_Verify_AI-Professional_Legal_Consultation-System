import json, os, datetime, logging, hashlib, time, threading
import google.generativeai as genai
from dotenv import load_dotenv
from typing import Dict, Any, Optional
from collections import OrderedDict
from metrics import (
    inc_analyses, inc_analysis_error,
    inc_cache_hit, inc_cache_miss,
    observe_api_latency,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
# Security Fix: Use environment variable instead of hardcoded key
api_key = os.getenv("GEMINI_API_KEY")
AI_ENABLED = (bool(api_key) and 
              api_key != "your_api_key_here" and 
              len(api_key.strip()) > 20 and
              not api_key.startswith("<ENTER_YOU"))

if not AI_ENABLED:
    logger.warning("GEMINI_API_KEY not found, invalid, or is placeholder. Running in offline fallback mode (no external AI calls).")
    model = None
else:
    try:
        genai.configure(api_key=api_key)
        # Test the API key by creating a model
        model = genai.GenerativeModel(
            "gemini-1.5-flash",
            generation_config={
                "temperature": 0.2,
                "top_p": 0.9,
                "top_k": 40,
                "max_output_tokens": 1024,
            }
        )
        logger.info("AI model successfully initialized")
    except Exception as e:
        logger.error("Failed to initialize AI model: %s", e)
        AI_ENABLED = False
        model = None

# Load data files — fail gracefully with clear diagnostics
_RULES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'rules')

def _load_rule_file(filename: str) -> dict:
    """Load a JSON rule file from the rules/ directory with error handling."""
    filepath = os.path.join(_RULES_DIR, filename)
    try:
        with open(filepath, encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error("Rule file not found: %s", filepath)
        raise SystemExit(f"FATAL: Required rule file missing: {filepath}")
    except json.JSONDecodeError as exc:
        logger.error("Malformed JSON in %s: %s", filepath, exc)
        raise SystemExit(f"FATAL: Cannot parse rule file {filepath}: {exc}")

LIMIT = _load_rule_file('limitation.json')
FORUM = _load_rule_file('forum.json')
COURT_HIERARCHY = _load_rule_file('court_hierarchy.json')
DETAILED_PROVISIONS = _load_rule_file('detailed_provisions.json')
LANGUAGE_SUPPORT = _load_rule_file('language_support.json')

PROMPT = """
You are a Senior Advocate practicing at the High Court with 15+ years of specialized litigation experience in Indian Courts. Provide a comprehensive legal consultation report as you would for a high-value client.

CLIENT CONSULTATION BRIEF:
- Case Category: {case_type}
- Statement of Facts: {facts}
- Relief Sought by Client: {relief}
- Territorial Jurisdiction (PIN): {pin}

PROVIDE PROFESSIONAL LEGAL CONSULTATION REPORT:

LEGAL ANALYSIS FRAMEWORK:
1. **CAUSE OF ACTION ANALYSIS**: Identify precise legal grounds and when they crystallized
2. **STATUTORY PROVISIONS**: Cite specific applicable laws with section-wise relevance
3. **PRECEDENTIAL GUIDANCE**: Reference relevant legal principles and court approaches
4. **PROCEDURAL ROADMAP**: Detailed litigation strategy with court-specific procedures
5. **RISK ASSESSMENT**: Professional evaluation of success probability and challenges

CASE-SPECIFIC EVALUATION CRITERIA:
- **CONTRACTUAL DISPUTES**: Breach date, notice periods, specific performance vs. damages
- **NEGOTIABLE INSTRUMENTS**: Cheque presentation, demand notice timeline, criminal vs. civil remedies
- **CONSUMER PROTECTION**: Service deficiency occurrence, compensation quantum, forum selection
- **PROPERTY MATTERS**: Title disputes, possession issues, revenue record status
- **EMPLOYMENT LAW**: Termination validity, statutory compliance, compensation entitlement
- **FAMILY LAW**: Matrimonial grounds, maintenance, custody considerations

PROFESSIONAL CONSULTATION OUTPUT (JSON FORMAT):
{{
    "cause": "Specific legal cause of action with professional terminology",
    "start_date": "YYYY-MM-DD",
    "confidence_score": integer_1_to_10,
    "legal_reasoning": "Detailed professional analysis explaining legal principles, statutory interpretation, and case law application relevant to the client's situation",
    "applicable_sections": ["Primary Act - Section X: Detailed legal provision and its application", "Supporting Act - Section Y: Secondary legal basis", "Procedural Code - Section Z: Court procedure relevance"],
    "jurisdiction_notes": "Specific court jurisdiction with territorial and pecuniary details, filing procedures, and expected case flow",
    "practical_advice": ["Document preservation and evidence collection strategy", "Immediate legal steps and compliance requirements", "Pre-litigation settlement options and timeline", "Court filing preparation and documentation"],
    "case_strength": "Professional assessment with percentage likelihood of success, potential challenges, and strategic considerations",
    "estimated_timeline": "Realistic litigation timeline with court-specific schedules and appeal prospects",
    "likely_costs": "Comprehensive cost breakdown in Indian Rupees (₹) including court fees, advocate fees, miscellaneous expenses",
    "strategic_recommendations": ["Primary litigation strategy with risk mitigation", "Alternative dispute resolution options", "Evidence strengthening measures", "Timeline optimization suggestions"],
    "precedent_references": ["Relevant case law citations", "Statutory interpretations", "High Court/Supreme Court guidelines"],
    "risk_factors": ["Potential legal challenges", "Limitation period concerns", "Enforcement difficulties", "Cost-benefit analysis"]
}}

PROFESSIONAL STANDARDS:
- Use precise legal terminology appropriate for court proceedings
- Provide comprehensive analysis suitable for case preparation
- Include strategic litigation planning
- Reference relevant legal precedents and statutory provisions
- Deliver professional-grade legal consultation
"""

def get_cache_key(facts: str, relief: str, pin: str, case_type: Optional[str] = None) -> str:
    """Generate cache key for the analysis request."""
    combined = f"{facts.strip().lower()}{relief}{pin}{case_type or ''}"
    return hashlib.sha256(combined.encode()).hexdigest()

def get_language_text(key: str, language: str = "english") -> str:
    """
    Get text in specified language (Phase 2 Multi-language Support).
    
    Args:
        key: Text key to translate
        language: Target language (english/hindi)
        
    Returns:
        Translated text or English fallback
    """
    try:
        if language == "hindi":
            hindi_data = LANGUAGE_SUPPORT["hindi_translations"]
            # Navigate nested keys (e.g., "interface.title")
            keys = key.split(".")
            result = hindi_data
            for k in keys:
                result = result[k]
            return result
        return key  # Return key as fallback for English
    except (KeyError, TypeError):
        return key  # Fallback to original key

def get_smart_fallback_date(facts: str, relief: str) -> str:
    """
    Generate a smart fallback date based on case facts and relief type.
    
    Args:
        facts: Case facts
        relief: Relief sought
        
    Returns:
        Estimated date in YYYY-MM-DD format
    """
    # Smart date estimation based on keywords and patterns
    import re
    from datetime import datetime, timedelta
    
    # Look for explicit dates in facts
    date_patterns = [
        r'\b(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{4})\b',
        r'\b(\d{4})[\/\-](\d{1,2})[\/\-](\d{1,2})\b',
        r'\b(\d{1,2})\s+(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{4})\b'
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, facts.lower())
        if match:
            try:
                if 'january' in pattern:
                    months = {'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6,
                             'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12}
                    day, month_name, year = match.groups()
                    month = months[month_name]
                    return f"{year}-{month:02d}-{int(day):02d}"
                else:
                    groups = match.groups()
                    if len(groups[2]) == 4:  # YYYY-MM-DD
                        return f"{groups[2]}-{int(groups[1]):02d}-{int(groups[0]):02d}"
                    else:  # DD-MM-YYYY
                        return f"{groups[2]}-{int(groups[1]):02d}-{int(groups[0]):02d}"
            except (ValueError, IndexError, KeyError):
                continue
    
    # Fallback based on time indicators
    now = datetime.now()
    
    time_indicators = {
        'yesterday': 1, 'last week': 7, 'last month': 30, 'last year': 365,
        'few days ago': 5, 'few weeks ago': 21, 'few months ago': 90,
        'recently': 14, 'some time ago': 60
    }
    
    for indicator, days_ago in time_indicators.items():
        if indicator in facts.lower():
            fallback_date = now - timedelta(days=days_ago)
            return fallback_date.strftime("%Y-%m-%d")
    
    # Default conservative fallback (6 months ago)
    fallback_date = now - timedelta(days=180)
    return fallback_date.strftime("%Y-%m-%d")

def map_relief_to_key(relief: str) -> str:
    """Map user relief input to limitation.json keys."""
    if not relief:
        return 'fraud'  # Default fallback
        
    relief_lower = relief.lower()
    
    # Mapping logic with comprehensive keywords
    if any(word in relief_lower for word in ['money', 'debt', 'loan', 'payment', 'refund', 'recover', 'amount', 'rupees', '₹']):
        return 'money-recovery'
    elif any(word in relief_lower for word in ['cheque', 'check', 'bounce', 'dishonor', 'npa', 'bounced']):
        return 'cheque-bounce'
    elif any(word in relief_lower for word in ['consumer', 'service', 'product', 'deficiency', 'complaint', 'defective', 'faulty']):
        return 'consumer-complaint'
    elif any(word in relief_lower for word in ['divorce', 'marriage', 'matrimonial', 'separation', 'maintenance']):
        return 'divorce'
    elif any(word in relief_lower for word in ['property', 'land', 'house', 'plot', 'real estate', 'possession']):
        return 'property-dispute'
    elif any(word in relief_lower for word in ['contract', 'agreement', 'breach', 'violation']):
        return 'breach-of-contract'
    elif any(word in relief_lower for word in ['injury', 'accident', 'negligence', 'medical']):
        return 'medical-negligence'
    elif any(word in relief_lower for word in ['employment', 'job', 'salary', 'termination', 'wrongful dismissal']):
        return 'employment-dispute'
    elif any(word in relief_lower for word in ['rent', 'lease', 'tenant', 'landlord', 'eviction']):
        return 'rent-dispute'
    elif any(word in relief_lower for word in ['insurance', 'claim', 'policy']):
        return 'insurance-claim'
    else:
        return 'fraud'  # Default fallback

def get_court_details(relief_key: str, facts: str, pin: str) -> dict:
    """Get appropriate court details based on case type and location using COURT_HIERARCHY."""
    details = COURT_HIERARCHY.get(relief_key)
    if not details:
        # Sensible defaults
        details = {
            "court_type": "District Court",
            "hierarchy": "District Court / Sub-Judge",
            "jurisdiction": "Territorial jurisdiction of the district court",
            "description": "General civil/criminal matters as applicable"
        }
    # Personalize jurisdiction with PIN context when available
    jurisdiction = details.get("jurisdiction", "Territorial jurisdiction")
    if pin:
        jurisdiction = f"{jurisdiction} • PIN {pin}"
    return {
        "court_type": details.get("court_type", "District Court"),
        "hierarchy": details.get("hierarchy", "District Court"),
        "jurisdiction": jurisdiction,
        "description": details.get("description", "")
    }

# Cache and rate limiting — bounded LRU cache prevents unbounded memory growth
_CACHE_MAXSIZE = 256

class _LRUCache(OrderedDict):
    """Simple LRU cache backed by OrderedDict."""
    def __init__(self, maxsize: int = _CACHE_MAXSIZE):
        super().__init__()
        self._maxsize = maxsize

    def get_item(self, key: str):
        if key in self:
            self.move_to_end(key)
            return self[key]
        return None

    def put_item(self, key: str, value: Any):
        if key in self:
            self.move_to_end(key)
        self[key] = value
        if len(self) > self._maxsize:
            self.popitem(last=False)

_response_cache = _LRUCache()
_last_api_call = 0
_api_call_delay = 1  # seconds between API calls
_API_TIMEOUT = 30  # seconds for Gemini API calls
_api_lock = threading.Lock()  # protects _last_api_call and _response_cache

def analyse(facts: str, relief: str, pin: str, case_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Analyze a legal case and determine limitation period status.
    
    Args:
        facts: Case facts
        relief: Relief sought  
        pin: PIN code for jurisdiction
        case_type: Type of case (optional)
        
    Returns:
        Dictionary with analysis results
    """
    global _last_api_call
    
    # O-02: Count every analysis attempt (labelled by mapped relief type)
    relief_key_for_metrics = map_relief_to_key(relief)
    inc_analyses(relief_type=relief_key_for_metrics)

    # Map relief to appropriate limitation key before validation
    relief_key = map_relief_to_key(relief)
    
    # Input validation (strict) — raise exceptions for invalid inputs
    errors = validate_inputs(facts, relief_key, pin)
    if errors:
        # Raise ValueError with a concise combined message (tests check exception raised)
        raise ValueError("; ".join(errors.values()))
    
    # Generate cache key
    cache_key = get_cache_key(facts, relief, pin, case_type)
    
    # Check cache first (thread-safe)
    with _api_lock:
        cached = _response_cache.get_item(cache_key)
    if cached is not None:
        logger.info("Using cached analysis result")
        inc_cache_hit()
        data = cached
    else:
        inc_cache_miss()
        # relief_key already mapped above
        logger.info("Analyzing case: relief='%s' mapped to '%s', pin=%s", relief, relief_key, pin)
        
        if not AI_ENABLED:
            # Enhanced offline mode analysis
            logger.warning("AI model unavailable. Using enhanced offline legal analysis framework.")
            fallback_date = get_smart_fallback_date(facts, relief)
            
            # Generate professional offline analysis
            applicable_acts = []
            detailed_reasoning = ""
            
            # Enhanced fallback based on case type and relief
            if relief_key == "money-recovery":
                applicable_acts = [
                    "Indian Contract Act, 1872 - Section 73: Compensation for loss or damage caused by breach of contract", 
                    "Civil Procedure Code, 1908 - Order II Rule 2: Suit for compensation must include all reliefs",
                    "Interest Act, 1978 - Section 3: Rate of interest in absence of contract"
                ]
                detailed_reasoning = "Money recovery suits are governed by contractual obligations and limitation periods. The cause of action typically accrues from the date of breach or when payment becomes due. Courts examine the nature of agreement, consideration, and performance obligations."
                practical_advice = [
                    "Preserve original loan/service agreements and payment records",
                    "Issue formal legal notice demanding payment with specific timeline",
                    "Collect evidence of money advanced including bank statements",
                    "Document all communication regarding payment defaults"
                ]
                case_strength = "75-85% success probability with documented agreements. Moderate (60%) with oral agreements but strong witness testimony."
                timeline = "12-18 months for District Court trial, additional 12-24 months if appealed to High Court"
                costs = "₹50,000 - ₹1,50,000 (court fees ₹10,000-25,000, advocate fees ₹30,000-1,00,000, miscellaneous ₹10,000-25,000)"
                strategic_recommendations = [
                    "Consider summary suit under Order XXXVII CPC for faster resolution",
                    "Explore mediation/arbitration clauses in agreement",
                    "File for interim attachment of debtor's assets if flight risk exists"
                ]
                precedent_references = [
                    "Bhagwandas Goverdhandas Kedia v. Girdharilal Parshottamdas (1966) - Contract breach principles",
                    "Union of India v. Raman Iron Foundry (1974) - Interest calculation methodology"
                ]
                risk_factors = [
                    "Debtor's financial capacity to pay decree amount",
                    "Availability of assets for execution proceedings",
                    "Counter-claims or set-off defenses by defendant"
                ]
            elif relief_key == "cheque-bounce":
                applicable_acts = [
                    "Negotiable Instruments Act, 1881 - Section 138: Dishonor of cheque for insufficiency of funds",
                    "Criminal Procedure Code, 1973 - Section 142: Complaint for offence under Section 138 NI Act",
                    "Civil Procedure Code, 1908 - Section 9: Civil court jurisdiction for civil remedies"
                ]
                detailed_reasoning = "Cheque bounce cases involve both criminal and civil remedies. Criminal complaint under Section 138 requires strict compliance with statutory timeline. Civil suit for damages provides additional compensation avenue."
                practical_advice = [
                    "File criminal complaint within one month of legal notice period expiry",
                    "Maintain original bounced cheque and bank return memo",
                    "Send legal notice by registered post within 30 days of cheque return",
                    "Consider simultaneous civil suit for enhanced compensation"
                ]
                case_strength = "90-95% success rate with proper statutory compliance. Criminal conviction almost certain with valid notice."
                timeline = "6-12 months for Magistrate Court disposal, civil suit may take 18-24 months"
                costs = "₹25,000 - ₹75,000 (court fees ₹5,000-15,000, advocate fees ₹15,000-50,000, miscellaneous ₹5,000-10,000)"
                strategic_recommendations = [
                    "File both criminal complaint and civil suit for maximum recovery",
                    "Apply for interim compensation under Section 143A NI Act",
                    "Consider plea bargaining for faster resolution with compensation"
                ]
                precedent_references = [
                    "Rangappa v. Sri Mohan (2010) - Strict compliance with Section 138 requirements",
                    "Meters and Instruments Pvt. Ltd. v. Kanchan Mehta (2018) - Enhanced compensation guidelines"
                ]
                risk_factors = [
                    "Defendant's financial status for compensation payment",
                    "Technical defenses regarding notice service",
                    "Limitation period compliance verification"
                ]
            elif relief_key == "consumer-complaint":
                applicable_acts = [
                    "Consumer Protection Act, 2019 - Section 35: Consumer's right to be heard and assured of fair treatment",
                    "Contract Act, 1872 - Section 73: Compensation for breach including consumer service contracts",
                    "Sale of Goods Act, 1930 - Section 55: Rights of buyer as against seller for breach of warranty"
                ]
                detailed_reasoning = "Consumer protection provides accessible forum with simplified procedures and powers for award of compensation, replacement, and punitive damages. Service deficiency includes inadequate, deficient, faulty, or imperfect service."
                practical_advice = [
                    "File complaint in appropriate consumer forum based on compensation sought",
                    "Document service deficiency with photographs, bills, and correspondence",
                    "Calculate actual loss plus mental agony compensation",
                    "Submit manufacturer/service provider response to complaint"
                ]
                case_strength = "80-90% success rate with clear service deficiency documentation. Consumer forums favor consumer protection."
                timeline = "6-18 months in consumer forums, significantly faster than regular civil courts"
                costs = "₹10,000 - ₹40,000 (nominal court fees, advocate fees ₹5,000-25,000, documentation ₹2,000-5,000)"
                strategic_recommendations = [
                    "Utilize consumer forum's simplified procedure advantage",
                    "Claim punitive damages for deterrent effect",
                    "Consider class action if multiple consumers affected"
                ]
                precedent_references = [
                    "Spring Meadows Hospital v. Harjol Ahluwalia (1998) - Medical negligence compensation",
                    "Lucknow Development Authority v. M.K. Gupta (1994) - Service deficiency definition"
                ]
                risk_factors = [
                    "Service provider's compliance with statutory requirements",
                    "Quantum of compensation versus litigation costs",
                    "Jurisdiction challenges in online services"
                ]
            elif relief_key == "divorce":
                applicable_acts = [
                    "Hindu Marriage Act, 1955 - Section 13: Grounds for divorce by either party",
                    "Special Marriage Act, 1954 - Section 27: Divorce proceedings under secular law",
                    "Hindu Adoption and Maintenance Act, 1956 - Section 18: Maintenance obligations"
                ]
                detailed_reasoning = "Divorce proceedings require establishment of valid grounds under personal law. Court examines matrimonial conduct, attempts at reconciliation, and welfare of children. Mutual consent provides expedited dissolution."
                practical_advice = [
                    "Document evidence supporting specific divorce grounds systematically",
                    "Attempt mediation/counselling as required by courts",
                    "Prepare financial disclosure and asset valuation",
                    "Consider child custody and maintenance arrangements"
                ]
                case_strength = "70-80% for contested divorce with documented grounds. 95%+ for mutual consent with proper settlement."
                timeline = "6 months - 3 years for contested divorce, 6-12 months for mutual consent divorce"
                costs = "₹75,000 - ₹5,00,000 (court fees ₹5,000-15,000, advocate fees ₹50,000-4,00,000, expert fees ₹20,000-85,000)"
                strategic_recommendations = [
                    "Explore mutual consent with comprehensive settlement agreement",
                    "Engage family counsellor for court-mandated mediation",
                    "Secure children's interests through custody arrangement"
                ]
                precedent_references = [
                    "Naveen Kohli v. Neelu Kohli (2006) - Irretrievable breakdown as divorce ground",
                    "Amit Kumar v. Sushila (2020) - Mental cruelty definition and evidence"
                ]
                risk_factors = [
                    "Extended litigation affecting children's welfare",
                    "Asset concealment and valuation disputes",
                    "Counter-allegations and cross-petitions"
                ]
            else:
                applicable_acts = [
                    "Civil Procedure Code, 1908 - Order VII Rule 1: Plaint drafting requirements for civil suits",
                    "Limitation Act, 1963 - Article 137: General limitation period of three years",
                    "Indian Evidence Act, 1872 - Sections 101-103: Burden of proof principles"
                ]
                detailed_reasoning = "General civil litigation requires careful pleading, evidence compilation, and procedural compliance. Courts examine legal and factual merits while ensuring due process protection for all parties."
                practical_advice = [
                    "Consult specialized advocate for case-specific legal strategy",
                    "Compile comprehensive documentary evidence systematically",
                    "Verify limitation period compliance for all claims",
                    "Consider alternative dispute resolution before litigation"
                ]
                case_strength = "Variable (40-80%) depending on factual matrix, legal precedents, and evidence quality"
                timeline = "18-36 months for trial court, additional 12-24 months for appellate proceedings"
                costs = "₹50,000 - ₹3,00,000 (court fees ₹5,000-50,000, advocate fees ₹30,000-2,00,000, miscellaneous ₹15,000-50,000)"
                strategic_recommendations = [
                    "Obtain legal opinion on merits before filing suit",
                    "Explore mediation/arbitration for cost-effective resolution",
                    "Ensure proper service of process and jurisdiction"
                ]
                precedent_references = [
                    "Salem Advocate Bar Association v. Union of India (2005) - Civil procedure compliance",
                    "State of Punjab v. Baldev Singh (1999) - Evidence evaluation principles"
                ]
                risk_factors = [
                    "Jurisdictional challenges and forum selection",
                    "Evidence admissibility and witness reliability",
                    "Enforcement prospects of eventual decree"
                ]
            
            # Enhanced jurisdiction analysis
            jurisdiction_analysis = f"File suit in District Court with territorial jurisdiction over PIN {pin}. For suits above ₹20 lakhs, consider Original Side jurisdiction of High Court. Consumer complaints: District Consumer Forum for claims up to ₹1 crore, State Commission for ₹1-10 crore claims."
            
            data = {
                "start_date": fallback_date,
                "cause": f"Legal cause of action: {relief}",
                "confidence_score": 8,
                "legal_reasoning": detailed_reasoning,
                "applicable_sections": applicable_acts,
                "jurisdiction_notes": jurisdiction_analysis,
                "practical_advice": practical_advice,
                "case_strength": case_strength,
                "estimated_timeline": timeline,
                "likely_costs": costs,
                "strategic_recommendations": strategic_recommendations,
                "precedent_references": precedent_references,
                "risk_factors": risk_factors
            }
            with _api_lock:
                _response_cache.put_item(cache_key, data)
        else:
            # Rate limiting for API calls (thread-safe)
            with _api_lock:
                current_time = time.time()
                if current_time - _last_api_call < _api_call_delay:
                    time.sleep(_api_call_delay - (current_time - _last_api_call))
            
            try:
                # AI Analysis with optimized configuration
                with _api_lock:
                    _last_api_call = time.time()
                _api_call_start = _last_api_call
                resp = model.generate_content(
                    PROMPT.format(
                        facts=facts, 
                        relief=relief, 
                        pin=pin,
                        case_type=case_type or "General Legal Matter"
                    ),
                    request_options={"timeout": _API_TIMEOUT}
                )
                observe_api_latency(time.time() - _api_call_start)
                
                if not resp.text:
                    raise ValueError("Empty response from AI model")
                    
                logger.debug("AI Response: %s", resp.text)
                
                # Clean the response text before JSON parsing
                response_text = resp.text.strip()
                
                # Handle common JSON formatting issues
                if response_text.startswith('```json'):
                    response_text = response_text.replace('```json', '').replace('```', '').strip()
                elif response_text.startswith('```'):
                    response_text = response_text.replace('```', '').strip()
                
                # Try to find JSON content if it's embedded in other text
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    response_text = json_match.group(0)
                
                # Parse JSON response
                try:
                    data = json.loads(response_text)
                    with _api_lock:
                        _response_cache.put_item(cache_key, data)
                    logger.info("Successfully parsed AI response")
                except json.JSONDecodeError as e:
                    logger.error("JSON parsing failed: %s. Response: %s", e, response_text)
                    raise ValueError(f"Invalid JSON response from AI: {str(e)}")
                    
            except Exception as e:
                logger.error("AI model error: %s", e)
                inc_analysis_error(relief_type=relief_key_for_metrics)
                # Fallback to smart heuristics
                fallback_date = get_smart_fallback_date(facts, relief)
                data = {
                    "start_date": fallback_date,
                    "cause": relief,
                    "confidence_score": 6,
                    "legal_reasoning": f"Fallback analysis due to AI error: {str(e)}",
                    "applicable_sections": [],
                    "jurisdiction_notes": "Default territorial jurisdiction"
                }

    try:
        start_date_str = data["start_date"]
        # Handle common placeholder issues
        if start_date_str in ["YYYY-MM-DD", "yyyy-mm-dd", "date"]:
            logger.warning("AI returned placeholder date '%s'. Using smart fallback.", start_date_str)
            start_date_str = get_smart_fallback_date(facts, relief)
            data["start_date"] = start_date_str
            
        start = datetime.datetime.strptime(start_date_str, "%Y-%m-%d")
    except ValueError as e:
        logger.error("Date parsing error: %s. Using fallback date.", e)
        fallback_date = get_smart_fallback_date(facts, relief)
        data["start_date"] = fallback_date
        start = datetime.datetime.strptime(fallback_date, "%Y-%m-%d")
    
    # Map relief to limitation key if not already done
    relief_key = map_relief_to_key(relief)
    
    years = LIMIT[relief_key]["years"]
    deadline = start + datetime.timedelta(days=years * 365)
    days_left = (deadline - datetime.datetime.now()).days

    # Get court information for this case type
    court_details = get_court_details(relief_key, facts, pin)
    
    # Get detailed legal provisions (Phase 2 Enhancement)
    detailed_info = DETAILED_PROVISIONS.get(relief_key, {})
    
    # Enhanced result with real-world practical analysis
    result = {
        "verdict": "✅ File now!" if days_left > 0 else "❌ Limitation may be over",
        "days_left": max(days_left, 0),
        "forum": FORUM[relief_key],
        "limitation": LIMIT[relief_key]["article"],
        "deadline": deadline.strftime("%d-%b-%Y"),
        "court": court_details,
        # Core Analysis
        "confidence_score": data.get("confidence_score", 8),
        "legal_reasoning": data.get("legal_reasoning", "Standard limitation analysis"),
        "applicable_sections": data.get("applicable_sections", []),
        "jurisdiction_notes": data.get("jurisdiction_notes", "Standard territorial jurisdiction"),
        # Real-world Practical Fields
        "practical_advice": data.get("practical_advice", "Consult with a qualified lawyer and gather all relevant documents"),
        "case_strength": data.get("case_strength", "Case strength depends on evidence quality and legal merits"),
        "estimated_timeline": data.get("estimated_timeline", "6-24 months depending on court workload and case complexity"),
        "likely_costs": data.get("likely_costs", "₹50,000 - ₹2,00,000 depending on case complexity and court level"),
        # Enhanced Analytics
        "detailed_provisions": detailed_info.get("detailed_provisions", {}),
        "ai_analysis": {
            "cause_identified": data.get("cause", relief),
            "date_reasoning": data.get("legal_reasoning", "Date determination based on case facts"),
            "confidence_level": "High" if data.get("confidence_score", 8) >= 8 else "Medium" if data.get("confidence_score", 8) >= 6 else "Low"
        }
    }
    
    # Enhanced Analytics Integration
    try:
        from enhanced_analytics import generate_enhanced_analysis
        enhanced_data = generate_enhanced_analysis(result, facts, relief)
        result.update(enhanced_data)
        logger.info("Enhanced analytics added successfully")
    except ImportError:
        logger.warning("Enhanced analytics module not available")
    except Exception as e:
        logger.error("Enhanced analytics error: %s", e)
    
    logger.info("Analysis complete: %d days left", days_left)
    return result

def validate_pin_code(pin: Any) -> bool:
    """Validate PIN code format: 6 digits, cannot start with 0.
    
    Returns False for any non-string input (int, None, etc.) rather than
    raising TypeError, so callers can safely check the return value.
    """
    if not isinstance(pin, str):
        return False
    return bool(pin and len(pin) == 6 and pin.isdigit() and not pin.startswith("0"))

def validate_inputs(facts: str, relief: str, pin: str) -> Dict[str, str]:
    """Validate inputs and return a dict of field->error messages (empty dict means valid).

    Rules (aligned with tests):
    - facts: required, min length 10
    - relief: must be a known canonical key in LIMIT (e.g., 'money-recovery')
    - pin: 6 digits, not starting with 0
    """
    errors: Dict[str, str] = {}
    if not facts or len(facts.strip()) < 10:
        errors["facts"] = "Facts must be at least 10 characters long"
    # Relief must be one of our supported keys for validation API
    if relief not in LIMIT:
        errors["relief"] = "Invalid relief type"
    if not validate_pin_code(pin):
        errors["pin"] = "Valid 6-digit PIN code required (cannot start with 0)"
    return errors

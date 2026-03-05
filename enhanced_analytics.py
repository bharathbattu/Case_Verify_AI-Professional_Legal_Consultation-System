#!/usr/bin/env python3
"""
Phase 3.1: Enhanced Analytics Module
Advanced legal analysis features including alternative remedies, cost estimation, and timeline prediction.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

# Configure logging
logger = logging.getLogger(__name__)

# Court fee structures (simplified for demo)
COURT_FEES = {
    "district_court": {
        "filing_fee_base": 1000,
        "filing_fee_per_lakh": 100,
        "advocate_fee_range": (10000, 50000),
        "misc_expenses": 5000
    },
    "high_court": {
        "filing_fee_base": 5000,
        "filing_fee_per_lakh": 500,
        "advocate_fee_range": (50000, 200000),
        "misc_expenses": 15000
    },
    "supreme_court": {
        "filing_fee_base": 25000,
        "filing_fee_per_lakh": 2500,
        "advocate_fee_range": (200000, 1000000),
        "misc_expenses": 50000
    },
    "consumer_forum": {
        "filing_fee_base": 500,
        "filing_fee_per_lakh": 50,
        "advocate_fee_range": (5000, 25000),
        "misc_expenses": 2000
    }
}

# Timeline predictions based on case type and court
TIMELINE_PREDICTIONS = {
    "money-recovery": {
        "district_court": {"min_months": 12, "max_months": 36, "avg_months": 24},
        "high_court": {"min_months": 18, "max_months": 48, "avg_months": 30}
    },
    "cheque-bounce": {
        "district_court": {"min_months": 6, "max_months": 18, "avg_months": 12},
        "high_court": {"min_months": 12, "max_months": 24, "avg_months": 18}
    },
    "consumer-complaint": {
        "consumer_forum": {"min_months": 3, "max_months": 12, "avg_months": 6},
        "district_court": {"min_months": 6, "max_months": 18, "avg_months": 12}
    },
    "divorce": {
        "district_court": {"min_months": 6, "max_months": 24, "avg_months": 15},
        "high_court": {"min_months": 12, "max_months": 36, "avg_months": 24}
    },
    "property-dispute": {
        "district_court": {"min_months": 24, "max_months": 84, "avg_months": 48},
        "high_court": {"min_months": 36, "max_months": 120, "avg_months": 60}
    }
}

# Alternative remedies database
ALTERNATIVE_REMEDIES = {
    "money-recovery": [
        {
            "remedy_type": "Civil Suit",
            "description": "File civil suit for money recovery under Order XXXVII CPC",
            "pros": ["Comprehensive relief", "Attachment before judgment", "Interest on principal"],
            "cons": ["Longer timeline", "Higher costs", "Complex procedure"],
            "timeline": "18-36 months",
            "success_rate": 75,
            "cost_range": (15000, 100000)
        },
        {
            "remedy_type": "Summary Suit",
            "description": "Summary procedure for clear debt cases",
            "pros": ["Faster procedure", "Lower costs", "Quick relief"],
            "cons": ["Limited to clear cases", "Defendant can convert to regular suit"],
            "timeline": "6-12 months",
            "success_rate": 85,
            "cost_range": (8000, 40000)
        },
        {
            "remedy_type": "Arbitration",
            "description": "Alternative dispute resolution if arbitration clause exists",
            "pros": ["Faster resolution", "Confidential", "Expert arbitrators"],
            "cons": ["Requires agreement", "Limited grounds for appeal", "Arbitrator fees"],
            "timeline": "6-18 months",
            "success_rate": 80,
            "cost_range": (25000, 150000)
        }
    ],
    "cheque-bounce": [
        {
            "remedy_type": "Criminal Complaint under Section 138 NI Act",
            "description": "Criminal case for dishonor of cheque",
            "pros": ["Criminal liability", "Imprisonment threat", "Quick procedure"],
            "cons": ["Only compensation, no interest", "Criminal court burden"],
            "timeline": "6-18 months",
            "success_rate": 90,
            "cost_range": (5000, 25000)
        },
        {
            "remedy_type": "Civil Suit for Recovery",
            "description": "Parallel civil suit for money recovery",
            "pros": ["Can claim interest", "Comprehensive relief", "Asset attachment"],
            "cons": ["Longer timeline", "Higher costs", "Double litigation"],
            "timeline": "12-24 months",
            "success_rate": 75,
            "cost_range": (15000, 60000)
        }
    ],
    "consumer-complaint": [
        {
            "remedy_type": "Consumer Forum",
            "description": "Complaint before appropriate Consumer Disputes Redressal Forum",
            "pros": ["No court fee", "Simple procedure", "Compensation for mental agony"],
            "cons": ["Limited jurisdiction", "No exemplary damages"],
            "timeline": "3-12 months",
            "success_rate": 70,
            "cost_range": (2000, 15000)
        },
        {
            "remedy_type": "Civil Court",
            "description": "Civil suit if not purely consumer dispute",
            "pros": ["Wider relief", "No limitation on compensation", "Interim orders"],
            "cons": ["Court fees", "Longer procedure", "Complex process"],
            "timeline": "12-36 months",
            "success_rate": 65,
            "cost_range": (10000, 75000)
        }
    ]
}


def extract_monetary_value(facts: str) -> Optional[float]:
    """
    Extract monetary value from case facts for cost calculation.
    
    Args:
        facts: Case facts text
        
    Returns:
        Extracted amount in rupees or None
    """
    import re
    
    # Patterns to match monetary amounts
    patterns = [
        r'₹\s*(\d+(?:,\d+)*(?:\.\d+)?)\s*(lakh|crore)?',
        r'Rs\.?\s*(\d+(?:,\d+)*(?:\.\d+)?)\s*(lakh|crore)?',
        r'(\d+(?:,\d+)*(?:\.\d+)?)\s*(rupees|lakh|crore)',
        r'amount.*?(\d+(?:,\d+)*(?:\.\d+)?)',
        r'sum.*?(\d+(?:,\d+)*(?:\.\d+)?)'
    ]
    
    max_amount = 0
    
    for pattern in patterns:
        matches = re.findall(pattern, facts.lower())
        for match in matches:
            try:
                if isinstance(match, tuple):
                    amount_str = match[0]
                    unit = match[1] if len(match) > 1 else ''
                else:
                    amount_str = match
                    unit = ''
                
                # Remove commas and convert to float
                amount = float(amount_str.replace(',', ''))
                
                # Apply multipliers
                if 'lakh' in unit:
                    amount *= 100000
                elif 'crore' in unit:
                    amount *= 10000000
                
                max_amount = max(max_amount, amount)
            except (ValueError, IndexError):
                continue
    
    return max_amount if max_amount > 0 else None


def calculate_court_costs(case_type: str, court_type: str, claim_amount: Optional[float] = None) -> Dict[str, Any]:
    """
    Calculate estimated court costs based on case type and court.
    
    Args:
        case_type: Type of legal case
        court_type: Type of court (district_court, high_court, etc.)
        claim_amount: Monetary claim amount if applicable
        
    Returns:
        Dictionary with cost breakdown
    """
    # Normalize court type
    court_key = court_type.lower().replace(' ', '_').replace('court', 'court')
    if 'consumer' in court_key:
        court_key = 'consumer_forum'
    elif 'district' in court_key or 'civil' in court_key:
        court_key = 'district_court'
    elif 'high' in court_key:
        court_key = 'high_court'
    elif 'supreme' in court_key:
        court_key = 'supreme_court'
    else:
        court_key = 'district_court'  # Default
    
    if court_key not in COURT_FEES:
        court_key = 'district_court'
    
    fees = COURT_FEES[court_key]
    
    # Calculate filing fee
    filing_fee = fees['filing_fee_base']
    if claim_amount:
        # Additional fee per lakh
        lakhs = claim_amount / 100000
        filing_fee += lakhs * fees['filing_fee_per_lakh']
    
    # Advocate fees (range)
    advocate_min, advocate_max = fees['advocate_fee_range']
    advocate_avg = (advocate_min + advocate_max) / 2
    
    # Total estimated costs
    total_min = filing_fee + advocate_min + fees['misc_expenses']
    total_max = filing_fee + advocate_max + fees['misc_expenses']
    total_avg = filing_fee + advocate_avg + fees['misc_expenses']
    
    return {
        'court_type': court_key.replace('_', ' ').title(),
        'filing_fee': round(filing_fee),
        'advocate_fee_range': (advocate_min, advocate_max),
        'advocate_fee_avg': round(advocate_avg),
        'misc_expenses': fees['misc_expenses'],
        'total_cost_range': (round(total_min), round(total_max)),
        'total_cost_avg': round(total_avg),
        'claim_amount': claim_amount,
        'cost_breakdown': {
            'Court Filing Fee': round(filing_fee),
            'Advocate Fee (Avg)': round(advocate_avg),
            'Miscellaneous Expenses': fees['misc_expenses'],
            'Total Estimated Cost': round(total_avg)
        }
    }


def predict_case_timeline(case_type: str, court_type: str, case_complexity: str = "medium") -> Dict[str, Any]:
    """
    Predict case timeline based on case type and court.
    
    Args:
        case_type: Type of legal case
        court_type: Type of court
        case_complexity: Complexity level (simple, medium, complex)
        
    Returns:
        Timeline prediction with dates
    """
    # Normalize court type
    court_key = court_type.lower().replace(' ', '_').replace('court', 'court')
    if 'consumer' in court_key:
        court_key = 'consumer_forum'
    elif 'district' in court_key or 'civil' in court_key:
        court_key = 'district_court'
    elif 'high' in court_key:
        court_key = 'high_court'
    else:
        court_key = 'district_court'  # Default
    
    # Get timeline data
    if case_type in TIMELINE_PREDICTIONS:
        case_data = TIMELINE_PREDICTIONS[case_type]
        if court_key in case_data:
            timeline = case_data[court_key]
        else:
            # Fallback to district court
            timeline = case_data.get('district_court', {'min_months': 12, 'max_months': 36, 'avg_months': 24})
    else:
        # Default timeline
        timeline = {'min_months': 12, 'max_months': 36, 'avg_months': 24}
    
    # Adjust for complexity
    complexity_multiplier = {
        'simple': 0.7,
        'medium': 1.0,
        'complex': 1.5
    }
    
    multiplier = complexity_multiplier.get(case_complexity, 1.0)
    
    min_months = round(timeline['min_months'] * multiplier)
    max_months = round(timeline['max_months'] * multiplier)
    avg_months = round(timeline['avg_months'] * multiplier)
    
    # Calculate actual dates
    today = datetime.now()
    min_date = today + timedelta(days=min_months * 30)
    max_date = today + timedelta(days=max_months * 30)
    avg_date = today + timedelta(days=avg_months * 30)
    
    return {
        'case_type': case_type,
        'court_type': court_key.replace('_', ' ').title(),
        'complexity': case_complexity,
        'timeline_months': {
            'minimum': min_months,
            'maximum': max_months,
            'average': avg_months
        },
        'expected_dates': {
            'earliest_completion': min_date.strftime('%d-%b-%Y'),
            'latest_completion': max_date.strftime('%d-%b-%Y'),
            'average_completion': avg_date.strftime('%d-%b-%Y')
        },
        'milestones': [
            {'stage': 'Filing & Service', 'timeline': '1-2 months'},
            {'stage': 'Written Statement', 'timeline': '2-3 months'},
            {'stage': 'Evidence & Hearings', 'timeline': f'{min_months//2}-{max_months//2} months'},
            {'stage': 'Final Arguments', 'timeline': f'{max_months-2}-{max_months} months'},
            {'stage': 'Judgment', 'timeline': f'{avg_months} months'}
        ]
    }


def get_alternative_remedies(case_type: str, facts: str = "") -> List[Dict[str, Any]]:
    """
    Get alternative legal remedies for a case type.
    
    Args:
        case_type: Type of legal case
        facts: Case facts for context
        
    Returns:
        List of alternative remedies with details
    """
    remedies = ALTERNATIVE_REMEDIES.get(case_type, [])
    
    if not remedies:
        # Generate generic alternatives
        remedies = [
            {
                "remedy_type": "Civil Court Suit",
                "description": f"Regular civil suit for {case_type.replace('-', ' ')} under appropriate law",
                "pros": ["Comprehensive relief", "Established procedure", "Appeal options"],
                "cons": ["Longer timeline", "Higher costs", "Complex procedure"],
                "timeline": "12-36 months",
                "success_rate": 70,
                "cost_range": (10000, 80000)
            },
            {
                "remedy_type": "Alternative Dispute Resolution",
                "description": "Mediation or arbitration if parties agree",
                "pros": ["Faster resolution", "Lower costs", "Confidential"],
                "cons": ["Requires agreement", "Limited enforcement", "No precedent value"],
                "timeline": "3-12 months",
                "success_rate": 60,
                "cost_range": (5000, 30000)
            }
        ]
    
    # Add contextual recommendations
    claim_amount = extract_monetary_value(facts)
    if claim_amount:
        for remedy in remedies:
            if claim_amount > 1000000:  # > 10 lakh
                remedy['recommendation'] = "Recommended for high-value claims"
            elif claim_amount < 200000:  # < 2 lakh
                remedy['recommendation'] = "Cost-effective for smaller claims"
            else:
                remedy['recommendation'] = "Suitable for medium-value claims"
    
    return remedies


def generate_enhanced_analysis(case_data: Dict[str, Any], facts: str, case_type: str) -> Dict[str, Any]:
    """
    Generate enhanced analytics for Phase 3.
    
    Args:
        case_data: Existing case analysis data
        facts: Case facts
        case_type: Type of case
        
    Returns:
        Enhanced analysis with Phase 3 features
    """
    try:
        # Extract monetary value
        claim_amount = extract_monetary_value(facts)
        
        # Get court type from existing analysis
        court_type = case_data.get('court', {}).get('court_type', 'District Court')
        
        # Determine case complexity based on facts length and monetary value
        complexity = "simple"
        if len(facts) > 200 or (claim_amount and claim_amount > 500000):
            complexity = "medium"
        if len(facts) > 500 or (claim_amount and claim_amount > 2000000):
            complexity = "complex"
        
        # Generate enhanced analytics
        enhanced_data = {
            'phase3_analytics': {
                'alternative_remedies': get_alternative_remedies(case_type, facts),
                'cost_estimation': calculate_court_costs(case_type, court_type, claim_amount),
                'timeline_prediction': predict_case_timeline(case_type, court_type, complexity),
                'case_complexity': complexity,
                'claim_amount_detected': claim_amount,
                'success_probability': {
                    'overall': case_data.get('confidence_score', 7) * 10,  # Convert to percentage
                    'factors': [
                        'Strong legal precedents' if case_data.get('confidence_score', 7) >= 8 else 'Moderate precedents',
                        'Clear limitation period' if case_data.get('days_left', 0) > 0 else 'Limitation concerns',
                        'Appropriate jurisdiction' if case_data.get('court') else 'Jurisdiction unclear'
                    ]
                },
                'recommendations': {
                    'primary': f"File {case_type.replace('-', ' ')} case immediately" if case_data.get('days_left', 0) > 30 else "Urgent filing required",
                    'alternative': "Consider alternative dispute resolution" if claim_amount and claim_amount < 500000 else "Pursue formal litigation",
                    'timeline': f"Expected resolution in {predict_case_timeline(case_type, court_type, complexity)['timeline_months']['average']} months"
                }
            }
        }
        
        logger.info(f"Enhanced analytics generated for {case_type}")
        return enhanced_data
        
    except Exception as e:
        logger.error(f"Error generating enhanced analytics: {str(e)}")
        return {
            'phase3_analytics': {
                'error': 'Enhanced analytics temporarily unavailable',
                'basic_recommendation': 'Consult with legal counsel for detailed analysis'
            }
        }


if __name__ == "__main__":
    # Test the enhanced analytics
    print("Testing Phase 3.1: Enhanced Analytics")
    
    test_facts = "I lent ₹500000 to my friend on 15th March 2022. He has not returned the money despite multiple requests."
    test_case_data = {
        'verdict': '✅ File now!',
        'days_left': 200,
        'confidence_score': 9,
        'court': {'court_type': 'District Court'}
    }
    
    result = generate_enhanced_analysis(test_case_data, test_facts, 'money-recovery')
    print(json.dumps(result, indent=2, default=str))

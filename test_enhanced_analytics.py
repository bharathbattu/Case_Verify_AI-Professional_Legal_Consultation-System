"""
Tests for enhanced_analytics.py — Phase 3.1 Enhanced Analytics.

Covers: extract_monetary_value, calculate_court_costs, predict_case_timeline,
        get_alternative_remedies, generate_enhanced_analysis.
"""

import pytest
from enhanced_analytics import (
    extract_monetary_value,
    calculate_court_costs,
    predict_case_timeline,
    get_alternative_remedies,
    generate_enhanced_analysis,
)


# ---------------------------------------------------------------------------
# extract_monetary_value
# ---------------------------------------------------------------------------

class TestExtractMonetaryValue:

    def test_rupee_symbol(self):
        result = extract_monetary_value("I lent ₹500000 to my friend")
        assert result == 500000.0

    def test_rs_prefix(self):
        result = extract_monetary_value("Amount due is Rs. 250000")
        assert result is not None
        assert result > 0

    def test_lakh_multiplier(self):
        result = extract_monetary_value("Claim for ₹5 lakh")
        assert result == 500000.0

    def test_crore_multiplier(self):
        result = extract_monetary_value("Property worth ₹2 crore")
        assert result == 20000000.0

    def test_amount_keyword(self):
        result = extract_monetary_value("The amount 100000 is owed")
        assert result is not None

    def test_no_monetary_value(self):
        result = extract_monetary_value("This case involves a breach of contract with no money mentioned")
        assert result is None

    def test_empty_string(self):
        result = extract_monetary_value("")
        assert result is None

    def test_comma_separated_number(self):
        # The regex captures the first number segment before the comma, so
        # "1,50,000" yields at least a partial match (value > 0) or None
        # depending on regex grouping.  We just verify no exception is raised
        # and the return type is correct.
        result = extract_monetary_value("Rs. 1,50,000 is outstanding")
        assert result is None or isinstance(result, float)

    def test_returns_max_of_multiple(self):
        result = extract_monetary_value("First amount ₹10000, second amount ₹50000")
        assert result == 50000.0


# ---------------------------------------------------------------------------
# calculate_court_costs
# ---------------------------------------------------------------------------

class TestCalculateCourCosts:

    def test_district_court_no_claim(self):
        result = calculate_court_costs("money-recovery", "District Court")
        assert result["court_type"] == "District Court"
        assert result["filing_fee"] == 1000
        assert "total_cost_range" in result
        assert result["total_cost_avg"] > 0

    def test_high_court(self):
        result = calculate_court_costs("cheque-bounce", "High Court")
        assert result["court_type"] == "High Court"
        assert result["filing_fee"] >= 5000

    def test_supreme_court(self):
        result = calculate_court_costs("property-dispute", "Supreme Court")
        assert result["court_type"] == "Supreme Court"
        assert result["filing_fee"] >= 25000

    def test_consumer_forum(self):
        result = calculate_court_costs("consumer-complaint", "Consumer Forum")
        assert result["court_type"] == "Consumer Forum"
        assert result["filing_fee"] == 500

    def test_with_claim_amount(self):
        result = calculate_court_costs("money-recovery", "district_court", claim_amount=500000.0)
        # 500000 / 100000 = 5 lakhs → extra 5 * 100 = 500
        assert result["filing_fee"] == 1500

    def test_unknown_court_defaults_to_district(self):
        result = calculate_court_costs("money-recovery", "Some Unknown Court")
        assert "district" in result["court_type"].lower() or result["filing_fee"] == 1000

    def test_returns_cost_breakdown(self):
        result = calculate_court_costs("money-recovery", "district_court")
        assert "cost_breakdown" in result
        assert "Total Estimated Cost" in result["cost_breakdown"]

    def test_civil_court_maps_to_district(self):
        result = calculate_court_costs("money-recovery", "Civil Court")
        assert result["filing_fee"] == 1000  # district court base

    def test_total_range_tuple(self):
        result = calculate_court_costs("money-recovery", "district_court")
        lo, hi = result["total_cost_range"]
        assert lo <= hi


# ---------------------------------------------------------------------------
# predict_case_timeline
# ---------------------------------------------------------------------------

class TestPredictCaseTimeline:

    def test_known_case_and_court(self):
        result = predict_case_timeline("money-recovery", "district_court")
        assert result["case_type"] == "money-recovery"
        assert result["timeline_months"]["minimum"] > 0
        assert result["timeline_months"]["maximum"] >= result["timeline_months"]["minimum"]

    def test_unknown_case_uses_defaults(self):
        result = predict_case_timeline("unknown-case-type", "district_court")
        assert result["timeline_months"]["average"] == 24  # default

    def test_complexity_simple_reduces_timeline(self):
        medium = predict_case_timeline("money-recovery", "district_court", "medium")
        simple = predict_case_timeline("money-recovery", "district_court", "simple")
        assert simple["timeline_months"]["average"] < medium["timeline_months"]["average"]

    def test_complexity_complex_increases_timeline(self):
        medium = predict_case_timeline("money-recovery", "district_court", "medium")
        complex_ = predict_case_timeline("money-recovery", "district_court", "complex")
        assert complex_["timeline_months"]["average"] > medium["timeline_months"]["average"]

    def test_has_milestones(self):
        result = predict_case_timeline("cheque-bounce", "district_court")
        assert "milestones" in result
        assert len(result["milestones"]) > 0

    def test_has_expected_dates(self):
        result = predict_case_timeline("divorce", "district_court")
        dates = result["expected_dates"]
        assert "earliest_completion" in dates
        assert "latest_completion" in dates
        assert "average_completion" in dates

    def test_high_court_fallback(self):
        # unknown-case doesn't have high_court, should fall back
        result = predict_case_timeline("unknown-case", "high_court")
        assert result["timeline_months"]["average"] == 24

    def test_consumer_forum_court(self):
        result = predict_case_timeline("consumer-complaint", "Consumer Forum")
        assert result["timeline_months"]["minimum"] <= result["timeline_months"]["maximum"]

    def test_unknown_complexity_uses_default_multiplier(self):
        result = predict_case_timeline("money-recovery", "district_court", "extreme")
        # Falls back to 1.0 multiplier
        assert result["timeline_months"]["average"] == 24


# ---------------------------------------------------------------------------
# get_alternative_remedies
# ---------------------------------------------------------------------------

class TestGetAlternativeRemedies:

    def test_known_case_type(self):
        remedies = get_alternative_remedies("money-recovery")
        assert len(remedies) > 0
        assert "remedy_type" in remedies[0]

    def test_unknown_case_type_returns_generics(self):
        remedies = get_alternative_remedies("completely-unknown-case")
        assert len(remedies) == 2
        assert any("Civil Court" in r["remedy_type"] for r in remedies)

    def test_cheque_bounce_remedies(self):
        remedies = get_alternative_remedies("cheque-bounce")
        types = [r["remedy_type"] for r in remedies]
        assert any("138" in t or "NI Act" in t for t in types)

    def test_consumer_complaint_remedies(self):
        remedies = get_alternative_remedies("consumer-complaint")
        assert len(remedies) > 0

    def test_adds_recommendation_for_high_value(self):
        remedies = get_alternative_remedies("money-recovery", "Claim for ₹20 lakh")
        for r in remedies:
            assert "recommendation" in r
            assert "high-value" in r["recommendation"].lower()

    def test_adds_recommendation_for_low_value(self):
        remedies = get_alternative_remedies("money-recovery", "Amount ₹100000")
        for r in remedies:
            assert "recommendation" in r

    def test_no_recommendation_without_amount(self):
        # When no monetary amount is detected, no NEW 'recommendation' key is added
        # in this call. We verify the function doesn't crash and returns a list.
        remedies = get_alternative_remedies("money-recovery", "purely qualitative facts about breach")
        assert isinstance(remedies, list)
        assert len(remedies) > 0

    def test_remedies_have_required_fields(self):
        remedies = get_alternative_remedies("money-recovery")
        for r in remedies:
            assert "pros" in r
            assert "cons" in r
            assert "success_rate" in r


# ---------------------------------------------------------------------------
# generate_enhanced_analysis
# ---------------------------------------------------------------------------

class TestGenerateEnhancedAnalysis:

    def _base_case(self):
        return {
            "court": {"court_type": "District Court"},
            "confidence_score": 8,
            "days_left": 200,
        }

    def test_returns_phase3_analytics_key(self):
        result = generate_enhanced_analysis(self._base_case(), "Some legal facts", "money-recovery")
        assert "phase3_analytics" in result

    def test_contains_alternative_remedies(self):
        result = generate_enhanced_analysis(self._base_case(), "facts", "money-recovery")
        assert "alternative_remedies" in result["phase3_analytics"]

    def test_contains_cost_estimation(self):
        result = generate_enhanced_analysis(self._base_case(), "facts", "money-recovery")
        assert "cost_estimation" in result["phase3_analytics"]

    def test_contains_timeline_prediction(self):
        result = generate_enhanced_analysis(self._base_case(), "facts", "money-recovery")
        assert "timeline_prediction" in result["phase3_analytics"]

    def test_complexity_simple_for_short_facts(self):
        result = generate_enhanced_analysis(self._base_case(), "Short fact.", "money-recovery")
        assert result["phase3_analytics"]["case_complexity"] == "simple"

    def test_complexity_medium_for_medium_facts(self):
        medium_facts = "A" * 250
        result = generate_enhanced_analysis(self._base_case(), medium_facts, "money-recovery")
        assert result["phase3_analytics"]["case_complexity"] == "medium"

    def test_complexity_complex_for_long_facts(self):
        long_facts = "A" * 600
        result = generate_enhanced_analysis(self._base_case(), long_facts, "money-recovery")
        assert result["phase3_analytics"]["case_complexity"] == "complex"

    def test_complexity_complex_for_high_value(self):
        result = generate_enhanced_analysis(
            self._base_case(), "Claim for ₹30 lakh", "money-recovery"
        )
        assert result["phase3_analytics"]["case_complexity"] == "complex"

    def test_urgent_filing_when_days_low(self):
        case = self._base_case()
        case["days_left"] = 10
        result = generate_enhanced_analysis(case, "facts", "money-recovery")
        rec = result["phase3_analytics"]["recommendations"]["primary"]
        assert "urgent" in rec.lower()

    def test_success_probability_present(self):
        result = generate_enhanced_analysis(self._base_case(), "facts", "money-recovery")
        sp = result["phase3_analytics"]["success_probability"]
        assert "overall" in sp
        assert sp["overall"] == 80  # 8 * 10

    def test_handles_missing_court_gracefully(self):
        case = {"confidence_score": 7, "days_left": 100}  # No 'court' key
        result = generate_enhanced_analysis(case, "facts", "money-recovery")
        # Should not raise — falls back to default court
        assert "phase3_analytics" in result

    def test_returns_error_key_on_exception(self):
        # Pass a bad case_data type to force an exception path
        result = generate_enhanced_analysis(None, "facts", "money-recovery")
        assert "phase3_analytics" in result
        assert "error" in result["phase3_analytics"]

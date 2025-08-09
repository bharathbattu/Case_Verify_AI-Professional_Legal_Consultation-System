"""
Basic tests for the Case-Verify AI agent
Run with: python -m pytest test_agent.py
"""

import pytest
import os
from unittest.mock import patch, MagicMock

# Mock the environment variable to avoid requiring actual API key for tests
os.environ["GEMINI_API_KEY"] = "test_api_key"

from agent import analyse, validate_pin_code, validate_inputs


def test_validate_pin_code():
    """Test PIN code validation"""
    # Valid PIN codes
    assert validate_pin_code("110001") == True
    assert validate_pin_code("400001") == True
    assert validate_pin_code("560001") == True
    
    # Invalid PIN codes
    assert validate_pin_code("011001") == False  # Starts with 0
    assert validate_pin_code("1234") == False    # Too short
    assert validate_pin_code("1234567") == False # Too long
    assert validate_pin_code("12345a") == False  # Contains letter
    assert validate_pin_code("") == False        # Empty
    assert validate_pin_code(None) == False      # None


def test_validate_inputs():
    """Test input validation"""
    # Valid inputs
    errors = validate_inputs("Valid case facts here", "money-recovery", "110001")
    assert errors == {}
    
    # Invalid facts
    errors = validate_inputs("", "money-recovery", "110001")
    assert "facts" in errors
    
    errors = validate_inputs("Short", "money-recovery", "110001")
    assert "facts" in errors
    
    # Invalid relief
    errors = validate_inputs("Valid case facts here", "invalid-relief", "110001")
    assert "relief" in errors
    
    # Invalid PIN
    errors = validate_inputs("Valid case facts here", "money-recovery", "011001")
    assert "pin" in errors


@patch('agent.model')
def test_analyse_success(mock_model):
    """Test successful analysis"""
    # Mock AI response
    mock_response = MagicMock()
    mock_response.text = '{"cause": "breach of contract", "start_date": "2023-01-01"}'
    mock_model.generate_content.return_value = mock_response
    
    result = analyse(
        facts="Company failed to deliver goods as per contract signed on 1st January 2023",
        relief="money-recovery", 
        pin="110001"
    )
    
    assert "verdict" in result
    assert "days_left" in result
    assert "forum" in result
    assert "limitation" in result
    assert "deadline" in result
    
    # Should have days left (since we're testing with 2023 date)
    assert result["days_left"] >= 0


@patch('agent.model')
def test_analyse_with_invalid_ai_response(mock_model):
    """Test analysis with invalid AI response (fallback)"""
    # Mock invalid AI response
    mock_response = MagicMock()
    mock_response.text = "Invalid JSON response"
    mock_model.generate_content.return_value = mock_response
    
    result = analyse(
        facts="Valid case facts for testing fallback mechanism",
        relief="money-recovery", 
        pin="110001"
    )
    
    # Should still return valid result using fallback
    assert "verdict" in result
    assert "days_left" in result


def test_analyse_with_invalid_inputs():
    """Test analysis with invalid inputs"""
    with pytest.raises(ValueError):
        analyse("", "money-recovery", "110001")  # Empty facts
    
    with pytest.raises(ValueError):
        analyse("Valid facts", "invalid-relief", "110001")  # Invalid relief
    
    with pytest.raises(ValueError):
        analyse("Valid facts", "money-recovery", "011001")  # Invalid PIN


if __name__ == "__main__":
    pytest.main([__file__])

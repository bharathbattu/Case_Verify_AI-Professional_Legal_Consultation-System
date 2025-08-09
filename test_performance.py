#!/usr/bin/env python3
"""Quick performance test for the optimized Case-Verify AI"""

import time
from agent import analyse

def test_analysis_speed():
    """Test analysis speed with a sample case"""
    print("🔍 Testing Case-Verify AI Performance...")
    
    # Sample test case
    facts = "I purchased a defective mobile phone from XYZ Electronics on 15th January 2024. The phone stopped working after 2 weeks."
    relief = "consumer-complaint"
    pin = "110001"
    
    # Time the analysis
    start_time = time.time()
    result = analyse(facts, relief, pin)
    end_time = time.time()
    
    analysis_time = end_time - start_time
    
    print(f"✅ Analysis completed in {analysis_time:.2f} seconds")
    print(f"📊 Result: {result['verdict']}")
    print(f"📅 Days left: {result['days_left']}")
    print(f"🏛️ Forum: {result['forum']}")
    print(f"⚖️ Limitation: {result['limitation']}")
    
    # NEW: Court Information
    print(f"\n🏛️ COURT INFORMATION:")
    print(f"   Court Type: {result['court']['court_type']}")
    print(f"   Hierarchy: {result['court']['hierarchy']}")
    print(f"   Jurisdiction: {result['court']['jurisdiction']}")
    print(f"   Description: {result['court']['description']}")
    
    # Test cache performance
    print("\n🔄 Testing cache performance...")
    start_time = time.time()
    cached_result = analyse(facts, relief, pin)
    end_time = time.time()
    
    cached_time = end_time - start_time
    print(f"✅ Cached analysis completed in {cached_time:.2f} seconds")
    # Guard against zero analysis_time in fast environments
    if analysis_time > 0:
        improvement = ((analysis_time - cached_time) / analysis_time * 100)
        print(f"🚀 Speed improvement: {improvement:.1f}%")
    else:
        print("🚀 Speed improvement: N/A (baseline time ~0s)")
    
    # Assertions to validate output without returning values
    assert isinstance(result, dict)
    assert 'court' in result and all(k in result['court'] for k in ('court_type', 'hierarchy', 'jurisdiction', 'description'))
    assert analysis_time >= 0
    assert cached_time >= 0

if __name__ == "__main__":
    test_analysis_speed()

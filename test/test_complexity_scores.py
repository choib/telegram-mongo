"""
Test to verify text complexity scores are reasonable
"""

import asyncio
from src.context_aware_splitter import create_context_aware_splitter, clear_llm_cache


async def test_complexity_scores():
    """Test that complexity scores are in reasonable range."""
    
    # Create splitter
    splitter = await create_context_aware_splitter()
    
    print("=" * 70)
    print("TEXT COMPLEXITY SCORE VERIFICATION")
    print("=" * 70)
    
    # Test cases with expected complexity
    test_cases = [
        {
            "name": "Simple text",
            "text": "This is a simple sentence. It has basic words and structure.",
            "expected_range": (0.0, 0.3)
        },
        {
            "name": "Moderate text",
            "text": "The contract between parties A and B will be effective from January 1, 2024 to December 31, 2025. Both parties agree to the terms and conditions outlined in this document.",
            "expected_range": (0.2, 0.5)
        },
        {
            "name": "Complex legal text",
            "text": "제1조 (목적) 이 계약의 목적은 당사자 간의 권리 및 의무를 명확히 하는 것이다. 제2조 (정의) 이 계약에서 사용하는 용어의 정의는 다음과 같다. 제3조 (계약기간) 이 계약의 기간은 2024년 1월 1일부터 2025년 12월 31일까지이다.",
            "expected_range": (0.3, 0.8)
        },
        {
            "name": "Technical text",
            "text": "The algorithm uses dynamic programming with O(n^2) time complexity. The space complexity is O(n) due to the memoization table. This approach ensures optimal substructure and overlapping subproblems are handled efficiently.",
            "expected_range": (0.4, 0.8)
        }
    ]
    
    all_passed = True
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print(f"   Text length: {len(test_case['text'])} characters")
        print(f"   Expected range: {test_case['expected_range'][0]:.2f} - {test_case['expected_range'][1]:.2f}")
        
        # Get complexity score
        clear_llm_cache()  # Clear cache for each test
        complexity = await splitter._analyze_text_complexity(test_case['text'])
        
        print(f"   Actual score: {complexity:.4f}")
        
        # Check if score is in expected range
        if test_case['expected_range'][0] <= complexity <= test_case['expected_range'][1]:
            print(f"   ✓ PASS - Score within expected range")
        else:
            print(f"   ✗ FAIL - Score outside expected range")
            all_passed = False
        
        # Also check that score is not too low (< 0.05)
        if complexity < 0.05:
            print(f"   ✗ WARNING - Score is too low (< 0.05)")
            all_passed = False
    
    print("\n" + "=" * 70)
    if all_passed:
        print("✓ ALL TESTS PASSED - Complexity scores are reasonable")
    else:
        print("✗ SOME TESTS FAILED - Complexity scores need adjustment")
    print("=" * 70)
    
    return all_passed


if __name__ == "__main__":
    result = asyncio.run(test_complexity_scores())
    exit(0 if result else 1)

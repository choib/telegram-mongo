#!/usr/bin/env python3
"""
Test script to verify the markdown formatting fix.
"""

import sys
sys.path.insert(0, '/Users/bo/workspace/telegram-mongo/src')

from agentic_handlers import format_response_with_markdown

def test_markdown_formatting():
    """Test the format_response_with_markdown function."""
    
    test_cases = [
        # Test case 1: Text with important words
        {
            'input': 'This is an important note for you.',
            'description': 'Text with important words'
        },
        
        # Test case 2: Text with special characters that need escaping
        {
            'input': 'This is a test [link] with (parentheses) and [brackets].',
            'description': 'Text with special characters'
        },
        
        # Test case 3: Text with URLs
        {
            'input': 'Please visit https://example.com for more information.',
            'description': 'Text with URL'
        },
        
        # Test case 4: Text with underscores
        {
            'input': 'This is a test_with_underscores.',
            'description': 'Text with underscores'
        },
        
        # Test case 5: Text with dots
        {
            'input': 'This is a test. Another sentence.',
            'description': 'Text with dots'
        },
        
        # Test case 6: Complex text with multiple features
        {
            'input': 'This is important! Visit https://example.com for more note.',
            'description': 'Complex text with multiple features'
        },
        
        # Test case 7: Text that might cause the original error
        {
            'input': 'Important: This is a note about the warning system.',
            'description': 'Text with multiple important words'
        },
    ]
    
    print("Testing format_response_with_markdown function...\n")
    
    all_passed = True
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}: {test_case['description']}")
        print(f"Input: {test_case['input']}")
        
        try:
            result = format_response_with_markdown(test_case['input'])
            print(f"Output: {result}")
            print("✓ PASSED\n")
        except Exception as e:
            print(f"✗ FAILED: {e}\n")
            all_passed = False
    
    assert all_passed, "Some markdown formatting tests failed!"

if __name__ == '__main__':
    sys.exit(test_markdown_formatting())

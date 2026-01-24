"""
Test script to verify the markdown fix handles existing markdown correctly.
"""
import sys
sys.path.insert(0, 'src')

from agentic_handlers import format_response_with_markdown

# Test cases that should trigger the "can't find end of bold entity" error
test_cases = [
    {
        "name": "Text with existing bold formatting",
        "input": "This is **important** information",
        "should_not_error": True
    },
    {
        "name": "Text with existing italic formatting",
        "input": "You *may* want to check this",
        "should_not_error": True
    },
    {
        "name": "Text with existing code formatting",
        "input": "Use `code` in your program",
        "should_not_error": True
    },
    {
        "name": "Mixed existing and new markdown",
        "input": "This is **important** and you *should* check it",
        "should_not_error": True
    },
    {
        "name": "Text that matches pattern but already formatted",
        "input": "This is **important** note",
        "should_not_error": True
    },
    {
        "name": "Complex case with URLs and code",
        "input": "Visit `https://example.com` for more info. Use `code` in your program.",
        "should_not_error": True
    },
    {
        "name": "Plain text that should get formatted",
        "input": "This is an important note about the law",
        "should_not_error": True
    }
]

print("=" * 80)
print("MARKDOWN FIX VERIFICATION TEST")
print("=" * 80)
print("\nThis test verifies that the fix prevents the error:")
print("'Can't parse entities: can't find end of bold entity'")
print("\n" + "=" * 80)

all_passed = True

for i, test in enumerate(test_cases, 1):
    print(f"\nTest {i}: {test['name']}")
    print("-" * 80)
    print(f"Input: {test['input']}")
    
    try:
        result = format_response_with_markdown(test['input'])
        print(f"Output: {result[:200]}..." if len(result) > 200 else f"Output: {result}")
        
        # Check for potential issues
        issues = []
        
        # Check for unclosed bold markers
        bold_count = result.count('**')
        if bold_count % 2 != 0:
            issues.append(f"Unbalanced bold markers: {bold_count}")
        
        # Check for unclosed italic markers
        italic_count = result.count('*')
        # Only check if we have an odd number and it's not just for emphasis
        if italic_count > 0 and italic_count % 2 != 0:
            # Count actual italic pairs
            import re
            italic_pairs = len(re.findall(r'\*.*?\*', result))
            if italic_count - 2 * italic_pairs != 0:
                issues.append(f"Unbalanced italic markers: {italic_count}")
        
        # Check for unclosed code markers
        code_count = result.count('`')
        if code_count % 2 != 0:
            issues.append(f"Unbalanced code markers: {code_count}")
        
        if issues:
            print(f"❌ ISSUES FOUND:")
            for issue in issues:
                print(f"  - {issue}")
            all_passed = False
            status = "❌ FAIL"
        else:
            print("✅ PASS - No parsing errors detected")
            status = "✅ PASS"
            
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        all_passed = False
        status = "❌ FAIL"
    
    print(f"\n{status}")

print("\n" + "=" * 80)
if all_passed:
    print("✅ ALL TESTS PASSED - The fix successfully prevents parsing errors!")
else:
    print("❌ SOME TESTS FAILED - Please review the output above")
print("=" * 80)

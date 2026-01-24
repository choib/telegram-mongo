"""
Final comprehensive test for markdown rendering fix
"""
import sys
sys.path.insert(0, 'src')

from agentic_handlers import format_response_with_markdown

# Test cases
test_cases = [
    {
        "name": "Korean legal text with existing markdown",
        "input": """### 검사의 의무에 대한 설명

**법률 문서에 기반한 검사의 의무**

검사의 의무는 형사소송법 및 관련 법률에 따라 규정되어 있으며, 주요 의무는 다음과 같습니다:

1. **수사 지휘 및 수행**
   - 검사는 범죄 수사에 필요한 압수, 수색, 검증을 할 수 있으며, 사법경찰관의 수사 결과를 감독합니다.
   - 형사소송법 제215조에 따르면, 검사는 범죄 수사에 필요한 경우 지방법원 판사에게 영장을 청구하여 압수, 수색, 검증을 할 수 있습니다.

2. **불구속 및 임의 수사의 원칙 준수**
   - 형사소송법 제198조에 따라, 검사는 피의자에 대한 수사를 불구속 상태에서 하는 것을 원칙으로 합니다.
""",
        "expected": "Should preserve **bold**, *italic*, # headers, and - lists"
    },
    {
        "name": "Text with URLs and code",
        "input": "Visit https://example.com for more info. Use `code` in your program.",
        "expected": "Should preserve URLs and code blocks"
    },
    {
        "name": "Text with special characters that need escaping",
        "input": "This is a test with _underscores_, +plus+, and =equals=",
        "expected": "Should escape _ + and = but preserve * and `"
    }
]

print("=" * 80)
print("COMPREHENSIVE MARKDOWN RENDERING TEST")
print("=" * 80)

all_passed = True

for i, test in enumerate(test_cases, 1):
    print(f"\nTest {i}: {test['name']}")
    print("-" * 80)
    
    result = format_response_with_markdown(test['input'])
    
    print(f"Input length: {len(test['input'])}")
    print(f"Output length: {len(result)}")
    print(f"\nExpected: {test['expected']}")
    
    # Check for markdown preservation
    has_bold = '**' in result
    has_italic = '*' in result and not all(c == '*' for c in result if c == '*')
    has_headers = '#' in result
    has_lists = '-' in result
    has_code = '`' in result
    
    print(f"\nMarkdown preservation:")
    print(f"  Bold (**): {has_bold}")
    print(f"  Italic (*): {has_italic}")
    print(f"  Headers (#): {has_headers}")
    print(f"  Lists (-): {has_lists}")
    print(f"  Code (`): {has_code}")
    
    # Check for proper escaping
    escaped_underscore = '\\_' in result
    escaped_plus = '\\+' in result
    escaped_equals = '\\=' in result
    escaped_period = '\\.' in result
    
    print(f"\nCharacter escaping:")
    print(f"  _ (underscore): {escaped_underscore}")
    print(f"  + (plus): {escaped_plus}")
    print(f"  = (equals): {escaped_equals}")
    print(f"  . (period): {escaped_period}")
    
    # Sample output
    print(f"\nSample output (first 200 chars):")
    print(result[:200])
    
    # Determine pass/fail
    test_passed = has_bold and has_headers and has_lists
    status = "✅ PASS" if test_passed else "❌ FAIL"
    print(f"\n{status}")
    
    if not test_passed:
        all_passed = False

print("\n" + "=" * 80)
if all_passed:
    print("✅ ALL TESTS PASSED - Markdown rendering should now work correctly!")
else:
    print("❌ SOME TESTS FAILED - Please review the output above")
print("=" * 80)

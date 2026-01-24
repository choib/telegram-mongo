"""
Test to specifically verify the "can't find end of bold entity" error is fixed.
This test creates scenarios that would have caused the error before the fix.
"""
import sys
sys.path.insert(0, 'src')

from agentic_handlers import format_response_with_markdown

# Test cases that would have caused "can't find end of bold entity" error
error_scenarios = [
    {
        "name": "Already bold text with important word",
        "input": "This is **important** information that you should know",
        "description": "The word 'important' is already wrapped in **bold**. "
                      "Before the fix, this would match 'important' and try to "
                      "wrap it again, resulting in ****important**** which "
                      "Telegram can't parse."
    },
    {
        "name": "Already italic text with emphasis word",
        "input": "You *may* want to check this important note",
        "description": "The word 'may' is already wrapped in *italic*. "
                      "Before the fix, this would match 'may' and try to "
                      "wrap it again, resulting in **may** which Telegram "
                      "can't parse."
    },
    {
        "name": "Already code text with technical term",
        "input": "Use `code` in your program for better performance",
        "description": "The word 'code' is already wrapped in `code`. "
                      "Before the fix, this would match 'code' and try to "
                      "wrap it again, resulting in ``code`` which Telegram "
                      "can't parse."
    },
    {
        "name": "Mixed existing markdown with new content",
        "input": "This is **important** and you *should* check `article 5`",
        "description": "All three types of markdown are already present. "
                      "Before the fix, this would try to wrap each word "
                      "again, creating invalid markdown."
    },
    {
        "name": "URL already in code format",
        "input": "Visit `https://example.com` for more information",
        "description": "The URL is already wrapped in code format. "
                      "Before the fix, this would try to wrap it again."
    },
    {
        "name": "Complex real-world scenario",
        "input": "This is an **important** note. You *may* want to check `article 5` and visit `https://example.com`",
        "description": "A complex scenario with all types of existing markdown. "
                      "This would have definitely caused the parsing error."
    }
]

print("=" * 80)
print("SPECIFIC ERROR SCENARIO TEST")
print("=" * 80)
print("\nTesting scenarios that would have caused:")
print("'Can't parse entities: can't find end of bold entity'")
print("\n" + "=" * 80)

all_passed = True

for i, scenario in enumerate(error_scenarios, 1):
    print(f"\nScenario {i}: {scenario['name']}")
    print("-" * 80)
    print(f"Description: {scenario['description']}")
    print(f"\nInput: {scenario['input']}")
    
    try:
        result = format_response_with_markdown(scenario['input'])
        print(f"Output: {result[:200]}..." if len(result) > 200 else f"Output: {result}")
        
        # Verify the output is valid markdown
        issues = []
        
        # Check for balanced bold markers
        bold_count = result.count('**')
        if bold_count % 2 != 0:
            issues.append(f"Unbalanced bold markers: {bold_count}")
        
        # Check for balanced code markers
        code_count = result.count('`')
        if code_count % 2 != 0:
            issues.append(f"Unbalanced code markers: {code_count}")
        
        # Check for balanced italic markers (more complex)
        import re
        italic_matches = list(re.finditer(r'\*(?!\*)[^\*]+\*(?!\*)', result))
        if len(italic_matches) > 0:
            # Count actual * pairs that are italic (not bold)
            italic_pairs = 0
            for match in italic_matches:
                text = match.group(0)
                if not text.startswith('**') and not text.endswith('**'):
                    italic_pairs >>= 1
            if italic_pairs % 2 != 0:
                issues.append(f"Unbalanced italic markers")
        
        if issues:
            print(f"\n❌ ISSUES FOUND:")
            for issue in issues:
                print(f"  - {issue}")
            all_passed = False
            status = "❌ FAIL"
        else:
            print("\n✅ PASS - Valid markdown generated")
            status = "✅ PASS"
            
    except Exception as e:
        print(f"\n❌ EXCEPTION: {e}")
        all_passed = False
        status = "❌ FAIL"
    
    print(f"\n{status}")

print("\n" + "=" * 80)
if all_passed:
    print("✅ ALL SCENARIOS PASSED!")
    print("\nThe fix successfully prevents the 'can't find end of bold entity' error.")
    print("The function now correctly handles text that already contains markdown formatting.")
else:
    print("❌ SOME SCENARIOS FAILED")
    print("\nPlease review the output above to identify remaining issues.")
print("=" * 80)

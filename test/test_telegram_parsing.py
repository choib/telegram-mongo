"""
Test to check if the formatted text would cause Telegram parsing errors
"""
import sys
sys.path.insert(0, 'src')

from agentic_handlers import format_response_with_markdown

# Test cases that might cause Telegram parsing errors
test_cases = [
    # Case 1: Text with unescaped special characters that could interfere with markdown
    "This is a test with important information about article 5 of the law.",
    
    # Case 2: Text with existing markdown that might conflict
    "This is **already bold** and you *should* know about it.",
    
    # Case 3: Text with URLs
    "Visit https://example.com for more information about the important note.",
    
    # Case 4: Text with special characters that need escaping
    "This is a test (with parentheses) and [brackets] and .dots and !exclamation.",
    
    # Case 5: Complex text with multiple features
    "This is an important note. You should check article 5 and visit https://example.com for more info.",
]

print("=" * 80)
print("TELEGRAM MARKDOWN PARSING VALIDATION TEST")
print("=" * 80)
print("\nChecking if formatted text would cause Telegram parsing errors\n")

all_valid = True

for i, test in enumerate(test_cases, 1):
    print(f"Test {i}:")
    print(f"Input: {test[:100]}..." if len(test) > 100 else f"Input: {test}")
    
    try:
        result = format_response_with_markdown(test)
        print(f"Output: {result[:100]}..." if len(result) > 100 else f"Output: {result}")
        
        # Validate the markdown
        errors = []
        
        # Check for balanced bold markers
        bold_count = result.count('**')
        if bold_count % 2 != 0:
            errors.append(f"Unbalanced bold markers: {bold_count}")
        
        # Check for balanced italic markers
        italic_count = result.count('*')
        if italic_count % 2 != 0:
            errors.append(f"Unbalanced italic markers: {italic_count}")
        
        # Check for balanced code markers
        code_count = result.count('`')
        if code_count % 2 != 0:
            errors.append(f"Unbalanced code markers: {code_count}")
        
        # Check for escaped markdown characters (these would be literal, not syntax)
        # In MarkdownV2, \* is literal *, \** is literal **, etc.
        # We need to check if there are unescaped markdown characters
        
        # Find all ** pairs
        import re
        bold_matches = list(re.finditer(r'(?<!\\)\*\*(.*?)(?<!\\)\*\*', result))
        for match in bold_matches:
            content = match.group(1)
            # Check if the content contains unescaped asterisks
            if '*' in content and not r'\*' in content:
                errors.append(f"Bold content contains unescaped asterisks: {content}")
        
        # Find all * pairs (italic)
        italic_matches = list(re.finditer(r'(?<!\\)\*(.*?)(?<!\\)\*', result))
        for match in italic_matches:
            content = match.group(1)
            # Check if the content contains unescaped asterisks
            if '*' in content and not r'\*' in content:
                errors.append(f"Italic content contains unescaped asterisks: {content}")
        
        # Find all ` pairs
        code_matches = list(re.finditer(r'`(.*?)`', result))
        for match in code_matches:
            content = match.group(1)
            # Check if the content contains backticks
            if '`' in content:
                errors.append(f"Code content contains backticks: {content}")
        
        if errors:
            print("❌ VALIDATION ERRORS:")
            for error in errors:
                print(f"  - {error}")
            all_valid = False
            status = "❌ INVALID"
        else:
            print("✅ VALID - No parsing errors detected")
            status = "✅ VALID"
            
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        all_valid = False
        status = "❌ INVALID"
    
    print(f"{status}\n")

print("=" * 80)
if all_valid:
    print("✅ ALL TESTS PASSED - Text should parse correctly in Telegram")
else:
    print("❌ SOME TESTS FAILED - Potential parsing errors detected")
print("=" * 80)

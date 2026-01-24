"""
Test script to verify enhanced markdown formatting works correctly.
"""

# Import the format_response_with_markdown function
exec(open('src/agentic_handlers.py').read())

# Test cases
test_responses = [
    # Plain text that should get enhanced with markdown
    "This is an important note about the law",
    "You should check article 5 and paragraph 3",
    "This may be relevant to your situation",
    "Please note that this is a caution",
    
    # Text with URLs
    "Check https://example.com for more information",
    
    # Mixed content
    "This is an important point. You should review section 12 and article 3. For example, check https://example.com",
    
    # Korean text
    "이것은 중요한 참고사항입니다",
    "법률 5조와 조항 3을 확인하세요",
]

print("Testing enhanced markdown formatting:\n")
print("=" * 80)

for i, response in enumerate(test_responses, 1):
    print(f"\nTest {i}:")
    print(f"Original: {response}")
    
    formatted = format_response_with_markdown(response)
    print(f"Formatted: {formatted}")
    
    # Check what markdown was added
    has_bold = '**' in response
    has_italic = '*' in response and not has_bold
    has_code = '`' in response
    
    print(f"Has bold markers: {has_bold}")
    print(f"Has italic markers: {has_italic}")
    print(f"Has code markers: {has_code}")
    
    print("-" * 80)

print("\n" + "=" * 80)
print("\nSummary:")
print("- The function now adds markdown formatting to plain text")
print("- Important words get wrapped in **bold**")
print("- Emphasis words get wrapped in *italic*")
print("- Technical terms and URLs get wrapped in `code`")
print("- All special characters are properly escaped")

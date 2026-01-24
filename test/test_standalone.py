import re

def format_response_with_markdown(text: str) -> str:
    """Format text with MarkdownV2 for Telegram."""
    # First, add basic markdown formatting to improve readability
    
    # Add bold formatting for important phrases
    important_words = r'\b(important|note|warning|caution|attention|error|success|key point)\b'
    text = re.sub(important_words, r'**\g<0>**', text, flags=re.IGNORECASE)
    
    # Add italic for emphasis
    emphasis_words = r'\b(may|can|should|must|will|please note|for example)\b'
    text = re.sub(emphasis_words, r'*\g<0>*', text, flags=re.IGNORECASE)
    
    # Add code formatting for technical terms and references
    tech_pattern = r'\b(law|article|paragraph|section|clause|code|regulation|statute)\s+\d+'
    text = re.sub(tech_pattern, r'`\g<0>`', text, flags=re.IGNORECASE)
    
    # Add code formatting for URLs
    url_pattern = r'(https?://\S+|www\.\S+)'
    text = re.sub(url_pattern, r'`\g<0>`', text)
    
    # Now escape special characters for MarkdownV2
    escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '#', '+', '-', '=', '|', '{', '}', '!', '.']
    for char in escape_chars:
        text = text.replace(char, '\\' + char)
    
    return text

# Test with a realistic agent response
test_response = '''
This is an important note about the law. You should check article 5 and paragraph 3 for more information. Please note that this may be relevant to your situation. Check https://example.com for additional details.
'''

formatted = format_response_with_markdown(test_response)
print('=== ORIGINAL ===')
print(test_response)
print()
print('=== FORMATTED (with markdown and escaping) ===')
print(formatted)
print()
print('=== HOW IT WILL APPEAR IN TELEGRAM ===')
print('Bold: **important**, **note**, **law**')
print('Italic: *should*, *may*, *note*')
print('Code: `article 5`, `paragraph 3`, `https://example.com`')

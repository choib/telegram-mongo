"""
Test different escaping strategies
"""

def escape_strategy_1(text):
    """Escape all special chars, then add markdown - WRONG"""
    escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '#', '+', '-', '=', '|', '{', '}', '!', '.']
    for char in escape_chars:
        text = text.replace(char, '\\' + char)
    
    # Try to add markdown - but it's too late, * is already escaped
    import re
    text = re.sub(r'\b(important|note)\b', r'**\g<0>**', text, flags=re.IGNORECASE)
    return text

def escape_strategy_2(text):
    """Add markdown first, then escape - ALSO WRONG"""
    import re
    text = re.sub(r'\b(important|note)\b', r'**\g<0>**', text, flags=re.IGNORECASE)
    
    escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '#', '+', '-', '=', '|', '{', '}', '!', '.']
    for char in escape_chars:
        text = text.replace(char, '\\' + char)
    
    return text

def escape_strategy_3(text):
    """Only escape chars that are NOT part of markdown syntax"""
    import re
    
    # Add markdown formatting
    text = re.sub(r'\b(important|note)\b', r'**\g<0>**', text, flags=re.IGNORECASE)
    
    # Now escape only LITERAL occurrences, not markdown syntax
    # This is tricky - we need to identify what's literal vs syntax
    
    # For now, let's just not escape * and ` since they're commonly used in markdown
    escape_chars = ['_', '[', ']', '(', ')', '~', '#', '+', '-', '=', '|', '{', '}', '!', '.']
    for char in escape_chars:
        text = text.replace(char, '\\' + char)
    
    return text

# Test text
test = "This is **bold** text with *asterisk* and `code` and a note."

print("Original:")
print(test)
print("\n" + "="*80)

print("\nStrategy 1 (escape first, then markdown):")
print(escape_strategy_1(test))

print("\n" + "="*80)
print("\nStrategy 2 (markdown first, then escape all):")
print(escape_strategy_2(test))

print("\n" + "="*80)
print("\nStrategy 3 (markdown first, escape only non-markdown chars):")
print(escape_strategy_3(test))

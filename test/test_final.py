import sys
sys.path.insert(0, '.')
from src.agentic_handlers import format_response_with_markdown

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

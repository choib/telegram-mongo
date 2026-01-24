import re

# Test the regex patterns directly
text = 'You should check article 5 and paragraph 3'

# Test 1: emphasis words
emphasis_pattern = r'\b(may|can|should|must|will|please note|for example)\b'
result1 = re.sub(emphasis_pattern, r'*\g<0>*', text, flags=re.IGNORECASE)
print(f'After emphasis: {result1}')

# Test 2: tech terms
tech_pattern = r'\b(law|article|paragraph|section|clause|code|regulation|statute)\s+\d+'
result2 = re.sub(tech_pattern, r'`\g<0>`', result1, flags=re.IGNORECASE)
print(f'After tech: {result2}')

# Test 3: escaping
escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '#', '+', '-', '=', '|', '{', '}', '!', '.']
result3 = result2
for char in escape_chars:
    result3 = result3.replace(char, '\\' + char)
print(f'After escaping: {result3}')

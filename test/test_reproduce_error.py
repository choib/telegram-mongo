"""
Test to reproduce the exact error from the log:
2025-12-24 17:19:19,294 - ERROR - Error in agentic handler: Can't parse entities: can't find end of bold entity at byte offset 2309
"""
import sys
sys.path.insert(0, 'src')

from agentic_handlers import format_response_with_markdown

# Test with a long text that might trigger the error at byte offset 2309
test_text = """
This is a long response that might contain important information about the law and regulations. 
The system should be able to handle this without errors. However, if there's an issue with 
the markdown formatting, it might cause a "can't find end of bold entity" error at a specific byte offset.

Let me check if this text, when formatted, will cause the error at byte offset 2309.
""" * 50  # Repeat to make it long enough

print("Testing with long text...")
print(f"Text length: {len(test_text)} bytes")
print(f"Text preview: {test_text[:200]}...")

try:
    result = format_response_with_markdown(test_text)
    print(f"\n✅ SUCCESS! Formatting completed without errors.")
    print(f"Result length: {len(result)} bytes")
    print(f"Result preview: {result[:200]}...")
    
    # Check for balanced markers
    bold_count = result.count('**')
    code_count = result.count('`')
    
    print(f"\nBold markers (**): {bold_count} (should be even)")
    print(f"Code markers (`): {code_count} (should be even)")
    
    if bold_count % 2 == 0 and code_count % 2 == 0:
        print("\n✅ All markers are balanced!")
    else:
        print("\n❌ Unbalanced markers detected!")
        
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

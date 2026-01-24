import sys
from typing import List
import os

# Mock the config and context
sys.path.append('/Users/bo/workspace/telegram-mongo')
from src.agentic_handlers import split_message, safe_truncate

def test_truncation():
    print("Testing safe_truncate...")
    # Test unclosed bold
    text = "This is *bold and unclosed"
    # Ensure max_len is large enough to include the '*' given the 10-char safety buffer
    # '*' is at index 8, so we need target_pos >= 9. 
    # target_pos = max_len - 10, so max_len >= 19.
    truncated = safe_truncate(text, 20, suffix="")
    print(f"Truncated unclosed bold: '{truncated}'")
    assert truncated.endswith('*')
    
    # Test escaped characters at the end
    text = "Escaped dot\\."
    truncated = safe_truncate(text, 22, suffix="")
    print(f"Truncated escaped dot: '{truncated}'")
    assert truncated.endswith('\\.')
    
    print("safe_truncate tests passed!")

def test_splitting():
    print("\nTesting split_message...")
    # Create a long message with multiple paragraphs and bold text
    long_text = ""
    for i in range(20):
        long_text += f"Paragraph {i}: This is some *bold text for paragraph {i}* and it just keeps going on and on to fill up space so we can test the splitting logic properly. "
        long_text += "More content here to ensure we cross the 4096 character limit eventually.\n\n"
    
    print(f"Total length: {len(long_text)}")
    
    # Split with a small limit for testing
    parts = split_message(long_text, max_part_len=500)
    print(f"Split into {len(parts)} parts.")
    
    for i, part in enumerate(parts):
        print(f"Part {i} length: {len(part)}")
        # Check if tags are balanced (simple check for even number of stars in this controlled test)
        star_count = part.count('*')
        if star_count % 2 != 0:
            print(f"WARNING: Part {i} has unbalanced stars: {star_count}")
        
    assert len(parts) > 1
    print("split_message tests passed!")

if __name__ == "__main__":
    try:
        test_truncation()
        test_splitting()
        print("\nAll verification tests passed!")
    except Exception as e:
        print(f"\nTests failed: {e}")
        import traceback
        traceback.print_exc()

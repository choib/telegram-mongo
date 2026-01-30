import sys
import os
sys.path.append('/Users/bo/workspace/telegram-mongo')
from update_laws import update_law

target_laws = [
    "가맹사업거래의 공정화에 관한 법률",
    "식품위생법",
    "상법",
    "상표법",
    "부가가치세법",
    "근로기준법",
    "소비자기본법",
    "독점규제 및 공정거래법"
]

print(f"Starting specific update for: {target_laws}")
for law in target_laws:
    # We pass an empty list for old_filenames because my updated update_law 
    # now uses a pattern-based deletion for robustness.
    success = update_law(law, [])
    if success:
        print(f"Successfully processed {law}")
    else:
        # Try without '대한민국' prefix for constitution if it failed
        if law == "대한민국헌법":
            print("Retrying as '헌법'...")
            update_law("헌법", [])

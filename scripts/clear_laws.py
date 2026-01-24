import os

SOURCE_DIR = "/Users/bo/workspace/korean_law"
count = 0
for f in os.listdir(SOURCE_DIR):
    if f.endswith('.txt'):
        try:
            os.remove(os.path.join(SOURCE_DIR, f))
            count += 1
        except:
            pass
print(f"Cleared {count} files.")

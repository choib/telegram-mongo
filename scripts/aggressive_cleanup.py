import os

SOURCE_DIR = "/Users/bo/workspace/korean_law"
deleted_count = 0
kept_count = 0

for f in os.listdir(SOURCE_DIR):
    if not f.endswith('.txt'):
        continue
    
    # Any file with brackets, newlines, or carriage returns is considered "messy"
    if '[' in f or ']' in f or '\r' in f or '\n' in f:
        path = os.path.join(SOURCE_DIR, f)
        try:
            os.remove(path)
            deleted_count += 1
        except Exception as e:
            print(f"Error deleting {f}: {e}")
    else:
        kept_count += 1

print(f"Aggressive cleanup complete.")
print(f"Deleted: {deleted_count} messy files.")
print(f"Kept: {kept_count} clean files.")

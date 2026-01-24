import os

SOURCE_DIR = "/Users/bo/workspace/korean_law"

def cleanup():
    if not os.path.exists(SOURCE_DIR):
        print("Source directory not found.")
        return
    
    deleted_count = 0
    for filename in os.listdir(SOURCE_DIR):
        path = os.path.join(SOURCE_DIR, filename)
        if not os.path.isfile(path):
            continue
            
        # Check for carriage returns, newlines, or metadata prefix
        if '\r' in filename or '\n' in filename or filename.startswith('['):
            try:
                os.remove(path)
                print(f"Deleted: {repr(filename)}")
                deleted_count += 1
            except Exception as e:
                print(f"Error deleting {repr(filename)}: {e}")
                
    print(f"\nCleanup complete. Deleted {deleted_count} files.")

if __name__ == "__main__":
    cleanup()

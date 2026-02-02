import os

def sync_laws():
    law_names_path = "/Users/bo/workspace/telegram-mongo/law_names.txt"
    extracted_names_path = "/Users/bo/workspace/telegram-mongo/extracted_law_names.txt"
    
    # Read existing law names
    if os.path.exists(law_names_path):
        with open(law_names_path, 'r', encoding='utf-8') as f:
            existing_laws = set(line.strip() for line in f if line.strip())
    else:
        existing_laws = set()
    
    # Read extracted law names
    if os.path.exists(extracted_names_path):
        with open(extracted_names_path, 'r', encoding='utf-8') as f:
            extracted_laws = set(line.strip() for line in f if line.strip())
    else:
        print(f"Error: {extracted_names_path} not found.")
        return

    # Find new laws
    new_laws = extracted_laws - existing_laws
    print(f"Found {len(new_laws)} new laws to add.")
    
    if new_laws:
        all_laws = sorted(list(existing_laws | extracted_laws))
        with open(law_names_path, 'w', encoding='utf-8') as f:
            for law in all_laws:
                f.write(f"{law}\n")
        print(f"Updated {law_names_path} with {len(all_laws)} total laws.")
    else:
        print("No new laws found to add.")

if __name__ == "__main__":
    sync_laws()

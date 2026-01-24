---
name: law_updater
description: Update the local Korean law text files from the National Law Information Center.
---

# Law Updater Skill

This skill provides tools for keeping the Korean law text files in sync with the latest versions from `law.go.kr`.

## Instructions

### Updating Laws
The primary script is `update_laws.py`. It reads a list of law names and fetches their latest XML or PDF content, converts it to text, and saves it to the configured source directory.

Example:
```bash
python3 .agent/skills/law_updater/scripts/update_laws.py
```

## Troubleshooting
- **Network Issues**: The script connects to `www.law.go.kr`. Ensure the environment has internet access.
- **Log Files**: Check `update_laws.log` in the root directory for specific errors and successes for each law.
- **Source Directory**: The destination for text files is currently hardcoded in the script (`SOURCE_DIR`). Ensure this directory exists.

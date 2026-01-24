---
name: rag_manager
description: Manage and debug the Retrieval-Augmented Generation (RAG) system.
---

# RAG Manager Skill

This skill provides tools and instructions for managing the RAG system, including vector store inspection and retrieval testing.

## Instructions

### Testing Retrieval Accuracy
Use the `scripts/test_retrieval.py` script to verify what chunks are being retrieved for a given query.

Example:
```bash
python3 .agent/skills/rag_manager/scripts/test_retrieval.py "How do I file US taxes?"
```

### Inspecting Vector Store
You can directly check the `db/` directory to see the status of the persistent stores.
The current active database path is configured in `config/config.py`.

## troubleshooting
If retrieval results are poor:
1. Check `EMBED_PATH` in `.env` to ensure the correct embedding model is being used.
2. Verify that documents have been properly indexed in the `db/` directory.
3. Check `CHUNK_SIZE` in `.env`.

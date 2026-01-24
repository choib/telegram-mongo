# 📚 Context-Aware RAG Specification (SPEC_RAG.md)

This specification defines the document processing and retrieval strategy for legal documents.

## 1. Document Ingestion Pipeline
1. **Source**: PDF or Text files containing raw Korean law text.
2. **Preprocessing**: Removal of boilerplate but preservation of structural markers (e.g., 제1조, ①).
3. **Splitting**: **Context-Aware Splitter**
   - **Unit**: Primarily splits by Articles (`제N조`).
   - **Hierarchy**: Maintains the relationship between parent Articles and child Paragraphs/Items.
   - **Chunk Size**: Target ~1024 characters per chunk.

## 2. Embedding & Vectorization
- **Embedding Model**: KR-SBERT or similar specialized Korean legal embedding model.
- **Store**: ChromaDB local instance.
- **Indexing**: Optimized for similarity search with Metadata filtering (by Law name).

## 3. Retrieval Strategy
- **Stage 1 (Augmentation)**: LLM rephrases the user query into a formal legal search query using recent conversation context.
- **Stage 2 (Similarity Search)**: `k=4` retrieval using cosine similarity.
- **Stage 3 (Re-ranking)**: Heuristic or LLM-based re-ranking to select the most relevant Article/Clause.

## 4. Maintenance
- **Rebuilding**: Rebuilding is triggered via `python3 rag.py --rebuild` when new legal files are added to the `data/` directory.
- **Update Frequency**: On-demand or scheduled via `update_laws.py` fetching from NLIC.

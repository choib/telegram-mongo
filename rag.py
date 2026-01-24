"""
Context-aware RAG (Retrieval-Augmented Generation) module for legal document retrieval.
This module provides optimized vector store implementation with context-aware chunking.
"""

# Try imports from langchain first, fall back to langchain_community for compatibility
try:
    from langchain.embeddings import HuggingFaceEmbeddings
    from langchain.vectorstores import Chroma
    from langchain.document_loaders import TextLoader, DirectoryLoader
    from langchain.schema import Document
    from langchain.text_splitter import RecursiveCharacterTextSplitter
except ImportError:
    # Fallback for older langchain versions
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from langchain_chroma import Chroma
    from langchain_community.document_loaders import TextLoader, DirectoryLoader
    from langchain_core.documents import Document
    from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import config
import os
import re
import logging
from typing import List, Optional, Dict, Any
import asyncio

# Monkeypatch simsimd to fix incompatibility with LangChain's math utils
# This fixes "unsupported operand type(s) for -: 'int' and 'simsimd.DistancesTensor'"
try:
    import simsimd
    import numpy as np
    _original_cdist = simsimd.cdist
    def _patched_cdist(*args, **kwargs):
        res = _original_cdist(*args, **kwargs)
        if hasattr(res, "__array__") or str(type(res)).find("DistancesTensor") != -1:
            return np.array(res)
        return res
    simsimd.cdist = _patched_cdist
    # Note: logger is defined below, so we use a temporary one if needed or just pass
except Exception:
    pass

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import context-aware splitter
from src.context_aware_splitter import LegalContextAwareSplitter, create_context_aware_splitter

# Global context-aware splitter instance
context_aware_splitter = None


class ContextAwareLegalDocumentProcessor:
    """
    Process legal documents for RAG pipeline with context-aware chunking.
    Handles document loading, text splitting, and metadata extraction.
    """
    
    def __init__(self, config, use_context_aware: bool = True):
        self.config = config
        self.embeddings = HuggingFaceEmbeddings(model_name=config.EMBED_PATH)
        self.text_loader_kwargs = {'autodetect_encoding': True}
        self.use_context_aware = use_context_aware
        self.splitter = self._create_text_splitter()
    
    def _create_text_splitter(self) -> RecursiveCharacterTextSplitter:
        """Create optimized text splitter for legal documents."""
        return RecursiveCharacterTextSplitter().from_huggingface_tokenizer(
            self.config.TOKENIZER,
            chunk_size=self.config.CHUNK_SIZE,
            chunk_overlap=50,
        )
    
    async def _split_with_context_awareness(self, text: str) -> List[str]:
        """
        Split text using context-aware splitter.
        
        Args:
            text: Text to split
            
        Returns:
            List of text chunks
        """
        global context_aware_splitter
        
        if context_aware_splitter is None:
            context_aware_splitter = await create_context_aware_splitter()
        
        return await context_aware_splitter.split_text(text)
    
    async def _split_traditional(self, text: str) -> List[str]:
        """
        Split text using traditional recursive character splitter.
        
        Args:
            text: Text to split
            
        Returns:
            List of text chunks
        """
        return self.splitter.split_text(text)
    
    def _extract_legal_metadata(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extract legal metadata from document text.
        Returns structured metadata including law type, article number, etc.
        """
        pattern = re.compile(
            r'^(?P<law>\w+):?\s+제\s?(?P<number>\d+)\s?조(?:의\s+(?P<sub>\d+)\w?)?[\n\s]?(?P<title>[\w|\d|\s|\u3000-\u303f]+)?\((?P<contents>.*)?',
            flags=re.U | re.DOTALL
        )
        
        match = re.search(pattern, text)
        if match:
            return match.groupdict()
        return None
    
    def _clean_and_normalize_text(self, text: str) -> str:
        """Clean and normalize text for better embedding quality."""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        # Normalize Korean characters
        text = re.sub(r'[\u3000-\u303f]', ' ', text)
        return text
    
    async def load_and_process_documents(self) -> List[Document]:
        """
        Load and process legal documents from directory.
        Returns list of processed Document objects with enriched metadata.
        """
        logger.info(f"Loading documents from {self.config.LOCAL_DATA}")
        
        try:
            loader = DirectoryLoader(
                self.config.LOCAL_DATA,
                glob="*.txt",
                show_progress=True,
                loader_cls=TextLoader,
                loader_kwargs=self.text_loader_kwargs
            )
            docs = loader.load()
            logger.info(f"Loaded {len(docs)} documents")
            
            processed_documents = []
            
            for page in docs:
                try:
                    metadata = page.metadata
                    filename = os.path.basename(metadata["source"])
                    base_name = filename.split("(")[0].strip()
                    
                    # Split by legal article markers first
                    chunks = re.split(
                        r'\n+(?=제\s?\d+[조절장편관])|(?=제\s?\d+[조절장편관]\s?\(.*\))\s?$',
                        page.page_content
                    )
                    
                    for chunk in chunks:
                        chunk = chunk.strip()
                        if not chunk or len(chunk) < 50:  # Skip very short chunks
                            continue
                            
                        # Use context-aware splitting if enabled
                        if self.use_context_aware:
                            logger.info(f"Using context-aware splitting for chunk from {base_name}")
                            sub_chunks = await self._split_with_context_awareness(chunk)
                        else:
                            logger.info(f"Using traditional splitting for chunk from {base_name}")
                            sub_chunks = await self._split_traditional(chunk)
                        
                        # Extract legal metadata
                        legal_meta = self._extract_legal_metadata(chunk)
                        
                        # Process each sub-chunk
                        for i, sub_chunk in enumerate(sub_chunks):
                            # Create enriched metadata - filter out None values
                            enriched_metadata = {
                                "source": metadata["source"],
                                "filename": base_name,
                                "content_length": len(sub_chunk),
                                "chunk_id": f"{base_name}_{len(processed_documents)}_{i}",
                                "split_method": "context_aware" if self.use_context_aware else "traditional"
                            }
                            
                            # Add legal metadata only if not None
                            if legal_meta:
                                law_type = legal_meta.get("law")
                                if law_type:
                                    enriched_metadata["law_type"] = law_type
                                article_number = legal_meta.get("number")
                                if article_number:
                                    enriched_metadata["article_number"] = article_number
                                article_title = legal_meta.get("title")
                                if article_title:
                                    enriched_metadata["article_title"] = article_title
                            
                            # Clean and normalize text
                            clean_text = self._clean_and_normalize_text(sub_chunk)
                            
                            # Create document with proper structure
                            document_content = f"{base_name}: {clean_text}"
                            processed_documents.append(
                                Document(
                                    page_content=document_content,
                                    metadata=enriched_metadata
                                )
                            )
                        
                except Exception as e:
                    logger.warning(f"Error processing document {page.metadata.get('source', 'unknown')}: {e}")
                    continue
            
            logger.info(f"Processed {len(processed_documents)} document chunks")
            return processed_documents
            
        except Exception as e:
            logger.error(f"Failed to load documents: {e}")
            raise


# Alias for backward compatibility with existing tests
LegalDocumentProcessor = ContextAwareLegalDocumentProcessor


class LegalVectorStore:
    """
    Optimized vector store for legal document retrieval.
    Provides specialized retrievers for different query types.
    """
    
    def __init__(self, config, embeddings, persist_directory: str):
        self.config = config
        self.embeddings = embeddings
        self.persist_directory = persist_directory
        self.vector_store = None
    
    def initialize_from_documents(self, documents: List[Document]):
        """
        Initialize vector store from processed documents.
        """
        logger.info(f"Creating vector store with {len(documents)} documents")
        
        try:
            # Process in batches to avoid "Batch size of ... is greater than max batch size of 5461"
            batch_size = 5000
            for i in range(0, len(documents), batch_size):
                batch = documents[i : i + batch_size]
                logger.info(f"Processing batch {i//batch_size + 1}/{(len(documents)-1)//batch_size + 1}")
                
                if i == 0:
                    self.vector_store = Chroma.from_documents(
                        documents=batch,
                        embedding=self.embeddings,
                        persist_directory=self.persist_directory
                    )
                else:
                    self.vector_store.add_documents(batch)
            
            logger.info("Vector store created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create vector store: {e}")
            raise
    
    def load_existing(self):
        """
        Load existing vector store from disk.
        """
        logger.info(f"Loading existing vector store from {self.persist_directory}")
        
        try:
            self.vector_store = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings
            )
            logger.info("Vector store loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load vector store: {e}")
            raise
    
    def get_question_retriever(self):
        """
        Get retriever optimized for question-type queries.
        Uses lower diversity (higher lambda_mult) to focus on most relevant results.
        """
        if not self.vector_store:
            raise ValueError("Vector store not initialized")
        
        return self.vector_store.as_retriever(
            search_type="mmr",
            search_kwargs={
                'lambda_mult': 0.3,
                'k': 1,
                'fetch_k': 9,
                'score_threshold': 0.7
            }
        )
    
    def get_answer_retriever(self):
        """
        Get retriever optimized for answer-type queries.
        Uses balanced diversity for comprehensive retrieval.
        """
        if not self.vector_store:
            raise ValueError("Vector store not initialized")
        
        return self.vector_store.as_retriever(
            search_type="mmr",
            search_kwargs={
                'lambda_mult': 0.7,
                'k': 7,
                'fetch_k': 29,
                'score_threshold': 0.8
            }
        )
    
    def get_inspect_retriever(self):
        """
        Get retriever optimized for detailed inspection queries.
        Uses high diversity and strict scoring for precise retrieval.
        """
        if not self.vector_store:
            raise ValueError("Vector store not initialized")
        
        return self.vector_store.as_retriever(
            search_type="mmr",
            search_kwargs={
                'lambda_mult': 0.7,
                'k': 3,
                'fetch_k': 29,
                'score_threshold': 0.9
            }
        )


async def create_context_aware_rag_pipeline(config, force_rebuild: bool = False):
    """
    Create complete RAG pipeline with context-aware chunking.
    
    Args:
        config: Configuration object
        force_rebuild: If True, rebuild vector store even if it exists
        
    Returns:
        Tuple of (question_retriever, answer_retriever, inspect_retriever)
    """
    
    # Validate configuration
    if not config.EMBED_PATH or not config.DATABASE or not config.LOCAL_DATA:
        raise ValueError("Missing required configuration: EMBED_PATH, DATABASE, or LOCAL_DATA")
    
    # Check if vector store exists
    vector_store_exists = os.path.exists(config.DATABASE)
    
    if vector_store_exists and not force_rebuild:
        logger.info("Existing vector store found, loading it...")
        embeddings = HuggingFaceEmbeddings(model_name=config.EMBED_PATH)
        vector_store = LegalVectorStore(config, embeddings, config.DATABASE)
        vector_store.load_existing()
    
    else:
        logger.info("Building new vector store from documents with context-aware chunking...")
        embeddings = HuggingFaceEmbeddings(model_name=config.EMBED_PATH)
        
        # Process documents with context-aware splitting
        processor = ContextAwareLegalDocumentProcessor(config, use_context_aware=True)
        documents = await processor.load_and_process_documents()
        
        # Create vector store
        vector_store = LegalVectorStore(config, embeddings, config.DATABASE)
        vector_store.initialize_from_documents(documents)
    
    # Return configured retrievers
    return (
        vector_store.get_question_retriever(),
        vector_store.get_answer_retriever(),
        vector_store.get_inspect_retriever()
    )


def create_rag_pipeline(config, force_rebuild: bool = False):
    """Synchronous wrapper for pipeline creation."""
    import asyncio
    
    # Check if a loop is already running
    try:
        loop = asyncio.get_running_loop()
        if loop.is_running():
            # If we're already in an async event loop, we can't use asyncio.run
            # This is a bit tricky for module-level initialization.
            # We'll use a simplified version for loading existing.
            if os.path.exists(config.DATABASE) and not force_rebuild:
                embeddings = HuggingFaceEmbeddings(model_name=config.EMBED_PATH)
                vector_store = LegalVectorStore(config, embeddings, config.DATABASE)
                vector_store.load_existing()
                return (
                    vector_store.get_question_retriever(),
                    vector_store.get_answer_retriever(),
                    vector_store.get_inspect_retriever()
                )
    except RuntimeError:
        pass
        
    return asyncio.run(create_context_aware_rag_pipeline(config, force_rebuild))

# Global retriever instances and lazy loader
_retriever_cache = {}

def get_retriever(type='ans', config=None, force_rebuild=False):
    """
    Lazy loader for retrievers to avoid module-level initialization issues.
    """
    global _retriever_cache
    if type not in _retriever_cache or force_rebuild:
        from config import config as default_config
        cfg = config or default_config
        try:
            logger.info(f"Initializing RAG pipeline (requested {type})...")
            q, ans, i = create_rag_pipeline(cfg, force_rebuild=force_rebuild)
            _retriever_cache['question'] = q
            _retriever_cache['ans'] = ans
            _retriever_cache['inspect'] = i
        except Exception as e:
            logger.error(f"Failed to initialize RAG pipeline: {e}")
            from langchain_core.retrievers import BaseRetriever
            class DummyRetriever(BaseRetriever):
                def _get_relevant_documents(self, query): return []
            dummy = DummyRetriever()
            _retriever_cache['question'] = dummy
            _retriever_cache['ans'] = dummy
            _retriever_cache['inspect'] = dummy
            
    return _retriever_cache.get(type)

# Wrapper classes for lazy retrievers to maintain backward compatibility
class LazyRetrieverProxy:
    def __init__(self, type):
        self._type = type
    
    @property
    def _retriever(self):
        return get_retriever(self._type)
    
    def invoke(self, *args, **kwargs):
        return self._retriever.invoke(*args, **kwargs)
    
    def get_relevant_documents(self, *args, **kwargs):
        # LangChain 0.1 legacy method
        return self._retriever.get_relevant_documents(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(self._retriever, name)

# Exported instances for backward compatibility
ans_retriever = LazyRetrieverProxy('ans')
question_retriever = LazyRetrieverProxy('question')
inspect_retriever = LazyRetrieverProxy('inspect')

if __name__ == "__main__":
    import argparse
    import sys
    import config.config as cfg
    
    parser = argparse.ArgumentParser(description="Legal RAG Database Management")
    parser.add_argument("--rebuild", action="store_true", help="Force rebuild the vector database")
    parser.add_argument("--test", type=str, help="Run a test query")
    
    args = parser.parse_args()
    
    if args.rebuild:
        logger.info("Initializing force rebuild of the RAG database...")
        asyncio.run(create_context_aware_rag_pipeline(cfg, force_rebuild=True))
        logger.info("Database regeneration complete.")
    
    if args.test:
        logger.info(f"Running test query: {args.test}")
        retriever = get_retriever('ans', config=cfg)
        results = retriever.invoke(args.test)
        print(f"\nFound {len(results)} relevant chunks:")
        for i, doc in enumerate(results):
            print(f"\n--- Result {i+1} ---")
            print(f"File: {doc.metadata.get('source')}")
            print(f"Content Sample: {doc.page_content[:200]}...")
    
    if not args.rebuild and not args.test:
        parser.print_help()

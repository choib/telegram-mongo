import os
import logging
import asyncio
from typing import List, Optional, Dict, Any
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Import context-aware splitter
from src.context_aware_splitter import create_context_aware_splitter

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GeneralPDFProcessor:
    """
    Process general PDF documents for RAG pipeline with context-aware support.
    """
    
    def __init__(self, embed_path: str, chunk_size: int = 1000, chunk_overlap: int = 100, use_context_aware: bool = True):
        self.embed_path = embed_path
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.use_context_aware = use_context_aware
        self.embeddings = HuggingFaceEmbeddings(model_name=embed_path)
        self.standard_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            is_separator_regex=False,
        )
        self.context_aware_splitter = None
    
    async def _initialize_splitter(self):
        """Initialize the context-aware splitter if needed."""
        if self.use_context_aware and self.context_aware_splitter is None:
            logger.info("Initializing context-aware splitter for PDF processor...")
            self.context_aware_splitter = await create_context_aware_splitter()

    async def load_and_process_pdfs(self, data_dir: str) -> List[Document]:
        """
        Load and process PDF documents from directory (Asynchronous).
        """
        logger.info(f"Loading PDFs from {data_dir}")
        
        if not os.path.exists(data_dir):
            logger.error(f"Data directory {data_dir} does not exist")
            return []
            
        try:
            await self._initialize_splitter()
            
            loader = DirectoryLoader(
                data_dir,
                glob="*.pdf",
                loader_cls=PyPDFLoader,
                show_progress=True
            )
            
            # loader.load() is synchronous, but we split asynchronously
            docs = loader.load()
            logger.info(f"Loaded {len(docs)} document pages")
            
            processed_docs = []
            
            for doc in docs:
                if self.use_context_aware:
                    # Context-aware splitting
                    chunks = await self.context_aware_splitter.split_text(doc.page_content)
                    for chunk in chunks:
                        processed_docs.append(Document(
                            page_content=chunk,
                            metadata={**doc.metadata, "split_method": "context_aware"}
                        ))
                else:
                    # Traditional splitting
                    split_docs = self.standard_splitter.split_documents([doc])
                    for sd in split_docs:
                        sd.metadata["split_method"] = "traditional"
                    processed_docs.extend(split_docs)
            
            logger.info(f"Created {len(processed_docs)} chunks from {len(docs)} pages")
            return processed_docs
            
        except Exception as e:
            logger.error(f"Failed to load PDF documents: {e}")
            raise

class PDFVectorStore:
    """
    Vector store for general PDF documents.
    """
    
    def __init__(self, embed_path: str, persist_directory: str):
        self.embeddings = HuggingFaceEmbeddings(model_name=embed_path)
        self.persist_directory = persist_directory
        self.vector_store = None
        
    def initialize_from_documents(self, documents: List[Document]):
        """Initialize vector store from documents."""
        logger.info(f"Creating vector store at {self.persist_directory}")
        try:
            self.vector_store = Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings,
                persist_directory=self.persist_directory
            )
            logger.info("Vector store created successfully")
        except Exception as e:
            logger.error(f"Failed to create vector store: {e}")
            raise
            
    def load_existing(self):
        """Load existing vector store from disk."""
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
            
    def get_retriever(self, k: int = 5, score_threshold: float = 0.5):
        """Get standard retriever."""
        if not self.vector_store:
            raise ValueError("Vector store not initialized")
        return self.vector_store.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={"k": k, "score_threshold": score_threshold}
        )

async def create_pdf_rag_pipeline(
    embed_path: str, 
    data_dir: str, 
    db_dir: str, 
    force_rebuild: bool = False,
    use_context_aware: bool = True
):
    """
    Create a complete PDF RAG pipeline (Asynchronous).
    """
    if os.path.exists(db_dir) and not force_rebuild:
        logger.info("Loading existing PDF vector store...")
        vector_store = PDFVectorStore(embed_path, db_dir)
        vector_store.load_existing()
    else:
        logger.info("Building new PDF vector store...")
        processor = GeneralPDFProcessor(embed_path, use_context_aware=use_context_aware)
        documents = await processor.load_and_process_pdfs(data_dir)
        
        vector_store = PDFVectorStore(embed_path, db_dir)
        vector_store.initialize_from_documents(documents)
        
    return vector_store.get_retriever()

async def main():
    # Example usage / testing
    TEST_EMBED = os.getenv("EMBED_PATH", "sentence-transformers/all-MiniLM-L6-v2")
    TEST_DATA = "./data/pdfs"
    TEST_DB = "./db/pdf_store"
    
    os.makedirs(TEST_DATA, exist_ok=True)
    
    print(f"Testing PDF RAG Pipeline creation with embed: {TEST_EMBED}")
    try:
        retriever = await create_pdf_rag_pipeline(TEST_EMBED, TEST_DATA, TEST_DB)
        print("✅ PDF RAG Pipeline initialized with context-aware chunking")
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")

if __name__ == "__main__":
    asyncio.run(main())

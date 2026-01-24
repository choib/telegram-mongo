"""
Test to verify the Chroma persist() fix
"""
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
import tempfile

print("Testing Chroma vector store without persist() call...")

with tempfile.TemporaryDirectory() as tmpdir:
    docs = [Document(page_content='test document')]
    
    # This should work without calling persist()
    chroma = Chroma.from_documents(
        documents=docs,
        embedding=None,  # Using None for testing
        persist_directory=tmpdir
    )
    
    print('✓ Chroma.from_documents works without persist() call')
    print('✓ Chroma object created successfully')
    print('✓ Fix verified!')

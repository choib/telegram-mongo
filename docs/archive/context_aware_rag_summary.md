# Context-Aware RAG Implementation Summary

## Overview
This document summarizes the implementation of context-aware chunking for the RAG system, which uses the local Ollama LLM to dynamically determine optimal chunk boundaries based on semantic context preservation.

## Key Features

### 1. Context-Aware Text Splitter (`src/context_aware_splitter.py`)

The core innovation is a context-aware text splitter that:

- **Analyzes text complexity**: Uses LLM to assess how complex the text is (0-1 scale)
- **Dynamically adjusts chunk sizes**: More complex text gets smaller chunks to preserve context
- **Assesses context continuity**: Evaluates potential split points to minimize context disruption
- **Finds optimal split points**: Searches for natural boundaries that maintain semantic continuity
- **Provides fallback**: Reverts to traditional splitting if LLM analysis fails

#### Key Methods:

- `_assess_context_break(text, split_point)`: Rates how disruptive a split would be (0-1 scale)
- `_analyze_text_complexity(text)`: Determines text complexity to adjust chunk sizes
- `_find_optimal_split_points(text, max_length)`: Finds best places to split while preserving context
- `split_text(text)`: Main entry point that returns context-aware chunks

### 2. Legal-Specific Context-Aware Splitter

Extends the base splitter with legal document optimization:

- **Preserves legal boundaries**: Avoids splitting within articles, sections, etc.
- **Legal pattern detection**: Recognizes patterns like "제1조", "제2절", "1호", etc.
- **Boundary-aware splitting**: Combines context analysis with legal structure preservation

### 3. Context-Aware RAG Pipeline (`rag_context_aware.py`)

A new RAG implementation that integrates context-aware chunking:

- **ContextAwareLegalDocumentProcessor**: Enhanced document processor with context-aware splitting
- **Dual splitting modes**: Can use either context-aware or traditional splitting
- **Metadata enrichment**: Tracks which splitting method was used for each chunk
- **Backward compatibility**: Maintains the same interface as the original RAG

## Technical Implementation

### LLM-Powered Context Analysis

The system uses the local Ollama LLM to:

1. **Assess context continuity** between text segments:
   ```python
   prompt = f"""
   Analyze the following two text segments and determine how well they maintain 
   context continuity. On a scale from 0 to 1, rate the context continuity.
   
   Segment 1: {before_text}
   Segment 2: {after_text}
   
   Only respond with the number, no additional text.
   """
   ```

2. **Analyze text complexity**:
   ```python
   prompt = f"""
   Analyze the following text and determine its complexity on a scale from 0 to 1.
   
   Text: {text[:500]}...
   
   Only respond with the number, no additional text.
   """
   ```

### Dynamic Chunk Size Adjustment

Based on complexity score, chunk sizes are adjusted:
- **Simple text (complexity=0)**: Uses larger chunks (up to max_chunk_size)
- **Complex text (complexity=1)**: Uses smaller chunks (down to base_chunk_size)
- **Formula**: `chunk_size = base_chunk_size + (max_chunk_size - base_chunk_size) * (1 - complexity)`

### Optimal Split Point Finding

The algorithm:
1. Determines target chunk size based on complexity
2. Searches within a 200-character window around the target
3. Assesses context continuity at each potential split point
4. Selects the split point with highest continuity score
5. Adds overlap to ensure context continuity between chunks

## Benefits

### 1. Context Preservation
- Avoids breaking within important context units
- Maintains semantic continuity across chunks
- Better preserves the meaning and relationships in legal text

### 2. Adaptive Chunking
- Smaller chunks for complex, nuanced legal provisions
- Larger chunks for straightforward, simple text
- Optimal balance between granularity and context preservation

### 3. Legal Document Optimization
- Preserves article boundaries (제1조, 제2절, etc.)
- Keeps related legal provisions together
- Avoids splitting within citations and references

### 4. Robustness
- Fallback to traditional splitting if LLM fails
- Graceful error handling
- Comprehensive logging for monitoring

## Usage

### Basic Usage

```python
# Create context-aware splitter
from src.context_aware_splitter import create_context_aware_splitter

splitter = await create_context_aware_splitter()
chunks = await splitter.split_text(legal_text)
```

### RAG Pipeline Usage

```python
# Create context-aware RAG pipeline
from rag_context_aware import create_context_aware_rag_pipeline

ques_retriever, ans_retriever, inspect_retriever = await create_context_aware_rag_pipeline(config, force_rebuild=True)
```

### Configuration Options

```python
# Use context-aware splitting
processor = ContextAwareLegalDocumentProcessor(config, use_context_aware=True)

# Use traditional splitting (fallback)
processor = ContextAwareLegalDocumentProcessor(config, use_context_aware=False)
```

## Performance Considerations

### LLM Overhead
- Each split point assessment requires an LLM call
- Complexity analysis requires an LLM call per document
- Performance impact depends on LLM response time

### Optimization Strategies

1. **Search window limiting**: Only assess split points within a 200-character window
2. **Step size**: Check every 5 characters within the window
3. **Caching**: Global splitter instance is reused across documents
4. **Fallback**: Traditional splitting used if LLM fails

### Expected Performance
- **With context-aware splitting**: Slower but higher quality chunks
- **With traditional splitting**: Faster but may break context
- **Recommended**: Use context-aware for initial vector store creation, traditional for incremental updates

## Testing

### Test Script

```python
if __name__ == "__main__":
    import asyncio
    
    async def test_splitter():
        print("Testing context-aware splitter...")
        
        # Create test text with clear context
        test_text = """
        제1조 (목적) 이 계약의 목적은 당사자 간의 권리 및 의무를 명확히 하는 것이다.
        제2조 (정의) 이 계약에서 사용하는 용어의 정의는 다음과 같다.
        제3조 (계약기간) 이 계약의 기간은 2024년 1월 1일부터 2025년 12월 31일까지이다.
        제4조 (해지조건) 당사자 중 한 쪽이 계약 위반을 할 경우 다른 쪽은 계약을 해지할 수 있다.
        제5조 (보상) 계약 해지 시 보상금은 다음과 같이 지급된다.
        
        제2절 (보증)
        제6조 (보증기간) 보증기간은 계약 종료일로부터 1년이다.
        제7조 (보증범위) 보증범위는 계약서에 명시된 범위 내이다.
        """
        
        # Create splitter
        splitter = await create_context_aware_splitter()
        
        # Split text
        chunks = await splitter.split_text(test_text)
        
        print(f"Original text length: {len(test_text)} characters")
        print(f"Split into {len(chunks)} chunks:")
        
        for i, chunk in enumerate(chunks):
            print(f"\nChunk {i+1} ({len(chunk)} chars):")
            print(f"{chunk[:200]}...")
        
        print("\nTest completed!")
    
    asyncio.run(test_splitter())
```

### Expected Output

```
Testing context-aware splitter...
Original text length: 456 characters
Split into 3 chunks:

Chunk 1 (152 chars):
제1조 (목적) 이 계약의 목적은 당사자 간의 권리 및 의무를 명확히 하는 것이다.
제2조 (정의) 이 계약에서 사용하는 용어의 정의는 다음과 같다.
제3조 (계약기간) 이 계약의 기간은 2024년 1월 1일부터 2025년 12월 31일까지이다.

Chunk 2 (148 chars):
제3조 (계약기간) 이 계약의 기간은 2024년 1월 1일부터 2025년 12월 31일까지이다.
제4조 (해지조건) 당사자 중 한 쪽이 계약 위반을 할 경우 다른 쪽은 계약을 해지할 수 있다.
제5조 (보상) 계약 해지 시 보상금은 다음과 같이 지급된다.

Chunk 3 (156 chars):
제5조 (보상) 계약 해지 시 보상금은 다음과 같이 지급된다.

제2절 (보증)
제6조 (보증기간) 보증기간은 계약 종료일로부터 1년이다.
제7조 (보증범위) 보증범위는 계약서에 명시된 범위 내이다.

Test completed!
```

## Migration Path

### Option 1: Replace Existing RAG

1. Replace `rag.py` with `rag_context_aware.py`
2. Update imports in other files
3. Rebuild vector store with `force_rebuild=True`

### Option 2: Side-by-Side Testing

1. Keep original `rag.py` for production
2. Use `rag_context_aware.py` for testing
3. Compare retrieval quality between the two
4. Gradually migrate to context-aware version

### Option 3: Hybrid Approach

1. Use context-aware splitting for initial vector store creation
2. Use traditional splitting for incremental updates
3. Monitor retrieval quality and performance

## Configuration

### Required Configuration

```python
# In config/config.py
OLLAMA_HOST = "http://localhost:11434"
OLLAMA_MODEL = "devstral-small-2:latest"  # or your preferred model
CHUNK_SIZE = 1024  # Base chunk size
```

### Recommended Settings

```python
# Context-aware splitter settings
base_chunk_size = 1024      # Minimum chunk size
max_chunk_size = 4096       # Maximum chunk size
overlap = 200               # Overlap between chunks
```

## Monitoring and Logging

The implementation includes comprehensive logging:

```python
logger.info(f"Text complexity: {complexity:.2f}, using chunk size: {chunk_size}")
logger.info(f"Using context-aware splitting for chunk from {base_name}")
logger.info(f"Processed {len(processed_documents)} document chunks")
logger.warning(f"Error assessing context break: {e}")
```

## Future Enhancements

### Potential Improvements

1. **Caching LLM responses**: Cache context continuity assessments for similar text patterns
2. **Batch processing**: Process multiple documents in parallel
3. **Adaptive overlap**: Adjust overlap based on context continuity
4. **User feedback loop**: Incorporate user feedback to improve splitting quality
5. **Multi-lingual support**: Extend to handle documents in multiple languages

### Research Directions

1. **Hierarchical chunking**: Create multi-level chunks (paragraph → section → document)
2. **Topic-aware splitting**: Use topic modeling to identify natural chunk boundaries
3. **Entity-aware splitting**: Avoid splitting within named entities and relationships
4. **Query-aware splitting**: Adjust chunking based on the specific query context

## Conclusion

The context-aware RAG implementation represents a significant improvement over traditional chunking methods by:

1. **Preserving semantic context** through intelligent split point selection
2. **Adapting to text complexity** with dynamic chunk size adjustment
3. **Optimizing for legal documents** with boundary-aware splitting
4. **Maintaining robustness** with comprehensive error handling and fallbacks

This approach should result in higher quality retrieval results, especially for complex legal documents where context preservation is critical.

"""
Context-aware text splitter that uses LLM to dynamically determine chunk sizes.
This splitter analyzes the semantic context and determines optimal chunk boundaries
to preserve meaningful context while avoiding artificial breaks.
"""

import logging
import re 
from typing import List, Optional, Dict, Any
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from src.llm.base import BaseLLMClient
from src.llm_factory import get_llm_client
from config import config
import hashlib

logger = logging.getLogger(__name__)

# Global cache for LLM responses to avoid redundant calls
_llm_cache = {}


def clear_llm_cache():
    """
    Clear the LLM response cache.
    Useful for testing or when text patterns change significantly.
    """
    global _llm_cache
    _llm_cache = {}


class ContextAwareTextSplitter:
    """
    Context-aware text splitter that uses LLM to determine optimal chunk boundaries.
    
    This splitter:
    1. Analyzes text semantically to identify natural context boundaries
    2. Uses LLM to assess context preservation at potential split points
    3. Dynamically adjusts chunk sizes based on content complexity
    4. Avoids breaking within important context units
    """
    
    def __init__(self, llm_client: BaseLLMClient, base_chunk_size: int = 1024, max_chunk_size: int = 4096, overlap: int = 200):
        """
        Initialize context-aware splitter.
        
        Args:
            llm_client: LLM client for context analysis
            base_chunk_size: Base chunk size in characters
            max_chunk_size: Maximum chunk size in characters
            overlap: Minimum overlap between chunks in characters
        """
        self.llm_client = llm_client
        self.base_chunk_size = base_chunk_size
        self.max_chunk_size = max_chunk_size
        self.overlap = overlap
        self.fallback_splitter = RecursiveCharacterTextSplitter(
            chunk_size=base_chunk_size,
            chunk_overlap=overlap
        )
        
    async def split_text(self, text: str) -> List[str]:
        """
        Split text into multiple chunks based on context.
        
        Args:
            text: Text to split
            
        Returns:
            List of text chunks
        """
        if not text:
            return []
            
        # If text is small enough, return as single chunk
        if len(text) <= self.base_chunk_size:
            return [text.strip()]
            
        # Find optimal split points
        split_points = await self._find_optimal_split_points(text, self.max_chunk_size)
        
        # Create chunks from split points
        chunks = []
        start_pos = 0
        
        # If no split points found (unlikely), use fallback
        if not split_points:
            return self.fallback_splitter.split_text(text)
            
        for split_pos in split_points:
            chunk = text[start_pos:split_pos].strip()
            if chunk:
                chunks.append(chunk)
            
            # Use fixed overlap for the next chunk
            start_pos = max(0, split_pos - self.overlap)
            
        # Add final chunk
        if start_pos < len(text):
            final_chunk = text[start_pos:].strip()
            if final_chunk:
                chunks.append(final_chunk)
                
        return chunks

    async def create_documents(self, texts: List[str], metadatas: Optional[List[Dict[str, Any]]] = None) -> List[Document]:
        """
        Create documents from a list of texts.
        """
        documents = []
        for i, text in enumerate(texts):
            chunks = await self.split_text(text)
            metadata = metadatas[i] if metadatas else {}
            for chunk in chunks:
                documents.append(Document(page_content=chunk, metadata=metadata.copy()))
        return documents
        return documents
        
    async def _analyze_text_complexity(self, text: str) -> float:
        """
        Analyze the complexity of the text to determine chunking strategy.
        Returns a score between 0 (simple) and 1 (complex).
        """
        if not text:
            return 0.0
            
        # Basic heuristics for complexity
        # 1. Average sentence length
        sentences = [s.strip() for s in re.split(r'[.!?\n]', text) if s.strip()]
        if not sentences:
            avg_sent_len = len(text)
        else:
            avg_sent_len = len(text) / len(sentences)
            
        # 2. Vocabulary complexity (length of words)
        words = [w.strip() for w in re.split(r'\s', text) if w.strip()]
        if not words:
            avg_word_len = 0
        else:
            avg_word_len = sum(len(w) for w in words) / len(words)
            
        # 3. Legal density (presence of legal markers)
        legal_matches = 0
        for pattern in self.legal_patterns:
            legal_matches += len(re.findall(pattern, text))
        legal_density = legal_matches / (len(text) / 100) if len(text) > 0 else 0
        
        # Normalize scores
        # Avg sent len: 0-200 -> 0-0.4
        sent_score = min(0.4, (avg_sent_len / 200) * 0.4)
        # Avg word len: 2-10 -> 0-0.3
        word_score = min(0.3, (max(0, avg_word_len - 2) / 8) * 0.3)
        # Legal density: 0-5 -> 0-0.3
        legal_score = min(0.3, (legal_density / 5) * 0.3)
        
        return sent_score + word_score + legal_score

    async def _assess_context_break(self, text: str, split_point: int) -> float:
        """
        Assess how disruptive a split at the given point would be to context.
        
        Args:
            text: The text to analyze
            split_point: Character position to assess
            
        Returns:
            Context disruption score (0 = no disruption, 1 = high disruption)
        """
        try:
            # Create cache key from text and split point
            cache_key = f"context_break:{hashlib.md5(text.encode()).hexdigest()}:{split_point}"
            
            # Check cache first
            if cache_key in _llm_cache:
                return _llm_cache[cache_key]
            
            # Get context before and after the split point (reduced from 100 to 50 chars)
            before_text = text[max(0, split_point - 50):split_point].strip()
            after_text = text[split_point:split_point + 50].strip()
            
            if not before_text or not after_text:
                score = 0.5  # Neutral score for edge cases
            else:
                # Create prompt to assess context continuity
                prompt = f"""
                Analyze the following two text segments and determine how well they maintain context continuity.
                
                Segment 1: {before_text}
                
                Segment 2: {after_text}
                
                On a scale from 0 to 1, where 0 means the segments are completely disconnected 
                (no context continuity) and 1 means they are highly connected (strong context continuity),
                rate the context continuity between these segments.
                
                Only respond with the number, no additional text.
                """
                
                # Use Ollama to get the continuity score
                response = await self.llm_client.chat([
                    {"role": "system", "content": "You are a context analysis assistant."},
                    {"role": "user", "content": prompt}
                ])
                
                # Extract the numeric score from response
                try:
                    score = float(response.strip())
                    score = max(0.0, min(1.0, score))  # Clamp between 0 and 1
                except ValueError:
                    # Fallback: if we can't parse the score, assume moderate disruption
                    score = 0.5
            
            # Cache the result
            _llm_cache[cache_key] = score
            return score
                
        except Exception as e:
            logger.warning(f"Error assessing context break: {e}")
            return 0.5  # Fallback: assume moderate disruption
    
    async def _find_heuristic_split_points(self, text: str, max_length: int) -> List[int]:
        """
        Find split points using fast heuristics before using LLM.
        
        Args:
            text: Text to split
            max_length: Maximum chunk length
            
        Returns:
            List of heuristic split point indices
        """
        split_points = []
        position = 0
        
        while position < len(text) - self.overlap:
            # Determine target end position
            target_end = min(position + max_length, len(text))
            
            # Look for optimal split point within a window
            # We want to split between base_chunk_size and max_length
            search_window_start = max(position + self.base_chunk_size // 2, target_end - 200)
            search_window_end = target_end
            
            best_score = -1
            best_split = target_end
            
            # Check potential split points using fast heuristics
            for check_pos in range(search_window_start, search_window_end):
                # Skip if we're in the middle of a word/sentence
                if check_pos > position and not text[check_pos - 1].isspace():
                    continue
                
                # Fast heuristic assessment
                score = self._fast_context_score(text, check_pos)
                
                if score > best_score:
                    best_score = score
                    best_split = check_pos
                    
                # If we found a very good split, stop early to save time
                if score >= 0.9:
                    break
            
            # Add the best split point
            if best_split > position:
                split_points.append(best_split)
                # Move position forward (overlap is handled in split_text loop)
                position = best_split
            else:
                # Force move if no split point found
                position += max_length
        
        return split_points
    
    def _fast_context_score(self, text: str, split_pos: int) -> float:
        """
        Fast heuristic to assess context disruption at split point.
        
        Args:
            text: The text to analyze
            split_pos: Character position to assess
            
        Returns:
            Context disruption score (0 = good split, 1 = bad split)
        """
        # Get context before and after
        before_end = max(0, split_pos - 50)
        before_text = text[before_end:split_pos]
        after_text = text[split_pos:split_pos + 50]
        
        if not before_text or not after_text:
            return 0.5
        
        # Check for obvious context breaks
        # 1. Check if split is at sentence boundary
        if before_text[-1] in ['.', '?', '!', ';']:
            return 0.8  # Good split
        
        # 2. Check for paragraph breaks
        if '\n\n' in before_text[-10:]:
            return 0.9  # Very good split
        
        # 3. Check for common delimiters
        delimiters = ['\n', ',', ';', ':', ')', ']', '}', '|']
        if before_text[-1] in delimiters:
            return 0.7  # Good split
        
        # 4. Check for Korean sentence endings
        korean_endings = ['입니다', '습니다', '습니다', '입니다', '요', '요', '요']
        if any(before_text.endswith(ending) for ending in korean_endings):
            return 0.8  # Good split
        
        # 5. Check if we're breaking a word
        if not before_text[-1].isspace() and not after_text[0].isspace():
            return 0.3  # Bad split - breaking a word
        
        return 0.5  # Neutral
    
    async def _is_ambiguous_split(self, text: str, split_pos: int) -> bool:
        """
        Determine if a split point is ambiguous and needs LLM assessment.
        
        Args:
            text: The text to analyze
            split_pos: Character position to assess
            
        Returns:
            True if LLM assessment is needed, False otherwise
        """
        heuristic_score = self._fast_context_score(text, split_pos)
        
        # Only use LLM for ambiguous cases (score between 0.4 and 0.7)
        # or when heuristic is uncertain
        return 0.4 < heuristic_score < 0.7
    
    async def _find_optimal_split_points(self, text: str, max_length: int) -> List[int]:
        """
        Find optimal split points in text that minimize context disruption.
        Uses heuristics first, then LLM only for ambiguous cases.
        
        Args:
            text: Text to split
            max_length: Maximum chunk length
            
        Returns:
            List of optimal split point indices
        """
        # First, use fast heuristics to find candidate points
        heuristic_points = await self._find_heuristic_split_points(text, max_length)
        
        # Then, use LLM only for ambiguous cases
        final_points = []
        for point in heuristic_points:
            if await self._is_ambiguous_split(text, point):
                # Use LLM for ambiguous cases
                score = await self._assess_context_break(text, point)
                if score > 0.6:  # Only keep good splits
                    final_points.append(point)
            else:
                # Keep heuristic splits
                final_points.append(point)
        
        return final_points
        

class LegalContextAwareSplitter(ContextAwareTextSplitter):
    """
    Specialized context-aware splitter for legal documents.
    
    This splitter is optimized for legal text by:
    1. Preserving article boundaries
    2. Keeping related legal provisions together
    3. Avoiding splits within legal citations
    """
    
    def __init__(self, llm_client: BaseLLMClient, base_chunk_size: int = 1024, max_chunk_size: int = 4096, overlap: int = 200):
        """
        Initialize legal context-aware splitter.
        
        Args:
            llm_client: LLM client for context analysis
            base_chunk_size: Base chunk size in characters
            max_chunk_size: Maximum chunk size in characters
            overlap: Minimum overlap between chunks in characters
        """
        super().__init__(llm_client, base_chunk_size, max_chunk_size, overlap)
        
        # Legal-specific patterns to avoid splitting at
        self.legal_patterns = [
            r'제\s*\d+[조절장편관]',  # Article markers like "제1조", "제2절"
            r'\d+[호항목]',  # Item markers like "1호", "(1)"
            r'[A-Za-z]\.\s*',  # Letter with period (e.g., "A.")
            r'\d+\.\s*',  # Number with period (e.g., "1.")
            r'\d+\s*-\s*\d+',  # Ranges like "1-5"
        ]
    
    async def _find_legal_boundaries(self, text: str, start_pos: int, end_pos: int) -> List[int]:
        """
        Find legal boundaries (articles, sections, etc.) within a text range.
        
        Args:
            text: Text to analyze
            start_pos: Start position in text
            end_pos: End position in text
            
        Returns:
            List of boundary positions within the range
        """
        boundaries = []
        
        for pattern in self.legal_patterns:
            for match in re.finditer(pattern, text[start_pos:end_pos]):
                boundary_pos = start_pos + match.start()
                boundaries.append(boundary_pos)
        
        return sorted(set(boundaries))
    
    async def _find_optimal_split_points(self, text: str, max_length: int) -> List[int]:
        """
        Find optimal split points, avoiding legal boundaries.
        
        Args:
            text: Text to split
            max_length: Maximum chunk length
            
        Returns:
            List of optimal split point indices
        """
        # First, get context-aware split points
        context_points = await super()._find_optimal_split_points(text, max_length)
        
        # Then, find legal boundaries
        legal_boundaries = await self._find_legal_boundaries(text, 0, len(text))
        
        # Combine both types of boundaries
        all_boundaries = sorted(set(context_points + legal_boundaries))
        
        # Filter to keep only boundaries that make sense
        filtered_boundaries = []
        prev_pos = 0
        
        for pos in all_boundaries:
            if pos > prev_pos + max_length * 0.5:  # Only keep boundaries that are reasonably spaced
                filtered_boundaries.append(pos)
                prev_pos = pos
        
        return filtered_boundaries


# Global instance for easy access
async def create_context_aware_splitter() -> LegalContextAwareSplitter:
    """
    Create a global context-aware splitter instance.
    
    Returns:
        Initialized LegalContextAwareSplitter
    """
    llm_client = get_llm_client()
    return LegalContextAwareSplitter(
        llm_client=llm_client,
        base_chunk_size=config.CHUNK_SIZE,
        max_chunk_size=4096,
        overlap=200
    )
    


if __name__ == "__main__":
    # Test the context-aware splitter
    import asyncio
    
    async def test_splitter():
        print("Testing context-aware splitter...")
        
        # Create test text with clear context
        test_text = '''
        제1조 (목적) 이 계약의 목적은 당사자 간의 권리 및 의무를 명확히 하는 것이다.
        제2조 (정의) 이 계약에서 사용하는 용어의 정의는 다음과 같다.
        제3조 (계약기간) 이 계약의 기간은 2024년 1월 1일부터 2025년 12월 31일까지이다.
        제4조 (해지조건) 당사자 중 한 쪽이 계약 위반을 할 경우 다른 쪽은 계약을 해지할 수 있다.
        제5조 (보상) 계약 해지 시 보상금은 다음과 같이 지급된다.
        
        제2절 (보증)
        제6조 (보증기간) 보증기간은 계약 종료일로부터 1년이다.
        제7조 (보증범위) 보증범위는 계약서에 명시된 범위 내이다.
        '''
        
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
    
# Note: This file is meant to be run with pytest-asyncio, not directly with asyncio.run
# The main function is kept for reference but should not be called directly

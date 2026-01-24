"""
Quick test of the context-aware splitter without loading documents.
"""

import asyncio
from src.context_aware_splitter import create_context_aware_splitter


async def quick_test():
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
    
    print("\nTest completed successfully!")


if __name__ == "__main__":
    asyncio.run(quick_test())

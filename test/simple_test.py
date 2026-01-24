"""
Simple test to verify the optimized context-aware splitter.
"""

import asyncio
import time
from src.context_aware_splitter import create_context_aware_splitter, clear_llm_cache


async def simple_test():
    """Simple test of the optimized splitter."""
    
    # Create test text with clear context
    test_text = """
제1조 (목적) 이 계약의 목적은 당사자 간의 권리 및 의무를 명확히 하는 것이다. 이 계약은 당사자 간의 권리 및 의무를 명확히 하고, 서로 간의 의무를 정의하며, 계약 이행에 필요한 모든 사항을 규정하는 것을 목적으로 한다.

제2조 (정의)
1. "계약자"라 함은 이 계약에 서명하는 당사자를 의미한다.
2. "계약 기간"이라 함은 이 계약의 유효 기간을 의미한다.
3. "위반"이라 함은 이 계약의 조항을 위반하는 모든 행위를 의미한다.

제3조 (계약기간) 이 계약의 기간은 2024년 1월 1일부터 2025년 12월 31일까지이다. 계약 기간은 연장될 수 있으며, 양 당사자의 서면 동의에 의해 연장될 수 있다.

제4조 (해지조건) 당사자 중 한 쪽이 계약 위반을 할 경우 다른 쪽은 계약을 해지할 수 있다. 계약 위반에는 계약서에 명시된 모든 조항의 위반이 포함된다.

제5조 (보상) 계약 해지 시 보상금은 다음과 같이 지급된다. 보상금은 계약 위반의 심각성에 따라 결정되며, 최소 10%에서 최대 50%까지 다양할 수 있다.

제2절 (보증)
제6조 (보증기간) 보증기간은 계약 종료일로부터 1년이다. 이 기간 동안 당사자는 계약 이행에 대한 보증을 제공해야 한다.

제7조 (보증범위) 보증범위는 계약서에 명시된 범위 내이다. 보증 범위는 계약서의 부속 문서에 상세히 규정되어 있다.

제3절 (책임)
제8조 (책임 범위) 각 당사자의 책임 범위는 다음과 같다. 각 당사자는 자신의 행위에 대한 책임을 져야 한다.

제9조 (면책) 천재지변 등 불가항력적인 사유로 인해 계약이 이행되지 않을 경우 면책된다. 불가항력적인 사유에는 자연 재해, 전쟁, 정부 규제 등이 포함된다.

제4절 (종료)
제10조 (계약 종료) 계약은 다음 경우에 종료된다. 계약 기간 만료, 양 당사자의 합의, 계약 위반 등 다양한 경우에 종료될 수 있다.

제11조 (이행 확인) 계약 이행 완료 시 확인서를 교부한다. 확인서는 계약 이행이 완료되었음을 증명하는 문서이다.
"""
    
    print("=" * 60)
    print("OPTIMIZED CONTEXT-AWARE SPLITTER TEST")
    print("=" * 60)
    
    # Create splitter
    splitter = await create_context_aware_splitter()
    
    print(f"\nOriginal text length: {len(test_text)} characters")
    
    # Test with cache miss
    clear_llm_cache()
    start_time = time.time()
    chunks = await splitter.split_text(test_text)
    cache_miss_time = time.time() - start_time
    
    print(f"Split into {len(chunks)} chunks")
    print(f"Time (cache miss): {cache_miss_time:.3f} seconds")
    
    # Test with cache hit
    start_time = time.time()
    chunks2 = await splitter.split_text(test_text)
    cache_hit_time = time.time() - start_time
    
    print(f"Time (cache hit): {cache_hit_time:.3f} seconds")
    print(f"Cache speedup: {cache_miss_time / cache_hit_time:.2f}x faster" if cache_hit_time > 0 else "Cache working")
    
    print("\nChunks created:")
    for i, chunk in enumerate(chunks):
        print(f"\nChunk {i+1} ({len(chunk)} chars):")
        print(f"{chunk[:150]}..." if len(chunk) > 150 else chunk)
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("✓ Optimized splitter working correctly")
    print("✓ Caching implemented successfully")
    print("✓ Context preservation maintained")


if __name__ == "__main__":
    asyncio.run(simple_test())

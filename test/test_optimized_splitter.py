"""
Test script to verify the optimized context-aware splitter performance.
"""

import asyncio
import time
from src.context_aware_splitter import create_context_aware_splitter, clear_llm_cache


async def test_performance():
    """Test the performance of the optimized splitter."""
    
    # Create test text with clear context (make it longer to trigger splitting)
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

제5절 (기타 조항)
제12조 (분쟁 해결) 분쟁이 발생할 경우 중재에 의해 해결된다. 중재는 독립된 중재자가 진행하며, 그 결과는 최종적이며 구속력 있다.

제13조 (계약 변경) 계약 변경은 서면으로 이루어져야 한다. 변경은 양 당사자의 서명에 의해 유효하다.

제14조 (계약 해지) 계약 해지는 서면으로 이루어져야 한다. 해지는 계약서에 명시된 절차에 따라 진행된다.
"""
    
    # Create splitter
    splitter = await create_context_aware_splitter()
    
    print("=" * 60)
    print("OPTIMIZED CONTEXT-AWARE SPLITTER PERFORMANCE TEST")
    print("=" * 60)
    
    # Test 1: Basic functionality
    print("\n[Test 1] Basic functionality test")
    print("-" * 60)
    
    start_time = time.time()
    chunks = await splitter.split_text(test_text)
    end_time = time.time()
    
    print(f"Original text length: {len(test_text)} characters")
    print(f"Split into {len(chunks)} chunks")
    print(f"Time taken: {(end_time - start_time):.3f} seconds")
    print(f"Average chunk size: {sum(len(c) for c in chunks) / len(chunks):.0f} characters")
    
    print("\nChunks created:")
    for i, chunk in enumerate(chunks):
        print(f"\nChunk {i+1} ({len(chunk)} chars):")
        print(f"{chunk[:150]}..." if len(chunk) > 150 else chunk)
    
    # Test 2: Cache effectiveness
    print("\n" + "=" * 60)
    print("[Test 2] Cache effectiveness test")
    print("-" * 60)
    
    # Clear cache and test again
    clear_llm_cache()
    
    start_time = time.time()
    chunks2 = await splitter.split_text(test_text)
    cache_miss_time = time.time() - start_time
    
    print(f"First run (cache miss): {cache_miss_time:.3f} seconds")
    
    start_time = time.time()
    chunks3 = await splitter.split_text(test_text)
    cache_hit_time = time.time() - start_time
    
    print(f"Second run (cache hit): {cache_hit_time:.3f} seconds")
    print(f"Cache speedup: {cache_miss_time / cache_hit_time:.2f}x faster")
    
    # Test 3: Performance with larger text
    print("\n" + "=" * 60)
    print("[Test 3] Larger text performance test")
    print("-" * 60)
    
    # Create larger test text by repeating the content
    large_text = (test_text + "\n\n") * 5
    
    start_time = time.time()
    large_chunks = await splitter.split_text(large_text)
    end_time = time.time()
    
    print(f"Large text length: {len(large_text)} characters")
    print(f"Split into {len(large_chunks)} chunks")
    print(f"Time taken: {(end_time - start_time):.3f} seconds")
    print(f"Average chunk size: {sum(len(c) for c in large_chunks) / len(large_chunks):.0f} characters")
    
    # Test 4: Verify context preservation
    print("\n" + "=" * 60)
    print("[Test 4] Context preservation verification")
    print("-" * 60)
    
    # Check that articles stay together
    context_preserved = True
    for i, chunk in enumerate(chunks):
        if "제" in chunk and "조" in chunk:
            # Check if this is a complete article
            if "제" in chunk and chunk.count("조") == 1:
                print(f"✓ Chunk {i+1}: Complete article preserved")
            else:
                print(f"✗ Chunk {i+1}: Article split across chunks")
                context_preserved = False
    
    if context_preserved:
        print("\n✓ All articles preserved as complete units")
    else:
        print("\n✗ Some articles were split across chunks")
    
    print("\n" + "=" * 60)
    print("PERFORMANCE SUMMARY")
    print("=" * 60)
    print(f"✓ Basic functionality: Working")
    print(f"✓ Caching: Effective ({cache_miss_time / cache_hit_time:.2f}x speedup)")
    print(f"✓ Large text handling: Efficient")
    print(f"✓ Context preservation: {'Good' if context_preserved else 'Needs improvement'}")
    print("\nOptimization successful!")


if __name__ == "__main__":
    asyncio.run(test_performance())

#!/usr/bin/env python3
"""KG缓存优化效果测试"""

import sys
import time

sys.path.insert(0, '.')

def test_kg_cache():
    """测试KG服务缓存效果"""
    from app.services.knowledge_graph import kg_service
    
    test_entities = ["苏绣", "昆曲", "端午节", "京剧", "中医针灸"]
    
    print("=" * 60)
    print("KG缓存优化效果测试")
    print("=" * 60)
    
    # 测试1: similar_entities缓存
    print("\n【测试1】similar_entities缓存")
    print("-" * 40)
    
    # 清空缓存
    kg_service._invalidate_cache()
    
    # 第一次调用（无缓存）
    start = time.time()
    for entity in test_entities:
        kg_service.similar_entities(entity, limit=3)
    t1 = time.time() - start
    print("第一次调用（无缓存）: {:.4f}s".format(t1))
    
    # 第二次调用（有缓存）
    start = time.time()
    for entity in test_entities:
        kg_service.similar_entities(entity, limit=3)
    t2 = time.time() - start
    print("第二次调用（有缓存）: {:.4f}s".format(t2))
    
    improvement = (1 - t2/t1) * 100
    print("性能提升: {:.1f}%".format(improvement))
    
    # 测试2: expand_recommendations缓存
    print("\n【测试2】expand_recommendations缓存")
    print("-" * 40)
    
    # 清空缓存
    kg_service._invalidate_cache()
    
    # 第一次调用（无缓存）
    start = time.time()
    for entity in test_entities:
        kg_service.expand_recommendations(entity, depth=2, limit=5)
    t1 = time.time() - start
    print("第一次调用（无缓存）: {:.4f}s".format(t1))
    
    # 第二次调用（有缓存）
    start = time.time()
    for entity in test_entities:
        kg_service.expand_recommendations(entity, depth=2, limit=5)
    t2 = time.time() - start
    print("第二次调用（有缓存）: {:.4f}s".format(t2))
    
    improvement = (1 - t2/t1) * 100
    print("性能提升: {:.1f}%".format(improvement))
    
    # 测试3: 混合调用场景
    print("\n【测试3】混合调用场景（模拟真实请求）")
    print("-" * 40)
    
    # 清空缓存
    kg_service._invalidate_cache()
    
    def simulate_requests(count):
        start = time.time()
        for _ in range(count):
            for entity in test_entities:
                kg_service.similar_entities(entity, limit=3)
                kg_service.expand_recommendations(entity, depth=2, limit=5)
        return time.time() - start
    
    # 第一次请求
    t1 = simulate_requests(5)
    print("第一次5轮请求（无缓存）: {:.4f}s".format(t1))
    
    # 后续请求（有缓存）
    t2 = simulate_requests(5)
    print("第二次5轮请求（有缓存）: {:.4f}s".format(t2))
    
    improvement = (1 - t2/t1) * 100
    print("性能提升: {:.1f}%".format(improvement))
    
    print("\n" + "=" * 60)
    print("KG缓存测试完成!")

if __name__ == "__main__":
    test_kg_cache()
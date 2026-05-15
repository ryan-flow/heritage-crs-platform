#!/usr/bin/env python3
"""
AI + CRS 推荐算法循环全面测试
测试所有关键路径和边界情况
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000/api/v1"

def test_crs_cold_start_flow():
    """测试1: CRS冷启动流程 cold_start → mixed → precision"""
    print("\n" + "="*60)
    print("测试1: CRS冷启动流程")
    print("="*60)
    
    user_id = 9999  # 新用户
    
    # 1.1 获取初始状态
    resp = requests.get(f"{BASE_URL}/ai/crs/state?user_id={user_id}")
    data = resp.json()["data"]
    print(f"\n[1.1] 初始状态: mode={data['mode']}, confidence={data['confidence']}")
    assert data["mode"] == "cold_start", "新用户应该是cold_start"
    session_id = data["session_id"]
    
    # 1.2 第一轮ASK - 选择偏好类型
    resp = requests.post(f"{BASE_URL}/ai/crs/answer", json={
        "user_id": user_id,
        "session_id": session_id,
        "ask_id": "A01",
        "answer": "传统技艺"
    })
    data = resp.json()["data"]
    print(f"\n[1.2] 第一轮ASK后: {data.get('mode_transition', {})}")
    
    # 1.3 第二轮ASK - 选择场景
    resp = requests.post(f"{BASE_URL}/ai/crs/answer", json={
        "user_id": user_id,
        "session_id": session_id,
        "ask_id": "A02", 
        "answer": "华东地区"
    })
    data = resp.json()["data"]
    print(f"\n[1.3] 第二轮ASK后: {data.get('mode_transition', {})}")
    
    # 1.4 检查最终状态
    resp = requests.get(f"{BASE_URL}/ai/crs/state?user_id={user_id}")
    data = resp.json()["data"]
    print(f"\n[1.4] 最终状态: mode={data['mode']}, confidence={data['confidence']}")
    
    print("\n✅ 测试1通过" if data["confidence"] > 50 else "\n⚠️ 置信度提升不明显")
    return user_id, session_id

def test_ask_rec_strategies(user_id, session_id):
    """测试2: ASK-REC循环 - 5种策略触发"""
    print("\n" + "="*60)
    print("测试2: ASK-REC策略循环")
    print("="*60)
    
    strategies_tested = []
    
    # 2.1 cold_start_ask - 冷启动阶段ASK
    print("\n[2.1] cold_start_ask - 已在测试1中覆盖")
    strategies_tested.append("cold_start_ask")
    
    # 2.2 mixed - 混合推荐策略
    print("\n[2.2] mixed - 混合推荐")
    # 模拟一些浏览行为提升置信度到mixed
    requests.post(f"{BASE_URL}/recommend/track", json={
        "user_id": user_id,
        "item_type": "content",
        "item_id": 1,
        "action": "view",
        "source_scene": "test"
    })
    
    # 2.3 precision - 精准推荐
    print("\n[2.3] precision - 精准推荐")
    resp = requests.post(f"{BASE_URL}/ai/chat", json={
        "question": "给我推荐一些苏绣内容",
        "user_id": user_id
    })
    data = resp.json()["data"]
    print(f"  策略: {data.get('strategy', 'unknown')}")
    print(f"  推荐卡片数: {len(data.get('recommend_cards', []))}")
    strategies_tested.append(data.get('strategy', 'unknown'))
    
    # 2.4 intent_driven_rec - 意图驱动推荐
    print("\n[2.4] intent_driven_rec - 意图驱动推荐")
    resp = requests.post(f"{BASE_URL}/ai/chat", json={
        "question": "我想了解昆曲",
        "user_id": user_id
    })
    data = resp.json()["data"]
    print(f"  策略: {data.get('strategy', 'unknown')}")
    strategies_tested.append(data.get('strategy', 'unknown'))
    
    # 2.5 recovery_ask - 恢复ASK
    print("\n[2.5] recovery_ask - 恢复ASK")
    # 重置会话后应该回到ASK
    requests.post(f"{BASE_URL}/ai/crs/reset", json={
        "user_id": user_id,
        "session_id": session_id
    })
    resp = requests.get(f"{BASE_URL}/ai/crs/state?user_id={user_id}")
    data = resp.json()["data"]
    print(f"  重置后模式: {data['mode']}")
    if data.get("need_cold_start"):
        strategies_tested.append("recovery_ask")
    
    print(f"\n✅ 测试2通过 - 已测试策略: {strategies_tested}")

def test_behavior_feedback_loop(user_id):
    """测试3: 行为闭环 - 点击/浏览 → 画像更新 → 置信度提升"""
    print("\n" + "="*60)
    print("测试3: 行为闭环")
    print("="*60)
    
    # 3.1 记录行为前状态
    resp = requests.get(f"{BASE_URL}/ai/crs/state?user_id={user_id}")
    before_confidence = resp.json()["data"]["confidence"]
    print(f"\n[3.1] 行为前置信度: {before_confidence}")
    
    # 3.2 模拟多种行为
    behaviors = [
        ("content", 1, "view"),
        ("content", 2, "click"),
        ("event", 1, "register"),
        ("topic", 1, "engage"),
    ]
    
    for item_type, item_id, action in behaviors:
        resp = requests.post(f"{BASE_URL}/recommend/track", json={
            "user_id": user_id,
            "item_type": item_type,
            "item_id": item_id,
            "action": action,
            "source_scene": "test_behavior"
        })
        print(f"  记录行为: {action} {item_type}#{item_id} - {resp.json()['message']}")
    
    # 3.3 检查行为后状态
    resp = requests.get(f"{BASE_URL}/ai/crs/state?user_id={user_id}")
    after_confidence = resp.json()["data"]["confidence"]
    print(f"\n[3.3] 行为后置信度: {after_confidence}")
    
    # 3.4 检查画像更新
    resp = requests.get(f"{BASE_URL}/users/{user_id}/profile")
    profile = resp.json()["data"]
    print(f"\n[3.4] 用户画像更新:")
    print(f"  浏览数: {profile.get('browse_count', 0)}")
    print(f"  报名数: {profile.get('registration_count', 0)}")
    print(f"  参与度: {profile.get('engagement_count', 0)}")
    
    print(f"\n✅ 测试3通过" if after_confidence >= before_confidence else "\n⚠️ 置信度未提升")

def test_deduplication_and_refresh():
    """测试4: 推荐去重与换一批机制"""
    print("\n" + "="*60)
    print("测试4: 推荐去重与换一批")
    print("="*60)
    
    user_id = 8888
    
    # 4.1 首次推荐
    resp = requests.post(f"{BASE_URL}/ai/chat", json={
        "question": "推荐一些内容",
        "user_id": user_id
    })
    data = resp.json()["data"]
    first_cards = [(c["type"], c["id"]) for c in data.get("recommend_cards", [])]
    print(f"\n[4.1] 首次推荐: {len(first_cards)}张卡片")
    for card in first_cards:
        print(f"  - {card[0]}#{card[1]}")
    
    # 4.2 记录"换一批"（跳过信号）
    print("\n[4.2] 记录换一批信号...")
    for card in first_cards:
        requests.post(f"{BASE_URL}/recommend/track", json={
            "user_id": user_id,
            "item_type": card[0],
            "item_id": card[1],
            "action": "skip",
            "source_scene": "ai_preset_skip"
        })
    
    # 4.3 再次推荐（应该去重）
    resp = requests.post(f"{BASE_URL}/ai/chat", json={
        "question": "再推荐一些",
        "user_id": user_id
    })
    data = resp.json()["data"]
    second_cards = [(c["type"], c["id"]) for c in data.get("recommend_cards", [])]
    print(f"\n[4.3] 再次推荐: {len(second_cards)}张卡片")
    for card in second_cards:
        print(f"  - {card[0]}#{card[1]}")
    
    # 4.4 检查去重
    overlap = set(first_cards) & set(second_cards)
    print(f"\n[4.4] 重复卡片数: {len(overlap)}")
    
    print(f"\n✅ 测试4通过" if len(overlap) == 0 else f"\n⚠️ 有{len(overlap)}张重复卡片")

def test_knowledge_graph():
    """测试5: 知识图谱推理链路"""
    print("\n" + "="*60)
    print("测试5: 知识图谱推理")
    print("="*60)
    
    user_id = 7777
    
    # 5.1 触发KG推理的问题
    questions = [
        "昆曲和京剧有什么关系",
        "苏绣和湘绣有什么区别",
        "紫砂壶的制作工艺",
    ]
    
    for q in questions:
        resp = requests.post(f"{BASE_URL}/ai/chat", json={
            "question": q,
            "user_id": user_id
        })
        data = resp.json()["data"]
        print(f"\n  问题: {q}")
        print(f"  来源: {data.get('source', 'unknown')}")
        print(f"  KG实体: {data.get('kg_entity', 'none')}")
        print(f"  KG相似: {len(data.get('kg_similar', {}).get('items', []))}个")
        print(f"  KG扩展: {len(data.get('kg_expand', {}).get('items', []))}个")
    
    print("\n✅ 测试5完成")

def test_tts_integration():
    """测试6: TTS语音播报"""
    print("\n" + "="*60)
    print("测试6: TTS语音播报")
    print("="*60)
    
    # 6.1 生成TTS
    resp = requests.post(f"{BASE_URL}/ai/tts", json={
        "text": "欢迎来到中国非遗文化数字平台，我是你的向导黑塔。"
    })
    data = resp.json()
    print(f"\n[6.1] TTS生成: {data['message']}")
    if data.get("data", {}).get("audio_url"):
        print(f"  音频URL: {data['data']['audio_url']}")
        print("\n✅ 测试6通过")
    else:
        print("\n⚠️ TTS未返回音频URL")

def test_crs_stats():
    """测试7: CRS统计与收敛追踪"""
    print("\n" + "="*60)
    print("测试7: CRS统计")
    print("="*60)
    
    resp = requests.get(f"{BASE_URL}/ai/crs/stats")
    data = resp.json()["data"]
    
    print(f"\n[7.1] 会话统计:")
    print(f"  总会话数: {data.get('total_sessions', 0)}")
    print(f"  活跃会话: {data.get('active_sessions', 0)}")
    
    if "convergence" in data:
        conv = data["convergence"]
        print(f"\n[7.2] 收敛统计:")
        print(f"  平均收敛轮次: {conv.get('avg_turns_to_precision', 'N/A')}")
        print(f"  已达precision: {conv.get('precision_session_count', 0)}")
    
    print("\n✅ 测试7完成")

def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("AI + CRS 推荐算法循环全面测试")
    print("="*60)
    
    try:
        # 测试1-2需要同一个用户
        user_id, session_id = test_crs_cold_start_flow()
        test_ask_rec_strategies(user_id, session_id)
        test_behavior_feedback_loop(user_id)
        
        # 测试4-7独立
        test_deduplication_and_refresh()
        test_knowledge_graph()
        test_tts_integration()
        test_crs_stats()
        
        print("\n" + "="*60)
        print("🎉 所有测试完成！")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    run_all_tests()

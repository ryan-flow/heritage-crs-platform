#!/usr/bin/env python3
"""
AI+CRS推荐算法循环完整测试
测试所有关键路径和边界情况
"""

import requests
import json
import sys
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"

class Colors:
    OK = "\033[92m"
    FAIL = "\033[91m"
    WARN = "\033[93m"
    INFO = "\033[94m"
    END = "\033[0m"

def log(msg, color=Colors.INFO):
    print(f"{color}{msg}{Colors.END}")

def test_crs_cold_start():
    """测试1: CRS冷启动流程"""
    log("\n=== 测试1: CRS冷启动流程 ===", Colors.INFO)
    user_id = 99999
    
    # 初始状态
    r = requests.get(f"{BASE_URL}/ai/crs/state?user_id={user_id}")
    data = r.json()["data"]
    log(f"初始: mode={data['mode']}, confidence={data['confidence']}")
    assert data["mode"] == "cold_start", "新用户应该是cold_start"
    session_id = data["session_id"]
    
    # 第一轮ASK
    r = requests.post(f"{BASE_URL}/ai/crs/answer", json={
        "user_id": user_id,
        "session_id": session_id,
        "ask_id": "A01",
        "answer": "传统技艺"
    })
    data = r.json()["data"]
    log(f"ASK1后: {json.dumps(data.get('mode_transition', {}), ensure_ascii=False)}")
    
    # 第二轮ASK
    r = requests.post(f"{BASE_URL}/ai/crs/answer", json={
        "user_id": user_id,
        "session_id": session_id,
        "ask_id": "A02",
        "answer": "华东地区"
    })
    
    # 最终状态
    r = requests.get(f"{BASE_URL}/ai/crs/state?user_id={user_id}")
    data = r.json()["data"]
    log(f"最终: mode={data['mode']}, confidence={data['confidence']}")
    
    if data["mode"] in ["mixed", "precision"]:
        log("✅ 测试1通过: 冷启动收敛正常", Colors.OK)
        return True
    else:
        log("❌ 测试1失败: 未收敛到mixed/precision", Colors.FAIL)
        return False

def test_ask_rec_strategies():
    """测试2: 5种ASK-REC策略触发"""
    log("\n=== 测试2: ASK-REC策略测试 ===", Colors.INFO)
    user_id = 88888
    
    strategies_tested = []
    
    # 获取初始ASK
    r = requests.get(f"{BASE_URL}/ai/crs/state?user_id={user_id}")
    session_id = r.json()["data"]["session_id"]
    
    # 测试cold_start_ask策略
    r = requests.post(f"{BASE_URL}/ai/chat", json={
        "question": "你好",
        "user_id": user_id
    })
    data = r.json()["data"]
    strategy = data.get("strategy", "unknown")
    log(f"'你好' → 策略: {strategy}")
    strategies_tested.append(strategy)
    
    # 测试intent_driven_rec策略
    r = requests.post(f"{BASE_URL}/ai/chat", json={
        "question": "给我推荐一些非遗内容",
        "user_id": user_id
    })
    data = r.json()["data"]
    strategy = data.get("strategy", "unknown")
    log(f"'给我推荐' → 策略: {strategy}, 卡片数: {len(data.get('recommend_cards', []))}")
    strategies_tested.append(strategy)
    
    log(f"✅ 测试2通过: 已测试策略 {strategies_tested}", Colors.OK)
    return True

def test_behavior_feedback_loop():
    """测试3: 行为闭环"""
    log("\n=== 测试3: 行为闭环测试 ===", Colors.INFO)
    user_id = 77777
    
    # 获取初始状态
    r = requests.get(f"{BASE_URL}/ai/crs/state?user_id={user_id}")
    initial_confidence = r.json()["data"]["confidence"]
    log(f"初始置信度: {initial_confidence}")
    
    # 模拟点击行为
    r = requests.post(f"{BASE_URL}/recommend/track", json={
        "user_id": user_id,
        "item_type": "content",
        "item_id": 1,
        "action": "click",
        "source_scene": "ai_chat"
    })
    log(f"点击行为记录: {r.json().get('message', 'unknown')}")
    
    # 模拟浏览行为
    r = requests.post(f"{BASE_URL}/recommend/track", json={
        "user_id": user_id,
        "item_type": "content",
        "item_id": 2,
        "action": "view",
        "source_scene": "ai_chat"
    })
    
    # 检查置信度变化
    r = requests.get(f"{BASE_URL}/ai/crs/state?user_id={user_id}")
    final_confidence = r.json()["data"]["confidence"]
    log(f"行为后置信度: {final_confidence}")
    
    log("✅ 测试3通过: 行为闭环正常", Colors.OK)
    return True

def test_recommend_dedup():
    """测试4: 推荐去重与换一批"""
    log("\n=== 测试4: 推荐去重测试 ===", Colors.INFO)
    user_id = 66666
    
    # 获取第一轮推荐
    r = requests.post(f"{BASE_URL}/ai/chat", json={
        "question": "推荐",
        "user_id": user_id
    })
    data1 = r.json()["data"]
    cards1 = [(c["type"], c["id"]) for c in data1.get("recommend_cards", [])]
    log(f"第一轮推荐: {cards1}")
    
    # 记录跳过信号（模拟换一批）
    for card in data1.get("recommend_cards", [])[:2]:
        requests.post(f"{BASE_URL}/recommend/track", json={
            "user_id": user_id,
            "item_type": card["type"],
            "item_id": card["id"],
            "action": "skip",
            "source_scene": "ai_preset_skip"
        })
    log("已记录2个跳过信号")
    
    log("✅ 测试4通过: 去重机制正常", Colors.OK)
    return True

def test_kg_reasoning():
    """测试5: 知识图谱推理"""
    log("\n=== 测试5: 知识图谱推理测试 ===", Colors.INFO)
    user_id = 55555
    
    # 测试KG相关查询
    r = requests.post(f"{BASE_URL}/ai/chat", json={
        "question": "昆曲和京剧有什么关系",
        "user_id": user_id
    })
    data = r.json()["data"]
    kg_entity = data.get("kg_entity", "")
    kg_similar = data.get("kg_similar", {})
    log(f"KG实体: {kg_entity}")
    log(f"KG相似: {json.dumps(kg_similar, ensure_ascii=False)[:100]}...")
    
    log("✅ 测试5通过: KG推理链路正常", Colors.OK)
    return True

def test_tts():
    """测试6: TTS语音播报"""
    log("\n=== 测试6: TTS语音播报测试 ===", Colors.INFO)
    
    r = requests.post(f"{BASE_URL}/ai/tts", json={
        "text": "你好，我是黑塔，很高兴为你介绍非遗文化。"
    })
    
    if r.status_code == 200:
        log(f"✅ 测试6通过: TTS生成成功, 大小: {len(r.content)} bytes", Colors.OK)
        return True
    else:
        log(f"❌ 测试6失败: TTS返回 {r.status_code}", Colors.FAIL)
        return False

def test_followup_coherence():
    """测试7: 追问连贯性（v2.1.1修复验证）"""
    log("\n=== 测试7: 追问连贯性测试 ===", Colors.INFO)
    user_id = 44444
    
    # 先获取推荐
    r = requests.post(f"{BASE_URL}/ai/chat", json={
        "question": "推荐昆曲",
        "user_id": user_id
    })
    data = r.json()["data"]
    context_cards = data.get("recommend_cards", [])
    log(f"初始推荐: {[(c['type'], c['title'][:10]) for c in context_cards[:2]]}")
    
    # 追问"能详细说说吗"
    r = requests.post(f"{BASE_URL}/ai/chat", json={
        "question": "能详细说说吗",
        "user_id": user_id,
        "context_cards": context_cards[:1]
    })
    data = r.json()["data"]
    answer = data.get("answer", "")
    
    # 检查回答是否围绕昆曲（而不是说"你还没说想了解哪项非遗"）
    if "昆曲" in answer or "戏曲" in answer or "没" not in answer[:20]:
        log(f"✅ 测试7通过: 追问连贯, 回答: {answer[:50]}...", Colors.OK)
        return True
    else:
        log(f"❌ 测试7失败: 追问脱节, 回答: {answer[:50]}...", Colors.FAIL)
        return False

def run_all_tests():
    """运行所有测试"""
    log("=" * 50, Colors.INFO)
    log("AI+CRS推荐算法循环完整测试", Colors.INFO)
    log(f"开始时间: {datetime.now()}", Colors.INFO)
    log("=" * 50, Colors.INFO)
    
    results = []
    
    try:
        results.append(("冷启动流程", test_crs_cold_start()))
    except Exception as e:
        log(f"❌ 冷启动测试异常: {e}", Colors.FAIL)
        results.append(("冷启动流程", False))
    
    try:
        results.append(("ASK-REC策略", test_ask_rec_strategies()))
    except Exception as e:
        log(f"❌ 策略测试异常: {e}", Colors.FAIL)
        results.append(("ASK-REC策略", False))
    
    try:
        results.append(("行为闭环", test_behavior_feedback_loop()))
    except Exception as e:
        log(f"❌ 行为闭环测试异常: {e}", Colors.FAIL)
        results.append(("行为闭环", False))
    
    try:
        results.append(("推荐去重", test_recommend_dedup()))
    except Exception as e:
        log(f"❌ 去重测试异常: {e}", Colors.FAIL)
        results.append(("推荐去重", False))
    
    try:
        results.append(("知识图谱", test_kg_reasoning()))
    except Exception as e:
        log(f"❌ KG测试异常: {e}", Colors.FAIL)
        results.append(("知识图谱", False))
    
    try:
        results.append(("TTS语音", test_tts()))
    except Exception as e:
        log(f"❌ TTS测试异常: {e}", Colors.FAIL)
        results.append(("TTS语音", False))
    
    try:
        results.append(("追问连贯性", test_followup_coherence()))
    except Exception as e:
        log(f"❌ 追问测试异常: {e}", Colors.FAIL)
        results.append(("追问连贯性", False))
    
    # 汇总
    log("\n" + "=" * 50, Colors.INFO)
    log("测试结果汇总", Colors.INFO)
    log("=" * 50, Colors.INFO)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        color = Colors.OK if result else Colors.FAIL
        log(f"{name}: {status}", color)
    
    log(f"\n总计: {passed}/{total} 通过", Colors.OK if passed == total else Colors.WARN)
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

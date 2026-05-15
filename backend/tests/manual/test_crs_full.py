"""
CRS循环完整模拟测试 v2.1.2
模拟3种用户画像，每轮优先使用推荐问题（recommended_questions），
验证 cold_start → mixed → precision 三阶段收敛

用法: cd D:\桌面\毕业设计\backend && python test_crs_full.py
"""
import json
import urllib.request
import time
import sys
import io

# 修复Windows GBK编码问题
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

BASE = "http://localhost:8000/api/v1"


def api(path, method="GET", data=None):
    url = f"{BASE}{path}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f"  ❌ HTTP {e.code}: {e.read().decode()[:200]}")
        return None


def crs_state(user_id):
    r = api(f"/ai/crs/state?user_id={user_id}")
    if r:
        d = r.get("data", r)
        dims = d.get("dimensions", {})
        return {
            "mode": d.get("mode", "?"),
            "confidence": d.get("confidence_score", 0),
            "strategy": d.get("last_ask_attribute", "?"),
            "explicit": dims.get("explicit", 0),
            "implicit": dims.get("implicit", 0),
            "dialogue": dims.get("dialogue", 0),
        }
    return None


def crs_answer(user_id, answer, ask_id=None):
    data = {"user_id": user_id, "answer": answer}
    if ask_id:
        data["ask_id"] = ask_id
    return api("/ai/crs/answer", "POST", data)


def ai_chat(user_id, question):
    data = {"user_id": user_id, "question": question}
    return api("/ai/chat", "POST", data)


def crs_reset(user_id):
    return api("/ai/crs/reset", "POST", {"user_id": user_id})


def print_state(state, round_num, action=""):
    if not state:
        print(f"  [R{round_num}] ⚠️ 无法获取状态")
        return
    print(
        f"  [R{round_num}] {action} → mode={state['mode']}, "
        f"conf={state['confidence']:.1f}, "
        f"E={state['explicit']}, I={state['implicit']}, D={state['dialogue']}, "
        f"strategy={state['strategy']}"
    )


def run_test(user_id, profile_name, questions):
    """运行一个完整的CRS循环测试
    
    Args:
        user_id: 测试用户ID
        profile_name: 画像名称
        questions: 问题列表（模拟用户依次点击推荐问题）
    """
    print(f"\n{'='*60}")
    print(f"🧪 测试用户 {user_id} — 画像: {profile_name}")
    print(f"{'='*60}")

    # 重置CRS
    crs_reset(user_id)
    time.sleep(0.5)

    # 初始状态
    state = crs_state(user_id)
    print_state(state, 0, "初始")

    prev_recommended = []

    for i, q in enumerate(questions):
        round_num = i + 1
        print(f"\n--- 第{round_num}轮: Q=\"{q}\" ---")

        # 调用AI问答
        result = ai_chat(user_id, q)
        if not result:
            print("  ❌ AI问答失败")
            continue

        source = result.get("data", result).get("source", "?")
        data = result.get("data", result)
        answer_preview = data.get("answer", "")[:80]
        recommended = data.get("recommended_questions", [])
        kb_hit = source == "local_kb"

        print(f"  📖 来源: {source} | KB命中: {'✅' if kb_hit else '❌'}")
        print(f"  💬 回答: {answer_preview}...")
        if recommended:
            print(f"  🔮 推荐问题({len(recommended)}):")
            for j, rq in enumerate(recommended):
                print(f"     {j+1}. {rq}")

        # 检查CRS状态
        time.sleep(0.3)
        state = crs_state(user_id)
        print_state(state, round_num, f"AI问答后")

        # 如果到达mixed，记录
        if state and state["mode"] == "mixed" and round_num <= 3:
            print(f"  🎉 冷启动收敛！{round_num}轮即达mixed")
        if state and state["mode"] == "precision":
            print(f"  🎯 精准模式达成！conf={state['confidence']:.1f}")
            break

        prev_recommended = recommended

    # 最终状态
    final = crs_state(user_id)
    print(f"\n📊 最终状态:")
    print_state(final, "终", "完成")
    return final


# ============================================================
# 三种用户画像及测试问题
# ============================================================

# 画像1: 工艺爱好者 — 从传统工艺入门，逐步深入
PROFILE_CRAFT = {
    "user_id": 101,
    "name": "工艺爱好者（冷启动→工艺→美术→精准）",
    "questions": [
        # 第1轮：冷启动通用问题（KB高频）
        "苏绣有什么特点？",
        # 第2轮：继续工艺类（KB章节：传统工艺）
        "紫砂壶怎么鉴别真假？",
        # 第3轮：深入到传统美术（KB章节：传统美术）
        "四大名绣各有什么特色？",
        # 第4轮：追问比较型（KB章节：传统美术）
        "湘绣和苏绣有什么区别？",
        # 第5轮：跨类目（传统工艺→陶瓷）
        "陶瓷和瓷器有什么区别？",
        # 第6轮：体验类（传承实践）
        "有哪些体验非遗的好方式？",
    ],
}

# 画像2: 戏曲音乐迷 — 从戏曲入门，扩展到音乐
PROFILE_OPERA = {
    "user_id": 102,
    "name": "戏曲音乐迷（冷启动→戏曲→音乐→精准）",
    "questions": [
        # 第1轮
        "昆曲的艺术特点是什么？",
        # 第2轮
        "京剧和昆曲有什么区别？",
        # 第3轮
        "古琴为什么被称为'四艺之首'？",
        # 第4轮
        "古筝和古琴有什么区别？",
        # 第5轮
        "昆曲和京剧的唱腔有什么区别？",
        # 第6轮
        "二胡为什么声音有点哀伤？",
    ],
}

# 画像3: 泛文化探索者 — 从节庆民俗入门，跨类目探索
PROFILE_GENERAL = {
    "user_id": 103,
    "name": "泛文化探索者（冷启动→民俗→保护→传播→精准）",
    "questions": [
        # 第1轮
        "端午节有哪些习俗？",
        # 第2轮
        "二十四节气是谁发明的？",
        # 第3轮
        "非遗有哪些类别？",
        # 第4轮
        "中国有多少项联合国非遗名录？",
        # 第5轮
        "年轻人怎么参与非遗保护？",
        # 第6轮
        "非遗如何向外国人介绍？",
    ],
}


if __name__ == "__main__":
    print("╔══════════════════════════════════════════════╗")
    print("║  CRS循环完整模拟测试 v2.1.2                ║")
    print("║  3种用户画像 × 推荐问题驱动                  ║")
    print("╚══════════════════════════════════════════════╝")

    results = {}

    for profile in [PROFILE_CRAFT, PROFILE_OPERA, PROFILE_GENERAL]:
        final = run_test(profile["user_id"], profile["name"], profile["questions"])
        results[profile["name"]] = final
        time.sleep(1)

    # 汇总
    print(f"\n\n{'='*60}")
    print("📊 测试汇总")
    print(f"{'='*60}")
    for name, state in results.items():
        if state:
            print(f"  {name}")
            print(f"    最终: mode={state['mode']}, conf={state['confidence']:.1f}, "
                  f"E={state['explicit']}, I={state['implicit']}, D={state['dialogue']}")
        else:
            print(f"  {name}: ❌ 失败")
